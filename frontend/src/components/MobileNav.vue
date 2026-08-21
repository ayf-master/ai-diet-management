<template>
  <nav class="m-nav">
    <router-link
      v-for="item in tabs"
      :key="item.to"
      :to="item.to"
      class="m-tab"
      :class="{ 'm-tab--active': isActive(item) }"
    >
      <span class="m-tab__icon" v-html="item.icon"></span>
      <span class="m-tab__label">{{ item.label }}</span>
    </router-link>
  </nav>
</template>

<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()

const tabs = [
  {
    to: '/dashboard', label: '首页',
    icon: '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/></svg>',
  },
  {
    to: '/my-foods', label: '食材',
    icon: '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 3v8a3 3 0 0 0 6 0V3"/><path d="M8 3v18"/><path d="M19 3c-2 0-3 2-3 5s1 4 3 4v9"/></svg>',
  },
  {
    to: '/my-recipes', label: '食谱',
    icon: '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h16v4a8 8 0 0 1-16 0V5z"/><path d="M4 5H3v3a3 3 0 0 0 3 3"/><path d="M20 5h1v3a3 3 0 0 1-3 3"/><path d="M9 21h6"/></svg>',
  },
  {
    to: '/meal', label: '打卡',
    icon: '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
  },
  {
    to: '/me', label: '我的',
    icon: '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-6 8-6s8 2 8 6"/></svg>',
  },
]

// 精确匹配当前路由（避免 /my-foods 与 /my-recipes 互相高亮）
function isActive(item) {
  return route.path === item.to
}
</script>

<style scoped>
.m-nav {
  position: fixed;
  left: 0; right: 0; bottom: 0;
  height: calc(58px + env(safe-area-inset-bottom, 0px));
  padding-bottom: env(safe-area-inset-bottom, 0px);
  display: flex;
  background: #fff;
  border-top: 1px solid var(--border, #EAEAEA);
  z-index: 200;
  /* 桌面端安全阴影，移动端更轻薄 */
  box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.04);
}
.m-tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  text-decoration: none;
  color: var(--text-light, #787774);
  /* 触控目标足够大 */
  min-height: 44px;
  -webkit-tap-highlight-color: transparent;
  transition: color 0.15s;
}
.m-tab__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 24px;
}
.m-tab__label {
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.02em;
}
.m-tab--active {
  color: var(--primary, #111);
}
.m-tab--active .m-tab__icon {
  transform: translateY(-1px);
}
.m-tab:active {
  opacity: 0.6;
}
</style>
