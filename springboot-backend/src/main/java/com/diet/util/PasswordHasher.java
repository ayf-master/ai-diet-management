package com.diet.util;

import org.bouncycastle.crypto.generators.SCrypt;

import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;
import java.security.MessageDigest;
import java.util.Random;

// Werkzeug 兼容密码工具：能校验 md5 / scrypt / pbkdf2 三种历史格式，新密码统一写 pbkdf2 格式
public class PasswordHasher {

    private static final String SALT_ALPHABET =
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";

    // 新密码：werkzeug 兼容的 pbkdf2:sha256:600000$salt$hash
    public static String encode(String password) {
        String salt = genSalt(16);
        return "pbkdf2:sha256:600000$" + salt + "$" + pbkdf2Hex(password, salt, "SHA256", 600000);
    }

    public static boolean verify(String password, String stored) {
        if (password == null || stored == null || stored.isEmpty()) {
            return false;
        }
        if (stored.contains("$")) {
            // werkzeug 格式：method$salt$hash
            String[] parts = stored.split("\\$", 2);
            String method = parts[0];
            String rest = parts.length > 1 ? parts[1] : "";
            String[] second = rest.split("\\$", 2);
            if (second.length != 2) {
                return false;
            }
            String salt = second[0];
            String hash = second[1];
            if (method.startsWith("scrypt")) {
                String[] params = method.split(":");
                if (params.length != 4) {
                    return false;
                }
                try {
                    int n = Integer.parseInt(params[1]);
                    int r = Integer.parseInt(params[2]);
                    int p = Integer.parseInt(params[3]);
                    byte[] derived = SCrypt.generate(
                            password.getBytes(java.nio.charset.StandardCharsets.UTF_8),
                            salt.getBytes(java.nio.charset.StandardCharsets.UTF_8), n, r, p, 64);
                    return slowEquals(toHex(derived), hash.toLowerCase());
                } catch (Exception e) {
                    return false;
                }
            }
            if (method.startsWith("pbkdf2")) {
                String[] params = method.split(":");
                if (params.length != 3) {
                    return false;
                }
                try {
                    String hashName = params[1];
                    int iterations = Integer.parseInt(params[2]);
                    return slowEquals(pbkdf2Hex(password, salt, hashName, iterations), hash.toLowerCase());
                } catch (Exception e) {
                    return false;
                }
            }
            return false;
        }
        // 旧种子数据：裸 md5 hex
        if (stored.length() == 32) {
            try {
                byte[] digest = MessageDigest.getInstance("MD5")
                        .digest(password.getBytes(java.nio.charset.StandardCharsets.UTF_8));
                return slowEquals(toHex(digest), stored.toLowerCase());
            } catch (Exception e) {
                return false;
            }
        }
        return false;
    }

    private static String pbkdf2Hex(String password, String salt, String hashName, int iterations) {
        try {
            String factoryName = "PBKDF2WithHmac" + hashName.replace("-", "");
            PBEKeySpec spec = new PBEKeySpec(password.toCharArray(),
                    salt.getBytes(java.nio.charset.StandardCharsets.UTF_8), iterations, 256);
            byte[] key = SecretKeyFactory.getInstance(factoryName).generateSecret(spec).getEncoded();
            return toHex(key);
        } catch (Exception e) {
            throw new IllegalStateException("pbkdf2 failed", e);
        }
    }

    private static String genSalt(int length) {
        Random random = new Random();
        StringBuilder sb = new StringBuilder(length);
        for (int i = 0; i < length; i++) {
            sb.append(SALT_ALPHABET.charAt(random.nextInt(SALT_ALPHABET.length())));
        }
        return sb.toString();
    }

    private static boolean slowEquals(String a, String b) {
        byte[] ba = a.getBytes(java.nio.charset.StandardCharsets.UTF_8);
        byte[] bb = b.getBytes(java.nio.charset.StandardCharsets.UTF_8);
        return MessageDigest.isEqual(ba, bb);
    }

    private static String toHex(byte[] bytes) {
        StringBuilder sb = new StringBuilder(bytes.length * 2);
        for (byte b : bytes) {
            sb.append(String.format("%02x", b));
        }
        return sb.toString();
    }
}
