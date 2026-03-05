"""
app.py - Aplicativo principal de gestão de imóveis públicos
Execute com: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import io

# ── Configuração da página ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Imóveis Públicos",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS customizado ────────────────────────────────────────────────────────
st.markdown("""
<style>
    section[data-testid="stSidebar"] {
        background-color: #1a2332;
        min-width: 260px;
    }
    section[data-testid="stSidebar"] * { color: #ecf0f1 !important; }
    [data-testid="stMetric"] {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 12px;
        border-left: 4px solid #3498db;
    }
    .stDataFrame { border-radius: 8px; overflow: hidden; }
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #f1f1f1; }
    ::-webkit-scrollbar-thumb { background: #888; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ── Inicialização do banco ─────────────────────────────────────────────────
from database import criar_tabelas, contar_registros
criar_tabelas()

# ── Estado da navegação ────────────────────────────────────────────────────
if "pagina_menu" not in st.session_state:
    st.session_state.pagina_menu = "Dashboard"

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 20px 0 15px 0;'>
        <div style='font-size:2.5rem;'>🏛️</div>
        <div style='font-size:1.1rem; font-weight:bold;'>Imóveis Públicos</div>
        <div style='font-size:0.75rem; color:#7f8c8d; margin-top:4px;'>Sistema de Gestão</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    MENU_ITEMS = [
        ("📊", "Dashboard"),
        ("🏛️", "Base de Imóveis"),
        ("📄", "Relatórios"),
        ("📂", "Importar Planilha"),
    ]

    for icone, nome in MENU_ITEMS:
        label = f"{icone}  {nome}"
        is_active = st.session_state.pagina_menu == nome
        if is_active:
            st.markdown(
                f"<div style='background:#2980b9;border-radius:6px;padding:9px 14px;"
                f"margin-bottom:5px;font-weight:bold;'>{label}</div>",
                unsafe_allow_html=True
            )
        else:
            if st.button(label, use_container_width=True, key=f"nav_{nome}"):
                st.session_state.pagina_menu = nome
                if nome == "Base de Imóveis":
                    st.session_state.pagina_atual = 0
                st.rerun()

    st.markdown("---")
    total_banco = contar_registros()
    if total_banco > 0:
        formatted = f"{total_banco:,}".replace(",", ".")
        st.markdown(
            f"<div style='background:#27ae60;border-radius:6px;padding:8px 12px;"
            f"text-align:center;font-size:0.85rem;'>✅ {formatted} imóveis</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            "<div style='background:#c0392b;border-radius:6px;padding:8px 12px;"
            "text-align:center;font-size:0.85rem;'>⚠️ Banco vazio</div>",
            unsafe_allow_html=True
        )

# ── Roteamento ─────────────────────────────────────────────────────────────
pagina = st.session_state.pagina_menu

if pagina == "Dashboard":
    from dashboard import render_dashboard
    render_dashboard()

elif pagina == "Base de Imóveis":
    from busca import render_pagina_busca
    render_pagina_busca()

elif pagina == "Detalhes do Imóvel":
    from busca import render_detalhe_imovel
    render_detalhe_imovel()

elif pagina == "Relatórios":
    from relatorios import render_pagina_relatorios
    render_pagina_relatorios()

elif pagina == "Importar Planilha":
    from importador_excel import importar_excel, detectar_colunas_excel, gerar_planilha_modelo
    from database import historico_importacoes

    st.title("📂 Importar Planilha Excel")
    st.markdown("Importe sua planilha de imóveis públicos para o sistema.")
    st.markdown("---")

    with st.expander("📋 Baixar planilha modelo (opcional)"):
        st.markdown("Baixe um modelo com as colunas corretas para preencher:")
        modelo_df = gerar_planilha_modelo()
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            modelo_df.to_excel(writer, index=False, sheet_name="Imóveis")
        st.download_button(
            "📥 Baixar Modelo",
            data=buf.getvalue(),
            file_name="modelo_imoveis_publicos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.markdown("### 1️⃣ Selecione o arquivo Excel")
    arquivo = st.file_uploader(
        "Arraste ou clique para selecionar",
        type=["xlsx", "xls"],
        help="Formatos: .xlsx ou .xls"
    )

    if arquivo is not None:
        arquivo.seek(0)
        colunas = detectar_colunas_excel(arquivo)
        if colunas:
            with st.expander(f"🔍 Colunas detectadas no arquivo ({len(colunas)})"):
                st.write(colunas)

        st.markdown("### 2️⃣ Modo de importação")
        modo = st.radio(
            "Como deseja importar?",
            options=["atualizar", "substituir"],
            format_func=lambda x: (
                "🔄 Atualizar — mantém dados existentes e adiciona/atualiza por RIP"
                if x == "atualizar"
                else "🗑️ Substituir — apaga tudo e reimporta do zero"
            )
        )

        if modo == "substituir":
            st.warning("⚠️ Esta opção apagará TODOS os dados existentes!")

        st.markdown("### 3️⃣ Confirmar importação")
        if st.button("📥 Iniciar Importação", type="primary", use_container_width=True):
            with st.spinner("⏳ Importando planilha... Aguarde..."):
                arquivo.seek(0)
                resultado = importar_excel(arquivo, arquivo.name, modo=modo)

            if resultado["sucesso"]:
                st.success(resultado["mensagem"])
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("📊 Lidos", resultado["total_lidos"])
                c2.metric("✅ Novos", resultado["novos_registros"])
                c3.metric("🔄 Atualizados", resultado["atualizados"])
                c4.metric("⚠️ Ignorados", resultado["ignorados"])
                st.balloons()
                st.info("Acesse **Base de Imóveis** no menu para consultar os dados.")
            else:
                st.error(resultado["mensagem"])
                if resultado.get("erros"):
                    with st.expander("Detalhes dos erros"):
                        for e in resultado["erros"][:10]:
                            st.code(e)

    st.markdown("---")
    st.markdown("### 📜 Histórico de Importações")
    hist = historico_importacoes()
    if not hist.empty:
        hist.columns = ["ID", "Arquivo", "Data", "Total", "Novos"]
        st.dataframe(hist, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma importação realizada ainda.")
