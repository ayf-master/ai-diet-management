package com.diet.repo;

import com.diet.util.Rows;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Repository
public class MealRepo {

    private final JdbcTemplate jdbc;

    public MealRepo(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public List<Map<String, Object>> listMealTypes() {
        return jdbc.query("SELECT type_id, type_name, sort_order FROM meal_type_def ORDER BY sort_order",
                (rs, i) -> Rows.toMap(rs));
    }

    public Map<String, Object> mealTypeById(long typeId) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT type_id, type_name, sort_order FROM meal_type_def WHERE type_id = ?",
                (rs, i) -> Rows.toMap(rs), typeId);
        return rows.isEmpty() ? null : rows.get(0);
    }

    public long insertRecord(long userId, long mealTypeId, String eatDate, String eatTime, String note) {
        jdbc.update("INSERT INTO diet_record (user_id, meal_type_id, eat_date, eat_time, total_cal, note) " +
                        "VALUES (?, ?, ?, ?, 0, ?)", userId, mealTypeId, eatDate, eatTime, note);
        Long id = jdbc.queryForObject(
                "SELECT record_id FROM diet_record WHERE user_id = ? ORDER BY record_id DESC LIMIT 1",
                Long.class, userId);
        return id == null ? 0 : id;
    }

    public void insertDetail(long recordId, long recipeId, double eatWeight, int singleCal,
                             double oilG, double sauceG) {
        jdbc.update("INSERT INTO diet_record_detail (record_id, recipe_id, eat_weight, single_cal, oil_g, sauce_g) " +
                        "VALUES (?, ?, ?, ?, ?, ?)", recordId, recipeId, eatWeight, singleCal, oilG, sauceG);
    }

    public void updateTotalCal(long recordId, int totalCal) {
        jdbc.update("UPDATE diet_record SET total_cal = ? WHERE record_id = ?", totalCal, recordId);
    }

    public Map<String, Object> rawRecord(long recordId) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT * FROM diet_record WHERE record_id = ?",
                (rs, i) -> Rows.toMap(rs), recordId);
        return rows.isEmpty() ? null : rows.get(0);
    }

    // 完整展示结构，对齐 DietRecord.to_dict()
    public Map<String, Object> findById(long recordId) {
        Map<String, Object> record = rawRecord(recordId);
        if (record == null) {
            return null;
        }
        return attachDetails(record);
    }

    public List<Map<String, Object>> listRecords(long userId, String date) {
        StringBuilder sql = new StringBuilder("SELECT * FROM diet_record WHERE user_id = ?");
        java.util.List<Object> args = new java.util.ArrayList<>();
        args.add(userId);
        if (date != null && !date.isEmpty()) {
            sql.append(" AND eat_date = ?");
            args.add(date);
        }
        sql.append(" ORDER BY eat_date DESC, eat_time");
        List<Map<String, Object>> records = jdbc.query(sql.toString(), (rs, i) -> Rows.toMap(rs), args.toArray());
        for (Map<String, Object> r : records) {
            attachDetails(r);
        }
        return records;
    }

    private Map<String, Object> attachDetails(Map<String, Object> record) {
        Object mealTypeId = record.get("meal_type_id");
        Map<String, Object> type = mealTypeId == null ? null
                : mealTypeById(((Number) mealTypeId).longValue());
        record.put("meal_type", type != null ? type.get("type_name") : null);

        List<Map<String, Object>> details = jdbc.query(
                "SELECT d.detail_id, d.recipe_id, r.recipe_name, d.eat_weight, d.single_cal, d.oil_g, d.sauce_g " +
                        "FROM diet_record_detail d LEFT JOIN recipe r ON r.recipe_id = d.recipe_id " +
                        "WHERE d.record_id = ? ORDER BY d.detail_id",
                (rs, i) -> Rows.toMap(rs), record.get("record_id"));
        record.put("details", details);
        return record;
    }

    public void deleteRecord(long recordId) {
        jdbc.update("DELETE FROM diet_record_detail WHERE record_id = ?", recordId);
        jdbc.update("DELETE FROM diet_record WHERE record_id = ?", recordId);
    }

    // 统计
    public List<Map<String, Object>> recordsByDate(long userId, String date) {
        return jdbc.query(
                "SELECT d.*, m.type_name FROM diet_record d LEFT JOIN meal_type_def m ON m.type_id = d.meal_type_id " +
                        "WHERE d.user_id = ? AND d.eat_date = ?",
                (rs, i) -> Rows.toMap(rs), userId, date);
    }

    public List<Map<String, Object>> recordsBetween(long userId, String start, String end) {
        return jdbc.query(
                "SELECT * FROM diet_record WHERE user_id = ? AND eat_date BETWEEN ? AND ? ORDER BY eat_date",
                (rs, i) -> Rows.toMap(rs), userId, start, end);
    }

    public List<Map<String, Object>> weightRecordsBetween(long userId, String start, String end) {
        return jdbc.query(
                "SELECT * FROM weight_record WHERE user_id = ? AND measure_date BETWEEN ? AND ? ORDER BY measure_date",
                (rs, i) -> Rows.toMap(rs), userId, start, end);
    }
}
