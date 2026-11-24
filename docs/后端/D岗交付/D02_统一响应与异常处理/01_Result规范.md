# 统一响应与异常处理（D02）

> 维护人：杨姗姗（D 岗）　|　版本 v1.0　|　2026-11-20
> 契约依据：`docs/contracts/03-接口规范.md` · 1.2 节

---

## 一、统一响应结构

所有接口（成功、失败、异常）都返回同一个 JSON 形状：

```json
{
  "code": 200,
  "message": "success",
  "data": { },
  "timestamp": 1795159655771
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `code` | int | 200 成功；400 参数错误；401 未认证；403 无权限；404 资源不存在；405 方法不支持；500 服务异常；503 依赖不可用 |
| `message` | string | 前端失败时直接展示给用户（**所以必须是中文人话**） |
| `data` | object/array | 数据载荷；失败时为 `null`（Jackson 配了 `non_null`，实际不出现在 JSON 里） |
| `timestamp` | long | 服务端毫秒时间戳，用于前端排查"拿到的是不是旧响应" |

### 为什么 HTTP 状态码恒为 200

这是**故意**的设计，和契约 03 一致：

```javascript
// frontend/js/common.js —— C 岗的请求封装
const res = await fetch(url);
if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText}`);  // ← 这里会先抛
const json = await res.json();
if (json.code !== 200) throw new Error(json.message || '请求失败');
```

如果后端对参数错误返回 HTTP 400，前端会在第一行就抛 `HTTP 400 Bad Request`，
**后端写的中文提示（例如"limit 最大值为 100"）根本到不了页面**，用户只看到一行英文。

所以：**HTTP 层永远 200，业务成败只看 body 里的 `code`。**

---

## 二、错误码表（与代码 `ErrorCode.java` 一一对应）

| code | 枚举 | 默认 message | 触发场景 |
|---|---|---|---|
| 200 | `SUCCESS` | success | 正常返回 |
| 400 | `PARAM_ERROR` | 请求参数不合法 | 缺参、类型错、范围越界、`startDate > endDate` |
| 401 | `UNAUTHORIZED` | 未登录或令牌已失效 | 无令牌、令牌过期、用户名或密码错误 |
| 403 | `FORBIDDEN` | 没有访问权限 | 账号被停用 |
| 404 | `NOT_FOUND` | 资源不存在 | 分区编号不存在、KPI 数据未就绪、路径拼错 |
| 405 | `METHOD_NOT_ALLOWED` | 请求方法不支持 | 对只读接口发 POST |
| 500 | `SERVICE_ERROR` | 服务器内部错误，请稍后重试 | 未预期异常（兜底） |
| 503 | `DB_UNAVAILABLE` | 数据库暂时不可用，已降级返回 | MySQL 停机 / 连接池耗尽 |

> 设计取舍：401 和 404 的 message **故意分开写**（"用户名或密码错误"不区分是哪一个错），
> 避免通过错误提示反推账号是否存在。

---

## 三、异常处理矩阵（谁能抛、谁来接、最后变成什么）

| 异常来源 | 异常类型 | 处理器 | 输出 code | 日志级别 |
|---|---|---|---|---|
| Service 主动抛 | `BusinessException` | `handleBusiness` | 跟随 `ErrorCode` | WARN（不打堆栈） |
| `@RequestBody @Valid` 失败 | `MethodArgumentNotValidException` | `handleValid` | 400 | WARN |
| 查询对象绑定失败 | `BindException` | `handleBind` | 400 | 无 |
| `@RequestParam` 约束失败 | `ConstraintViolationException` | `handleConstraint` | 400 | 无 |
| 缺必填参数 | `MissingServletRequestParameterException` | `handleMissingParam` | 400 | 无 |
| 参数类型错 | `MethodArgumentTypeMismatchException` | `handleTypeMismatch` | 400 | 无 |
| 请求体非 JSON | `HttpMessageNotReadableException` | `handleUnreadable` | 400 | 无 |
| 方法不支持 | `HttpRequestMethodNotSupportedException` | `handleMethod` | 405 | 无 |
| **数据库异常** | `DataAccessException` | `handleDataAccess` | **503** | ERROR（带堆栈） |
| **路径不存在** | `NoResourceFoundException` | `handleAll` 内判别 | **404** | WARN |
| 其它一切 | `Exception` | `handleAll` | 500 | ERROR（带堆栈） |

**关键点：数据库异常必须单独接。** 否则 MySQL 挂了会落到兜底的 500"服务器内部错误"，
用户以为是后端崩了，其实是数据库的事 —— 这是排查里最容易浪费时间的坑。

---

## 四、实测样例（2026-11-20 本机实跑，原样粘贴）

| # | 请求 | 实际返回 |
|---|---|---|
| 1 | `GET /api/charts/imbalance?limit=999` | `{"code":400,"message":"limit 最大值为 100","timestamp":1795159893782}` |
| 2 | `GET /api/zones/999` | `{"code":404,"message":"分区 999 不存在","timestamp":1795159893804}` |
| 3 | `GET /api/hours/xx`（不存在的路径） | `{"code":404,"message":"接口不存在，请核对路径","timestamp":1795159893813}` |
| 4 | `GET /api/auth/me`（不带令牌） | `{"code":401,"message":"未携带令牌，请先登录","timestamp":1795159893819}` |
| 5 | `POST /api/auth/login`（密码错） | `{"code":401,"message":"用户名或密码错误","timestamp":1795159893923}` |
| 6 | `GET /api/charts/hourly?hourRange=19-17` | `{"code":400,"message":"hourRange 起始小时不能大于结束小时","timestamp":1795159893939}` |
| 7 | MySQL 停机后 `GET /api/charts/imbalance?limit=9` | `{"code":503,"message":"数据库暂时不可用，已降级返回","timestamp":1795160141491}` |

> 这 7 条同时是 D11 测试用例表里"异常用例"的实测结果列，不需要另编数据。

---

## 五、核心代码（完整版见 `代码/`）

### 5.1 统一响应（`ApiResponse.java`）
```java
public class ApiResponse<T> implements Serializable {
    private int code;
    private String message;
    private T data;
    private long timestamp;

    public static <T> ApiResponse<T> ok(T data) {
        return new ApiResponse<>(ErrorCode.SUCCESS.getCode(), ErrorCode.SUCCESS.getMessage(), data);
    }

    public static <T> ApiResponse<T> fail(ErrorCode errorCode, String message) {
        return new ApiResponse<>(errorCode.getCode(), message, null);
    }
}
```

### 5.2 业务异常（`BusinessException.java`）
```java
public class BusinessException extends RuntimeException {
    private final ErrorCode errorCode;

    public static BusinessException paramError(String message) {
        return new BusinessException(ErrorCode.PARAM_ERROR, message);
    }
    public static BusinessException notFound(String message) {
        return new BusinessException(ErrorCode.NOT_FOUND, message);
    }
}
```
Service 只抛这一种，Controller 一个 try-catch 都不用写。

### 5.3 数据库异常单独接（`GlobalExceptionHandler.java` 片段）
```java
@ExceptionHandler(org.springframework.dao.DataAccessException.class)
public ApiResponse<Void> handleDataAccess(org.springframework.dao.DataAccessException e) {
    log.error("[数据访问异常] 数据库不可用或 SQL 执行失败", e);
    return ApiResponse.fail(ErrorCode.DB_UNAVAILABLE);
}
```

### 5.4 兜底与"路径不存在"判别
```java
@ExceptionHandler(Exception.class)
public ApiResponse<Void> handleAll(Exception e) {
    if (e instanceof org.springframework.web.servlet.resource.NoResourceFoundException) {
        return ApiResponse.fail(ErrorCode.NOT_FOUND, "接口不存在，请核对路径");
    }
    log.error("[系统异常] 未预期异常，已统一转为 500 响应", e);
    return ApiResponse.fail(ErrorCode.SERVICE_ERROR);
}
```
> Spring Boot 3 把"路径不存在"抛成 `NoResourceFoundException`，
> 不判别就会变成 500 —— 前端拼错一个接口名就会以为后端挂了。

---

## 六、这套机制的验证方式（答辩 30 秒演示）

1. 打开 Postman，故意把 `limit` 改成 999 → 看到 `code:400` + 中文提示
2. 把分区编号改成 `999` → 看到 `code:404` + "分区 999 不存在"
3. 停掉 MySQL 服务 → 再请求一次没缓存过的接口 → 看到 `code:503` + "数据库暂时不可用"
4. 任何一步，HTTP 状态码都是 **200**，页面不会被 `HTTP 500` 卡死

> 结论一句话：**接口的失败是"可读的"，不是"白屏的"。**
