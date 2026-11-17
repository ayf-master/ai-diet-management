package com.diet.service;

import com.diet.repo.MealRepo;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

// 日/周统计（对齐 stats_service.py）
@Service
public class StatsService {

    private final MealRepo meals;

    public StatsService(MealRepo meals) {
        this.meals = meals;
    }

    public String[] weekRange(String end) {
        LocalDate endDate = end == null || end.isEmpty() ? LocalDate.now() : LocalDate.parse(end);
        return new String[]{endDate.minusDays(6).toString(), endDate.toString()};
    }

    public Map<String, Object> dailyStats(long userId, String date) {
        String d = date == null || date.isEmpty() ? LocalDate.now().toString() : date;
        List<Map<String, Object>> records = meals.recordsByDate(userId, d);
        int totalCal = 0;
        List<Map<String, Object>> mealsList = new ArrayList<>();
        for (Map<String, Object> r : records) {
            totalCal += numOf(r.get("total_cal"));
            Map<String, Object> meal = new LinkedHashMap<>();
            meal.put("meal_type", r.get("type_name"));
            meal.put("cal", numOf(r.get("total_cal")));
            mealsList.add(meal);
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("date", d);
        out.put("total_cal", totalCal);
        out.put("meal_count", records.size());
        out.put("meals", mealsList);
        return out;
    }

    public Map<String, Object> weeklyStats(long userId, String end) {
        String[] range = weekRange(end);
        LocalDate start = LocalDate.parse(range[0]);
        List<Map<String, Object>> records = meals.recordsBetween(userId, range[0], range[1]);

        Map<String, Double> dailyData = new LinkedHashMap<>();
        int totalCal = 0;
        for (Map<String, Object> r : records) {
            String day = String.valueOf(r.get("eat_date"));
            double cal = numOf(r.get("total_cal"));
            dailyData.merge(day, cal, Double::sum);
            totalCal += cal;
        }
        List<Map<String, Object>> daily = new ArrayList<>();
        for (int i = 0; i < 7; i++) {
            String day = start.plusDays(i).toString();
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("date", day);
            item.put("cal", dailyData.getOrDefault(day, 0.0));
            daily.add(item);
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("start", range[0]);
        out.put("end", range[1]);
        out.put("total_cal", totalCal);
        out.put("daily", daily);
        return out;
    }

    public List<Map<String, Object>> weightRecordsBetween(long userId, String start, String end) {
        return meals.weightRecordsBetween(userId, start, end);
    }

    public double weightDiff(List<Map<String, Object>> records) {
        if (records != null && records.size() >= 2) {
            return Math.round((numOf(records.get(records.size() - 1).get("weight"))
                    - numOf(records.get(0).get("weight"))) * 10.0) / 10.0;
        }
        return 0;
    }

    static double numOf(Object v) {
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
}
