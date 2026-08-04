# radar-vagas

Coletor de vagas de TI que monitora o ATS de empresas-alvo, normaliza, deduplica,
pontua por afinidade com o seu perfil e avisa no WhatsApp. Usa GitHub Actions
como agendador e persiste os dados no Turso ou em SQLite local.

## Setup

1. Crie o repositorio no GitHub. Prefira **privado** se nao quiser expor as
   configuracoes das fontes e do perfil; o painel do GitHub Pages sera publico.
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
4. Para usar o Turso, crie tambem os segredos `TURSO_DATABASE_URL` e
   `TURSO_AUTH_TOKEN`. Sem eles, a execucao local usa `data/radar.db`.
5. Em **Variables**, crie `RADAR_PERFIL_EMAIL` com o e-mail usado para salvar
   seu perfil no painel. Se a variavel estiver ausente ou o perfil remoto nao
   existir, o radar usa `radar/profile.yml` como fallback.
6. Edite `radar/sources.yml` (empresas-alvo) e `radar/profile.yml` (perfil de
   fallback).
7. Teste local antes de agendar:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
mkdir -p data
python radar/collect.py
python radar/score.py
WHATSAPP_TOKEN=xxx WHATSAPP_PHONE_ID=yyy WHATSAPP_TO=55DDNNNNNNNNN python radar/notify.py
```

8. Faca push. O workflow roda em dias uteis as 08h de Brasilia, e tambem
   manualmente pela aba Actions (`workflow_dispatch`).

## Descoberta automatica de empresas (recomendado para escalar)

Em vez de adivinhar slug por slug, `radar/discover.py` testa uma lista de
nomes contra os tres ATS suportados (Greenhouse, Lever, Ashby) e so grava
no arquivo de saida quem responder de verdade - nada de "pendente" chutado.

```bash
pip install -r requirements.txt
python radar/discover.py --in radar/candidatos.txt --out radar/sources.discovered.yml
```

Isso demora (uma pausa de 0.3s por tentativa, varias tentativas por nome) -
para 320 nomes, espere ~15-25 minutos. No final voce tem:

- `sources.discovered.yml` - so as empresas confirmadas, com tipo e slug reais.
- No terminal, a lista de nomes que nao bateram em nenhum ATS suportado
  (normalmente porque usam Workday, SuccessFactors ou pagina propria com
  JSON-LD - adicione essas manualmente como `tipo: jsonld` se souber a URL).

Revise o resultado e mescle com `radar/sources.yml` manualmente, ou rode com
`--out radar/sources.yml` direto (sobrescreve) quando confiar no processo.

Edite `radar/candidatos.txt` para adicionar mais nomes (uma empresa por
linha) e rode de novo - o script e idempotente, so soma o que existir.

## Como descobrir o ATS de uma empresa manualmente

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
- `radar/db.py` — usa Turso/libSQL quando configurado e SQLite local como fallback
- `data/radar.db` — banco SQLite para execucao local

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

## Painel publico (GitHub Pages)

O repositorio ja inclui `docs/index.html` - um painel estatico (sem
dependencias externas) que le `docs/jobs.json`, gerado automaticamente pelo
workflow a cada coleta.

Para ativar o endereco publico:

1. No GitHub, va em **Settings > Pages**.
2. Em **Source**, escolha **Deploy from a branch**.
3. Branch: `main`, pasta: **/docs**. Salve.
4. Aguarde 1-2 minutos. O endereco fica em
   `https://SEU-USUARIO.github.io/radar-vagas/` (aparece na mesma tela).

**Atencao — mesmo com o repositorio privado, o site do GitHub Pages pode ser
publico** (qualquer um com o link acessa), dependendo do plano e da configuracao
da conta. Como o painel mostra apenas titulo, empresa, local e link da
vaga (nada sensivel do seu perfil), isso costuma ser aceitavel - mas se
preferir manter tudo privado, nao ative o Pages e continue usando o arquivo
`Painel do Radar de Vagas.dc.html` localmente, abrindo `data/jobs.json` na
maquina.

O `docs/jobs.json` e sobrescrito a cada rodada do workflow, sempre com as
vagas ativas no momento da coleta.

## Limites e proximos passos

- **Actions**: 2.000 min/mes em repo privado; uma rodada leva ~2 min.
- **Persistencia**: SQLite atende ao uso local; para automacao e crescimento,
  use o Turso configurado pelos segredos do GitHub Actions.
- **Sem semantica**: vaga com vocabulario fora do dicionario passa batido.
  Proximo upgrade gratuito: embeddings locais via Ollama no runner.
- **Sem interface**: use Datasette local, ou exporte JSON para GitHub Pages.

## Regras de coleta

Somente fontes que publicam dado de proposito (API publica, JSON-LD, feed).
Respeite `robots.txt` e limite de taxa, identifique-se no `User-Agent` (ajuste
o e-mail em `collect.py`) e nao redistribua as descricoes coletadas.
