# 🏛️ Sistema de Gestão de Imóveis Públicos

Sistema local para consulta, busca e geração de relatórios de imóveis públicos.

---

## 📋 Pré-requisitos

- Python 3.9 ou superior instalado
- Acesso ao terminal (Prompt de Comando / PowerShell no Windows)

---

## 🚀 Como instalar e rodar

### Passo 1 — Abra o terminal na pasta do projeto

**Windows:** Clique com botão direito na pasta → "Abrir no Terminal"
**Mac/Linux:** Abra o terminal e navegue até a pasta

### Passo 2 — Instale as dependências (apenas uma vez)

```bash
pip install -r requirements.txt
```

### Passo 3 — Inicie o sistema

```bash
streamlit run app.py
```

O navegador abrirá automaticamente em: **http://localhost:8501**

---

## 📌 Como usar

### 1. Importar Planilha
- Clique em **📂 Importar Planilha** no menu lateral
- Clique em "Browse files" e selecione seu arquivo Excel
- Escolha o modo de importação:
  - **Atualizar:** mantém dados existentes, adiciona novos
  - **Substituir:** apaga tudo e reimporta
- Clique em **Iniciar Importação**

### 2. Consultar Imóveis
- Clique em **🏛️ Base de Imóveis**
- Use a barra de busca para pesquisar por RIP, município, endereço, etc.
- Use os filtros laterais para refinar os resultados
- Clique em **Ver Detalhes** para ver todas as informações de um imóvel

### 3. Dashboard
- Clique em **📊 Dashboard**
- Veja gráficos automáticos por estado, município, tipo e ocupação

### 4. Gerar Relatórios
- Clique em **📄 Relatórios**
- Configure os filtros desejados
- Clique em **Aplicar Filtros**
- Exporte para **Excel** ou **CSV**

---

## 📁 Estrutura do projeto

```
imoveis_publicos/
├── app.py              # Arquivo principal (ponto de entrada)
├── database.py         # Banco de dados SQLite
├── importador_excel.py # Importação de planilhas Excel
├── busca.py            # Busca e filtros
├── dashboard.py        # Gráficos e análises
├── relatorios.py       # Exportação de relatórios
├── utils.py            # Funções auxiliares
├── requirements.txt    # Dependências Python
└── LEIA-ME.md          # Este arquivo
```

O banco de dados `imoveis.db` é criado automaticamente na mesma pasta.

---

## 🗂️ Colunas da planilha

O sistema reconhece automaticamente estas colunas:

| Nome na Planilha | Descrição |
|---|---|
| TOTAL | Número sequencial |
| Nº SUEST | Número da Superintendência |
| RIP | Registro Imobiliário do Patrimônio |
| RIP UTILIZAÇÃO | RIP de utilização |
| valor terreno | Valor do terreno |
| valor benfeitoria | Valor das benfeitorias |
| total | Valor total |
| ESTADO | Sigla do estado |
| cod.municipio | Código IBGE do município |
| MUNICIPIO | Nome do município |
| ENDEREÇO | Endereço completo |
| Área Terreno | Área do terreno em m² |
| Área Construída | Área construída em m² |
| PROPRIEDADE | Tipo de propriedade |
| ocupação | Situação de ocupação |
| OBS1 | Observação 1 |
| PROCESSO | Número do processo |
| OBS5 | Observação 5 |

---

## ❓ Perguntas frequentes

**O sistema não abre?**
→ Verifique se o Python está instalado: `python --version`
→ Reinstale as dependências: `pip install -r requirements.txt`

**Erro ao importar a planilha?**
→ Verifique se o arquivo é .xlsx ou .xls
→ Confirme que os nomes das colunas estão corretos
→ Baixe o modelo na página de importação

**Onde ficam os dados?**
→ No arquivo `imoveis.db` na mesma pasta do projeto
→ Faça backup deste arquivo regularmente

---

## 🔧 Melhorias futuras possíveis

- Exportação para PDF
- Mapa interativo com localização dos imóveis
- Autenticação de usuários
- Gráficos de evolução temporal
- Integração com APIs do governo
- Backup automático do banco de dados
- Importação de múltiplas planilhas simultaneamente
