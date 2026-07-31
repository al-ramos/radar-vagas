"""Coleta vagas dos ATS configurados, normaliza, deduplica e registra eventos."""
import datetime as dt
import hashlib
import json
import os
import re
import sys

import requests
import yaml
from selectolax.parser import HTMLParser

import db

AQUI = os.path.dirname(os.path.abspath(__file__))
UA = "radar-vagas/0.1 (contato: seu-email@exemplo.com)"
HOJE = dt.date.today().isoformat()


def get(url):
    r = requests.get(url, headers={"User-Agent": UA}, timeout=30)
    r.raise_for_status()
    return r


def limpa(html):
    if not html:
        return ""
    txt = HTMLParser(html).text(separator=" ")
    return re.sub(r"\s+", " ", txt).strip()[:6000]


# --------------------------------------------------------------- coletores
def greenhouse(ident):
    url = f"https://boards-api.greenhouse.io/v1/boards/{ident}/jobs?content=true"
    for j in get(url).json().get("jobs", []):
        yield {
            "titulo": j.get("title", ""),
            "local": (j.get("location") or {}).get("name", ""),
            "url": j.get("absolute_url", ""),
            "publicado_em": (j.get("updated_at") or "")[:10] or HOJE,
            "descricao": limpa(j.get("content", "")),
        }


def lever(ident):
    url = f"https://api.lever.co/v0/postings/{ident}?mode=json"
    for j in get(url).json():
        ts = j.get("createdAt")
        data = dt.datetime.utcfromtimestamp(ts / 1000).date().isoformat() if ts else HOJE
        yield {
            "titulo": j.get("text", ""),
            "local": (j.get("categories") or {}).get("location", ""),
            "url": j.get("hostedUrl", ""),
            "publicado_em": data,
            "descricao": limpa(j.get("descriptionPlain") or j.get("description", "")),
        }


def ashby(ident):
    url = f"https://api.ashbyhq.com/posting-api/job-board/{ident}"
    for j in get(url).json().get("jobs", []):
        yield {
            "titulo": j.get("title", ""),
            "local": j.get("location", ""),
            "url": j.get("jobUrl", ""),
            "publicado_em": (j.get("publishedAt") or "")[:10] or HOJE,
            "descricao": limpa(j.get("descriptionHtml", "")),
        }


def jsonld(url):
    """Parser universal: le schema.org/JobPosting embutido na pagina."""
    html = get(url).text
    for node in HTMLParser(html).css('script[type="application/ld+json"]'):
        try:
            data = json.loads(node.text())
        except Exception:
            continue
        for o in data if isinstance(data, list) else [data]:
            if not isinstance(o, dict) or o.get("@type") != "JobPosting":
                continue
            loc = o.get("jobLocation") or {}
            if isinstance(loc, list):
                loc = loc[0] if loc else {}
            end = loc.get("address") or {} if isinstance(loc, dict) else {}
            yield {
                "titulo": o.get("title", ""),
                "local": end.get("addressLocality", "") if isinstance(end, dict) else "",
                "url": o.get("url", url),
                "publicado_em": (o.get("datePosted") or "")[:10] or HOJE,
                "descricao": limpa(o.get("description", "")),
            }


def jsonfeed(url):
    """Feed JSON generico (ex: Apps Script publicando e-mails de vagas).
    Espera uma lista de objetos com titulo/empresa/local/url/publicado_em/descricao.
    """
    for j in get(url).json():
        yield {
            "empresa": j.get("empresa", ""),
            "titulo": j.get("titulo", ""),
            "local": j.get("local", ""),
            "url": j.get("url", ""),
            "publicado_em": (j.get("publicado_em") or "")[:10] or HOJE,
            "descricao": limpa(j.get("descricao", "")),
        }


COLETORES = {
    "greenhouse": greenhouse,
    "lever": lever,
    "ashby": ashby,
    "jsonld": jsonld,
    "jsonfeed": jsonfeed,
}


# ------------------------------------------------------------ normalizacao
def chave(empresa, titulo, local):
    titulo = titulo or ""
    local = local or ""
    t = re.sub(r"[^a-z0-9]+", "", titulo.lower())
    base = f"{empresa}|{t}|{local.lower()}"
    return hashlib.sha1(base.encode()).hexdigest()


NIVEL_TERMOS = [
    ("especialista", "especialista"),
    ("principal", "especialista"),
    ("staff", "especialista"),
    ("senior", "senior"),
    ("sênior", "senior"),
    ("pleno", "pleno"),
    ("junior", "junior"),
    ("júnior", "junior"),
    ("estag", "estagio"),
    ("trainee", "estagio"),
]


def senioridade(titulo):
    t = titulo.lower()
    for termo, nivel in NIVEL_TERMOS:
        if termo in t:
            return nivel
    if re.search(r"\bsr\b", t):
        return "senior"
    if re.search(r"\bjr\b", t):
        return "junior"
    return "nao_informado"


def modalidade(texto):
    t = texto.lower()
    if "remoto" in t or "remote" in t or "home office" in t or "anywhere" in t:
        return "remoto"
    if "hibrido" in t or "híbrido" in t or "hybrid" in t:
        return "hibrido"
    return "presencial"


def main():
    con = db.conectar()
    with open(os.path.join(AQUI, "schema.sql")) as fh:
        con.executescript(fh.read())
    with open(os.path.join(AQUI, "sources.yml")) as fh:
        fontes = yaml.safe_load(fh) or []

    # pre-carrega todas as chaves existentes numa unica consulta, em vez de
    # uma consulta de rede por vaga (essencial com um backend remoto)
    existentes = {chv: jid for jid, chv in con.execute("SELECT id, chave FROM job").fetchall()}

    novas = 0
    for f in fontes:
        fn = COLETORES.get(f.get("tipo"))
        if not fn:
            print(f"tipo desconhecido: {f}", file=sys.stderr)
            continue
        try:
            vagas = list(fn(f["id"]))
        except Exception as e:
            print(f"FALHA {f['empresa']} ({f['tipo']}): {e}", file=sys.stderr)
            continue

        corpo = json.dumps(vagas, ensure_ascii=False)
        con.execute(
            "INSERT OR IGNORE INTO raw_fetch (fonte, url, coletado_em, status, hash, corpo)"
            " VALUES (?,?,?,?,?,?)",
            (
                f["tipo"],
                str(f["id"]),
                dt.datetime.utcnow().isoformat(),
                200,
                hashlib.sha1(corpo.encode()).hexdigest(),
                corpo[:2000],
            ),
        )

        for v in vagas:
            v = {kk: (vv if vv is not None else "") for kk, vv in v.items()}
            if not v["titulo"]:
                continue
            empresa = v.get("empresa") or f["empresa"]
            k = chave(empresa, v["titulo"], v["local"])
            texto = f"{v['titulo']} {v['local']} {v['descricao']}"
            jid_existente = existentes.get(k)
            if jid_existente:
                con.execute(
                    "UPDATE job SET ultima_vez = ?, ativo = 1 WHERE id = ?",
                    (HOJE, jid_existente),
                )
                continue
            cur = con.execute(
                "INSERT OR IGNORE INTO job (chave, empresa, titulo, senioridade, modalidade,"
                " local, stack, publicado_em, url, descricao, primeira_vez, ultima_vez)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    k,
                    empresa,
                    v["titulo"],
                    senioridade(v["titulo"]),
                    modalidade(texto),
                    v["local"],
                    "",
                    v["publicado_em"],
                    v["url"],
                    v["descricao"],
                    HOJE,
                    HOJE,
                ),
            )
            con.execute(
                "INSERT OR IGNORE INTO job_event (job_id, tipo, ocorrido_em, detalhe)"
                " VALUES (?,?,?,?)",
                (cur.lastrowid, "nova", HOJE, f["tipo"]),
            )
            novas += 1
        print(f"{f['empresa']}: {len(vagas)} vagas")

    sumidas = con.execute(
        "SELECT id FROM job WHERE ativo = 1 AND ultima_vez != ?", (HOJE,)
    ).fetchall()
    for (jid,) in sumidas:
        con.execute("UPDATE job SET ativo = 0 WHERE id = ?", (jid,))
        con.execute(
            "INSERT OR IGNORE INTO job_event (job_id, tipo, ocorrido_em, detalhe)"
            " VALUES (?,?,?,?)",
            (jid, "fechada", HOJE, "ausente na coleta"),
        )

    # limpa capturas brutas antigas (raw_fetch e so auditoria, nao e lido em
    # nenhum outro lugar - mantem o banco pequeno)
    limite = HOJE
    con.execute("DELETE FROM raw_fetch WHERE coletado_em < ?", (limite,))

    con.commit()
    try:
        con.execute("VACUUM")
    except Exception:
        pass  # VACUUM pode nao ser suportado num backend remoto
    print(f"novas: {novas} | fechadas: {len(sumidas)}")


if __name__ == "__main__":
    main()
