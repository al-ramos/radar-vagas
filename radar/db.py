"""Camada de conexao: usa Turso (libsql) se TURSO_DATABASE_URL estiver
definido; caso contrario cai para o arquivo sqlite local (uso manual/local).
Expoe uma API minima parecida com sqlite3 para nao precisar mudar as
queries dos outros scripts (collect.py, score.py, notify.py, export_json.py).
"""
import os
import sqlite3

AQUI = os.path.dirname(os.path.abspath(__file__))
DB_LOCAL = os.path.join(AQUI, "..", "data", "radar.db")


class _CursorLibsql:
    def __init__(self, result_set):
        self._rows = [tuple(r) for r in (result_set.rows or [])]
        self._i = 0
        self.lastrowid = getattr(result_set, "last_insert_rowid", None)

    def fetchone(self):
        if self._i >= len(self._rows):
            return None
        row = self._rows[self._i]
        self._i += 1
        return row

    def fetchall(self):
        rows = self._rows[self._i:]
        self._i = len(self._rows)
        return rows


class _ConexaoLibsql:
    def __init__(self, url, token):
        import libsql_client
        self._client = libsql_client.create_client_sync(url=url, auth_token=token)

    def execute(self, sql, params=()):
        return _CursorLibsql(self._client.execute(sql, list(params) if params else []))

    def executemany(self, sql, seq_params):
        for params in seq_params:
            self._client.execute(sql, list(params))

    def executescript(self, script):
        for stmt in [s.strip() for s in script.split(";") if s.strip()]:
            self._client.execute(stmt)

    def commit(self):
        pass  # cada execute() no Turso ja e confirmado na hora

    def close(self):
        self._client.close()


def conectar():
    url = os.environ.get("TURSO_DATABASE_URL")
    if url:
        token = os.environ.get("TURSO_AUTH_TOKEN", "")
        # forca HTTP em vez do protocolo websocket (mais confiavel em runners
        # como o do GitHub Actions, onde o handshake ws as vezes falha)
        if url.startswith("libsql://"):
            url = "https://" + url[len("libsql://"):]
        return _ConexaoLibsql(url, token)
    os.makedirs(os.path.dirname(DB_LOCAL), exist_ok=True)
    return sqlite3.connect(DB_LOCAL)
