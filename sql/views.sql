-- W2：食谱营养视图（应用与 AI 候选召回共用同一份数据库真值）
CREATE OR REPLACE VIEW v_recipe_nutrition AS
SELECT
    r.recipe_id,
    r.recipe_name,
    r.type,
    r.suitable_goals,
    r.user_id,
    r.cook_method,
    r.total_weight,
    r.total_calorie,
    r.base_calorie,
    r.added_calorie,
    r.oil_g,
    r.sauce_g,
    COALESCE(SUM(n.calorie * rf.weight / 100.0), 0) AS ingredient_calorie,
    COALESCE(SUM(n.protein * rf.weight / 100.0), 0) AS protein_g,
    COALESCE(SUM(n.fat * rf.weight / 100.0), 0) AS fat_g,
    COALESCE(SUM(n.carbohydrate * rf.weight / 100.0), 0) AS carbohydrate_g,
    COALESCE(SUM(n.fiber * rf.weight / 100.0), 0) AS fiber_g,
    COALESCE(SUM(n.sugar * rf.weight / 100.0), 0) AS sugar_g,
    COALESCE(SUM(n.sodium * rf.weight / 100.0), 0) AS sodium_mg,
    COUNT(rf.food_id) AS ingredient_count,
    CASE WHEN r.total_weight > 0
         THEN ROUND(r.total_calorie * 100.0 / r.total_weight, 1)
         ELSE 0 END AS calorie_per_100g,
    CASE WHEN r.total_weight > 0
         THEN ROUND(COALESCE(SUM(n.protein * rf.weight / 100.0), 0) * 100.0 / r.total_weight, 1)
         ELSE 0 END AS protein_per_100g
FROM recipe r
LEFT JOIN recipe_food rf ON rf.recipe_id = r.recipe_id
LEFT JOIN nutrition n ON n.food_id = rf.food_id
GROUP BY
    r.recipe_id, r.recipe_name, r.type, r.suitable_goals, r.user_id,
    r.cook_method, r.total_weight, r.total_calorie, r.base_calorie,
    r.added_calorie, r.oil_g, r.sauce_g;
