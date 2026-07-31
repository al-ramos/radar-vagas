"""Digest no WhatsApp (Meta Cloud API) das vagas novas acima do corte.
Silencio quando nao ha nada.
"""
import os
import sqlite3

import requests
import yaml

AQUI = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(AQUI, "..", "data", "radar.db")

with open(os.path.join(AQUI, "profile.yml")) as fh:
    P = yaml.safe_load(fh)

TOKEN = os.environ["WHATSAPP_TOKEN"]
PHONE_ID = os.environ["WHATSAPP_PHONE_ID"]
TO = os.environ["WHATSAPP_TO"]
CORTE = P.get("corte", 55)
LIMITE_MSG = 4000


def main():
    con = sqlite3.connect(DB)
    linhas = con.execute(
        "SELECT id, empresa, titulo, local, stack, pontos, url FROM job"
        " WHERE ativo = 1 AND avisado = 0 AND pontos >= ?"
        " ORDER BY pontos DESC LIMIT 12",
        (CORTE,),
    ).fetchall()

    if not linhas:
        print("nada a avisar")
        return

    partes = [f"*{len(linhas)} vagas novas acima de {CORTE} pontos*", ""]
    for _, empresa, titulo, local, stack, pts, url in linhas:
        partes.append(f"*{titulo}* - {empresa}")
        partes.append(f"{local or 'local nao informado'} | {pts:.0f} pts")
        if stack:
            partes.append(f"match: {stack}")
        partes.append(url)
        partes.append("")

    texto = "\n".join(partes)
    if len(texto) > LIMITE_MSG:
        texto = texto[:LIMITE_MSG] + "\n(lista cortada - veja o restante no banco)"

    r = requests.post(
        f"https://graph.facebook.com/v20.0/{PHONE_ID}/messages",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={
            "messaging_product": "whatsapp",
            "to": TO,
            "type": "text",
            "text": {"body": texto, "preview_url": False},
        },
        timeout=30,
    )
    print(f"resposta da API: {r.status_code} {r.text}")
    r.raise_for_status()

    con.executemany(
        "UPDATE job SET avisado = 1 WHERE id = ?", [(l[0],) for l in linhas]
    )
    con.commit()
    print(f"avisadas: {len(linhas)}")


if __name__ == "__main__":
    main()