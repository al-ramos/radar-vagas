# radar-vagas

Coletor de vagas de TI que monitora o ATS de empresas-alvo, normaliza, deduplica,
pontua por afinidade com o seu perfil e avisa no Telegram. Custo zero: GitHub
Actions como agendador, SQLite versionado no proprio repositorio.

## Setup

1. Crie este repositorio como **privado** no GitHub e suba estes arquivos.
2. WhatsApp (Meta Cloud API, gratuito no tier de teste):
   - crie um app em https://developers.facebook.com, tipo "Business";
   - adicione o produto **WhatsApp** — vem com numero de teste e token
     temporario (~24h; depois gere um token permanente em *System Users*
     para o agendamento nao quebrar);
   - em *WhatsApp > API Setup*, cadastre seu proprio numero como
     destinatario de teste (o tier gratuito só envia a numeros verificados);
   - anote o **Phone number ID** (não é o número), o **token** e o **seu
     número** no formato `55DDNNNNNNNNN`.
3. Em *Settings > Secrets and variables > Actions*, crie os segredos
   `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_ID` e `WHATSAPP_TO`.
4. Edite `radar/sources.yml` (empresas-alvo) e `radar/profile.yml` (seu perfil).
5. Teste local antes de agendar:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
mkdir -p data
python radar/collect.py
python radar/score.py
WHATSAPP_TOKEN=xxx WHATSAPP_PHONE_ID=yyy WHATSAPP_TO=55DDNNNNNNNNN python radar/notify.py
```

6. Faca push. O workflow roda em dias uteis as 08h de Brasilia, e tambem
   manualmente pela aba Actions (`workflow_dispatch`).

## Como descobrir o ATS de uma empresa

Abra a pagina de carreiras e olhe o dominio:

| URL da pagina de vagas | tipo | id |
| --- | --- | --- |
| boards.greenhouse.io/**empresa** | greenhouse | empresa |
| jobs.lever.co/**empresa** | lever | empresa |
| jobs.ashbyhq.com/**empresa** | ashby | empresa |
| **empresa**.gupy.io | jsonld | URL completa da listagem |
| qualquer outro site | jsonld | URL completa da listagem |

O tipo `jsonld` funciona em qualquer pagina que publique dado estruturado
`schema.org/JobPosting` — o que cobre a maioria dos sites de vaga.

## Estrutura

- `radar/collect.py` — coleta, normaliza, deduplica, registra eventos
- `radar/score.py` — pontuacao deterministica de 0 a 100 (sem LLM, sem custo)
- `radar/notify.py` — digest no WhatsApp (Meta Cloud API) do que passou do corte
- `radar/schema.sql` — 4 tabelas: `raw_fetch`, `job`, `job_event`
- `data/radar.db` — SQLite versionado; o historico e o ativo do projeto

## Pontuacao

| Peso | Componente |
| --- | --- |
| 35 | stack da vaga que voce domina |
| 25 | area que voce quer atuar |
| 15 | proximidade de senioridade |
| 15 | modalidade e local |
| 10 | frescor da publicacao |

Termos em `evitar` zeram a nota. Calibre marcando 50 vagas manualmente como
"aplicaria / nao aplicaria" e ajuste os pesos contra esse conjunto.

## Consultas uteis

```sql
-- quem mais contrata
SELECT empresa, COUNT(*) AS vagas FROM job GROUP BY empresa ORDER BY vagas DESC;

-- vagas que ficaram muito tempo abertas (sinal de vaga fantasma ou dificil)
SELECT empresa, titulo, primeira_vez, ultima_vez,
       julianday(ultima_vez) - julianday(primeira_vez) AS dias
FROM job ORDER BY dias DESC LIMIT 20;

-- fluxo de abertura e fechamento por dia
SELECT ocorrido_em, tipo, COUNT(*) FROM job_event
GROUP BY ocorrido_em, tipo ORDER BY ocorrido_em DESC;
```

## Limites e proximos passos

- **Actions**: 2.000 min/mes em repo privado; uma rodada leva ~2 min.
- **SQLite no Git**: bom ate ~50 MB de historico; depois, Postgres gerenciado.
- **Sem semantica**: vaga com vocabulario fora do dicionario passa batido.
  Proximo upgrade gratuito: embeddings locais via Ollama no runner.
- **Sem interface**: use Datasette local, ou exporte JSON para GitHub Pages.

## Regras de coleta

Somente fontes que publicam dado de proposito (API publica, JSON-LD, feed).
Respeite `robots.txt` e limite de taxa, identifique-se no `User-Agent` (ajuste
o e-mail em `collect.py`) e nao redistribua as descricoes coletadas.
