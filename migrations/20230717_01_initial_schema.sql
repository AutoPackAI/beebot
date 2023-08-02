--
-- depends:

CREATE TABLE body (
  id SERIAL PRIMARY KEY,
  initial_task TEXT NOT NULL,
  current_task TEXT NOT NULL,
  state TEXT NOT NULL DEFAULT 'setup',
  packs JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE memory_chain (
  id SERIAL PRIMARY KEY,
  body_id INT REFERENCES body(id),
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE memory (
  id SERIAL PRIMARY KEY,
  memory_chain_id INT REFERENCES memory_chain(id),
  plan JSONB,
  decision JSONB,
  observation JSONB,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE document (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_document_name ON document(name);

CREATE UNIQUE INDEX idx_document_name_content ON document(name, content);

CREATE TABLE document_memory (
  id SERIAL PRIMARY KEY,
  memory_id integer NOT NULL references memory(id),
  document_id integer NOT NULL references document(id),
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);



