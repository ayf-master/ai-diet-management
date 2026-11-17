package com.diet.controller;

import com.diet.service.AuthService;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class AuthController {

    private final AuthService auth;

    public AuthController(AuthService auth) {
        this.auth = auth;
    }

    @PostMapping("/register")
    public Map<String, Object> register(@RequestBody(required = false) Map<String, Object> data) {
        if (data == null) {
            throw new com.diet.common.DomainException(400, "请求数据为空");
        }
        return auth.register(data);
    }

    @PostMapping("/login")
    public Map<String, Object> login(@RequestBody(required = false) Map<String, Object> data) {
        if (data == null) {
            throw new com.diet.common.DomainException(400, "请求数据为空");
        }
        return auth.login(data);
    }

    @PostMapping("/admin/login")
    public Map<String, Object> adminLogin(@RequestBody(required = false) Map<String, Object> data) {
        if (data == null) {
            throw new com.diet.common.DomainException(400, "请求数据为空");
        }
        return auth.adminLogin(data);
    }

    @PostMapping("/send-code")
    public Map<String, Object> sendCode(@RequestBody(required = false) Map<String, Object> data) {
        return auth.sendCode(data == null ? Map.of() : data);
    }

    @PostMapping("/reset-password")
    public Map<String, Object> resetPassword(@RequestBody(required = false) Map<String, Object> data) {
        return auth.resetPassword(data == null ? Map.of() : data);
    }

    @GetMapping("/user/profile")
    public Map<String, Object> profile(@RequestParam(required = false) Long user_id) {
        return auth.profile(user_id);
    }

    @PutMapping("/user/zones")
    public Map<String, Object> updateZones(@RequestBody(required = false) Map<String, Object> data) {
        return auth.updateZones(data == null ? Map.of() : data);
    }

    @PostMapping(value = "/user/avatar", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public Map<String, Object> uploadAvatar(@RequestParam(required = false) Long user_id,
                                            @RequestParam(value = "avatar", required = false) MultipartFile avatar) throws IOException {
        return auth.uploadAvatar(user_id, avatar);
    }

    @DeleteMapping("/user/avatar")
    public Map<String, Object> removeAvatar(@RequestParam(required = false) Long user_id) throws IOException {
        return auth.removeAvatar(user_id);
    }
}
