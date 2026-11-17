package com.diet.repo;

import com.diet.util.Rows;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Repository
public class FoodRepo {

    private final JdbcTemplate jdbc;

    public FoodRepo(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public List<Map<String, Object>> listFoods(Long categoryId, String keyword, Long viewerId, boolean admin) {
        StringBuilder sql = new StringBuilder(
                "SELECT f.food_id, f.food_name, f.category_id, f.user_id, c.category_name, f.unit, " +
                        "f.img_path, f.created_at FROM food f " +
                        "LEFT JOIN food_category c ON c.category_id = f.category_id WHERE 1=1");
        java.util.List<Object> args = new java.util.ArrayList<>();
        if (!admin && viewerId != null) {
            sql.append(" AND (f.user_id IS NULL OR f.user_id = ?)");
            args.add(viewerId);
        }
        if (categoryId != null) {
            sql.append(" AND f.category_id = ?");
            args.add(categoryId);
        }
        if (keyword != null && !keyword.isEmpty()) {
            sql.append(" AND f.food_name LIKE ?");
            args.add("%" + keyword + "%");
        }
        sql.append(" ORDER BY f.food_id");
        List<Map<String, Object>> foods = jdbc.query(sql.toString(), (rs, i) -> Rows.toMap(rs), args.toArray());
        for (Map<String, Object> f : foods) {
            f.put("nutrition", nutritionOf(((Number) f.get("food_id")).longValue()));
        }
        return foods;
    }

    public Map<String, Object> findFood(long foodId) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT f.food_id, f.food_name, f.category_id, f.user_id, c.category_name, f.unit, " +
                        "f.img_path, f.created_at FROM food f " +
                        "LEFT JOIN food_category c ON c.category_id = f.category_id WHERE f.food_id = ?",
                (rs, i) -> Rows.toMap(rs), foodId);
        if (rows.isEmpty()) {
            return null;
        }
        Map<String, Object> food = rows.get(0);
        food.put("nutrition", nutritionOf(foodId));
        return food;
    }

    // nutrition 仅业务字段，对齐 Python Nutrition.to_dict()
    public Map<String, Object> nutritionOf(long foodId) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT calorie, protein, fat, carbohydrate, fiber, sugar, sodium FROM nutrition WHERE food_id = ?",
                (rs, i) -> Rows.toMap(rs), foodId);
        return rows.isEmpty() ? null : rows.get(0);
    }

    public List<Map<String, Object>> listCategories() {
        return jdbc.query("SELECT category_id, category_name, sort_order FROM food_category ORDER BY sort_order",
                (rs, i) -> Rows.toMap(rs));
    }

    public boolean dupFood(String name, Long userId, Long excludeId) {
        StringBuilder sql = new StringBuilder(
                "SELECT COUNT(*) FROM food WHERE LOWER(TRIM(food_name)) = ?");
        java.util.List<Object> args = new java.util.ArrayList<>();
        args.add(name == null ? "" : name.trim().toLowerCase());
        if (userId != null && userId != 0) {
            sql.append(" AND (user_id IS NULL OR user_id = ?)");
            args.add(userId);
        }
        if (excludeId != null) {
            sql.append(" AND food_id <> ?");
            args.add(excludeId);
        }
        Integer count = jdbc.queryForObject(sql.toString(), Integer.class, args.toArray());
        return count != null && count > 0;
    }

    public long insertFood(String name, long categoryId, Long userId, String unit, String imgPath) {
        jdbc.update("INSERT INTO food (food_name, category_id, user_id, unit, img_path) VALUES (?, ?, ?, ?, ?)",
                name, categoryId, userId, unit, imgPath);
        Long id = jdbc.queryForObject(
                "SELECT food_id FROM food WHERE food_name = ? AND category_id = ? AND (? IS NULL OR user_id = ?) " +
                        "ORDER BY food_id DESC LIMIT 1",
                Long.class, name, categoryId, userId, userId);
        return id == null ? 0 : id;
    }

    public long insertNutrition(long foodId, Map<String, Object> nut) {
        jdbc.update("""
                        INSERT INTO nutrition (food_id, calorie, protein, fat, carbohydrate, fiber, sugar, sodium)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                foodId, numOf(nut.get("calorie"), 0), numOf(nut.get("protein"), 0),
                numOf(nut.get("fat"), 0), numOf(nut.get("carbohydrate"), 0),
                numOf(nut.get("fiber"), 0), numOf(nut.get("sugar"), 0), numOf(nut.get("sodium"), 0));
        return foodId;
    }

    public void updateNutrition(long foodId, Map<String, Object> nut) {
        if (nut.containsKey("calorie")) {
            jdbc.update("UPDATE nutrition SET calorie = ? WHERE food_id = ?", nut.get("calorie"), foodId);
        }
        if (nut.containsKey("protein")) {
            jdbc.update("UPDATE nutrition SET protein = ? WHERE food_id = ?", nut.get("protein"), foodId);
        }
        if (nut.containsKey("fat")) {
            jdbc.update("UPDATE nutrition SET fat = ? WHERE food_id = ?", nut.get("fat"), foodId);
        }
        if (nut.containsKey("carbohydrate")) {
            jdbc.update("UPDATE nutrition SET carbohydrate = ? WHERE food_id = ?", nut.get("carbohydrate"), foodId);
        }
        if (nut.containsKey("fiber")) {
            jdbc.update("UPDATE nutrition SET fiber = ? WHERE food_id = ?", nut.get("fiber"), foodId);
        }
        if (nut.containsKey("sugar")) {
            jdbc.update("UPDATE nutrition SET sugar = ? WHERE food_id = ?", nut.get("sugar"), foodId);
        }
        if (nut.containsKey("sodium")) {
            jdbc.update("UPDATE nutrition SET sodium = ? WHERE food_id = ?", nut.get("sodium"), foodId);
        }
    }

    public void updateFoodFields(long foodId, Map<String, Object> data) {
        if (data.containsKey("food_name")) {
            jdbc.update("UPDATE food SET food_name = ? WHERE food_id = ?", data.get("food_name"), foodId);
        }
        if (data.containsKey("category_id")) {
            jdbc.update("UPDATE food SET category_id = ? WHERE food_id = ?", data.get("category_id"), foodId);
        }
        if (data.containsKey("unit")) {
            jdbc.update("UPDATE food SET unit = ? WHERE food_id = ?", data.get("unit"), foodId);
        }
        if (data.containsKey("img_path")) {
            jdbc.update("UPDATE food SET img_path = ? WHERE food_id = ?", data.get("img_path"), foodId);
        }
    }

    public void deleteFood(long foodId) {
        jdbc.update("DELETE FROM nutrition WHERE food_id = ?", foodId);
        jdbc.update("DELETE FROM food WHERE food_id = ?", foodId);
    }

    // 食谱食材营养输入，供 evaluateRecipe / 热量重算
    public List<Map<String, Object>> recipeIngredientNutrition(long recipeId) {
        return jdbc.query(
                "SELECT rf.weight, n.calorie, n.protein, n.fat, n.carbohydrate, n.fiber, n.sugar, n.sodium " +
                        "FROM recipe_food rf LEFT JOIN nutrition n ON n.food_id = rf.food_id " +
                        "WHERE rf.recipe_id = ?",
                (rs, i) -> {
                    Map<String, Object> m = Rows.toMap(rs);
                    Map<String, Object> nut = new LinkedHashMap<>();
                    nut.put("calorie", m.get("calorie"));
                    nut.put("protein", m.get("protein"));
                    nut.put("fat", m.get("fat"));
                    nut.put("carbohydrate", m.get("carbohydrate"));
                    nut.put("fiber", m.get("fiber"));
                    nut.put("sugar", m.get("sugar"));
                    nut.put("sodium", m.get("sodium"));
                    Map<String, Object> out = new LinkedHashMap<>();
                    out.put("weight", m.get("weight"));
                    out.put("nutrition", nut);
                    return out;
                }, recipeId);
    }

    private static double numOf(Object v, double def) {
        if (v instanceof Number n) {
            return n.doubleValue();
        }
        if (v instanceof String s && !s.isEmpty()) {
            try {
                return Double.parseDouble(s);
            } catch (NumberFormatException ignored) {
            }
        }
        return def;
    }
}
