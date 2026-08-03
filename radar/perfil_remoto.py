"""Carrega o perfil parametrizado pelo usuario no painel (tabela `perfil`,
coluna config_json no Turso) - unica fonte de perfil usada por score.py e
notify.py. Nao ha mais fallback pro profile.yml: se o perfil nao estiver
configurado, a execucao falha com erro claro.

Exige a variavel de ambiente RADAR_PERFIL_EMAIL com o e-mail da conta usada
para logar no painel e salvar "Meu perfil".
"""
import json
import os

import db


def _dividir(txt):
    return [s.strip().lower() for s in (txt or "").split(",") if s.strip()]


def carregar():
    email = os.environ.get("RADAR_PERFIL_EMAIL", "").strip()
    if not email:
        raise SystemExit(
            "RADAR_PERFIL_EMAIL nao configurado. Defina esse secret com o "
            "e-mail da conta usada para logar no painel e salvar 'Meu perfil' "
            "antes de rodar score.py/notify.py."
        )
    con = db.conectar()
    linha = con.execute(
        "SELECT config_json FROM perfil WHERE usuario_email = ?", (email,)
    ).fetchone()
    if not linha or not linha[0]:
        raise SystemExit(
            f"Nenhum perfil salvo no banco para '{email}'. Entre no painel com "
            "essa conta, abra 'Meu perfil' e clique em Salvar antes de rodar "
            "score.py/notify.py."
        )
    cfg = json.loads(linha[0])
    return {
        "senioridade": cfg.get("senioridade") or "",
        "modalidade_preferida": cfg.get("modalidade") or "",
        "cidades": _dividir(cfg.get("cidades")),
        "corte": cfg.get("corte") or 55,
        "domino": _dividir(cfg.get("stacks")),
        "quero": _dividir(cfg.get("quero")),
        "evitar": _dividir(cfg.get("evitar")),
    }
