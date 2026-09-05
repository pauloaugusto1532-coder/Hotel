"""
collect_trends.py

Coleta diária do índice de interesse de busca (Google Trends) para termos
turísticos ligados a São Lourenço, MG, e atualiza um arquivo trends.json
que o painel (fluxo-turistico.jsx) carrega automaticamente via fetch().

Isto NÃO é a ocupação hoteleira real — é um proxy de demanda (quanto as
pessoas estão pesquisando sobre a cidade), usado no painel para estimar
fluxo relativo e, quando calibrado com um número oficial mensal, uma
aproximação de ocupação.

Requisitos:
    pip install pytrends pandas

Uso local:
    python collect_trends.py

Uso recomendado: 1x por dia via GitHub Actions (ver collect-trends.yml).
"""
import json
import os
from datetime import datetime, timezone

from pytrends.request import TrendReq

# Termos de busca monitorados. Ajuste livremente — quanto mais específico
# ("pousada X"), menor o volume de busca e mais ruidoso o dado.
KEYWORDS = [
    "hotel são lourenço mg",
    "pousada são lourenço mg",
    "parque das águas são lourenço",
    "são lourenço mg turismo",
]

GEO = "BR"                 # não restringe geo do pesquisador: queremos
                            # interesse pela cidade vindo de qualquer lugar
TIMEFRAME = "today 3-m"    # janela móvel de ~90 dias, granularidade diária
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trends.json")


def fetch_trends():
    pytrends = TrendReq(hl="pt-BR", tz=180)
    pytrends.build_payload(KEYWORDS, timeframe=TIMEFRAME, geo=GEO)
    df = pytrends.interest_over_time()
    if df.empty:
        return {}
    df = df.drop(columns=["isPartial"], errors="ignore")
    # índice combinado = média simples dos termos monitorados (0-100)
    df["indice"] = df[KEYWORDS].mean(axis=1).round(1)
    return {d.strftime("%Y-%m-%d"): float(v) for d, v in df["indice"].items()}


def load_existing():
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"atualizado_em": None, "keywords": KEYWORDS, "dados": {}}


def main():
    existing = load_existing()
    novos = fetch_trends()

    if not novos:
        print("Google Trends não retornou dados nesta execução (tente novamente mais tarde).")
        return

    existing["dados"].update(novos)
    existing["keywords"] = KEYWORDS
    existing["atualizado_em"] = datetime.now(timezone.utc).isoformat()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    print(f"trends.json atualizado com {len(novos)} dias. Total acumulado: {len(existing['dados'])} dias.")


if __name__ == "__main__":
    main()
