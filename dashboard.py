"""dashboard.py"""
import streamlit as st
import pandas as pd
import plotly.express as px
from database import buscar_todos_para_dashboard, contar_registros, eh_cessao
from utils import fmt_moeda, fmt_numero


def render_dashboard():
    st.title("📊 Dashboard — Imóveis Públicos")

    if contar_registros() == 0:
        st.warning("⚠️ Importe uma planilha primeiro."); return

    df = buscar_todos_para_dashboard()
    if df.empty:
        st.warning("Sem dados."); return

    # ── KPIs ──────────────────────────────────────────────────────────────────
    total = len(df)
    valor_total = pd.to_numeric(df["valor_total"], errors="coerce").sum()
    cessoes = df["ocupacao"].apply(eh_cessao).sum()
    estados_n = df["estado"].nunique()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🏛️ Total de Imóveis",   fmt_numero(total))
    c2.metric("💰 Valor Total",         fmt_moeda(valor_total))
    c3.metric("🔄 Em Cessão de Uso",    fmt_numero(int(cessoes)))
    c4.metric("🗺️ Estados",            str(estados_n))

    st.markdown("---")

    # ── Linha 1: Estado | Município ───────────────────────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("### 🗺️ Imóveis por Estado")
        d = df["estado"].dropna().value_counts().reset_index()
        d.columns = ["Estado", "Qtd"]
        d = d.sort_values("Qtd", ascending=True)
        fig = px.bar(d, x="Qtd", y="Estado", orientation="h",
                     color="Qtd", color_continuous_scale="Blues",
                     template="plotly_white")
        fig.update_layout(height=420, showlegend=False, coloraxis_showscale=False,
                          margin=dict(l=5,r=5,t=5,b=5))
        fig.update_traces(texttemplate="%{x}", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown("### 🏙️ Top 15 Municípios")
        d = df["municipio"].dropna().value_counts().head(15).reset_index()
        d.columns = ["Município", "Qtd"]
        d = d.sort_values("Qtd", ascending=True)
        fig = px.bar(d, x="Qtd", y="Município", orientation="h",
                     color="Qtd", color_continuous_scale="Greens",
                     template="plotly_white")
        fig.update_layout(height=420, showlegend=False, coloraxis_showscale=False,
                          margin=dict(l=5,r=5,t=5,b=5))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ── Linha 2: Ocupação (top categorias) | Cessão vs Não-cessão ────────────
    col_c, col_d = st.columns(2)

    with col_c:
        st.markdown("### 🔑 Top 15 Tipos de Ocupação / Destinação")
        d = df["ocupacao"].dropna().replace("", pd.NA).dropna()
        # normaliza um pouco
        d = d.str.strip().value_counts().head(15).reset_index()
        d.columns = ["Ocupação", "Qtd"]
        d = d.sort_values("Qtd", ascending=True)
        fig = px.bar(d, x="Qtd", y="Ocupação", orientation="h",
                     color="Qtd", color_continuous_scale="Oranges",
                     template="plotly_white")
        fig.update_layout(height=420, showlegend=False, coloraxis_showscale=False,
                          margin=dict(l=5,r=5,t=5,b=5))
        st.plotly_chart(fig, use_container_width=True)

    with col_d:
        st.markdown("### 🔄 Situação de Uso")
        cessao_s = df["ocupacao"].apply(
            lambda x: "Cessão de Uso" if eh_cessao(x) else (
                "Sem informação" if (not x or str(x).strip() in ("","nan","None"))
                else "Em uso / Outro"
            )
        )
        d = cessao_s.value_counts().reset_index()
        d.columns = ["Situação", "Qtd"]
        cores = {
            "Cessão de Uso":   "#3498db",
            "Em uso / Outro":  "#27ae60",
            "Sem informação":  "#bdc3c7",
        }
        fig = px.pie(d, names="Situação", values="Qtd", hole=0.4,
                     color="Situação", color_discrete_map=cores)
        fig.update_layout(height=420, margin=dict(l=5,r=5,t=30,b=5))
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ── Linha 3: Valor por estado | Propriedade ───────────────────────────────
    col_e, col_f = st.columns(2)

    with col_e:
        st.markdown("### 💰 Valor Total por Estado")
        df["_vt"] = pd.to_numeric(df["valor_total"], errors="coerce")
        d = df.groupby("estado")["_vt"].sum().reset_index().sort_values("_vt", ascending=False).head(15)
        d.columns = ["Estado", "Valor"]
        fig = px.bar(d, x="Estado", y="Valor", color="Valor",
                     color_continuous_scale="Reds", template="plotly_white")
        fig.update_layout(height=350, showlegend=False, coloraxis_showscale=False,
                          margin=dict(l=5,r=5,t=5,b=5))
        st.plotly_chart(fig, use_container_width=True)

    with col_f:
        st.markdown("### 🏢 Tipo de Propriedade")
        # Normaliza variações (Próprio / PRÓPRIO → Próprio)
        prop_norm = df["propriedade"].dropna().replace("", pd.NA).dropna()
        prop_norm = prop_norm.str.strip()
        # Agrupa variações óbvias
        prop_norm = prop_norm.replace({
            "PRÓPRIO": "Próprio", "Próprio": "Próprio",
            "REGULAR": "Regular",
            "IRREGULAR": "Irregular",
            "UNIÃO": "União",
        })
        d = prop_norm.value_counts().head(10).reset_index()
        d.columns = ["Propriedade", "Qtd"]
        fig = px.pie(d, names="Propriedade", values="Qtd", hole=0.4,
                     color_discrete_sequence=px.colors.qualitative.Set3)
        fig.update_layout(height=350, margin=dict(l=5,r=5,t=30,b=5))
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ── Tabela resumo por estado ──────────────────────────────────────────────
    st.markdown("### 📋 Resumo por Estado")
    df["_vt"] = pd.to_numeric(df["valor_total"], errors="coerce")
    df["_cessao"] = df["ocupacao"].apply(eh_cessao)
    resumo = df.groupby("estado").agg(
        Imóveis=("id", "count"),
        Cessões=("_cessao", "sum"),
        Valor_Total=("_vt", "sum")
    ).reset_index().sort_values("Imóveis", ascending=False)
    resumo["Valor_Total"] = resumo["Valor_Total"].apply(fmt_moeda)
    resumo["Cessões"] = resumo["Cessões"].astype(int)
    resumo.columns = ["Estado", "Qtd. Imóveis", "Em Cessão", "Valor Total"]
    st.dataframe(resumo, use_container_width=True, hide_index=True)
