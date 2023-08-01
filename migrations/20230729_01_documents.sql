-- 
-- depends: 20230720_02_body_packs

CREATE TABLE public.document (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_document_name ON public.document(name);

CREATE UNIQUE INDEX idx_document_name_content ON public.document(name, content);

CREATE TABLE public.document_memory (
  id SERIAL PRIMARY KEY,
  memory_id integer NOT NULL references memory(id),
  document_id integer NOT NULL references document(id),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);



