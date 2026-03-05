"""
utils.py - Funções utilitárias
"""

import pandas as pd


def formatar_moeda(valor):
    """Formata um valor como moeda brasileira."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return "—"
    try:
        valor = float(valor)
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "—"


def formatar_area(valor):
    """Formata uma área em m²."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return "—"
    try:
        valor = float(valor)
        return f"{valor:,.2f} m²".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "—"


def formatar_numero(valor):
    """Formata um número inteiro com separador de milhar."""
    try:
        return f"{int(valor):,}".replace(",", ".")
    except (ValueError, TypeError):
        return str(valor)


def limpar_texto(texto):
    """Remove espaços extras e normaliza texto."""
    if texto is None:
        return ""
    return str(texto).strip()


def sigla_estado_valida(sigla):
    """Verifica se uma sigla de estado é válida."""
    estados_validos = {
        'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO',
        'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI',
        'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
    }
    return str(sigla).upper().strip() in estados_validos


def truncar_texto(texto, max_chars=50):
    """Trunca um texto longo com reticências."""
    if not texto:
        return ""
    texto = str(texto)
    if len(texto) > max_chars:
        return texto[:max_chars] + "..."
    return texto
