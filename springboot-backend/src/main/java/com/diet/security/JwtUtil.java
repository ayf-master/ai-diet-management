package com.diet.security;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;

// JWT 签发与校验；token 只放身份与角色，对齐 Flask 版设计
@Component
public class JwtUtil {

    private final SecretKey key;
    private final long expireMs = 12 * 3600 * 1000;

    public JwtUtil(@Value("${app.jwt-secret}") String secret) {
        // HS256 要求密钥至少 32 字节
        byte[] bytes = (secret + "0123456789abcdef0123456789abcdef").getBytes(StandardCharsets.UTF_8);
        this.key = Keys.hmacShaKeyFor(bytes.length > 64 ? java.util.Arrays.copyOf(bytes, 64) : pad(bytes));
    }

    private static byte[] pad(byte[] src) {
        byte[] out = new byte[32];
        for (int i = 0; i < 32; i++) {
            out[i] = src.length > 0 ? src[i % src.length] : 0;
        }
        return out;
    }

    public String issue(long subjectId, String role, Long adminId) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("role", role);
        if (adminId != null) {
            claims.put("admin_id", adminId);
        }
        Date now = new Date();
        return Jwts.builder()
                .subject(String.valueOf(subjectId))
                .claims(claims)
                .issuedAt(now)
                .expiration(new Date(now.getTime() + expireMs))
                .signWith(key)
                .compact();
    }

    // 解析失败或过期返回 null，由过滤器统一翻译成 401 JSON
    public Claims parse(String token) {
        try {
            return Jwts.parser().verifyWith(key).build()
                    .parseSignedClaims(token).getPayload();
        } catch (JwtException | IllegalArgumentException e) {
            return null;
        }
    }
}
