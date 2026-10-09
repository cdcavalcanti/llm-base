"""Uma linha de entrada, uma resposta do ajuste. Temperatura zero."""

from __future__ import annotations

import torch
from tokenizers import Tokenizer

from modelo import Config, Modelo
from treino_instrucao import encerrar_fim

RAIZ = __import__("pathlib").Path(__file__).resolve().parent


def main() -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tok = Tokenizer.from_file(str(RAIZ / "tokenizer.json"))
    cfg = Config()
    modelo = Modelo(cfg).to(device)
    salvo = torch.load(RAIZ / "checkpoints" / "ciclo1-instrucao.pt", map_location=device, weights_only=False)
    modelo.load_state_dict(salvo["modelo"])
    modelo.eval()
    fim = tok.token_to_id("<fim>")
    print("Digite a instrução. Linha vazia encerra.", flush=True)
    while True:
        try:
            texto = input("> ").strip()
        except EOFError:
            break
        if not texto:
            break
        prompt = f"Instrução: {texto}\nResposta: "
        ids = encerrar_fim(tok, tok.encode(prompt).ids)
        idx = torch.tensor([ids], device=device)
        with torch.no_grad():
            for _ in range(48):
                prox = int(modelo(idx[:, -cfg.seq :])[:, -1, :].argmax(dim=-1).item())
                idx = torch.cat((idx, torch.tensor([[prox]], device=device)), dim=1)
                if prox == fim:
                    break
                if "\n" in tok.decode(idx[0, len(ids) :].tolist()):
                    break
        print(tok.decode(idx[0, len(ids) :].tolist()).split("\n", 1)[0].strip(), flush=True)


if __name__ == "__main__":
    main()
