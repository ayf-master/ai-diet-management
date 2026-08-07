<template>
  <div class="forgot-page">
    <div class="forgot-card">
      <div class="forgot-header">
        <div class="logo-mark">食</div>
        <h1 class="forgot-title">重置密码</h1>
        <p class="forgot-sub">{{ step === 1 ? '输入账号，验证码将发送到注册邮箱' : '输入验证码和新密码' }}</p>
      </div>

      <!-- 步骤1: 输入账号 -->
      <template v-if="step === 1">
        <form @submit.prevent="handleSendCode">
          <div class="form-group">
            <label>账号</label>
            <input v-model="account" class="input" placeholder="请输入注册时的账号" required autofocus>
          </div>
          <p v-if="error" class="error-msg">{{ error }}</p>
          <p v-if="success" class="success-msg">{{ success }}</p>
          <button type="submit" class="btn btn-primary btn-block" :disabled="sending">
            {{ sending ? '发送中...' : '发送验证码' }}
          </button>
        </form>
        <p class="back-link"><router-link to="/login">返回登录</router-link></p>
      </template>

      <!-- 步骤2: 输入验证码 + 新密码 -->
      <template v-if="step === 2">
        <form @submit.prevent="handleReset">
          <div class="form-group">
            <label>验证码</label>
            <input v-model="code" class="input" placeholder="6位验证码" maxlength="6" required autofocus>
            <div v-if="devCode" class="dev-hint">🔧 开发模式验证码: <strong>{{ devCode }}</strong></div>
            <button type="button" class="resend-btn" @click="handleSendCode" :disabled="sending || resendCooldown > 0">
              {{ resendCooldown > 0 ? `${resendCooldown}s后重发` : '重新发送' }}
            </button>
          </div>
          <div class="form-group">
            <label>新密码</label>
            <input v-model="password" class="input" type="password" placeholder="至少6位" minlength="6" required>
          </div>
          <div class="form-group">
            <label>确认密码</label>
            <input v-model="confirmPwd" class="input" type="password" placeholder="再次输入新密码" minlength="6" required>
          </div>
          <p v-if="error" class="error-msg">{{ error }}</p>
          <p v-if="success" class="success-msg">{{ success }}</p>
          <button type="submit" class="btn btn-primary btn-block" :disabled="resetting">
            {{ resetting ? '重置中...' : '重置密码' }}
          </button>
        </form>
        <p class="back-link"><router-link to="/login">返回登录</router-link></p>
      </template>

      <!-- 步骤3: 成功 -->
      <template v-if="step === 3">
        <div class="success-box">
          <div class="success-icon">✓</div>
          <h2>密码已重置</h2>
          <p>请用新密码登录</p>
          <router-link to="/login" class="btn btn-primary">去登录</router-link>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '../api/index.js'

const step = ref(1)
const account = ref('')
const code = ref('')
const devCode = ref('')
const password = ref('')
const confirmPwd = ref('')
const error = ref('')
const success = ref('')
const sending = ref(false)
const resetting = ref(false)
const resendCooldown = ref(0)

async function handleSendCode() {
  if (!account.value.trim()) { error.value = '请输入账号'; return }
  sending.value = true; error.value = ''; success.value = ''
  try {
    const res = await api.sendCode(account.value.trim())
    if (res.code === 200) {
      if (res.dev_mode) {
        // 开发模式：SMTP 未配置，验证码直接显示
        success.value = `开发模式 — 验证码: ${res.dev_code}`
        devCode.value = res.dev_code
      } else {
        success.value = res.msg
      }
      if (step.value === 1) {
        step.value = 2
        startCooldown()
      } else {
        startCooldown()
      }
    } else {
      error.value = res.msg
    }
  } catch (e) {
    error.value = '网络错误'
  } finally {
    sending.value = false
  }
}

function startCooldown() {
  resendCooldown.value = 60
  const t = setInterval(() => {
    resendCooldown.value--
    if (resendCooldown.value <= 0) clearInterval(t)
  }, 1000)
}

async function handleReset() {
  if (!code.value.trim()) { error.value = '请输入验证码'; return }
  if (password.value.length < 6) { error.value = '密码至少6位'; return }
  if (password.value !== confirmPwd.value) { error.value = '两次密码不一致'; return }
  resetting.value = true; error.value = ''; success.value = ''
  try {
    const res = await api.resetPassword(account.value.trim(), code.value.trim(), password.value)
    if (res.code === 200) {
      step.value = 3
    } else {
      error.value = res.msg
    }
  } catch (e) {
    error.value = '网络错误'
  } finally {
    resetting.value = false
  }
}
</script>

<style scoped>
.forgot-page {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  background: #F7F6F3;
}
.forgot-card {
  background: #fff; border-radius: 12px; padding: 36px;
  max-width: 420px; width: 100%;
  border: 1px solid #EAEAEA;
}
.forgot-header { text-align: center; margin-bottom: 24px; }
.logo-mark {
  width: 48px; height: 48px; background: #111; color: #fff;
  border-radius: 8px; display: inline-flex; align-items: center;
  justify-content: center; font-size: 22px; font-weight: 700; margin-bottom: 10px;
}
.forgot-title { font-size: 22px; color: #111; font-weight: 600; }
.forgot-sub { color: #787774; font-size: 14px; margin-top: 4px; }
.form-group { margin-bottom: 16px; position: relative; }
.form-group label { display: block; font-size: 13px; font-weight: 500; color: #333; margin-bottom: 4px; }
.resend-btn {
  position: absolute; right: 0; top: 0; font-size: 12px; color: #2ECC71;
  background: none; border: none; cursor: pointer; padding: 0;
}
.resend-btn:disabled { color: #bbb; cursor: default; }
.error-msg { color: #E74C3C; font-size: 14px; margin-bottom: 12px; }
.success-msg { color: #27AE60; font-size: 14px; margin-bottom: 12px; }
.back-link { text-align: center; margin-top: 16px; font-size: 13px; }
.back-link a { color: #787774; text-decoration: none; }
.back-link a:hover { color: #111; text-decoration: underline; }
.success-box { text-align: center; padding: 24px 0; }
.success-icon {
  width: 56px; height: 56px; background: #27AE60; color: #fff; border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 28px; font-weight: 700; margin-bottom: 16px;
}
.success-box h2 { margin: 0 0 8px; color: #111; }
.success-box p { color: #787774; margin-bottom: 24px; }
.dev-hint {
  margin-top: 6px; padding: 6px 10px; background: #FFF8E1; border-radius: 6px;
  font-size: 13px; color: #795548; text-align: center;
}
.dev-hint strong { font-size: 18px; letter-spacing: 4px; }
</style>
