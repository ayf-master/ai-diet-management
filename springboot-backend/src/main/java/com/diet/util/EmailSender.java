package com.diet.util;

import org.springframework.mail.javamail.JavaMailSenderImpl;
import org.springframework.mail.javamail.MimeMessageHelper;

import jakarta.mail.MessagingException;
import jakarta.mail.internet.MimeMessage;
import java.util.Properties;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

// 端口 587(TLS) -> 465(SSL) 自动回退，与 Flask 版行为一致
public class EmailSender {

    private static final Logger log = LoggerFactory.getLogger(EmailSender.class);

    public record SmtpConfig(String host, int port, String user, String password, String sender) {
        public boolean configured() {
            return user != null && !user.isEmpty() && !user.equals("your_email@qq.com")
                    && password != null && !password.isEmpty();
        }
    }

    public static SmtpConfig fromEnv() {
        int port = 587;
        try {
            port = Integer.parseInt(System.getenv().getOrDefault("SMTP_PORT", "587"));
        } catch (NumberFormatException ignored) {
        }
        String user = env("SMTP_USER");
        return new SmtpConfig(env("SMTP_HOST"), port, user, env("SMTP_PASSWORD"),
                env("SMTP_SENDER") == null || env("SMTP_SENDER").isEmpty() ? user : env("SMTP_SENDER"));
    }

    private static String env(String key) {
        String v = System.getenv(key);
        return v == null ? "" : v;
    }

    public static boolean sendVerificationCode(String toEmail, String code) {
        SmtpConfig cfg = fromEnv();
        if (!cfg.configured()) {
            log.warn("[邮件] SMTP 未配置，请在环境变量中填写 SMTP_USER 和 SMTP_PASSWORD");
            return false;
        }

        String body = "<div style=\"max-width:480px;margin:0 auto;padding:24px;font-family:sans-serif;"
                + "border:1px solid #eee;border-radius:8px\">"
                + "<div style=\"text-align:center;margin-bottom:20px\">"
                + "<div style=\"width:48px;height:48px;background:#111;color:#fff;border-radius:8px;"
                + "display:inline-flex;align-items:center;justify-content:center;font-size:22px;font-weight:700\">食</div>"
                + "<h2 style=\"color:#111;margin:8px 0 0\">密码重置</h2></div>"
                + "<p style=\"color:#555;font-size:14px;line-height:1.6\">您正在重置饮食管理系统的登录密码，验证码如下：</p>"
                + "<div style=\"text-align:center;margin:24px 0;font-size:36px;font-weight:700;"
                + "letter-spacing:8px;color:#111\">" + code + "</div>"
                + "<p style=\"color:#999;font-size:12px\">验证码有效期为10分钟，如非本人操作请忽略此邮件。</p></div>";

        // 与 Python 版相同的端口回退顺序
        int configured = cfg.port();
        int fallback = configured == 465 ? 587 : 465;
        Exception lastError = null;
        for (int[] attempt : new int[][]{{configured, configured == 465 ? 1 : 0}, {fallback, fallback == 465 ? 1 : 0}}) {
            try {
                send(cfg, toEmail, body, attempt[0], attempt[1] == 1);
                log.info("[邮件] 验证码已发送至 {} (端口 {})", toEmail, attempt[0]);
                return true;
            } catch (Exception e) {
                lastError = e;
                log.warn("[邮件] 端口 {} 失败: {}", attempt[0], e.getMessage());
            }
        }
        log.error("[邮件] 所有端口尝试均失败: {}", lastError == null ? "" : lastError.getMessage());
        return false;
    }

    private static void send(SmtpConfig cfg, String toEmail, String htmlBody,
                             int port, boolean ssl) throws MessagingException {
        JavaMailSenderImpl sender = new JavaMailSenderImpl();
        sender.setHost(cfg.host());
        sender.setPort(port);
        sender.setUsername(cfg.user());
        sender.setPassword(cfg.password());
        sender.setDefaultEncoding("UTF-8");
        Properties props = sender.getJavaMailProperties();
        props.put("mail.smtp.auth", "true");
        props.put("mail.smtp.ssl.enable", String.valueOf(ssl));
        props.put("mail.smtp.starttls.enable", String.valueOf(!ssl));
        props.put("mail.smtp.connectiontimeout", "10000");
        props.put("mail.smtp.timeout", "10000");

        MimeMessage message = sender.createMimeMessage();
        MimeMessageHelper helper = new MimeMessageHelper(message, false, "UTF-8");
        try {
            helper.setFrom(cfg.sender());
            helper.setTo(toEmail);
            helper.setSubject("饮食管理系统 — 密码重置验证码");
            helper.setText(htmlBody, true);
        } catch (MessagingException e) {
            throw e;
        } catch (Exception e) {
            throw new MessagingException(e.getMessage(), e);
        }
        sender.send(message);
    }
}
