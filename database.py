"""
database.py - Banco de dados SQLite com colunas reais da planilha
"""

import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = "imoveis.db"

# Colunas exatas como aparecem na planilha (para mapeamento)
MAPA_COLUNAS_EXCEL = {
    "TOTAL":            "total_seq",
    "N.º SUEST":        "n_suest",
    "N° SUEST":         "n_suest",
    "RIP":              "rip",
    "RIP UTILIZAÇÃO":   "rip_utilizacao",
    "valor terreno":    "valor_terreno",
    "valor benfeitoria":"valor_benfeitoria",
    "total":            "valor_total",
    "ESTADO":           "estado",
    "cod.municipio":    "cod_municipio",
    "MUNICIPIO":        "municipio",
    "ENDEREÇO":         "endereco",
    # coluna com nome longo
    "Área Terreno                    Se for o caso (Não se aplica a unidade autônoma)": "area_terreno",
    "Área Construída":  "area_construida",
    "PROPRIEDADE (Próprio/União/Terceiros)": "propriedade",
    "ocupação":         "ocupacao",
    "OBS1":             "obs1",
    "PROCESSO":         "processo",
    "OBS5":             "obs5",
}

# Colunas no banco (ordem fixa)
COLUNAS_BD = [
    "total_seq", "n_suest", "rip", "rip_utilizacao",
    "valor_terreno", "valor_benfeitoria", "valor_total",
    "estado", "cod_municipio", "municipio", "endereco",
    "area_terreno", "area_construida",
    "propriedade", "ocupacao",
    "obs1", "processo", "obs5",
]

# Rótulos legíveis para exibição
LABELS = {
    "id":               "ID",
    "total_seq":        "Nº Total",
    "n_suest":          "Nº SUEST",
    "rip":              "RIP",
    "rip_utilizacao":   "RIP Utilização",
    "valor_terreno":    "Valor Terreno",
    "valor_benfeitoria":"Valor Benfeitoria",
    "valor_total":      "Valor Total",
    "estado":           "Estado",
    "cod_municipio":    "Cód. Município",
    "municipio":        "Município",
    "endereco":         "Endereço",
    "area_terreno":     "Área Terreno",
    "area_construida":  "Área Construída",
    "propriedade":      "Propriedade",
    "ocupacao":         "Ocupação / Destinação",
    "obs1":             "OBS1 (Registro/Título)",
    "processo":         "Processo",
    "obs5":             "OBS5 (Escrituração)",
    "data_importacao":  "Data Importação",
}

# Identifica se o imóvel está cedido
TERMOS_CESSAO = ["cessão", "cessao", "cedido", "cedida", "cesso de uso", "cessão de uso"]


def get_connection():
    return sqlite3.connect(DB_PATH)


def criar_tabelas():
    conn = get_connection()
    c = conn.cursor()
    c.execute(f"""
        CREATE TABLE IF NOT EXISTS imoveis (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            total_seq        TEXT,
            n_suest          TEXT,
            rip              TEXT,
            rip_utilizacao   TEXT,
            valor_terreno    REAL,
            valor_benfeitoria REAL,
            valor_total      REAL,
            estado           TEXT,
            cod_municipio    TEXT,
            municipio        TEXT,
            endereco         TEXT,
            area_terreno     TEXT,
            area_construida  TEXT,
            propriedade      TEXT,
            ocupacao         TEXT,
            obs1             TEXT,
            processo         TEXT,
            obs5             TEXT,
            data_importacao  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS importacoes (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            arquivo          TEXT,
            data_importacao  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_registros  INTEGER,
            novos_registros  INTEGER
        )
    """)
    conn.commit()
    conn.close()


def banco_existe():
    if not Path(DB_PATH).exists():
        return False
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM imoveis")
    n = c.fetchone()[0]
    conn.close()
    return n > 0


def contar_registros():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM imoveis")
    n = c.fetchone()[0]
    conn.close()
    return n


def listar_valores_unicos(campo, estado=None):
    conn = get_connection()
    c = conn.cursor()
    if estado and estado != "Todos":
        c.execute(
            f"SELECT DISTINCT {campo} FROM imoveis WHERE estado=? AND {campo} IS NOT NULL AND TRIM({campo})!='' ORDER BY {campo}",
            [estado]
        )
    else:
        c.execute(
            f"SELECT DISTINCT {campo} FROM imoveis WHERE {campo} IS NOT NULL AND TRIM({campo})!='' ORDER BY {campo}"
        )
    vals = [r[0] for r in c.fetchall()]
    conn.close()
    return vals


def buscar_imoveis(filtros=None, busca_global="", limit=50, offset=0):
    conn = get_connection()
    where = []
    params = []

    if busca_global and busca_global.strip():
        t = f"%{busca_global.strip()}%"
        campos = ["rip", "rip_utilizacao", "municipio", "estado", "endereco",
                  "ocupacao", "obs1", "obs5", "processo", "n_suest", "propriedade"]
        where.append("(" + " OR ".join([f"UPPER({c}) LIKE UPPER(?)" for c in campos]) + ")")
        params.extend([t] * len(campos))

    if filtros:
        if filtros.get("estado") and filtros["estado"] != "Todos":
            where.append("estado = ?"); params.append(filtros["estado"])
        if filtros.get("municipio") and filtros["municipio"] != "Todos":
            where.append("municipio = ?"); params.append(filtros["municipio"])
        if filtros.get("propriedade") and filtros["propriedade"] != "Todos":
            where.append("propriedade = ?"); params.append(filtros["propriedade"])
        if filtros.get("so_cessao"):
            termos = " OR ".join([f"UPPER(ocupacao) LIKE '%{t.upper()}%'" for t in TERMOS_CESSAO])
            where.append(f"({termos})")
        if filtros.get("so_rip_util"):
            where.append("rip_utilizacao IS NOT NULL AND TRIM(rip_utilizacao) != ''")

    ws = ("WHERE " + " AND ".join(where)) if where else ""

    c = conn.cursor()
    c.execute(f"SELECT COUNT(*) FROM imoveis {ws}", params)
    total = c.fetchone()[0]

    df = pd.read_sql_query(
        f"SELECT * FROM imoveis {ws} ORDER BY id LIMIT ? OFFSET ?",
        conn, params=params + [limit, offset]
    )
    conn.close()
    return df, total


def buscar_por_id(imovel_id):
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM imoveis WHERE id=?", conn, params=[imovel_id])
    conn.close()
    return df.iloc[0].to_dict() if len(df) > 0 else None


def buscar_todos_para_dashboard():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM imoveis", conn)
    conn.close()
    return df


def buscar_para_relatorio(filtros=None, busca_global=""):
    df, _ = buscar_imoveis(filtros=filtros, busca_global=busca_global, limit=999999, offset=0)
    return df


def historico_importacoes():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM importacoes ORDER BY data_importacao DESC", conn)
    conn.close()
    return df


def eh_cessao(ocupacao_str):
    """Retorna True se a ocupação indica cessão de uso."""
    if not ocupacao_str:
        return False
    s = str(ocupacao_str).lower()
    return any(t in s for t in TERMOS_CESSAO)
