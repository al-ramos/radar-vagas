"""Exporta as vagas do SQLite para JSON, para visualizar num painel HTML.

Uso:
    python radar/export_json.py --out data/jobs.json --somente-ativas
"""
import argparse
import json
import os
import sqlite3

AQUI = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(AQUI, "..", "data", "radar.db")

CAMPOS = [
    "id", "empresa", "titulo", "senioridade", "modalidade", "local",
    "stack", "publicado_em", "url", "pontos", "primeira_vez",
    "ultima_vez", "ativo", "avisado",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(AQUI, "..", "data", "jobs.json"))
    ap.add_argument("--somente-ativas", action="store_true")
    args = ap.parse_args()

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    sql = f"SELECT {', '.join(CAMPOS)} FROM job"
    if args.somente_ativas:
        sql += " WHERE ativo = 1"
    sql += " ORDER BY pontos DESC"

    linhas = [dict(r) for r in con.execute(sql).fetchall()]
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(linhas, fh, ensure_ascii=False, indent=2)

    print(f"exportadas {len(linhas)} vagas para {args.out}")


if __name__ == "__main__":
    main()
