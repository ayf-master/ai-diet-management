package com.diet.repo;

import com.diet.util.Rows;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Repository
public class UserRepo {

    private final JdbcTemplate jdbc;

    public UserRepo(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public Map<String, Object> findById(long userId) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT * FROM user WHERE user_id = ?",
                (rs, i) -> Rows.toMap(rs), userId);
        return rows.isEmpty() ? null : attachGoals(rows.get(0));
    }

    public Map<String, Object> findByAccount(String account) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT * FROM user WHERE account = ?",
                (rs, i) -> Rows.toMap(rs), account);
        return rows.isEmpty() ? null : attachGoals(rows.get(0));
    }

    // 原始行（不拼 goals），登录校验用
    public Map<String, Object> rawByAccount(String account) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT * FROM user WHERE account = ?",
                (rs, i) -> Rows.toMap(rs), account);
        return rows.isEmpty() ? null : rows.get(0);
    }

    public Map<String, Object> rawById(long userId) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT * FROM user WHERE user_id = ?",
                (rs, i) -> Rows.toMap(rs), userId);
        return rows.isEmpty() ? null : rows.get(0);
    }

    public boolean accountExists(String account) {
        Integer count = jdbc.queryForObject(
                "SELECT COUNT(*) FROM user WHERE account = ?", Integer.class, account);
        return count != null && count > 0;
    }

    public long insertUser(Map<String, Object> u) {
        jdbc.update("""
                INSERT INTO user (account, password, nickname, email, age, gender, height,
                                  current_weight, target_weight, activity_level, diet_goal, recommend_cal)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                u.get("account"), u.get("password"), u.get("nickname"), u.get("email"),
                u.get("age"), u.get("gender"), u.get("height"),
                u.get("current_weight"), u.get("target_weight"), u.get("activity_level"),
                u.get("diet_goal"), u.get("recommend_cal"));
        Long id = jdbc.queryForObject("SELECT user_id FROM user WHERE account = ?", Long.class, u.get("account"));
        return id == null ? 0 : id;
    }

    public void insertGoal(long userId, String goal) {
        jdbc.update("INSERT INTO user_goal (user_id, goal) VALUES (?, ?)", userId, goal);
    }

    public void deleteGoals(long userId) {
        jdbc.update("DELETE FROM user_goal WHERE user_id = ?", userId);
    }

    public void updatePassword(long userId, String hashed) {
        jdbc.update("UPDATE user SET password = ? WHERE user_id = ?", hashed, userId);
    }

    public void updateDietGoal(long userId, String goal) {
        jdbc.update("UPDATE user SET diet_goal = ? WHERE user_id = ?", goal, userId);
    }

    public void updateAvatar(long userId, String avatarUrl) {
        jdbc.update("UPDATE user SET avatar_url = ? WHERE user_id = ?", avatarUrl, userId);
    }

    public void callRecommendCal(long userId) {
        jdbc.update("CALL sp_recommend_daily_cal(?)", userId);
    }

    // 按创建时间倒序取用户目标（含 created_at），供 30 天间隔判断
    public List<Map<String, Object>> goalsWithCreatedAt(long userId) {
        return jdbc.query(
                "SELECT id, goal, created_at FROM user_goal WHERE user_id = ? ORDER BY created_at DESC",
                (rs, i) -> Rows.toMap(rs), userId);
    }

    private Map<String, Object> attachGoals(Map<String, Object> user) {
        user.remove("password");
        List<String> goals = jdbc.query(
                "SELECT goal FROM user_goal WHERE user_id = ? ORDER BY id",
                (rs, i) -> rs.getString("goal"), user.get("user_id"));
        List<String> goalList = goals.isEmpty()
                ? List.of(String.valueOf(user.get("diet_goal")))
                : goals;
        Map<String, Object> out = new LinkedHashMap<>(user);
        out.put("diet_goals", goalList);
        return out;
    }

    public Map<String, Object> findAdminByAccount(String account) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT admin_id, account, nickname, created_at FROM admin WHERE account = ?",
                (rs, i) -> Rows.toMap(rs), account);
        return rows.isEmpty() ? null : rows.get(0);
    }

    public Map<String, Object> rawAdminByAccount(String account) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT admin_id, account, password, nickname, created_at FROM admin WHERE account = ?",
                (rs, i) -> Rows.toMap(rs), account);
        return rows.isEmpty() ? null : rows.get(0);
    }

    // 验证码
    public String generateCode(String email, int minutes) {
        String code = String.format("%06d", new java.security.SecureRandom().nextInt(1000000));
        java.sql.Timestamp now = new java.sql.Timestamp(System.currentTimeMillis());
        java.sql.Timestamp expires = new java.sql.Timestamp(now.getTime() + minutes * 60_000L);
        jdbc.update("INSERT INTO verification_code (email, code, created_at, expires_at, used) VALUES (?, ?, ?, ?, 0)",
                email, code, now, expires);
        return code;
    }

    public boolean verifyCode(String email, String code) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT id, expires_at FROM verification_code WHERE email = ? AND code = ? AND used = 0 " +
                        "ORDER BY created_at DESC LIMIT 1",
                (rs, i) -> Rows.toMap(rs), email, code);
        if (rows.isEmpty()) {
            return false;
        }
        Map<String, Object> vc = rows.get(0);
        java.sql.Timestamp expires = (java.sql.Timestamp) vc.get("expires_at");
        if (expires.before(new java.sql.Timestamp(System.currentTimeMillis()))) {
            return false;
        }
        jdbc.update("UPDATE verification_code SET used = 1 WHERE id = ?", vc.get("id"));
        return true;
    }
}
