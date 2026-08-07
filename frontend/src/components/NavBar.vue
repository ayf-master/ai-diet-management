<template>
  <nav class="navbar">
    <div class="nav-inner">
      <router-link :to="isAdmin ? '/admin/foods' : '/dashboard'" class="nav-brand">食</router-link>

      <div v-if="!isAdmin" class="nav-links">
        <router-link to="/dashboard" class="nav-link">首页</router-link>
        <router-link to="/my-foods" class="nav-link">食材</router-link>
        <router-link to="/my-recipes" class="nav-link">食谱</router-link>
        <router-link to="/meal" class="nav-link">打卡</router-link>
        <router-link to="/stats" class="nav-link">统计</router-link>
        <router-link to="/ai-plan" class="nav-link">AI分析</router-link>
        <router-link to="/settings" class="nav-link">设置</router-link>
      </div>

      <div v-else class="nav-links">
        <router-link to="/admin/foods" class="nav-link">食材管理</router-link>
        <router-link to="/admin/recipes" class="nav-link">食谱管理</router-link>
      </div>

      <div class="nav-right">
        <router-link to="/dashboard" class="nav-home-btn">返回主页</router-link>
        <span class="nav-user">{{ username }}</span>
        <button class="btn btn-sm" style="background:#111;color:#fff;border:none;padding:4px 12px;border-radius:4px" @click="logout">退出</button>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const user = JSON.parse(sessionStorage.getItem('user') || '{}')
const admin = JSON.parse(sessionStorage.getItem('admin') || '{}')

const isAdmin = computed(() => !!admin.admin_id)
const username = computed(() => {
  if (isAdmin.value) return admin.nickname || admin.account || '管理员'
  return user.nickname || user.account || '用户'
})

function logout() {
  sessionStorage.clear()
  router.push('/login')
}
</script>

<style scoped>
.navbar {
  position: fixed; top: 0; left: 0; right: 0; height: 56px;
  background: #fff; border-bottom: 1px solid #EAEAEA;
  z-index: 100;
}
.nav-inner {
  max-width: 1100px; margin: 0 auto; padding: 0 16px;
  height: 100%; display: flex; align-items: center; gap: 20px;
}
.nav-brand {
  font-weight: 700; font-size: 18px; color: #111; white-space: nowrap;
  width: 32px; height: 32px; background: #111; color: #fff;
  display: flex; align-items: center; justify-content: center;
  border-radius: 6px; text-decoration: none;
}
.nav-links { display: flex; gap: 2px; flex: 1; }
.nav-link {
  padding: 6px 12px; border-radius: 4px;
  font-size: 13px; color: #555; font-weight: 500; transition: all 0.15s;
  text-decoration: none;
}
.nav-link:hover { background: #F7F6F3; color: #111; }
.nav-link.router-link-active { background: #111; color: #fff; }
.nav-right { display: flex; align-items: center; gap: 12px; }
.nav-user { font-size: 13px; color: #787774; }
.nav-home-btn {
  font-size: 13px; color: #111; font-weight: 500; text-decoration: none;
  padding: 5px 12px; border: 1px solid #EAEAEA; border-radius: 4px;
  background: #fff; transition: all 0.15s;
}
.nav-home-btn:hover { background: #F7F6F3; border-color: #111; }
@media (max-width: 640px) {
  .nav-link { padding: 4px 8px; font-size: 12px; }
  .nav-user { display: none; }
}
</style>
