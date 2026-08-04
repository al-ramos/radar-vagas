"""Digest no WhatsApp (Meta Cloud API) das vagas novas acima do corte.
Silencio quando nao ha nada.

Setup (gratuito, tier de teste):
1. Crie um app em https://developers.facebook.com > tipo "Business".
2. Adicione o produto "WhatsApp" ao app - ele ja vem com um numero de teste
   e um token temporario (valido ~24h; gere um token permanente depois,
   em System Users, para nao quebrar o agendamento).
3. Em WhatsApp > API Setup, cadastre seu proprio numero como destinatario
   de teste (limite do tier gratuito: so numeros verificados recebem).
4. Guarde: WHATSAPP_TOKEN, WHATSAPP_PHONE_ID (o "Phone number ID" da Meta,
   nao o numero em si) e WHATSAPP_TO (seu numero, formato 55DDNNNNNNNNN).
"""
import os

import requests

import perfil_remoto

import db

AQUI = os.path.dirname(os.path.abspath(__file__))

P = perfil_remoto.carregar()

TOKEN = os.environ["WHATSAPP_TOKEN"]
PHONE_ID = os.environ["WHATSAPP_PHONE_ID"]
TO = os.environ["WHATSAPP_TO"]
CORTE = P.get("corte", 55)
DOMINIO = set((P.get("domino") or []))
LIMITE_MSG = 4000  # margem de seguranca abaixo do limite de 4096 da API


def bate_com_perfil(stack):
    if not DOMINIO:
        return True
    itens = {s.strip().lower() for s in (stack or "").split(",") if s.strip()}
    return bool(itens & DOMINIO)


def main():
    if P.get("_sem_perfil"):
        print("sem perfil configurado - nao envia alerta (evita spam sem base real)")
        return
    con = db.conectar()
    linhas = con.execute(
        "SELECT id, empresa, titulo, local, stack, pontos, url FROM job"
        " WHERE ativo = 1 AND avisado = 0 AND pontos >= ?"
        " ORDER BY pontos DESC LIMIT 40",
        (CORTE,),
    ).fetchall()
    linhas = [l for l in linhas if bate_com_perfil(l[4])][:12]

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
