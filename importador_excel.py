"""
importador_excel.py - Importação e processamento de planilhas Excel
"""

import pandas as pd
import sqlite3
import numpy as np
from database import (
    get_connection, criar_tabelas, MAPA_COLUNAS,
    COLUNAS_ESPERADAS
)


def normalizar_nome_coluna(nome):
    """Normaliza o nome de uma coluna para mapeamento."""
    if pd.isna(nome):
        return ""
    return str(nome).strip()


def mapear_colunas(df):
    """
    Mapeia as colunas do Excel para os nomes padronizados do banco.
    Retorna o DataFrame com colunas renomeadas.
    """
    mapa_aplicar = {}
    colunas_originais = df.columns.tolist()

    for col_original in colunas_originais:
        col_norm = normalizar_nome_coluna(col_original)
        # Tentativa direta
        if col_norm in MAPA_COLUNAS:
            mapa_aplicar[col_original] = MAPA_COLUNAS[col_norm]
            continue
        # Tentativa case-insensitive
        for chave, valor in MAPA_COLUNAS.items():
            if col_norm.upper() == chave.upper():
                mapa_aplicar[col_original] = valor
                break

    df_renomeado = df.rename(columns=mapa_aplicar)

    # Adiciona colunas faltantes como vazias
    for col in COLUNAS_ESPERADAS:
        if col not in df_renomeado.columns:
            df_renomeado[col] = None

    # Mantém apenas colunas esperadas
    colunas_existentes = [c for c in COLUNAS_ESPERADAS if c in df_renomeado.columns]
    df_final = df_renomeado[colunas_existentes].copy()

    # Garante todas as colunas esperadas
    for col in COLUNAS_ESPERADAS:
        if col not in df_final.columns:
            df_final[col] = None

    return df_final[COLUNAS_ESPERADAS]


def limpar_dados(df):
    """
    Limpa e normaliza os dados do DataFrame.
    """
    # Remove linhas completamente vazias
    df = df.dropna(how='all')

    # Normaliza colunas de texto
    colunas_texto = [
        "TOTAL", "N_SUEST", "RIP", "RIP_UTILIZACAO",
        "ESTADO", "COD_MUNICIPIO", "MUNICIPIO", "ENDERECO",
        "PROPRIEDADE", "OCUPACAO", "OBS1", "PROCESSO", "OBS5"
    ]
    for col in colunas_texto:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace(['nan', 'None', 'NaN', 'N/A', '-', ''], None)

    # Normaliza colunas numéricas
    colunas_numericas = [
        "VALOR_TERRENO", "VALOR_BENFEITORIA", "VALOR_TOTAL",
        "AREA_TERRENO", "AREA_CONSTRUIDA"
    ]
    for col in colunas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str)
                .str.replace(',', '.', regex=False)
                .str.replace(r'[^\d.]', '', regex=True),
                errors='coerce'
            )
            df[col] = df[col].replace([np.inf, -np.inf], None)

    # Remove linhas sem RIP (campo chave)
    if 'RIP' in df.columns:
        df = df[df['RIP'].notna() & (df['RIP'] != '')]

    return df.reset_index(drop=True)


def importar_excel(arquivo_bytes, nome_arquivo, modo='atualizar'):
    """
    Importa uma planilha Excel para o banco SQLite.

    Parâmetros:
        arquivo_bytes: bytes do arquivo Excel
        nome_arquivo: nome do arquivo
        modo: 'atualizar' (evita duplicatas por RIP) ou 'substituir' (limpa tudo)

    Retorna:
        dict com resultado da importação
    """
    resultado = {
        "sucesso": False,
        "mensagem": "",
        "total_lidos": 0,
        "novos_registros": 0,
        "atualizados": 0,
        "ignorados": 0,
        "erros": []
    }

    try:
        # Lê o Excel
        try:
            df = pd.read_excel(arquivo_bytes, engine='openpyxl')
        except Exception as e:
            # Tenta ler ignorando linhas de cabeçalho extras
            try:
                df = pd.read_excel(arquivo_bytes, engine='openpyxl', header=1)
            except Exception:
                resultado["mensagem"] = f"Erro ao ler arquivo Excel: {str(e)}"
                return resultado

        resultado["total_lidos"] = len(df)

        if len(df) == 0:
            resultado["mensagem"] = "Planilha vazia!"
            return resultado

        # Mapeia e limpa colunas
        df = mapear_colunas(df)
        df = limpar_dados(df)

        if len(df) == 0:
            resultado["mensagem"] = "Nenhum registro válido encontrado após limpeza."
            return resultado

        # Inicializa banco
        criar_tabelas()
        conn = get_connection()
        cursor = conn.cursor()

        if modo == 'substituir':
            cursor.execute("DELETE FROM imoveis")
            conn.commit()

        novos = 0
        atualizados = 0
        ignorados = 0

        # RIPs já existentes no banco
        cursor.execute("SELECT RIP FROM imoveis WHERE RIP IS NOT NULL")
        rips_existentes = set(row[0] for row in cursor.fetchall())

        for _, row in df.iterrows():
            rip = row.get('RIP')

            try:
                valores = {col: row.get(col) for col in COLUNAS_ESPERADAS}

                # Converte NaN para None
                for k, v in valores.items():
                    if isinstance(v, float) and np.isnan(v):
                        valores[k] = None

                if modo == 'atualizar' and rip and rip in rips_existentes:
                    # Atualiza registro existente
                    set_clause = ", ".join([f"{col} = ?" for col in COLUNAS_ESPERADAS if col != 'RIP'])
                    vals = [valores[col] for col in COLUNAS_ESPERADAS if col != 'RIP']
                    vals.append(rip)
                    cursor.execute(
                        f"UPDATE imoveis SET {set_clause} WHERE RIP = ?",
                        vals
                    )
                    atualizados += 1
                else:
                    # Insere novo registro
                    cols = ", ".join(COLUNAS_ESPERADAS)
                    placeholders = ", ".join(["?"] * len(COLUNAS_ESPERADAS))
                    vals = [valores[col] for col in COLUNAS_ESPERADAS]
                    cursor.execute(
                        f"INSERT INTO imoveis ({cols}) VALUES ({placeholders})",
                        vals
                    )
                    novos += 1
                    if rip:
                        rips_existentes.add(rip)

            except Exception as e:
                ignorados += 1
                resultado["erros"].append(str(e))

        # Registra importação no histórico
        cursor.execute(
            "INSERT INTO importacoes (arquivo, total_registros, novos_registros) VALUES (?, ?, ?)",
            (nome_arquivo, len(df), novos)
        )

        conn.commit()
        conn.close()

        resultado["sucesso"] = True
        resultado["novos_registros"] = novos
        resultado["atualizados"] = atualizados
        resultado["ignorados"] = ignorados
        resultado["mensagem"] = (
            f"✅ Importação concluída! "
            f"{novos} novos | {atualizados} atualizados | {ignorados} ignorados"
        )

    except Exception as e:
        resultado["mensagem"] = f"❌ Erro durante importação: {str(e)}"
        resultado["erros"].append(str(e))

    return resultado


def detectar_colunas_excel(arquivo_bytes):
    """
    Lê apenas o cabeçalho do Excel para mostrar colunas detectadas.
    """
    try:
        df = pd.read_excel(arquivo_bytes, engine='openpyxl', nrows=0)
        return list(df.columns)
    except Exception as e:
        return []


def gerar_planilha_modelo():
    """Gera uma planilha modelo para o usuário preencher."""
    colunas_modelo = [
        "TOTAL", "Nº SUEST", "RIP", "RIP UTILIZAÇÃO",
        "valor terreno", "valor benfeitoria", "total",
        "ESTADO", "cod.municipio", "MUNICIPIO", "ENDEREÇO",
        "Área Terreno", "Área Construída", "PROPRIEDADE",
        "ocupação", "OBS1", "PROCESSO", "OBS5"
    ]
    df_modelo = pd.DataFrame(columns=colunas_modelo)
    # Adiciona linha de exemplo
    exemplo = {
        "TOTAL": "1",
        "Nº SUEST": "SR-XX",
        "RIP": "0000.0000.000.0",
        "RIP UTILIZAÇÃO": "USO",
        "valor terreno": 100000.00,
        "valor benfeitoria": 50000.00,
        "total": 150000.00,
        "ESTADO": "SP",
        "cod.municipio": "3550308",
        "MUNICIPIO": "SÃO PAULO",
        "ENDEREÇO": "RUA EXEMPLO, 100",
        "Área Terreno": 500.00,
        "Área Construída": 200.00,
        "PROPRIEDADE": "PRÓPRIO NACIONAL",
        "ocupação": "OCUPADO",
        "OBS1": "",
        "PROCESSO": "00000.000000/0000-00",
        "OBS5": ""
    }
    df_modelo = pd.concat([df_modelo, pd.DataFrame([exemplo])], ignore_index=True)
    return df_modelo
