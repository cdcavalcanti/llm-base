"""Pares da Digimob. O conjunto de avaliação não repete a pergunta do treino."""

from __future__ import annotations

import json
import random
from pathlib import Path

# Cada fato: perguntas de treino, uma de aceite (também entra no treino) e
# perguntas de avaliação com outro enunciado. A resposta é a mesma.
FATOS = [
    {
        "id": "primeiro_contato",
        "resposta": "No primeiro contato o lead escolhe visitar ou falar com um especialista.",
        "exige": ["visitar", "especialista"],
        "treino": [
            "O que a IA oferece no primeiro contato?",
            "Como começa o atendimento?",
            "Quais opções o lead recebe no oi?",
            "Oi, queria saber mais sobre um lote.",
        ],
        "aceite": "No primeiro contato, o que o lead pode escolher?",
        "geral": ["A conversa começa oferecendo o quê?"],
    },
    {
        "id": "preco_lote",
        "resposta": "A IA responde o preço de lote.",
        "exige": ["preço", "lote"],
        "proibe": ["casa"],
        "treino": [
            "A IA pode falar o preço de um lote?",
            "Quem responde o valor do lote?",
            "Preço de lote passa para alguém?",
        ],
        "aceite": "A IA responde preço de lote?",
        "geral": ["Dúvida de valor de terreno a IA pode responder?"],
    },
    {
        "id": "preco_casa",
        "resposta": "Preço de casa vai para o especialista.",
        "exige": ["casa", "especialista"],
        "treino": [
            "Quem responde o preço de uma casa?",
            "A IA fala o valor de casa?",
            "Para onde vai a pergunta de preço de casa?",
            "Vocês vendem casa?",
        ],
        "aceite": "Preço de casa a IA responde?",
        "geral": ["O cliente perguntou quanto custa a casa. O que a IA faz?"],
    },
    {
        "id": "juridico",
        "resposta": "Jurídico vai para o especialista.",
        "exige": ["jurídico", "especialista"],
        "treino": [
            "Quem responde dúvida jurídica?",
            "A IA resolve questão de jurídico?",
            "Para onde vai o assunto jurídico?",
        ],
        "aceite": "Dúvida jurídica fica com quem?",
        "geral": ["O cliente quer uma orientação jurídica. Quem assume?"],
    },
    {
        "id": "desconto",
        "resposta": "Desconto só o Felipe autoriza. Ele é o gerente.",
        "exige": ["felipe"],
        "proibe": ["5%", "10%"],
        "treino": [
            "Quem autoriza desconto?",
            "O corretor pode dar desconto sozinho?",
            "Desconto passa por quem?",
            "Queria desconto. Quem pode autorizar?",
        ],
        "aceite": "Quem libera desconto?",
        "geral": ["O cliente pediu um abatimento no preço. Quem decide?"],
    },
    {
        "id": "entrada_duas",
        "resposta": "A entrada pode ser parcelada em duas vezes.",
        "exige": ["duas"],
        "proibe": ["10 vezes", "três"],
        "treino": [
            "Dá para parcelar a entrada?",
            "O sinal pode ser dividido?",
            "Em quantas vezes a entrada pode começar?",
        ],
        "aceite": "A entrada parcela em quantas vezes?",
        "geral": ["O cliente não quer pagar o sinal de uma vez. Qual é a primeira opção?"],
    },
    {
        "id": "entrada_cartao",
        "resposta": "Se a objeção da entrada continuar, o cartão parcela em 10 vezes.",
        "exige": ["10", "cartão"],
        "treino": [
            "Se o cliente recusar as duas vezes da entrada, o que vem?",
            "Quantas vezes no cartão quando a objeção continua?",
            "Qual é a opção de cartão para a entrada?",
        ],
        "aceite": "Depois das duas vezes, o cartão fica em quantas?",
        "geral": ["A objeção do sinal continuou. Como fica o cartão de crédito?"],
    },
    {
        "id": "entrada_boleto",
        "resposta": "No boleto a entrada fica em 2 vezes e pode chegar a 3. Três vezes é a última opção.",
        "exige": ["boleto", "última"],
        "treino": [
            "Como a entrada fica no boleto?",
            "O boleto da entrada pode passar de duas vezes?",
            "Qual é a última opção da entrada no boleto?",
            "No boleto dá para parcelar em mais vezes?",
        ],
        "aceite": "Até quantas vezes a entrada vai no boleto?",
        "geral": ["Qual o limite de parcelas da entrada no boleto?"],
    },
    {
        "id": "pagamento",
        "resposta": "As formas são à vista, entrada, parcela, boleto em 2 vezes e cartão em 10 vezes.",
        "exige": ["à vista", "cartão"],
        "treino": [
            "Quais formas de pagamento a Digimob aceita?",
            "Como o cliente pode pagar?",
            "Quais são as opções de pagamento?",
        ],
        "aceite": "Quais são as formas de pagamento?",
        "geral": ["Me lista como o pagamento pode ser feito."],
    },
    {
        "id": "visita_docs",
        "resposta": "Na visita o cliente leva os documentos pessoais.",
        "exige": ["documentos"],
        "treino": [
            "O que o cliente leva na visita?",
            "Precisa levar documento na visita?",
            "A visita pede algum papel?",
        ],
        "aceite": "O cliente leva o que na visita?",
        "geral": ["Vou visitar o lote. Levo algum documento?"],
    },
    {
        "id": "visita_horario",
        "resposta": "A visita preferencial é em horário comercial. No fim de semana, pela manhã.",
        "exige": ["comercial", "manhã"],
        "treino": [
            "Qual o horário da visita?",
            "Dá para visitar no fim de semana?",
            "Quando a visita acontece?",
        ],
        "aceite": "Qual o horário preferencial da visita?",
        "geral": ["Posso ver o lote no sábado de manhã?"],
    },
    {
        "id": "feriado",
        "resposta": "Feriado depende da agenda.",
        "exige": ["feriado", "agenda"],
        "proibe": ["exce"],
        "treino": [
            "Tem visita em feriado?",
            "Feriado entra na agenda de visita?",
            "Como fica a visita se o dia é feriado?",
        ],
        "aceite": "Dá para agendar visita em feriado?",
        "geral": ["O feriado tem visita marcada como?"],
    },
    {
        "id": "feriado_excecao",
        "resposta": "As exceções de feriado não estão no material.",
        "exige": ["não estão"],
        "treino": [
            "Quais são as exceções de feriado?",
            "Me lista as exceções de visita em feriado.",
            "Que feriado é exceção?",
        ],
        "aceite": "Quais feriados são exceção?",
        "geral": ["Existe lista de feriado liberado?"],
    },
    {
        "id": "reserva_dias",
        "resposta": "A reserva dura 7 dias.",
        "exige": ["7 dias"],
        "treino": [
            "Quantos dias dura a reserva do lote?",
            "Por quanto tempo o lote fica reservado?",
            "Qual o prazo da reserva?",
            "Por quanto tempo vocês seguram um lote?",
        ],
        "aceite": "A reserva do lote dura quanto?",
        "geral": ["O lote reservado segura por quanto tempo?"],
    },
    {
        "id": "reserva_confirma",
        "resposta": "A reserva confirma com o pagamento do sinal e a coleta dos documentos.",
        "exige": ["sinal", "documentos"],
        "treino": [
            "O que confirma a reserva?",
            "Como a reserva fica confirmada?",
            "Reserva confirma com o quê?",
        ],
        "aceite": "O que fecha a confirmação da reserva?",
        "geral": ["Para a reserva valer, o cliente faz o quê?"],
    },
    {
        "id": "reserva_sumiu",
        "resposta": "Se o cliente para de responder, a IA tenta retomar por 2 dias e depois cancela a reserva.",
        "exige": ["2 dias", "cancela"],
        "treino": [
            "O que acontece se o cliente some na reserva?",
            "Sem retorno, a reserva continua?",
            "Como funciona a ressuscitação da reserva?",
        ],
        "aceite": "Se o cliente não responde, o que a IA faz com a reserva?",
        "geral": ["O cliente reservou e sumiu. Qual é o prazo da tentativa?"],
    },
    {
        "id": "proposta",
        "resposta": "A proposta pede nome completo, profissão, endereço, estado civil, e-mail, telefone, CPF e RG.",
        "exige": ["cpf", "rg", "profissão"],
        "treino": [
            "Quais dados entram na proposta?",
            "O que a proposta coleta?",
            "Que informações a proposta pede do comprador?",
        ],
        "aceite": "A proposta pede quais dados?",
        "geral": ["Para montar a proposta, quais campos são obrigatórios?"],
    },
    {
        "id": "doc_pdf",
        "resposta": "A documentação do cliente vai em PDF.",
        "exige": ["pdf"],
        "treino": [
            "Em que formato vai a documentação do cliente?",
            "O documento do comprador é enviado como?",
            "A documentação do cliente chega em qual arquivo?",
        ],
        "aceite": "A documentação do cliente é em qual formato?",
        "geral": ["O comprador manda os papéis em que tipo de arquivo?"],
    },
    {
        "id": "doc_lote",
        "resposta": "A documentação do lote só é entregue com a assinatura.",
        "exige": ["assinatura"],
        "treino": [
            "Quando o cliente recebe a documentação do lote?",
            "A documentação do lote sai antes de assinar?",
            "O que libera a documentação do lote?",
        ],
        "aceite": "A documentação do lote é entregue quando?",
        "geral": ["Sem assinatura, o cliente recebe o documento do lote?"],
    },
    {
        "id": "certidao",
        "resposta": "A certidão do lote sai depois da assinatura da proposta.",
        "exige": ["certidão", "proposta"],
        "treino": [
            "Quando sai a certidão do lote?",
            "A certidão do lote vem antes da proposta?",
            "O que antecede a certidão do lote?",
        ],
        "aceite": "A certidão do lote sai em que momento?",
        "geral": ["Depois de assinar a proposta, qual documento do lote vem?"],
    },
    {
        "id": "doze_dias",
        "resposta": "Em 12 dias sai o contrato com o boleto, em duas vias.",
        "exige": ["12 dias", "duas vias"],
        "treino": [
            "Em quantos dias sai o contrato com o boleto?",
            "Quantas vias do contrato são emitidas?",
            "Depois do preenchimento, quando sai o contrato?",
        ],
        "aceite": "O contrato com o boleto sai em quanto tempo?",
        "geral": ["Quanto tempo depois do preenchimento o contrato e o boleto saem?"],
    },
    {
        "id": "cessao_quando",
        "resposta": "A cessão vale quando ainda há parcelas em aberto e o lote passa para outro comprador.",
        "exige": ["parcelas", "outro"],
        "treino": [
            "Quando a cessão pode ser feita?",
            "Dá para transferir o lote que ainda está sendo pago?",
            "A cessão existe em que situação?",
        ],
        "aceite": "Em que caso se faz a cessão?",
        "geral": ["O cliente quer passar o lote para outra pessoa e ainda deve parcelas. Pode?"],
    },
    {
        "id": "cessao_prazo",
        "resposta": "Em 10 dias chega o documento de cessão. Assinam o comprador antigo e o dono do lote.",
        "exige": ["10 dias", "dono"],
        "treino": [
            "Em quantos dias chega o documento de cessão?",
            "Quem assina a cessão?",
            "Qual o prazo do documento de cessão?",
        ],
        "aceite": "Quem assina o documento de cessão e em quanto tempo ele chega?",
        "geral": ["Depois de pagar a taxa, quando o papel da cessão fica pronto?"],
    },
    {
        "id": "cessao_b1",
        "resposta": "No contrato do lote B1-22 a taxa de cessão é 5% do valor total do lote.",
        "exige": ["5%", "b1-22"],
        "proibe": ["varia"],
        "treino": [
            "Qual a taxa de cessão do lote B1-22?",
            "No Teresópolis, lote 22 da quadra B1, a cessão cobra quanto?",
            "A taxa administrativa de cessão do contrato B1-22 é qual?",
        ],
        "aceite": "Quanto é a taxa de cessão no contrato B1-22?",
        "geral": ["A transferência do lote 22 da quadra B1 cobra qual percentual?"],
    },
    {
        "id": "distrato_op",
        "resposta": "Na operação, o distrato devolve 50% das parcelas pagas. O sinal não volta e não cobra taxa.",
        "exige": ["50%", "sinal não volta"],
        "proibe": ["10%", "0,75"],
        "treino": [
            "Como funciona o distrato na operação?",
            "No distrato, quanto das parcelas volta?",
            "O distrato da operação cobra taxa?",
        ],
        "aceite": "O que volta no distrato da operação?",
        "geral": ["Se o cliente desistir pela regra da operação, o sinal é devolvido?"],
    },
    {
        "id": "distrato_aceite",
        "resposta": "O distrato depende de a empresa aceitar a devolução do lote. Sem caixa, precisa consultar.",
        "exige": ["aceitar", "consultar"],
        "treino": [
            "A empresa é obrigada a aceitar o distrato?",
            "E se a empresa estiver sem caixa no distrato?",
            "O distrato sempre devolve o lote?",
        ],
        "aceite": "O distrato depende de quê da empresa?",
        "geral": ["A devolução do lote no distrato é automática?"],
    },
    {
        "id": "pos_venda",
        "resposta": "Depois de quitar, o cliente recebe o recibo de quitação, gera o imposto de TBI na prefeitura e registra no cartório.",
        "exige": ["quitação", "tbi", "cartório"],
        "treino": [
            "O que acontece quando o cliente termina de pagar o terreno?",
            "Qual o caminho do pós-venda depois da quitação?",
            "Para que serve o recibo de quitação?",
        ],
        "aceite": "Depois de quitar o terreno, qual é o caminho?",
        "geral": ["O cliente pagou a última parcela. Qual documento ele usa no fórum?"],
    },
    {
        "id": "iptu",
        "resposta": "Quem já comprou e está pagando passa o IPTU para o nome dele.",
        "exige": ["iptu", "nome"],
        "treino": [
            "O IPTU fica no nome de quem?",
            "Quem está pagando o lote transfere o IPTU?",
            "Quando o IPTU muda de nome?",
        ],
        "aceite": "O IPTU de quem já está pagando o lote fica como?",
        "geral": ["O comprador que ainda parcela precisa mudar o IPTU?"],
    },
    {
        "id": "b1_onde",
        "resposta": "O lote B1-22 fica no loteamento Teresópolis, quadra B1, 200 m², Rua Cícero Monteiro de Melo, São Cristóvão, Arcoverde.",
        "exige": ["teresópolis", "200", "arcoverde"],
        "treino": [
            "Onde fica o lote B1-22?",
            "Qual o tamanho e o endereço do lote 22 da quadra B1?",
            "O lote B1-22 é de qual loteamento?",
        ],
        "aceite": "Qual é o lote B1-22?",
        "geral": ["Me situa o lote 22 da quadra B1: cidade, bairro e metragem."],
    },
    {
        "id": "b1_preco",
        "resposta": "O preço do lote B1-22 é R$ 56.273,28.",
        "exige": ["56.273,28"],
        "proibe": ["4.200", "619,92"],
        "treino": [
            "Qual o preço total do lote B1-22?",
            "Quanto custa o lote 22 da quadra B1 no Teresópolis?",
            "Qual o valor do contrato B1-22?",
            "Qual o preço em reais do lote B1-22?",
            "Me diga somente o preço total do B1-22.",
            "O valor de venda do lote B1-22 é qual?",
        ],
        "aceite": "Qual o preço do lote B1-22?",
        "geral": ["O imóvel do contrato B1-22 fecha em qual valor?"],
    },
    {
        "id": "b1_sinal",
        "resposta": "O sinal do lote B1-22 é R$ 4.200,00.",
        "exige": ["4.200,00"],
        "proibe": ["56.273"],
        "treino": [
            "Qual o sinal do lote B1-22?",
            "Quanto é a entrada do contrato B1-22?",
            "O ato do lote 22 da quadra B1 custa quanto?",
        ],
        "aceite": "Qual o valor do sinal do B1-22?",
        "geral": ["No contrato B1-22, o pagamento do ato é de quanto?"],
    },
    {
        "id": "b1_parcelas",
        "resposta": "O saldo do lote B1-22 são 84 parcelas de R$ 619,92.",
        "exige": ["84", "619,92"],
        "treino": [
            "Quantas parcelas tem o lote B1-22 e de quanto?",
            "Como é o saldo do contrato B1-22?",
            "O lote 22 da quadra B1 parcela em quantas vezes?",
        ],
        "aceite": "Qual o parcelamento do saldo do B1-22?",
        "geral": ["Depois do sinal, o B1-22 fica em quantas prestações e de qual valor?"],
    },
    {
        "id": "b1_ipca",
        "resposta": "As parcelas do lote B1-22 têm correção anual pelo IPCA.",
        "exige": ["ipca"],
        "treino": [
            "As parcelas do B1-22 são corrigidas por quê?",
            "Qual o índice de correção do contrato B1-22?",
            "O lote 22 da quadra B1 reajusta como?",
        ],
        "aceite": "Qual a correção das parcelas do B1-22?",
        "geral": ["O saldo do Teresópolis, lote B1-22, usa qual índice?"],
    },
    {
        "id": "b1_atraso",
        "resposta": "No lote B1-22 o atraso cobra 1% de mora ao mês e multa de 2%.",
        "exige": ["1%", "2%"],
        "treino": [
            "Qual a mora e a multa de atraso do lote B1-22?",
            "Se atrasar a parcela do contrato B1-22, quanto cobra?",
            "Juros e multa do Teresópolis lote 22 são quais?",
        ],
        "aceite": "Quanto é a multa de atraso do B1-22?",
        "geral": ["A prestação do contrato B1-22 atrasou. Quais os encargos?"],
    },
    {
        "id": "b1_habite",
        "resposta": "É proibido morar no loteamento Teresópolis antes do habite-se da Prefeitura de Arcoverde.",
        "exige": ["habite-se", "proibido"],
        "treino": [
            "Dá para morar no lote do Teresópolis antes do habite-se?",
            "Quando a habitação é permitida no loteamento Teresópolis?",
            "O habite-se de Arcoverde libera o quê?",
        ],
        "aceite": "Posso morar no lote antes do habite-se?",
        "geral": ["Construir eu posso, mas morar antes da prefeitura liberar pode?"],
    },
    {
        "id": "b1_escritura",
        "resposta": "A escritura do lote B1-22 sai depois de quitar. ITBI, registro e escritura ficam com o comprador.",
        "exige": ["escritura", "itbi", "comprador"],
        "treino": [
            "Quando sai a escritura do lote B1-22?",
            "Quem paga o ITBI do contrato B1-22?",
            "A escritura do Teresópolis sai antes de quitar?",
        ],
        "aceite": "A escritura do B1-22 sai quando, e quem paga o ITBI?",
        "geral": ["O registro e o ITBI do lote 22 da quadra B1 ficam por conta de quem?"],
    },
    {
        "id": "b1_infra",
        "resposta": "A infraestrutura do Teresópolis inclui demarcação, ruas, meio-fio, calçamento da Rua Projetada 02, água e energia.",
        "exige": ["meio-fio", "água", "energia"],
        "treino": [
            "O que a vendedora implanta no Teresópolis?",
            "Qual a infraestrutura do loteamento Teresópolis?",
            "Água e energia do Teresópolis ficam com quem?",
        ],
        "aceite": "Quais melhoramentos entram no Teresópolis?",
        "geral": ["O loteamento de Arcoverde entrega rua, água e luz?"],
    },
    {
        "id": "b1_desfaz",
        "resposta": "No desfazimento do contrato B1-22 saem a comissão de corretagem, 10% do que foi pago, os tributos e a fruição de 0,75%. O que sobrar volta em 12 parcelas.",
        "exige": ["10%", "12 parcelas"],
        "proibe": ["50%"],
        "treino": [
            "No desfazimento do contrato B1-22, o que é descontado?",
            "Como volta o dinheiro se o contrato B1-22 se desfaz?",
            "A fruição do lote B1-22 entra no desfazimento?",
        ],
        "aceite": "O que o contrato B1-22 desconta no desfazimento?",
        "geral": ["Se o contrato do lote 22 da quadra B1 for desfeito, em quantas parcelas volta o restante?"],
    },
    {
        "id": "lote_ausente",
        "resposta": "Esse preço não está no material.",
        "exige": ["não está"],
        "proibe": ["56.273", "4.200"],
        "treino": [
            "Qual o preço do lote da quadra C8?",
            "Quanto custa o lote 99 da quadra H?",
            "Qual o valor do lote 3 da quadra D2?",
        ],
        "aceite": "Qual o preço do lote 7 da quadra F?",
        "geral": ["Quanto custa o lote 15 da quadra K?"],
    },
    {
        "id": "crm",
        "resposta": "A IA dá suporte à equipe. Funil, cobrança e monitoria ficam no CRM.",
        "exige": ["crm"],
        "treino": [
            "Quem cuida de funil, cobrança e monitoria?",
            "A IA substitui o CRM na cobrança?",
            "O suporte à equipe fica com quem?",
        ],
        "aceite": "Funil e cobrança rodam onde?",
        "geral": ["A monitoria de lead parado está na IA ou no CRM?"],
    },
]


def _item(fato: dict, instrucao: str) -> dict:
    item = {
        "tipo": "fato",
        "id": fato["id"],
        "instrucao": instrucao,
        "contexto": "",
        "resposta": fato["resposta"],
        "exige": fato["exige"],
    }
    if fato.get("proibe"):
        item["proibe"] = fato["proibe"]
    return item


def gerar_treino(rng: random.Random) -> list[dict]:
    saida: list[dict] = []
    for fato in FATOS:
        perguntas = list(fato["treino"]) + [fato["aceite"]]
        vezes = 12 if fato["id"] == "b1_preco" else 4
        for _ in range(vezes):
            ordem = perguntas[:]
            rng.shuffle(ordem)
            saida.extend(_item(fato, pergunta) for pergunta in ordem)
    rng.shuffle(saida)
    return saida


def gerar_geral() -> list[dict]:
    return [_item(fato, fato["geral"][0]) for fato in FATOS]


def aceite() -> list[dict]:
    return [_item(fato, fato["aceite"]) for fato in FATOS]


def _sem_vazamento(treino: list[dict], bloqueio: list[dict]) -> list[dict]:
    proibidos = {item["instrucao"] for item in bloqueio}
    return [item for item in treino if item["instrucao"] not in proibidos]


def gravar(destino: Path) -> None:
    rng = random.Random(11)
    geral = gerar_geral()
    fechado = aceite()
    treino = _sem_vazamento(gerar_treino(rng), geral)
    texto = json.dumps(treino + geral, ensure_ascii=False).lower()
    for proibido in ("capital do brasil", "lora", "lisboa", "brasília"):
        if proibido in texto:
            raise SystemExit(f"sobrou conteúdo fora da Digimob: {proibido}")
    destino.mkdir(parents=True, exist_ok=True)
    for nome, itens in (("treino.jsonl", treino), ("avaliacao.jsonl", geral), ("aceite.jsonl", fechado)):
        caminho = destino / nome
        caminho.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in itens), encoding="utf-8")
        print(nome, len(itens))
    print("aceite_no_treino", sum(item["instrucao"] in {t["instrucao"] for t in treino} for item in fechado))


if __name__ == "__main__":
    gravar(Path(__file__).resolve().parent / "instrucao")
