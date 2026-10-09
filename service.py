"""Serve recomendações: mesma técnica + popularidade, com complemento por pedidos.

Além do endpoint original (`recomendar`), expõe 3 endpoints MOCKADOS
baseados no Documento de Requisitos (sem lógica real, retorno fixo):

  - POST /v1/recommendations/home     (RF01, RF05, RF10, RF12)
  - POST /v1/recommendations/seller   (RF08)
  - POST /v1/events                   (RF04, RF11)
"""

from __future__ import annotations

import pickle
from datetime import datetime, timezone
from pathlib import Path

import bentoml

modelo = bentoml.models.get("recomendador:latest")
ARTEFATO = "model.pkl"


@bentoml.service(resources={"cpu": "1"})
class Recomendador:

    def __init__(self) -> None:
        caminho = Path(modelo.path_of(ARTEFATO))
        self.artefato = pickle.loads(caminho.read_bytes())

    # ------------------------------------------------------------------
    # Endpoint original
    # ------------------------------------------------------------------
    @bentoml.api
    def recomendar(
        self,
        produto_na_pagina: str,
        limite: int = 4,
        excluir: list[str] | None = None,
    ) -> dict:
        """Devolve outros produtos a partir do produto que o cliente está vendo.

        Entrada:
          - produto_na_pagina: id do produto aberto na tela (ex.: \"p01\")
          - limite: quantos produtos sugerir (padrão 4)
          - excluir: ids que não devem voltar (já vistos / já comprados)
        """
        produtos = self.artefato["produtos"]
        pagina = produto_na_pagina
        if pagina not in produtos:
            return {
                "erro": "produto_inexistente",
                "produto_na_pagina": pagina,
                "items": [],
            }

        excluir_set = set(excluir or [])
        excluir_set.add(pagina)
        atual = produtos[pagina]
        tecnica = atual["tecnica"]
        pedidos_brutos = self.artefato["pedidos_brutos"]
        pop = self.artefato["pop"]
        cooc_pagina = self.artefato["cooc"].get(pagina, {})

        candidatos = [
            pid
            for pid, p in produtos.items()
            if p["tecnica"] == tecnica and pid not in excluir_set
        ]
        candidatos.sort(
            key=lambda pid: (
                0.7 * pop[pid] + 0.3 * cooc_pagina.get(pid, 0.0),
                pedidos_brutos[pid],
            ),
            reverse=True,
        )

        escolhidos: list[str] = candidatos[: max(limite, 0)]
        complemento_usado = False

        if len(escolhidos) < limite:
            complemento_usado = True
            resto = [
                pid
                for pid in sorted(produtos, key=lambda x: pedidos_brutos[x], reverse=True)
                if pid not in excluir_set and pid not in escolhidos
            ]
            escolhidos.extend(resto[: limite - len(escolhidos)])

        items = []
        for rank, pid in enumerate(escolhidos, start=1):
            p = produtos[pid]
            mesma_tec = p["tecnica"] == tecnica
            score = (
                (0.7 * pop[pid] + 0.3 * cooc_pagina.get(pid, 0.0))
                if mesma_tec
                else 0.5 * pop[pid]
            )
            items.append(
                {
                    "product_id": pid,
                    "nome": p["nome"],
                    "tecnica": p["tecnica"],
                    "regiao": p["regiao"],
                    "score": round(score, 4),
                    "reason": "mesma_tecnica" if mesma_tec else "complemento_popularidade",
                    "rank": rank,
                }
            )

        return {
            "items": items,
            "strategy": self.artefato["estrategia"],
            "complemento_usado": complemento_usado,
            "produto_na_pagina": {
                "product_id": pagina,
                "nome": atual["nome"],
                "tecnica": tecnica,
                "regiao": atual["regiao"],
            },
            "modelo": str(modelo.tag),
        }

    # ------------------------------------------------------------------
    # 1) Recomendações personalizadas para a home (MOCK)
    # ------------------------------------------------------------------
    @bentoml.api(route="/v1/recommendations/home")
    def recomendar_home(
        self,
        user_id: str | None = None,
        session_id: str | None = None,
        limit: int = 12,
        filters: dict | None = None,
        context: dict | None = None,
    ) -> dict:
        """Vitrine da home. `user_id` nulo = visitante (fallback por popularidade).

        Entrada:
          - user_id: id do usuário autenticado (ou None para visitante)
          - session_id: id da sessão de navegação
          - limit: quantidade de itens
          - filters: {"categoria": [...], "estado_origem": [...], "tecnica": ...}
          - context: {"device": "mobile"}
        """
        return {
            "strategy": "hybrid",
            "fallback_used": user_id is None,
            "items": [
                {
                    "product_id": "p_1042",
                    "artisan_id": "a_207",
                    "score": 0.91,
                    "reason": {
                        "code": "BOUGHT_SIMILAR_CATEGORY",
                        "text": "Porque você comprou peças de cerâmica",
                    },
                },
                {
                    "product_id": "p_0877",
                    "artisan_id": "a_113",
                    "score": 0.87,
                    "reason": {
                        "code": "FOLLOWED_ARTISAN",
                        "text": "Porque você segue este artesão",
                    },
                },
                {
                    "product_id": "p_2210",
                    "artisan_id": "a_309",
                    "score": 0.79,
                    "reason": {
                        "code": "TRENDING",
                        "text": "Em alta na plataforma",
                    },
                },
            ],
            "model_version": "mock-0.0.1",
            "latency_ms": 12,
        }

    # ------------------------------------------------------------------
    # 2) Insights para o artesão (MOCK) - RF08
    # ------------------------------------------------------------------
    @staticmethod
    def _ler_vendas_artesao(artisan_id: str) -> list[dict] | None:
        """MOCK de leitura no banco de dados.

        Em produção seria algo como:
            SELECT p.id, p.nome, p.preco, p.tags, p.visualizacoes,
                   COUNT(i.id) AS vendas
              FROM produtos p
         LEFT JOIN itens_pedido i ON i.produto_id = p.id
             WHERE p.artesao_id = :artisan_id
          GROUP BY p.id;

        Retorna None se o artesão não existir.
        """
        banco_fake = {
            "a_207": [
                {"product_id": "p_1042", "nome": "Vaso de barro esmaltado", "preco": 89.90,
                 "tags": ["ceramica", "decoracao-rustica", "vaso"], "visualizacoes": 1500, "vendas": 42},
                {"product_id": "p_0877", "nome": "Jogo de xícaras artesanais", "preco": 129.00,
                 "tags": ["ceramica", "presente-artesanal", "cozinha"], "visualizacoes": 2300, "vendas": 9},
                {"product_id": "p_2210", "nome": "Prato decorativo pintado a mão", "preco": 64.50,
                 "tags": ["ceramica", "decoracao-rustica", "parede"], "visualizacoes": 800, "vendas": 31},
                {"product_id": "p_3301", "nome": "Porta-temperos de barro", "preco": 39.90,
                 "tags": ["cozinha", "presente-artesanal"], "visualizacoes": 600, "vendas": 18},
            ],
        }
        return banco_fake.get(artisan_id)

    @staticmethod
    def _rodar_modelo_tags(vendas: list[dict]) -> list[dict]:
        """MOCK de execução de um modelo que estima quais tags têm mais sucesso.

        Aqui só agregamos taxa de conversão por tag e inventamos uma
        tendência de buscas; em produção seria a inferência de um modelo
        treinado com dados de todo o marketplace.
        """
        agregado: dict[str, dict] = {}
        for v in vendas:
            for tag in v["tags"]:
                a = agregado.setdefault(tag, {"vendas": 0, "views": 0})
                a["vendas"] += v["vendas"]
                a["views"] += v["visualizacoes"]

        resultado = []
        for tag, a in agregado.items():
            conversao = a["vendas"] / a["views"] if a["views"] else 0.0
            resultado.append(
                {
                    "tag": tag,
                    "taxa_conversao": round(conversao, 4),
                    "score_sucesso": round(min(1.0, conversao * 10), 2),  # fake
                    "buscas_7d_marketplace": 500 + 137 * len(tag),         # fake
                }
            )
        resultado.sort(key=lambda t: t["score_sucesso"], reverse=True)
        return resultado

    @bentoml.api(route="/v1/recommendations/seller")
    def recomendar_artesao(
        self,
        artisan_id: str,
        product_id: str | None = None,
        limit: int = 5,
    ) -> dict:
        """Insights para o Painel do Vendedor: preço, tags e potencial de conversão.

        Entrada:
          - artisan_id: id do artesão (obrigatório; usado para ler suas vendas no BD)
          - product_id: se informado, foca o preço sugerido nesse produto
          - limit: máximo de tags / produtos retornados
        """
        vendas = self._ler_vendas_artesao(artisan_id)  # mock: leitura no BD
        if vendas is None:
            return {"erro": "artesao_inexistente", "artisan_id": artisan_id}

        tags_modelo = self._rodar_modelo_tags(vendas)  # mock: modelo de tags

        total_vendas = sum(v["vendas"] for v in vendas)
        total_views = sum(v["visualizacoes"] for v in vendas)
        conversao_media = total_vendas / total_views if total_views else 0.0

        alvo = next((v for v in vendas if v["product_id"] == product_id), vendas[0])

        # produtos com muita visualização e conversão abaixo da média do artesão
        potencial = [
            {
                "product_id": v["product_id"],
                "nome": v["nome"],
                "conversao": round(v["vendas"] / v["visualizacoes"], 4),
                "motivo": "Muitas visualizações e poucas compras: revise fotos, descrição ou preço",
            }
            for v in vendas
            if v["visualizacoes"] and v["vendas"] / v["visualizacoes"] < conversao_media
        ]

        return {
            "artisan_id": artisan_id,
            "resumo_vendas": {
                "produtos": len(vendas),
                "total_vendas": total_vendas,
                "conversao_media": round(conversao_media, 4),
            },
            "preco_sugerido": {
                "product_id": alvo["product_id"],
                "preco_atual": alvo["preco"],
                "faixa_sugerida": {
                    "min": round(alvo["preco"] * 1.05, 2),
                    "max": round(alvo["preco"] * 1.25, 2),
                },
                "motivo": "Peças similares no marketplace vendem em média 18% acima",
            },
            "tags_com_mais_sucesso": tags_modelo[: max(limit, 0)],
            "produtos_potencial_conversao": potencial[: max(limit, 0)],
            "model_version": "mock-tags-0.0.1",
        }

    # ------------------------------------------------------------------
    # 3) Registro de eventos e feedback (MOCK)
    # ------------------------------------------------------------------
    @bentoml.api(route="/v1/events")
    def registrar_evento(
        self,
        user_id: str | None = None,
        session_id: str | None = None,
        event_type: str = "view",
        product_id: str | None = None,
        artisan_id: str | None = None,
        source: str | None = None,
        dwell_time_ms: int | None = None,
        timestamp: str | None = None,
    ) -> dict:
        """Registra evento de interação ou feedback sobre uma recomendação.

        event_type: view | click | search | add_to_cart | favorite |
                    purchase | rating | not_interested | hide_artisan
        """
        return {
            "status": "accepted",
            "event_id": "evt_99812",
            "received_at": datetime.now(timezone.utc).isoformat(),
        }
