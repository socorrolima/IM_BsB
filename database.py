"""
database.py - Gerenciamento do banco de dados SQLite
"""

import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = "imoveis.db"

COLUNAS_ESPERADAS = [
    "TOTAL", "N_SUEST", "RIP", "RIP_UTILIZACAO",
    "VALOR_TERRENO", "VALOR_BENFEITORIA", "VALOR_TOTAL",
    "ESTADO", "COD_MUNICIPIO", "MUNICIPIO", "ENDERECO",
    "AREA_TERRENO", "AREA_CONSTRUIDA", "PROPRIEDADE",
    "OCUPACAO", "OBS1", "PROCESSO", "OBS5"
]

MAPA_COLUNAS = {
    "TOTAL": "TOTAL",
    "Nº SUEST": "N_SUEST",
    "N° SUEST": "N_SUEST",
    "N SUEST": "N_SUEST",
    "RIP": "RIP",
    "RIP UTILIZAÇÃO": "RIP_UTILIZACAO",
    "RIP UTILIZACAO": "RIP_UTILIZACAO",
    "valor terreno": "VALOR_TERRENO",
    "VALOR TERRENO": "VALOR_TERRENO",
    "valor benfeitoria": "VALOR_BENFEITORIA",
    "VALOR BENFEITORIA": "VALOR_BENFEITORIA",
    "total": "VALOR_TOTAL",
    "TOTAL VALOR": "VALOR_TOTAL",
    "ESTADO": "ESTADO",
    "cod.municipio": "COD_MUNICIPIO",
    "COD.MUNICIPIO": "COD_MUNICIPIO",
    "COD MUNICIPIO": "COD_MUNICIPIO",
    "MUNICIPIO": "MUNICIPIO",
    "MUNICÍPIO": "MUNICIPIO",
    "ENDEREÇO": "ENDERECO",
    "ENDERECO": "ENDERECO",
    "Área Terreno": "AREA_TERRENO",
    "ÁREA TERRENO": "AREA_TERRENO",
    "AREA TERRENO": "AREA_TERRENO",
    "Área Construída": "AREA_CONSTRUIDA",
    "ÁREA CONSTRUÍDA": "AREA_CONSTRUIDA",
    "AREA CONSTRUIDA": "AREA_CONSTRUIDA",
    "PROPRIEDADE": "PROPRIEDADE",
    "ocupação": "OCUPACAO",
    "OCUPAÇÃO": "OCUPACAO",
    "OCUPACAO": "OCUPACAO",
    "OBS1": "OBS1",
    "PROCESSO": "PROCESSO",
    "OBS5": "OBS5",
}


def get_connection():
    """Retorna conexão com o banco SQLite."""
    return sqlite3.connect(DB_PATH)


def criar_tabelas():
    """Cria as tabelas necessárias no banco de dados."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS imoveis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            TOTAL TEXT,
            N_SUEST TEXT,
            RIP TEXT,
            RIP_UTILIZACAO TEXT,
            VALOR_TERRENO REAL,
            VALOR_BENFEITORIA REAL,
            VALOR_TOTAL REAL,
            ESTADO TEXT,
            COD_MUNICIPIO TEXT,
            MUNICIPIO TEXT,
            ENDERECO TEXT,
            AREA_TERRENO REAL,
            AREA_CONSTRUIDA REAL,
            PROPRIEDADE TEXT,
            OCUPACAO TEXT,
            OBS1 TEXT,
            PROCESSO TEXT,
            OBS5 TEXT,
            data_importacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS importacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            arquivo TEXT,
            data_importacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_registros INTEGER,
            novos_registros INTEGER
        )
    """)

    conn.commit()
    conn.close()


def banco_existe():
    """Verifica se o banco já tem dados."""
    if not Path(DB_PATH).exists():
        return False
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM imoveis")
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0


def contar_registros():
    """Conta total de registros no banco."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM imoveis")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def buscar_imoveis(filtros=None, busca_global="", limit=100, offset=0):
    """
    Busca imóveis com filtros e busca global.
    Retorna (DataFrame, total_count).
    """
    conn = get_connection()

    where_clauses = []
    params = []

    if busca_global and busca_global.strip():
        termo = f"%{busca_global.strip()}%"
        campos_busca = [
            "RIP", "MUNICIPIO", "ESTADO", "ENDERECO",
            "PROCESSO", "OBS1", "OBS5", "PROPRIEDADE",
            "OCUPACAO", "N_SUEST", "RIP_UTILIZACAO"
        ]
        busca_clause = " OR ".join([f"UPPER({c}) LIKE UPPER(?)" for c in campos_busca])
        where_clauses.append(f"({busca_clause})")
        params.extend([termo] * len(campos_busca))

    if filtros:
        if filtros.get("estado") and filtros["estado"] != "Todos":
            where_clauses.append("ESTADO = ?")
            params.append(filtros["estado"])

        if filtros.get("municipio") and filtros["municipio"] != "Todos":
            where_clauses.append("MUNICIPIO = ?")
            params.append(filtros["municipio"])

        if filtros.get("propriedade") and filtros["propriedade"] != "Todos":
            where_clauses.append("PROPRIEDADE = ?")
            params.append(filtros["propriedade"])

        if filtros.get("ocupacao") and filtros["ocupacao"] != "Todos":
            where_clauses.append("OCUPACAO = ?")
            params.append(filtros["ocupacao"])

        if filtros.get("valor_min") is not None:
            where_clauses.append("VALOR_TOTAL >= ?")
            params.append(filtros["valor_min"])

        if filtros.get("valor_max") is not None:
            where_clauses.append("VALOR_TOTAL <= ?")
            params.append(filtros["valor_max"])

        if filtros.get("area_min") is not None:
            where_clauses.append("AREA_TERRENO >= ?")
            params.append(filtros["area_min"])

        if filtros.get("area_max") is not None:
            where_clauses.append("AREA_TERRENO <= ?")
            params.append(filtros["area_max"])

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    count_sql = f"SELECT COUNT(*) FROM imoveis {where_sql}"
    cursor = conn.cursor()
    cursor.execute(count_sql, params)
    total = cursor.fetchone()[0]

    data_sql = f"SELECT * FROM imoveis {where_sql} LIMIT ? OFFSET ?"
    df = pd.read_sql_query(data_sql, conn, params=params + [limit, offset])

    conn.close()
    return df, total


def buscar_por_id(imovel_id):
    """Retorna um imóvel pelo ID."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM imoveis WHERE id = ?", conn, params=[imovel_id])
    conn.close()
    if len(df) > 0:
        return df.iloc[0].to_dict()
    return None


def listar_valores_unicos(campo):
    """Lista valores únicos de um campo para os filtros."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT DISTINCT {campo} FROM imoveis WHERE {campo} IS NOT NULL AND {campo} != '' ORDER BY {campo}")
    valores = [row[0] for row in cursor.fetchall()]
    conn.close()
    return valores


def buscar_todos_para_dashboard():
    """Retorna todos os dados para o dashboard."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM imoveis", conn)
    conn.close()
    return df


def buscar_com_filtros_para_relatorio(filtros=None, busca_global=""):
    """Busca todos os registros filtrados para exportação."""
    df, _ = buscar_imoveis(filtros=filtros, busca_global=busca_global, limit=999999, offset=0)
    return df


def historico_importacoes():
    """Retorna histórico de importações."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM importacoes ORDER BY data_importacao DESC", conn)
    conn.close()
    return df
