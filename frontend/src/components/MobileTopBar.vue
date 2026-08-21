<template>
  <header class="m-topbar">
    <div class="m-topbar__brand">食</div>
    <div class="m-topbar__greet">
      <span class="m-topbar__hi">Hi, {{ nickname }}</span>
      <span class="m-topbar__sub">{{ subText }}</span>
    </div>
    <div class="m-topbar__avatar">
      <img v-if="avatarUrl" :src="avatarUrl" alt="头像" />
      <span v-else>{{ letter }}</span>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  user: { type: Object, default: () => ({}) },
})

const nickname = computed(() => props.user.nickname || props.user.account || '用户')
const letter = computed(() => (nickname.value || '用')[0])
const subText = computed(() => {
  const g = props.user.diet_goals || [props.user.diet_goal || 'healthy']
  const map = { healthy: '健康饮食', lose_weight: '减脂', gain_muscle: '增肌' }
  return (g[0] && map[g[0]]) || '健康饮食'
})
const avatarUrl = computed(() => {
  const u = props.user.avatar_url
  if (!u) return ''
  if (u.startsWith('http')) return u
  return `http://localhost:9876${u}`
})
</script>

<style scoped>
.m-topbar {
  position: fixed;
  top: 0; left: 0; right: 0;
  height: calc(52px + env(safe-area-inset-top, 0px));
  padding-top: env(safe-area-inset-top, 0px);
  display: flex;
  align-items: center;
  gap: 10px;
  padding-left: 16px;
  padding-right: 16px;
  background: #fff;
  border-bottom: 1px solid var(--border, #EAEAEA);
  z-index: 200;
}
.m-topbar__brand {
  width: 32px; height: 32px;
  background: var(--primary, #111); color: #fff;
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 16px;
  flex-shrink: 0;
}
.m-topbar__greet {
  display: flex; flex-direction: column;
  flex: 1; min-width: 0;
}
.m-topbar__hi {
  font-size: 15px; font-weight: 600; color: var(--text, #111);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.m-topbar__sub {
  font-size: 11px; color: var(--text-light, #787774);
}
.m-topbar__avatar {
  width: 34px; height: 34px; border-radius: 50%;
  background: #111; color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 14px;
  overflow: hidden; flex-shrink: 0;
}
.m-topbar__avatar img { width: 100%; height: 100%; object-fit: cover; }
</style>
