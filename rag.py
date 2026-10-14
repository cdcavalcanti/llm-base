"""Busca no material da Digimob. Os pesos não guardam esse texto."""

from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
PASTA = RAIZ / "conhecimento"
FORA = "Ainda falta"
MAX_PALAVRAS = 90

SECAO = {
    "primeiro_contato": "Primeiro contato",
    "preco_lote": "Preço de lote",
    "preco_casa": "Preço de casa",
    "juridico": "Jurídico",
    "desconto": "Desconto",
    "entrada_duas": "Entrada em duas vezes",
    "entrada_cartao": "Entrada no cartão",
    "entrada_boleto": "Entrada no boleto",
    "pagamento": "Formas de pagamento",
    "visita_docs": "Visita ao lote",
    "visita_horario": "Visita ao lote",
    "feriado": "Feriado",
    "feriado_excecao": "Exceções de feriado",
    "reserva_dias": "Prazo da reserva",
    "reserva_confirma": "Confirmação da reserva",
    "reserva_sumiu": "Reserva sem retorno",
    "proposta": "Dados da proposta",
    "doc_pdf": "Documento do cliente",
    "doc_lote": "Documento do lote",
    "certidao": "Certidão do lote",
    "doze_dias": "Prazo do contrato",
    "cessao_quando": "Quando cabe cessão",
    "cessao_prazo": "Prazo da cessão",
    "cessao_b1": "Taxa de cessão do B1-22",
    "distrato_op": "Distrato da operação",
    "distrato_aceite": "Aceite do distrato",
    "pos_venda": "Depois de quitar",
    "iptu": "IPTU no nome",
    "b1_onde": "Onde fica o B1-22",
    "b1_preco": "Preço do B1-22",
    "b1_sinal": "Sinal do B1-22",
    "b1_parcelas": "Parcelas do B1-22",
    "b1_ipca": "Correção do B1-22",
    "b1_atraso": "Atraso do B1-22",
    "b1_habite": "Habite-se",
    "b1_escritura": "Escritura do B1-22",
    "b1_infra": "Infraestrutura",
    "b1_desfaz": "Desfazimento do B1-22",
    "lote_ausente": "Preço ausente",
    "crm": "Funil no CRM",
}

APELIDOS = {
    "Primeiro contato": "oi ola boa noite bom dia anuncio saber mais",
    "Preço de lote": "lote terreno responde",
    "Preço de casa": "casa vendem vender",
    "Jurídico": "juridico juridica advogado",
    "Desconto": "desconto abatimento autoriza autorizar felipe gerente",
    "Entrada em duas vezes": "parcelar sinal vez vezes entrada inicio",
    "Entrada no cartão": "cartao credito caro",
    "Entrada no boleto": "boleto ultima",
    "Formas de pagamento": "avista formas aceita",
    "Visita ao lote": "visitar visita sabado manha documento documentos levar",
    "Feriado": "feriado agenda",
    "Exceções de feriado": "excecao excecoes lista liberado",
    "Prazo da reserva": "segurar seguram segura tempo prazo dura",
    "Confirmação da reserva": "confirmar confirma pagamento",
    "Reserva sem retorno": "sumir sumiu cancelar cancelam",
    "Dados da proposta": "proposta dados campos cpf rg profissao",
    "Documento do cliente": "pdf arquivo",
    "Documento do lote": "assinatura entregue",
    "Certidão do lote": "certidao",
    "Prazo do contrato": "preenchimento vias",
    "Quando cabe cessão": "irmao passar pagando transferencia",
    "Prazo da cessão": "assinam dono",
    "Taxa de cessão do B1-22": "taxa percentual",
    "Distrato da operação": "desistir devolvem devolve volta",
    "Aceite do distrato": "aceitar caixa consultar automatica",
    "Depois de quitar": "quitar quitou quitacao registrar registro forum tbi cartorio",
    "IPTU no nome": "iptu nome",
    "Onde fica o B1-22": "arcoverde investir teresopolis onde fica endereco",
    "Preço do B1-22": "custa reais",
    "Sinal do B1-22": "ato",
    "Parcelas do B1-22": "prestacoes saldo",
    "Correção do B1-22": "ipca correcao reajuste indice",
    "Atraso do B1-22": "atraso mora multa encargos",
    "Habite-se": "morar construir liberar prefeitura",
    "Escritura do B1-22": "itbi",
    "Infraestrutura": "infraestrutura agua luz meiofio",
    "Desfazimento do B1-22": "desfazimento fruicao comissao",
    "Preço ausente": "",
    "Funil no CRM": "funil cobranca monitoria crm equipe suporte",
}

PARA = {
    "á": "a", "à": "a", "ã": "a", "â": "a",
    "é": "e", "ê": "e",
    "í": "i",
    "ó": "o", "ô": "o", "õ": "o",
    "ú": "u",
    "ç": "c",
}
PARADA = {
    "a", "o", "e", "de", "da", "do", "das", "dos", "em", "um", "uma", "para", "com",
    "que", "no", "na", "os", "as", "se", "por", "ao", "eu", "me", "meu", "minha",
    "voce", "voces", "tem", "como", "qual", "quais", "quanto", "quando", "onde",
    "isso", "essa", "esse", "nao", "sim", "mais", "ja", "ou", "ser", "estar",
}


@dataclass(frozen=True)
class Trecho:
    titulo: str
    texto: str

    def busca(self) -> str:
        return f"{self.titulo}\n{self.texto}\n{APELIDOS.get(self.titulo, '')}"


def _tokens(texto: str) -> list[str]:
    baixo = texto.lower()
    for origem, destino in PARA.items():
        baixo = baixo.replace(origem, destino)
    return [t for t in re.findall(r"[a-z0-9]+", baixo) if t not in PARADA and len(t) > 1]


def _fatiar(titulo: str, corpo: str) -> list[Trecho]:
    texto = " ".join(corpo.split())
    if not texto:
        return []
    return [Trecho(titulo, texto)]


def carregar(pasta: Path = PASTA) -> list[Trecho]:
    trechos: list[Trecho] = []
    for caminho in sorted(pasta.glob("*.md")):
        partes = re.split(r"\n(?=## )", caminho.read_text(encoding="utf-8"))
        for parte in partes:
            if not parte.startswith("## "):
                continue
            titulo, _, corpo = parte.partition("\n")
            titulo = titulo.removeprefix("## ").strip()
            if titulo == FORA or not corpo.strip():
                continue
            trechos.extend(_fatiar(titulo, corpo.strip()))
    return trechos


PRECO = {"preco", "custa", "valor", "reais", "pedida", "cobram"}
PARCELA = {"parcelar", "sinal", "entrada", "boleto", "cartao", "vezes"}
AUSENTE = "Esse preço não está no material."
LOTE_OK = {"b1", "22", "teresopolis"}


def _bate(consulta: set[str], raizes: tuple[str, ...]) -> bool:
    for tok in consulta:
        for raiz in raizes:
            if len(raiz) <= 3:
                if tok == raiz:
                    return True
            elif tok.startswith(raiz):
                return True
    return False


def _quadra_alheia(pergunta: str) -> bool:
    baixo = pergunta.lower()
    for origem, destino in PARA.items():
        baixo = baixo.replace(origem, destino)
    achou = re.search(r"quadra\s+([a-z0-9]+)", baixo)
    return bool(achou) and achou.group(1) not in {"b", "b1"}


INCIDENTAL = {"1", "2", "3", "4", "5", "7", "10", "12", "28", "30", "50", "56", "75", "84", "90", "92", "200", "273", "619", "00", "075", "4200"}


def _norm(pergunta: str) -> str:
    baixo = pergunta.lower()
    for origem, destino in PARA.items():
        baixo = baixo.replace(origem, destino)
    return baixo


def _lote_estranho(consulta: set[str]) -> bool:
    if "lote" not in consulta and "quadra" not in consulta:
        return False
    return bool(_numeros(consulta) - LOTE_OK - INCIDENTAL)


def rotear(pergunta: str, consulta: set[str]) -> str | None:
    """Manda a fala para um trecho mesmo quando o vocabulário muda."""
    texto = _norm(pergunta)
    casa = _bate(consulta, ("sobrad", "casa"))
    preco = _bate(consulta, ("prec", "cust", "valor", "reais", "pedid")) or (
        "sai" in consulta and _bate(consulta, ("lote", "terren")) and not _bate(consulta, ("contrat", "escritur", "certid", "cess"))
    )
    lote = bool(consulta & LOTE_OK) or _bate(consulta, ("teresopol",))
    quanto = "quanto" in texto or "quantos" in texto or "quantas" in texto

    if _bate(consulta, ("sobrad",)):
        return "Preço de casa"
    if preco and not casa and (_quadra_alheia(pergunta) or _lote_estranho(consulta)):
        return "AUSENTE"
    if _bate(consulta, ("iptu",)):
        return "IPTU no nome"
    if _bate(consulta, ("jurid", "advog")):
        return "Jurídico"
    if _bate(consulta, ("desf", "fruic", "corretag")):
        return "Desfazimento do B1-22"
    if ("desconto" in consulta or "descontos" in consulta) and (_bate(consulta, ("avista", "tabela", "igpm")) or "vista" in consulta):
        return "Desconto da tabela"
    if "desconto" in consulta or "descontos" in consulta or _bate(consulta, ("chor", "abat", "abaix", "negoci")):
        return "Desconto"
    if _bate(consulta, ("funil", "monitor", "cobranc", "crm")) or (_bate(consulta, ("suport",)) and _bate(consulta, ("equipe",))):
        return "Funil no CRM"
    if "igpm" in consulta or "igp" in consulta or (_bate(consulta, ("tabela",)) and _bate(consulta, ("correc", "corrig", "indice"))):
        return "Correção da tabela"
    if _bate(consulta, ("ipca", "reajust", "correc", "corrig", "indice")):
        return "Correção do B1-22"
    if _bate(consulta, ("atras", "multa", "encarg", "juros")) or "mora" in consulta:
        return "Atraso do B1-22"
    if _bate(consulta, ("habit", "habite")) or (_bate(consulta, ("morar", "muda")) and _bate(consulta, ("prefeit", "habite", "deix"))):
        return "Habite-se"
    if _bate(consulta, ("escritur", "itbi")):
        return "Escritura do B1-22"
    if _bate(consulta, ("esgot", "cardeal")) or (_bate(consulta, ("calcad",)) and _bate(consulta, ("casa",))):
        return "Ruas das casas"
    if _bate(consulta, ("agua", "luz", "energ", "asfalt", "infra", "implant", "melhor", "demarc", "calcament", "ruas")) or "rua" in consulta:
        return "Infraestrutura"
    if _bate(consulta, ("quit", "tbi")) or ("pos" in consulta and "venda" in consulta) or (
        _bate(consulta, ("termin",)) and _bate(consulta, ("paga", "terren"))
    ) or (_bate(consulta, ("ultim",)) and _bate(consulta, ("pag", "parcel", "forum", "cartor", "document", "prestac"))):
        return "Depois de quitar"
    if (_bate(consulta, ("excec",)) and _bate(consulta, ("feriad",))) or (_bate(consulta, ("lista", "liberad")) and _bate(consulta, ("feriad",))):
        return "Exceções de feriado"
    if _bate(consulta, ("feriad",)):
        return "Feriado"
    if _bate(consulta, ("certid",)) or (_bate(consulta, ("propost",)) and _bate(consulta, ("document",)) and _bate(consulta, ("lote",))):
        return "Certidão do lote"
    if _bate(consulta, ("visit", "simul", "marc")) and _bate(consulta, ("casa",)):
        return "Visita das casas"
    if _bate(consulta, ("aluguel", "autonom", "carteir", "filho", "sozinh", "simul", "qualific")) or "minha casa" in texto or "morar bem" in texto:
        return "Qualificação"
    if "investir" in texto and not _bate(consulta, ("lote", "terren", "arcoverd", "teresopol")):
        return "Qualificação"
    if "morar" in texto and _bate(consulta, ("casa", "investir", "quem", "filho")) and not _bate(consulta, ("prefeit", "habite")):
        return "Qualificação"
    if _bate(consulta, ("visit", "conhec", "sabad")) or (
        _bate(consulta, ("papel", "document")) and _bate(consulta, ("leva", "visit", "conhec", "sabad", "manha", "cedo"))
    ):
        return "Visita ao lote"
    if _bate(consulta, ("document",)) and _bate(consulta, ("lote",)):
        return "Documento do lote"
    if "pdf" in consulta or _bate(consulta, ("arquivo", "formato")) or (
        _bate(consulta, ("document", "papel")) and _bate(consulta, ("cliente", "comprad"))
    ):
        return "Documento do cliente"
    if _bate(consulta, ("propost", "ficha")) or (_bate(consulta, ("cpf", "rg")) and _bate(consulta, ("dad", "camp", "ped"))):
        return "Dados da proposta"
    if _bate(consulta, ("contrat",)) and (_bate(consulta, ("vias", "preench")) or ("sai" in consulta and _bate(consulta, ("dias", "boleto", "tempo")))):
        return "Prazo do contrato"
    if _bate(consulta, ("cess",)) and _bate(consulta, ("dias", "prazo", "assin", "chega", "pronto", "papel", "document")):
        return "Prazo da cessão"
    if (_bate(consulta, ("cess",)) and _bate(consulta, ("taxa", "percent", "administr"))) or (
        _bate(consulta, ("transfer",)) and _bate(consulta, ("percent", "taxa"))
    ) or (lote and _bate(consulta, ("cess",)) and _bate(consulta, ("cobr", "prec", "cust", "valor"))):
        return "Taxa de cessão do B1-22"
    if not _bate(consulta, ("boleto", "carne", "cartao", "credit")) and (
        _bate(consulta, ("cess", "irma")) or (_bate(consulta, ("pass", "transfer")) and _bate(consulta, ("paga", "pago", "prestac", "parc")))
    ):
        return "Quando cabe cessão"
    if _bate(consulta, ("distrat", "desist", "arrepend", "devolv")) and _bate(consulta, ("aceit", "obrig", "consult", "caixa", "automat", "sempre", "depend")):
        return "Aceite do distrato"
    if _bate(consulta, ("distrat", "desist", "arrepend")) and _bate(consulta, ("devolv", "lote")) and "sinal" not in consulta:
        return "Aceite do distrato"
    if _bate(consulta, ("arrepend", "desist", "distrat")) or (_bate(consulta, ("sinal",)) and _bate(consulta, ("volt", "devolv"))):
        return "Distrato da operação"
    if _bate(consulta, ("mudo", "sumi", "desaparec", "ghost", "ressusc", "retorno")) or "some" in consulta or (
        _bate(consulta, ("reserv",)) and _bate(consulta, ("respond", "cancel"))
    ):
        return "Reserva sem retorno"
    if _bate(consulta, ("reserv",)) and (_bate(consulta, ("paga", "valer", "trav", "confirm")) or "vale" in consulta):
        return "Confirmação da reserva"
    if _bate(consulta, ("guard", "apart", "segur", "reserv")) and _bate(consulta, ("dias", "tempo", "prazo", "dura")):
        return "Prazo da reserva"
    if lote and _bate(consulta, ("prestac", "saldo")):
        return "Parcelas do B1-22"
    if lote and _bate(consulta, ("parcel",)) and not _bate(consulta, ("entrad", "sinal", "boleto", "cartao", "carne")):
        return "Parcelas do B1-22"
    if lote and _bate(consulta, ("sinal", "entrad", "ato")) and (preco or quanto) and not _bate(consulta, ("parcel", "divid", "boleto", "cartao", "carne", "vezes")) and "vez" not in consulta:
        return "Sinal do B1-22"
    if preco and lote:
        return "Preço do B1-22"
    if _bate(consulta, ("recus", "objec", "continu")) and _bate(consulta, ("entrad", "sinal", "vezes", "cartao", "credit")):
        return "Entrada no cartão"
    if _bate(consulta, ("cartao", "credit")) and not _bate(consulta, ("boleto", "carne")):
        return "Entrada no cartão"
    if _bate(consulta, ("boleto", "carne")):
        return "Entrada no boleto"
    if _bate(consulta, ("sinal", "entrad")) and (_bate(consulta, ("divid", "parcel", "picad", "vezes", "comec")) or "vez" in consulta):
        return "Entrada em duas vezes"
    if _bate(consulta, ("avista", "formas")) or (_bate(consulta, ("lista", "opco")) and _bate(consulta, ("pagament", "paga", "pagar"))):
        return "Formas de pagamento"
    if "pode" in consulta and _bate(consulta, ("paga",)) and not _bate(consulta, ("reserv", "sinal", "entrad", "boleto", "cartao")):
        return "Formas de pagamento"
    if preco and _bate(consulta, ("lote", "terren")):
        return "Preço de lote"
    if _bate(consulta, ("aplic", "invest", "arcoverd", "teresopol", "enderec", "bairro", "metragem", "cidade", "loteament", "tamanh", "situa")) or "onde fica" in texto:
        return "Onde fica o B1-22"
    if lote and consulta <= {"lote", "b1", "22", "quadra", "contrato", "teresopolis"}:
        return "Onde fica o B1-22"
    if _bate(consulta, ("oi", "ola", "eai", "tarde", "noite", "anunc", "explic", "funcion", "inform")) or (
        _bate(consulta, ("atend", "convers", "contato")) and _bate(consulta, ("comec", "oferec", "primeiro"))
    ) or (_bate(consulta, ("primeiro",)) and _bate(consulta, ("contato", "oferec"))):
        return "Primeiro contato"
    return None


def _numeros(tokens: set[str]) -> set[str]:
    return {tok for tok in tokens if any(c.isdigit() for c in tok)}


def _sufixo_lote(codigo: str) -> tuple[str, str]:
    cod = codigo.lower()
    especial = re.match(r"\d+x-(.+)$", cod)
    if especial:
        return "x", especial.group(1)
    quadra, _, resto = cod.partition("-")
    return quadra, resto


def _numero_lote(texto: str) -> str:
    baixo = texto.lower()
    achou = re.match(r"0*(\d+)([a-z]*)$", baixo)
    if not achou:
        return baixo
    return achou.group(1) + achou.group(2)


def _extrair_lote(pergunta: str) -> tuple[str, str] | None:
    texto = _norm(pergunta)
    quadra = re.search(r"quadra\s+([a-z0-9]+)", texto)
    numero = re.search(r"lote\s+([0-9]+[a-z]?)", texto)
    if quadra and numero:
        return quadra.group(1), numero.group(1)
    codigo = re.search(r"\b((?:[a-z]\d?|\d{2}[a-z])-(?:[0-9]+[a-z]?)(?:-[0-9]+[a-z]?)?)\b", texto)
    if not codigo:
        return None
    quadra_codigo, resto = _sufixo_lote(codigo.group(1))
    return quadra_codigo, resto.split("-")[-1]


def _lote_da_tabela(codigo: str, quadra: str, numero: str) -> bool:
    quadra_codigo, resto = _sufixo_lote(codigo)
    if quadra_codigo != quadra.lower():
        return False
    return _numero_lote(resto.split("-")[-1]) == _numero_lote(numero)


def _preco_de_lote(consulta: set[str], pergunta: str) -> bool:
    texto = _norm(pergunta)
    if _bate(consulta, ("prec", "cust", "valor", "reais", "pedid", "avista")):
        return True
    pedido = _extrair_lote(pergunta)
    if pedido and ("quanto" in texto or "sai" in consulta):
        return True
    return "sai" in consulta and _bate(consulta, ("lote", "terren"))


def _produto(pergunta: str, consulta: set[str], trechos: list[Trecho]) -> list[Trecho] | None:
    if _bate(consulta, ("sintra",)) and _bate(consulta, ("coimbra",)):
        ambos = [trecho for trecho in trechos if trecho.titulo == "Casas do Teresópolis"]
        if ambos:
            return ambos[:1]
    if _bate(consulta, ("sintra",)):
        return [trecho for trecho in trechos if trecho.titulo == "Casa Sintra"][:1]
    if _bate(consulta, ("coimbra",)):
        return [trecho for trecho in trechos if trecho.titulo == "Casa Coimbra"][:1]
    if _bate(consulta, ("cistern",)) or (_bate(consulta, ("casa",)) and _preco_de_lote(consulta, pergunta) and not _bate(consulta, ("sobrad",))):
        achou = [trecho for trecho in trechos if trecho.titulo == "Casas do Teresópolis"]
        if achou:
            return achou[:1]
    if _bate(consulta, (
        "escritur", "itbi", "certid", "cess", "atras", "multa", "mora", "juros",
        "parcel", "prestac", "saldo", "ipca", "correc", "corrig", "habit",
        "desfaz", "distrat", "desist", "contrat",
    )):
        return None
    pedido = _extrair_lote(pergunta)
    if not pedido or not _preco_de_lote(consulta, pergunta):
        return None
    if _bate(consulta, ("sinal", "entrad", "ato")) and not (_bate(consulta, ("avista",)) or "vista" in consulta):
        return None
    quadra, numero = pedido
    achados = [
        trecho for trecho in trechos
        if trecho.titulo.startswith("Lote ") and _lote_da_tabela(trecho.titulo.removeprefix("Lote "), quadra, numero)
    ]
    if achados:
        return achados[:1]
    return [Trecho("Contrato", AUSENTE)]


def buscar(pergunta: str, k: int = 1, pasta: Path = PASTA) -> list[Trecho]:
    consulta = set(_tokens(pergunta))
    if not consulta:
        return []
    trechos = carregar(pasta)
    produto = _produto(pergunta, consulta, trechos)
    if produto is not None:
        return produto
    conhecidos: set[str] = set()
    for trecho in trechos:
        conhecidos |= _numeros(set(_tokens(trecho.texto)))
    destino = rotear(pergunta, consulta)
    if destino == "AUSENTE":
        return [Trecho("Contrato", AUSENTE)]
    if destino:
        for trecho in trechos:
            if trecho.titulo == destino:
                return [trecho]
    pede_preco = bool(PRECO & consulta) and "casa" not in consulta and not (PARCELA & consulta)
    if pede_preco and _numeros(consulta) - conhecidos:
        return [Trecho("Contrato", AUSENTE)]
    pontuados: list[tuple[int, Trecho]] = []
    for trecho in trechos:
        base = set(_tokens(trecho.busca()))
        titulo = set(_tokens(trecho.titulo))
        apelido = set(_tokens(APELIDOS.get(trecho.titulo, "")))
        pontos = 0
        for tok in consulta:
            if tok in titulo:
                pontos += 3 * len(tok)
            elif tok in apelido:
                pontos += 2 * len(tok)
            elif tok in base:
                pontos += len(tok)
        if pede_preco and "56.273" in trecho.texto:
            pontos += 80
        if pontos:
            pontuados.append((pontos, trecho))
    pontuados.sort(key=lambda item: item[0], reverse=True)
    return [trecho for _, trecho in pontuados[:k]]


def montar_contexto(pergunta: str) -> tuple[str, str]:
    trechos = buscar(pergunta, k=1)
    if not trechos:
        return "Nenhum trecho do material cobre essa pergunta.", "-"
    return trechos[0].texto, trechos[0].titulo


def garantir(resposta: str, contexto: str) -> str:
    """Se a frase gerada sai do trecho, vale o trecho."""
    if not contexto or contexto.startswith("Nenhum"):
        return resposta
    frases = [frase.strip() for frase in re.split(r"(?<=[.!?])\s+", contexto) if frase.strip()]
    if len(frases) > 1:
        baixo = resposta.lower()
        for frase in frases:
            marcas = [tok for tok in _tokens(frase) if len(tok) > 4]
            if marcas and not any(tok in baixo for tok in marcas):
                return contexto
    uteis = [tok for tok in _tokens(contexto) if len(tok) > 4]
    dito = set(_tokens(resposta))
    if uteis and not any(tok in dito for tok in uteis):
        return contexto
    numeros = _numeros(set(_tokens(contexto)))
    if numeros and not (_numeros(dito) & numeros):
        return contexto
    return resposta


def _pedaco(trechos: list[Trecho], titulo: str, resposta: str) -> Trecho:
    candidatos = [t for t in trechos if t.titulo == titulo] or trechos
    alvo = set(_tokens(resposta))
    numeros = {tok for tok in alvo if any(c.isdigit() for c in tok)}

    def nota(trecho: Trecho) -> tuple[int, int]:
        toks = set(_tokens(trecho.texto))
        return (len(numeros & toks), len(alvo & toks))

    return max(candidatos, key=nota)


def _outro(trechos: list[Trecho], titulo: str, exige: list[str]) -> Trecho | None:
    proibidos = {_tokens(p)[0] for p in exige if _tokens(p)}
    for trecho in trechos:
        if trecho.titulo == titulo:
            continue
        if proibidos & set(_tokens(trecho.texto)):
            continue
        return trecho
    return None


def gravar(destino: Path | None = None) -> None:
    from dados_instrucao import FATOS

    rng = random.Random(11)
    trechos = carregar()
    treino: list[dict] = []
    geral: list[dict] = []
    for fato in FATOS:
        titulo = SECAO[fato["id"]]
        if fato["id"] == "lote_ausente":
            certo = Trecho("Contrato", AUSENTE)
        else:
            certo = _pedaco(trechos, titulo, fato["resposta"])
        item = {
            "tipo": "fato",
            "id": fato["id"],
            "instrucao": "",
            "contexto": certo.texto,
            "resposta": fato["resposta"],
            "exige": fato["exige"],
        }
        if fato.get("proibe"):
            item["proibe"] = fato["proibe"]
        alheio = _outro(trechos, titulo, fato["exige"])
        for pergunta in list(fato["treino"]) + [fato["aceite"]]:
            for _ in range(4):
                copia = dict(item)
                copia["instrucao"] = pergunta
                treino.append(copia)
        copia_regra = dict(item)
        copia_regra["instrucao"] = "Diga a regra que está no contexto."
        copia_regra["id"] = fato["id"] + "_copia"
        treino.append(copia_regra)
        if alheio is not None and fato["id"] != "lote_ausente":
            treino.append({
                "tipo": "fato",
                "id": fato["id"] + "_fora",
                "instrucao": fato["aceite"],
                "contexto": alheio.texto,
                "resposta": "Isso não está no contexto.",
                "exige": ["não está"],
                "proibe": fato["exige"],
            })
        fora = dict(item)
        fora["instrucao"] = fato["geral"][0]
        geral.append(fora)
    rng.shuffle(treino)
    destino = destino or (RAIZ / "instrucao")
    destino.mkdir(parents=True, exist_ok=True)
    for nome, itens in (("rag_treino.jsonl", treino), ("rag_avaliacao.jsonl", geral)):
        (destino / nome).write_text(
            "".join(json.dumps(i, ensure_ascii=False) + "\n" for i in itens),
            encoding="utf-8",
        )
        print(nome, len(itens))


if __name__ == "__main__":
    gravar()
