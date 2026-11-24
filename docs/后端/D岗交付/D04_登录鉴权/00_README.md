# D04 · 登录鉴权

> 截止：11/26　|　应交文件：2（`登录鉴权说明.md` + `代码/`）　|　状态：✅ 已完成

## 这一项放什么

| 文件 | 说明 |
|---|---|
| `登录鉴权说明.md` | 主交付物：JWT 签发/校验、拦截器白名单、BCrypt 存储、实测记录 |
| `代码/JwtUtil.java` `AuthService.java` `AuthInterceptor.java` `AuthController.java` `LoginRequest.java` `LoginResponse.java` | 鉴权全部真代码（6 个文件，可直接读） |
| `04_auth_seed.sql` | 角色与账号初始化（密码为 BCrypt 密文） |

## 验收标准

- [x] 账号密码**不以明文**入库（`sys_user.password_hash` 存 `$2a$10$…`）
- [x] 登录成功返回 JWT，实测令牌长度 172 字符，`/api/auth/me` 可凭令牌换回用户信息
- [x] 不带令牌访问受保护接口 → `code 401`「未携带令牌，请先登录」
- [x] 密码错误 → `code 401`「用户名或密码错误」（不区分是哪一项错）
- [x] 令牌过期/伪造 → `code 401`「令牌已失效，请重新登录」，不会 500
- [x] 密钥从配置读、启动校验长度 ≥ 32 字节，**没有硬编码在代码里**
- [x] 默认 `uev.auth.enabled=false`，保证 C 岗前端联调不被拦住（答辩前可一键打开）
