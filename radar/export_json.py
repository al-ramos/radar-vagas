"""Exporta as vagas do banco para JSON, para visualizar num painel HTML.

Uso:
    python radar/export_json.py --out data/jobs.json --somente-ativas
"""
import argparse
import json
import os

import db

AQUI = os.path.dirname(os.path.abspath(__file__))

CAMPOS = [
    "id", "empresa", "titulo", "senioridade", "modalidade", "local",
    "stack", "publicado_em", "url", "pontos", "primeira_vez",
    "ultima_vez", "ativo", "avisado", "descricao",
    "lida", "status_usuario", "status_atualizado_em",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(AQUI, "..", "data", "jobs.json"))
    ap.add_argument("--somente-ativas", action="store_true")
    args = ap.parse_args()

    con = db.conectar()
    campos_finais = CAMPOS + ["fonte"]
    campos = ", ".join(CAMPOS) + (
        ", (SELECT detalhe FROM job_event WHERE job_id = job.id AND tipo = 'nova'"
        " ORDER BY id LIMIT 1) AS fonte"
    )
    sql = f"SELECT {campos} FROM job"
    if args.somente_ativas:
        sql += " WHERE ativo = 1"
    sql += " ORDER BY pontos DESC"

    linhas = [dict(zip(campos_finais, row)) for row in con.execute(sql).fetchall()]
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(linhas, fh, ensure_ascii=False, indent=2)

    print(f"exportadas {len(linhas)} vagas para {args.out}")


if __name__ == "__main__":
    main()
