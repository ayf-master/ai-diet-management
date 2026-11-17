package com.diet.common;

// 业务异常：service 层只描述业务错误，由全局处理器翻译成 HTTP {code,msg}
public class DomainException extends RuntimeException {
    private final int code;

    public DomainException(int code, String message) {
        super(message);
        this.code = code;
    }

    public int getCode() {
        return code;
    }
}
