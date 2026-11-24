# D 岗（后端服务）交付说明 · 杨姗姗

> 学号 2400770293　|　软工 2405 班 · 第 02 组　|　分支 `feat/D-backend`

本目录是 D 岗 15 项交付物的**文档与证据**，代码与 SQL 已经按仓库既有的目录规范落到 `backend/`、`db/`。

## 一、这份分支往仓库里放了什么

| 仓库路径 | 内容 | 对应交付项 |
|---|---|---|
| `backend/src/main/java/com/uev/` | 16 个接口的完整实现：6 Controller、5 Service、5 Mapper、JWT 鉴权、双模缓存（Redis / 本地降级）、统一响应与异常 | D01 / D02 / D04 / D06 / D07 / D08 |
| `backend/src/main/resources/mapper/*.xml` | 13 条 SQL 全部 `FROM v_*`，只读 B 岗交付的视图，不碰底座表 | D08 |
| `backend/pom.xml` | Spring Boot 3.2.5 + MyBatis + jjwt + AOP，`finalName=uev-charge-analysis`（与 Dockerfile 的 COPY 对齐） | D01 / D06 |
| `db/mysql/01_schema.sql` | 14 张表（含 4 个业务创新指标落地表） | D03 |
| `db/mysql/02_seed_mock.sql` | 演示数据（与契约同口径：275 站 / 23441 桩） | D03 / D05 |
| `db/mysql/03_views.sql` | 10 个视图（D 岗对该视图的接入口径） | D08 |
| `db/mysql/04_auth_seed.sql` | 账号与角色初始化（admin / ADMIN） | D04 |
| `docs/screenshots/D10_postman/` | **16 张 Postman 真实界面截图**（2400×1786 PNG）+ 集合 JSON | D10 |
| `docs/后端/D岗交付/D01…D15/` | 每一项的说明文档、结论、证据文本、mock 契约、测试用例表、报告章节 | D01~D15 |

## 二、怎么跑起来（3 步）

```bash
# 1. 库
mysql -u root -p < db/mysql/01_schema.sql
mysql -u root -p uev_charge < db/mysql/02_seed_mock.sql
mysql -u root -p uev_charge < db/mysql/03_views.sql
mysql -u root -p uev_charge < db/mysql/04_auth_seed.sql

# 2. 后端（默认连 localhost:3306 / uev_charge，可用 MYSQL_* 环境变量覆盖）
cd backend && mvn spring-boot:run

# 3. 自检
curl http://localhost:8080/api/health
# → {"code":200,"data":{"status":"DEGRADED","regionCount":275,"components":{"mysql":"UP","redis":"DOWN"}},...}
```

`redis=DOWN` 是**有意为之的降级**：没装 Redis 时自动切本地缓存，接口照常返回 200（D13 有实测证据）。

## 三、几个容易踩的点

- **端口**：`server.port` 走 `${SERVER_PORT:8080}`，本机演示若 8080 被占就 `--server.port=18080`，Postman 集合里的 `baseUrl` 要跟着改。
- **鉴权默认关闭**（`AUTH_ENABLED:false`），因为 C 岗前端骨架是裸 GET；答辩要展示 JWT 就加 `AUTH_ENABLED=true`，再按 D10 的顺序先跑 `/api/auth/login`。
- **Redis 密码**：本地默认空串，Docker 部署由 `docker-compose.yml` 注入 `REDIS_PASSWORD`。
- **截图是界面实测，不是渲染稿**：D10 的 16 张图来自 Postman 12.38 逐条 Send 后的全屏截图，裁到窗口后放大到 2400px，耗时/体积都是 Postman 自报值。

## 四、还差一件需要本人做的事

D14「第二台机器启动验证」需要在另一台机器或另一个目录跑一遍 `start.ps1` 并填记录表（`D14_第二台机器启动验证/01_第二台机器验证记录.md`），本机已验过，第二台待补。
