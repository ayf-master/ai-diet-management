package com.diet.controller;

import com.diet.security.AuthSupport;
import com.diet.service.AiProxyService;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

// /api/ai/** 全部转发给 Python AI 服务；user_id 在这里完成身份解析后再传
@RestController
@RequestMapping("/api/ai")
public class AiController {

    private final AiProxyService ai;

    public AiController(AiProxyService ai) {
        this.ai = ai;
    }

    @PostMapping("/plan")
    public ResponseEntity<Map<String, Object>> createPlan(@RequestBody(required = false) Map<String, Object> data) {
        Map<String, Object> body = data == null ? Map.of() : Map.of(
                "user_id", AuthSupport.resolveUserId(toLong(data.get("user_id"))));
        return ai.forward(HttpMethod.POST, "/ai/v1/plan", body);
    }

    @GetMapping("/plan")
    public ResponseEntity<Map<String, Object>> listPlans(@RequestParam(required = false) Long user_id,
                                                         @RequestParam(required = false, defaultValue = "5") Integer limit) {
        Long userId = AuthSupport.resolveUserId(user_id);
        return ai.forward(HttpMethod.GET,
                "/ai/v1/plan?user_id=" + userId + "&limit=" + limit, null);
    }

    @DeleteMapping("/plan/{planId}")
    public ResponseEntity<Map<String, Object>> deletePlan(@PathVariable long planId) {
        return ai.forward(HttpMethod.DELETE, "/ai/v1/plan/" + planId, null);
    }

    @PostMapping("/report")
    public ResponseEntity<Map<String, Object>> createReport(@RequestBody(required = false) Map<String, Object> data) {
        Map<String, Object> body = data == null ? Map.of() : Map.of(
                "user_id", AuthSupport.resolveUserId(toLong(data.get("user_id"))));
        return ai.forward(HttpMethod.POST, "/ai/v1/report", body);
    }

    @GetMapping("/report")
    public ResponseEntity<Map<String, Object>> listReports(@RequestParam(required = false) Long user_id,
                                                           @RequestParam(required = false, defaultValue = "5") Integer limit) {
        Long userId = AuthSupport.resolveUserId(user_id);
        return ai.forward(HttpMethod.GET,
                "/ai/v1/report?user_id=" + userId + "&limit=" + limit, null);
    }

    @DeleteMapping("/report/{reportId}")
    public ResponseEntity<Map<String, Object>> deleteReport(@PathVariable long reportId) {
        return ai.forward(HttpMethod.DELETE, "/ai/v1/report/" + reportId, null);
    }

    @PostMapping("/assistant")
    public ResponseEntity<Map<String, Object>> assistant(@RequestBody(required = false) Map<String, Object> data) {
        if (data == null) {
            data = Map.of();
        }
        Long userId = AuthSupport.resolveUserId(toLong(data.get("user_id")));
        Map<String, Object> body = Map.of(
                "user_id", userId,
                "message", data.get("message") == null ? "" : data.get("message"));
        return ai.forward(HttpMethod.POST, "/ai/v1/assistant", body);
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
