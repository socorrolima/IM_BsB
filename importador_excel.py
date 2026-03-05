"""
importador_excel.py - Importa a planilha real para o SQLite
"""

import pandas as pd
import numpy as np
import sqlite3
import re
from database import get_connection, criar_tabelas, MAPA_COLUNAS_EXCEL, COLUNAS_BD


def _limpar_area(valor):
    """Converte área em texto variado para string padronizada."""
    if pd.isna(valor):
        return None
    s = str(valor).strip()
    if not s or s.lower() in ("nan", "none", "-", "n/a"):
        return None
    return s


def _limpar_numero(valor):
    """Converte texto com vírgula/ponto para float."""
    if pd.isna(valor):
        return None
    s = str(valor).strip().replace(" ", "")
    if not s or s.lower() in ("nan", "none", "-", "n/a", "0.0"):
        return None
    # remove R$, m², letras
    s = re.sub(r'[^\d.,]', '', s)
    # trata separador brasileiro
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
    try:
        return float(s)
    except Exception:
        return None


def _limpar_texto(valor):
    if pd.isna(valor):
        return None
    s = str(valor).strip()
    if s.lower() in ("nan", "none", ""):
        return None
    return s


def mapear_df(df):
    """Renomeia colunas do Excel para colunas do banco."""
    # Mapeamento case-insensitive + strip
    rename = {}
    for col in df.columns:
        col_strip = str(col).strip()
        # direto
        if col_strip in MAPA_COLUNAS_EXCEL:
            rename[col] = MAPA_COLUNAS_EXCEL[col_strip]
            continue
        # case-insensitive
        for k, v in MAPA_COLUNAS_EXCEL.items():
            if col_strip.upper() == k.upper():
                rename[col] = v
                break
    return df.rename(columns=rename)


def importar_excel(arquivo_bytes, nome_arquivo, modo="atualizar"):
    resultado = {
        "sucesso": False, "mensagem": "",
        "total_lidos": 0, "novos_registros": 0,
        "atualizados": 0, "ignorados": 0, "erros": []
    }

    try:
        df = pd.read_excel(arquivo_bytes, engine="openpyxl", dtype=str)
        resultado["total_lidos"] = len(df)

        if len(df) == 0:
            resultado["mensagem"] = "Planilha vazia!"
            return resultado

        # Mapeia colunas
        df = mapear_df(df)

        # Garante todas as colunas do banco
        for col in COLUNAS_BD:
            if col not in df.columns:
                df[col] = None

        df = df[COLUNAS_BD].copy()

        # Remove linhas totalmente vazias
        df = df.dropna(how="all").reset_index(drop=True)

        criar_tabelas()
        conn = get_connection()
        cursor = conn.cursor()

        if modo == "substituir":
            cursor.execute("DELETE FROM imoveis")
            conn.commit()

        # RIPs existentes
        cursor.execute("SELECT rip FROM imoveis WHERE rip IS NOT NULL")
        rips_existentes = set(r[0] for r in cursor.fetchall())

        novos = atualizados = ignorados = 0

        for _, row in df.iterrows():
            try:
                vals = {}
                for col in COLUNAS_BD:
                    v = row.get(col)
                    if col in ("valor_terreno", "valor_benfeitoria", "valor_total"):
                        vals[col] = _limpar_numero(v)
                    elif col in ("area_terreno", "area_construida"):
                        vals[col] = _limpar_area(v)
                    else:
                        vals[col] = _limpar_texto(v)

                rip = vals.get("rip")

                if modo == "atualizar" and rip and rip in rips_existentes:
                    set_clause = ", ".join([f"{c}=?" for c in COLUNAS_BD if c != "rip"])
                    v_list = [vals[c] for c in COLUNAS_BD if c != "rip"] + [rip]
                    cursor.execute(f"UPDATE imoveis SET {set_clause} WHERE rip=?", v_list)
                    atualizados += 1
                else:
                    cols = ", ".join(COLUNAS_BD)
                    ph = ", ".join(["?"] * len(COLUNAS_BD))
                    cursor.execute(f"INSERT INTO imoveis ({cols}) VALUES ({ph})",
                                   [vals[c] for c in COLUNAS_BD])
                    novos += 1
                    if rip:
                        rips_existentes.add(rip)

            except Exception as e:
                ignorados += 1
                resultado["erros"].append(str(e))

        cursor.execute(
            "INSERT INTO importacoes (arquivo, total_registros, novos_registros) VALUES (?,?,?)",
            (nome_arquivo, len(df), novos)
        )
        conn.commit()
        conn.close()

        resultado.update({
            "sucesso": True,
            "novos_registros": novos,
            "atualizados": atualizados,
            "ignorados": ignorados,
            "mensagem": f"✅ {novos} novos | {atualizados} atualizados | {ignorados} ignorados"
        })

    except Exception as e:
        resultado["mensagem"] = f"❌ Erro: {str(e)}"
        resultado["erros"].append(str(e))

    return resultado


def detectar_colunas_excel(arquivo_bytes):
    try:
        df = pd.read_excel(arquivo_bytes, engine="openpyxl", nrows=0)
        return list(df.columns)
    except Exception:
        return []
