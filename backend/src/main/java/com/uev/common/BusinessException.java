package com.uev.common;

/**
 * 业务异常 —— Service 层只抛这一种异常，由 {@link GlobalExceptionHandler} 统一转响应。
 *
 * <p>好处：Controller 里不出现 try-catch，也不出现 new ResponseEntity(...)，
 * 三层职责彻底分开（D01 分层规范第 4 条）。
 *
 * @author 杨珊珊（D 岗）
 */
public class BusinessException extends RuntimeException {

    private static final long serialVersionUID = 1L;

    private final ErrorCode errorCode;

    public BusinessException(ErrorCode errorCode) {
        super(errorCode.getMessage());
        this.errorCode = errorCode;
    }

    public BusinessException(ErrorCode errorCode, String message) {
        super(message);
        this.errorCode = errorCode;
    }

    public BusinessException(ErrorCode errorCode, String message, Throwable cause) {
        super(message, cause);
        this.errorCode = errorCode;
    }

    public ErrorCode getErrorCode() {
        return errorCode;
    }

    public static BusinessException paramError(String message) {
        return new BusinessException(ErrorCode.PARAM_ERROR, message);
    }

    public static BusinessException notFound(String message) {
        return new BusinessException(ErrorCode.NOT_FOUND, message);
    }

    public static BusinessException serviceError(String message) {
        return new BusinessException(ErrorCode.SERVICE_ERROR, message);
    }
}
