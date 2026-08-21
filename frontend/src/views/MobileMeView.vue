<template>
  <div class="page m-me">
    <!-- 用户信息卡 -->
    <div class="me-card">
      <div class="me-avatar">
        <img v-if="avatarUrl" :src="avatarUrl" alt="头像" />
        <span v-else>{{ letter }}</span>
      </div>
      <div class="me-info">
        <h2 class="me-name">{{ user.nickname || user.account }}</h2>
        <p class="me-meta">BMI <strong>{{ user.bmi || '-' }}</strong> · 推荐 {{ user.recommend_cal || 0 }} kcal/日</p>
        <div class="me-zones">
          <span v-for="z in zones" :key="z.key" class="badge" :class="'badge-' + z.key">{{ z.label }}</span>
        </div>
      </div>
    </div>

    <!-- 快捷数据 -->
    <div class="me-stats card">
      <div class="me-stat" @click="go('/stats')">
        <strong>{{ todayCal }}<small> kcal</small></strong>
        <span>今日摄入</span>
      </div>
      <div class="me-stat" @click="go('/stats')">
        <strong>{{ latestWeight }}<small> kg</small></strong>
        <span>最新体重</span>
      </div>
      <div class="me-stat" @click="go('/stats')">
        <strong>{{ targetWeight }}<small> kg</small></strong>
        <span>目标体重</span>
      </div>
    </div>

    <!-- 功能菜单 -->
    <div class="me-menu card">
      <div class="me-item" @click="go('/stats')">
        <span class="me-item__icon" style="background:rgba(52,152,219,0.1);color:#3498DB">▦</span>
        <span class="me-item__label">数据统计</span>
        <span class="me-item__arrow">›</span>
      </div>
      <div class="me-item" @click="go('/ai-plan')">
        <span class="me-item__icon" style="background:rgba(124,154,122,0.15);color:#5e7d5c">✦</span>
        <span class="me-item__label">AI 饮食方案</span>
        <span class="me-item__arrow">›</span>
      </div>
      <div class="me-item" @click="go('/settings')">
        <span class="me-item__icon" style="background:rgba(17,17,17,0.08);color:#111">⚙</span>
        <span class="me-item__label">账号设置</span>
        <span class="me-item__arrow">›</span>
      </div>
    </div>

    <button class="btn btn-block me-logout" @click="logout">退出登录</button>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/index.js'

const router = useRouter()
const user = JSON.parse(sessionStorage.getItem('user') || '{}')

const avatarUrl = user.avatar_url
  ? (user.avatar_url.startsWith('http') ? user.avatar_url : `http://localhost:9876${user.avatar_url}`)
  : ''
const letter = (user.nickname || user.account || '用')[0]

const zoneMap = { healthy: '健康饮食', lose_weight: '减脂', gain_muscle: '增肌' }
const rawZones = user.diet_goals || [user.diet_goal || 'healthy']
const zones = rawZones.map(k => ({ key: k, label: zoneMap[k] || '健康饮食' }))

const todayCal = ref(0)
const latestWeight = ref(user.current_weight || '-')
const targetWeight = ref(user.target_weight || '-')

const go = (p) => router.push(p)

function logout() {
  sessionStorage.clear()
  router.push('/login')
}

onMounted(async () => {
  try {
    const today = new Date().toISOString().split('T')[0]
    const [d, lw] = await Promise.all([
      api.getDailyStats(user.user_id, today),
      api.getLatestWeight(user.user_id),
    ])
    todayCal.value = d.data?.total_cal || 0
    latestWeight.value = lw.data?.weight ?? user.current_weight ?? '-'
  } catch (e) { /* 非关键，失败不影响页面 */ }
})
</script>

<style scoped>
.m-me { padding-bottom: 24px; }
.me-card {
  display: flex; align-items: center; gap: 14px;
  background: #fff; border: 1px solid var(--border, #EAEAEA);
  border-radius: 14px; padding: 18px 16px; margin-bottom: 14px;
}
.me-avatar {
  width: 56px; height: 56px; border-radius: 50%;
  background: #111; color: #fff; overflow: hidden;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 20px; flex-shrink: 0;
}
.me-avatar img { width: 100%; height: 100%; object-fit: cover; }
.me-info { min-width: 0; }
.me-name { font-size: 18px; font-weight: 700; margin: 0 0 2px; }
.me-meta { font-size: 12px; color: var(--text-light, #787774); margin: 0 0 8px; }
.me-meta strong { color: var(--text, #111); }
.me-zones { display: flex; gap: 4px; flex-wrap: wrap; }
.badge { font-size: 10px; padding: 2px 8px; border-radius: 999px; }
.badge-healthy { background: #E1F3FE; color: #1F6C9F; }
.badge-lose_weight { background: #FDEBEC; color: #9F2F2D; }
.badge-gain_muscle { background: #EDF3EC; color: #346538; }

.me-stats {
  display: flex; margin-bottom: 14px; padding: 6px 4px;
}
.me-stat {
  flex: 1; text-align: center; padding: 10px 4px;
  border-right: 1px solid var(--border, #EAEAEA);
  cursor: pointer;
}
.me-stat:last-child { border-right: none; }
.me-stat strong { display: block; font-size: 18px; color: var(--text, #111); }
.me-stat small { font-size: 11px; color: var(--text-light, #787774); font-weight: 400; }
.me-stat span { font-size: 11px; color: var(--text-light, #787774); }

.me-menu { padding: 6px 4px; margin-bottom: 18px; }
.me-item {
  display: flex; align-items: center; gap: 12px;
  padding: 13px 10px; cursor: pointer;
  border-bottom: 1px solid var(--border, #EAEAEA);
  -webkit-tap-highlight-color: transparent;
}
.me-item:last-child { border-bottom: none; }
.me-item:active { background: #F7F6F3; }
.me-item__icon {
  width: 32px; height: 32px; border-radius: 9px;
  display: flex; align-items: center; justify-content: center; font-size: 15px;
  flex-shrink: 0;
}
.me-item__label { flex: 1; font-size: 15px; color: var(--text, #111); }
.me-item__arrow { color: #CcCcCc; font-size: 20px; }

.me-logout {
  background: #fff; color: var(--danger, #E74C3C);
  border: 1px solid var(--border, #EAEAEA); border-radius: 10px;
  min-height: 46px; font-size: 15px; font-weight: 600;
}
.me-logout:active { background: #FDEBEC; }
</style>
