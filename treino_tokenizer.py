"""Treina o tokenizer neste corpus. O vocabulário resultante é nosso."""

from __future__ import annotations

import argparse
from pathlib import Path

from tokenizers import Tokenizer
from tokenizers.decoders import ByteLevel as ByteLevelDecoder
from tokenizers.models import BPE
from tokenizers.pre_tokenizers import ByteLevel
from tokenizers.processors import TemplateProcessing
from tokenizers.trainers import BpeTrainer


def treinar(textos: list[Path], destino: Path, vocab: int) -> None:
    tokenizer = Tokenizer(BPE(unk_token="<unk>"))
    tokenizer.pre_tokenizer = ByteLevel(add_prefix_space=False)
    tokenizer.decoder = ByteLevelDecoder()
    trainer = BpeTrainer(
        vocab_size=vocab,
        special_tokens=["<pad>", "<fim>", "<unk>"],
        min_frequency=2,
    )
    tokenizer.train([str(p) for p in textos], trainer)
    tokenizer.post_processor = TemplateProcessing(
        single="$A <fim>",
        special_tokens=[("<fim>", tokenizer.token_to_id("<fim>"))],
    )
    destino.parent.mkdir(parents=True, exist_ok=True)
    tokenizer.save(str(destino))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--destino", type=Path, default=Path("tokenizer.json"))
    parser.add_argument("--vocab", type=int, default=8192)
    args = parser.parse_args()
    arquivos = sorted(p for p in args.corpus.rglob("*.txt") if p.is_file())
    if not arquivos:
        raise SystemExit(f"nenhum .txt em {args.corpus}")
    treinar(arquivos, args.destino, args.vocab)
    print(f"tokenizer {args.destino} vocab={args.vocab} arquivos={len(arquivos)}")


if __name__ == "__main__":
    main()
