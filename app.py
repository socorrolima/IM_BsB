"""
app.py — Sistema de Gestão de Imóveis Públicos
Inicie com: streamlit run app.py
"""
import streamlit as st
import pandas as pd
import io

st.set_page_config(
    page_title="Imóveis Públicos",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
section[data-testid="stSidebar"] { background-color: #1a2332; min-width: 260px; }
section[data-testid="stSidebar"] * { color: #ecf0f1 !important; }
[data-testid="stMetric"] {
    background:#f8f9fa; border-radius:10px;
    padding:12px; border-left:4px solid #3498db;
}
.stDataFrame { border-radius:8px; }
</style>
""", unsafe_allow_html=True)

from database import criar_tabelas, contar_registros
criar_tabelas()

if "pagina_menu" not in st.session_state:
    st.session_state.pagina_menu = "Dashboard"

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:20px 0 10px'>
        <div style='font-size:2.2rem'>🏛️</div>
        <div style='font-size:1.05rem;font-weight:bold'>Imóveis Públicos</div>
        <div style='font-size:0.72rem;color:#7f8c8d'>Funasa / SPU</div>
    </div>""", unsafe_allow_html=True)
    st.markdown("---")

    for icone, nome in [
        ("📊", "Dashboard"),
        ("🏛️", "Base de Imóveis"),
        ("📄", "Relatórios"),
        ("📂", "Importar Planilha"),
    ]:
        label = f"{icone}  {nome}"
        if st.session_state.pagina_menu == nome:
            st.markdown(
                f"<div style='background:#2980b9;border-radius:6px;"
                f"padding:9px 14px;margin-bottom:5px;font-weight:bold'>{label}</div>",
                unsafe_allow_html=True
            )
        else:
            if st.button(label, use_container_width=True, key=f"nav_{nome}"):
                st.session_state.pagina_menu = nome
                if nome == "Base de Imóveis":
                    st.session_state.pagina_atual = 0
                st.rerun()

    st.markdown("---")
    n = contar_registros()
    cor = "#27ae60" if n > 0 else "#c0392b"
    txt = f"✅ {n:,} imóveis".replace(",",".") if n > 0 else "⚠️ Banco vazio"
    st.markdown(
        f"<div style='background:{cor};border-radius:6px;padding:8px 12px;"
        f"text-align:center;font-size:0.85rem'>{txt}</div>",
        unsafe_allow_html=True
    )

# ── Roteamento ────────────────────────────────────────────────────────────────
p = st.session_state.pagina_menu

if p == "Dashboard":
    from dashboard import render_dashboard
    render_dashboard()

elif p == "Base de Imóveis":
    from busca import render_pagina_busca
    render_pagina_busca()

elif p == "Detalhes do Imóvel":
    from busca import render_detalhe_imovel
    render_detalhe_imovel()

elif p == "Relatórios":
    from relatorios import render_pagina_relatorios
    render_pagina_relatorios()

elif p == "Importar Planilha":
    from importador_excel import importar_excel, detectar_colunas_excel
    from database import historico_importacoes

    st.title("📂 Importar Planilha Excel")
    st.markdown("---")

    st.markdown("### 1️⃣ Selecione o arquivo")
    arquivo = st.file_uploader("Arraste ou clique (.xlsx / .xls)", type=["xlsx","xls"])

    if arquivo:
        arquivo.seek(0)
        cols = detectar_colunas_excel(arquivo)
        if cols:
            with st.expander(f"🔍 Colunas detectadas ({len(cols)})"):
                st.write(cols)

        st.markdown("### 2️⃣ Modo de importação")
        modo = st.radio("", ["atualizar","substituir"],
            format_func=lambda x:
                "🔄 Atualizar — adiciona novos, atualiza existentes por RIP" if x=="atualizar"
                else "🗑️ Substituir — apaga tudo e reimporta do zero")

        if modo == "substituir":
            st.warning("⚠️ Apagará TODOS os dados existentes!")

        st.markdown("### 3️⃣ Importar")
        if st.button("📥 Iniciar Importação", type="primary", use_container_width=True):
            with st.spinner("Importando... aguarde..."):
                arquivo.seek(0)
                r = importar_excel(arquivo, arquivo.name, modo=modo)

            if r["sucesso"]:
                st.success(r["mensagem"])
                c1,c2,c3,c4 = st.columns(4)
                c1.metric("Lidos",      r["total_lidos"])
                c2.metric("Novos",      r["novos_registros"])
                c3.metric("Atualizados",r["atualizados"])
                c4.metric("Ignorados",  r["ignorados"])
                st.balloons()
                st.info("Acesse **Base de Imóveis** para consultar.")
            else:
                st.error(r["mensagem"])
                if r.get("erros"):
                    with st.expander("Detalhes"):
                        for e in r["erros"][:10]: st.code(e)

    st.markdown("---")
    st.markdown("### 📜 Histórico")
    hist = historico_importacoes()
    if not hist.empty:
        hist.columns = ["ID","Arquivo","Data","Total","Novos"]
        st.dataframe(hist, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma importação ainda.")
