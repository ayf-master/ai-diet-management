package com.diet.controller;

import com.diet.service.RecipeService;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class RecipeController {

    private final RecipeService recipes;

    public RecipeController(RecipeService recipes) {
        this.recipes = recipes;
    }

    @GetMapping("/recipes")
    public Map<String, Object> list(@RequestParam(required = false, defaultValue = "") String goal,
                                    @RequestParam(required = false, defaultValue = "") String goals,
                                    @RequestParam(required = false, defaultValue = "") String type,
                                    @RequestParam(required = false, defaultValue = "") String keyword,
                                    @RequestParam(required = false) Long user_id) {
        Map<String, Object> resp = new java.util.LinkedHashMap<>();
        resp.put("code", 200);
        resp.put("data", recipes.listRecipes(goal, goals, type, keyword, user_id));
        return resp;
    }

    @GetMapping("/recipes/{recipeId}")
    public Map<String, Object> get(@PathVariable long recipeId,
                                   @RequestParam(required = false) Long user_id) {
        Map<String, Object> resp = new java.util.LinkedHashMap<>();
        resp.put("code", 200);
        resp.put("data", recipes.getRecipePayload(recipeId, user_id));
        return resp;
    }

    @GetMapping("/cooking-methods")
    public Map<String, Object> cookingMethods() {
        return recipes.listCookingMethods();
    }

    @PostMapping("/recipes")
    public Map<String, Object> create(@RequestBody(required = false) Map<String, Object> data) {
        return recipes.createRecipe(data == null ? Map.of() : data);
    }

    @PutMapping("/recipes/{recipeId}")
    public Map<String, Object> update(@PathVariable long recipeId, @RequestBody(required = false) Map<String, Object> data) {
        return recipes.updateRecipe(recipeId, data == null ? Map.of() : data);
    }

    @DeleteMapping("/recipes/{recipeId}")
    public Map<String, Object> delete(@PathVariable long recipeId) {
        return recipes.deleteRecipe(recipeId);
    }

    @GetMapping("/user-cooking-prefs")
    public Map<String, Object> getPrefs(@RequestParam(required = false) Long user_id) {
        return recipes.getCookingPrefs(user_id);
    }

    @PutMapping("/user-cooking-prefs")
    public Map<String, Object> savePrefs(@RequestBody(required = false) Map<String, Object> data) {
        Long userId = data == null || data.get("user_id") == null ? null
                : ((Number) toNum(data.get("user_id"))).longValue();
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> prefs = (List<Map<String, Object>>) (data == null ? null : data.get("prefs"));
        return recipes.saveCookingPrefs(userId, prefs);
    }

    @DeleteMapping("/user-cooking-prefs")
    public Map<String, Object> resetPrefs(@RequestParam(required = false) Long user_id) {
        return recipes.resetCookingPrefs(user_id);
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
