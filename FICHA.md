# LLM Digimob · ciclo 1

Frase deste ciclo: os pesos nascem aleatórios nesta RTX 4060 Ti. O tokenizer é treinado por nós. O arquivo é nosso. É um modelo pequeno de pesquisa, de completar texto. Não é um modelo de instrução na classe de 7B a 27B.

Placa medida: NVIDIA GeForce RTX 4060 Ti, 8188 MiB, cerca de 7561 MiB livres, driver 550.163.01. A área de trabalho usa a mesma placa. Disco de trabalho: `/home`.

## Passos

1. Medir a GPU. Feito.
2. Travar a frase acima. 8 GB não treina um 7B.
3. Baixar um recorte público de português e registrar a licença do pacote. Dado de cliente fica de fora.
4. Treinar o tokenizer nesse recorte.
5. Subir o modelo pequeno e dar os primeiros passos de pré-treino na GPU. Guardar checkpoint e hash.
6. Aumentar o corpus para a escala de pré-treino e deixar o treino longo correr.
7. Só então fazer o ajuste de instrução das quatro provas: seguir instrução, não inventar, copiar o número, responder curto.
8. Serviço no CRM só depois, se for pedido.

O passo 5 não fecha as quatro provas. Pré-treino ensina a prever a próxima parte do texto. A abstenção entra no passo 7.

## O que já rodou

Corpus: Wortschatz Leipzig `por_news_2024_100K`, 98 mil frases no treino e 2 mil fora dele. Cerca de 3,1 milhões de tokens. O meta do pacote não traz a linha de licença.

Tokenizer nosso, vocabulário 8192. Modelo com 106.980.096 parâmetros, pesos iniciais aleatórios.

Checkpoint `checkpoints/ciclo1.pt` na máquina, 3.200 passos, perda de 9,15 para 4,01, pico de 2523 MiB na 4060 Ti.

sha256 `7396227ab31727853a7b9db0e250110a7d6f39f36f50768d68af11161c980ade`

Isso ainda é um recorte pequeno. O pré-treino de verdade pede bem mais texto do que essas 98 mil frases.

## Treino em andamento

Corpus acrescentado, ainda público, sem dado de cliente:

- Wortschatz Leipzig `por_news_2024_1M`, 1 milhão de frases
- Wortschatz Leipzig `por_wikipedia_2021_1M`, 1 milhão de frases

Junto com o recorte anterior, o treino vê 66.406.668 tokens. O tokenizer não foi refeito, para o checkpoint continuar válido.

Esse treino terminou. 25.000 passos em cima dos 3.200 anteriores, 28.200 no total, em 3.232 segundos. Perda final 3,20. Pico de 2523 MiB.

Checkpoint `checkpoints/ciclo1-longo.pt`
sha256 `a63cea48a98955ba7ce265f7b82b005292bc8bd26e659ac418672096f725b2e0`

O `ciclo1.pt` ficou como estava.

## Ajuste de instrução

4.500 pares de treino e 52 provas que não repetem o texto do treino. Três épocas em cima de `ciclo1-longo.pt`. Checkpoint `checkpoints/ciclo1-instrucao.pt`.

O treino de instrução foi refeito a partir de `ciclo1-longo.pt`, com o país copiado da pergunta e com a resposta curta de volta ao conjunto. Checkpoint `checkpoints/ciclo1-instrucao.pt`, sha256 `2fff9bc0b79251f67b931117ffd10175193e5119bb9a62c256ea558f941b4dcb`.

Nos quatro enunciados do estudo, temperatura zero, o pré-treino erra os quatro e o ajuste acerta os quatro:

- Capital do Brasil: `A capital do Brasil é Brasília.`
- Multa ausente: `O valor da multa não está no contexto.`
- Número: `1.247`
- Resposta curta: `Um adaptador LoRA é um ajuste pequeno ao lado do modelo.`

Num conjunto separado, com países, campos e conceitos que não estavam no treino, o ajuste acerta 7 de 19. Fora do texto que ele viu, ainda troca o país e o assunto.
