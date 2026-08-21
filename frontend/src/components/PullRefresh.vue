<template>
  <div class="pr" ref="el">
    <div class="pr__spacer" :class="{ 'pr__spacer--dragging': dragging }" :style="{ height: spacerH + 'px' }">
      <div class="pr__indicator">
        <span class="pr__spinner" :class="{ spin: refreshing }"></span>
        <span class="pr__text">{{ text }}</span>
      </div>
    </div>
    <div class="pr__content">
      <slot />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { runPullRefresh } from '../composables/pullRefresh.js'

const el = ref(null)
const drag = ref(0)            // 当前下拉位移（px）
const dragging = ref(false)    // 是否正在手指拖动
const refreshing = ref(false)   // 是否处于刷新加载中

const THRESHOLD = 60           // 触发刷新的下拉距离
const MAX_PULL = 90            // 最大可视下拉距离

const spacerH = computed(() => (refreshing.value ? 52 : drag.value))
const text = computed(() => {
  if (refreshing.value) return '刷新中…'
  if (drag.value >= THRESHOLD) return '松开刷新'
  return '下拉刷新'
})

let startY = 0
let tracking = false

function onTouchStart(e) {
  if (refreshing.value) return
  // 仅在滚动到顶部时允许下拉刷新
  if (el.value && el.value.scrollTop <= 0) {
    tracking = true
    startY = e.touches[0].clientY
  }
}

function onTouchMove(e) {
  if (!tracking || refreshing.value) return
  const dy = e.touches[0].clientY - startY
  if (dy <= 0) {
    // 向上滑动（正常浏览），取消跟踪
    drag.value = 0
    tracking = false
    return
  }
  // 阻止浏览器默认的下拉/橡皮筋效果
  if (e.cancelable) e.preventDefault()
  dragging.value = true
  // 阻尼系数，越拉越“沉”
  drag.value = Math.min(dy * 0.5, MAX_PULL)
}

function onTouchEnd() {
  if (!tracking) return
  tracking = false
  dragging.value = false
  if (drag.value >= THRESHOLD) {
    refreshing.value = true
    drag.value = 0
    runPullRefresh().finally(() => {
      refreshing.value = false
    })
  } else {
    drag.value = 0
  }
}

onMounted(() => {
  const node = el.value
  if (!node) return
  // passive:false 才能让 preventDefault 生效
  node.addEventListener('touchstart', onTouchStart, { passive: true })
  node.addEventListener('touchmove', onTouchMove, { passive: false })
  node.addEventListener('touchend', onTouchEnd, { passive: true })
  node.addEventListener('touchcancel', onTouchEnd, { passive: true })
})

onBeforeUnmount(() => {
  const node = el.value
  if (!node) return
  node.removeEventListener('touchstart', onTouchStart)
  node.removeEventListener('touchmove', onTouchMove)
  node.removeEventListener('touchend', onTouchEnd)
  node.removeEventListener('touchcancel', onTouchEnd)
})
</script>

<style scoped>
.pr {
  height: 100%;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-y: contain; /* 阻止 iOS 滚动链到外层 */
  position: relative;
}
.pr__spacer {
  height: 0;
  overflow: hidden;
  transition: height 0.22s ease;
}
.pr__spacer--dragging { transition: none; }
.pr__indicator {
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--text-light, #787774);
  font-size: 13px;
}
.pr__spinner {
  width: 16px; height: 16px;
  border: 2px solid #ddd;
  border-top-color: var(--primary, #111);
  border-radius: 50%;
}
.pr__spinner.spin { animation: pr-spin 0.7s linear infinite; }
@keyframes pr-spin { to { transform: rotate(360deg); } }
</style>
