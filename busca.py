"""
busca.py - Página de busca, listagem e detalhes
"""

import streamlit as st
import pandas as pd
from database import buscar_imoveis, listar_valores_unicos, buscar_por_id, contar_registros, LABELS, eh_cessao
from utils import fmt_moeda, fmt_area, fmt_numero, badge_ocupacao

POR_PAGINA = 50


# ── Filtros sidebar ───────────────────────────────────────────────────────────
def render_filtros():
    st.sidebar.markdown("## 🔍 Filtros")

    filtros = {}

    estados = ["Todos"] + listar_valores_unicos("estado")
    filtros["estado"] = st.sidebar.selectbox("🗺️ Estado", estados, key="f_estado")

    try:
        if filtros["estado"] != "Todos":
            municipios = ["Todos"] + listar_valores_unicos("municipio", estado=filtros["estado"])
        else:
            municipios = ["Todos"] + listar_valores_unicos("municipio")
    except Exception:
        municipios = ["Todos"]
    filtros["municipio"] = st.sidebar.selectbox("🏙️ Município", municipios, key="f_municipio")

    props = ["Todos"] + listar_valores_unicos("propriedade")
    filtros["propriedade"] = st.sidebar.selectbox("🏢 Propriedade", props, key="f_prop")

    st.sidebar.markdown("---")
    filtros["so_cessao"]   = st.sidebar.checkbox("🔄 Somente Cessão de Uso", key="f_cessao")
    filtros["so_rip_util"] = st.sidebar.checkbox("📋 Somente com RIP Utilização", key="f_riputil")

    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Limpar Filtros", use_container_width=True):
        for k in list(st.session_state.keys()):
            if k.startswith("f_") or k in ("busca_global", "pagina_atual", "ultima_busca"):
                del st.session_state[k]
        st.rerun()

    return filtros


# ── Página principal ──────────────────────────────────────────────────────────
def render_pagina_busca():
    st.title("🏛️ Base de Imóveis Públicos")

    if contar_registros() == 0:
        st.warning("⚠️ Banco vazio. Acesse **Importar Planilha** para começar.")
        return

    busca = st.text_input(
        "🔎 Busca Global",
        placeholder="RIP, município, endereço, processo, cessão, posto de saúde...",
        key="busca_global"
    )

    filtros = render_filtros()

    # reseta paginação quando busca muda
    if "pagina_atual" not in st.session_state:
        st.session_state.pagina_atual = 0
    chave = str(busca) + str(filtros)
    if st.session_state.get("ultima_busca") != chave:
        st.session_state.pagina_atual = 0
        st.session_state.ultima_busca = chave

    offset = st.session_state.pagina_atual * POR_PAGINA
    df, total = buscar_imoveis(filtros=filtros, busca_global=busca, limit=POR_PAGINA, offset=offset)

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Resultados", fmt_numero(total))
    c2.metric("Total no Banco", fmt_numero(contar_registros()))
    vt = pd.to_numeric(df["valor_total"], errors="coerce").sum() if (not df.empty and "valor_total" in df.columns) else 0
    c3.metric("Valor Total (página)", fmt_moeda(vt))
    cessoes = int(df["ocupacao"].apply(eh_cessao).sum()) if (not df.empty and "ocupacao" in df.columns) else 0
    c4.metric("🔄 Cessões (página)", cessoes)

    st.markdown("---")

    if df.empty:
        st.info("Nenhum resultado encontrado.")
        return

    # ── Tabela com TODOS os campos relevantes ─────────────────────────────────
    st.markdown(f"### Resultados — página {st.session_state.pagina_atual + 1}")

    # Prepara colunas para exibição — só inclui colunas que existem no df
    colunas_desejadas = [
        "id", "rip", "rip_utilizacao",
        "municipio", "estado",
        "endereco",
        "propriedade",
        "ocupacao",
        "valor_total",
        "area_terreno", "area_construida",
        "obs1", "processo", "obs5"
    ]
    colunas_presentes = [c for c in colunas_desejadas if c in df.columns]
    df_show = df[colunas_presentes].copy()

    df_show["valor_total"] = df_show["valor_total"].apply(fmt_moeda)

    # Destaca cessão na coluna ocupação
    def fmt_ocup(v):
        if not v or str(v).strip() in ("", "None", "nan"):
            return "—"
        return str(v)

    df_show["ocupacao"] = df_show["ocupacao"].apply(fmt_ocup)
    df_show["area_terreno"]   = df_show["area_terreno"].apply(fmt_area)
    df_show["area_construida"] = df_show["area_construida"].apply(fmt_area)

    # Preenche nulos de texto
    for col in ["rip_utilizacao", "propriedade", "obs1", "processo", "obs5"]:
        df_show[col] = df_show[col].fillna("—").replace("", "—")

    df_show.columns = [
        "ID", "RIP", "RIP Utilização",
        "Município", "UF",
        "Endereço",
        "Propriedade",
        "Ocupação / Destinação",
        "Valor Total",
        "Área Terreno", "Área Construída",
        "OBS1 (Registro)", "Processo", "OBS5 (Escritura)"
    ]

    st.dataframe(df_show, use_container_width=True, hide_index=True, height=430)

    # Seleção para detalhes
    st.markdown("#### 🔎 Ver ficha completa de um imóvel")
    col_a, col_b = st.columns([3, 1])
    with col_a:
        id_sel = st.selectbox(
            "Selecione pelo ID",
            df["id"].tolist(),
            format_func=lambda x: (
                f"ID {x} — RIP {df[df['id']==x]['rip'].values[0]}  |  "
                f"{df[df['id']==x]['municipio'].values[0]} / {df[df['id']==x]['estado'].values[0]}"
            ),
            key="sel_id"
        )
    with col_b:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📄 Ver Ficha", type="primary", use_container_width=True):
            st.session_state.imovel_id = id_sel
            st.session_state.pagina_menu = "Detalhes do Imóvel"
            st.rerun()

    # Paginação
    st.markdown("---")
    total_pag = max(1, -(-total // POR_PAGINA))
    pa, pb, pc = st.columns([1, 2, 1])
    with pa:
        if st.button("◀ Anterior", disabled=st.session_state.pagina_atual == 0):
            st.session_state.pagina_atual -= 1; st.rerun()
    with pb:
        st.markdown(
            f"<div style='text-align:center;padding-top:8px;'>"
            f"Página <b>{st.session_state.pagina_atual+1}</b> de <b>{total_pag}</b></div>",
            unsafe_allow_html=True
        )
    with pc:
        if st.button("Próximo ▶", disabled=st.session_state.pagina_atual >= total_pag - 1):
            st.session_state.pagina_atual += 1; st.rerun()


# ── Ficha do imóvel ───────────────────────────────────────────────────────────
def render_detalhe_imovel(imovel_id=None):
    imovel_id = imovel_id or st.session_state.get("imovel_id")

    if not imovel_id:
        st.info("Nenhum imóvel selecionado.")
        return

    if st.button("← Voltar para lista"):
        st.session_state.pagina_menu = "Base de Imóveis"
        st.rerun()

    d = buscar_por_id(imovel_id)
    if not d:
        st.error("Imóvel não encontrado."); return

    # Cabeçalho
    situacao = badge_ocupacao(d.get("ocupacao"))
    cessao = eh_cessao(d.get("ocupacao"))

    st.markdown(f"## 🏛️ Ficha do Imóvel")

    # Banner de cessão
    if cessao:
        st.info(
            f"🔄 **Este imóvel está em CESSÃO DE USO**\n\n"
            f"**Cessionário / Uso:** {d.get('ocupacao') or '—'}\n\n"
            f"**OBS1 (Registro/Título):** {d.get('obs1') or '—'}\n\n"
            f"**Processo:** {d.get('processo') or '—'}"
        )

    st.markdown("---")

    # Bloco 1 — Identificação
    st.markdown("### 📋 Identificação")
    col1, col2, col3 = st.columns(3)
    col1.markdown(f"**RIP**\n\n`{d.get('rip') or '—'}`")
    col2.markdown(f"**RIP Utilização**\n\n`{d.get('rip_utilizacao') or '—'}`")
    col3.markdown(f"**Nº SUEST**\n\n{d.get('n_suest') or '—'}")

    st.markdown("---")

    # Bloco 2 — Localização
    st.markdown("### 📍 Localização")
    col1, col2, col3 = st.columns(3)
    col1.markdown(f"**Estado**\n\n{d.get('estado') or '—'}")
    col2.markdown(f"**Município**\n\n{d.get('municipio') or '—'}")
    col3.markdown(f"**Cód. Município**\n\n{d.get('cod_municipio') or '—'}")
    st.markdown(f"**Endereço**\n\n{d.get('endereco') or '—'}")

    st.markdown("---")

    # Bloco 3 — Situação e Uso
    st.markdown("### 🔑 Situação / Destinação / Ocupação")
    st.markdown(
        f"<div style='background:#f0f4ff;border-left:4px solid #3498db;"
        f"padding:14px;border-radius:6px;white-space:pre-wrap;'>"
        f"{d.get('ocupacao') or '—'}</div>",
        unsafe_allow_html=True
    )

    st.markdown("---")

    # Bloco 4 — Áreas e Valores
    st.markdown("### 📐 Áreas e Valores")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Área Terreno",    fmt_area(d.get("area_terreno")))
    col2.metric("Área Construída", fmt_area(d.get("area_construida")))
    col3.metric("Valor Terreno",   fmt_moeda(d.get("valor_terreno")))
    col4.metric("Valor Benfeitoria", fmt_moeda(d.get("valor_benfeitoria")))
    col5.metric("Valor Total",     fmt_moeda(d.get("valor_total")))

    st.markdown("---")

    # Bloco 5 — Propriedade
    st.markdown("### 🏢 Propriedade")
    st.markdown(
        f"<div style='background:#f9f9f9;border-left:4px solid #95a5a6;"
        f"padding:12px;border-radius:6px;white-space:pre-wrap;'>"
        f"{d.get('propriedade') or '—'}</div>",
        unsafe_allow_html=True
    )

    st.markdown("---")

    # Bloco 6 — Documentação
    st.markdown("### 📝 Documentação e Observações")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**OBS1 — Registro / Título de Propriedade**")
        st.markdown(
            f"<div style='background:#fffbf0;border-left:4px solid #f39c12;"
            f"padding:12px;border-radius:6px;min-height:60px;white-space:pre-wrap;'>"
            f"{d.get('obs1') or '—'}</div>",
            unsafe_allow_html=True
        )

    with col2:
        st.markdown("**OBS5 — Situação da Escrituração**")
        st.markdown(
            f"<div style='background:#f0fff4;border-left:4px solid #27ae60;"
            f"padding:12px;border-radius:6px;min-height:60px;white-space:pre-wrap;'>"
            f"{d.get('obs5') or '—'}</div>",
            unsafe_allow_html=True
        )

    st.markdown(f"**Processo Administrativo**")
    st.markdown(
        f"<div style='background:#f5f0ff;border-left:4px solid #8e44ad;"
        f"padding:12px;border-radius:6px;'>"
        f"{d.get('processo') or '—'}</div>",
        unsafe_allow_html=True
    )
