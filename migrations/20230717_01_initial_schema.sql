--
-- depends:

CREATE TABLE body (
  id SERIAL PRIMARY KEY,
  task TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE task_execution (
  id SERIAL PRIMARY KEY,
  body_id INT REFERENCES body(id),
  agent TEXT NOT NULL,
  state TEXT NOT NULL DEFAULT 'waiting',
  instructions TEXT NOT NULL,
  complete BOOLEAN NOT NULL DEFAULT FALSE,
  inputs JSONB,
  outputs JSONB,
  variables JSONB,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE oversight (
  id SERIAL PRIMARY KEY,
  original_plan_text TEXT NOT NULL,
  modified_plan_text TEXT NOT NULL,
  modifications JSONB,
  llm_response TEXT,
  prompt_variables JSONB,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE decision (
  id SERIAL PRIMARY KEY,
  tool_name TEXT NOT NULL,
  tool_args JSONB,
  prompt_variables JSONB,
  llm_response TEXT,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE observation (
  id SERIAL PRIMARY KEY,
  response TEXT,
  error_reason TEXT,
  success BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE plan (
  id SERIAL PRIMARY KEY,
  plan_text TEXT NOT NULL,
  prompt_variables JSONB,
  llm_response TEXT,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE step (
  id SERIAL PRIMARY KEY,
  task_execution_id INT REFERENCES task_execution(id),
  plan_id INT REFERENCES plan(id),
  oversight_id INT REFERENCES oversight(id),
  decision_id INT REFERENCES decision(id),
  observation_id INT REFERENCES observation(id),
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

CREATE TABLE document_step (
  id SERIAL PRIMARY KEY,
  step_id integer NOT NULL references step(id),
  document_id integer NOT NULL references document(id),
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
