package com.diet.repo;

import com.diet.util.Rows;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Repository
public class RecipeRepo {

    private final JdbcTemplate jdbc;

    public RecipeRepo(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public Map<String, Object> rawById(long recipeId) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT * FROM recipe WHERE recipe_id = ?",
                (rs, i) -> Rows.toMap(rs), recipeId);
        return rows.isEmpty() ? null : rows.get(0);
    }

    // 附 ingredients 的完整展示结构，对齐 Python Recipe.to_dict()
    public Map<String, Object> findById(long recipeId) {
        Map<String, Object> recipe = rawById(recipeId);
        if (recipe == null) {
            return null;
        }
        recipe.put("ingredients", ingredientsOf(recipeId));
        return recipe;
    }

    public List<Map<String, Object>> ingredientsOf(long recipeId) {
        return jdbc.query(
                "SELECT rf.food_id, f.food_name, rf.weight, n.calorie FROM recipe_food rf " +
                        "LEFT JOIN food f ON f.food_id = rf.food_id " +
                        "LEFT JOIN nutrition n ON n.food_id = rf.food_id WHERE rf.recipe_id = ? ORDER BY rf.id",
                (rs, i) -> {
                    Map<String, Object> m = Rows.toMap(rs);
                    Object cal = m.get("calorie");
                    Object weight = m.get("weight");
                    if (cal instanceof Number c && weight instanceof Number w) {
                        m.put("calorie", Math.round(c.doubleValue() * w.doubleValue() / 100));
                    } else {
                        m.put("calorie", 0);
                    }
                    return m;
                }, recipeId);
    }

    public List<Map<String, Object>> listRecipes(Long viewerId, boolean admin, String goal, String goals,
                                                 String mealType, String keyword) {
        StringBuilder sql = new StringBuilder("SELECT * FROM recipe WHERE 1=1");
        java.util.List<Object> args = new java.util.ArrayList<>();
        if (!admin && viewerId != null) {
            sql.append(" AND (user_id IS NULL OR user_id = ?)");
            args.add(viewerId);
        }
        if (goals != null && !goals.isEmpty()) {
            StringBuilder cond = new StringBuilder(" AND (");
            for (String g : goals.split(",")) {
                String t = g.trim();
                if (t.isEmpty()) {
                    continue;
                }
                if (cond.length() > 7) {
                    cond.append(" OR ");
                }
                cond.append("suitable_goals LIKE ?");
                args.add("%" + t + "%");
            }
            cond.append(")");
            if (args.size() > (admin ? 0 : 1)) {
                sql.append(cond);
            }
        } else if (goal != null && !goal.isEmpty()) {
            sql.append(" AND suitable_goals LIKE ?");
            args.add("%" + goal + "%");
        }
        if (mealType != null && !mealType.isEmpty()) {
            sql.append(" AND type = ?");
            args.add(mealType);
        }
        if (keyword != null && !keyword.isEmpty()) {
            sql.append(" AND recipe_name LIKE ?");
            args.add("%" + keyword + "%");
        }
        sql.append(" ORDER BY recipe_id");
        List<Map<String, Object>> recipes = jdbc.query(sql.toString(), (rs, i) -> Rows.toMap(rs), args.toArray());
        for (Map<String, Object> r : recipes) {
            r.put("ingredients", ingredientsOf(((Number) r.get("recipe_id")).longValue()));
        }
        return recipes;
    }

    public boolean dupRecipe(String name, Long ownerId, Long excludeId) {
        StringBuilder sql = new StringBuilder(
                "SELECT COUNT(*) FROM recipe WHERE LOWER(TRIM(recipe_name)) = ?");
        java.util.List<Object> args = new java.util.ArrayList<>();
        args.add(name == null ? "" : name.trim().toLowerCase());
        if (ownerId != null) {
            sql.append(" AND (user_id IS NULL OR user_id = ?)");
            args.add(ownerId);
        }
        if (excludeId != null) {
            sql.append(" AND recipe_id <> ?");
            args.add(excludeId);
        }
        Integer count = jdbc.queryForObject(sql.toString(), Integer.class, args.toArray());
        return count != null && count > 0;
    }

    public long insertRecipe(Map<String, Object> r) {
        jdbc.update("""
                        INSERT INTO recipe (admin_id, user_id, recipe_name, type, suitable_goals, intro,
                            cook_method, forbid_tips, total_calorie, added_calorie, base_calorie,
                            total_weight, oil_g, sauce_g)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, 0, ?, ?)
                        """,
                r.get("admin_id"), r.get("user_id"), r.get("recipe_name"), r.get("type"),
                r.get("suitable_goals"), r.get("intro"), r.get("cook_method"),
                r.get("forbid_tips"), r.get("oil_g"), r.get("sauce_g"));
        Long id = jdbc.queryForObject(
                "SELECT recipe_id FROM recipe WHERE recipe_name = ? AND (? IS NULL OR user_id = ?) " +
                        "ORDER BY recipe_id DESC LIMIT 1",
                Long.class, r.get("recipe_name"), r.get("user_id"), r.get("user_id"));
        return id == null ? 0 : id;
    }

    public void updateRecipeFields(long recipeId, Map<String, Object> data) {
        if (data.containsKey("recipe_name")) {
            jdbc.update("UPDATE recipe SET recipe_name = ? WHERE recipe_id = ?", data.get("recipe_name"), recipeId);
        }
        if (data.containsKey("type")) {
            jdbc.update("UPDATE recipe SET type = ? WHERE recipe_id = ?", data.get("type"), recipeId);
        }
        if (data.containsKey("suitable_goals")) {
            jdbc.update("UPDATE recipe SET suitable_goals = ? WHERE recipe_id = ?", data.get("suitable_goals"), recipeId);
        }
        if (data.containsKey("intro")) {
            jdbc.update("UPDATE recipe SET intro = ? WHERE recipe_id = ?", data.get("intro"), recipeId);
        }
        if (data.containsKey("cook_method")) {
            jdbc.update("UPDATE recipe SET cook_method = ? WHERE recipe_id = ?", data.get("cook_method"), recipeId);
        }
        if (data.containsKey("forbid_tips")) {
            jdbc.update("UPDATE recipe SET forbid_tips = ? WHERE recipe_id = ?", data.get("forbid_tips"), recipeId);
        }
        if (data.containsKey("oil_g")) {
            jdbc.update("UPDATE recipe SET oil_g = ? WHERE recipe_id = ?", data.get("oil_g"), recipeId);
        }
        if (data.containsKey("sauce_g")) {
            jdbc.update("UPDATE recipe SET sauce_g = ? WHERE recipe_id = ?", data.get("sauce_g"), recipeId);
        }
    }

    public void updateRecipeTotals(long recipeId, double totalWeight, int baseCalorie, int addedCalorie, int totalCalorie) {
        jdbc.update("UPDATE recipe SET total_weight = ?, base_calorie = ?, added_calorie = ?, total_calorie = ? " +
                        "WHERE recipe_id = ?",
                totalWeight, baseCalorie, addedCalorie, totalCalorie, recipeId);
    }

    public void deleteRecipeFoods(long recipeId) {
        jdbc.update("DELETE FROM recipe_food WHERE recipe_id = ?", recipeId);
    }

    public void deleteRecipe(long recipeId) {
        jdbc.update("DELETE FROM recipe WHERE recipe_id = ?", recipeId);
    }

    public void insertRecipeFood(long recipeId, long foodId, double weight) {
        jdbc.update("INSERT INTO recipe_food (recipe_id, food_id, weight) VALUES (?, ?, ?)",
                recipeId, foodId, weight);
    }

    public Double foodCaloriePer100g(long foodId) {
        List<Double> rows = jdbc.query(
                "SELECT calorie FROM nutrition WHERE food_id = ?",
                (rs, i) -> rs.getDouble(1), foodId);
        return rows.isEmpty() ? null : rows.get(0);
    }

    public Map<String, Object> findFood(long foodId) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT food_id, food_name FROM food WHERE food_id = ?",
                (rs, i) -> Rows.toMap(rs), foodId);
        return rows.isEmpty() ? null : rows.get(0);
    }

    public Map<String, Object> findCookingMethod(String cookMethod) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT cook_method, oil_per_100g, sauce_kcal_per_100g, description FROM cooking_method " +
                        "WHERE cook_method = ?",
                (rs, i) -> Rows.toMap(rs), cookMethod);
        return rows.isEmpty() ? null : rows.get(0);
    }

    public List<String> listCookingMethods() {
        return jdbc.query("SELECT cook_method FROM cooking_method ORDER BY cook_method",
                (rs, i) -> rs.getString(1));
    }

    public List<Map<String, Object>> userCookingPrefs(long userId) {
        return jdbc.query(
                "SELECT user_id, cook_method, oil_per_100g, sauce_kcal_per_100g FROM user_cooking_pref " +
                        "WHERE user_id = ?",
                (rs, i) -> Rows.toMap(rs), userId);
    }

    public List<Map<String, Object>> allCookingMethods() {
        return jdbc.query(
                "SELECT cook_method, oil_per_100g, sauce_kcal_per_100g, description FROM cooking_method " +
                        "ORDER BY cook_method",
                (rs, i) -> Rows.toMap(rs));
    }

    public void deleteCookingPrefs(long userId) {
        jdbc.update("DELETE FROM user_cooking_pref WHERE user_id = ?", userId);
    }

    public void insertCookingPref(long userId, String cookMethod, double oilPer100g, double sauceKcalPer100g) {
        jdbc.update("INSERT INTO user_cooking_pref (user_id, cook_method, oil_per_100g, sauce_kcal_per_100g) " +
                        "VALUES (?, ?, ?, ?)",
                userId, cookMethod, oilPer100g, sauceKcalPer100g);
    }

    private static Map<String, Object> newMap() {
        return new LinkedHashMap<>();
    }
}
