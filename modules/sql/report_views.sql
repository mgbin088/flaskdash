
--Budget vs Actual report summary by month
--Designed to be filtered for company and node at run time
CREATE OR REPLACE VIEW v_budget_actual AS
with b as (
SELECT budget.client_id, budget.node_id AS node_id, budget.period::DATE AS period, NULL AS actual, sum(budget.value) AS budget
FROM budget
GROUP BY budget.node_id, budget.period, budget.client_id
UNION ALL
SELECT gl.client_id, a.heirarchy_node_id as node_id, date_trunc('month', gl.date)::DATE as period, sum(gl.amount) as actual, NULL
  FROM gl_transactions gl, transactions_assigned a
WHERE  gl.id = a.transaction_id
group by a.heirarchy_node_id, date_trunc('month', gl.date), gl.client_id)

SELECT b.client_id, b.node_id, period, sum(actual) as actual, sum(budget) as budget
FROM b, calendar c, heirarchy_node h
WHERE b.period = c.date_actual
  AND b.node_id = h.id
  --AND c.fiscal_year_4 = 2018
  --and b.client_id = 1
  --AND h.path_id @> ARRAY[246]
group by b.client_id, b.node_id, b.period
