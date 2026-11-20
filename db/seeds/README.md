# seed 数据目录

> MySQL 容器首次启动时，`/docker-entrypoint-initdb.d/` 下的 .sql 会按文件名顺序执行。
> 本目录用于放置**初始化后**需要补灌的数据（例如 ADS 快照、字典表初始行）。

★ 注意：`01_schema.sql` 目前只建表、**0 条 INSERT**，所以业务表建完即空，
  smoke_test 的 MySQL 段会报 fail。两种补法（择一）：
  1. 把 ADS 层导出的样例 CSV 前 100 行做成 `NN_seed.sql` 放这里；
  2. 或用 `scripts/restore_from_mysql.sh` 从 MySQL 反向灌回 Hive。

★ 交付包里要包含 `数据导出样例/`（每张表前 100 行），见 A09 验收清单。
