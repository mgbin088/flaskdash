DROP FUNCTION IF EXISTS materialize_heirarchy_node();
CREATE OR REPLACE FUNCTION materialize_heirarchy_node()
  RETURNS trigger AS
$$
BEGIN
WITH RECURSIVE heirarchy AS -- (client_id, id, name, ancestors, tree, depth, cycle) AS (
(SELECT n.client_id, c.abbreviation as client, n.id, n.name, '{}'::integer[] as path_id, '{}'::text[] || n.name as path_name, 0 as depth, FALSE as cycle
    FROM heirarchy_node n, client c WHERE parent_id IS NULL and n.client_id = c.id
  UNION ALL
    SELECT
      n.client_id, c.abbreviation, n.id, n.name, t.path_id || n.parent_id,
      t.path_name || n.name,
      t.depth + 1,
      n.parent_id = ANY(t.path_id)
    FROM heirarchy_node n, heirarchy t, client c
    WHERE n.parent_id = t.id AND n.client_id = c.id
    AND NOT t.cycle
)
UPDATE public.heirarchy_node t
    set path_id = v.path_id,
        path_name = v.path_name,
        depth = v.depth
  from heirarchy v
  WHERE t.id =v.id;
RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER materialize_heirarchy_node_trig
  AFTER INSERT
  ON heirarchy_node
  FOR EACH STATEMENT
  EXECUTE PROCEDURE materialize_heirarchy_node();