
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
  1 as client_id,
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


INSERT INTO vendor
 (client_id,
qb_id,
name,
  active,
  created_ts,
  updated_ts)
select
  1 as client_id,
  "ID",
  "Name",
  "IsActive",
  "TimeModified"::timestamp,
  "TimeCreated"::timestamp
from vendors_temp;


INSERT INTO project_customer
 (client_id,
  qb_id,
  name,
  active,
  class_id,
  qb_parent_id,
  created_ts,
  updated_ts)
select
  1 as client_id,
  "ID",
  "FullName",
  "IsActive",
  "ClassId",
  "ParentId",
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

INSERT INTO gl_transactions (client_id, account_number,
  account_name,
  txn_type,
  date,
  month,
  fiscal_year,
  txn_number,
  ref_num,
  name,
  memo,
  split,
  amount,
  account_id,
  name_id)
select
  1 as client_id,
  account_number,
  account_name,
  type,
  date::date,
  month::date,
  fiscal_year,
  txn_number,
  ref_num,
  name,
  line_memo,
  split,
  amount,
  account_id,
  name_id
from gl_transactions_temp;
