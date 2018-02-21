
INSERT INTO chart_accounts
 (client_id,
  account_type,
  account_number,
  name,
  qb_fullname,
  description,
  active,
  qb_parent_id,
  qb_id,
  updated_ts,
  created_ts)
select
  client_id,
  account_type,
  account_number,
  account_name,
  account_full_name,
  account_description,
  is_active,
  account_parent_id,
  account_id,
  time_modified::timestamp,
  time_created::timestamp
from chart_accounts_temp;


INSERT INTO vendor_customer
 (client_id,
qb_id,
name,
  active,
  project_flag,
  created_ts,
  updated_ts)
select
  client_id,
  "ID",
  "Name",
  "IsActive",
  FALSE,
  "TimeModified"::timestamp,
  "TimeCreated"::timestamp
from vendors_temp;


INSERT INTO vendor_customer
 (client_id,
  qb_id,
  name,
  active,
  created_ts,
  updated_ts)
select
  client_id,
  "ID",
  "FullName",
  "IsActive",

  "TimeModified"::timestamp,
  "TimeCreated"::timestamp
from customers_temp;

INSERT INTO project_class
 (client_id,
  qb_id,
  name,
  active,
  qb_parent_id,
  created_ts,
  updated_ts)
select
  1 as client_id,
  "ID",
  "FullName",
  "IsActive",
  "ParentRef_ListId",
  "TimeModified"::timestamp,
  "TimeCreated"::timestamp
from classes_temp;

INSERT INTO gl_transactions (
  client_id,
  account_id,
  vendor_id,
  project_customer_id,
  project_class_id,
  --budget_node not assigned here

  txn_type,
  txn_number,
  date,
  ref_num,
  memo,
  amount
  )
select
  1 as client_id,
  a.id as account_id,
  v.id as vendor_id,
  c.id as customer_id,
  cl.id as class_id,

  gl.source as txn_type,
  gl.txn_number,
  gl.date::date,
  gl.reference_number,
  gl.line_memo as memo,
  gl.amount
from gl_detail_temp gl
  JOIN chart_accounts a ON gl.account_id = a.qb_id
  LEFT JOIN project_class cl on gl.class_id = cl.qb_id
  LEFT JOIN vendor_customer v
    ON gl.name_id = v.qb_id
  LEFT JOIN vendor_customer c
    ON gl.customer_id = c.qb_id
