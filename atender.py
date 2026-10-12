"""Pergunta do lead, busca no material, resposta do modelo."""

from __future__ import annotations

import torch
from tokenizers import Tokenizer

from avaliar import responder
from modelo import Config, Modelo
from rag import RAIZ, garantir, montar_contexto

FALAS = [
    "Oi, boa noite. Vi um anúncio de lote e queria saber mais.",
    "Quero um lote para investir. Vocês têm em Arcoverde?",
    "Quanto custa o lote 22 da quadra B1?",
    "Esse valor dá para parcelar? Não consigo pagar o sinal de uma vez.",
    "E se eu ainda achar caro, dá para jogar no cartão?",
    "No boleto, consigo mais vezes?",
    "Queria um desconto. Quem autoriza?",
    "E casa, vocês vendem? Quanto custa?",
    "Posso visitar sábado de manhã? Preciso levar documento?",
    "E se cair num feriado?",
    "Se eu gostar, por quanto tempo vocês seguram o lote?",
    "O que eu preciso pagar para confirmar a reserva?",
    "Se eu sumir uns dias, vocês cancelam?",
    "Para fazer a proposta, quais dados vocês pedem?",
    "Quero passar o lote para o meu irmão e ainda vou estar pagando. Dá?",
    "Se eu desistir, devolvem o sinal?",
    "Depois que eu quitar, o que eu faço para registrar?",
    "Posso construir e já morar antes da prefeitura liberar?",
    "Quanto custa o lote 15 da quadra K?",
    "Boa tarde. Me explica como funciona a compra de um lote.",
    "Tô pensando em aplicar num terreno. Tem aí em Arcoverde?",
    "Qual a pedida do 22 da quadra B1?",
    "A entrada eu não consigo pagar de uma vez. Dá pra dividir?",
    "Se continuar pesado, aceita crédito?",
    "E no carnê, passa de duas parcelas?",
    "Rola um choro? Quem libera isso?",
    "Quero um sobrado. Vocês falam o preço?",
    "Quero conhecer o terreno no fim de semana cedo. Levo algum papel?",
    "Se o dia for feriado, vocês atendem?",
    "Fechando hoje, o terreno fica guardado quantos dias?",
    "O que eu pago pra essa reserva valer de verdade?",
    "Se eu ficar mudo depois de reservar, perde?",
    "Que dados entram na ficha de compra?",
    "Meu irmão assume as prestações. Pode passar pra ele?",
    "Me arrependi da compra. O sinal volta?",
    "Quitei a última. Como levo pro cartório?",
    "Dá pra mudar pro lote antes da prefeitura deixar?",
    "Quanto sai o lote 8 da quadra Z?",
]


def contexto_de(pergunta: str) -> tuple[str, str]:
    return montar_contexto(pergunta)


def main() -> None:
    device = torch.device("cuda")
    tok = Tokenizer.from_file(str(RAIZ / "tokenizer.json"))
    modelo = Modelo(Config()).to(device)
    salvo = torch.load(RAIZ / "checkpoints" / "ciclo1-rag.pt", map_location=device, weights_only=False)
    modelo.load_state_dict(salvo["modelo"])
    modelo.eval()
    for fala in FALAS:
        texto, titulo = contexto_de(fala)
        item = {"instrucao": fala, "contexto": texto, "resposta": ""}
        print("LEAD:", fala, flush=True)
        print("TRECHO:", titulo, flush=True)
        print("IA:", garantir(responder(modelo, tok, item, device), texto), flush=True)
        print(flush=True)


if __name__ == "__main__":
    main()
