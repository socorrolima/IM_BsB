"""
relatorios.py - Geração de relatórios em Excel e CSV
"""

import streamlit as st
import pandas as pd
import io
from datetime import datetime
from database import buscar_com_filtros_para_relatorio, listar_valores_unicos
from utils import formatar_moeda


NOMES_COLUNAS = {
    "id": "ID",
    "TOTAL": "Total",
    "N_SUEST": "Nº SUEST",
    "RIP": "RIP",
    "RIP_UTILIZACAO": "RIP Utilização",
    "VALOR_TERRENO": "Valor Terreno (R$)",
    "VALOR_BENFEITORIA": "Valor Benfeitoria (R$)",
    "VALOR_TOTAL": "Valor Total (R$)",
    "ESTADO": "Estado",
    "COD_MUNICIPIO": "Cód. Município",
    "MUNICIPIO": "Município",
    "ENDERECO": "Endereço",
    "AREA_TERRENO": "Área Terreno (m²)",
    "AREA_CONSTRUIDA": "Área Construída (m²)",
    "PROPRIEDADE": "Propriedade",
    "OCUPACAO": "Ocupação",
    "OBS1": "OBS1",
    "PROCESSO": "Processo",
    "OBS5": "OBS5",
    "data_importacao": "Data Importação"
}


def exportar_excel(df):
    """Exporta DataFrame para bytes de Excel."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Renomeia colunas
        df_export = df.rename(columns=NOMES_COLUNAS)

        df_export.to_excel(writer, index=False, sheet_name="Imóveis")

        # Formata a planilha
        ws = writer.sheets["Imóveis"]

        # Ajusta largura das colunas
        for col_idx, col in enumerate(df_export.columns, 1):
            max_len = max(
                len(str(col)),
                df_export[col].astype(str).str.len().max() if len(df_export) > 0 else 0
            )
            ws.column_dimensions[ws.cell(1, col_idx).column_letter].width = min(max_len + 2, 50)

        # Aba de resumo
        if len(df) > 0:
            resumo_data = {
                "Métrica": [
                    "Total de Imóveis",
                    "Valor Total (R$)",
                    "Área Total Terreno (m²)",
                    "Área Total Construída (m²)",
                    "Estados",
                    "Municípios",
                    "Data do Relatório"
                ],
                "Valor": [
                    len(df),
                    f"R$ {df['VALOR_TOTAL'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if "VALOR_TOTAL" in df.columns else "N/A",
                    f"{df['AREA_TERRENO'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if "AREA_TERRENO" in df.columns else "N/A",
                    f"{df['AREA_CONSTRUIDA'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if "AREA_CONSTRUIDA" in df.columns else "N/A",
                    df["ESTADO"].nunique() if "ESTADO" in df.columns else "N/A",
                    df["MUNICIPIO"].nunique() if "MUNICIPIO" in df.columns else "N/A",
                    datetime.now().strftime("%d/%m/%Y %H:%M")
                ]
            }
            df_resumo = pd.DataFrame(resumo_data)
            df_resumo.to_excel(writer, index=False, sheet_name="Resumo")

    return output.getvalue()


def exportar_csv(df):
    """Exporta DataFrame para bytes de CSV."""
    df_export = df.rename(columns=NOMES_COLUNAS)
    return df_export.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')


def render_pagina_relatorios():
    """Renderiza a página de geração de relatórios."""
    st.title("📄 Geração de Relatórios")
    st.markdown("Configure os filtros abaixo e exporte os dados filtrados.")

    st.markdown("---")

    # ── Filtros do Relatório ────────────────────────────────────────────────
    st.markdown("### 🔍 Filtros do Relatório")

    col1, col2 = st.columns(2)
    filtros = {}

    with col1:
        try:
            estados = ["Todos"] + listar_valores_unicos("ESTADO")
        except Exception:
            estados = ["Todos"]
        filtros["estado"] = st.selectbox("🗺️ Estado", estados, key="rel_estado")

        try:
            propriedades = ["Todos"] + listar_valores_unicos("PROPRIEDADE")
        except Exception:
            propriedades = ["Todos"]
        filtros["propriedade"] = st.selectbox("🏢 Tipo de Propriedade", propriedades, key="rel_prop")

    with col2:
        try:
            municipios = ["Todos"] + listar_valores_unicos("MUNICIPIO")
        except Exception:
            municipios = ["Todos"]
        filtros["municipio"] = st.selectbox("🏙️ Município", municipios, key="rel_mun")

        try:
            ocupacoes = ["Todos"] + listar_valores_unicos("OCUPACAO")
        except Exception:
            ocupacoes = ["Todos"]
        filtros["ocupacao"] = st.selectbox("🔑 Situação de Ocupação", ocupacoes, key="rel_ocup")

    col3, col4 = st.columns(2)
    with col3:
        usar_valor = st.checkbox("Filtrar por valor", key="rel_usar_valor")
        if usar_valor:
            filtros["valor_min"] = st.number_input("Valor mínimo (R$)", min_value=0.0, value=0.0, step=1000.0, key="rel_vmin")
            filtros["valor_max"] = st.number_input("Valor máximo (R$)", min_value=0.0, value=10000000.0, step=1000.0, key="rel_vmax")
    with col4:
        busca_texto = st.text_input("🔎 Busca por texto", placeholder="RIP, endereço, processo...", key="rel_busca")

    # Normaliza filtros
    for key in ["estado", "municipio", "propriedade", "ocupacao"]:
        if filtros.get(key) == "Todos":
            filtros[key] = None
    if not usar_valor:
        filtros["valor_min"] = None
        filtros["valor_max"] = None

    st.markdown("---")

    # ── Preview e Exportação ───────────────────────────────────────────────
    if st.button("🔍 Aplicar Filtros e Pré-visualizar", type="primary", use_container_width=True):
        with st.spinner("Buscando dados..."):
            df = buscar_com_filtros_para_relatorio(filtros=filtros, busca_global=busca_texto)
            st.session_state.df_relatorio = df

    if "df_relatorio" in st.session_state and st.session_state.df_relatorio is not None:
        df = st.session_state.df_relatorio

        st.markdown(f"### 📊 Resultado: **{len(df):,}** registros encontrados")

        # Métricas resumo
        if len(df) > 0:
            col_m1, col_m2, col_m3 = st.columns(3)
            if "VALOR_TOTAL" in df.columns:
                col_m1.metric("💰 Valor Total", formatar_moeda(df["VALOR_TOTAL"].sum()))
            if "AREA_TERRENO" in df.columns:
                col_m2.metric("📐 Área Terreno", f"{df['AREA_TERRENO'].sum():,.0f} m²".replace(",", "."))
            if "ESTADO" in df.columns:
                col_m3.metric("🗺️ Estados", str(df["ESTADO"].nunique()))

            # Preview da tabela (100 primeiros)
            st.markdown("#### Preview (primeiros 100 registros)")
            colunas_preview = ["RIP", "MUNICIPIO", "ESTADO", "ENDERECO",
                               "PROPRIEDADE", "OCUPACAO", "VALOR_TOTAL", "AREA_TERRENO"]
            colunas_validas = [c for c in colunas_preview if c in df.columns]
            st.dataframe(df[colunas_validas].head(100), use_container_width=True, hide_index=True)

            # Botões de exportação
            st.markdown("---")
            st.markdown("### 💾 Exportar")

            nome_base = f"imoveis_publicos_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            col_exp1, col_exp2 = st.columns(2)

            with col_exp1:
                with st.spinner("Preparando Excel..."):
                    excel_bytes = exportar_excel(df)
                st.download_button(
                    label="📥 Baixar Excel (.xlsx)",
                    data=excel_bytes,
                    file_name=f"{nome_base}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    type="primary"
                )

            with col_exp2:
                csv_bytes = exportar_csv(df)
                st.download_button(
                    label="📥 Baixar CSV (.csv)",
                    data=csv_bytes,
                    file_name=f"{nome_base}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.info("Nenhum registro encontrado com os filtros aplicados.")
