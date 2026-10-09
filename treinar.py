"""Pré-treino de próximo token. Os pesos começam aleatórios."""

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


def carregar_ids(corpus: Path, tokenizer: Tokenizer) -> torch.Tensor:
    pedacos: list[int] = []
    arquivos = sorted(p for p in corpus.rglob("*.txt") if "provas" not in p.parts)
    if not arquivos:
        raise SystemExit(f"nenhum texto em {corpus}")
    for caminho in arquivos:
        texto = caminho.read_text(encoding="utf-8", errors="replace")
        pedacos.extend(tokenizer.encode(texto).ids)
    if len(pedacos) < 1024:
        raise SystemExit("corpus curto demais para um passo")
    return torch.tensor(pedacos, dtype=torch.long)


def lote(ids: torch.Tensor, seq: int, batch: int, device: torch.device) -> tuple[torch.Tensor, torch.Tensor]:
    limite = ids.numel() - seq - 1
    inicio = torch.randint(0, limite, (batch,))
    x = torch.stack([ids[i : i + seq] for i in inicio])
    y = torch.stack([ids[i + 1 : i + seq + 1] for i in inicio])
    return x.to(device), y.to(device)


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--passos", type=int, default=200)
    parser.add_argument("--batch", type=int, default=4)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--corpus", type=Path, default=RAIZ / "corpus")
    parser.add_argument("--tokenizer", type=Path, default=RAIZ / "tokenizer.json")
    parser.add_argument("--saida", type=Path, default=RAIZ / "checkpoints" / "ciclo1-passo.pt")
    parser.add_argument("--continuar", type=Path, default=None)
    args = parser.parse_args()

    if not torch.cuda.is_available():
        raise SystemExit("CUDA não está visível. Este ciclo treina na GPU.")

    cfg = Config()
    tokenizer = Tokenizer.from_file(str(args.tokenizer))
    ids = carregar_ids(args.corpus, tokenizer)
    device = torch.device("cuda")
    modelo = Modelo(cfg).to(device)
    ja_feitos = 0
    if args.continuar is not None:
        salvo = torch.load(args.continuar, map_location=device, weights_only=False)
        modelo.load_state_dict(salvo["modelo"])
        ja_feitos = int(salvo.get("passos", 0))
    otim = torch.optim.AdamW(modelo.parameters(), lr=args.lr, betas=(0.9, 0.95), weight_decay=0.1)
    n = modelo.n_parametros()
    print(f"parametros={n} tokens={ids.numel()} gpu={torch.cuda.get_device_name(0)}", flush=True)

    modelo.train()
    perda_ultima = None
    t0 = time.time()
    for passo in range(1, args.passos + 1):
        x, y = lote(ids, cfg.seq, args.batch, device)
        otim.zero_grad(set_to_none=True)
        with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
            logits = modelo(x)
            perda = torch.nn.functional.cross_entropy(logits.flatten(0, 1), y.flatten())
        perda.backward()
        torch.nn.utils.clip_grad_norm_(modelo.parameters(), 1.0)
        otim.step()
        perda_ultima = float(perda.item())
        if passo == 1 or passo % 20 == 0 or passo == args.passos:
            mem = torch.cuda.max_memory_allocated() / (1024**2)
            print(f"passo={passo} perda={perda_ultima:.4f} vram_max_mib={mem:.0f}", flush=True)

    args.saida.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "modelo": modelo.state_dict(),
            "config": cfg.__dict__,
            "passos": ja_feitos + args.passos,
            "perda": perda_ultima,
            "tokens_corpus": int(ids.numel()),
            "parametros": n,
        },
        args.saida,
    )
    resumo = {
        "arquivo": str(args.saida),
        "sha256": sha256(args.saida),
        "passos": ja_feitos + args.passos,
        "perda": perda_ultima,
        "parametros": n,
        "tokens_corpus": int(ids.numel()),
        "segundos": round(time.time() - t0, 1),
        "gpu": torch.cuda.get_device_name(0),
        "vram_max_mib": round(torch.cuda.max_memory_allocated() / (1024**2), 1),
    }
    ficha = args.saida.with_suffix(".json")
    ficha.write_text(json.dumps(resumo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(resumo, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
