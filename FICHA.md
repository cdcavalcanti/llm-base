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

## Ajuste Digimob

O conjunto de países saiu. O ajuste novo parte de `ciclo1-longo.pt` e usa só o que já está fechado da operação e do contrato B1-22. Checkpoint `checkpoints/ciclo1-digimob.pt`, sha256 `55b9a31395c653e678976a9f286c75e6a34acf03d560273f44a6e477943c9f85`. 708 pares, 267 passos, perda 0,0008, 30 segundos.

Nas 40 perguntas que entraram no treino, acerta 39. Erra "Funil e cobrança rodam onde?": responde a frase da cessão. O preço do lote B1-22 sai certo: R$ 56.273,28.

Nas 40 perguntas com outro enunciado, que não estavam no treino, acerta 6. Fora da frase que ele viu, ainda cola uma resposta vizinha. O bloco do Felipe ainda não entrou.

## RAG

O material fica em `conhecimento/`, uma regra por trecho. A busca é `rag.py`. Os pesos não guardam esse texto. Se a frase gerada sai do trecho, a resposta que sai é o próprio trecho.

O ajuste `checkpoints/ciclo1-rag.pt` parte de `ciclo1-longo.pt`. sha256 `3a40c56792efd3faf14f6d50168add49f96180e92c6eae3d2e6a6a407ccf1f2f`. 751 pares, 376 passos, 4 épocas, perda 0,0002, 42 segundos.

No lead de 19 falas, as 19 saem com a regra certa: oi, preço do B1-22, entrada em duas vezes, cartão, boleto, desconto do Felipe, casa, visita, feriado, reserva de 7 dias, confirmação, sumiço, proposta, cessão, distrato da operação, pós-venda, habite-se e lote ausente.

A busca passou a reconhecer o mesmo pedido com outras palavras. Um segundo lead, com vocabulário que não entrou nos apelidos nem no treino, também fecha 19 de 19 na GPU, no mesmo checkpoint. As 208 perguntas já escritas (treino, aceite e avaliação) caem no trecho certo.

O Felipe enviou a tabela Veredas do Teresópolis, datada de 24/11/2021 no próprio arquivo, com 135 lotes em 21 quadras, e a tabela das 10 casas da quadra V. Cada lote é um trecho. O preço à vista do B1-22 nessa tabela é R$ 48.000,00. O contrato continua em R$ 56.273,28, e a frase do lote traz os dois. Casa Sintra R$ 260.000,00. Casa Coimbra R$ 210.000,00 sem cisterna e R$ 215.000,00 com cisterna. A qualificação que ele escreveu também entrou. Os pesos não foram retreinados.

Em 14/10/2026 o atendimento na GPU fechou 15 pontos novos: lotes da tabela, casas, sobrado, desconto, sinal do contrato, qualificação e visita. As duas formas de perguntar deram a mesma resposta. A correção ficou em dois pontos, porque a tabela usa IGP-M e o contrato do B1-22 usa IPCA. Lote fora da tabela continua sem preço.
