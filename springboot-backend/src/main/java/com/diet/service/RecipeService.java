package com.diet.service;

import com.diet.common.DomainException;
import com.diet.repo.RecipeRepo;
import com.diet.security.AuthContext;
import com.diet.security.AuthSupport;
import com.diet.util.NutritionCalc;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

// 食谱用例：创建/更新/删除、可见性、展示热量、烹饪偏好（对齐 recipe_service.py）
@Service
public class RecipeService {

    private final RecipeRepo recipes;
    private final HealthCheckService health;

    public RecipeService(RecipeRepo recipes, HealthCheckService health) {
        this.recipes = recipes;
        this.health = health;
    }

    public List<Map<String, Object>> listRecipes(String goal, String goals, String mealType,
                                                 String keyword, Long scopeUserId) {
        AuthContext.Identity me = AuthContext.get();
        List<Map<String, Object>> recipesList =
                recipes.listRecipes(me.userId(), me.isAdmin(), goal, goals, mealType, keyword);

        Map<String, Map<String, Object>> prefs = cookingPrefsMap(scopeUserId);
        List<Map<String, Object>> data = new ArrayList<>();
        for (Map<String, Object> r : recipesList) {
            data.add(recipePayload(r, prefs));
        }
        if (scopeUserId != null) {
            List<Map<String, Object>> diseases = health.loadUserDiseaseRules(scopeUserId);
            if (!diseases.isEmpty()) {
                for (int i = 0; i < recipesList.size(); i++) {
                    Map<String, Object> r = recipesList.get(i);
                    data.get(i).put("health_warning", health.evaluateRecipe(
                            ((Number) r.get("recipe_id")).longValue(),
                            (String) r.get("recipe_name"), diseases));
                }
            }
        }
        return data;
    }

    public Map<String, Object> getRecipePayload(long recipeId, Long scopeUserId) {
        Map<String, Object> recipe = recipes.findById(recipeId);
        if (recipe == null || !AuthSupport.canView((Long) recipe.get("user_id"))) {
            throw new DomainException(404, "食谱不存在");
        }
        return recipePayload(recipe, cookingPrefsMap(scopeUserId));
    }

    @Transactional
    public Map<String, Object> createRecipe(Map<String, Object> data) {
        String name = validatedName(data);
        Long ownerId;
        Long adminId = null;
        if (data.get("user_id") != null) {
            ownerId = ((Number) toNum(data.get("user_id"))).longValue();
            AuthSupport.ensureSelf(ownerId);
        } else if (AuthContext.get().isAdmin()) {
            adminId = AuthContext.get().adminId();
            ownerId = null;
        } else {
            ownerId = AuthContext.get().userId();
        }
        if (recipes.dupRecipe(name, ownerId, null)) {
            throw new DomainException(409, "食谱「" + name + "」已存在，请勿重复添加");
        }

        Map<String, Object> r = new LinkedHashMap<>();
        r.put("admin_id", adminId);
        r.put("user_id", ownerId);
        r.put("recipe_name", name);
        r.put("type", data.getOrDefault("type", "午餐"));
        r.put("suitable_goals", data.getOrDefault("suitable_goals", "healthy"));
        r.put("intro", data.get("intro"));
        r.put("cook_method", data.getOrDefault("cook_method", "炒"));
        r.put("forbid_tips", data.get("forbid_tips"));
        r.put("oil_g", numOf(data.get("oil_g")));
        r.put("sauce_g", numOf(data.get("sauce_g")));

        long recipeId = recipes.insertRecipe(r);
        applyIngredients(recipeId, toIngredients(data.get("ingredients")));
        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("code", 200);
        resp.put("msg", "创建成功");
        resp.put("data", recipes.findById(recipeId));
        return resp;
    }

    @Transactional
    public Map<String, Object> updateRecipe(long recipeId, Map<String, Object> data) {
        AuthContext.Identity me = AuthContext.get();
        Map<String, Object> recipe = getEditableRecipe(recipeId);
        if (data == null || data.isEmpty()) {
            throw new DomainException(400, "请求数据为空");
        }
        String newName = data.get("recipe_name") == null
                ? String.valueOf(recipe.get("recipe_name"))
                : String.valueOf(data.get("recipe_name")).trim();
        if (recipes.dupRecipe(newName, (Long) recipe.get("user_id"), recipeId)) {
            throw new DomainException(409, "食谱「" + newName + "」已存在，无法改名成重复名称");
        }

        for (String field : List.of("recipe_name", "type", "suitable_goals", "intro",
                "cook_method", "forbid_tips", "oil_g", "sauce_g")) {
            if (data.containsKey(field)) {
                recipe.put(field, data.get(field) == null || "".equals(data.get(field))
                        ? (field.equals("oil_g") || field.equals("sauce_g") ? 0 : data.get(field))
                        : data.get(field));
            }
        }
        // oil_g/sauce_g 允许显式清零
        recipe.put("oil_g", data.containsKey("oil_g") ? numOf(data.get("oil_g")) : recipe.get("oil_g"));
        recipe.put("sauce_g", data.containsKey("sauce_g") ? numOf(data.get("sauce_g")) : recipe.get("sauce_g"));
        recipes.updateRecipeFields(recipeId, recipe);

        if (data.containsKey("ingredients")) {
            applyIngredients(recipeId, toIngredients(data.get("ingredients")));
        } else if (data.containsKey("cook_method")) {
            // 只改烹饪方式：用现有食材重算基础热量，再叠加新做法附加热量
            recalcFromExisting(recipeId, recipe);
        }
        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("code", 200);
        resp.put("msg", "更新成功");
        resp.put("data", recipes.findById(recipeId));
        return resp;
    }

    @Transactional
    public Map<String, Object> deleteRecipe(long recipeId) {
        getEditableRecipe(recipeId);
        try {
            recipes.deleteRecipeFoods(recipeId);
            recipes.deleteRecipe(recipeId);
        } catch (Exception e) {
            throw new DomainException(400, "该食谱被打卡记录引用，无法删除");
        }
        return com.diet.common.ApiResponse.ok("删除成功");
    }

    private Map<String, Object> getEditableRecipe(long recipeId) {
        Map<String, Object> recipe = recipes.rawById(recipeId);
        if (recipe == null) {
            throw new DomainException(404, "食谱不存在");
        }
        Long ownerId = (Long) recipe.get("user_id");
        if (!AuthSupport.canEdit(ownerId)) {
            if (ownerId == null) {
                throw new DomainException(403, "系统数据仅管理员可修改");
            }
            throw new DomainException(403, "无权操作该食谱");
        }
        return recipe;
    }

    // 写入 RecipeFood 并重算热量四项
    private void applyIngredients(long recipeId, List<Map<String, Object>> ingredients) {
        List<NutritionCalc.Ingredient> inputs = new ArrayList<>();
        for (Map<String, Object> item : ingredients) {
            Long foodId = toLong(item.get("food_id"));
            if (foodId == null) {
                throw new DomainException(400, "食材参数错误：缺少 food_id");
            }
            if (recipes.findFood(foodId) == null) {
                throw new DomainException(400, "食材 " + foodId + " 不存在");
            }
            double weight = numOf(item.get("weight"));
            recipes.insertRecipeFood(recipeId, foodId, weight);
            inputs.add(new NutritionCalc.Ingredient(weight, recipes.foodCaloriePer100g(foodId)));
        }
        applyTotals(recipeId, inputs);
    }

    private void recalcFromExisting(long recipeId, Map<String, Object> recipe) {
        List<NutritionCalc.Ingredient> inputs = new ArrayList<>();
        for (Map<String, Object> ing : recipes.ingredientsOf(recipeId)) {
            Long foodId = toLong(ing.get("food_id"));
            inputs.add(new NutritionCalc.Ingredient(numOf(ing.get("weight")), recipes.foodCaloriePer100g(foodId)));
        }
        applyTotals(recipeId, inputs);
    }

    private void applyTotals(long recipeId, List<NutritionCalc.Ingredient> inputs) {
        Map<String, Object> recipe = recipes.rawById(recipeId);
        double oilG = numOf(recipe.get("oil_g"));
        double sauceG = numOf(recipe.get("sauce_g"));
        String cookMethod = (String) recipe.get("cook_method");
        double oilPer100g = 0;
        double saucePer100g = 0;
        Map<String, Object> cm = recipes.findCookingMethod(cookMethod);
        if (cm != null) {
            oilPer100g = numOf(cm.get("oil_per_100g"));
            saucePer100g = numOf(cm.get("sauce_kcal_per_100g"));
        }
        NutritionCalc.RecipeTotals totals =
                NutritionCalc.calcRecipeTotals(inputs, oilG, sauceG, oilPer100g, saucePer100g);
        recipes.updateRecipeTotals(recipeId, totals.totalWeight(), totals.baseCalorie(),
                totals.addedCalorie(), totals.totalCalorie());
    }

    // 展示用热量：用户偏好覆盖烹饪方式系数（不写库）
    private Map<String, Object> recipePayload(Map<String, Object> recipe, Map<String, Map<String, Object>> prefs) {
        Map<String, Object> data = new LinkedHashMap<>(recipe);
        double base = numOf(recipe.get("base_calorie"));
        double oilG = numOf(recipe.get("oil_g"));
        double sauceG = numOf(recipe.get("sauce_g"));
        if (oilG > 0 || sauceG > 0) {
            int added = NutritionCalc.addedCaloriesFromGrams(oilG, sauceG);
            data.put("added_calorie", added);
            data.put("total_calorie", Math.round(base + added));
            return data;
        }
        Map<String, Object> pref = prefs.get((String) recipe.get("cook_method"));
        double totalWeight = numOf(recipe.get("total_weight"));
        if (pref != null && totalWeight > 0) {
            double addedRaw = NutritionCalc.addedCaloriesFromCookMethodRaw(
                    totalWeight, numOf(pref.get("oil_per_100g")), numOf(pref.get("sauce_kcal_per_100g")));
            data.put("added_calorie", Math.round(addedRaw));
            data.put("total_calorie", Math.round(base + addedRaw));
        }
        return data;
    }

    private Map<String, Map<String, Object>> cookingPrefsMap(Long userId) {
        Map<String, Map<String, Object>> map = new LinkedHashMap<>();
        if (userId == null) {
            return map;
        }
        for (Map<String, Object> p : recipes.userCookingPrefs(userId)) {
            map.put((String) p.get("cook_method"), p);
        }
        return map;
    }

    public Map<String, Object> getCookingPrefs(Long userId) {
        if (userId == null) {
            throw new DomainException(400, "缺少user_id");
        }
        AuthSupport.ensureSelf(userId);
        Map<String, Map<String, Object>> prefs = cookingPrefsMap(userId);
        List<Map<String, Object>> data = new ArrayList<>();
        for (Map<String, Object> cm : recipes.allCookingMethods()) {
            String method = (String) cm.get("cook_method");
            Map<String, Object> up = prefs.get(method);
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("cook_method", method);
            item.put("oil_per_100g", up != null ? up.get("oil_per_100g") : cm.get("oil_per_100g"));
            item.put("sauce_kcal_per_100g", up != null ? up.get("sauce_kcal_per_100g") : cm.get("sauce_kcal_per_100g"));
            item.put("is_custom", up != null);
            data.add(item);
        }
        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("code", 200);
        resp.put("data", data);
        return resp;
    }

    @Transactional
    public Map<String, Object> saveCookingPrefs(Long userId, List<Map<String, Object>> prefs) {
        if (userId == null) {
            throw new DomainException(400, "缺少user_id");
        }
        AuthSupport.ensureSelf(userId);
        recipes.deleteCookingPrefs(userId);
        if (prefs != null) {
            for (Map<String, Object> item : prefs) {
                String method = item.get("cook_method") == null ? null : String.valueOf(item.get("cook_method"));
                if (method == null || method.isEmpty()) {
                    continue;
                }
                recipes.insertCookingPref(userId, method, numOf(item.get("oil_per_100g")),
                        numOf(item.get("sauce_kcal_per_100g")));
            }
        }
        return com.diet.common.ApiResponse.ok("保存成功");
    }

    @Transactional
    public Map<String, Object> resetCookingPrefs(Long userId) {
        if (userId == null) {
            throw new DomainException(400, "缺少user_id");
        }
        AuthSupport.ensureSelf(userId);
        recipes.deleteCookingPrefs(userId);
        return com.diet.common.ApiResponse.ok("已重置为默认");
    }

    public Map<String, Object> listCookingMethods() {
        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("code", 200);
        resp.put("data", recipes.listCookingMethods());
        return resp;
    }

    private static String validatedName(Map<String, Object> data) {
        String name = data.get("recipe_name") == null ? "" : String.valueOf(data.get("recipe_name")).trim();
        if (name.isEmpty()) {
            throw new DomainException(400, "食谱名称不能为空");
        }
        return name;
    }

    @SuppressWarnings("unchecked")
    private static List<Map<String, Object>> toIngredients(Object raw) {
        if (raw == null) {
            return List.of();
        }
        if (!(raw instanceof List)) {
            throw new DomainException(400, "ingredients 必须是数组");
        }
        List<Map<String, Object>> out = new ArrayList<>();
        for (Object item : (List<Object>) raw) {
            if (item instanceof Map<?, ?> m) {
                out.add((Map<String, Object>) m);
            } else {
                throw new DomainException(400, "食材参数错误：缺少 food_id");
            }
        }
        return out;
    }

    private static double numOf(Object v) {
        if (v instanceof Number n) {
            return n.doubleValue();
        }
        if (v instanceof String s && !s.isEmpty()) {
            try {
                return Double.parseDouble(s);
            } catch (NumberFormatException ignored) {
            }
        }
        return 0;
    }

    private static Long toLong(Object v) {
        if (v instanceof Number n) {
            return n.longValue();
        }
        try {
            return Long.parseLong(String.valueOf(v));
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private static double toNum(Object v) {
        if (v instanceof Number n) {
            return n.doubleValue();
        }
        try {
            return Double.parseDouble(String.valueOf(v));
        } catch (NumberFormatException e) {
            return 0;
        }
    }
}
