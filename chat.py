"""Uma pergunta, o trecho do material, a resposta. Temperatura zero."""

from __future__ import annotations

import torch
from tokenizers import Tokenizer

from avaliar import responder
from modelo import Config, Modelo
from rag import RAIZ, garantir, montar_contexto


def main() -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tok = Tokenizer.from_file(str(RAIZ / "tokenizer.json"))
    modelo = Modelo(Config()).to(device)
    caminho = RAIZ / "checkpoints" / "ciclo1-rag.pt"
    salvo = torch.load(caminho, map_location=device, weights_only=False)
    modelo.load_state_dict(salvo["modelo"])
    modelo.eval()
    print("Digite a pergunta. Linha vazia encerra.", flush=True)
    while True:
        try:
            texto = input("> ").strip()
        except EOFError:
            break
        if not texto:
            break
        contexto, _titulo = montar_contexto(texto)
        saida = responder(modelo, tok, {"instrucao": texto, "contexto": contexto}, device)
        print(garantir(saida, contexto), flush=True)


if __name__ == "__main__":
    main()
