"""relatorios.py"""
import streamlit as st
import pandas as pd
import io
from datetime import datetime
from database import buscar_para_relatorio, listar_valores_unicos, LABELS
from utils import fmt_moeda

RENAME = {
    "id": "ID", "total_seq": "Nº Total", "n_suest": "Nº SUEST",
    "rip": "RIP", "rip_utilizacao": "RIP Utilização",
    "valor_terreno": "Valor Terreno (R$)", "valor_benfeitoria": "Valor Benfeitoria (R$)",
    "valor_total": "Valor Total (R$)", "estado": "Estado",
    "cod_municipio": "Cód. Município", "municipio": "Município",
    "endereco": "Endereço", "area_terreno": "Área Terreno",
    "area_construida": "Área Construída", "propriedade": "Propriedade",
    "ocupacao": "Ocupação / Destinação", "obs1": "OBS1 (Registro/Título)",
    "processo": "Processo", "obs5": "OBS5 (Escrituração)",
    "data_importacao": "Data Importação",
}


def exportar_excel(df):
    buf = io.BytesIO()
    df_e = df.rename(columns=RENAME)
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df_e.to_excel(writer, index=False, sheet_name="Imóveis")
        ws = writer.sheets["Imóveis"]
        for i, col in enumerate(df_e.columns, 1):
            w = max(len(str(col)), df_e[col].astype(str).str.len().max() if len(df_e) > 0 else 10)
            ws.column_dimensions[ws.cell(1, i).column_letter].width = min(w + 2, 60)

        # aba resumo
        vt = pd.to_numeric(df["valor_total"], errors="coerce").sum()
        resumo = pd.DataFrame({
            "Métrica": ["Total de Imóveis", "Valor Total (R$)", "Estados", "Municípios", "Data"],
            "Valor": [len(df), fmt_moeda(vt),
                      df["estado"].nunique(), df["municipio"].nunique(),
                      datetime.now().strftime("%d/%m/%Y %H:%M")]
        })
        resumo.to_excel(writer, index=False, sheet_name="Resumo")
    return buf.getvalue()


def exportar_csv(df):
    return df.rename(columns=RENAME).to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")


def render_pagina_relatorios():
    st.title("📄 Geração de Relatórios")
    st.markdown("Configure os filtros e exporte os dados.")
    st.markdown("---")

    st.markdown("### 🔍 Filtros")
    c1, c2 = st.columns(2)
    filtros = {}

    with c1:
        filtros["estado"]    = st.selectbox("Estado",    ["Todos"] + listar_valores_unicos("estado"),    key="r_est")
        filtros["propriedade"] = st.selectbox("Propriedade", ["Todos"] + listar_valores_unicos("propriedade"), key="r_prop")
        filtros["so_cessao"] = st.checkbox("🔄 Somente Cessão de Uso", key="r_cess")

    with c2:
        filtros["municipio"] = st.selectbox("Município",  ["Todos"] + listar_valores_unicos("municipio"), key="r_mun")
        busca = st.text_input("Busca por texto", key="r_busca")
        filtros["so_rip_util"] = st.checkbox("📋 Somente com RIP Utilização", key="r_riputil")

    for k in ["estado", "municipio", "propriedade"]:
        if filtros.get(k) == "Todos":
            filtros[k] = None

    st.markdown("---")

    if st.button("🔍 Aplicar e Visualizar", type="primary", use_container_width=True):
        with st.spinner("Buscando..."):
            df = buscar_para_relatorio(filtros=filtros, busca_global=busca)
            st.session_state.df_rel = df

    if "df_rel" in st.session_state:
        df = st.session_state.df_rel
        st.markdown(f"### {len(df):,} registros encontrados".replace(",","."))

        if len(df) > 0:
            c1, c2, c3 = st.columns(3)
            vt = pd.to_numeric(df["valor_total"], errors="coerce").sum()
            c1.metric("Valor Total", fmt_moeda(vt))
            c2.metric("Estados",    str(df["estado"].nunique()))
            c3.metric("Municípios", str(df["municipio"].nunique()))

            st.dataframe(
                df[["rip","rip_utilizacao","municipio","estado","endereco",
                    "propriedade","ocupacao","valor_total","area_terreno",
                    "obs1","processo","obs5"]].head(100),
                use_container_width=True, hide_index=True
            )

            st.markdown("---")
            st.markdown("### 💾 Exportar")
            nome = f"imoveis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            ca, cb = st.columns(2)
            with ca:
                st.download_button("📥 Excel (.xlsx)", exportar_excel(df),
                    file_name=f"{nome}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True, type="primary")
            with cb:
                st.download_button("📥 CSV (.csv)", exportar_csv(df),
                    file_name=f"{nome}.csv", mime="text/csv",
                    use_container_width=True)
        else:
            st.info("Nenhum registro encontrado.")
