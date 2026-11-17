package com.diet.controller;

import com.diet.service.FoodService;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api")
public class FoodController {

    private final FoodService foods;

    public FoodController(FoodService foods) {
        this.foods = foods;
    }

    @GetMapping("/foods")
    public Map<String, Object> list(@RequestParam(required = false) Long category_id,
                                    @RequestParam(required = false, defaultValue = "") String keyword,
                                    @RequestParam(required = false) Long user_id) {
        Map<String, Object> resp = new java.util.LinkedHashMap<>();
        resp.put("code", 200);
        resp.put("data", foods.listFoods(category_id, keyword, user_id));
        return resp;
    }

    @GetMapping("/foods/{foodId}")
    public Map<String, Object> get(@PathVariable long foodId) {
        return foods.getFood(foodId);
    }

    @PostMapping("/foods")
    public Map<String, Object> create(@RequestBody Map<String, Object> data) {
        return foods.createFood(data);
    }

    @PutMapping("/foods/{foodId}")
    public Map<String, Object> update(@PathVariable long foodId, @RequestBody Map<String, Object> data) {
        return foods.updateFood(foodId, data);
    }

    @DeleteMapping("/foods/{foodId}")
    public Map<String, Object> delete(@PathVariable long foodId) {
        return foods.deleteFood(foodId);
    }

    @GetMapping("/food-categories")
    public Map<String, Object> categories() {
        return foods.listCategories();
    }
}
