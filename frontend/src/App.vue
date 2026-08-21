<template>
  <div id="app-root" :class="{ 'mobile-shell': mobileShell }">
    <!-- 移动端：顶部细栏 + 下拉刷新滚动区 + 底部 Tab 导航 -->
    <template v-if="mobileShell">
      <MobileTopBar :user="userObj" />
      <PullRefresh>
        <router-view />
      </PullRefresh>
      <MobileNav />
    </template>

    <!-- 桌面端：保持原有顶部导航，不做改动 -->
    <template v-else>
      <NavBar v-if="showNav" />
      <main :class="{ 'with-nav': showNav }">
        <router-view />
      </main>
    </template>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import NavBar from './components/NavBar.vue'
import MobileTopBar from './components/MobileTopBar.vue'
import MobileNav from './components/MobileNav.vue'
import PullRefresh from './components/PullRefresh.vue'
import { useDevice } from './composables/useDevice.js'

const route = useRoute()
const isMobile = useDevice()

const showNav = computed(() => !['Login', 'AdminLogin', 'ForgotPassword'].includes(route.name))

// 仅当用户（非管理员）登录时，移动端才启用底部 Tab 导航；
// 管理员页在移动端沿用桌面顶部导航，避免重复导航层级。
const isUser = ref(false)
function refreshUser() {
  isUser.value = !!sessionStorage.getItem('user')
}
refreshUser()
watch(route, refreshUser)

const mobileShell = computed(() => showNav.value && isMobile.value && isUser.value)
const userObj = computed(() => JSON.parse(sessionStorage.getItem('user') || '{}'))
</script>
