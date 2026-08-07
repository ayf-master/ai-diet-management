<template>
  <div class="login-page">
    <div class="login-bg-shapes">
      <div class="shape shape-1"></div>
      <div class="shape shape-2"></div>
    </div>
    <div class="login-card">
      <div class="login-logo">
        <div class="logo-icon">&#9881;</div>
        <h1 class="login-title">管理员登录</h1>
        <p class="login-sub">后台管理系统</p>
      </div>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label>账号</label>
          <input v-model="account" class="input" placeholder="管理员账号" required>
        </div>
        <div class="form-group">
          <label>密码</label>
          <input v-model="password" class="input" type="password" placeholder="密码" required>
        </div>
        <p v-if="error" class="error-msg">{{ error }}</p>
        <button type="submit" class="btn btn-primary btn-block" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>
      <p class="login-footer"><router-link to="/login">用户登录</router-link></p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api/index.js'

const router = useRouter()
const account = ref('admin')
const password = ref('123456')
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  loading.value = true; error.value = ''
  try {
    const res = await api.adminLogin(account.value, password.value)
    if (res.code === 200) {
      sessionStorage.setItem('admin', JSON.stringify(res.data))
      router.push('/admin/foods')
    } else { error.value = res.msg }
  } catch (e) { error.value = '网络错误' }
  finally { loading.value = false }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  position: relative; overflow: hidden;
  background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
}
.login-bg-shapes { position: absolute; inset: 0; pointer-events: none; overflow: hidden; }
.shape {
  position: absolute; border-radius: 50%; opacity: 0.12;
}
.shape-1 { width: 350px; height: 350px; background: #3498DB; top: -80px; right: -60px; }
.shape-2 { width: 250px; height: 250px; background: #2980B9; bottom: -50px; left: -50px; }
.login-card {
  background: rgba(255,255,255,0.92); backdrop-filter: blur(12px);
  border-radius: 20px; padding: 32px; max-width: 400px; width: 100%;
  box-shadow: 0 8px 40px rgba(0,0,0,0.08);
  border: 1px solid rgba(255,255,255,0.5); position: relative; z-index: 1;
}
.login-logo { text-align: center; margin-bottom: 24px; }
.logo-icon { font-size: 36px; margin-bottom: 8px; }
.login-title { font-size: 20px; color: var(--text); margin-bottom: 4px; }
.login-sub { color: var(--text-light); font-size: 13px; }
.error-msg { color: var(--danger); font-size: 14px; margin-bottom: 12px; }
.login-footer { text-align: center; margin-top: 16px; font-size: 13px; }
</style>
