package com.uev.common;

/**
 * 统一错误码 —— 与契约 03 的 code 约定保持一致。
 *
 * <p>约定：200 成功 / 400 参数错误 / 404 资源不存在 / 500 服务异常；
 * 401、403、405、503 是在骨架上补充的细分码，前端遇到非 200 一律展示 message。
 *
 * @author 杨珊珊（D 岗）
 */
public enum ErrorCode {

    SUCCESS(200, "success"),
    PARAM_ERROR(400, "请求参数不合法"),
    UNAUTHORIZED(401, "未登录或令牌已失效"),
    FORBIDDEN(403, "没有访问权限"),
    NOT_FOUND(404, "资源不存在"),
    METHOD_NOT_ALLOWED(405, "请求方法不支持"),
    SERVICE_ERROR(500, "服务器内部错误，请稍后重试"),
    DB_UNAVAILABLE(503, "数据库暂时不可用，已降级返回"),
    REDIS_DOWN(503, "缓存不可用，已降级为直接查库");

    private final int code;
    private final String message;

    ErrorCode(int code, String message) {
        this.code = code;
        this.message = message;
    }

    public int getCode() {
        return code;
    }

    public String getMessage() {
        return message;
    }
}
