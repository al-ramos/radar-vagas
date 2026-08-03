CREATE TABLE IF NOT EXISTS raw_fetch (
  id INTEGER PRIMARY KEY,
  fonte TEXT NOT NULL,
  url TEXT NOT NULL,
  coletado_em TEXT NOT NULL,
  status INTEGER,
  hash TEXT,
  corpo TEXT
);

CREATE TABLE IF NOT EXISTS job (
  id INTEGER PRIMARY KEY,
  chave TEXT UNIQUE NOT NULL,
  empresa TEXT NOT NULL,
  titulo TEXT NOT NULL,
  senioridade TEXT,
  modalidade TEXT,
  local TEXT,
  stack TEXT,
  publicado_em TEXT,
  url TEXT,
  descricao TEXT,
  pontos REAL,
  primeira_vez TEXT NOT NULL,
  ultima_vez TEXT NOT NULL,
  ativo INTEGER DEFAULT 1,
  avisado INTEGER DEFAULT 0,
  lida INTEGER DEFAULT 0,
  status_usuario TEXT DEFAULT '',
  status_atualizado_em TEXT,
  usuario_email TEXT
);

CREATE TABLE IF NOT EXISTS job_event (
  id INTEGER PRIMARY KEY,
  job_id INTEGER NOT NULL REFERENCES job(id),
  tipo TEXT NOT NULL,
  ocorrido_em TEXT NOT NULL,
  detalhe TEXT
);

CREATE TABLE IF NOT EXISTS perfil (
  usuario_email TEXT PRIMARY KEY,
  stacks TEXT,
  atualizado_em TEXT
);

CREATE TABLE IF NOT EXISTS usuario_conta (
  usuario TEXT PRIMARY KEY,
  senha_hash TEXT NOT NULL,
  criado_em TEXT
);

CREATE INDEX IF NOT EXISTS ix_job_empresa ON job(empresa, publicado_em);
CREATE INDEX IF NOT EXISTS ix_job_ativo ON job(ativo, pontos);
CREATE INDEX IF NOT EXISTS ix_event_job ON job_event(job_id, ocorrido_em);
