"""Compara o pré-treino e o ajuste nas quatro provas, com temperatura zero."""

from __future__ import annotations

import json
import re
from pathlib import Path

import torch
from tokenizers import Tokenizer

from modelo import Config, Modelo
from treino_instrucao import encerrar_fim

RAIZ = Path(__file__).resolve().parent


def prefixo(item: dict) -> str:
    texto = f"Instrução: {item['instrucao']}\n"
    if item.get("contexto"):
        texto += f"Contexto: {item['contexto']}\n"
    return texto + "Resposta: "


def digitos(texto: str) -> str:
    return re.sub(r"\D", "", texto)


def uma_frase(texto: str) -> bool:
    limpo = texto.strip()
    if not limpo or "\n" in limpo:
        return False
    return len(re.findall(r"[.!?]", limpo)) <= 1 and len(limpo) < 220


def nao_inventa(texto: str) -> bool:
    baixo = texto.lower()
    return "não está" in baixo and not re.search(r"\d", texto)


def so_numero(texto: str, numero: str) -> bool:
    limpo = texto.strip().strip(".")
    return digitos(limpo) == numero and re.fullmatch(r"[\d.]+", limpo) is not None


def curto(texto: str, limite: int) -> bool:
    return 0 < len(texto.split()) <= limite


def fato(texto: str, item: dict) -> bool:
    baixo = texto.lower()
    if not all(parte.lower() in baixo for parte in item.get("exige", [])):
        return False
    return not any(parte.lower() in baixo for parte in item.get("proibe", []))


def passa(item: dict, resposta: str) -> bool:
    tipo = item["tipo"]
    gold = item["resposta"]
    if tipo == "fato":
        return fato(resposta, item)
    if tipo == "uma_frase":
        chave = gold.rstrip(".").split()[-1]
        return uma_frase(resposta) and chave.lower() in resposta.lower()
    if tipo == "nao_inventar":
        return nao_inventa(resposta)
    if tipo == "numero":
        return so_numero(resposta, str(item["numero"]))
    if tipo == "curto":
        uteis = [p.lower().strip(".,") for p in gold.split() if len(p) > 3]
        return curto(resposta, int(item["limite"])) and any(p in resposta.lower() for p in uteis)
    return False


def carregar(caminho: Path, device: torch.device) -> Modelo:
    cfg = Config()
    modelo = Modelo(cfg).to(device)
    salvo = torch.load(caminho, map_location=device, weights_only=False)
    modelo.load_state_dict(salvo["modelo"])
    modelo.eval()
    return modelo


@torch.no_grad()
def responder(modelo: Modelo, tok: Tokenizer, item: dict, device: torch.device) -> str:
    ids = encerrar_fim(tok, tok.encode(prefixo(item)).ids)
    idx = torch.tensor([ids], device=device)
    fim = tok.token_to_id("<fim>")
    for _ in range(96):
        logits = modelo(idx[:, -modelo.cfg.seq :])[:, -1, :]
        prox = int(logits.argmax(dim=-1).item())
        idx = torch.cat((idx, torch.tensor([[prox]], device=device)), dim=1)
        if prox == fim:
            break
        texto = tok.decode(idx[0, len(ids) :].tolist())
        if "\n" in texto:
            break
    return tok.decode(idx[0, len(ids) :].tolist()).split("\n", 1)[0].strip()


def avaliar_conjunto(nome_conjunto: str, itens: list[dict], modelos: dict, tok: Tokenizer, device: torch.device) -> dict:
    totais = {nome: {} for nome in modelos}
    exemplos = []
    print(f"== {nome_conjunto} ==", flush=True)
    for item in itens:
        linha = {"tipo": item["tipo"], "instrucao": item["instrucao"], "contexto": item.get("contexto", "")}
        for nome, modelo in modelos.items():
            resposta = responder(modelo, tok, item, device)
            ok = passa(item, resposta)
            totais[nome].setdefault(item["tipo"], [0, 0])
            totais[nome][item["tipo"]][1] += 1
            totais[nome][item["tipo"]][0] += int(ok)
            linha[nome] = {"resposta": resposta, "passa": ok}
        exemplos.append(linha)
        print(item["tipo"], linha["pretreino"]["passa"], linha["ajuste"]["passa"], linha["ajuste"]["resposta"], flush=True)
    for nome, tipos in totais.items():
        acertos = sum(v[0] for v in tipos.values())
        provas = sum(v[1] for v in tipos.values())
        print(f"{nome_conjunto} {nome} {acertos}/{provas}", flush=True)
        for tipo, (ok, n) in tipos.items():
            print(f"  {tipo} {ok}/{n}", flush=True)
    return {"totais": totais, "exemplos": exemplos}


def ler_jsonl(caminho: Path) -> list[dict]:
    return [json.loads(linha) for linha in caminho.read_text(encoding="utf-8").splitlines() if linha.strip()]


def main() -> None:
    device = torch.device("cuda")
    tok = Tokenizer.from_file(str(RAIZ / "tokenizer.json"))
    modelos = {
        "pretreino": carregar(RAIZ / "checkpoints" / "ciclo1-longo.pt", device),
        "ajuste": carregar(RAIZ / "checkpoints" / "ciclo1-digimob.pt", device),
    }
    pasta = RAIZ / "instrucao"
    resumo = {
        "aceite": avaliar_conjunto("aceite", ler_jsonl(pasta / "aceite.jsonl"), modelos, tok, device),
        "geral": avaliar_conjunto("geral", ler_jsonl(pasta / "avaliacao.jsonl"), modelos, tok, device),
    }
    destino = RAIZ / "checkpoints" / "avaliacao-instrucao.json"
    destino.write_text(json.dumps(resumo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
