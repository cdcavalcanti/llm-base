# Modelo base

Modelo de linguagem pequeno, treinado do zero em português. 106.980.096 parâmetros. Os pesos nascem aleatórios; o tokenizer também é deste repositório.

Este é o modelo base. Dá para conversar com ele fora de qualquer empresa. O material operacional da Digimob entra depois, num ajuste em cima destes pesos.

## Arquivos que importam

- `checkpoints/ciclo1-instrucao.pt` — modelo que segue instrução. O `chat.py` carrega este. sha256 `2fff9bc0b79251f67b931117ffd10175193e5119bb9a62c256ea558f941b4dcb`
- `checkpoints/ciclo1-longo.pt` — pré-treino. Ponto de partida para um ajuste novo. sha256 `a63cea48a98955ba7ce265f7b82b005292bc8bd26e659ac418672096f725b2e0`
- `tokenizer.json` — BPE próprio, vocabulário 8192

## Conversar

```bash
python3 -m venv .venv
.venv/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv/bin/pip install -r requirements.txt
.venv/bin/python chat.py
```

Com GPU NVIDIA, troque o índice do torch por `https://download.pytorch.org/whl/cu124`.

## O que ele já faz

Temperatura zero, nos quatro enunciados do ciclo:

- `A capital do Brasil é Brasília.`
- `O valor da multa não está no contexto.`
- `1.247`
- `Um adaptador LoRA é um ajuste pequeno ao lado do modelo.`

Num conjunto separado, com assunto que não estava no treino, acerta 7 de 19. Fora do texto visto, ainda troca o tema.
