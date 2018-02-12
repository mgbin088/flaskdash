#Custom View SQL


sql_budget_node_detail = """
    CREATE RECURSIVE VIEW budget_node_detail (client_id, id, name, ancestors, tree, depth, cycle) AS
        (SELECT client_id, id, name, '{}'::integer[] as ancestors, '{}'::text[] || name as tree, 0 as depth, FALSE as cycle
            FROM budget_node WHERE parent_id IS NULL
          UNION ALL
            SELECT
              n.client_id, n.id, n.name, t.ancestors || n.parent_id,
              t.tree || n.name,
              t.depth + 1,
              n.parent_id = ANY(t.ancestors)
            FROM budget_node n, budget_node_detail t
            WHERE n.parent_id = t.id
            AND NOT t.cycle
        )"""
        
sql_budget_heirarchy_gl = """create view budget_heirarchy_gl AS
    WITH RECURSIVE heirarchy AS -- (client_id, id, name, ancestors, tree, depth, cycle) AS (
    (SELECT client_id, id, name, '{}'::integer[] as ancestors, '{}'::text[] || name as tree, 0 as depth, FALSE as cycle
        FROM budget_node WHERE parent_id IS NULL
      UNION ALL
        SELECT
          n.client_id, n.id, n.name, t.ancestors || n.parent_id,
          t.tree || n.name,
          t.depth + 1,
          n.parent_id = ANY(t.ancestors)
        FROM budget_node n, heirarchy t
        WHERE n.parent_id = t.id
        AND NOT t.cycle
    )
    SELECT client_id, tree[1] as department, tree[2] as budget_line, a.name as gl_account
      FROM heirarchy h
      LEFT JOIN accounts a ON h.tree[3] = a.id
      WHERE depth = 2"""