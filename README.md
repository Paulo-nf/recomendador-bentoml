# Projeto Integrador, Módulo de Recomendação

Aqui no top do README está as informações especificas do fork

## Equipe

Equipe FolcStore, ADS Regular, 4º período

## Integrantes

Luiz Felipe Matias Xavier<br>
Heitor Didier Jalfim<br>
Paulo Nery da Fonseca<br>
Thomaz Barros Costa<br>

## Instruções para subir

```bash
just treino    # lê dados/catalogo.json, grava o modelo no store do BentoML
just serve     # sobe o serviço (deixe este terminal aberto)
```

## Instruções para tester

Com o serviço no ar (`just serve`), rode cada comando em outro terminal. Os
mesmos comandos estão no `justfile` como `just curl-teste-1`, `just curl-teste-2`
e `just curl-teste-3`.

### Teste 1 — Recomendações personalizadas para a home (`/v1/recommendations/home`)

```bash
curl -sS -X POST http://127.0.0.1:3000/v1/recommendations/home \
  -H 'Content-Type: application/json' \
  -d '{"user_id": "u_83921", "limit": 3}' | python3 -m json.tool
```

Resposta esperada:

```json
{
    "strategy": "hybrid",
    "fallback_used": false,
    "items": [
        {
            "product_id": "p_1042",
            "artisan_id": "a_207",
            "score": 0.91,
            "reason": {
                "code": "BOUGHT_SIMILAR_CATEGORY",
                "text": "Porque você comprou peças de cerâmica"
            }
        },
        {
            "product_id": "p_0877",
            "artisan_id": "a_113",
            "score": 0.87,
            "reason": {
                "code": "FOLLOWED_ARTISAN",
                "text": "Porque você segue este artesão"
            }
        },
        {
            "product_id": "p_2210",
            "artisan_id": "a_309",
            "score": 0.79,
            "reason": {
                "code": "TRENDING",
                "text": "Em alta na plataforma"
            }
        }
    ],
    "model_version": "mock-0.0.1",
    "latency_ms": 12
}
```

### Teste 2 — Insights para o artesão (`/v1/recommendations/seller`)

```bash
curl -sS -X POST http://127.0.0.1:3000/v1/recommendations/seller \
  -H 'Content-Type: application/json' \
  -d '{"artisan_id": "a_207", "limit": 3}' | python3 -m json.tool
```

Resposta esperada:

```json
{
    "artisan_id": "a_207",
    "resumo_vendas": {
        "produtos": 4,
        "total_vendas": 100,
        "conversao_media": 0.0192
    },
    "preco_sugerido": {
        "product_id": "p_1042",
        "preco_atual": 89.9,
        "faixa_sugerida": {
            "min": 94.4,
            "max": 112.38
        },
        "motivo": "Peças similares no marketplace vendem em média 18% acima"
    },
    "tags_com_mais_sucesso": [
        {
            "tag": "parede",
            "taxa_conversao": 0.0387,
            "score_sucesso": 0.39,
            "buscas_7d_marketplace": 1322
        },
        {
            "tag": "decoracao-rustica",
            "taxa_conversao": 0.0317,
            "score_sucesso": 0.32,
            "buscas_7d_marketplace": 2829
        },
        {
            "tag": "vaso",
            "taxa_conversao": 0.028,
            "score_sucesso": 0.28,
            "buscas_7d_marketplace": 1048
        }
    ],
    "produtos_potencial_conversao": [
        {
            "product_id": "p_0877",
            "nome": "Jogo de xícaras artesanais",
            "conversao": 0.0039,
            "motivo": "Muitas visualizações e poucas compras: revise fotos, descrição ou preço"
        }
    ],
    "model_version": "mock-tags-0.0.1"
}
```

### Teste 3 — Registro de eventos e feedback (`/v1/events`)

```bash
curl -sS -X POST http://127.0.0.1:3000/v1/events \
  -H 'Content-Type: application/json' \
  -d '{"user_id": "u_83921", "event_type": "click", "product_id": "p_1042"}' | python3 -m json.tool
```

Resposta esperada (`received_at` muda a cada chamada: é o horário UTC do servidor):

```json
{
    "status": "accepted",
    "event_id": "evt_99812",
    "received_at": "2026-10-13T17:36:11.807790+00:00"
}
```

### Testes automatizados

```bash
just testes  # realiza todos os testes em test_service.py
```


## Tabela Requisitos/Endpoint

| Funcionalidade | Requisitos | Endpoint | Tipo
| --- | --- | --- | --- |
| **Recomendações personalizadas para a home** | (RF01, RF05, RF10, RF12) | `/v1/recommendations/home` | POST |
| **Insights para o artesão** | (RF08, com RF09 como dependência) | `/v1/recommendations/seller` | POST |
| **Registro de eventos e feedback** | (RF04, RF11) | `/v1/events` | POST |

# Recomendador no BentoML

Imagine uma feira de artesanato na internet. Tem jarro de barro, renda, xilogravura,
cesto de palha. A pessoa abre a página de um jarro de Tracunhaém. Embaixo da foto,
aparecem outras peças: um prato da mesma técnica, uma boneca de barro, e mais duas
sugestões que muita gente já pediu. Ninguém digitou “cerâmica” na busca. A loja
simplesmente **chutou com cuidado** o que ainda pode interessar.

Esse “chute com cuidado” é o **sistema de recomendação**. Sem ele, a pessoa só vê o
que ela mesma procura — e a maior parte do catálogo fica invisível. Com ele, a loja
usa o produto da página (e, neste material, o histórico de pedidos de exemplo) para
montar uma lista curta de **outros** produtos. Não é um chatbot: não conversa. Não é
um classificador genérico: não rotula texto. É um ranqueador: recebe um produto e
devolve outros, cada um com uma nota e um motivo legível.

Este repositório traz um catálogo pequeno de
peças pernambucanas, um treino que calcula popularidade e “aparecem juntos”, e um
serviço HTTP no BentoML que responde a essas sugestões. Você sobe com dois comandos,
confere no Swagger ou no `curl`, e depois lê as contas no caderno e nos slides.

Pastas irmãs (portas e artefatos) estão em [Variantes](#variantes), no fim deste
README — depois do baseline.

## Sinais que a loja observa

Antes de ranquear, a loja já acumula duas leituras do passado. Elas chegam ao
recomendador como matéria-prima da nota:

| Leitura | O que a loja vê | Papel na nota |
| --- | --- | --- |
| **Demanda** | Quantas vezes cada peça já foi pedida | Mostra o que a vitrine costuma vender bem |
| **Compra conjunta** | Quais peças saíram na mesma compra | Mostra pares que andam juntos |

Essas leituras viram as métricas da seção seguinte; a forma em JSON vem depois,
na [cesta de compra](#cesta-de-compra) e em [Popularidade e co-ocorrência](#popularidade-e-co-ocorrência).

## Métricas do projeto

Linguagem comum da ordenação — o que cada número (e cada rótulo) significa neste
material, ainda em prosa. O detalhe de cálculo e de campos JSON está nas seções
seguintes.

| Nome | Significado |
| --- | --- |
| **Popularidade** | Quão pedido é cada produto no histórico da loja. Vira um peso na ordenação. |
| **Co-ocorrência** | Quão frequentemente dois produtos saem na mesma compra. Reforça pares que andam juntos. |
| **Score** | Nota única que mistura esses sinais — e, nas variantes, sinais extras — para ranquear candidatos. |
| **Reason** | Rótulo legível do motivo da sugestão (`mesma_tecnica`, `complemento_popularidade`, ou os rótulos das variantes). |

A variante demográfica acrescenta **afinidade de perfil**; a de clustering acrescenta
**vizinhança de grupo**. Detalhe operacional no fim, em [Variantes](#variantes).

## Cesta de compra

Na literatura de *market basket analysis*, a mesma ideia aparece como **cesta de
mercado**: o conjunto de produtos que saíram juntos numa compra. Numa loja real, uma
**cesta** (ou carrinho fechado) é esse conjunto. Se alguém pediu jarro + prato +
boneca juntos, esses três ids formam uma cesta. O recomendador usa esse padrão para
aprender associação entre itens: produtos que compartilham cestas tendem a se
reforçar na nota de **co-ocorrência**.

Neste material as cestas são **exemplos sintéticos** (não tickets de loja real).
Elas vivem em [`dados/catalogo.json`](dados/catalogo.json), no array `cestas`:
cada elemento é uma lista de ids de produto.

```json
"cestas": [
  ["p01", "p02", "p03"],
  ["p01", "p02"],
  ["p04", "p05", "p06"]
]
```

A primeira linha lê-se: “numa compra de exemplo saíram `p01`, `p02` e `p03`
juntos”. Ordem dentro da lista não importa para o treino; o que importa é o
**par** (a, b) aparecer na mesma cesta. O catálogo de itens (nome, técnica,
região, **`pedidos`**) fica no array irmão `produtos` — detalhes em
[`dados/README.md`](dados/README.md).

## Popularidade e co-ocorrência

Dois números que o treino tira do JSON e que o serviço usa na nota. Ambos acabam
em escala **0…1**, para poderem entrar na mesma fórmula de score. Vêm de **chaves
diferentes** do mesmo arquivo:

| Sinal | Array / campo no JSON | O que mede |
| --- | --- | --- |
| Popularidade | `produtos[].pedidos` | Quão pedido é o item (contagem por produto) |
| Co-ocorrência | `cestas` | Quão frequentemente dois ids saem **na mesma** compra |

Não misture: contar em quantas cestas um id aparece **não** é o que este baseline
faz para popularidade. Aqui a demanda já veio agregada no campo `pedidos` de cada
produto; as `cestas` servem só para pares.

### Popularidade

**Popularidade** é quão pedido é cada produto. No dataset isso é o campo `pedidos`
dentro de cada objeto de `produtos` — por exemplo `"pedidos": 42` no jarro `p01`.
Não lemos `cestas` neste passo. No treino copiamos esses valores para um mapa
`pedidos_brutos` e viramos um número entre 0 e 1 (`pop`) dividindo pelo maior
`pedidos` do catálogo — o item mais pedido fica em 1,0; os outros ficam abaixo.

Pseudocódigo a partir do JSON (`produtos` apenas):

```text
# Variáveis:
#   catalogo       — objeto JSON raiz (lido de catalogo.json)
#   produtos       — lista catalogo["produtos"]
#   p              — um registro {id, nome, tecnica, regiao, pedidos}
#   pedidos_brutos — mapa id → pedidos crus (número)
#   max_pedidos    — maior valor em pedidos_brutos
#   pop            — mapa id → popularidade normalizada em 0…1
#   id             — chave de produto

produtos ← catalogo["produtos"]

para cada p em produtos:
    pedidos_brutos[p.id] ← p.pedidos     # campo pedidos; não vem de cestas

max_pedidos ← máximo dos valores em pedidos_brutos
para cada id:
    pop[id] ← pedidos_brutos[id] / max_pedidos
```

No Python (`treino.py`, função `main`) os nomes batem com o pseudocódigo:

| Pseudocódigo | Código |
| --- | --- |
| `catalogo` | `catalogo = json.loads(…)` |
| Ler `produtos` | `produtos = {p["id"]: p for p in catalogo["produtos"]}` |
| `pedidos_brutos` | `pedidos_brutos = {pid: float(p["pedidos"]) for …}` |
| `max_pedidos` | `max_pedidos = max(pedidos_brutos.values()) or 1.0` |
| `pop[id]` | `pop = {pid: n / max_pedidos for …}` |

O artefato guarda **os dois**: `pedidos_brutos` (cru) e `pop` (0…1). O serviço
usa `pop` no score.

### Co-ocorrência

**Co-ocorrência** mede, para cada produto A, quão frequentemente outro produto B
sai **na mesma cesta** de exemplo (a mesma compra fictícia do dataset). Neste passo
usamos só o array `cestas` — o campo `pedidos` não entra.

Como contamos: se uma cesta traz `[p01, p02, p03]`, registramos que `p01` apareceu
com `p02` e com `p03`, que `p02` apareceu com `p01` e `p03`, e assim por diante
(o par é simétrico). No fim, para cada produto A, dividimos essas contagens pelo
parceiro que mais apareceu junto com A. O resultado fica entre 0 e 1: o parceiro
mais comum de A vale 1,0; os outros ficam abaixo.

Isso **não** olha a técnica artesanal. Dois produtos podem sair juntos muitas vezes
e ter técnicas diferentes; ou ser da mesma técnica e nunca terem saído na mesma
cesta. A técnica é um filtro **à parte**, aplicado depois em `service.py`, quando
a vitrine já pediu recomendações para o produto da página.

```mermaid
sequenceDiagram
  participant JSON as catalogo.json
  participant T as treino.py
  participant C as conta / cooc
  JSON->>T: cestas (listas de ids)
  loop cada cesta
    T->>C: para cada par (A, B) na cesta: conta[A][B] += 1
  end
  T->>C: para cada A: cooc[A][B] = conta[A][B] / max_parceiro(A)
  Note over C: Artefato guarda cooc (0…1), não as cestas crus
```

Pseudocódigo a partir do JSON:

```text
# Variáveis:
#   catalogo — objeto JSON raiz
#   cestas   — lista catalogo["cestas"] (cada item = lista de ids)
#   cesta    — uma compra de exemplo (lista de ids)
#   ids      — ids únicos dentro de uma cesta
#   a, b     — dois ids distintos formando um par
#   conta    — mapa produto_ref → (vizinho → contagem bruta)
#   m        — máximo de conta[a][*] para o produto de referência a
#   cooc     — mapa produto_ref → (vizinho → co-ocorrência em 0…1)

cestas ← catalogo["cestas"]

# contagem bruta de pares (simétrica)
para cada cesta em cestas:
    ids ← únicos na cesta
    para cada par ordenado (a, b) com a ≠ b entre ids:
        conta[a][b] ← conta[a][b] + 1
        conta[b][a] ← conta[b][a] + 1

# normalização por produto de referência (cada linha do mapa)
para cada produto de referência a:
    m ← máximo de conta[a][*]
    para cada vizinho b:
        cooc[a][b] ← conta[a][b] / m
```

No Python isso é a função `_cooc` + a chamada em `main`:

| Pseudocódigo | Código |
| --- | --- |
| Percorrer `cestas` | `for cesta in cestas:` |
| `ids` (únicos) | `ids = list(dict.fromkeys(cesta))` |
| `conta[a][b]` | `conta[a][b] += 1.0` e `conta[b][a] += 1.0` |
| `cooc[a][b]` | `cooc[a] = {b: v / m for b, v in vizinhos.items()}` |
| Guardar no artefato | `cooc = _cooc(catalogo["cestas"])` |

No artefato o mapa se chama `cooc`: `cooc[pagina][candidato]` é a co-ocorrência
normalizada do candidato dado o produto da página (0 se nunca apareceram juntos).

## Workflow

Dois momentos distintos — e, em MLOps, dois **papéis** distintos. Não misture na
mesma sequência: quem treina não é quem clica na vitrine.

| Momento | Em MLOps | Neste repo | Quem age | Frequência |
| --- | --- | --- | --- | --- |
| **Treino** (offline) | *training* / *batch* — a partir dos dados, produz um artefato | `just treino` → `treino.py` | Operador (local, CI/CD ou job agendado) | Rara: quando o catálogo ou a regra mudam |
| **Inferência** (online) | *inference* / *serving* — aplica o artefato a um pedido novo | `just serve` → `POST /recomendar` | A vitrine (cliente HTTP); o serviço só responde | A cada página de produto |

**Treino** lê o histórico (aqui: `catalogo.json`), calcula `pop` e `cooc`, e **grava**
o pickle no model store (`recomendador:…`). Sem esse passo, o serviço não tem o que
carregar.

**Inferência** sobe o HTTP uma vez (`just serve`), carrega `recomendador:latest`, e
em cada clique aplica a regra já pronta — **não** relê o JSON nem recalcula o
catálogo. A saída é JSON para a WEB desenhar a faixa de sugestões.

No mapa de dependências (ainda juntos, só para ver a seta do artefato):

```mermaid
flowchart LR
  catalogo["catalogo.json"] --> treino["treino.py"]
  treino --> store["model store<br/>(pickle)"]
  store --> service["service.py"]
  web["vitrine WEB"] -->|"POST /recomendar"| service
  service --> jsonOut["JSON<br/>(items, reason, score)"]
```

No mapa acima, à **esquerda** do model store fica o **treino**; à **direita**, a
**inferência**. A vitrine fala com `service.py`; o JSON de dados alimenta o treino.

### Sequência 1 — só o treino (offline)

Aqui o ator é quem prepara o artefato. A vitrine **não** aparece.

```mermaid
sequenceDiagram
  actor Op as Operador (treino)
  participant JSON as catalogo.json
  participant Treino as treino.py
  participant Store as BentoML model store

  Op->>Treino: just treino
  Treino->>JSON: lê produtos + cestas
  Treino->>Treino: calcula pop e cooc
  Treino->>Store: grava artefato recomendador:…
  Treino-->>Op: imprime tag no store
```

### Sequência 2 — só a inferência (online)

Outro momento, outros atores: sobe o serviço (ainda o operador, uma vez) e depois
só a vitrine conversa com a API. O treino **não** roda de novo a cada clique.

```mermaid
sequenceDiagram
  actor Op as Operador (serve)
  participant Store as BentoML model store
  participant Serve as service.py
  participant Web as vitrine WEB

  Op->>Serve: just serve
  Serve->>Store: carrega recomendador:latest
  Note over Serve: processo HTTP fica no ar

  loop cada página de produto
    Web->>Serve: POST /recomendar (pagina, limite, excluir)
    Serve->>Serve: regra sobre o artefato (sem reler o JSON)
    Serve-->>Web: JSON (items, reason, score)
  end
```

Mudou o JSON? Isso é de novo **treino**: rode `just treino` e reinicie o serve (ou
deixe o `--reload` pegar a tag `latest`). Enquanto o catálogo não muda, só a
sequência 2 se repete.

## Visão geral do algoritmo

O fluxo cabe em cinco passos, na ordem em que o serviço decide a lista:

```mermaid
flowchart TD
  ctx["1. Contexto<br/>pagina, limite, excluir"] --> filtro["2. Mesma técnica<br/>candidatos"]
  filtro --> nota["3. Score e ordem<br/>0,7×pop + 0,3×cooc"]
  nota --> falta{"Faltam vagas?"}
  falta -->|sim| comp["4. Complemento<br/>por popularidade"]
  falta -->|não| resp["5. Resposta JSON"]
  comp --> resp
```

O mesmo caminho, como troca de mensagens dentro de **um** pedido:

```mermaid
sequenceDiagram
  participant Web as vitrine WEB
  participant API as recomendar
  participant Art as artefato

  Web->>API: produto_na_pagina, limite, excluir
  API->>Art: le produto da pagina
  API->>API: excluir = excluir + pagina
  API->>Art: candidatos mesma tecnica fora de excluir
  loop cada candidato
    API->>Art: pop e cooc do candidato
    API->>API: score = 0.7*pop + 0.3*cooc
  end
  API->>API: ordena e corta em limite
  alt ainda faltam vagas
    API->>Art: completa com mais pedidos do catalogo
  end
  API-->>Web: items, reason, complemento_usado
```


1. **Contexto.** A vitrine manda o id do produto aberto (`produto_na_pagina`), quantas
   sugestões quer (`limite`) e ids a omitir (`excluir`). O próprio produto da página
   entra automaticamente na lista de omitidos.
2. **Mesma técnica.** Entre os demais itens do catálogo, ficam só os que têm a mesma
   `tecnica` artesanal (por exemplo, todos de *ceramica* se a página é um jarro de barro).
3. **Nota e ordem nesse grupo.** Cada candidato recebe
   $`\mathrm{score} = 0.7 \times \mathrm{pop} + 0.3 \times \mathrm{cooc}`$.
   A popularidade vem dos `pedidos` normalizados; a co-ocorrência mede quantas vezes
   dois produtos apareceram juntos nas cestas de exemplo do dataset. Ordenamos do maior
   score para o menor e pegamos até `limite` itens. O motivo gravado é `mesma_tecnica`.

   **Por que essa fórmula?** Mistura dois sinais: “muita gente pede isso” (popularidade)
   e “costuma sair junto com o produto da página” (co-ocorrência). O peso **0,7 / 0,3**
   privilegia a demanda geral dentro da mesma técnica, sem ignorar o histórico das
   cestas. Os pesos ficam em `service.py` — dá para trocá-los e comparar o JSON.

   **O que é “normalizado”?** Os `pedidos` brutos são contagens (8, 28, 42…). Se
   somássemos pedidos crus com co-ocorrência (que já está em 0…1), o número grande
   dominaria a nota. Normalizar aqui significa **dividir pelo máximo do catálogo**:


$$
\mathrm{pop}_i = \frac{\mathrm{pedidos}_i}{\max_j \mathrm{pedidos}_j}
$$

   Assim a popularidade também fica entre 0 e 1 (o jarro com 42 pedidos vira 1,0; quem
   tem 21 vira 0,5). A co-ocorrência já nasce normalizada **por produto de referência**:
   para o produto da página, contamos quantas vezes cada vizinho saiu na mesma cesta e
   dividimos pelo vizinho mais frequente daquele produto.

   Pseudocódigo (mesmo grupo, após filtrar técnica e exclusões):

   ```text
   # Variáveis:
   #   produtos   — mapa id → registro (já no artefato)
   #   pop        — mapa id → popularidade 0…1 (artefato.pop)
   #   cooc       — mapa produto_ref → (vizinho → 0…1) (artefato.cooc)
   #   pagina     — id do produto_na_pagina
   #   excluir    — conjunto de ids a omitir (mais a própria pagina)
   #   candidatos — lista de ids mesma tecnica, fora de excluir
   #   c          — um id candidato
   #   score      — mapa id → nota composta
   #   limite     — quantos itens devolver
   #   escolhidos — lista final ordenada (até limite)

   # pop e cooc já vêm do artefato; aqui só a montagem da lista:
   candidatos ← produtos com mesma tecnica que pagina
                e id ∉ excluir ∪ {pagina}

   para cada c em candidatos:
       score[c] ← 0.7 * pop[c] + 0.3 * cooc[pagina].get(c, 0)

   ordenar candidatos por score decrescente
   escolhidos ← primeiros limite de candidatos
   # reason ← "mesma_tecnica"
   ```
4. **Complemento por popularidade.** Se ainda faltarem vagas (poucos produtos daquela
   técnica), completamos com os mais pedidos do catálogo inteiro, ainda respeitando
   `excluir`. Nesses, $`\mathrm{score} = 0.5 \times \mathrm{pop}`$ e o motivo é
   `complemento_popularidade`. O campo `complemento_usado` fica `true`.
5. **Resposta.** Devolvemos a lista com id, nome, técnica, região, score, motivo e rank —
   pronta para a WEB desenhar a faixa “Você também pode gostar”.

Não há rede neural nem modelo de linguagem neste baseline: são contagens e uma regra
fixa, auditáveis no papel (ver [`material/calculos-trabalhados.md`](material/calculos-trabalhados.md)).
O dataset e o significado de cada campo estão em [`dados/README.md`](dados/README.md).

---

## O que a API espera e o que ela devolve

O serviço escuta em `http://127.0.0.1:3000` depois de `just serve`. O endpoint útil
para a vitrine é:

```http
POST /recomendar
Content-Type: application/json
```

### Entrada

| Campo | Tipo | Exemplo | Significado |
| --- | --- | --- | --- |
| `produto_na_pagina` | string | `"p01"` | Id do produto aberto na tela (obrigatório) |
| `limite` | inteiro | `4` | Quantos produtos sugerir (padrão 4) |
| `excluir` | lista de strings | `[]` | Ids que não devem voltar (já vistos, já no carrinho, etc.) |

O próprio `produto_na_pagina` **nunca** entra na lista de saída: a loja não recomenda
o item que a pessoa já está olhando.

### Saída (sucesso)

JSON com:

| Campo | Significado |
| --- | --- |
| `items` | Lista ordenada de sugestões |
| `items[].product_id` | Id no catálogo |
| `items[].nome` | Nome legível |
| `items[].tecnica` | Técnica artesanal (ceramica, renda, …) |
| `items[].regiao` | Polo / região |
| `items[].score` | Nota numérica usada na ordenação |
| `items[].reason` | Motivo: `mesma_tecnica` ou `complemento_popularidade` |
| `items[].rank` | Posição 1…N |
| `strategy` | Nome da estratégia gravada no treino |
| `complemento_usado` | `true` se faltaram candidatos da mesma técnica e a lista foi completada com popularidade geral |
| `produto_na_pagina` | Eco do produto de contexto (id, nome, técnica, região) |
| `modelo` | Tag do artefato no store do BentoML |

### Saída (produto inexistente)

Se o id não estiver no catálogo:

```json
{
  "erro": "produto_inexistente",
  "produto_na_pagina": "nao-existe",
  "items": []
}
```

---

## Como subir e o que esperar nos testes

Pré-requisitos: [uv](https://docs.astral.sh/uv/) e [just](https://github.com/casey/just).
Nesta pasta:

```bash
just treino    # lê dados/catalogo.json, grava o modelo no store do BentoML
just serve     # sobe o serviço (deixe este terminal aberto)
```

Quer a **mesma** API numa imagem Docker? Depois do treino:
`just imagem` → `just serve-container` (detalhes em
[Empacote e container](#empacote-e-container-bento--imagem-oci)).

Em outro terminal, ou pela UI em <http://127.0.0.1:3000>:

### Exemplo 1 — página do jarro (`p01`), quatro sugestões

É o caso trabalhado em [`material/calculos-trabalhados.md`](material/calculos-trabalhados.md)
(as contas de lá usam o catálogo original de 12 produtos; os valores abaixo já
refletem o catálogo expandido).

```bash
just curl-exemplo
```

Corpo enviado:

```json
{"produto_na_pagina": "p01", "limite": 4, "excluir": []}
```

Resultado esperado (ordem e motivos):

| rank | produto | reason | score (aprox.) |
| ---: | --- | --- | ---: |
| 1 | Prato esmaltado Tracunhaém (`p02`) | `mesma_tecnica` | ≈ 0,77 |
| 2 | Vaso de barro Alto do Moura (`p13`) | `mesma_tecnica` | ≈ 0,48 |
| 3 | Boneca de barro (`p03`) | `mesma_tecnica` | ≈ 0,47 |
| 4 | Boneco de barro figurativo (`p14`) | `mesma_tecnica` | ≈ 0,41 |

`complemento_usado` deve ser **false**: o catálogo tem seis outras cerâmicas
(`p02`, `p03`, `p13`, `p14`, `p15`, `p38`), então as quatro vagas saem da mesma
técnica. Repare que `p13` e `p14` têm os mesmos 20 pedidos, mas `p13` saiu junto
com o jarro em duas cestas e `p14` em uma só: a co-ocorrência separa os dois, e
`p03` (19 pedidos, também duas cestas com o jarro) fica entre eles.

### Exemplo 2 — forçar o complemento (pouca mesma técnica)

```bash
just curl-complemento
```

Corpo:

```json
{"produto_na_pagina": "p12", "limite": 4, "excluir": ["p10", "p11"]}
```

Aqui o produto da página é o sousplat de palha (`p12`, cestaria). Excluímos dois
outros de cestaria (`p10`, `p11`). Sobram só **dois** candidatos da mesma técnica
(`p34`, `p35`), menos que o `limite` de 4 → as duas últimas vagas vêm dos mais
pedidos do catálogo inteiro (`complemento_usado`: true).

| rank | produto | reason | score (aprox.) |
| ---: | --- | --- | ---: |
| 1 | Chapéu de palha (`p35`) | `mesma_tecnica` | ≈ 0,32 |
| 2 | Esteira de palha (`p34`) | `mesma_tecnica` | ≈ 0,07 |
| 3 | Jarro barro Tracunhaém (`p01`) | `complemento_popularidade` | ≈ 0,50 |
| 4 | Xilogravura Bezerros (`p22`) | `complemento_popularidade` | ≈ 0,45 |

O `rank` não segue o `score` aqui: os itens da mesma técnica vêm sempre primeiro,
e o complemento só entra depois deles, mesmo com nota maior. Como `p12` não
aparece em nenhuma cesta, a co-ocorrência é zero e a nota dos dois primeiros é
só `0,7 × pop`.

Para ver o complemento preencher a lista **inteira**, use `just curl-tecnica-unica`
(`p31`, único produto de funilaria).

### Exemplo 3 — id que não existe

```bash
just curl-inexistente
```

Deve devolver `erro: "produto_inexistente"` e `items` vazio, sem inventar produtos.

---

## Empacote e container (Bento → imagem OCI)

Até aqui o serviço sobe com `just serve`: processo Python na sua máquina, lendo o
model store local. **Containerizar** é o passo seguinte — útil quando a pergunta
é: “como levo essa API para outro computador sem repetir o ambiente?”

Três ideias, nesta ordem:

| Nome | O que é | Comando neste repo |
| --- | --- | --- |
| **Modelo** | Artefato do treino (`recomendador:…` no store) | `just treino` |
| **Bento** | Pacote do *serviço de inferência*: código + deps + referência ao modelo | `just build` |
| **Imagem OCI** | Esse Bento virado container (Docker/Podman/…) | `just containerize` |

O container embala o **pipeline online** (o que `service.py` faz). Ele **não**
reexecuta o treino: quem gerou `pop` e `cooc` continua sendo `just treino` na
máquina (ou no CI) *antes* do `build`.

```mermaid
flowchart LR
  treino["just treino<br/>modelo no store"] --> build["just build<br/>Bento"]
  build --> img["just containerize<br/>imagem OCI"]
  img --> run["just serve-container<br/>docker run :3000"]
  run --> curl["just curl-exemplo<br/>mesmo POST"]
```

### O que o `bentofile.yaml` congela

Na raiz, [`bentofile.yaml`](bentofile.yaml) declara o que entra no Bento:

| Campo | Neste baseline | Papel |
| --- | --- | --- |
| `service` | `service:Recomendador` | Classe HTTP a subir |
| `include` | `*.py`, `dados/*.json` | Código e catálogo que viajam com o pacote |
| `python.packages` | `bentoml` | Deps instaladas na imagem |
| `models` | `recomendador:latest` | Artefato do treino embutido no Bento |

Sem `just treino` antes, o `build` falha ou fica incompleto: não há
`recomendador:latest` para embutir.

### Demonstração (baseline)

Pré-requisitos extras: [Docker](https://docs.docker.com/get-docker/) (ou outro
builder OCI) **rodando**. Pare um `just serve` local se ele já estiver na porta
3000 — os dois não compartilham a mesma porta ao mesmo tempo.

```bash
just treino           # 1) modelo no store (se ainda não rodou)
just imagem           # 2+3) build (Bento) + containerize (tag estável)
just serve-container  # 4) docker run --rm -p 3000:3000 recomendador:aula serve
```

`just imagem` é só o atalho de `just build` seguido de `just containerize`. Os
passos separados existem para conferir cada artefato:

```bash
just build            # cria o Bento Recomendador:…
just listar-bentos    # confere no store de Bentos
just containerize     # gera a imagem Docker recomendador:aula
just listar-imagens   # confere no Docker local
just serve-container
```

Em outro terminal, **os mesmos curls** do serve local:

```bash
just curl-exemplo
just curl-complemento
just curl-inexistente
```

O contrato HTTP não muda. O que muda é *onde* o processo roda: venv da pasta
versus imagem OCI. A tag fixa `recomendador:aula` evita decorar o hash que o
BentoML atribui a cada build e deixa o `docker run` legível.

Equivalente sem `just`:

```bash
uv run bentoml build
uv run bentoml containerize Recomendador:latest --image-tag recomendador:aula
docker run --rm -p 3000:3000 recomendador:aula serve
```

Pastas irmãs: cada uma tem o próprio `bentofile.yaml`, artefato e tag de imagem
(ver [Variantes](#variantes)). A porta no *host* continua a da pasta; dentro do
container a API escuta 3000, por isso o mapeamento `HOST:3000`.

Exemplo (clustering):

```bash
cd variante-clustering
just treino
just imagem
just serve-container   # -p 3002:3000
just curl-exemplo
```

### O que este passo não é

Não é orquestração (Kubernetes), não é registro remoto (`docker push`), não é
rebuild automático a cada clique. É a prova mínima de **portabilidade da
inferência**: treinou uma vez, empacotou o serviço, subiu a imagem, bateu o
mesmo `POST /recomendar`.

---

## Mergulho técnico

### Ideia da regra (baseline, sem rede neural)

1. **Popularidade.** Cada produto tem um contador `pedidos` no JSON. No treino,
   normalizamos pelo máximo do catálogo:


$$
\mathrm{pop}_i = \frac{\mathrm{pedidos}_i}{\max_j \mathrm{pedidos}_j}
$$

2. **Co-ocorrência.** Nas cestas de exemplo, contamos quantas vezes dois produtos
   saem juntos; para cada produto de referência, normalizamos pelo vizinho mais
   frequente daquele produto.
3. **Candidatos.** Todos os produtos com a **mesma técnica** do item da página,
   exceto ele próprio e os ids em `excluir`.
4. **Ordenação (mesma técnica).**
   $`\mathrm{score} = 0.7 \cdot \mathrm{pop} + 0.3 \cdot \mathrm{cooc}`$.
5. **Complemento.** Se a lista ainda for menor que `limite`, completamos com os
   produtos de maior `pedidos` no catálogo (mesmo filtro de exclusão). Para esses,
   $`\mathrm{score} = 0.5 \cdot \mathrm{pop}`$.

O campo `regiao` vai no JSON de saída (a vitrine pode exibir), mas **esta versão
não usa região na ordenação**.

### Mapa de arquivos

| Arquivo | Papel |
| --- | --- |
| [`dados/catalogo.json`](dados/catalogo.json) | 40 produtos (10 técnicas) + 37 cestas de exemplo |
| [`treino.py`](treino.py) | Calcula popularidade e co-ocorrência; grava pickle no model store (`recomendador:…`) |
| [`service.py`](service.py) | Classe BentoML `Recomendador`; API `recomendar` |
| [`bentofile.yaml`](bentofile.yaml) | Empacote opcional: o que entra no Bento / imagem |
| [`justfile`](justfile) | Atalhos `treino`, `serve`, `imagem`, `serve-container`, curls |
| [`material/calculos-trabalhados.md`](material/calculos-trabalhados.md) | Contas do exemplo `p01` no papel |
| [`slides/`](slides/) | Slides (arco didático; ver [`slides/README.md`](slides/README.md)) |
| [`scripts/gerar_slides.py`](scripts/gerar_slides.py) | Regenera o deck (`just slides`) |
| [`variante-demografica/`](variante-demografica/) | Variante com `clientes` + `compras` e score demográfico |
| [`variante-clustering/`](variante-clustering/) | Cluster hierárquico + intercalação `cesta` / `cluster` |

### Dependências e ambiente

- Python **≥ 3.13**, gerenciado por **uv** (`pyproject.toml` / `uv.lock`).
- Dependência de runtime: **BentoML**.
- Grupo `dev`: **python-pptx** (só para gerar slides).
- Comandos passam por `uv run …` (via `just`), com venv local nesta pasta.

### Ciclo treino → serve

`treino.py` lê o JSON, monta um dicionário Python e o serializa com `pickle` dentro
de um modelo BentoML chamado `recomendador`. `service.py` faz
`bentoml.models.get("recomendador:latest")` e carrega esse artefato na subida do
serviço. Mudou o catálogo? Rode `just treino` de novo e reinicie (ou confie no
`--reload` do `just serve`).

Para levar o **mesmo** serviço numa imagem OCI (sem depender do venv da pasta),
veja [Empacote e container](#empacote-e-container-bento--imagem-oci):
`just treino` → `just imagem` → `just serve-container`.

### O que este material não é

Não é aprendizado profundo, não é filtragem colaborativa com matriz de usuários
reais, não autentica, não persiste log de impressões, não avalia Precision@k.
É um **baseline** com técnica, popularidade, exclusões, JSON e motivo legível —
servido como API para a WEB consumir.

### Para onde ir depois (fora deste repositório)

1. Ligar `POST /recomendar` à vitrine do marketplace da disciplina.
2. Incluir região (ou popularidade por polo) na ordenação, se o requisito exigir.
3. Trocar a regra por um modelo de aprendizado de máquina — mapa concreto no fim
   deste README ([Do Data Science à Machine Learning](#ds-para-ml-microsoft-learn)),
   ancorado em
   [Fundamentos do aprendizado de máquina](https://learn.microsoft.com/pt-br/training/modules/fundamentals-machine-learning/)
   (Microsoft Learn, pt-BR).

Nada disso é necessário para este pacote rodar sozinho.

### Licença

**GPL-3.0** — ver [`LICENSE`](LICENSE).

BentoML (Apache-2.0) e python-pptx (MIT) têm licenças próprias; elas não alteram a
licença deste código.

---

No fim das contas, um marketplace precisa de recomendação pela mesma razão que a
feira física coloca peças parecidas na mesma banca: a pessoa já mostrou um interesse
(abriu um jarro) e a loja responde com vizinhança útil, sem obrigá-la a adivinhar o
vocabulário do catálogo. Este projeto deixa essa ideia pequena, auditável e no ar —
você vê o JSON, confere as contas no caderno e entende cada `reason`. O contrato HTTP
e a lógica de baseline estão prontos para a vitrine consumir e, se quiser, evoluir.

## Nomes neste repo e na literatura de recomendação

Os nomes da esquerda são os deste projeto. Os da direita são aproximações úteis ao
ler livros e artigos de *recommender systems*.

| Neste repo | Na literatura (aprox.) |
| --- | --- |
| `pop` / `pedidos_brutos` | *popularity baseline* (não personalizado) |
| `cooc` / `cestas` | co-ocorrência item–item; sinal de associação |
| filtro por `tecnica` | filtragem baseada em conteúdo (atributo do item) |
| score `0,7×pop + 0,3×cooc` | combinação híbrida ponderada (regra fixa) |
| complemento por popularidade | *fallback* / preenchimento por cobertura |
| `reason` no JSON | explicabilidade por regra |
| artefato + `POST /recomendar` | *offline compute* + *online inference* |

Este baseline é **ciência de dados + serviço**: agregamos contagens, aplicamos uma
fórmula e servimos JSON. Ainda **não** é aprendizado de máquina no sentido do
módulo Microsoft Learn abaixo (não há rótulo supervisionado, divisão treino/validação
nem métrica de erro do preditor).

## Do Data Science à Machine Learning (Microsoft Learn)

<a id="ds-para-ml-microsoft-learn"></a>

Módulo de referência:
[Introdução aos conceitos de Machine Learning](https://learn.microsoft.com/pt-br/training/modules/fundamentals-machine-learning/)
(11 unidades). A própria introdução do módulo diz que ML fica na interseção de
**ciência de dados** e **engenharia de software**: dados do passado → modelo
preditivo → *inferência* dentro de um serviço. Este repositório já cobre o lado
“serviço” (BentoML) e o lado “explorar/agregar dados”; falta o miolo preditivo.

### O que muda na formulação

| Hoje (regra) | Amanhã (ML) |
| --- | --- |
| Candidatos + fórmula fixa | Observações com **recursos** (features) e **rótulo** (label) |
| Um pickle de mapas | Artefato de modelo (ex.: scikit-learn) com parâmetros aprendidos |
| Sem métrica de acerto | Treino / validação + MAE, acurácia, Precision@k, etc. |
| `reason` = nome da regra | `reason` pode citar modelo + top features (ou continuar a regra como baseline A/B) |

O **contrato HTTP** pode permanecer o mesmo: `POST /recomendar` com o mesmo I/O;
o que muda é a **origem do score** (regra fixa hoje → modelo aprendido amanhã).

Um caminho natural para recomendação: cada linha de treino é um par
`(pagina, candidato)` (e, se houver log, o usuário/sessão). O rótulo pode ser
“foi clicado / foi comprado / apareceu na mesma cesta” (binário) ou um score de
engajamento (regressão). Na inferência, o serviço ainda recebe `produto_na_pagina`
e devolve top‑k — só a origem da `score` muda.

### Mapa unidade → o que usar neste projeto

Links em pt-BR, mesma ordem do módulo.

| Unidade | Link | Como encaixa neste recomendador |
| --- | --- | --- |
| 1. Introdução | [1-introduction](https://learn.microsoft.com/pt-br/training/modules/fundamentals-machine-learning/1-introduction) | Vocabulário *features / labels / inferência*. Situar o baseline atual como preparação de dados + API, não como modelo treinado. |
| 2. O que é um modelo | [2-what-is-machine-learning](https://learn.microsoft.com/pt-br/training/modules/fundamentals-machine-learning/2-what-is-machine-learning) | Contraste: hoje os “parâmetros” (0,7 / 0,3) são escolhidos à mão; no ML eles (ou outros) saem do treino. |
| 3. Tipos de modelo | [3-types-of-machine-learning](https://learn.microsoft.com/pt-br/training/modules/fundamentals-machine-learning/3-types-of-machine-learning) | Escolher a família: supervisionado (há rótulo de clique/compra/cesta) vs não supervisionado (só atributos do catálogo). |
| 4. Regressão | [4-regression](https://learn.microsoft.com/pt-br/training/modules/fundamentals-machine-learning/4-regression) | Predizer um **score numérico** (ex.: probabilidade calibrada, pedidos esperados, afinidade). Treino/validação + MAE / RMSE / R² como no módulo — no lugar de só ordenar por regra. |
| 5. Classificação binária | [5-binary-classification](https://learn.microsoft.com/pt-br/training/modules/fundamentals-machine-learning/5-binary-classification) | Rótulo “este candidato é relevante dado `pagina`?” (clique, compra, par na cesta). Inferência: pontuar candidatos e ordenar pela probabilidade positiva. |
| 6. Classificação multiclasse | [6-multiclass-classification](https://learn.microsoft.com/pt-br/training/modules/fundamentals-machine-learning/6-multiclass-classification) | Predizer o **próximo id** entre muitos — viável com catálogo pequeno deste material; em loja real costuma virar ranking / top‑k, não uma classe única. |
| 7. Clustering | [7-clustering](https://learn.microsoft.com/pt-br/training/modules/fundamentals-machine-learning/7-clustering) | Substituir ou enriquecer o filtro manual por `tecnica`: agrupar produtos por atributos (e depois rotular clusters, se quiser classificação). |
| 8. Aprendizado profundo | [8-deep-learning](https://learn.microsoft.com/pt-br/training/modules/fundamentals-machine-learning/8-deep-learning) | Opcional e **fora** do próximo passo deste baseline; só depois de haver rótulos, métricas e um modelo tabular simples. |
| 9. Exercício (cenários) | [9-exercise](https://learn.microsoft.com/pt-br/training/modules/fundamentals-machine-learning/9-exercise) | Praticar o enquadramento: “sorvete/pinguim/diabetes” do módulo ↔ “par (página, candidato) → engajou?”. |

### Ordem sugerida na prática (teórica → código)

1. Ler unidades **1–3** e escrever no papel: features do par, rótulo, e o que o
   `POST /recomendar` continua recebendo.
2. Com log ou cestas como rótulo fraco, seguir **5** (binário) ou **4** (score);
   usar **7** se a dor for descobrir grupos além de `tecnica`.
3. Avaliar com holdout (como o módulo mostra na regressão) antes de trocar a
   regra no serviço — manter este baseline disponível para comparar.
4. Só então apontar `service.py` para o novo artefato; o contrato HTTP pode
   permanecer o mesmo.

Caminho Microsoft Learn seguinte (já com exercícios scikit-learn), quando forem
implementar de verdade:
[Criar modelos de machine learning](https://learn.microsoft.com/pt-br/training/paths/create-machine-learn-models/).

## Variantes

O **baseline** é a raiz; as pastas irmãs têm artefato BentoML, porta HTTP e imagem
OCI próprios (cada uma grava a própria tag — o baseline continua em
`recomendador:latest`).

| Pasta | Porta | Artefato | Imagem OCI | O que acrescenta |
| --- | ---: | --- | --- | --- |
| [`.`](.) (raiz / baseline) | 3000 | `recomendador` | `recomendador:aula` | técnica + `pop` + `cooc` + complemento por popularidade |
| [`variante-demografica/`](variante-demografica/) | 3001 | `recomendador-demo` | `recomendador-demo:aula` | `clientes` + `compras`; score com afinidade demográfica |
| [`variante-clustering/`](variante-clustering/) | 3002 | `recomendador-cluster` | `recomendador-cluster:aula` | cluster hierárquico (dendrograma); lista intercalada `cesta`/`cluster` |

Receitas de container em qualquer pasta: `just imagem` · `just serve-container`
(ver [Empacote e container](#empacote-e-container-bento--imagem-oci)).

### Baseline (raiz) — só o produto da página

A pessoa abre o jarro. A loja responde com o que já sabe do **catálogo** e das
**compras de exemplo**: filtra pela mesma técnica artesanal, ordena por
popularidade e co-ocorrência, e completa a lista com os mais pedidos se ainda
houver vaga. O motivo de cada sugestão vem no campo `reason`
(`mesma_tecnica` ou `complemento_popularidade`).

- **Regra:** candidatos da mesma `tecnica`;  
  $`\mathrm{score} = 0.7 \times \mathrm{pop} + 0.3 \times \mathrm{cooc}`$; se faltarem
  vagas, completa com os mais pedidos (`complemento_popularidade`).
- **Subir:** `just treino` · `just serve` · `just curl-exemplo`.
- **Container:** `just imagem` · `just serve-container` · mesmos curls.
- **Leitura:** seções [Cesta](#cesta-de-compra) → [Workflow](#workflow) → [API](#o-que-a-api-espera-e-o-que-ela-devolve).

### Variante demográfica — a loja também sabe *quem* olha

Mesma vitrine, com um perfil sintético a mais: faixa etária, técnicas e polos
preferidos, mais um histórico curto de compras por cliente. O treino prepara
`pop` / `cooc` **e** popularidade por faixa; a inferência mistura isso na nota
`demo`. Com `cliente_id`, a lista puxa afinidade de perfil; sem `cliente_id`, a
API ainda responde — a parte demográfica da nota fica em zero e os pesos do
artefato seguem valendo.

- **Dados extras:** `clientes[]` e `compras[]` em
  [`variante-demografica/dados/`](variante-demografica/dados/).
- **Regra (mesma técnica):**  
  $`0.45 \times \mathrm{pop} + 0.25 \times \mathrm{cooc} + 0.30 \times \mathrm{demo}`$,  
  onde `demo` mistura preferências declaradas e popularidade do produto **na faixa
  etária** do cliente.
- **Subir:** `cd variante-demografica && just treino && just serve` (porta **3001**).
- **Container:** nessa pasta, `just imagem` · `just serve-container` (host **3001**).
- **Doc:** [`variante-demografica/README.md`](variante-demografica/README.md).

### Variante clustering — cesta e grupo de atributos na mesma lista

Este pacote monta a faixa de sugestões **intercalando** dois fios. No treino, cada
produto vira um vetor (técnica, região, pedidos) e o linkage *ward* corta o
catálogo em grupos; o dendrograma fica em
[`variante-clustering/material/dendrograma.png`](variante-clustering/material/dendrograma.png).
Na inferência, ranks ímpares puxam a fila da **cesta** (co-ocorrência com a
página); ranks pares puxam o **cluster** (mesmo grupo, ordenado por popularidade).
Se a fila da vez esvaziar, a outra completa a vaga e o `reason` registra a fonte
que de fato entrou (`cesta` ou `cluster`).

- **Exemplo completo:** `produto_na_pagina=p07`, `limite=4` →  
  `cesta`, `cluster`, `cesta`, `cluster` (`intercalacao_completa: true`).
- **Subir:** `cd variante-clustering && just treino && just serve` (porta **3002**).
- **Container:** nessa pasta, `just imagem` · `just serve-container` (host **3002**).
- **Doc:** [`variante-clustering/README.md`](variante-clustering/README.md).

### Entradas e saídas esperadas

Contrato comum: `POST /recomendar` com `Content-Type: application/json`. Porta e
artefato mudam por pasta (tabela acima).

#### Entradas (`POST /recomendar`)

| Campo | Baseline `:3000` | Demográfica `:3001` | Clustering `:3002` |
| --- | --- | --- | --- |
| `produto_na_pagina` | obrigatório (string) | obrigatório | obrigatório |
| `limite` | opcional (padrão `4`) | opcional (padrão `4`) | opcional (padrão `4`) |
| `excluir` | opcional (lista de ids) | opcional | opcional |
| `cliente_id` | — | opcional (string, ex. `"u01"`) | — |

#### Saídas (sucesso)

Campos presentes no JSON de resposta. “comum” = os três pacotes; o restante é
específico da pasta.

| Campo | Baseline | Demográfica | Clustering |
| --- | --- | --- | --- |
| `items[]` | comum | comum | comum |
| `items[].product_id`, `nome`, `tecnica`, `regiao`, `rank` | comum | comum | comum |
| `items[].score` | `0,7×pop+0,3×cooc` ou `0,5×pop` no complemento | mistura com `demo` quando há cliente | `cooc` se `reason=cesta`; `pop` se `reason=cluster` |
| `items[].reason` | `mesma_tecnica` · `complemento_popularidade` | `mesma_tecnica` / `mesma_tecnica_demo` · `complemento_popularidade` / `complemento_demo` | `cesta` · `cluster` |
| `items[].afinidade_demo` | — | sim (`0…1`) | — |
| `items[].cluster_id`, `items[].cooc`, `items[].pop` | — | — | sim |
| `strategy` | comum | comum | comum |
| `modelo` | tag `recomendador:…` | tag `recomendador-demo:…` | tag `recomendador-cluster:…` |
| `produto_na_pagina` (eco) | id, nome, técnica, região | igual | igual **+** `cluster_id` |
| `complemento_usado` | bool | bool | — |
| `pesos` | — | `{pop, cooc, demo}` | — |
| `cliente_id` / `cliente` | — | eco; `cliente` só se o id existir | — |
| `intercalacao_completa` | — | — | bool |
| `n_clusters` | — | — | int (ex. `4`) |

#### Saídas de erro

| Situação | Baseline | Demográfica | Clustering |
| --- | --- | --- | --- |
| Produto inexistente | `erro: produto_inexistente`, `items: []` | igual | igual |
| Cliente inexistente | — | `erro: cliente_inexistente`, `items: []` | — |

### Como escolher

| Pergunta | Pasta |
| --- | --- |
| “Só produto da página, regra auditável” | raiz |
| “E se soubermos quem é o cliente?” | `variante-demografica/` |
| “E se agruparmos por atributos e misturarmos com a cesta?” | `variante-clustering/` |

Nenhuma variante é aprendizado de máquina supervisionado ainda — ver
[Do Data Science à Machine Learning](#ds-para-ml-microsoft-learn). Para **predição
de demanda** (outro problema: prever `pedidos`, não montar top‑k), use o
repositório irmão
[`predicao-demanda-bentoml`](https://github.com/lgallindo/predicao-demanda-bentoml).

