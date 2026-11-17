package com.diet.common;

import java.util.LinkedHashMap;
import java.util.Map;

// 统一响应结构，对齐 Flask 版 {code, msg, data}
public class ApiResponse {
    public static Map<String, Object> ok() {
        return base(200, null, null);
    }

    public static Map<String, Object> ok(String msg) {
        return base(200, msg, null);
    }

    public static Map<String, Object> ok(Object data) {
        return base(200, null, data);
    }

    public static Map<String, Object> ok(String msg, Object data) {
        return base(200, msg, data);
    }

    public static Map<String, Object> of(int code, String msg) {
        return base(code, msg, null);
    }

    public static Map<String, Object> of(int code, String msg, Object data) {
        return base(code, msg, data);
    }

    private static Map<String, Object> base(int code, String msg, Object data) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("code", code);
        m.put("msg", msg);
        m.put("data", data);
        return m;
    }
}
