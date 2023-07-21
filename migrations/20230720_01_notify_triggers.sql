-- Set up `NOTIFY` on changes to any of the 3 major tables. Connected clients will receive these messages.
-- depends: 20230717_01_initial_schema


CREATE OR REPLACE FUNCTION body_notify_trigger() RETURNS trigger AS $$
BEGIN
  PERFORM pg_notify('body_changes', TG_OP || ': ' || NEW::text);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER body_changes
AFTER INSERT OR UPDATE OR DELETE ON body
FOR EACH ROW EXECUTE PROCEDURE body_notify_trigger();


CREATE OR REPLACE FUNCTION memory_chain_notify_trigger() RETURNS trigger AS $$
BEGIN
  PERFORM pg_notify('memory_chain_changes', TG_OP || ': ' || NEW::text);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER memory_chain_changes
AFTER INSERT OR UPDATE OR DELETE ON memory_chain
FOR EACH ROW EXECUTE PROCEDURE memory_chain_notify_trigger();


CREATE OR REPLACE FUNCTION memory_notify_trigger() RETURNS trigger AS $$
BEGIN
  PERFORM pg_notify('memory_changes', TG_OP || ': ' || NEW::text);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER memory_changes
AFTER INSERT OR UPDATE OR DELETE ON memory
FOR EACH ROW EXECUTE PROCEDURE memory_notify_trigger();
