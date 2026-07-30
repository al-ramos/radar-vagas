"""Descobre automaticamente quais empresas tem board publico em cada ATS
suportado (Greenhouse, Lever, Ashby) e grava so as confirmadas em sources.yml.

Nao adivinha - testa. Cada candidato e uma tentativa real de request contra
a API publica do ATS; so entra no arquivo final quem responder com vagas
de verdade.

Uso:
    python radar/discover.py --in radar/candidatos.txt --out radar/sources.yml

candidatos.txt: um nome de empresa por linha (o nome "bonito", nao o slug).
Para cada nome o script tenta uma lista de variacoes de slug plausiveis
(minusculo, sem espaco, sem acento, com e sem sufixos comuns) contra os
tres ATS. Greenhouse e Lever tem paginas publicas sem necessidade de login;
Ashby tambem. O que nao bater em nenhum fica de fora - nao escreve "pendente"
para nao poluir com adivinhacao.
"""
import argparse
import re
import sys
import time
import unicodedata

import requests
import yaml

UA = "radar-vagas-discover/0.1 (contato: seu-email@exemplo.com)"
TIMEOUT = 12
PAUSA = 0.3  # segundos entre requests, por gentileza com os provedores


def slugifica(nome):
    """Gera variacoes plausiveis de slug a partir do nome da empresa."""
    base = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    base = base.lower().strip()
    base = re.sub(r"\(.*?\)", "", base)  # remove parenteses tipo "(Banco Inter)"
    base = re.sub(r"[^a-z0-9\s-]", "", base)
    palavras = base.split()
    if not palavras:
        return []

    junto = "".join(palavras)
    primeira = palavras[0]
    com_hifen = "-".join(palavras)

    candidatos = {junto, primeira, com_hifen}
    # remove sufixos genericos comuns (brasil, tech, group, sa, ltda...)
    genericos = {"brasil", "tech", "group", "grupo", "sa", "ltda", "inc", "corp", "solucoes"}
    sem_sufixo = [p for p in palavras if p not in genericos]
    if sem_sufixo:
        candidatos.add("".join(sem_sufixo))
        candidatos.add(sem_sufixo[0])

    return [c for c in candidatos if c and len(c) >= 3]


def testa_greenhouse(slug):
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)
    if r.status_code == 200:
        d = r.json()
        if isinstance(d.get("jobs"), list):
            return len(d["jobs"])
    return None


def testa_lever(slug):
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)
    if r.status_code == 200:
        d = r.json()
        if isinstance(d, list):
            return len(d)
    return None


def testa_ashby(slug):
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)
    if r.status_code == 200:
        d = r.json()
        jobs = d.get("jobs")
        if isinstance(jobs, list):
            return len(jobs)
    return None


TESTES = [
    ("greenhouse", testa_greenhouse),
    ("lever", testa_lever),
    ("ashby", testa_ashby),
]


def descobre(nome):
    """Tenta todas as variacoes de slug contra os tres ATS.
    Retorna (tipo, slug, n_vagas) do primeiro que bater com pelo menos 1 vaga,
    ou None se nada bateu."""
    for slug in slugifica(nome):
        for tipo, fn in TESTES:
            try:
                n = fn(slug)
            except Exception:
                n = None
            time.sleep(PAUSA)
            if n is not None and n > 0:
                return tipo, slug, n
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="entrada", required=True)
    ap.add_argument("--out", dest="saida", required=True)
    ap.add_argument("--append", action="store_true",
                     help="acrescenta ao arquivo de saida em vez de sobrescrever")
    args = ap.parse_args()

    with open(args.entrada, encoding="utf-8") as fh:
        nomes = [l.strip() for l in fh if l.strip() and not l.startswith("#")]

    confirmadas, sem_ats = [], []
    for i, nome in enumerate(nomes, 1):
        print(f"[{i}/{len(nomes)}] {nome} ...", file=sys.stderr, end=" ")
        achado = descobre(nome)
        if achado:
            tipo, slug, n = achado
            print(f"OK {tipo}:{slug} ({n} vagas)", file=sys.stderr)
            confirmadas.append({"empresa": nome, "tipo": tipo, "id": slug})
        else:
            print("sem ATS suportado", file=sys.stderr)
            sem_ats.append(nome)

    modo = "a" if args.append else "w"
    with open(args.saida, modo, encoding="utf-8") as fh:
        if not args.append:
            fh.write("# gerado por discover.py - apenas empresas com board confirmado\n\n")
        yaml.safe_dump(confirmadas, fh, allow_unicode=True, sort_keys=False)

    print(f"\nconfirmadas: {len(confirmadas)} | sem ATS suportado: {len(sem_ats)}",
          file=sys.stderr)
    if sem_ats:
        print("sem ATS suportado (Workday/SuccessFactors/JSON-LD proprio - "
              "adicione manualmente como jsonld se souber a URL):", file=sys.stderr)
        for n in sem_ats:
            print(f"  - {n}", file=sys.stderr)


if __name__ == "__main__":
    main()
