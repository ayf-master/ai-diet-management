package com.diet.service;

import com.diet.common.DomainException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.time.Duration;
import java.util.Map;

// Spring -> Python AI 服务转发：内部 token 鉴权 + 超时 + 错误翻译
@Service
public class AiProxyService {

    private final RestClient client;

    public AiProxyService(@Value("${app.ai.base-url}") String baseUrl,
                          @Value("${app.ai.internal-token}") String token,
                          @Value("${app.ai.connect-timeout-ms}") long connectTimeoutMs,
                          @Value("${app.ai.read-timeout-ms}") long readTimeoutMs) {
        java.net.http.HttpClient httpClient = java.net.http.HttpClient.newBuilder()
                .connectTimeout(Duration.ofMillis(connectTimeoutMs))
                .build();
        this.client = RestClient.builder()
                .baseUrl(baseUrl)
                .requestFactory(new org.springframework.http.client.JdkClientHttpRequestFactory(httpClient))
                .defaultHeader("X-Internal-Token", token)
                .build();
    }

    // 转发并原样返回 Python 服务的响应体与状态码（AI 服务返回的就是前端契约格式）
    public ResponseEntity<Map<String, Object>> forward(HttpMethod method, String path,
                                                       Map<String, Object> body) {
        try {
            ResponseEntity<Map<String, Object>> resp = client.method(method)
                    .uri(path)
                    .contentType(MediaType.APPLICATION_JSON)
                    .headers(headers -> {
                        // 把当前登录者身份透传给 AI 服务，供删除等归属校验使用
                        com.diet.security.AuthContext.Identity me = com.diet.security.AuthContext.get();
                        if (me != null) {
                            if (me.userId() != null) {
                                headers.set("X-Acting-User-Id", String.valueOf(me.userId()));
                            }
                            headers.set("X-Acting-Role", me.role());
                        }
                    })
                    .body(body == null ? Map.of() : body)
                    .exchange((req, res) -> {
                        Map<String, Object> parsed = null;
                        try {
                            parsed = objectMapper.readValue(res.getBody(),
                                    objectMapper.getTypeFactory().constructMapType(
                                            java.util.LinkedHashMap.class, String.class, Object.class));
                        } catch (Exception ignored) {
                        }
                        return new ResponseEntity<>(parsed, res.getHeaders(), res.getStatusCode());
                    });
            return resp;
        } catch (Exception e) {
            // AI 服务不可用：降级为 503，不让异常栈直接打到前端
            throw new DomainException(503, "AI 服务暂时不可用，请稍后重试");
        }
    }

    private static final com.fasterxml.jackson.databind.ObjectMapper objectMapper =
            new com.fasterxml.jackson.databind.ObjectMapper();
}
