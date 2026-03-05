"""
busca.py - Lógica de busca e filtros
"""

import streamlit as st
import pandas as pd
from database import (
    buscar_imoveis, listar_valores_unicos,
    buscar_por_id, contar_registros
)
from utils import formatar_moeda, formatar_area, formatar_numero

REGISTROS_POR_PAGINA = 50


def render_filtros_sidebar():
    """
    Renderiza os filtros no sidebar e retorna dict de filtros ativos.
    """
    st.sidebar.markdown("## 🔍 Filtros")

    filtros = {}

    # Estado
    try:
        estados = ["Todos"] + listar_valores_unicos("ESTADO")
    except Exception:
        estados = ["Todos"]
    filtros["estado"] = st.sidebar.selectbox("🗺️ Estado", estados, key="filtro_estado")

    # Município (dependente do estado)
    try:
        if filtros["estado"] != "Todos":
            from database import get_connection
            import sqlite3
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT MUNICIPIO FROM imoveis WHERE ESTADO = ? AND MUNICIPIO IS NOT NULL ORDER BY MUNICIPIO",
                [filtros["estado"]]
            )
            municipios = ["Todos"] + [r[0] for r in cursor.fetchall()]
            conn.close()
        else:
            municipios = ["Todos"] + listar_valores_unicos("MUNICIPIO")
    except Exception:
        municipios = ["Todos"]

    filtros["municipio"] = st.sidebar.selectbox("🏙️ Município", municipios, key="filtro_municipio")

    # Tipo de propriedade
    try:
        propriedades = ["Todos"] + listar_valores_unicos("PROPRIEDADE")
    except Exception:
        propriedades = ["Todos"]
    filtros["propriedade"] = st.sidebar.selectbox("🏢 Propriedade", propriedades, key="filtro_propriedade")

    # Situação de ocupação
    try:
        ocupacoes = ["Todos"] + listar_valores_unicos("OCUPACAO")
    except Exception:
        ocupacoes = ["Todos"]
    filtros["ocupacao"] = st.sidebar.selectbox("🔑 Ocupação", ocupacoes, key="filtro_ocupacao")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💰 Faixa de Valor Total")
    usar_valor = st.sidebar.checkbox("Filtrar por valor", key="usar_filtro_valor")
    if usar_valor:
        col1, col2 = st.sidebar.columns(2)
        filtros["valor_min"] = col1.number_input("Mín (R$)", min_value=0.0, value=0.0, step=10000.0, key="valor_min")
        filtros["valor_max"] = col2.number_input("Máx (R$)", min_value=0.0, value=10000000.0, step=10000.0, key="valor_max")
    else:
        filtros["valor_min"] = None
        filtros["valor_max"] = None

    st.sidebar.markdown("### 📐 Área do Terreno (m²)")
    usar_area = st.sidebar.checkbox("Filtrar por área", key="usar_filtro_area")
    if usar_area:
        col1, col2 = st.sidebar.columns(2)
        filtros["area_min"] = col1.number_input("Mín (m²)", min_value=0.0, value=0.0, step=100.0, key="area_min")
        filtros["area_max"] = col2.number_input("Máx (m²)", min_value=0.0, value=100000.0, step=100.0, key="area_max")
    else:
        filtros["area_min"] = None
        filtros["area_max"] = None

    # Botão limpar filtros
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Limpar Filtros", use_container_width=True):
        for key in list(st.session_state.keys()):
            if key.startswith("filtro_") or key in [
                "usar_filtro_valor", "usar_filtro_area",
                "valor_min", "valor_max", "area_min", "area_max", "busca_global"
            ]:
                del st.session_state[key]
        st.rerun()

    return filtros


def render_pagina_busca():
    """
    Renderiza a página principal de busca e listagem de imóveis.
    """
    st.title("🏛️ Base de Imóveis Públicos")

    total_banco = contar_registros()
    if total_banco == 0:
        st.warning("⚠️ Nenhum imóvel cadastrado. Acesse **Importar Planilha** para começar.")
        return

    # Barra de busca global
    busca = st.text_input(
        "🔎 Busca Global",
        placeholder="Digite RIP, município, processo, endereço, observação...",
        key="busca_global"
    )

    # Filtros do sidebar
    filtros = render_filtros_sidebar()

    # Paginação
    if "pagina_atual" not in st.session_state:
        st.session_state.pagina_atual = 0

    # Reseta página ao buscar/filtrar
    busca_key = str(busca) + str(filtros)
    if "ultima_busca" not in st.session_state:
        st.session_state.ultima_busca = busca_key
    if st.session_state.ultima_busca != busca_key:
        st.session_state.pagina_atual = 0
        st.session_state.ultima_busca = busca_key

    offset = st.session_state.pagina_atual * REGISTROS_POR_PAGINA

    # Busca no banco
    df, total = buscar_imoveis(
        filtros=filtros,
        busca_global=busca,
        limit=REGISTROS_POR_PAGINA,
        offset=offset
    )

    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📊 Resultados", formatar_numero(total))
    col2.metric("📦 Total no Banco", formatar_numero(total_banco))
    if not df.empty and "VALOR_TOTAL" in df.columns:
        valor_total = df["VALOR_TOTAL"].sum()
        col3.metric("💰 Valor (página)", formatar_moeda(valor_total))
    if not df.empty and "AREA_TERRENO" in df.columns:
        area_total = df["AREA_TERRENO"].sum()
        col4.metric("📐 Área (página)", formatar_area(area_total))

    st.markdown("---")

    if df.empty:
        st.info("Nenhum resultado encontrado para os filtros aplicados.")
        return

    # Tabela de resultados
    st.markdown(f"### Resultados — Página {st.session_state.pagina_atual + 1}")

    # Prepara display
    colunas_exibir = ["id", "RIP", "MUNICIPIO", "ESTADO", "ENDERECO",
                      "PROPRIEDADE", "OCUPACAO", "VALOR_TOTAL", "AREA_TERRENO"]
    colunas_validas = [c for c in colunas_exibir if c in df.columns]
    df_display = df[colunas_validas].copy()

    # Formata valores para exibição
    if "VALOR_TOTAL" in df_display.columns:
        df_display["VALOR_TOTAL"] = df_display["VALOR_TOTAL"].apply(
            lambda x: formatar_moeda(x) if pd.notna(x) else "-"
        )
    if "AREA_TERRENO" in df_display.columns:
        df_display["AREA_TERRENO"] = df_display["AREA_TERRENO"].apply(
            lambda x: f"{x:,.2f} m²".replace(",", "X").replace(".", ",").replace("X", ".") if pd.notna(x) else "-"
        )

    # Renomeia colunas para display
    df_display.columns = [
        c.replace("_", " ").replace("VALOR TOTAL", "VALOR TOTAL (R$)")
        .replace("AREA TERRENO", "ÁREA (m²)")
        for c in df_display.columns
    ]

    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        height=400
    )

    # Seleção de imóvel para detalhes
    st.markdown("#### 🔎 Ver detalhes de um imóvel")
    col_sel1, col_sel2 = st.columns([2, 1])
    with col_sel1:
        ids_disponiveis = df["id"].tolist()
        id_selecionado = st.selectbox(
            "Selecione o ID do imóvel:",
            options=ids_disponiveis,
            format_func=lambda x: f"ID {x} — {df[df['id']==x]['RIP'].values[0] if len(df[df['id']==x]) > 0 else x}",
            key="id_detalhe_select"
        )
    with col_sel2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔎 Ver Detalhes", use_container_width=True, type="primary"):
            st.session_state.imovel_detalhe_id = id_selecionado
            st.session_state.pagina_menu = "Detalhes do Imóvel"
            st.rerun()

    # Paginação
    st.markdown("---")
    total_paginas = max(1, -(-total // REGISTROS_POR_PAGINA))
    col_prev, col_info, col_next = st.columns([1, 2, 1])

    with col_prev:
        if st.button("◀ Anterior", disabled=st.session_state.pagina_atual == 0):
            st.session_state.pagina_atual -= 1
            st.rerun()

    with col_info:
        st.markdown(
            f"<div style='text-align:center; padding-top:8px;'>"
            f"Página <b>{st.session_state.pagina_atual + 1}</b> de <b>{total_paginas}</b>"
            f"</div>",
            unsafe_allow_html=True
        )

    with col_next:
        if st.button("Próximo ▶", disabled=st.session_state.pagina_atual >= total_paginas - 1):
            st.session_state.pagina_atual += 1
            st.rerun()


def render_detalhe_imovel(imovel_id=None):
    """
    Renderiza a página de detalhes de um imóvel.
    """
    if imovel_id is None:
        imovel_id = st.session_state.get("imovel_detalhe_id")

    if imovel_id is None:
        st.info("Nenhum imóvel selecionado. Volte para a base e clique em 'Ver Detalhes'.")
        return

    imovel = buscar_por_id(imovel_id)

    if imovel is None:
        st.error("Imóvel não encontrado.")
        return

    if st.button("← Voltar para a lista"):
        st.session_state.pagina_menu = "Base de Imóveis"
        st.rerun()

    st.title(f"🏛️ Detalhes do Imóvel")
    st.markdown(f"### RIP: `{imovel.get('RIP', 'N/A')}`")

    st.markdown("---")

    # Layout em colunas
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📍 Localização")
        st.markdown(f"**Estado:** {imovel.get('ESTADO') or '—'}")
        st.markdown(f"**Município:** {imovel.get('MUNICIPIO') or '—'}")
        st.markdown(f"**Cód. Município:** {imovel.get('COD_MUNICIPIO') or '—'}")
        st.markdown(f"**Endereço:** {imovel.get('ENDERECO') or '—'}")

        st.markdown("#### 📋 Identificação")
        st.markdown(f"**RIP:** {imovel.get('RIP') or '—'}")
        st.markdown(f"**RIP Utilização:** {imovel.get('RIP_UTILIZACAO') or '—'}")
        st.markdown(f"**Nº SUEST:** {imovel.get('N_SUEST') or '—'}")
        st.markdown(f"**Processo:** {imovel.get('PROCESSO') or '—'}")

    with col2:
        st.markdown("#### 💰 Valores")
        val_terreno = imovel.get('VALOR_TERRENO')
        val_benf = imovel.get('VALOR_BENFEITORIA')
        val_total = imovel.get('VALOR_TOTAL')
        st.markdown(f"**Valor Terreno:** {formatar_moeda(val_terreno) if val_terreno else '—'}")
        st.markdown(f"**Valor Benfeitoria:** {formatar_moeda(val_benf) if val_benf else '—'}")
        st.markdown(f"**Valor Total:** {formatar_moeda(val_total) if val_total else '—'}")

        st.markdown("#### 📐 Áreas")
        area_terreno = imovel.get('AREA_TERRENO')
        area_const = imovel.get('AREA_CONSTRUIDA')
        st.markdown(f"**Área Terreno:** {formatar_area(area_terreno) if area_terreno else '—'}")
        st.markdown(f"**Área Construída:** {formatar_area(area_const) if area_const else '—'}")

        st.markdown("#### 🏢 Situação")
        st.markdown(f"**Propriedade:** {imovel.get('PROPRIEDADE') or '—'}")
        st.markdown(f"**Ocupação:** {imovel.get('OCUPACAO') or '—'}")

    # Observações
    st.markdown("---")
    st.markdown("#### 📝 Observações")
    col_obs1, col_obs2 = st.columns(2)
    with col_obs1:
        obs1 = imovel.get('OBS1') or '—'
        st.markdown(f"**OBS1:** {obs1}")
    with col_obs2:
        obs5 = imovel.get('OBS5') or '—'
        st.markdown(f"**OBS5:** {obs5}")

    # Dados brutos em expansor
    with st.expander("📊 Todos os campos (dados brutos)"):
        dados_display = {k: v for k, v in imovel.items() if k not in ['data_importacao']}
        df_detalhe = pd.DataFrame([dados_display]).T.reset_index()
        df_detalhe.columns = ["Campo", "Valor"]
        st.dataframe(df_detalhe, use_container_width=True, hide_index=True)
