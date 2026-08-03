"""Pontuacao deterministica de 0 a 100, explicavel componente por componente."""
import datetime as dt
import os
import re

import perfil_remoto

import db

AQUI = os.path.dirname(os.path.abspath(__file__))

P = perfil_remoto.carregar()

NIVEIS = {"estagio": 0, "junior": 1, "pleno": 2, "senior": 3, "especialista": 4}


def achados(texto, termos):
    t = (texto or "").lower()
    return [x for x in (termos or []) if re.search(re.escape(x.lower()), t)]


def pontuar(titulo, descricao, senior, modal, local, publicado_em):
    texto = f"{titulo} {descricao}"
    veto = achados(texto, P.get("evitar"))
    if veto:
        return 0.0, [f"descartada: {', '.join(veto)}"]

    motivos = []
    total = 0.0

    dom = achados(texto, P.get("domino"))
    p1 = 35 * min(1.0, len(dom) / 4.0)
    motivos.append(f"stack que domino: {', '.join(dom) or 'nenhuma'} ({p1:.0f}/35)")
    total += p1

    q = achados(texto, P.get("quero"))
    p2 = 25 * min(1.0, len(q) / 2.0)
    motivos.append(f"area desejada: {', '.join(q) or 'nenhuma'} ({p2:.0f}/25)")
    total += p2

    if senior == "nao_informado":
        p3 = 8
    else:
        dist = abs(NIVEIS.get(P.get("senioridade"), 2) - NIVEIS.get(senior, 2))
        p3 = [15, 9, 3, 0, 0][min(dist, 4)]
    motivos.append(f"senioridade {senior} ({p3}/15)")
    total += p3

    if modal == P.get("modalidade_preferida"):
        p4 = 15
    elif modal == "hibrido":
        p4 = 7
    else:
        p4 = 0
    if any(c.lower() in (local or "").lower() for c in P.get("cidades") or []):
        p4 = max(p4, 10)
    motivos.append(f"modalidade {modal} / local {local or '-'} ({p4}/15)")
    total += p4

    try:
        dias = (dt.date.today() - dt.date.fromisoformat(publicado_em)).days
    except Exception:
        dias = 30
    if dias <= 3:
        p5 = 10
    elif dias <= 7:
        p5 = 7
    elif dias <= 21:
        p5 = 4
    else:
        p5 = 0
    motivos.append(f"publicada ha {dias} dias ({p5}/10)")
    total += p5

    return round(total, 1), motivos


def main():
    con = db.conectar()
    linhas = con.execute(
        "SELECT id, titulo, descricao, senioridade, modalidade, local, publicado_em"
        " FROM job WHERE ativo = 1"
    ).fetchall()
    for jid, tit, desc, sen, mod, loc, pub in linhas:
        pts, _ = pontuar(tit, desc or "", sen, mod, loc, pub)
        dom = ", ".join(achados(f"{tit} {desc}", P.get("domino")))
        con.execute("UPDATE job SET pontos = ?, stack = ? WHERE id = ?", (pts, dom, jid))
    con.commit()
    print(f"pontuadas: {len(linhas)}")


if __name__ == "__main__":
    main()
