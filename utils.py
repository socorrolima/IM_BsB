"""utils.py"""
import pandas as pd

def fmt_moeda(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    try:
        return f"R$ {float(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")
    except Exception:
        return "—"

def fmt_numero(v):
    try:
        return f"{int(v):,}".replace(",",".")
    except Exception:
        return str(v)

def fmt_area(v):
    """Retorna área formatada — já vem como texto da planilha."""
    if not v or str(v).strip() in ("", "None", "nan"):
        return "—"
    s = str(v).strip()
    # se já tem m², retorna como está
    if "m" in s.lower():
        return s
    # tenta formatar como número
    try:
        return f"{float(s):,.2f} m²".replace(",","X").replace(".",",").replace("X",".")
    except Exception:
        return s

def badge_ocupacao(ocupacao):
    """Retorna emoji indicativo da situação."""
    if not ocupacao:
        return "❓"
    s = str(ocupacao).lower()
    if any(t in s for t in ["cessão","cessao","cedido","cedida"]):
        return "🔄 CESSÃO"
    if any(t in s for t in ["vago","sem uso","desocupado","vago"]):
        return "⬜ VAGO"
    if any(t in s for t in ["prefeitura","secretaria","municipio","municipal","ubs","posto","centro de saúde","hospital"]):
        return "✅ EM USO"
    return "📋"
