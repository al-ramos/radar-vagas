"""Adiciona ao job as colunas de status do usuario (lida, status_usuario),
usadas pelo painel para marcar vaga como lida/candidatada/descartada
diretamente no banco. Rode uma vez: python radar/migrar_status.py
"""
import db

COLUNAS = [
    ("lida", "INTEGER DEFAULT 0"),
    ("status_usuario", "TEXT DEFAULT ''"),
    ("status_atualizado_em", "TEXT"),
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


if __name__ == "__main__":
    main()
