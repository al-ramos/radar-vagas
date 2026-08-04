"""Carrega o perfil salvo no painel e usa profile.yml como fallback.

O perfil remoto no Turso tem prioridade quando RADAR_PERFIL_EMAIL esta
configurado. Se a variavel, a tabela ou o registro nao existirem, score.py e
notify.py continuam funcionando com radar/profile.yml.
"""
import json
import os

import yaml

import db

AQUI = os.path.dirname(os.path.abspath(__file__))
PERFIL_LOCAL = os.path.join(AQUI, "profile.yml")

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


def _lista(valor):
    if isinstance(valor, list):
        return [str(s).strip().lower() for s in valor if str(s).strip()]
    return [s.strip().lower() for s in (valor or "").split(",") if s.strip()]


def _normalizar(cfg, remoto=False):
    return {
        "senioridade": cfg.get("senioridade") or "pleno",
        "modalidade_preferida": (
            cfg.get("modalidade") if remoto else cfg.get("modalidade_preferida")
        ) or "remoto",
        "cidades": _lista(cfg.get("cidades")),
        "corte": cfg.get("corte") or 55,
        "domino": _lista(cfg.get("stacks") if remoto else cfg.get("domino")),
        "quero": _lista(cfg.get("quero")),
        "evitar": _lista(cfg.get("evitar")),
        "_sem_perfil": False,
    }


def _carregar_local():
    try:
        with open(PERFIL_LOCAL, encoding="utf-8") as arquivo:
            cfg = yaml.safe_load(arquivo) or {}
        if cfg:
            print("[perfil_remoto] usando radar/profile.yml como fallback.")
            return _normalizar(cfg)
    except (OSError, yaml.YAMLError) as erro:
        print(f"[perfil_remoto] nao foi possivel carregar profile.yml: {erro}")
    print("[perfil_remoto] nenhum perfil configurado; usando perfil neutro.")
    return dict(_PADRAO)


def carregar():
    email = os.environ.get("RADAR_PERFIL_EMAIL", "").strip()
    if not email:
        print("[perfil_remoto] RADAR_PERFIL_EMAIL nao configurado.")
        return _carregar_local()

    try:
        con = db.conectar()
        linha = con.execute(
            "SELECT config_json FROM perfil WHERE usuario_email = ?", (email,)
        ).fetchone()
    except Exception as erro:
        print(f"[perfil_remoto] perfil remoto indisponivel: {erro}")
        return _carregar_local()

    if not linha or not linha[0]:
        print(f"[perfil_remoto] nenhum perfil remoto salvo para '{email}'.")
        return _carregar_local()

    try:
        return _normalizar(json.loads(linha[0]), remoto=True)
    except (TypeError, ValueError, json.JSONDecodeError) as erro:
        print(f"[perfil_remoto] perfil remoto invalido: {erro}")
        return _carregar_local()
