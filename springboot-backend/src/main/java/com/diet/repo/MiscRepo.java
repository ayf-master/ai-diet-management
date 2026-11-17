package com.diet.repo;

import com.diet.util.Rows;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

// 疾病 / 体重记录 等零散表
@Repository
public class MiscRepo {

    private final JdbcTemplate jdbc;

    public MiscRepo(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public List<Map<String, Object>> listDiseases() {
        return jdbc.query("SELECT disease_id, disease_name, forbid_desc, forbid_keywords, forbid_rules, created_at " +
                        "FROM disease ORDER BY disease_id",
                (rs, i) -> Rows.toMap(rs));
    }

    public Map<String, Object> findDisease(long diseaseId) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT disease_id, disease_name, forbid_desc, forbid_keywords, forbid_rules, created_at " +
                        "FROM disease WHERE disease_id = ?",
                (rs, i) -> Rows.toMap(rs), diseaseId);
        return rows.isEmpty() ? null : rows.get(0);
    }

    // 疾病判定规则 [{name, keywords, rules}]
    public List<Map<String, Object>> userDiseaseRules(long userId) {
        List<Map<String, Object>> out = new ArrayList<>();
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT d.disease_id, d.disease_name, d.forbid_keywords, d.forbid_rules " +
                        "FROM user_disease ud JOIN disease d ON d.disease_id = ud.disease_id WHERE ud.user_id = ?",
                (rs, i) -> Rows.toMap(rs), userId);
        for (Map<String, Object> d : rows) {
            List<String> keywords = new ArrayList<>();
            String kwStr = (String) d.get("forbid_keywords");
            if (kwStr != null) {
                for (String k : kwStr.split(",")) {
                    if (!k.trim().isEmpty()) {
                        keywords.add(k.trim());
                    }
                }
            }
            Map<String, Object> rules = new LinkedHashMap<>();
            String rulesStr = (String) d.get("forbid_rules");
            if (rulesStr != null && !rulesStr.isEmpty()) {
                try {
                    @SuppressWarnings("unchecked")
                    Map<String, Object> parsed = new com.fasterxml.jackson.databind.ObjectMapper()
                            .readValue(rulesStr, Map.class);
                    rules = parsed;
                } catch (Exception ignored) {
                }
            }
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("name", d.get("disease_name"));
            item.put("keywords", keywords);
            item.put("rules", rules);
            out.add(item);
        }
        return out;
    }

    // 用户疾病（含用户备注），供 AI prompt 用
    public List<Map<String, Object>> userDiseasesWithRemark(long userId) {
        return jdbc.query(
                "SELECT d.disease_id, d.disease_name, d.forbid_desc, d.forbid_keywords, d.forbid_rules, ud.remark " +
                        "FROM user_disease ud JOIN disease d ON d.disease_id = ud.disease_id WHERE ud.user_id = ?",
                (rs, i) -> Rows.toMap(rs), userId);
    }

    public List<Map<String, Object>> userDiseases(long userId) {
        return jdbc.query("SELECT id, user_id, disease_id, remark, created_at FROM user_disease WHERE user_id = ?",
                (rs, i) -> Rows.toMap(rs), userId);
    }

    public Map<String, Object> findUserDisease(long id) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT id, user_id, disease_id, remark, created_at FROM user_disease WHERE id = ?",
                (rs, i) -> Rows.toMap(rs), id);
        return rows.isEmpty() ? null : rows.get(0);
    }

    public boolean userDiseaseExists(long userId, long diseaseId) {
        Integer count = jdbc.queryForObject(
                "SELECT COUNT(*) FROM user_disease WHERE user_id = ? AND disease_id = ?",
                Integer.class, userId, diseaseId);
        return count != null && count > 0;
    }

    public void insertUserDisease(long userId, long diseaseId, String remark) {
        jdbc.update("INSERT INTO user_disease (user_id, disease_id, remark) VALUES (?, ?, ?)",
                userId, diseaseId, remark);
    }

    public void updateUserDiseaseRemark(long id, String remark) {
        jdbc.update("UPDATE user_disease SET remark = ? WHERE id = ?", remark, id);
    }

    public void deleteUserDisease(long id) {
        jdbc.update("DELETE FROM user_disease WHERE id = ?", id);
    }

    // 体重
    public void callRecordWeight(long userId, double weight, Double bodyFat, String measureDate, String note) {
        jdbc.update("CALL sp_record_weight(?, ?, ?, ?, ?)", userId, weight, bodyFat, measureDate, note);
    }

    public Map<String, Object> latestWeightByWeight(long userId, double weight) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT record_id, user_id, weight, body_fat_rate, measure_date, note, created_at " +
                        "FROM weight_record WHERE user_id = ? AND weight = ? ORDER BY created_at DESC LIMIT 1",
                (rs, i) -> Rows.toMap(rs), userId, weight);
        return rows.isEmpty() ? null : rows.get(0);
    }

    public List<Map<String, Object>> listWeights(long userId, int limit, int offset) {
        return jdbc.query(
                "SELECT record_id, user_id, weight, body_fat_rate, measure_date, note, created_at " +
                        "FROM weight_record WHERE user_id = ? ORDER BY measure_date DESC LIMIT ? OFFSET ?",
                (rs, i) -> Rows.toMap(rs), userId, limit, offset);
    }

    public Map<String, Object> latestWeight(long userId) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT record_id, user_id, weight, body_fat_rate, measure_date, note, created_at " +
                        "FROM weight_record WHERE user_id = ? ORDER BY measure_date DESC LIMIT 1",
                (rs, i) -> Rows.toMap(rs), userId);
        return rows.isEmpty() ? null : rows.get(0);
    }

    public Map<String, Object> findWeight(long recordId) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT record_id, user_id, weight, body_fat_rate, measure_date, note, created_at " +
                        "FROM weight_record WHERE record_id = ?",
                (rs, i) -> Rows.toMap(rs), recordId);
        return rows.isEmpty() ? null : rows.get(0);
    }

    public void deleteWeight(long recordId) {
        jdbc.update("DELETE FROM weight_record WHERE record_id = ?", recordId);
    }
}
