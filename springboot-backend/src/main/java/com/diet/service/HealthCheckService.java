package com.diet.service;

import com.diet.repo.FoodRepo;
import com.diet.repo.MiscRepo;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

// 按用户所选疾病判定食材/食谱健康风险；系统与自建食材共用同一逻辑
@Service
public class HealthCheckService {

    private static final List<String> NUTRI_FIELDS =
            List.of("calorie", "protein", "fat", "carbohydrate", "fiber", "sugar", "sodium");

    private final MiscRepo misc;
    private final FoodRepo foodRepo;

    public HealthCheckService(MiscRepo misc, FoodRepo foodRepo) {
        this.misc = misc;
        this.foodRepo = foodRepo;
    }

    // [{name, keywords:[], rules:{}}]
    public List<Map<String, Object>> loadUserDiseaseRules(Long userId) {
        if (userId == null) {
            return List.of();
        }
        List<Map<String, Object>> out = new ArrayList<>();
        for (Map<String, Object> rule : misc.userDiseaseRules(userId)) {
            out.add(rule);
        }
        return out;
    }

    // [{disease_name, forbid_desc, forbid_keywords, forbid_rules, remark}]
    public List<Map<String, Object>> loadUserDiseases(Long userId) {
        if (userId == null) {
            return List.of();
        }
        return misc.userDiseasesWithRemark(userId);
    }

    // 对一份「每100g营养」做判定，返回 {level, reasons}
    public Map<String, Object> evaluateNutrition(String name, Map<String, Object> nutrition,
                                                 List<Map<String, Object>> diseases) {
        Map<String, Object> result = new LinkedHashMap<>();
        List<String> reasons = new ArrayList<>();
        String level = "ok";
        if (diseases == null || diseases.isEmpty()) {
            result.put("level", "ok");
            result.put("reasons", reasons);
            return result;
        }
        String safeName = name == null ? "" : name;
        for (Map<String, Object> d : diseases) {
            @SuppressWarnings("unchecked")
            List<String> keywords = (List<String>) d.get("keywords");
            if (keywords != null) {
                for (String kw : keywords) {
                    if (kw != null && !kw.isEmpty() && safeName.contains(kw)) {
                        reasons.add(d.get("name") + "：名称含「" + kw + "」");
                        level = upgrade(level, "warn");
                    }
                }
            }
            @SuppressWarnings("unchecked")
            Map<String, Object> rules = (Map<String, Object>) d.get("rules");
            if (rules == null) {
                continue;
            }
            double sugar = numOf(nutrition, "sugar");
            double sodium = numOf(nutrition, "sodium");
            double fat = numOf(nutrition, "fat");
            double carb = numOf(nutrition, "carbohydrate");
            Double maxSugar = asDouble(rules.get("max_sugar"));
            Double maxSodium = asDouble(rules.get("max_sodium"));
            Double maxFat = asDouble(rules.get("max_fat"));
            Double maxCarb = asDouble(rules.get("max_carbohydrate"));
            if (maxSugar != null && sugar > maxSugar) {
                reasons.add(d.get("name") + "：糖分过高（" + sugar + "g/100g）");
                level = upgrade(level, "warn");
            }
            if (maxSodium != null && sodium > maxSodium) {
                reasons.add(d.get("name") + "：钠偏高（" + sodium + "mg/100g）");
                level = upgrade(level, "warn");
            }
            if (maxFat != null && fat > maxFat) {
                reasons.add(d.get("name") + "：脂肪偏高（" + fat + "g/100g）");
                level = upgrade(level, "danger");
            }
            if (maxCarb != null && carb > maxCarb) {
                reasons.add(d.get("name") + "：碳水偏高（" + carb + "g/100g）");
                level = upgrade(level, "warn");
            }
        }
        result.put("level", level);
        result.put("reasons", reasons);
        return result;
    }

    // 判定单个食材：food dict 含 food_name 与 nutrition
    public Map<String, Object> evaluateFood(Map<String, Object> food, List<Map<String, Object>> diseases) {
        @SuppressWarnings("unchecked")
        Map<String, Object> nutrition = (Map<String, Object>) food.get("nutrition");
        return evaluateNutrition((String) food.get("food_name"), nutrition, diseases);
    }

    // 判定食谱：食材配比加权聚合后折算每100g再判定
    public Map<String, Object> evaluateRecipe(long recipeId, String recipeName,
                                              List<Map<String, Object>> diseases) {
        if (diseases == null || diseases.isEmpty()) {
            return Map.of("level", "ok", "reasons", List.of());
        }
        double[] total = new double[NUTRI_FIELDS.size()];
        double totalWeight = 0;
        for (Map<String, Object> ing : foodRepo.recipeIngredientNutrition(recipeId)) {
            double w = numOf(ing, "weight");
            totalWeight += w;
            Map<String, Object> nutrition = (Map<String, Object>) ing.get("nutrition");
            if (nutrition != null) {
                for (int i = 0; i < NUTRI_FIELDS.size(); i++) {
                    double v = numOf(nutrition, NUTRI_FIELDS.get(i));
                    total[i] += v * w / 100.0;
                }
            }
        }
        Map<String, Object> per100 = new LinkedHashMap<>();
        if (totalWeight > 0) {
            for (int i = 0; i < NUTRI_FIELDS.size(); i++) {
                per100.put(NUTRI_FIELDS.get(i), Math.round(total[i] / totalWeight * 10000.0) / 100.0);
            }
        }
        return evaluateNutrition(recipeName, per100, diseases);
    }

    private static String upgrade(String cur, String next) {
        int orderCur = order(cur);
        int orderNew = order(next);
        return orderNew > orderCur ? next : cur;
    }

    private static int order(String level) {
        return switch (level) {
            case "warn" -> 1;
            case "danger" -> 2;
            default -> 0;
        };
    }

    static double numOf(Map<String, Object> m, String key) {
        if (m == null) {
            return 0;
        }
        Object v = m.get(key);
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

    static Double asDouble(Object v) {
        if (v instanceof Number n) {
            return n.doubleValue();
        }
        if (v instanceof String s && !s.isEmpty()) {
            try {
                return Double.parseDouble(s);
            } catch (NumberFormatException ignored) {
            }
        }
        return null;
    }
}
