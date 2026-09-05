"""
collect_forecast.py

Busca sinais públicos que ajudam a prever o fluxo dos PRÓXIMOS dias em
São Lourenço, MG:
  - previsão do tempo para 14 dias (Open-Meteo, gratuita, sem chave)
  - feriados nacionais do Brasil (BrasilAPI, gratuita, sem chave)

Gera forecast.json, que o painel combina com o histórico de índice de
busca (trends.json) para sugerir se um dia futuro tende a ter mais ou
menos fluxo.

NÃO inclui feriados municipais, eventos locais (festas, Festival de
Inverno etc.) ou férias escolares — não existe fonte pública confiável
e automatizável para isso numa cidade pequena. Cadastre esses direto
no painel, na aba "Previsão" (ficam salvos por lá, sem precisar mexer
neste script).

Requisitos: pip install requests
Uso: python collect_forecast.py
"""
import json
import os
from datetime import datetime, timezone

import requests

LAT, LON = -22.1167, -45.0500  # São Lourenço, MG (aproximado)
FORECAST_DAYS = 14
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "forecast.json")

WEATHER_CODES = {
    0: "céu limpo", 1: "poucas nuvens", 2: "parcialmente nublado", 3: "nublado",
    45: "neblina", 48: "neblina com geada", 51: "garoa fraca", 53: "garoa",
    55: "garoa forte", 61: "chuva fraca", 63: "chuva", 65: "chuva forte",
    71: "neve fraca", 80: "pancadas fracas", 81: "pancadas de chuva",
    82: "pancadas fortes", 95: "trovoadas",
}


def fetch_weather():
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={LAT}&longitude={LON}"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_mean,weathercode"
        "&timezone=America%2FSao_Paulo"
        f"&forecast_days={FORECAST_DAYS}"
    )
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    d = r.json()["daily"]
    dias = []
    for i, data in enumerate(d["time"]):
        dias.append({
            "data": data,
            "tmax": d["temperature_2m_max"][i],
            "tmin": d["temperature_2m_min"][i],
            "prob_chuva": d["precipitation_probability_mean"][i],
            "condicao": WEATHER_CODES.get(d["weathercode"][i], "—"),
        })
    return dias


def fetch_feriados_nacionais(anos):
    feriados = []
    for ano in anos:
        try:
            r = requests.get(f"https://brasilapi.com.br/api/feriados/v1/{ano}", timeout=30)
            r.raise_for_status()
            for f in r.json():
                feriados.append({"data": f["date"], "nome": f["name"]})
        except Exception as e:
            print(f"Aviso: não consegui buscar feriados de {ano}: {e}")
    return feriados


def main():
    dias = fetch_weather()
    if not dias:
        print("Open-Meteo não retornou dados de previsão.")
        return

    anos = sorted({int(d["data"][:4]) for d in dias})
    feriados = fetch_feriados_nacionais(anos)

    payload = {
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "lat": LAT, "lon": LON,
        "dias": dias,
        "feriados_nacionais": feriados,
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"forecast.json atualizado: previsão para {len(dias)} dias, {len(feriados)} feriados nacionais no período.")


if __name__ == "__main__":
    main()
