package com.diet.util;

// 纯营养计算：与 Flask services/nutrition.py 逐行对齐，不查数据库
public class NutritionCalc {

    public static final double OIL_KCAL_PER_G = 9.0;
    public static final double SAUCE_KCAL_PER_G = 4.0;

    public record Ingredient(double weight, Double caloriePer100g) {
    }

    public record RecipeTotals(double totalWeight, int baseCalorie, int addedCalorie, int totalCalorie) {
    }

    public record MealItemTotals(double oilG, double sauceG, int singleCal) {
    }

    public static int addedCaloriesFromGrams(double oilG, double sauceG) {
        return (int) Math.round(oilG * OIL_KCAL_PER_G + sauceG * SAUCE_KCAL_PER_G);
    }

    // 按烹饪方式系数算附加热量，返回未取整值
    public static double addedCaloriesFromCookMethodRaw(double totalWeight, double oilPer100g, double sauceKcalPer100g) {
        if (totalWeight <= 0) {
            return 0.0;
        }
        return oilPer100g * totalWeight / 100.0 * OIL_KCAL_PER_G
                + sauceKcalPer100g * totalWeight / 100.0;
    }

    public static RecipeTotals calcRecipeTotals(java.util.List<Ingredient> ingredients,
                                                double oilG, double sauceG,
                                                double oilPer100g, double sauceKcalPer100g) {
        double totalWeight = 0;
        double baseRaw = 0;
        if (ingredients != null) {
            for (Ingredient ing : ingredients) {
                totalWeight += ing.weight();
                if (ing.caloriePer100g() != null && ing.caloriePer100g() > 0) {
                    baseRaw += ing.caloriePer100g() * ing.weight() / 100.0;
                }
            }
        }
        int addedCalorie;
        if (oilG > 0 || sauceG > 0) {
            addedCalorie = addedCaloriesFromGrams(oilG, sauceG);
        } else {
            addedCalorie = (int) Math.round(addedCaloriesFromCookMethodRaw(totalWeight, oilPer100g, sauceKcalPer100g));
        }
        return new RecipeTotals(totalWeight, (int) Math.round(baseRaw), addedCalorie,
                (int) Math.round(baseRaw + addedCalorie));
    }

    // 打卡单条明细：按份量缩放；优先级与 Python 版一致
    public static MealItemTotals calcMealItem(double recipeTotalWeight, double recipeBaseCalorie,
                                              double recipeTotalCalorie, double recipeOilG, double recipeSauceG,
                                              double eatWeight, Double overrideOil, Double overrideSauce) {
        boolean hasOverride = overrideOil != null && overrideSauce != null;
        boolean overrideUsed = hasOverride && (overrideOil != 0 || overrideSauce != 0);

        double oilG;
        double sauceG;
        if (overrideUsed) {
            oilG = overrideOil;
            sauceG = overrideSauce;
        } else if (recipeOilG > 0 || recipeSauceG > 0) {
            double scale = eatWeight / (recipeTotalWeight > 0 ? recipeTotalWeight : Math.max(eatWeight, 1));
            oilG = recipeOilG * scale;
            sauceG = recipeSauceG * scale;
        } else {
            oilG = 0;
            sauceG = 0;
        }

        double basePart = recipeBaseCalorie * eatWeight / (recipeTotalWeight > 0 ? recipeTotalWeight : 100);
        int singleCal;
        if (overrideUsed || recipeOilG > 0 || recipeSauceG > 0) {
            singleCal = (int) Math.round(basePart + oilG * OIL_KCAL_PER_G + sauceG * SAUCE_KCAL_PER_G);
        } else {
            singleCal = (int) Math.round(recipeTotalCalorie * eatWeight
                    / (recipeTotalWeight > 0 ? recipeTotalWeight : 100));
        }
        return new MealItemTotals(Math.round(oilG * 100.0) / 100.0, Math.round(sauceG * 100.0) / 100.0, singleCal);
    }
}
