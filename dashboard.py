"""
dashboard.py - Dashboard com gráficos automáticos
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import buscar_todos_para_dashboard, contar_registros
from utils import formatar_moeda, formatar_numero


def render_dashboard():
    """Renderiza o dashboard com gráficos automáticos."""
    st.title("📊 Dashboard — Imóveis Públicos")

    total = contar_registros()
    if total == 0:
        st.warning("⚠️ Nenhum dado disponível. Importe uma planilha primeiro.")
        return

    df = buscar_todos_para_dashboard()

    if df.empty:
        st.warning("Nenhum dado disponível.")
        return

    # ── KPIs no topo ─────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    total_imoveis = len(df)
    valor_total = df["VALOR_TOTAL"].sum() if "VALOR_TOTAL" in df.columns else 0
    area_total = df["AREA_TERRENO"].sum() if "AREA_TERRENO" in df.columns else 0
    estados_count = df["ESTADO"].nunique() if "ESTADO" in df.columns else 0

    col1.metric("🏛️ Total de Imóveis", formatar_numero(total_imoveis))
    col2.metric("💰 Valor Total", formatar_moeda(valor_total))
    col3.metric("📐 Área Total (m²)", f"{area_total:,.0f}".replace(",", "."))
    col4.metric("🗺️ Estados", str(estados_count))

    st.markdown("---")

    # ── Linha 1: Estados e Municípios ────────────────────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("### 🗺️ Imóveis por Estado")
        if "ESTADO" in df.columns:
            df_estado = (
                df["ESTADO"]
                .dropna()
                .value_counts()
                .reset_index()
            )
            df_estado.columns = ["Estado", "Quantidade"]
            df_estado = df_estado.sort_values("Quantidade", ascending=True).tail(20)

            fig_estado = px.bar(
                df_estado,
                x="Quantidade",
                y="Estado",
                orientation='h',
                color="Quantidade",
                color_continuous_scale="Blues",
                template="plotly_white"
            )
            fig_estado.update_layout(
                height=400,
                showlegend=False,
                coloraxis_showscale=False,
                margin=dict(l=10, r=10, t=10, b=10)
            )
            fig_estado.update_traces(texttemplate='%{x}', textposition='outside')
            st.plotly_chart(fig_estado, use_container_width=True)
        else:
            st.info("Campo ESTADO não disponível.")

    with col_b:
        st.markdown("### 🏙️ Top 15 Municípios")
        if "MUNICIPIO" in df.columns:
            df_mun = (
                df["MUNICIPIO"]
                .dropna()
                .value_counts()
                .head(15)
                .reset_index()
            )
            df_mun.columns = ["Município", "Quantidade"]
            df_mun = df_mun.sort_values("Quantidade", ascending=True)

            fig_mun = px.bar(
                df_mun,
                x="Quantidade",
                y="Município",
                orientation='h',
                color="Quantidade",
                color_continuous_scale="Greens",
                template="plotly_white"
            )
            fig_mun.update_layout(
                height=400,
                showlegend=False,
                coloraxis_showscale=False,
                margin=dict(l=10, r=10, t=10, b=10)
            )
            st.plotly_chart(fig_mun, use_container_width=True)
        else:
            st.info("Campo MUNICIPIO não disponível.")

    st.markdown("---")

    # ── Linha 2: Propriedade e Ocupação ──────────────────────────────────────
    col_c, col_d = st.columns(2)

    with col_c:
        st.markdown("### 🏢 Tipo de Propriedade")
        if "PROPRIEDADE" in df.columns:
            df_prop = (
                df["PROPRIEDADE"]
                .dropna()
                .replace('', pd.NA)
                .dropna()
                .value_counts()
                .reset_index()
            )
            df_prop.columns = ["Propriedade", "Quantidade"]

            if not df_prop.empty:
                fig_prop = px.pie(
                    df_prop,
                    names="Propriedade",
                    values="Quantidade",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_prop.update_layout(
                    height=350,
                    margin=dict(l=10, r=10, t=30, b=10),
                    legend=dict(orientation="v", x=1.01)
                )
                fig_prop.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_prop, use_container_width=True)
            else:
                st.info("Sem dados de propriedade.")
        else:
            st.info("Campo PROPRIEDADE não disponível.")

    with col_d:
        st.markdown("### 🔑 Situação de Ocupação")
        if "OCUPACAO" in df.columns:
            df_ocup = (
                df["OCUPACAO"]
                .dropna()
                .replace('', pd.NA)
                .dropna()
                .value_counts()
                .reset_index()
            )
            df_ocup.columns = ["Ocupação", "Quantidade"]

            if not df_ocup.empty:
                cores = {
                    "OCUPADO": "#e74c3c",
                    "DESOCUPADO": "#2ecc71",
                    "CEDIDO": "#3498db",
                    "IRREGULAR": "#e67e22",
                }
                fig_ocup = px.bar(
                    df_ocup,
                    x="Ocupação",
                    y="Quantidade",
                    color="Ocupação",
                    color_discrete_map=cores,
                    template="plotly_white"
                )
                fig_ocup.update_layout(
                    height=350,
                    showlegend=False,
                    margin=dict(l=10, r=10, t=10, b=60)
                )
                fig_ocup.update_traces(texttemplate='%{y}', textposition='outside')
                st.plotly_chart(fig_ocup, use_container_width=True)
            else:
                st.info("Sem dados de ocupação.")
        else:
            st.info("Campo OCUPACAO não disponível.")

    st.markdown("---")

    # ── Linha 3: Valor por Estado e Distribuição de Áreas ───────────────────
    col_e, col_f = st.columns(2)

    with col_e:
        st.markdown("### 💰 Valor Total por Estado")
        if "ESTADO" in df.columns and "VALOR_TOTAL" in df.columns:
            df_val_estado = (
                df.groupby("ESTADO")["VALOR_TOTAL"]
                .sum()
                .reset_index()
                .sort_values("VALOR_TOTAL", ascending=False)
                .head(15)
            )
            df_val_estado.columns = ["Estado", "Valor Total"]

            fig_val = px.bar(
                df_val_estado,
                x="Estado",
                y="Valor Total",
                color="Valor Total",
                color_continuous_scale="Oranges",
                template="plotly_white"
            )
            fig_val.update_layout(
                height=350,
                showlegend=False,
                coloraxis_showscale=False,
                margin=dict(l=10, r=10, t=10, b=10),
                yaxis_tickformat=","
            )
            st.plotly_chart(fig_val, use_container_width=True)
        else:
            st.info("Dados de valor por estado não disponíveis.")

    with col_f:
        st.markdown("### 📐 Distribuição de Área do Terreno")
        if "AREA_TERRENO" in df.columns:
            df_area = df["AREA_TERRENO"].dropna()
            df_area = df_area[df_area > 0]

            if len(df_area) > 0:
                # Remove outliers extremos para melhor visualização
                q99 = df_area.quantile(0.99)
                df_area_plot = df_area[df_area <= q99]

                fig_hist = px.histogram(
                    df_area_plot,
                    x=df_area_plot,
                    nbins=30,
                    color_discrete_sequence=["#8e44ad"],
                    template="plotly_white"
                )
                fig_hist.update_layout(
                    height=350,
                    xaxis_title="Área (m²)",
                    yaxis_title="Quantidade",
                    showlegend=False,
                    margin=dict(l=10, r=10, t=10, b=10)
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            else:
                st.info("Sem dados de área disponíveis.")
        else:
            st.info("Campo AREA_TERRENO não disponível.")

    st.markdown("---")

    # ── Tabela resumo por estado ─────────────────────────────────────────────
    st.markdown("### 📋 Resumo por Estado")
    if "ESTADO" in df.columns:
        agg_dict = {"id": "count"}
        if "VALOR_TOTAL" in df.columns:
            agg_dict["VALOR_TOTAL"] = "sum"
        if "AREA_TERRENO" in df.columns:
            agg_dict["AREA_TERRENO"] = "sum"
        if "AREA_CONSTRUIDA" in df.columns:
            agg_dict["AREA_CONSTRUIDA"] = "sum"

        df_resumo = df.groupby("ESTADO").agg(agg_dict).reset_index()
        df_resumo.columns = (
            ["Estado", "Qtd. Imóveis"] +
            (["Valor Total"] if "VALOR_TOTAL" in agg_dict else []) +
            (["Área Terreno (m²)"] if "AREA_TERRENO" in agg_dict else []) +
            (["Área Construída (m²)"] if "AREA_CONSTRUIDA" in agg_dict else [])
        )
        df_resumo = df_resumo.sort_values("Qtd. Imóveis", ascending=False)

        if "Valor Total" in df_resumo.columns:
            df_resumo["Valor Total"] = df_resumo["Valor Total"].apply(
                lambda x: formatar_moeda(x) if pd.notna(x) else "—"
            )

        st.dataframe(df_resumo, use_container_width=True, hide_index=True)
