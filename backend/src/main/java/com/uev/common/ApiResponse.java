package com.uev.common;

import lombok.Data;

import java.io.Serializable;

/**
 * 统一响应结构 —— 契约 03《接口规范》1.2 节。
 *
 * <pre>
 * { "code": 200, "message": "success", "data": {...}, "timestamp": 1731993600000 }
 * </pre>
 *
 * 前端只判断 {@code code === 200}，不解析异常栈，所以任何异常都必须在
 * {@link GlobalExceptionHandler} 里被转成本结构。
 *
 * @param <T> 数据载荷类型
 * @author 杨姗姗（D 岗）
 */
@Data
public class ApiResponse<T> implements Serializable {

    private static final long serialVersionUID = 1L;

    /** 200 成功；400 参数错误；401 未认证；404 资源不存在；500 服务异常；503 依赖不可用 */
    private int code;
    private String message;
    private T data;
    /** 服务端时间戳（毫秒） */
    private long timestamp;

    public ApiResponse() {
        this.timestamp = System.currentTimeMillis();
    }

    public ApiResponse(int code, String message, T data) {
        this.code = code;
        this.message = message;
        this.data = data;
        this.timestamp = System.currentTimeMillis();
    }

    public static <T> ApiResponse<T> ok(T data) {
        return new ApiResponse<>(ErrorCode.SUCCESS.getCode(), ErrorCode.SUCCESS.getMessage(), data);
    }

    public static <T> ApiResponse<T> ok() {
        return ok(null);
    }

    public static <T> ApiResponse<T> fail(ErrorCode errorCode) {
        return new ApiResponse<>(errorCode.getCode(), errorCode.getMessage(), null);
    }

    public static <T> ApiResponse<T> fail(ErrorCode errorCode, String message) {
        return new ApiResponse<>(errorCode.getCode(), message, null);
    }

    public static <T> ApiResponse<T> fail(int code, String message) {
        return new ApiResponse<>(code, message, null);
    }
}
