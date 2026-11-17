package com.diet.security;

import io.jsonwebtoken.Claims;

// 请求级登录态；由 JwtAuthFilter 写入，控制器/service 读取
public class AuthContext {

    public record Identity(Long userId, String role, Long adminId) {
        public boolean isAdmin() {
            return "admin".equals(role);
        }
    }

    private static final ThreadLocal<Identity> HOLDER = new ThreadLocal<>();

    public static void set(Claims claims) {
        Long userId = null;
        try {
            userId = Long.parseLong(claims.getSubject());
        } catch (NumberFormatException ignored) {
        }
        Long adminId = claims.get("admin_id", Number.class) != null
                ? ((Number) claims.get("admin_id")).longValue() : null;
        String role = claims.get("role", String.class) != null
                ? claims.get("role", String.class) : "user";
        HOLDER.set(new Identity(userId, role, adminId));
    }

    public static Identity get() {
        return HOLDER.get();
    }

    public static void clear() {
        HOLDER.remove();
    }
}
