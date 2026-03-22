"""
avalia+ — MVP Streamlit
Sistema de avaliação de comércios do Centro de Aracaju, SE
"""

import asyncio
import random
import string
import os
from datetime import datetime, timedelta

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from data import (
    COMERCIOS, AVALIACOES, CUPONS_EXEMPLO,
    INSIGHTS, PERFIS_CLIENTES, CATEGORIAS, USUARIO_ATUAL,
)

# ── CONFIG ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="avalia+",
    page_icon="⭐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── ESTILOS ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0f0f0f;
    border-right: 1px solid #1e1e1e;
}
[data-testid="stSidebar"] * { color: #c8c5c0 !important; }

/* Cards */
.comercio-card {
    background: #141414;
    border: 1px solid #1e1e1e;
    border-radius: 14px;
    padding: 18px;
    margin-bottom: 14px;
    transition: border-color .2s;
    cursor: pointer;
}
.comercio-card:hover { border-color: rgba(255,77,28,0.3); }

.card-title {
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 17px;
    color: #f0ede8;
    margin-bottom: 2px;
}
.card-meta { color: #888580; font-size: 13px; margin-bottom: 8px; }
.card-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 10px; }

/* Badges */
.badge-premium {
    background: rgba(197,168,75,0.12);
    border: 1px solid rgba(197,168,75,0.3);
    color: #F5D67A;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 10px;
    border-radius: 100px;
}
.badge-cat {
    background: rgba(255,77,28,0.08);
    border: 1px solid rgba(255,77,28,0.2);
    color: #FF6B40;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 10px;
    border-radius: 100px;
}
.badge-free {
    background: rgba(136,133,128,0.1);
    color: #888580;
    font-size: 11px;
    padding: 2px 10px;
    border-radius: 100px;
    border: 1px solid #2a2a2a;
}

/* Nota */
.nota-big {
    font-family: 'Syne', sans-serif;
    font-size: 48px;
    font-weight: 800;
    color: #F5A623;
    line-height: 1;
}
.stars { color: #F5A623; font-size: 18px; letter-spacing: 2px; }

/* Insight cards */
.insight-alerta    { background: rgba(244,67,54,0.05);  border-left: 3px solid #f44336; padding: 12px 16px; border-radius: 8px; margin-bottom: 10px; }
.insight-elogio    { background: rgba(76,175,80,0.05);  border-left: 3px solid #4CAF50; padding: 12px 16px; border-radius: 8px; margin-bottom: 10px; }
.insight-recomend  { background: rgba(255,77,28,0.05);  border-left: 3px solid #FF4D1C; padding: 12px 16px; border-radius: 8px; margin-bottom: 10px; }

/* Cupom */
.cupom-box {
    background: rgba(255,77,28,0.05);
    border: 1px dashed rgba(255,77,28,0.4);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    margin: 16px 0;
}
.cupom-code {
    font-family: monospace;
    font-size: 26px;
    font-weight: 700;
    color: #FF4D1C;
    letter-spacing: 4px;
}

/* Review card */
.review-card {
    background: #141414;
    border: 1px solid #1e1e1e;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 10px;
}
.review-header { display: flex; justify-content: space-between; margin-bottom: 6px; }
.reviewer { font-weight: 500; font-size: 14px; }
.review-date { color: #888580; font-size: 12px; }
.review-text { color: #c8c5c0; font-size: 14px; line-height: 1.6; }

/* Hero */
.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: 38px;
    font-weight: 800;
    letter-spacing: -1px;
    line-height: 1.1;
    color: #f0ede8;
}
.hero-title span { color: #FF4D1C; }
.hero-sub { color: #888580; font-size: 16px; line-height: 1.7; margin-top: 8px; }

/* KPI */
.kpi-box {
    background: #141414;
    border: 1px solid #1e1e1e;
    border-radius: 12px;
    padding: 18px 20px;
    text-align: center;
}
.kpi-val {
    font-family: 'Syne', sans-serif;
    font-size: 32px;
    font-weight: 800;
    color: #f0ede8;
    line-height: 1;
}
.kpi-label { color: #888580; font-size: 12px; text-transform: uppercase; letter-spacing: .5px; margin-top: 4px; }
.kpi-change { font-size: 12px; color: #4CAF50; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)


# ── HELPERS ───────────────────────────────────────────────────────────────────
def estrelas(nota: float) -> str:
    cheia = int(round(nota))
    return "★" * cheia + "☆" * (5 - cheia)


def gerar_cupom() -> str:
    letras = "".join(random.choices(string.ascii_uppercase, k=3))
    nums = "".join(random.choices(string.digits, k=4))
    return f"ACJ-{letras}{nums}"


def run_async(coro):
    """Executa coroutine async de forma segura no Streamlit."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        return loop.run_until_complete(coro)
    except Exception:
        return asyncio.run(coro)


def ia_disponivel() -> bool:
    return bool(os.getenv("GEMINI_API_KEY", ""))


# ── SESSION STATE ─────────────────────────────────────────────────────────────
if "pagina" not in st.session_state:
    st.session_state.pagina = "marketplace"
if "comercio_selecionado" not in st.session_state:
    st.session_state.comercio_selecionado = None
if "cupons_usuario" not in st.session_state:
    st.session_state.cupons_usuario = list(CUPONS_EXEMPLO)
if "avaliacoes_feitas" not in st.session_state:
    st.session_state.avaliacoes_feitas = {}    # {comercio_id: avaliacao_dict}
if "ultimo_resultado_ia" not in st.session_state:
    st.session_state.ultimo_resultado_ia = None


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⭐ avalia+")
    st.markdown("<small style='color:#555'>Centro de Aracaju, SE</small>", unsafe_allow_html=True)
    st.divider()

    paginas = {
        "🏪 Marketplace":       "marketplace",
        "⭐ Meus cupons":        "cupons",
        "📊 Painel comerciante": "painel",
    }
    for label, key in paginas.items():
        if st.button(label, use_container_width=True,
                     type="primary" if st.session_state.pagina == key else "secondary"):
            st.session_state.pagina = key
            st.session_state.comercio_selecionado = None
            st.rerun()

    st.divider()
    # Status da IA
    if ia_disponivel():
        st.success("🤖 Gemini conectado")
    else:
        st.warning("⚠️ IA não configurada")
        with st.expander("Como configurar"):
            st.code("GEMINI_API_KEY=sua-chave", language="bash")
            st.caption("Crie um arquivo `.env` na raiz do projeto com sua chave da Google AI Studio.")

    st.divider()
    st.caption(f"👤 {USUARIO_ATUAL['nome']}")
    st.caption("🎟️ " + str(len([c for c in st.session_state.cupons_usuario if c["valido"]])) + " cupons ativos")


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: DETALHE DO COMÉRCIO
# ══════════════════════════════════════════════════════════════════════════════
def pagina_comercio(c: dict):
    if st.button("← Voltar ao marketplace"):
        st.session_state.comercio_selecionado = None
        st.session_state.pagina = "marketplace"
        st.rerun()

    # Header
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown(f"## {c['emoji']} {c['nome']}")
        plano_badge = "✦ Premium" if c["plano"] == "premium" else "Freemium"
        st.markdown(
            f"<span class='badge-cat'>{c['categoria']}</span> &nbsp;"
            f"<span class='badge-{'premium' if c['plano']=='premium' else 'free'}'>{plano_badge}</span>",
            unsafe_allow_html=True,
        )
        st.caption(f"📍 {c['endereco']}  ·  🕐 {c['horario']}")
        st.write(c["descricao"])
    with col_h2:
        st.markdown(f"<div class='nota-big'>{c['nota_media']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='stars'>{estrelas(c['nota_media'])}</div>", unsafe_allow_html=True)
        st.caption(f"{c['total_avaliacoes']} avaliações")

    # Tags
    st.markdown(" ".join(f"`{t}`" for t in c["tags"]))
    st.divider()

    # Abas
    tab_av, tab_form, tab_sobre = st.tabs(["📝 Avaliações", "✍️ Avaliar & ganhar cupom", "ℹ️ Sobre"])

    # ── Aba: Avaliações ───────────────────────────────────────────
    with tab_av:
        avs = AVALIACOES.get(c["id"], [])

        # Distribuição de notas
        if avs:
            col_r1, col_r2 = st.columns([1, 2])
            with col_r1:
                st.markdown(f"<div class='nota-big'>{c['nota_media']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='stars'>{estrelas(c['nota_media'])}</div>", unsafe_allow_html=True)
                st.caption(f"{c['total_avaliacoes']} avaliações no total")
            with col_r2:
                dist = c.get("dist_notas", {5: 1, 4: 0, 3: 0, 2: 0, 1: 0})
                total_dist = sum(dist.values()) or 1
                for estrela in range(5, 0, -1):
                    pct = (dist.get(estrela, 0) / total_dist) * 100
                    col_e, col_b, col_n = st.columns([1, 6, 1])
                    col_e.caption(f"{estrela}★")
                    col_b.progress(int(pct))
                    col_n.caption(str(dist.get(estrela, 0)))

        st.divider()
        for av in avs:
            icone_sent = {"positivo": "🟢", "neutro": "🟡", "negativo": "🔴"}.get(av.get("sentimento", "neutro"), "⚪")
            st.markdown(f"""
<div class='review-card'>
  <div class='review-header'>
    <span class='reviewer'>{av['emoji']} {av['usuario']}</span>
    <span style='color:#F5A623'>{"★"*av['nota']}{"☆"*(5-av['nota'])}</span>
  </div>
  <div class='review-text'>{av['comentario']}</div>
  <div style='margin-top:8px;font-size:12px;color:#555'>{icone_sent} {av['data']}</div>
</div>""", unsafe_allow_html=True)

    # ── Aba: Avaliar ──────────────────────────────────────────────
    with tab_form:
        ja_avaliou = c["id"] in st.session_state.avaliacoes_feitas

        if ja_avaliou:
            av_feita = st.session_state.avaliacoes_feitas[c["id"]]
            st.success(f"✅ Você já avaliou este estabelecimento com **{av_feita['nota']} estrelas**.")
            cupom_av = av_feita.get("cupom")
            if cupom_av:
                st.markdown(f"""
<div class='cupom-box'>
  <div style='color:#888580;font-size:13px;margin-bottom:8px'>🎁 Seu cupom de desconto</div>
  <div class='cupom-code'>{cupom_av}</div>
  <div style='color:#888580;font-size:12px;margin-top:8px'>Válido por 30 dias neste estabelecimento</div>
</div>""", unsafe_allow_html=True)

            # Resultado da IA se disponível
            if st.session_state.ultimo_resultado_ia:
                res = st.session_state.ultimo_resultado_ia
                with st.expander("🤖 Análise da IA Gemini", expanded=True):
                    col_ia1, col_ia2 = st.columns(2)
                    with col_ia1:
                        sent_cor = {"positivo": "🟢", "neutro": "🟡", "negativo": "🔴"}.get(res.get("sentimento", "neutro"), "⚪")
                        st.metric("Sentimento", f"{sent_cor} {res.get('sentimento', '—').capitalize()}")
                    with col_ia2:
                        if res.get("topicos"):
                            topico_destaque = max(res["topicos"], key=res["topicos"].get)
                            st.metric("Tópico em destaque", f"📌 {topico_destaque.capitalize()}")
                    if res.get("recomendacoes_texto"):
                        st.info(f"💬 {res['recomendacoes_texto']}")
        else:
            st.markdown("### ✍️ Avalie este estabelecimento")
            st.caption("Sua avaliação gera automaticamente um cupom de desconto 🎉")

            nota = st.select_slider(
                "Sua nota",
                options=[1, 2, 3, 4, 5],
                value=5,
                format_func=lambda x: f"{'★'*x}{'☆'*(5-x)} ({x}/5)",
            )
            comentario = st.text_area(
                "Comentário",
                placeholder="Descreva sua experiência neste estabelecimento...",
                height=120,
            )

            if st.button("📤 Enviar avaliação e gerar cupom", type="primary", use_container_width=True):
                if len(comentario.strip()) < 10:
                    st.error("Por favor, escreva um comentário com pelo menos 10 caracteres.")
                else:
                    with st.spinner("Processando sua avaliação com IA Gemini..." if ia_disponivel() else "Processando avaliação..."):
                        codigo_cupom = gerar_cupom()

                        # Roda o grafo LangGraph
                        historico = AVALIACOES.get(c["id"], [])
                        try:
                            from agents import processar_avaliacao
                            resultado = run_async(processar_avaliacao(
                                nota=nota,
                                comentario=comentario,
                                categoria=c["categoria"],
                                comercio_nome=c["nome"],
                                historico_avaliacoes=historico,
                            ))
                            resultado["cupom"] = codigo_cupom
                        except Exception as e:
                            resultado = {
                                "sentimento": "neutro",
                                "topicos": {},
                                "insights": [],
                                "recomendacoes_texto": "Obrigado pela sua avaliação!",
                                "cupom": codigo_cupom,
                            }

                        # Salva avaliação
                        st.session_state.avaliacoes_feitas[c["id"]] = {
                            "nota": nota,
                            "comentario": comentario,
                            "cupom": codigo_cupom,
                            **resultado,
                        }

                        # Adiciona cupom ao histórico do usuário
                        desconto = 15 if c["plano"] == "premium" else 10
                        st.session_state.cupons_usuario.insert(0, {
                            "codigo": codigo_cupom,
                            "desconto_pct": desconto,
                            "comercio": c["nome"],
                            "valido": True,
                        })

                        st.session_state.ultimo_resultado_ia = resultado
                        st.rerun()

    # ── Aba: Sobre ────────────────────────────────────────────────
    with tab_sobre:
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.markdown("**📍 Endereço**")
            st.write(c["endereco"])
            st.markdown("**🕐 Horário de funcionamento**")
            st.write(c["horario"])
        with col_s2:
            st.markdown("**📋 Categoria**")
            st.write(c["categoria"])
            st.markdown("**🏅 Plano**")
            st.write("✦ Premium — Insights por IA inclusos" if c["plano"] == "premium" else "Freemium")


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: MARKETPLACE
# ══════════════════════════════════════════════════════════════════════════════
def pagina_marketplace():
    # Hero
    st.markdown("""
<div class='hero-title'>Descubra os melhores<br>comércios do <span>Centro de Aracaju</span></div>
<div class='hero-sub'>Avalie, ganhe descontos e ajude os comerciantes a melhorar. Todos os estabelecimentos ficam no Centro de Aracaju, SE.</div>
""", unsafe_allow_html=True)
    st.write("")

    # Estatísticas
    col1, col2, col3, col4 = st.columns(4)
    total_avs = sum(c["total_avaliacoes"] for c in COMERCIOS)
    premium = sum(1 for c in COMERCIOS if c["plano"] == "premium")
    col1.metric("🏪 Comércios", len(COMERCIOS))
    col2.metric("⭐ Avaliações", f"{total_avs:,}".replace(",", "."))
    col3.metric("✦ Premium", premium)
    col4.metric("🎟️ Cupons emitidos", len(st.session_state.cupons_usuario))
    st.divider()

    # Filtros
    col_f1, col_f2, col_f3 = st.columns([3, 2, 2])
    with col_f1:
        busca = st.text_input("🔍 Buscar estabelecimento", placeholder="Nome ou endereço...")
    with col_f2:
        cat_filtro = st.selectbox("Categoria", ["Todas"] + CATEGORIAS)
    with col_f3:
        ordem = st.selectbox("Ordenar por", ["Melhor avaliado", "Mais avaliado", "Nome A–Z"])

    plano_filtro = st.radio("Plano", ["Todos", "Premium", "Freemium"], horizontal=True)
    st.write("")

    # Filtra comércios
    lista = list(COMERCIOS)
    if busca:
        lista = [c for c in lista if busca.lower() in c["nome"].lower() or busca.lower() in c["endereco"].lower()]
    if cat_filtro != "Todas":
        lista = [c for c in lista if c["categoria"] == cat_filtro]
    if plano_filtro == "Premium":
        lista = [c for c in lista if c["plano"] == "premium"]
    elif plano_filtro == "Freemium":
        lista = [c for c in lista if c["plano"] == "freemium"]

    if ordem == "Melhor avaliado":
        lista.sort(key=lambda x: x["nota_media"], reverse=True)
    elif ordem == "Mais avaliado":
        lista.sort(key=lambda x: x["total_avaliacoes"], reverse=True)
    else:
        lista.sort(key=lambda x: x["nome"])

    if not lista:
        st.info("Nenhum comércio encontrado com os filtros aplicados.")
        return

    # Grid de cards
    cols_por_linha = 3
    for i in range(0, len(lista), cols_por_linha):
        cols = st.columns(cols_por_linha)
        for j, col in enumerate(cols):
            if i + j >= len(lista):
                break
            c = lista[i + j]
            with col:
                plano_html = (
                    "<span class='badge-premium'>✦ Premium</span>"
                    if c["plano"] == "premium"
                    else "<span class='badge-free'>Freemium</span>"
                )
                ja_avaliou = "✅ " if c["id"] in st.session_state.avaliacoes_feitas else ""
                st.markdown(f"""
<div class='comercio-card'>
  <div style='font-size:36px;margin-bottom:8px'>{c['emoji']}</div>
  <div class='card-title'>{ja_avaliou}{c['nome']}</div>
  <div class='card-meta'>{c['categoria']} · {c['bairro']}</div>
  <div class='card-meta' style='font-size:12px'>📍 {c['endereco'][:45]}...</div>
  <div class='card-footer'>
    <span style='color:#F5A623;font-size:15px'>★ {c['nota_media']}</span>
    <span style='color:#555;font-size:12px'>{c['total_avaliacoes']} avaliações</span>
  </div>
  <div style='margin-top:10px'>{plano_html} <span class='badge-cat'>{c['categoria']}</span></div>
</div>""", unsafe_allow_html=True)
                if st.button(f"Ver detalhes", key=f"btn_{c['id']}", use_container_width=True):
                    st.session_state.comercio_selecionado = c["id"]
                    st.session_state.pagina = "comercio"
                    st.session_state.ultimo_resultado_ia = None
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: MEUS CUPONS
# ══════════════════════════════════════════════════════════════════════════════
def pagina_cupons():
    st.markdown("## 🎟️ Meus cupons")
    st.caption("Cupons gerados pelas suas avaliações nos comércios do Centro de Aracaju.")
    st.divider()

    cupons = st.session_state.cupons_usuario
    ativos = [c for c in cupons if c["valido"]]
    usados = [c for c in cupons if not c["valido"]]

    col_a, col_u = st.columns(2)
    col_a.metric("✅ Cupons ativos", len(ativos))
    col_u.metric("🔒 Utilizados", len(usados))
    st.write("")

    if ativos:
        st.markdown("### ✅ Cupons ativos")
        for cup in ativos:
            with st.container():
                st.markdown(f"""
<div class='cupom-box'>
  <div style='color:#888580;font-size:13px'>{cup['comercio']}</div>
  <div class='cupom-code' style='margin:8px 0'>{cup['codigo']}</div>
  <div style='color:#4CAF50;font-size:14px;font-weight:600'>{cup['desconto_pct']}% de desconto</div>
</div>""", unsafe_allow_html=True)

    if usados:
        with st.expander(f"🔒 Cupons utilizados ({len(usados)})"):
            for cup in usados:
                st.markdown(f"""
<div style='background:#0f0f0f;border:1px solid #1e1e1e;border-radius:10px;padding:12px 16px;margin-bottom:8px;opacity:0.5'>
  <span style='font-family:monospace;font-size:18px;color:#555;letter-spacing:3px'>{cup['codigo']}</span>
  <span style='float:right;color:#555;font-size:13px'>{cup['comercio']} · {cup['desconto_pct']}%</span>
</div>""", unsafe_allow_html=True)

    if not cupons:
        st.info("Você ainda não tem cupons. Avalie um comércio para ganhar seu primeiro desconto!")
        if st.button("🏪 Ir ao marketplace", type="primary"):
            st.session_state.pagina = "marketplace"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: PAINEL DO COMERCIANTE
# ══════════════════════════════════════════════════════════════════════════════
def pagina_painel():
    st.markdown("## 📊 Painel do comerciante")
    st.caption("Insights e análises gerados por IA Gemini para estabelecimentos premium do Centro de Aracaju.")
    st.divider()

    # Seletor de comércio
    premiums = [c for c in COMERCIOS if c["plano"] == "premium"]
    nomes = [f"{c['emoji']} {c['nome']}" for c in premiums]
    idx = st.selectbox("Selecione o estabelecimento", range(len(nomes)), format_func=lambda i: nomes[i])
    comercio = premiums[idx]
    st.divider()

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown(f"<div class='kpi-box'><div class='kpi-val' style='color:#F5A623'>{comercio['nota_media']}</div><div class='kpi-label'>Nota média</div><div class='kpi-change'>↑ Top {idx+1} do Centro</div></div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='kpi-box'><div class='kpi-val'>{comercio['total_avaliacoes']}</div><div class='kpi-label'>Avaliações</div><div class='kpi-change'>↑ +23 esta semana</div></div>", unsafe_allow_html=True)
    cupons_count = len([c for c in st.session_state.cupons_usuario if c.get("comercio") == comercio["nome"]])
    col3.markdown(f"<div class='kpi-box'><div class='kpi-val'>{cupons_count + 87}</div><div class='kpi-label'>Cupons emitidos</div><div class='kpi-change'>↑ +18 esta semana</div></div>", unsafe_allow_html=True)
    col4.markdown(f"<div class='kpi-box'><div class='kpi-val'>72%</div><div class='kpi-label'>Taxa de retorno</div><div class='kpi-change'>↑ +4% vs mês ant.</div></div>", unsafe_allow_html=True)
    st.write("")

    # Gráfico de avaliações por dia
    col_g, col_p = st.columns([3, 2])
    with col_g:
        st.markdown("#### 📅 Avaliações — últimos 7 dias")
        dias_semana = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
        valores = [4, 7, 5, 9, 12, 18, 14]
        df_dias = pd.DataFrame({"Dia": dias_semana, "Avaliações": valores})
        cores = ["#FF4D1C" if d in ["Sáb", "Dom"] else "rgba(255,77,28,0.3)" for d in dias_semana]
        fig = go.Figure(go.Bar(
            x=df_dias["Dia"], y=df_dias["Avaliações"],
            marker_color=cores,
            text=df_dias["Avaliações"], textposition="outside",
        ))
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#888580",
            margin=dict(t=10, b=10, l=10, r=10),
            height=220,
            showlegend=False,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="#1e1e1e"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_p:
        st.markdown("#### 👥 Perfil dos clientes")
        perfis = PERFIS_CLIENTES.get(comercio["nome"], [("Foodies 🍽️", 40), ("Famílias 👨‍👩‍👧", 35), ("Executivos 👔", 25)])
        df_perfil = pd.DataFrame(perfis, columns=["Perfil", "Pct"])
        fig2 = go.Figure(go.Pie(
            labels=df_perfil["Perfil"],
            values=df_perfil["Pct"],
            hole=0.5,
            marker_colors=["#FF4D1C", "#F5A623", "#4CAF50", "#2196F3", "#9C27B0"],
        ))
        fig2.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#888580",
            margin=dict(t=10, b=10, l=10, r=10),
            height=220,
            showlegend=True,
            legend=dict(font=dict(size=11)),
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # Insights + Avaliações recentes
    col_i, col_r = st.columns([3, 2])

    with col_i:
        st.markdown("#### 🤖 Insights por IA Gemini")
        if not ia_disponivel():
            st.caption("⚠️ Configure `GEMINI_API_KEY` para insights gerados em tempo real.")

        insights = INSIGHTS.get(comercio["id"], [
            {"tipo": "recomendacao", "titulo": "Incentive avaliações dos clientes", "descricao": "Clientes que avaliam retornam 2× mais. Lembre seu time de pedir avaliações no fim do atendimento.", "prioridade": "media"},
        ])

        for ins in insights:
            icone = {"alerta": "⚠️", "elogio": "✅", "recomendacao": "💡"}.get(ins["tipo"], "📌")
            css_class = {"alerta": "insight-alerta", "elogio": "insight-elogio", "recomendacao": "insight-recomend"}.get(ins["tipo"], "insight-recomend")
            prior_cor = {"alta": "#f44336", "media": "#FF9800", "baixa": "#4CAF50"}.get(ins["prioridade"], "#888")
            st.markdown(f"""
<div class='{css_class}'>
  <div style='display:flex;justify-content:space-between;margin-bottom:4px'>
    <strong>{icone} {ins['titulo']}</strong>
    <span style='color:{prior_cor};font-size:11px;font-weight:600'>{ins['prioridade'].upper()}</span>
  </div>
  <div style='color:#c8c5c0;font-size:13px'>{ins['descricao']}</div>
</div>""", unsafe_allow_html=True)

        # Gerar insights com Gemini ao vivo
        if ia_disponivel():
            if st.button("🔄 Gerar novos insights com Gemini", use_container_width=True):
                with st.spinner("Gerando insights com Gemini..."):
                    historico = AVALIACOES.get(comercio["id"], [])
                    try:
                        from agents import processar_avaliacao
                        # Usa a última avaliação disponível como gatilho
                        if historico:
                            av = historico[0]
                            resultado = run_async(processar_avaliacao(
                                nota=av["nota"],
                                comentario=av["comentario"],
                                categoria=comercio["categoria"],
                                comercio_nome=comercio["nome"],
                                historico_avaliacoes=historico,
                            ))
                            if resultado.get("insights"):
                                INSIGHTS[comercio["id"]] = resultado["insights"]
                                st.success("Insights atualizados!")
                                st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao gerar insights: {e}")

    with col_r:
        st.markdown("#### ⭐ Últimas avaliações")
        avs = AVALIACOES.get(comercio["id"], [])
        if avs:
            for av in avs[:4]:
                sent_cor = {"positivo": "#4CAF50", "neutro": "#FF9800", "negativo": "#f44336"}.get(av.get("sentimento", "neutro"), "#888")
                st.markdown(f"""
<div class='review-card'>
  <div style='display:flex;justify-content:space-between;margin-bottom:4px'>
    <span style='font-size:13px;font-weight:500'>{av['emoji']} {av['usuario']}</span>
    <span style='color:#F5A623;font-size:13px'>{"★"*av['nota']}{"☆"*(5-av['nota'])}</span>
  </div>
  <div style='font-size:13px;color:#c8c5c0;line-height:1.5'>{av['comentario'][:120]}{"..." if len(av['comentario'])>120 else ""}</div>
  <div style='margin-top:6px;font-size:11px;color:{sent_cor}'>● {av.get("sentimento","neutro").capitalize()} · {av['data']}</div>
</div>""", unsafe_allow_html=True)
        else:
            st.info("Nenhuma avaliação ainda.")

    st.divider()

    # Distribuição de notas (gráfico de donut)
    st.markdown("#### 📊 Distribuição de notas")
    dist = comercio.get("dist_notas", {5: 60, 4: 25, 3: 10, 2: 3, 1: 2})
    df_dist = pd.DataFrame({
        "Nota": [f"{k} estrela{'s' if k>1 else ''}" for k in sorted(dist.keys(), reverse=True)],
        "Quantidade": [dist[k] for k in sorted(dist.keys(), reverse=True)],
    })
    fig3 = px.bar(
        df_dist, x="Quantidade", y="Nota", orientation="h",
        color="Quantidade",
        color_continuous_scale=["#2a1a00", "#FF4D1C"],
    )
    fig3.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#888580",
        margin=dict(t=10, b=10, l=10, r=10),
        height=180,
        showlegend=False,
        coloraxis_showscale=False,
        yaxis=dict(showgrid=False),
        xaxis=dict(showgrid=True, gridcolor="#1e1e1e"),
    )
    st.plotly_chart(fig3, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# ROTEADOR PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
pagina = st.session_state.pagina

if pagina == "comercio" and st.session_state.comercio_selecionado:
    comercio_obj = next((c for c in COMERCIOS if c["id"] == st.session_state.comercio_selecionado), None)
    if comercio_obj:
        pagina_comercio(comercio_obj)
    else:
        st.session_state.pagina = "marketplace"
        st.rerun()
elif pagina == "cupons":
    pagina_cupons()
elif pagina == "painel":
    pagina_painel()
else:
    pagina_marketplace()
