package com.diet.common;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.Map;

// 对齐 Flask 版语义：DomainError -> {code, msg}；参数缺失 -> 400
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(com.diet.service.AuthService.ZonesException.class)
    public ResponseEntity<Map<String, Object>> handleZones(com.diet.service.AuthService.ZonesException e) {
        return ResponseEntity.status(429).body(e.body);
    }

    @ExceptionHandler(DomainException.class)
    public ResponseEntity<Map<String, Object>> handleDomain(DomainException e) {
        return ResponseEntity.status(e.getCode()).body(ApiResponse.of(e.getCode(), e.getMessage()));
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<Map<String, Object>> handleBadRequest(IllegalArgumentException e) {
        return ResponseEntity.badRequest().body(ApiResponse.of(400, e.getMessage()));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, Object>> handleOther(Exception e) {
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ApiResponse.of(500, "服务器内部错误: " + e.getMessage()));
    }
}
