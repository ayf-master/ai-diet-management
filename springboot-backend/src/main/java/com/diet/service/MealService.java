package com.diet.service;

import com.diet.common.DomainException;
import com.diet.repo.MealRepo;
import com.diet.repo.RecipeRepo;
import com.diet.security.AuthSupport;
import com.diet.util.NutritionCalc;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

// 打卡用例（对齐 meal_service.py）
@Service
public class MealService {

    private final MealRepo meals;
    private final RecipeRepo recipes;

    public MealService(MealRepo meals, RecipeRepo recipes) {
        this.meals = meals;
        this.recipes = recipes;
    }

    public List<Map<String, Object>> listMealTypes() {
        return meals.listMealTypes();
    }

    @Transactional
    public Map<String, Object> createMeal(Map<String, Object> data, long userId) {
        if (data == null || data.isEmpty()) {
            throw new DomainException(400, "请求数据为空");
        }
        long mealTypeId = data.get("meal_type_id") == null ? 1L
                : ((Number) toNum(data.get("meal_type_id"))).longValue();
        String eatDate = data.get("eat_date") == null
                ? LocalDate.now().toString() : String.valueOf(data.get("eat_date"));
        String eatTime = data.get("eat_time") == null
                ? LocalTime.now().withNano(0).toString() : String.valueOf(data.get("eat_time"));
        String note = data.get("note") == null ? null : String.valueOf(data.get("note"));

        long recordId = meals.insertRecord(userId, mealTypeId, eatDate, eatTime, note);

        int totalCal = 0;
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> details = (List<Map<String, Object>>) data.get("details");
        if (details != null) {
            for (Map<String, Object> item : details) {
                Long recipeId = toLong(item.get("recipe_id"));
                if (recipeId == null) {
                    throw new DomainException(400, "打卡明细缺少 recipe_id");
                }
                Map<String, Object> recipe = recipes.rawById(recipeId);
                // 只打卡自己可见的食谱（系统食谱或本人自建）
                if (recipe == null || !AuthSupport.canView((Long) recipe.get("user_id"))) {
                    continue;
                }
                double weight;
                if (item.get("eat_weight") != null) {
                    weight = numOf(item.get("eat_weight"));
                } else {
                    weight = numOf(recipe.get("total_weight"));
                    if (weight == 0) {
                        weight = 100;
                    }
                }
                NutritionCalc.MealItemTotals calc = NutritionCalc.calcMealItem(
                        numOf(recipe.get("total_weight")),
                        numOf(recipe.get("base_calorie")),
                        numOf(recipe.get("total_calorie")),
                        numOf(recipe.get("oil_g")),
                        numOf(recipe.get("sauce_g")),
                        weight,
                        item.get("oil_g") == null ? null : numOf(item.get("oil_g")),
                        item.get("sauce_g") == null ? null : numOf(item.get("sauce_g")));
                meals.insertDetail(recordId, recipeId, weight, calc.singleCal(), calc.oilG(), calc.sauceG());
                totalCal += calc.singleCal();
            }
        }
        meals.updateTotalCal(recordId, totalCal);
        return meals.findById(recordId);
    }

    public List<Map<String, Object>> listMeals(long userId, String date) {
        return meals.listRecords(userId, date);
    }

    public Map<String, Object> deleteMeal(long recordId) {
        Map<String, Object> record = meals.rawRecord(recordId);
        if (record == null) {
            throw new DomainException(404, "记录不存在");
        }
        AuthSupport.ensureEdit((Long) record.get("user_id"));
        meals.deleteRecord(recordId);
        return com.diet.common.ApiResponse.ok("删除成功");
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
}
