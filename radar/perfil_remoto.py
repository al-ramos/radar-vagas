"""Carrega o perfil parametrizado pelo usuario no painel (tabela `perfil`,
coluna config_json no Turso) - unica fonte de perfil usada por score.py e
notify.py.

Se o perfil nao estiver configurado, degrada com defaults neutros (nao trava
collect.py/score.py) mas marca P["_sem_perfil"] = True, para que notify.py
saiba nao mandar alerta sem perfil real.
"""
import json
import os

import db

_PADRAO = {
    "senioridade": "pleno",
    "modalidade_preferida": "remoto",
    "cidades": [],
    "corte": 55,
    "domino": [],
    "quero": [],
    "evitar": [],
    "_sem_perfil": True,
}


def _dividir(txt):
    return [s.strip().lower() for s in (txt or "").split(",") if s.strip()]


def carregar():
    email = os.environ.get("RADAR_PERFIL_EMAIL", "").strip()
    if not email:
        print("[perfil_remoto] RADAR_PERFIL_EMAIL nao configurado - usando perfil neutro (sem stacks/quero/evitar).")
        return dict(_PADRAO)
    con = db.conectar()
    linha = con.execute(
        "SELECT config_json FROM perfil WHERE usuario_email = ?", (email,)
    ).fetchone()
    if not linha or not linha[0]:
        print(f"[perfil_remoto] Nenhum perfil salvo para '{email}' - usando perfil neutro. "
              "Entre no painel e salve 'Meu perfil' para pontuacao/alerta corretos.")
        return dict(_PADRAO)
    cfg = json.loads(linha[0])
    return {
        "senioridade": cfg.get("senioridade") or "",
        "modalidade_preferida": cfg.get("modalidade") or "",
        "cidades": _dividir(cfg.get("cidades")),
        "corte": cfg.get("corte") or 55,
        "domino": _dividir(cfg.get("stacks")),
        "quero": _dividir(cfg.get("quero")),
        "evitar": _dividir(cfg.get("evitar")),
        "_sem_perfil": False,
    }
