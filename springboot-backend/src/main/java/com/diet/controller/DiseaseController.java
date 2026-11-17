package com.diet.controller;

import com.diet.common.DomainException;
import com.diet.repo.MiscRepo;
import com.diet.security.AuthSupport;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class DiseaseController {

    private final MiscRepo misc;

    public DiseaseController(MiscRepo misc) {
        this.misc = misc;
    }

    @GetMapping("/diseases")
    public Map<String, Object> listDiseases() {
        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("code", 200);
        resp.put("data", misc.listDiseases());
        return resp;
    }

    @GetMapping("/user/diseases")
    public Map<String, Object> listUserDiseases(@RequestParam(required = false) Long user_id) {
        Long userId = AuthSupport.resolveUserId(user_id);
        List<Map<String, Object>> result = new ArrayList<>();
        for (Map<String, Object> r : misc.userDiseases(userId)) {
            Map<String, Object> d = misc.findDisease(((Number) r.get("disease_id")).longValue());
            if (d != null) {
                r.put("disease_name", d.get("disease_name"));
                r.put("forbid_desc", d.get("forbid_desc"));
            } else {
                r.put("disease_name", null);
                r.put("forbid_desc", null);
            }
            result.add(r);
        }
        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("code", 200);
        resp.put("data", result);
        return resp;
    }

    @PostMapping("/user/diseases")
    public Map<String, Object> add(@RequestBody(required = false) Map<String, Object> data) {
        if (data == null || data.get("disease_id") == null) {
            throw new DomainException(400, "disease_id 不能为空");
        }
        Long userId = AuthSupport.resolveUserId(
                data.get("user_id") == null ? null : toLong(data.get("user_id")));
        long diseaseId = toLong(data.get("disease_id"));
        if (misc.userDiseaseExists(userId, diseaseId)) {
            throw new DomainException(409, "该疾病已关联");
        }
        String remark = data.get("remark") == null ? null : String.valueOf(data.get("remark"));
        misc.insertUserDisease(userId, diseaseId, remark);
        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("code", 200);
        resp.put("msg", "添加成功");
        resp.put("data", misc.userDiseases(userId).stream()
                .filter(r -> ((Number) r.get("disease_id")).longValue() == diseaseId)
                .findFirst().orElse(null));
        return resp;
    }

    @DeleteMapping("/user/diseases/{id}")
    public Map<String, Object> delete(@PathVariable long id) {
        Map<String, Object> record = misc.findUserDisease(id);
        if (record == null) {
            throw new DomainException(404, "记录不存在");
        }
        AuthSupport.ensureEdit((Long) record.get("user_id"));
        misc.deleteUserDisease(id);
        return com.diet.common.ApiResponse.ok("删除成功");
    }

    @PutMapping("/user/diseases/{id}")
    public Map<String, Object> update(@PathVariable long id, @RequestBody(required = false) Map<String, Object> data) {
        Map<String, Object> record = misc.findUserDisease(id);
        if (record == null) {
            throw new DomainException(404, "记录不存在");
        }
        AuthSupport.ensureEdit((Long) record.get("user_id"));
        if (data != null && data.containsKey("remark")) {
            misc.updateUserDiseaseRemark(id, data.get("remark") == null ? null : String.valueOf(data.get("remark")));
        }
        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("code", 200);
        resp.put("msg", "更新成功");
        resp.put("data", misc.findUserDisease(id));
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
