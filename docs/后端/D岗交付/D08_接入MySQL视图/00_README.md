# D08 · 接入 MySQL 视图

> 截止：11/27　|　应交文件：1（`视图接入说明.md` + 5 份 Mapper XML + 视图 SQL 作附件）　|　状态：✅ 已完成

## 这一项放什么

| 文件 | 说明 |
|---|---|
| `视图接入说明.md` | 主交付物：视图→Mapper 的对应关系、命名映射、参数落地、SQL 写法约定 |
| `03_views.sql` | 10 个视图的定义（与 B 岗 B10 的对接口） |
| `KpiMapper.xml` `ZoneMapper.xml` `ChartMapper.xml` `DictionaryMapper.xml` `SystemMapper.xml` | 5 份真 SQL，全部 `FROM v_*` |

## 验收标准

- [x] 5 个 Mapper、共 13 条 SQL，**全部 `FROM v_*` 视图，零直连实体表**
- [x] 表字段下划线 ↔ VO 驼峰自动映射（`map-underscore-to-camel-case: true`），不需要手写 resultMap
- [x] 动态条件用 `<where>` + `<if>`，不拼字符串、不用 `${}`（防 SQL 注入）
- [x] 分页/条数用 `LIMIT #{limit}`（`#{}` 预编译，不是 `${}`）
- [x] 视图可整体替换：只要视图名和字段名不变，B 岗改口径时 Mapper 一行不用改（已实测）
