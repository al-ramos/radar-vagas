"""Adiciona ao job as colunas de status do usuario (lida, status_usuario),
usadas pelo painel para marcar vaga como lida/candidatada/descartada
diretamente no banco. Rode uma vez: python radar/migrar_status.py
"""
import db

COLUNAS = [
    ("lida", "INTEGER DEFAULT 0"),
    ("status_usuario", "TEXT DEFAULT ''"),
    ("status_atualizado_em", "TEXT"),
    ("usuario_email", "TEXT"),
]


def main():
    con = db.conectar()
    for nome, tipo in COLUNAS:
        try:
            con.execute(f"ALTER TABLE job ADD COLUMN {nome} {tipo}")
            con.commit()
            print(f"coluna {nome}: adicionada")
        except Exception as e:
            print(f"coluna {nome}: {e}")
    try:
        con.execute(
            "CREATE TABLE IF NOT EXISTS perfil ("
            " usuario_email TEXT PRIMARY KEY, stacks TEXT, atualizado_em TEXT)"
        )
        con.commit()
        print("tabela perfil: ok")
    except Exception as e:
        print(f"tabela perfil: {e}")
    try:
        con.execute(
            "CREATE TABLE IF NOT EXISTS usuario_conta ("
            " usuario TEXT PRIMARY KEY, senha_hash TEXT NOT NULL, criado_em TEXT)"
        )
        con.commit()
        print("tabela usuario_conta: ok")
    except Exception as e:
        print(f"tabela usuario_conta: {e}")


if __name__ == "__main__":
    main()
