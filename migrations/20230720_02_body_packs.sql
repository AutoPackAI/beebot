-- 
-- depends: 20230720_01_notify_triggers


ALTER TABLE body ADD COLUMN packs text[] default '{}';