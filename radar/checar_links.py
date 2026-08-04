"""Marca vagas cujo link ja nao existe mais no ATS da empresa.

Roda no GitHub Actions (servidor, sem CORS): faz um HEAD/GET leve em cada
vaga ativa, em paralelo, e grava job.link_morto = 1 quando o ATS responde
404/410 ou redireciona para uma pagina generica de "vaga encerrada".

Uso: python radar/checar_links.py [--limite 200] [--workers 20]
"""
import argparse
import datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

import db

TIMEOUT = 6
CABECALHOS = {"User-Agent": "radar-vagas/1.0 (+github actions)"}
MORTOS = {404, 410}
PISTAS_ENCERRADA = (
    "no longer accepting",
    "position has been filled",
    "vaga encerrada",
    "nao esta mais disponivel",
    "job is no longer",
    "posting is closed",
)


def esta_morto(url):
    """Retorna (morto: bool, motivo: str)."""
    try:
        r = requests.head(url, headers=CABECALHOS, timeout=TIMEOUT, allow_redirects=True)
        if r.status_code in MORTOS:
            return True, f"HTTP {r.status_code}"
        if r.status_code == 405 or r.status_code >= 500:
            r = requests.get(url, headers=CABECALHOS, timeout=TIMEOUT, allow_redirects=True)
            if r.status_code in MORTOS:
                return True, f"HTTP {r.status_code}"
        if r.status_code == 200 and r.request.method == "GET":
            corpo = (r.text or "").lower()
            for pista in PISTAS_ENCERRADA:
                if pista in corpo:
                    return True, f"texto: {pista}"
        return False, ""
    except requests.RequestException as e:
        # Falha de rede nao e prova de vaga encerrada - nao marca.
        return False, f"erro: {type(e).__name__}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limite", type=int, default=200)
    ap.add_argument("--workers", type=int, default=20)
    args = ap.parse_args()

    con = db.conectar()
    linhas = con.execute(
        "SELECT id, url FROM job WHERE ativo = 1 AND url IS NOT NULL AND url != ''"
        " AND COALESCE(link_morto, 0) = 0 ORDER BY ultima_vez DESC LIMIT ?",
        (args.limite,),
    ).fetchall()

    agora = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    mortos = 0
    resultados = {}
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futuros = {ex.submit(esta_morto, url): (jid, url) for jid, url in linhas}
        for fut in as_completed(futuros, timeout=None):
            jid, url = futuros[fut]
            try:
                resultados[jid] = fut.result()
            except Exception as e:
                resultados[jid] = (False, f"erro: {type(e).__name__}")

    for jid, url in linhas:
        morto, motivo = resultados.get(jid, (False, ""))
        if morto:
            con.execute(
                "UPDATE job SET link_morto = 1, link_checado_em = ? WHERE id = ?",
                (agora, jid),
            )
            con.execute(
                "INSERT INTO job_event (job_id, tipo, ocorrido_em, detalhe)"
                " VALUES (?, 'link_morto', ?, ?)",
                (jid, agora, motivo),
            )
            mortos += 1
        else:
            con.execute("UPDATE job SET link_checado_em = ? WHERE id = ?", (agora, jid))
    con.commit()
    print(f"checadas {len(linhas)} vagas; {mortos} marcadas como encerradas")


if __name__ == "__main__":
    main()
