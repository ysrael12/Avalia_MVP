"""
avalia+ — Agentes LangGraph com suporte a Gemini
Fluxo: avaliação → análise → insights → recomendação
Fallback heurístico se a chave não estiver configurada.
"""

import os
import json
import re
import logging
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END, START

logger = logging.getLogger(__name__)


# ── LLM FACTORY ──────────────────────────────────────────────────────────────
def get_llm():
    """Retorna LLM Gemini se a chave existir, senão None."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return None
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=api_key,
            temperature=0.2,
            max_output_tokens=512,
        )
    except Exception as e:
        logger.warning(f"Não foi possível iniciar o LLM Gemini: {e}")
        return None


def _parse_json(text: str) -> dict:
    """Extrai JSON da resposta do LLM com segurança."""
    clean = re.sub(r"```json|```", "", text).strip()
    return json.loads(clean)


# ── ESTADO DO GRAFO ───────────────────────────────────────────────────────────
class AvaliacaoState(TypedDict):
    nota: int
    comentario: str
    categoria: str
    comercio_nome: str
    historico_avaliacoes: list[dict]   # avaliações recentes do comércio
    sentimento: str
    topicos: dict
    insights: list[dict]
    recomendacoes_texto: str
    erro: Optional[str]


# ── NÓ 1: ANALISAR AVALIAÇÃO ─────────────────────────────────────────────────
async def node_analisar(state: AvaliacaoState) -> dict:
    """Classifica sentimento e extrai tópicos da avaliação."""
    llm = get_llm()
    if llm is None:
        return _heuristica_analise(state)

    prompt = f"""Analise esta avaliação de um comércio e retorne APENAS um JSON:
{{
  "sentimento": "positivo" | "neutro" | "negativo",
  "topicos": {{
    "atendimento": <nota 1-5 ou null>,
    "produto": <nota 1-5 ou null>,
    "preco": <nota 1-5 ou null>,
    "ambiente": <nota 1-5 ou null>,
    "agilidade": <nota 1-5 ou null>
  }}
}}

Nota geral: {state['nota']}/5
Comentário: {state['comentario']}
Retorne APENAS o JSON."""

    try:
        from langchain_core.messages import HumanMessage
        resp = await llm.ainvoke([HumanMessage(content=prompt)])
        data = _parse_json(resp.content)
        return {
            "sentimento": data.get("sentimento", _nota_sentimento(state["nota"])),
            "topicos": {k: v for k, v in data.get("topicos", {}).items() if v is not None},
            "erro": None,
        }
    except Exception as e:
        logger.warning(f"Analisador falhou: {e}")
        return _heuristica_analise(state)


def _nota_sentimento(nota: int) -> str:
    if nota >= 4:
        return "positivo"
    if nota <= 2:
        return "negativo"
    return "neutro"


def _heuristica_analise(state: AvaliacaoState) -> dict:
    texto = state["comentario"].lower()
    sentimento = _nota_sentimento(state["nota"])
    for p in ["demor", "ruim", "péssim", "terrível", "mal"]:
        if p in texto:
            sentimento = "negativo"
            break
    topicos = {}
    mapa = {
        "atendimento": ["atendiment", "funcionári", "garçom", "vendedor"],
        "produto":     ["produt", "comida", "prato", "qualidade", "sabor", "açaí", "pizza", "café"],
        "preco":       ["preço", "caro", "barato", "valor"],
        "ambiente":    ["ambient", "lugar", "espaço", "limpeza"],
        "agilidade":   ["rápido", "demor", "espera", "fila"],
    }
    for topico, palavras in mapa.items():
        if any(p in texto for p in palavras):
            topicos[topico] = state["nota"]
    return {"sentimento": sentimento, "topicos": topicos, "erro": None}


# ── NÓ 2: GERAR INSIGHTS ─────────────────────────────────────────────────────
async def node_insights(state: AvaliacaoState) -> dict:
    """Gera 2-3 insights acionáveis para o comerciante baseado no histórico."""
    llm = get_llm()
    historico = state.get("historico_avaliacoes", [])

    if llm is None or not historico:
        return {"insights": _heuristica_insights(state, historico)}

    resumo = [
        {"nota": a["nota"], "comentario": a["comentario"][:200], "sentimento": a.get("sentimento", "")}
        for a in historico[-10:]
    ]

    prompt = f"""Você é um consultor de negócios para comércios de Aracaju, SE.
Analise as avaliações recentes do estabelecimento "{state['comercio_nome']}" ({state['categoria']}) e gere 2 a 3 insights acionáveis.

Retorne APENAS este JSON:
{{
  "insights": [
    {{
      "tipo": "alerta" | "elogio" | "recomendacao",
      "titulo": "título curto (máx 60 chars)",
      "descricao": "descrição prática em 1-2 frases (máx 200 chars)",
      "prioridade": "alta" | "media" | "baixa"
    }}
  ]
}}

Avaliações recentes:
{json.dumps(resumo, ensure_ascii=False)}

Retorne APENAS o JSON."""

    try:
        from langchain_core.messages import HumanMessage
        resp = await llm.ainvoke([HumanMessage(content=prompt)])
        data = _parse_json(resp.content)
        return {"insights": data.get("insights", [])}
    except Exception as e:
        logger.warning(f"Insights falhou: {e}")
        return {"insights": _heuristica_insights(state, historico)}


def _heuristica_insights(state: AvaliacaoState, historico: list) -> list:
    insights = []
    if not historico:
        return insights
    notas = [a["nota"] for a in historico]
    media = sum(notas) / len(notas)
    negativos = [a for a in historico if a.get("sentimento") == "negativo"]
    if negativos:
        insights.append({
            "tipo": "alerta",
            "titulo": f"{len(negativos)} avaliação(ões) negativa(s) recente(s)",
            "descricao": "Revise os comentários negativos e entre em contato com os clientes para entender os problemas.",
            "prioridade": "alta" if len(negativos) >= 3 else "media",
        })
    if media >= 4.5:
        insights.append({
            "tipo": "elogio",
            "titulo": "Nota excelente! Parabéns pela qualidade",
            "descricao": "Seus clientes estão muito satisfeitos. Compartilhe sua nota nas redes sociais para atrair mais clientes.",
            "prioridade": "baixa",
        })
    insights.append({
        "tipo": "recomendacao",
        "titulo": "Incentive mais avaliações",
        "descricao": "Clientes que recebem cupom de desconto tendem a voltar 2x mais. Continue incentivando avaliações.",
        "prioridade": "media",
    })
    return insights


# ── NÓ 3: GERAR RECOMENDAÇÃO TEXTUAL ─────────────────────────────────────────
async def node_recomendar(state: AvaliacaoState) -> dict:
    """Gera texto de recomendação personalizada para o usuário."""
    llm = get_llm()
    if llm is None:
        return {"recomendacoes_texto": "Continue explorando os comércios do Centro de Aracaju! Cada avaliação gera um cupom exclusivo para você."}

    prompt = f"""O usuário acabou de avaliar "{state['comercio_nome']}" com nota {state['nota']}/5 e disse:
"{state['comentario']}"

Com base nisso, sugira em 2 frases amigáveis o que o usuário pode explorar a seguir nos comércios do Centro de Aracaju.
Seja específico, caloroso e mencione o tipo de estabelecimento. Responda em português."""

    try:
        from langchain_core.messages import HumanMessage
        resp = await llm.ainvoke([HumanMessage(content=prompt)])
        return {"recomendacoes_texto": resp.content.strip()}
    except Exception as e:
        logger.warning(f"Recomendador falhou: {e}")
        return {"recomendacoes_texto": "Que tal explorar outros comércios do Centro de Aracaju? Cada avaliação garante um cupom exclusivo!"}


# ── CONSTRUÇÃO DO GRAFO ───────────────────────────────────────────────────────
def build_graph():
    builder = StateGraph(AvaliacaoState)
    builder.add_node("analisar",    node_analisar)
    builder.add_node("insights",    node_insights)
    builder.add_node("recomendar",  node_recomendar)
    builder.add_edge(START, "analisar")
    builder.add_edge("analisar", "insights")
    builder.add_edge("insights", "recomendar")
    builder.add_edge("recomendar", END)
    return builder.compile()


grafo = build_graph()


async def processar_avaliacao(
    nota: int,
    comentario: str,
    categoria: str,
    comercio_nome: str,
    historico_avaliacoes: list[dict],
) -> AvaliacaoState:
    state: AvaliacaoState = {
        "nota": nota,
        "comentario": comentario,
        "categoria": categoria,
        "comercio_nome": comercio_nome,
        "historico_avaliacoes": historico_avaliacoes,
        "sentimento": "neutro",
        "topicos": {},
        "insights": [],
        "recomendacoes_texto": "",
        "erro": None,
    }
    return await grafo.ainvoke(state)
