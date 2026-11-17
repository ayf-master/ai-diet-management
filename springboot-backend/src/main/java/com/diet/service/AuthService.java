package com.diet.service;

import com.diet.common.DomainException;
import com.diet.repo.UserRepo;
import com.diet.security.AuthContext;
import com.diet.security.AuthSupport;
import com.diet.security.JwtUtil;
import com.diet.util.EmailSender;
import com.diet.util.PasswordHasher;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

@Service
public class AuthService {

    private static final Set<String> ALLOWED_AVATAR_TYPES =
            Set.of("image/jpeg", "image/png", "image/webp", "image/gif");

    private final UserRepo users;
    private final JwtUtil jwt;
    private final String uploadFolder;
    private final String avatarUrlPrefix = "/static/avatars";

    public AuthService(UserRepo users, JwtUtil jwt,
                       @Value("${app.upload-folder}") String uploadFolder) {
        this.users = users;
        this.jwt = jwt;
        this.uploadFolder = uploadFolder;
    }

    public Map<String, Object> register(Map<String, Object> data) {
        String account = (String) data.get("account");
        String password = (String) data.get("password");
        if (account == null || password == null || account.isEmpty() || password.isEmpty()) {
            throw new DomainException(400, "账号和密码不能为空");
        }
        if (users.accountExists(account)) {
            throw new DomainException(409, "账号已存在");
        }

        @SuppressWarnings("unchecked")
        List<String> dietGoals = data.containsKey("diet_goals")
                ? (List<String>) data.get("diet_goals")
                : List.of(String.valueOf(data.getOrDefault("diet_goal", "healthy")));
        if (dietGoals == null || dietGoals.isEmpty()) {
            dietGoals = List.of("healthy");
        }

        Map<String, Object> u = new LinkedHashMap<>();
        u.put("account", account);
        u.put("password", PasswordHasher.encode(password));
        u.put("nickname", data.getOrDefault("nickname", account));
        u.put("email", data.get("email"));
        u.put("age", numOrDefault(data.get("age"), 18));
        u.put("gender", numOrDefault(data.get("gender"), 0));
        u.put("height", numOrDefault(data.get("height"), 160));
        u.put("current_weight", numOrDefault(data.get("current_weight"), 60));
        u.put("target_weight", numOrDefault(data.get("target_weight"), 55));
        u.put("activity_level", numOrDefault(data.get("activity_level"), 1));
        u.put("diet_goal", dietGoals.get(0));
        u.put("recommend_cal", 1500);

        long userId = users.insertUser(u);
        for (String goal : dietGoals) {
            users.insertGoal(userId, goal);
        }
        users.callRecommendCal(userId);

        Map<String, Object> user = users.findById(userId);
        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("code", 200);
        resp.put("msg", "注册成功");
        resp.put("data", user);
        resp.put("access_token", jwt.issue(userId, "user", null));
        return resp;
    }

    public Map<String, Object> login(Map<String, Object> data) {
        if (data == null || data.isEmpty()) {
            throw new DomainException(400, "请求数据为空");
        }
        Map<String, Object> user = users.rawByAccount((String) data.get("account"));
        if (user == null || !PasswordHasher.verify((String) data.get("password"), (String) user.get("password"))) {
            throw new DomainException(401, "账号或密码错误");
        }
        long userId = ((Number) user.get("user_id")).longValue();
        Map<String, Object> full = users.findById(userId);
        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("code", 200);
        resp.put("msg", "登录成功");
        resp.put("data", full);
        resp.put("access_token", jwt.issue(userId, "user", null));
        return resp;
    }

    public Map<String, Object> adminLogin(Map<String, Object> data) {
        if (data == null || data.isEmpty()) {
            throw new DomainException(400, "请求数据为空");
        }
        Map<String, Object> admin = users.rawAdminByAccount((String) data.get("account"));
        if (admin == null || !PasswordHasher.verify((String) data.get("password"), (String) admin.get("password"))) {
            throw new DomainException(401, "账号或密码错误");
        }
        long adminId = ((Number) admin.get("admin_id")).longValue();
        admin.remove("password");
        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("code", 200);
        resp.put("msg", "登录成功");
        resp.put("data", admin);
        resp.put("access_token", jwt.issue(adminId, "admin", adminId));
        return resp;
    }

    public Map<String, Object> profile(Long userId) {
        if (userId == null) {
            throw new DomainException(400, "缺少user_id");
        }
        AuthSupport.ensureSelf(userId);
        Map<String, Object> user = users.findById(userId);
        if (user == null) {
            throw new DomainException(404, "用户不存在");
        }
        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("code", 200);
        resp.put("data", user);
        return resp;
    }

    public Map<String, Object> updateZones(Map<String, Object> data) {
        Long userId = toLong(data.get("user_id"));
        @SuppressWarnings("unchecked")
        List<String> newGoals = (List<String>) data.get("diet_goals");
        if (userId == null || newGoals == null || newGoals.isEmpty()) {
            throw new DomainException(400, "参数错误");
        }
        AuthSupport.ensureSelf(userId);
        Map<String, Object> user = users.findById(userId);
        if (user == null) {
            throw new DomainException(404, "用户不存在");
        }

        // 30 天内只能改一次专区
        List<Map<String, Object>> goalRows = users.goalsWithCreatedAt(userId);
        if (!goalRows.isEmpty()) {
            String latest = (String) goalRows.get(0).get("created_at");
            long daysSince = -1;
            try {
                java.time.LocalDateTime created = java.time.LocalDateTime.parse(latest.replace(' ', 'T'));
                daysSince = java.time.temporal.ChronoUnit.DAYS.between(created.toLocalDate(), java.time.LocalDate.now());
            } catch (Exception ignored) {
            }
            if (daysSince >= 0 && daysSince < 30) {
                Map<String, Object> err = new LinkedHashMap<>();
                err.put("code", 429);
                err.put("msg", "专区修改需间隔30天，还剩" + (30 - daysSince) + "天");
                err.put("data", Map.of("days_remaining", 30 - daysSince));
                throw new ZonesException(err, (int) (30 - daysSince));
            }
        }

        users.deleteGoals(userId);
        for (String goal : newGoals) {
            users.insertGoal(userId, goal);
        }
        users.updateDietGoal(userId, newGoals.get(0));
        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("code", 200);
        resp.put("msg", "专区更新成功");
        resp.put("data", users.findById(userId));
        return resp;
    }

    private List<Map<String, Object>> goalsWithTime(long userId) {
        return users.goalsWithCreatedAt(userId);
    }

    public Map<String, Object> uploadAvatar(Long userId, MultipartFile file) throws IOException {
        if (userId == null) {
            throw new DomainException(400, "缺少user_id");
        }
        AuthSupport.ensureSelf(userId);
        Map<String, Object> user = users.rawById(userId);
        if (user == null) {
            throw new DomainException(404, "用户不存在");
        }
        if (file == null || file.isEmpty()) {
            throw new DomainException(400, "请选择头像文件");
        }
        if (!ALLOWED_AVATAR_TYPES.contains(file.getContentType())) {
            throw new DomainException(400, "仅支持 JPG/PNG/WebP/GIF 图片");
        }

        String ext = "png";
        String name = file.getOriginalFilename();
        if (name != null && name.contains(".")) {
            ext = name.substring(name.lastIndexOf('.') + 1).toLowerCase();
            if (!List.of("jpg", "jpeg", "png", "webp", "gif").contains(ext)) {
                ext = "png";
            }
        }
        String filename = userId + "_" + System.currentTimeMillis() / 1000 + "." + ext;
        Path dir = Path.of(uploadFolder);
        Files.createDirectories(dir);
        file.transferTo(dir.resolve(filename).toFile());

        cleanupOldAvatar((String) user.get("avatar_url"));
        String avatarUrl = avatarUrlPrefix + "/" + filename;
        users.updateAvatar(userId, avatarUrl);

        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("code", 200);
        resp.put("msg", "头像上传成功");
        resp.put("data", Map.of("avatar_url", avatarUrl));
        return resp;
    }

    public Map<String, Object> removeAvatar(Long userId) throws IOException {
        if (userId == null) {
            throw new DomainException(400, "缺少user_id");
        }
        AuthSupport.ensureSelf(userId);
        Map<String, Object> user = users.rawById(userId);
        if (user == null) {
            throw new DomainException(404, "用户不存在");
        }
        String avatarUrl = (String) user.get("avatar_url");
        if (avatarUrl != null && !avatarUrl.isEmpty()) {
            cleanupOldAvatar(avatarUrl);
            users.updateAvatar(userId, "");
        }
        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("code", 200);
        resp.put("msg", "头像已移除");
        resp.put("data", Map.of("avatar_url", ""));
        return resp;
    }

    private void cleanupOldAvatar(String avatarUrl) {
        if (avatarUrl == null || avatarUrl.isEmpty()) {
            return;
        }
        String oldName = avatarUrl.substring(avatarUrl.lastIndexOf('/') + 1);
        try {
            Files.deleteIfExists(Path.of(uploadFolder, oldName));
        } catch (IOException ignored) {
        }
    }

    public Map<String, Object> sendCode(Map<String, Object> data) {
        String account = data == null || data.get("account") == null
                ? "" : String.valueOf(data.get("account")).trim();
        if (account.isEmpty()) {
            throw new DomainException(400, "请输入账号");
        }
        Map<String, Object> user = users.rawByAccount(account);
        if (user == null) {
            throw new DomainException(404, "账号不存在");
        }
        String email = (String) user.get("email");
        if (email == null || email.isEmpty()) {
            throw new DomainException(400, "该账号未绑定邮箱，无法找回密码");
        }
        String code = users.generateCode(email, 10);
        boolean ok = EmailSender.sendVerificationCode(email, code);
        if (!ok) {
            if (!EmailSender.fromEnv().configured()) {
                Map<String, Object> resp = new LinkedHashMap<>();
                resp.put("code", 200);
                resp.put("msg", "验证码已发送至 " + email + "（开发模式）");
                resp.put("dev_code", code);
                resp.put("dev_mode", true);
                return resp;
            }
            throw new DomainException(500, "验证码发送失败，请检查服务器邮件配置");
        }
        String masked = email.substring(0, Math.min(3, email.length())) + "***@" + email.substring(email.indexOf('@') + 1);
        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("code", 200);
        resp.put("msg", "验证码已发送至 " + masked);
        return resp;
    }

    public Map<String, Object> resetPassword(Map<String, Object> data) {
        String account = data == null || data.get("account") == null
                ? "" : String.valueOf(data.get("account")).trim();
        String code = data == null || data.get("code") == null
                ? "" : String.valueOf(data.get("code")).trim();
        String password = data == null || data.get("password") == null
                ? "" : String.valueOf(data.get("password"));
        if (account.isEmpty() || code.isEmpty() || password.isEmpty()) {
            throw new DomainException(400, "账号、验证码和新密码不能为空");
        }
        if (password.length() < 6) {
            throw new DomainException(400, "密码长度至少6位");
        }
        Map<String, Object> user = users.rawByAccount(account);
        if (user == null) {
            throw new DomainException(404, "账号不存在");
        }
        String email = (String) user.get("email");
        if (email == null || email.isEmpty()) {
            throw new DomainException(400, "该账号未绑定邮箱");
        }
        if (!users.verifyCode(email, code)) {
            throw new DomainException(400, "验证码无效或已过期");
        }
        users.updatePassword(((Number) user.get("user_id")).longValue(), PasswordHasher.encode(password));
        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("code", 200);
        resp.put("msg", "密码重置成功，请用新密码登录");
        return resp;
    }

    private static Long toLong(Object v) {
        if (v == null) {
            return null;
        }
        if (v instanceof Number n) {
            return n.longValue();
        }
        try {
            return Long.parseLong(String.valueOf(v));
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private static Object numOrDefault(Object v, int def) {
        if (v == null) {
            return def;
        }
        if (v instanceof Number n) {
            return n;
        }
        try {
            return Double.parseDouble(String.valueOf(v));
        } catch (NumberFormatException e) {
            return def;
        }
    }

    // 429 响应体结构与普通 DomainException 不同，单独携带
    public static class ZonesException extends RuntimeException {
        public final Map<String, Object> body;

        public ZonesException(Map<String, Object> body, int daysRemaining) {
            super((String) body.get("msg"));
            this.body = body;
        }
    }
}
