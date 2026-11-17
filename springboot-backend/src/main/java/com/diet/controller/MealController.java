package com.diet.controller;

import com.diet.service.MealService;
import com.diet.service.StatsService;
import org.springframework.web.bind.annotation.*;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class MealController {

    private final MealService meals;
    private final StatsService stats;

    public MealController(MealService meals, StatsService stats) {
        this.meals = meals;
        this.stats = stats;
    }

    @GetMapping("/meal-types")
    public Map<String, Object> mealTypes() {
        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("code", 200);
        resp.put("data", meals.listMealTypes());
        return resp;
    }

    @PostMapping("/meals")
    public Map<String, Object> create(@RequestBody(required = false) Map<String, Object> data) {
        if (data == null) {
            data = Map.of();
        }
        Long userId = com.diet.security.AuthSupport.resolveUserId(
                data.get("user_id") == null ? null : toLong(data.get("user_id")));
        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("code", 200);
        resp.put("msg", "打卡成功");
        resp.put("data", meals.createMeal(data, userId));
        return resp;
    }

    @GetMapping("/meals")
    public Map<String, Object> list(@RequestParam(required = false) Long user_id,
                                    @RequestParam(required = false, defaultValue = "") String date) {
        Long userId = com.diet.security.AuthSupport.resolveUserId(user_id);
        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("code", 200);
        resp.put("data", meals.listMeals(userId, date));
        return resp;
    }

    @DeleteMapping("/meals/{recordId}")
    public Map<String, Object> delete(@PathVariable long recordId) {
        return meals.deleteMeal(recordId);
    }

    @GetMapping("/stats/daily")
    public Map<String, Object> daily(@RequestParam(required = false) Long user_id,
                                     @RequestParam(required = false) String date) {
        Long userId = com.diet.security.AuthSupport.resolveUserId(user_id);
        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("code", 200);
        resp.put("data", stats.dailyStats(userId, date));
        return resp;
    }

    @GetMapping("/stats/weekly")
    public Map<String, Object> weekly(@RequestParam(required = false) Long user_id) {
        Long userId = com.diet.security.AuthSupport.resolveUserId(user_id);
        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("code", 200);
        resp.put("data", stats.weeklyStats(userId, null));
        return resp;
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
