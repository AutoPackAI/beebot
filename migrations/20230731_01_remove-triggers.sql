-- remove_triggers
-- depends: 20230729_01_documents


DROP TRIGGER body_changes on body;
DROP FUNCTION body_notify_trigger;
DROP TRIGGER memory_chain_changes on memory_chain;
DROP FUNCTION memory_chain_notify_trigger;
DROP TRIGGER memory_changes on memory;
DROP FUNCTION memory_notify_trigger;
