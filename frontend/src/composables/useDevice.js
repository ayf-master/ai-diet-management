// 设备类型检测：根据视口宽度判断是否处于移动端（手机）布局
import { ref, onMounted, onBeforeUnmount } from 'vue'

export function useDevice() {
  const isMobile = ref(false)
  let mql = null

  function update(e) {
    isMobile.value = e.matches
  }

  onMounted(() => {
    // 主流手机竖屏宽度一般 ≤ 768px；平板/桌面走原布局
    mql = window.matchMedia('(max-width: 768px)')
    isMobile.value = mql.matches
    // 监听旋转 / 窗口缩放，实时切换桌面-移动外壳
    mql.addEventListener('change', update)
  })

  onBeforeUnmount(() => {
    if (mql) mql.removeEventListener('change', update)
  })

  return isMobile
}
