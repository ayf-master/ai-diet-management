<template>
  <div id="app-root">
    <NavBar v-if="showNav" />
    <main :class="{ 'with-nav': showNav }">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import NavBar from './components/NavBar.vue'

const route = useRoute()
const showNav = computed(() => !['Login', 'AdminLogin', 'ForgotPassword'].includes(route.name))
</script>
