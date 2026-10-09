"""Pares de instrução. O conjunto geral não repete o texto do treino."""

from __future__ import annotations

import json
import random
from pathlib import Path

# artigo, país, capital
PAISES = [
    ("do", "Brasil", "Brasília"),
    ("de", "Portugal", "Lisboa"),
    ("da", "Argentina", "Buenos Aires"),
    ("do", "Chile", "Santiago"),
    ("do", "Uruguai", "Montevidéu"),
    ("do", "Paraguai", "Assunção"),
    ("do", "Peru", "Lima"),
    ("da", "Colômbia", "Bogotá"),
    ("do", "México", "Cidade do México"),
    ("do", "Canadá", "Ottawa"),
    ("da", "França", "Paris"),
    ("da", "Espanha", "Madrid"),
    ("da", "Itália", "Roma"),
    ("da", "Alemanha", "Berlim"),
    ("do", "Japão", "Tóquio"),
    ("da", "China", "Pequim"),
    ("da", "Índia", "Nova Délhi"),
    ("do", "Egito", "Cairo"),
    ("de", "Angola", "Luanda"),
    ("de", "Moçambique", "Maputo"),
    ("da", "Austrália", "Camberra"),
    ("da", "Suécia", "Estocolmo"),
    ("da", "Noruega", "Oslo"),
    ("da", "Grécia", "Atenas"),
    ("da", "Polônia", "Varsóvia"),
    ("da", "Coreia do Sul", "Seul"),
    ("da", "África do Sul", "Pretória"),
    ("de", "Marrocos", "Rabat"),
    ("da", "Nigéria", "Abuja"),
    ("do", "Quênia", "Nairóbi"),
    ("da", "Irlanda", "Dublin"),
    ("dos", "Estados Unidos", "Washington"),
    ("do", "Reino Unido", "Londres"),
    ("da", "Rússia", "Moscou"),
]

GERAL_PAISES = [
    ("de", "Cuba", "Havana"),
    ("da", "Finlândia", "Helsinque"),
    ("do", "Vietnã", "Hanói"),
    ("da", "Nova Zelândia", "Wellington"),
    ("do", "Irã", "Teerã"),
    ("da", "Ucrânia", "Kiev"),
    ("da", "Islândia", "Reiquiavique"),
    ("da", "Tailândia", "Bangkok"),
]

CIDADES = [
    "Campinas", "Santos", "Recife", "Curitiba", "Belém", "Manaus",
    "Florianópolis", "João Pessoa", "Natal", "Cuiabá", "Vitória", "Londrina",
]
GERAL_CIDADES = ["Ouro Preto", "Petrópolis", "Blumenau", "Ribeirão Preto"]

CAMPOS = [
    ("o valor da multa", "o valor da multa"),
    ("o desconto", "o desconto"),
    ("o telefone", "o telefone"),
    ("o prazo", "o prazo"),
    ("a área", "a área"),
    ("o número do contrato", "o número do contrato"),
    ("a data de visita", "a data de visita"),
]
GERAL_CAMPOS = [
    ("o IPTU", "o IPTU"),
    ("a matrícula", "a matrícula"),
    ("o CRECI", "o CRECI"),
    ("o laudêmio", "o laudêmio"),
]

CONCEITOS = [
    ("o lote", "Um lote é um terreno em um empreendimento."),
    ("o boleto", "Um boleto é um documento de cobrança."),
    ("o corretor", "Um corretor apresenta o imóvel ao cliente."),
    ("a parcela", "Uma parcela é uma parte do pagamento."),
    ("o imóvel", "Um imóvel é uma casa, um apartamento ou um terreno."),
    ("a proposta", "Uma proposta é uma oferta de compra."),
    ("a entrada", "A entrada é o valor pago no início."),
    ("a planta", "A planta mostra as medidas do imóvel."),
    ("o contrato", "Um contrato registra o que foi combinado."),
    ("o recibo", "Um recibo confirma um pagamento."),
    ("o adaptador LoRA", "Um adaptador LoRA é um ajuste pequeno ao lado do modelo."),
]
GERAL_CONCEITOS = [
    ("a escritura", "A escritura formaliza a transferência do imóvel."),
    ("o alvará", "O alvará autoriza uma obra ou uma atividade."),
    ("o habite-se", "O habite-se libera o uso do imóvel."),
]


def _milhar(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _item(tipo: str, instrucao: str, contexto: str, resposta: str, **extra: object) -> dict:
    item = {"tipo": tipo, "instrucao": instrucao, "contexto": contexto, "resposta": resposta}
    item.update(extra)
    return item


def _capital(artigo: str, pais: str, capital: str) -> dict:
    return _item(
        "uma_frase",
        f"Responda em uma frase: qual é a capital {artigo} {pais}?",
        "",
        f"A capital {artigo} {pais} é {capital}.",
    )


def _ausente(pergunta: str, campo: str, cidade: str) -> dict:
    return _item(
        "nao_inventar",
        pergunta,
        f"O texto cita apenas a cidade de {cidade}.",
        f"{campo[:1].upper()}{campo[1:]} não está no contexto.",
    )


def _numero(rotulo: str, n: int) -> dict:
    return _item(
        "numero",
        f"Quantos {rotulo} o relatório fechou? Responda só o número.",
        f"O relatório fechou em {_milhar(n)} {rotulo}.",
        _milhar(n),
        numero=str(n),
    )


def _curto(conceito: str, definicao: str, limite: int) -> dict:
    return _item(
        "curto",
        f"Em no máximo {limite} palavras, diga o que é {conceito}.",
        "",
        definicao,
        limite=limite,
    )


def gerar_treino(rng: random.Random) -> list[dict]:
    saida: list[dict] = []
    for _ in range(8):
        for artigo, pais, capital in PAISES:
            saida.append(_capital(artigo, pais, capital))
    for _ in range(30):
        for pergunta, campo in CAMPOS:
            saida.append(_ausente(f"Qual é {pergunta}?", campo, rng.choice(CIDADES)))
        for rotulo in ("chamados", "lotes", "visitas", "contratos", "cobranças"):
            saida.append(_numero(rotulo, rng.randint(1000, 99999)))
        saida.append(_numero("chamados", 1247))
        for conceito, definicao in CONCEITOS:
            limite = 15 if len(definicao.split()) > 10 else 12
            saida.append(_curto(conceito, definicao, limite))
    for _ in range(400):
        nome = rng.choice(["Helena", "Miguel", "Lívia", "Caio", "Nina", "Otto", "Lara", "Davi"])
        nome = f"{nome} {rng.randint(10, 99)}"
        saida.append(
            _item(
                "copiar",
                "Repita somente o nome citado.",
                f"O nome citado é {nome}.",
                nome,
            )
        )
    return saida


def gerar_geral(rng: random.Random) -> list[dict]:
    saida: list[dict] = []
    for artigo, pais, capital in GERAL_PAISES:
        saida.append(_capital(artigo, pais, capital))
    for pergunta, campo in GERAL_CAMPOS:
        saida.append(_ausente(f"Qual é {pergunta}?", campo, rng.choice(GERAL_CIDADES)))
    for rotulo, n in (("chamados", 4288), ("visitas", 91504), ("contratos", 2703), ("lotes", 66012)):
        saida.append(_numero(rotulo, n))
    for conceito, definicao in GERAL_CONCEITOS:
        saida.append(_curto(conceito, definicao, 12))
    return saida


def aceite() -> list[dict]:
    return [
        _capital("do", "Brasil", "Brasília"),
        _ausente("Qual é o valor da multa?", "o valor da multa", "Campinas"),
        _numero("chamados", 1247),
        _curto(
            "o adaptador LoRA",
            "Um adaptador LoRA é um ajuste pequeno ao lado do modelo.",
            15,
        ),
    ]


def _sem_vazamento(treino: list[dict], bloqueio: list[dict]) -> list[dict]:
    proibidos = {(item["instrucao"], item["contexto"], item["resposta"]) for item in bloqueio}
    return [item for item in treino if (item["instrucao"], item["contexto"], item["resposta"]) not in proibidos]


def gravar(destino: Path) -> None:
    rng = random.Random(11)
    geral = gerar_geral(rng)
    treino = _sem_vazamento(gerar_treino(rng), geral)
    destino.mkdir(parents=True, exist_ok=True)
    for nome, itens in (("treino.jsonl", treino), ("avaliacao.jsonl", geral), ("aceite.jsonl", aceite())):
        caminho = destino / nome
        caminho.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in itens), encoding="utf-8")
        print(nome, len(itens))


if __name__ == "__main__":
    gravar(Path(__file__).resolve().parent / "instrucao")
