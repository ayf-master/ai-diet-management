<template>
  <div class="login-page">
    <div class="login-bg"></div>

    <div class="login-card">
      <div class="login-logo">
        <div class="logo-mark">食</div>
        <h1 class="login-title">饮食管理</h1>
        <p class="login-slogan">一切为了你的健康</p>
      </div>

      <div class="tabs">
        <button class="tab" :class="{ active: tab === 'login' }" @click="tab = 'login'">登录</button>
        <button class="tab" :class="{ active: tab === 'register' }" @click="tab = 'register'">注册</button>
      </div>

      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label>账号</label>
          <input v-model="form.account" class="input" placeholder="请输入账号" required>
        </div>
        <div class="form-group">
          <label>密码</label>
          <input v-model="form.password" class="input" type="password" placeholder="请输入密码" required>
          <router-link to="/forgot-password" class="forgot-link" v-if="tab === 'login'">忘记密码?</router-link>
        </div>

        <div class="register-collapse" :class="{ open: tab === 'register' }">
          <div class="register-inner">
          <div class="form-group">
            <label>昵称</label>
            <input v-model="form.nickname" class="input" placeholder="显示名称">
          </div>
          <div class="form-group">
            <label>邮箱</label>
            <input v-model="form.email" class="input" type="email" placeholder="用于找回密码">
          </div>
          <div class="form-row grid-2">
            <div class="form-group">
              <label>年龄</label>
              <input v-model.number="form.age" class="input" type="number">
            </div>
            <div class="form-group">
              <label>性别</label>
              <select v-model.number="form.gender" class="input">
                <option :value="0">女</option><option :value="1">男</option>
              </select>
            </div>
          </div>
          <div class="form-row grid-2">
            <div class="form-group">
              <label>身高 (cm)</label>
              <input v-model.number="form.height" class="input" type="number" step="0.1">
            </div>
            <div class="form-group">
              <label>活动等级</label>
              <select v-model.number="form.activity_level" class="input">
                <option :value="1">静坐</option><option :value="2">轻度</option>
                <option :value="3">中度</option><option :value="4">重度</option>
              </select>
            </div>
          </div>
          <div class="form-row grid-2">
            <div class="form-group">
              <label>当前体重 (kg)</label>
              <input v-model.number="form.current_weight" class="input" type="number" step="0.1">
            </div>
            <div class="form-group">
              <label>目标体重 (kg)</label>
              <input v-model.number="form.target_weight" class="input" type="number" step="0.1">
            </div>
          </div>
          <div class="form-group">
            <label>饮食目标（可多选）</label>
            <div class="zone-checks">
              <label v-for="z in zoneOptions" :key="z.key" class="zone-check">
                <input type="checkbox" :value="z.key" v-model="form.diet_goals">
                <span>{{ z.label }}</span>
              </label>
            </div>
          </div>
        </div>
        </div>

        <p v-if="error" class="error-msg">{{ error }}</p>
        <button type="submit" class="btn btn-primary btn-block" :disabled="loading">
          {{ loading ? '处理中...' : tab === 'login' ? '登录' : '注册' }}
        </button>
      </form>

      <p class="login-footer">
        <router-link to="/admin/login">管理员入口</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../api/index.js'

const router = useRouter()
const route = useRoute()
const tab = ref(route.query.mode === 'register' ? 'register' : 'login')
const loading = ref(false)
const error = ref('')

const zoneOptions = [
  { key: 'healthy', label: '健康饮食' },
  { key: 'lose_weight', label: '减脂' },
  { key: 'gain_muscle', label: '增肌' },
]

const form = reactive({
  account: '', password: '', nickname: '', email: '',
  age: 25, gender: 1, height: 170, current_weight: 65,
  target_weight: 60, activity_level: 2, diet_goal: 'healthy',
  diet_goals: ['healthy'],
})

async function handleSubmit() {
  loading.value = true; error.value = ''
  try {
    if (tab.value === 'login') {
      const res = await api.login(form.account, form.password)
      if (res.code === 200) {
        sessionStorage.setItem('user', JSON.stringify(res.data))
        sessionStorage.setItem('token', res.access_token || '')
        router.push('/dashboard')
      } else { error.value = res.msg }
    } else {
      if (!form.diet_goals.length) {
        error.value = '请至少选择一个饮食专区'
        loading.value = false
        return
      }
      const res = await api.register({ ...form, diet_goals: form.diet_goals })
      if (res.code === 200) {
        sessionStorage.setItem('user', JSON.stringify(res.data))
        sessionStorage.setItem('token', res.access_token || '')
        router.push('/dashboard')
      } else { error.value = res.msg }
    }
  } catch (e) { error.value = '网络错误' }
  finally { loading.value = false }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  position: relative; background: #F7F6F3;
}
.login-bg {
  position: absolute; inset: 0; pointer-events: none;
  background: radial-gradient(ellipse at 20% 50%, rgba(46,204,113,0.06) 0%, transparent 50%),
              radial-gradient(ellipse at 80% 50%, rgba(46,204,113,0.04) 0%, transparent 50%);
}
.login-card {
  background: #fff; border-radius: 12px; padding: 36px;
  max-width: 480px; width: 100%;
  border: 1px solid #EAEAEA; position: relative; z-index: 1;
}
.login-logo { text-align: center; margin-bottom: 24px; }
.logo-mark {
  width: 48px; height: 48px; background: #111; color: #fff;
  border-radius: 8px; display: inline-flex; align-items: center;
  justify-content: center; font-size: 22px; font-weight: 700; margin-bottom: 10px;
}
.login-title { font-size: 22px; color: #111; font-weight: 600; }
.login-slogan {
  font-family: 'Newsreader', 'Georgia', serif; font-size: 16px;
  color: #787774; margin-top: 4px; font-style: italic;
}
.zone-checks { display: flex; gap: 16px; margin-top: 4px; }
.zone-check { display: flex; align-items: center; gap: 6px; cursor: pointer; font-size: 14px; }
.zone-check input { accent-color: #111; }
.form-row { margin-bottom: 0; }
.error-msg { color: #E74C3C; font-size: 14px; margin-bottom: 12px; }
.login-footer { text-align: center; margin-top: 16px; font-size: 13px; }
.forgot-link {
  float: right; font-size: 13px; color: #787774; margin-top: 4px;
  text-decoration: none;
}
.forgot-link:hover { color: #111; text-decoration: underline; }

/* ── 登录/注册切换 — 平滑高度过渡 ── */
.register-collapse {
  display: grid;
  grid-template-rows: 0fr;
  transition: grid-template-rows 0.35s ease;
}
.register-collapse.open {
  grid-template-rows: 1fr;
}
.register-inner {
  overflow: hidden;
  opacity: 0;
  transition: opacity 0.25s ease;
}
.register-collapse.open .register-inner {
  opacity: 1;
}
</style>
