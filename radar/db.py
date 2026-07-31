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
    def __init__(self, cursor):
        self._cursor = cursor
        self.lastrowid = getattr(cursor, "lastrowid", None)

    def fetchone(self):
        row = self._cursor.fetchone()
        return tuple(row) if row is not None else None

    def fetchall(self):
        rows = self._cursor.fetchall()
        return [tuple(r) for r in rows]


class _ConexaoLibsql:
    def __init__(self, url, token):
        import libsql_experimental as libsql
        self._conn = libsql.connect(database=url, auth_token=token)

    def execute(self, sql, params=()):
        result = self._conn.execute(sql, tuple(params) if params else ())
        return _CursorLibsql(result)

    def executemany(self, sql, seq_params):
        for params in seq_params:
            self._conn.execute(sql, tuple(params))

    def executescript(self, script):
        for stmt in [s.strip() for s in script.split(";") if s.strip()]:
            self._conn.execute(stmt)

    def commit(self):
        pass

    def close(self):
        pass


def conectar():
    url = os.environ.get("TURSO_DATABASE_URL", "")
    if url:
        token = os.environ.get("TURSO_AUTH_TOKEN", "")
        return _ConexaoLibsql(url, token)
    os.makedirs(os.path.dirname(DB_LOCAL), exist_ok=True)
    return sqlite3.connect(DB_LOCAL)
