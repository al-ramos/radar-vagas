https://al-ramos.github.io/radar-vagas/	
RADAVAGAS

admin: usuário admin, senha RadarVagas2026! — guarde num lugar seguro (gerenciador de senhas), 
não vou repetir depois. Implementando o login local e removendo o link visível de admin:

*********************************************************************************************************************************


cp "C:\Users\al-ra\Downloads\index.html" "C:\GitHub\radar-vagas\docs\index.html"
cp "C:\Users\al-ra\Downloads\schema.sql" "C:\GitHub\radar-vagas\radar\schema.sql"
cp "C:\Users\al-ra\Downloads\migrar_status.py" "C:\GitHub\radar-vagas\radar\migrar_status.py"
cd /c/GitHub/radar-vagas
git add docs/index.html radar/schema.sql radar/migrar_status.py
git commit -m "tela de login/cadastro antes do painel"
git push
gh workflow run radar.yml

*********************************************************************************************************************************


cp "C:\Users\al-ra\Downloads\index.html" "C:\GitHub\radar-vagas\docs\index.html"
cd /c/GitHub/radar-vagas
git add docs/index.html
git commit -m "carta de apresentacao, exportar csv, diagnostico em lote, contador de uso de IA"
git push

*********************************************************************************************************************************


Senioridade: sênior
Modalidade preferida: remoto
Cidades/regiões: Remoto, Brasil, São Paulo
Corte de alerta: 55 pontos
Domina (stacks): C#, .NET, ASP.NET, React, SQL Server, Python, Docker, Kubernetes, Azure, AWS, DDD, microservices, API REST
Quer atuar em: arquitetura, plataforma, engenharia de dados, LLM, MLOps
Evitar: estágio, trainee, suporte técnico, telemarketing
Esse é o mesmo texto que dá pra colar no campo "Meu perfil (stacks que domino)" do painel (a parte de "domina"), pra persistir associado à sua conta

*********************************************************************************************************************************


Os pontos (0-100) vêm do score.py — pontuação automática de cada vaga contra seu perfil (profile.yml / o que você salvou em "Meu perfil"), somando:

35 pts — stack da vaga que você domina
25 pts — área que você quer atuar (arquitetura, plataforma, LLM etc.)
15 pts — proximidade de senioridade
15 pts — modalidade/local preferidos
10 pts — quão recente foi publicada
Termos da sua lista "evitar" (ex. "suporte técnico") zeram a nota. É por isso que uma vaga como a de suporte que você me mandou tem stack boa mas normalmente pontua baixo — o termo "suporte técnico" no perfil derruba a pontuação

*********************************************************************************************************************************


Senioridade: pleno
Modalidade: remoto
Cidades: Remoto, Brasil, São Paulo
Corte: 55
Domino (stacks): c#, .net, asp.net, react, sql server, python, docker, kubernetes, azure, aws, ddd, microservices, api rest
Quero atuar em: arquitetura, plataforma, engenharia de dados, llm, mlops
Evitar: estagio, trainee, suporte tecnico, telemarketin


*********************************************************************************************************************************



cp "C:\Users\al-ra\Downloads\index.html" "C:\GitHub\radar-vagas\docs\index.html"
cd /c/GitHub/radar-vagas
git add docs/index.html
git commit -m "abas Meu perfil / Outras / Processadas substituem o toggle antigo"
git pushs



*********************************************************************************************************************************

gh run list --workflow=radar.yml --limit 5

gh run view --log-failed --workflow=radar.yml

gh run view --log-failed

