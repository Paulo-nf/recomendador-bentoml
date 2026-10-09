# Baseline de recomendação no BentoML
#
# Dois momentos (não misture):
#   1) treino  — offline: lê JSON, grava modelo no store
#   2) serve   — online: carrega o modelo, responde HTTP
#
# Empacote (opcional, só o pipeline online):
#   treino → build (Bento) → containerize (imagem OCI) → serve-container
#
# Imagem de aula (tag estável): recomendador:aula
# Pare qualquer `just serve` na :3000 antes de `just serve-container`.

# ---------------------------------------------------------------------------
# Offline — treino
# ---------------------------------------------------------------------------

treino:
    # Lê dados/catalogo.json → calcula pop/cooc → store `recomendador:…`
    uv run python treino.py

# ---------------------------------------------------------------------------
# Online — processo local (sem Docker)
# ---------------------------------------------------------------------------

serve:
    # Requer `just treino` ao menos uma vez. Deixe o terminal aberto.
    uv run bentoml serve service:Recomendador --reload

# ---------------------------------------------------------------------------
# Empacote — Bento → imagem OCI → container
# ---------------------------------------------------------------------------
# O que entra no pacote está em bentofile.yaml:
#   service + *.py + dados/*.json + dep bentoml + modelo recomendador:latest
# O treino NÃO roda dentro do container; só a inferência.

build:
    # Congela o serviço num Bento (ainda não é imagem Docker).
    # Pré-requisito: `just treino` (senão falta recomendador:latest).
    uv run bentoml build

containerize:
    # Transforma o Bento `Recomendador:latest` numa imagem OCI.
    # --image-tag fixa o nome para a aula (evita decorar o hash do Bento).
    uv run bentoml containerize Recomendador:latest --image-tag recomendador:aula

# Atalho didático: Bento + imagem de uma vez (mesmos passos, na ordem).
imagem: build containerize

serve-container:
    # Sobe a imagem. Mesma API que `just serve` (porta 3000).
    # Pré-requisito: `just imagem` (ou build + containerize).
    docker run --rm -p 3000:3000 recomendador:aula serve

listar-bentos:
    # O que o `bentoml build` gravou no store de Bentos
    uv run bentoml list

listar-imagens:
    # A imagem que o `containerize` deixou no Docker local
    docker images recomendador

# ---------------------------------------------------------------------------
# Exemplos HTTP (serve local OU serve-container na :3000)
# ---------------------------------------------------------------------------

curl-exemplo:
    # Cliente abriu o jarro de barro (p01)
    curl -sS -X POST http://127.0.0.1:3000/recomendar \
      -H 'Content-Type: application/json' \
      -d '{"produto_na_pagina":"p01","limite":4,"excluir":[]}' | python3 -m json.tool

curl-complemento:
    # Poucos da mesma técnica → completa com os mais pedidos
    curl -sS -X POST http://127.0.0.1:3000/recomendar \
      -H 'Content-Type: application/json' \
      -d '{"produto_na_pagina":"p12","limite":4,"excluir":["p10","p11"]}' | python3 -m json.tool

curl-inexistente:
    curl -sS -X POST http://127.0.0.1:3000/recomendar \
      -H 'Content-Type: application/json' \
      -d '{"produto_na_pagina":"nao-existe","limite":4}' | python3 -m json.tool

# ---------------------------------------------------------------------------
# Material de aula
# ---------------------------------------------------------------------------

slides:
    uv run python scripts/gerar_slides.py

# ---------------------------------------------------------------------------
# Fork da equipe 2
# ---------------------------------------------------------------------------

testes:
    uv run pytest test_service.py -v
