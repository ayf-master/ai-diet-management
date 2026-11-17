package com.diet.controller;

import com.diet.common.DomainException;
import com.diet.repo.MiscRepo;
import com.diet.security.AuthSupport;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.LinkedHashMap;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class WeightController {

    private final MiscRepo misc;

    public WeightController(MiscRepo misc) {
        this.misc = misc;
    }

    @PostMapping("/weight")
    public Map<String, Object> record(@RequestBody(required = false) Map<String, Object> data) {
        if (data == null || data.isEmpty()) {
            throw new DomainException(400, "请求数据为空");
        }
        Object weightObj = data.get("weight");
        if (weightObj == null) {
            throw new DomainException(400, "weight 不能为空");
        }
        Long userId = AuthSupport.resolveUserId(
                data.get("user_id") == null ? null : toLong(data.get("user_id")));

        double weight = weightObj instanceof Number n ? n.doubleValue()
                : Double.parseDouble(String.valueOf(weightObj));
        Double bodyFat = data.get("body_fat_rate") == null ? null
                : (data.get("body_fat_rate") instanceof Number n2
                ? n2.doubleValue() : Double.parseDouble(String.valueOf(data.get("body_fat_rate"))));
        String measureDate = data.get("measure_date") == null
                ? LocalDate.now().toString() : String.valueOf(data.get("measure_date"));
        String note = data.get("note") == null ? null : String.valueOf(data.get("note"));

        misc.callRecordWeight(userId, weight, bodyFat, measureDate, note);
        Map<String, Object> record = misc.latestWeightByWeight(userId, weight);

        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("code", 200);
        resp.put("msg", "记录成功");
        resp.put("data", record);
        return resp;
    }

    @GetMapping("/weight")
    public Map<String, Object> list(@RequestParam(required = false) Long user_id,
                                    @RequestParam(required = false, defaultValue = "20") Integer limit,
                                    @RequestParam(required = false, defaultValue = "0") Integer offset) {
        Long userId = AuthSupport.resolveUserId(user_id);
        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("code", 200);
        resp.put("data", misc.listWeights(userId, limit, offset));
        return resp;
    }

    @GetMapping("/weight/latest")
    public Map<String, Object> latest(@RequestParam(required = false) Long user_id) {
        Long userId = AuthSupport.resolveUserId(user_id);
        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("code", 200);
        resp.put("data", misc.latestWeight(userId));
        return resp;
    }

    @DeleteMapping("/weight/{recordId}")
    public Map<String, Object> delete(@PathVariable long recordId) {
        Map<String, Object> record = misc.findWeight(recordId);
        if (record == null) {
            throw new DomainException(404, "记录不存在");
        }
        AuthSupport.ensureEdit((Long) record.get("user_id"));
        misc.deleteWeight(recordId);
        return com.diet.common.ApiResponse.ok("删除成功");
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
