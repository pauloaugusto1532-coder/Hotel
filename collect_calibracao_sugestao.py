"""
collect_calibracao_sugestao.py

Tenta encontrar, de forma automática, PISTAS sobre a taxa de ocupação
hoteleira mais recente divulgada publicamente — hoje, a fonte mais
regular e pública é o InFOHB, informativo mensal do Fórum de
Operadores Hoteleiros do Brasil, replicado por veículos como o
Panrotas.

IMPORTANTE — isto é uma busca de PISTA, não um número pronto para usar:
  - O InFOHB cobre hotéis de rede em grandes cidades/regiões — não é
    especificamente São Lourenço nem o Circuito das Águas.
  - Os textos publicados às vezes trazem a taxa de ocupação em valor
    absoluto (ex: "ocupação de 59,2%") e às vezes uma VARIAÇÃO
    percentual (ex: "avanço de 2,1% na taxa de ocupação") — são coisas
    diferentes, e confundir uma com a outra estragaria a calibração.

Por isso o script guarda o TRECHO de texto encontrado e o link da
fonte, e quem decide se aquilo serve como calibração é você, lendo o
trecho na aba "Calibração oficial" do painel. Nada é preenchido sozinho.

Requisitos: pip install requests beautifulsoup4
Uso: python collect_calibracao_sugestao.py
"""
import json
import os
import re
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

LISTAGEM_URL = "https://www.panrotas.com.br/tudo-sobre/infohb"
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sugestao_calibracao.json")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; FluxoSL-bot/1.0; uso pessoal, verificacao manual antes de usar)"}


def encontrar_ultimo_link():
    r = requests.get(LISTAGEM_URL, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/noticia" in href or "/hotelaria" in href:
            return href if href.startswith("http") else "https://www.panrotas.com.br" + href
    return None


def extrair_trechos(texto):
    trechos = []
    for m in re.finditer(r"[^.]{0,120}ocupa[çc][aã]o[^.]{0,120}\d{1,3}(?:,\d+)?\s?%[^.]{0,60}\.", texto, re.IGNORECASE):
        trecho = " ".join(m.group(0).split())
        if trecho not in trechos:
            trechos.append(trecho)
    return trechos[:5]


def main():
    candidatos = []
    fonte_url = None
    try:
        fonte_url = encontrar_ultimo_link()
        if fonte_url:
            r = requests.get(fonte_url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            texto = soup.get_text(" ", strip=True)
            for trecho in extrair_trechos(texto):
                candidatos.append({"fonte": "InFOHB (via Panrotas)", "url": fonte_url, "trecho": trecho})
        else:
            print("Não encontrei um link de artigo recente na listagem do Panrotas.")
    except Exception as e:
        print(f"Aviso: não consegui buscar agora: {e}")

    payload = {
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "aviso": (
            "Pistas encontradas automaticamente no InFOHB (hotéis de rede em grandes "
            "cidades — não é São Lourenço específico). Confira o trecho e a fonte antes "
            "de usar como calibração; não é um número pronto."
        ),
        "candidatos": candidatos,
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"sugestao_calibracao.json atualizado com {len(candidatos)} pista(s) de {fonte_url or 'nenhuma fonte encontrada'}.")


if __name__ == "__main__":
    main()
