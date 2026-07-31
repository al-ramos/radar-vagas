import libsql_client, os

url = "https://radar-vagas-al-ramos.aws-us-east-1.turso.io"
token = input("Cole o token: ").strip()

client = libsql_client.create_client_sync(url=url, auth_token=token)

with open("radar/schema.sql") as f:
    script = f.read()

statements = [s.strip() for s in script.split(";") if s.strip()]
print(f"Total de statements: {len(statements)}\n")

for i, stmt in enumerate(statements):
    try:
        client.execute(stmt)
        print(f"[{i}] OK: {stmt[:50]}...")
    except Exception as e:
        print(f"[{i}] FALHOU: {stmt[:80]}")
        print(f"    ERRO: {e}\n")

client.close()
