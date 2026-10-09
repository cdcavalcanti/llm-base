"""Ajuste de instrução em cima do pré-treino. A perda só olha a resposta."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import torch
from tokenizers import Tokenizer

from modelo import Config, Modelo

RAIZ = Path(__file__).resolve().parent


def encerrar_fim(tok: Tokenizer, ids: list[int]) -> list[int]:
    fim = tok.token_to_id("<fim>")
    if fim is not None and ids and ids[-1] == fim:
        return ids[:-1]
    return ids


def montar(tok: Tokenizer, item: dict, seq: int) -> tuple[list[int], list[int]] | None:
    prefixo = f"Instrução: {item['instrucao']}\n"
    if item.get("contexto"):
        prefixo += f"Contexto: {item['contexto']}\n"
    prefixo += "Resposta: "
    alvo = item["resposta"].strip() + "\n"
    ids_prefixo = encerrar_fim(tok, tok.encode(prefixo).ids)
    ids_resposta = encerrar_fim(tok, tok.encode(alvo).ids)
    ids = ids_prefixo + ids_resposta
    n_prefixo = len(ids_prefixo)
    if len(ids) > seq:
        corte = len(ids) - seq
        ids = ids[corte:]
        n_prefixo = max(0, n_prefixo - corte)
    if n_prefixo >= len(ids):
        return None
    # logits na posição t preveem o token t+1
    rotulos = [-100] * max(0, n_prefixo - 1) + ids[n_prefixo:]
    entrada = ids[:-1]
    if len(rotulos) != len(entrada) or not any(v != -100 for v in rotulos):
        return None
    return entrada, rotulos


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dados", type=Path, default=RAIZ / "instrucao" / "treino.jsonl")
    parser.add_argument("--continuar", type=Path, default=RAIZ / "checkpoints" / "ciclo1-longo.pt")
    parser.add_argument("--saida", type=Path, default=RAIZ / "checkpoints" / "ciclo1-instrucao.pt")
    parser.add_argument("--epocas", type=int, default=3)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--lr", type=float, default=8e-5)
    args = parser.parse_args()

    if not torch.cuda.is_available():
        raise SystemExit("CUDA não está visível.")

    tok = Tokenizer.from_file(str(RAIZ / "tokenizer.json"))
    cfg = Config()
    itens = [json.loads(linha) for linha in args.dados.read_text(encoding="utf-8").splitlines() if linha.strip()]
    pares = [par for item in itens if (par := montar(tok, item, cfg.seq))]
    if len(pares) < len(itens):
        print(f"descartados={len(itens) - len(pares)}", flush=True)
    print(f"pares={len(pares)}", flush=True)

    device = torch.device("cuda")
    modelo = Modelo(cfg).to(device)
    salvo = torch.load(args.continuar, map_location=device, weights_only=False)
    modelo.load_state_dict(salvo["modelo"])
    otim = torch.optim.AdamW(modelo.parameters(), lr=args.lr, betas=(0.9, 0.95), weight_decay=0.01)
    modelo.train()
    perda_ultima = None
    t0 = time.time()
    passo = 0
    for epoca in range(1, args.epocas + 1):
        ordem = torch.randperm(len(pares)).tolist()
        for inicio in range(0, len(ordem), args.batch):
            grupo = [pares[i] for i in ordem[inicio : inicio + args.batch]]
            tamanho = max(len(ids) for ids, _ in grupo)
            x = torch.full((len(grupo), tamanho), tok.token_to_id("<pad>"), dtype=torch.long)
            y = torch.full((len(grupo), tamanho), -100, dtype=torch.long)
            for i, (ids, labels) in enumerate(grupo):
                x[i, : len(ids)] = torch.tensor(ids)
                y[i, : len(labels)] = torch.tensor(labels)
            x, y = x.to(device), y.to(device)
            otim.zero_grad(set_to_none=True)
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                logits = modelo(x)
                perda = torch.nn.functional.cross_entropy(
                    logits.flatten(0, 1),
                    y.flatten(),
                    ignore_index=-100,
                )
            perda.backward()
            torch.nn.utils.clip_grad_norm_(modelo.parameters(), 1.0)
            otim.step()
            passo += 1
            perda_ultima = float(perda.item())
            if passo == 1 or passo % 50 == 0:
                print(f"epoca={epoca} passo={passo} perda={perda_ultima:.4f}", flush=True)
        print(f"epoca={epoca} perda={perda_ultima:.4f}", flush=True)

    args.saida.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "modelo": modelo.state_dict(),
            "config": cfg.__dict__,
            "base": str(args.continuar),
            "passos_instrucao": passo,
            "perda": perda_ultima,
            "pares": len(pares),
        },
        args.saida,
    )
    resumo = {
        "arquivo": str(args.saida),
        "sha256": sha256(args.saida),
        "passos_instrucao": passo,
        "pares": len(pares),
        "perda": perda_ultima,
        "segundos": round(time.time() - t0, 1),
        "gpu": torch.cuda.get_device_name(0),
    }
    args.saida.with_suffix(".json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(resumo, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
