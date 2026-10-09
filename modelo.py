"""Decoder pequeno, pesos nascem aleatórios. Não carrega checkpoint de terceiro."""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class Config:
    vocab: int = 8192
    d_model: int = 768
    n_camadas: int = 16
    n_cabecas: int = 12
    n_cabecas_kv: int = 4
    ffn: int = 2048
    seq: int = 512
    rope_base: float = 10000.0
    eps: float = 1e-5


class RMSNorm(nn.Module):
    def __init__(self, d: int, eps: float) -> None:
        super().__init__()
        self.peso = nn.Parameter(torch.ones(d))
        self.eps = eps

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        escala = x.float().pow(2).mean(-1, keepdim=True).add(self.eps).rsqrt()
        return (x.float() * escala).to(x.dtype) * self.peso


def _rope(x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> torch.Tensor:
    d = x.shape[-1] // 2
    x1, x2 = x[..., :d], x[..., d:]
    return torch.cat((x1 * cos - x2 * sin, x1 * sin + x2 * cos), dim=-1)


class Atencao(nn.Module):
    def __init__(self, cfg: Config) -> None:
        super().__init__()
        if cfg.d_model % cfg.n_cabecas != 0:
            raise ValueError("d_model tem de dividir pelas cabeças")
        if cfg.n_cabecas % cfg.n_cabecas_kv != 0:
            raise ValueError("cabeças de query têm de ser múltiplo das de key/value")
        self.n_cabecas = cfg.n_cabecas
        self.n_kv = cfg.n_cabecas_kv
        self.dim = cfg.d_model // cfg.n_cabecas
        self.q = nn.Linear(cfg.d_model, cfg.n_cabecas * self.dim, bias=False)
        self.k = nn.Linear(cfg.d_model, cfg.n_cabecas_kv * self.dim, bias=False)
        self.v = nn.Linear(cfg.d_model, cfg.n_cabecas_kv * self.dim, bias=False)
        self.o = nn.Linear(cfg.n_cabecas * self.dim, cfg.d_model, bias=False)

    def forward(self, x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> torch.Tensor:
        b, t, _ = x.shape
        q = self.q(x).view(b, t, self.n_cabecas, self.dim).transpose(1, 2)
        k = self.k(x).view(b, t, self.n_kv, self.dim).transpose(1, 2)
        v = self.v(x).view(b, t, self.n_kv, self.dim).transpose(1, 2)
        q = _rope(q, cos, sin)
        k = _rope(k, cos, sin)
        if self.n_cabecas != self.n_kv:
            rep = self.n_cabecas // self.n_kv
            k = k.repeat_interleave(rep, dim=1)
            v = v.repeat_interleave(rep, dim=1)
        y = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        y = y.transpose(1, 2).contiguous().view(b, t, -1)
        return self.o(y)


class Bloco(nn.Module):
    def __init__(self, cfg: Config) -> None:
        super().__init__()
        self.norm1 = RMSNorm(cfg.d_model, cfg.eps)
        self.attn = Atencao(cfg)
        self.norm2 = RMSNorm(cfg.d_model, cfg.eps)
        self.porta = nn.Linear(cfg.d_model, cfg.ffn, bias=False)
        self.sobe = nn.Linear(cfg.d_model, cfg.ffn, bias=False)
        self.desce = nn.Linear(cfg.ffn, cfg.d_model, bias=False)

    def forward(self, x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> torch.Tensor:
        x = x + self.attn(self.norm1(x), cos, sin)
        h = self.norm2(x)
        return x + self.desce(F.silu(self.porta(h)) * self.sobe(h))


class Modelo(nn.Module):
    def __init__(self, cfg: Config) -> None:
        super().__init__()
        self.cfg = cfg
        self.emb = nn.Embedding(cfg.vocab, cfg.d_model)
        self.blocos = nn.ModuleList(Bloco(cfg) for _ in range(cfg.n_camadas))
        self.norm = RMSNorm(cfg.d_model, cfg.eps)
        self.saida = nn.Linear(cfg.d_model, cfg.vocab, bias=False)
        self.saida.weight = self.emb.weight
        ang = self._angulos(cfg.seq, cfg.d_model // cfg.n_cabecas, cfg.rope_base)
        self.register_buffer("cos", torch.cos(ang)[None, None, :, :], persistent=False)
        self.register_buffer("sin", torch.sin(ang)[None, None, :, :], persistent=False)
        self.apply(self._iniciar)

    @staticmethod
    def _angulos(seq: int, dim: int, base: float) -> torch.Tensor:
        theta = base ** (-torch.arange(0, dim, 2).float() / dim)
        pos = torch.arange(seq).float()
        return torch.outer(pos, theta)

    @staticmethod
    def _iniciar(modulo: nn.Module) -> None:
        if isinstance(modulo, nn.Linear):
            nn.init.normal_(modulo.weight, mean=0.0, std=0.02)
        elif isinstance(modulo, nn.Embedding):
            nn.init.normal_(modulo.weight, mean=0.0, std=0.02)

    def n_parametros(self) -> int:
        return sum(p.numel() for p in self.parameters())

    def forward(self, idx: torch.Tensor) -> torch.Tensor:
        t = idx.shape[1]
        x = self.emb(idx)
        cos = self.cos[:, :, :t, :].to(x.dtype)
        sin = self.sin[:, :, :t, :].to(x.dtype)
        for bloco in self.blocos:
            if self.training:
                x = torch.utils.checkpoint.checkpoint(bloco, x, cos, sin, use_reentrant=False)
            else:
                x = bloco(x, cos, sin)
        return self.saida(self.norm(x))

    @torch.no_grad()
    def gerar(self, idx: torch.Tensor, max_novos: int, temperatura: float = 0.2) -> torch.Tensor:
        self.eval()
        for _ in range(max_novos):
            ctx = idx[:, -self.cfg.seq :]
            logits = self(ctx)[:, -1, :]
            if temperatura <= 0:
                prox = logits.argmax(dim=-1, keepdim=True)
            else:
                probs = torch.softmax(logits.float() / temperatura, dim=-1)
                prox = torch.multinomial(probs, num_samples=1)
            idx = torch.cat((idx, prox), dim=1)
        return idx
