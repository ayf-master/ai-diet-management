package com.diet.service;

import com.diet.common.DomainException;
import com.diet.repo.FoodRepo;
import com.diet.security.AuthContext;
import com.diet.security.AuthSupport;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
public class FoodService {

    private final FoodRepo foods;
    private final HealthCheckService health;

    public FoodService(FoodRepo foods, HealthCheckService health) {
        this.foods = foods;
        this.health = health;
    }

    public List<Map<String, Object>> listFoods(Long categoryId, String keyword, Long userId) {
        if (userId != null) {
            AuthSupport.ensureSelf(userId);
        }
        AuthContext.Identity me = AuthContext.get();
        List<Map<String, Object>> data = foods.listFoods(categoryId, keyword, me.userId(), me.isAdmin());
        if (userId != null) {
            List<Map<String, Object>> diseases = health.loadUserDiseaseRules(userId);
            if (!diseases.isEmpty()) {
                for (Map<String, Object> f : data) {
                    f.put("health_warning", health.evaluateFood(f, diseases));
                }
            }
        }
        return data;
    }

    public Map<String, Object> getFood(long foodId) {
        Map<String, Object> food = foods.findFood(foodId);
        if (food == null || !AuthSupport.canView((Long) food.get("user_id"))) {
            throw new DomainException(404, "食材不存在");
        }
        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("code", 200);
        resp.put("data", food);
        return resp;
    }

    @Transactional
    public Map<String, Object> createFood(Map<String, Object> data) {
        String name = data.get("food_name") == null ? "" : String.valueOf(data.get("food_name")).trim();
        if (name.isEmpty()) {
            throw new DomainException(400, "食材名称不能为空");
        }
        Long ownerId = toLong(data.get("user_id"));
        if (ownerId != null) {
            AuthSupport.ensureSelf(ownerId);
        } else if (!AuthContext.get().isAdmin()) {
            throw new DomainException(403, "只有管理员能创建系统食材");
        }
        if (foods.dupFood(name, ownerId, null)) {
            throw new DomainException(409, "食材「" + name + "」已存在，请勿重复添加");
        }

        long categoryId = data.get("category_id") == null ? 1L
                : ((Number) toNum(data.get("category_id"))).longValue();
        String unit = data.get("unit") == null ? "100g" : String.valueOf(data.get("unit"));
        long foodId = foods.insertFood(name, categoryId, ownerId, unit, (String) data.get("img_path"));

        @SuppressWarnings("unchecked")
        Map<String, Object> nut = (Map<String, Object>) data.get("nutrition");
        if (nut != null && !nut.isEmpty()) {
            foods.insertNutrition(foodId, nut);
        }

        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("code", 200);
        resp.put("msg", "创建成功");
        resp.put("data", foods.findFood(foodId));
        return resp;
    }

    @Transactional
    public Map<String, Object> updateFood(long foodId, Map<String, Object> data) {
        Map<String, Object> food = foods.findFood(foodId);
        if (food == null) {
            throw new DomainException(404, "食材不存在");
        }
        AuthSupport.ensureEdit((Long) food.get("user_id"));
        if (data == null || data.isEmpty()) {
            throw new DomainException(400, "请求数据为空");
        }
        String newName = data.get("food_name") == null
                ? String.valueOf(food.get("food_name"))
                : String.valueOf(data.get("food_name")).trim();
        if (foods.dupFood(newName, (Long) food.get("user_id"), foodId)) {
            throw new DomainException(409, "食材「" + newName + "」已存在，无法改名成重复名称");
        }
        foods.updateFoodFields(foodId, data);

        @SuppressWarnings("unchecked")
        Map<String, Object> nut = (Map<String, Object>) data.get("nutrition");
        if (nut != null && !nut.isEmpty()) {
            if (food.get("nutrition") != null) {
                foods.updateNutrition(foodId, nut);
            } else {
                foods.insertNutrition(foodId, nut);
            }
        }
        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("code", 200);
        resp.put("msg", "更新成功");
        resp.put("data", foods.findFood(foodId));
        return resp;
    }

    @Transactional
    public Map<String, Object> deleteFood(long foodId) {
        Map<String, Object> food = foods.findFood(foodId);
        if (food == null) {
            throw new DomainException(404, "食材不存在");
        }
        AuthSupport.ensureEdit((Long) food.get("user_id"));
        try {
            foods.deleteFood(foodId);
        } catch (Exception e) {
            throw new DomainException(400, "该食材被食谱引用，无法删除");
        }
        return com.diet.common.ApiResponse.ok("删除成功");
    }

    public Map<String, Object> listCategories() {
        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("code", 200);
        resp.put("data", foods.listCategories());
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

    private static Number toNum(Object v) {
        if (v instanceof Number n) {
            return n;
        }
        try {
            return Double.parseDouble(String.valueOf(v));
        } catch (NumberFormatException e) {
            return 0;
        }
    }
}
