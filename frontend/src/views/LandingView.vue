<template>
  <div class="landing" ref="rootRef">
    <!-- 顶部导航 -->
    <header class="site-header" :class="{ scrolled: isScrolled, 'nav-open': menuOpen }">
      <div class="header-inner">
        <router-link to="/" class="brand">
          <span class="brand-mark" v-html="brandIcon"></span>
          <span class="brand-name">食律</span>
        </router-link>

        <nav class="nav-links" :class="{ open: menuOpen }">
          <a href="#features" @click="closeMenu">核心功能</a>
          <a href="#why" @click="closeMenu">为什么选我们</a>
          <a href="#scenes" @click="closeMenu">使用场景</a>
          <a href="#how" @click="closeMenu">如何使用</a>
          <div class="nav-actions-mobile">
            <router-link to="/login" class="btn btn-ghost" @click="closeMenu">登录</router-link>
            <router-link to="/login?mode=register" class="btn btn-dark" @click="closeMenu">注册</router-link>
          </div>
        </nav>

        <div class="nav-actions">
          <router-link to="/login" class="btn btn-ghost">登录</router-link>
          <router-link to="/login?mode=register" class="btn btn-dark btn-cta">注册 <span class="arrow">→</span></router-link>
        </div>

        <button class="menu-toggle" @click="menuOpen = !menuOpen" :aria-expanded="menuOpen" aria-label="菜单">
          <span></span><span></span><span></span>
        </button>
      </div>
    </header>

    <!-- 首屏 -->
    <section class="hero">
      <div class="hero-glow"></div>
      <div class="hero-grid-bg"></div>
      <div class="hero-inner">
        <div class="hero-copy" :class="{ ready: heroReady }">
          <div class="eyebrow"><span class="dot"></span> AI 驱动的饮食健康管理</div>
          <h1 class="hero-title">
            吃得明白，<br />
            <span class="accent">瘦得健康。</span>
          </h1>
          <p class="hero-desc">
            从热量计算到 AI 定制方案，让每一餐都有据可依。<br class="desktop-break" />
            不用再靠意志力硬扛，把健康变成一种轻松的日常。
          </p>
          <div class="hero-actions">
            <router-link to="/login?mode=register" class="btn btn-dark btn-lg">立即注册 <span class="arrow">→</span></router-link>
            <a href="#features" class="btn btn-outline btn-lg">了解功能</a>
          </div>
          <div class="hero-trust">
            <span><span class="check">✓</span> 无需专业知识</span>
            <span><span class="check">✓</span> 3 分钟记录一餐</span>
            <span><span class="check">✓</span> 数据只属于你</span>
          </div>
        </div>

        <!-- 产品界面预览（纯 CSS / SVG） -->
        <div class="hero-visual" :class="{ ready: heroReady }">
          <div class="app-card">
            <div class="app-topbar">
              <div class="app-dots"><i></i><i></i><i></i></div>
              <span class="app-url">食律 · 今日概览</span>
            </div>
            <div class="app-body">
              <div class="app-greeting">
                <div>
                  <p class="app-hi">下午好，张三</p>
                  <p class="app-sub">今天也要好好吃饭呀</p>
                </div>
                <div class="app-avatar">张</div>
              </div>
              <div class="app-ring-row">
                <div class="app-ring">
                  <svg viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="42" fill="none" stroke="#EEE" stroke-width="9"/>
                    <circle cx="50" cy="50" r="42" fill="none" stroke="#2ECC71" stroke-width="9"
                      stroke-dasharray="264" stroke-dashoffset="86" stroke-linecap="round" transform="rotate(-90 50 50)"/>
                  </svg>
                  <div class="app-ring-text"><strong>1280</strong><small>/ 1800 kcal</small></div>
                </div>
                <div class="app-ring-info">
                  <div class="app-info-line"><span>今日摄入</span><strong>1280 kcal</strong></div>
                  <div class="app-info-line"><span>还可摄入</span><strong class="green">520 kcal</strong></div>
                  <div class="app-info-line"><span>目标进度</span><strong>71%</strong></div>
                </div>
              </div>
              <div class="app-meals">
                <div class="app-meal done"><span>早餐</span><b>420</b></div>
                <div class="app-meal done"><span>午餐</span><b>680</b></div>
                <div class="app-meal"><span>晚餐</span><b>—</b></div>
                <div class="app-meal"><span>加餐</span><b>180</b></div>
              </div>
              <div class="app-chart">
                <div class="app-chart-head"><span>体重趋势</span><span class="green">↓ 2.4 kg</span></div>
                <svg viewBox="0 0 260 60" preserveAspectRatio="none">
                  <path d="M0 12 C 30 10, 45 24, 70 22 S 110 34, 135 32 S 180 44, 205 41 S 240 52, 260 50"
                    fill="none" stroke="#2ECC71" stroke-width="2.5" stroke-linecap="round"/>
                  <circle cx="260" cy="50" r="4" fill="#fff" stroke="#2ECC71" stroke-width="2.5"/>
                </svg>
              </div>
            </div>
          </div>
          <div class="float-badge badge-ai"><span class="badge-ic">✦</span><div><b>AI 方案已生成</b><small>专属减脂计划</small></div></div>
          <div class="float-badge badge-streak"><span class="badge-fire">🔥</span><div><b>连续打卡 7 天</b><small>继续保持！</small></div></div>
        </div>
      </div>

      <a href="#features" class="scroll-hint" aria-label="向下滚动">
        <span class="mouse"><i></i></span>
        <span>向下探索</span>
      </a>
    </section>

    <!-- 数据条 -->
    <section class="stats-strip">
      <div class="stats-inner">
        <div class="stat-item reveal"><strong>3</strong><span>大饮食专区</span></div>
        <div class="stat-item reveal" style="--d:.08s"><strong>8+</strong><span>项核心功能</span></div>
        <div class="stat-item reveal" style="--d:.16s"><strong>AI</strong><span>智能定制方案</span></div>
        <div class="stat-item reveal" style="--d:.24s"><strong>100%</strong><span>数据自主掌控</span></div>
      </div>
    </section>

    <!-- 核心功能 -->
    <section id="features" class="section features-section">
      <div class="section-head reveal">
        <span class="section-tag">核心功能</span>
        <h2 class="section-title">管理健康，你需要的一切都在这里</h2>
        <p class="section-desc">从记录到分析，从方案到陪伴，覆盖饮食管理的完整链路。</p>
      </div>
      <div class="feature-grid">
        <article v-for="(f, i) in features" :key="f.title" class="feature-card reveal" :style="{ '--d': (i % 3) * 0.08 + 's' }">
          <div class="feature-icon" v-html="f.icon"></div>
          <h3>{{ f.title }}</h3>
          <p>{{ f.desc }}</p>
          <span class="feature-index">0{{ i + 1 }}</span>
        </article>
      </div>
    </section>

    <!-- 为什么选我们 -->
    <section id="why" class="section why-section">
      <div class="why-inner">
        <div class="why-head reveal">
          <span class="section-tag light">差异化优势</span>
          <h2 class="section-title">不是又一个<br /> calorie 计数器</h2>
          <p class="section-desc">我们把营养学的严谨和 AI 的灵活放在一起，做真正能长期用下去的饮食管理。</p>
        </div>
        <div class="why-list">
          <div v-for="(w, i) in why" :key="w.title" class="why-item reveal" :style="{ '--d': i * 0.1 + 's' }">
            <div class="why-num">0{{ i + 1 }}</div>
            <div class="why-text">
              <h3>{{ w.title }}</h3>
              <p>{{ w.desc }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 使用场景 / tab 切换 -->
    <section id="scenes" class="section scenes-section">
      <div class="section-head reveal">
        <span class="section-tag">使用场景</span>
        <h2 class="section-title">你的目标，就是我们的方案</h2>
        <p class="section-desc">不同阶段、不同目标，饮食策略本就该不一样。</p>
      </div>
      <div class="scene-box reveal">
        <div class="scene-tabs" role="tablist">
          <button v-for="s in sceneList" :key="s.key" role="tab" :aria-selected="activeScene === s.key"
            :class="{ active: activeScene === s.key }" @click="activeScene = s.key">
            <span class="scene-tab-ic">{{ s.icon }}</span>{{ s.label }}
          </button>
        </div>
        <div class="scene-panel">
          <Transition name="scene" mode="out-in">
            <div :key="activeScene" class="scene-content">
              <div class="scene-copy">
                <h3>{{ currentScene.title }}</h3>
                <p class="scene-lead">{{ currentScene.lead }}</p>
                <ul class="scene-points">
                  <li v-for="p in currentScene.points" :key="p"><span class="check">✓</span>{{ p }}</li>
                </ul>
                <router-link to="/login?mode=register" class="link-arrow">开启我的方案 <span>→</span></router-link>
              </div>
              <div class="scene-metric">
                <div class="metric-ring">
                  <svg viewBox="0 0 120 120">
                    <circle cx="60" cy="60" r="52" fill="none" stroke="#eee" stroke-width="10"/>
                    <circle cx="60" cy="60" r="52" fill="none" :stroke="currentScene.color" stroke-width="10"
                      stroke-linecap="round" :stroke-dasharray="327" :stroke-dashoffset="327 * (1 - currentScene.percent / 100)"
                      transform="rotate(-90 60 60)" class="metric-progress"/>
                  </svg>
                  <div class="metric-text"><strong>{{ currentScene.percent }}%</strong><small>{{ currentScene.metricLabel }}</small></div>
                </div>
                <p>{{ currentScene.metricNote }}</p>
              </div>
            </div>
          </Transition>
        </div>
      </div>
    </section>

    <!-- 使用流程 -->
    <section id="how" class="section how-section">
      <div class="section-head reveal">
        <span class="section-tag">如何使用</span>
        <h2 class="section-title">四步，开启你的健康饮食</h2>
      </div>
      <div class="steps">
        <div v-for="(s, i) in steps" :key="s.title" class="step reveal" :style="{ '--d': i * 0.08 + 's' }">
          <div class="step-num">{{ String(i + 1).padStart(2, '0') }}</div>
          <div class="step-line" v-if="i < steps.length - 1"></div>
          <h3>{{ s.title }}</h3>
          <p>{{ s.desc }}</p>
        </div>
      </div>
    </section>

    <!-- 底部 CTA -->
    <section class="cta-section">
      <div class="cta-inner reveal">
        <div class="cta-glow"></div>
        <span class="section-tag light">现在开始</span>
        <h2>从今天起，好好吃饭。</h2>
        <p>几分钟建立你的专属饮食档案，让改变从一个决定开始。</p>
        <div class="cta-actions">
          <router-link to="/login?mode=register" class="btn btn-light btn-lg">立即注册 <span class="arrow">→</span></router-link>
          <router-link to="/login" class="btn btn-outline-light btn-lg">已有账号，登录</router-link>
        </div>
      </div>
    </section>

    <!-- 页脚 -->
    <footer class="site-footer">
      <div class="footer-inner">
        <div class="footer-brand">
          <span class="brand-mark" v-html="brandIcon"></span>
          <div><strong>食律</strong><p>一切为了你的健康</p></div>
        </div>
        <p class="footer-copy">AI 辅助减脂饮食管理系统 · 用科学和数据，让健康成为一种习惯</p>
        <router-link to="/admin/login" class="footer-admin">管理员入口</router-link>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

const brandIcon = '<svg viewBox="0 0 64 64" width="22" height="22" fill="none"><path d="M20 18h24M24 18v10M32 18v10M40 18v10M20 28h24" stroke="#2ECC71" stroke-width="3.5" stroke-linecap="round"/><path d="M22 28c0 9 4.5 14 10 14s10-5 10-14" stroke="#2ECC71" stroke-width="3.5" stroke-linecap="round"/><path d="M32 42v5M27 47h10" stroke="#2ECC71" stroke-width="3.5" stroke-linecap="round"/><circle cx="45" cy="19" r="3.5" fill="#2ECC71"/></svg>'

const rootRef = ref(null)
const heroReady = ref(false)
const isScrolled = ref(false)
const menuOpen = ref(false)
const activeScene = ref('lose')

const features = [
  { title: 'AI 智能膳食方案', desc: '输入身体数据，AI 结合你的目标生成专属热量与食谱建议。', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l1.9 5.6L19.5 10l-5.6 1.9L12 17.5l-1.9-5.6L4.5 10l5.6-1.4L12 3z"/><path d="M19 16l.8 2.2L22 19l-2.2.8L19 22l-.8-2.2L16 19l2.2-.8L19 16z"/></svg>' },
  { title: '三餐快捷打卡', desc: '选食材、填重量，热量自动汇总，记录一餐只要几秒钟。', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 3v7a3 3 0 006 0V3M7 3v18"/><path d="M17 3c-2 2-2 6 0 8v10"/></svg>' },
  { title: '体重趋势追踪', desc: '曲线直观呈现体重变化，目标进度看得见，坚持更有动力。', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M3 17l6-6 4 4 8-8"/><path d="M21 7v5h-5"/></svg>' },
  { title: '可视化数据洞察', desc: '周报统计摄入与营养结构，看懂自己真实的饮食习惯。', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M7 15v-3M12 15V8M17 15v-5"/></svg>' },
  { title: 'AI 健康助手', desc: '关于吃什么的疑问，随时提问，获得贴合你情况的回答。', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a8 8 0 01-8 8H7l-4 3 1.2-4A8 8 0 1121 12z"/><path d="M9 11h.01M15 11h.01M9 15c2 1.5 4 1.5 6 0"/></svg>' },
  { title: '专属食材与食谱库', desc: '收藏常用食材和菜品，自带禁忌提醒，越用越懂你。', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5a2 2 0 012-2h12a2 2 0 012 2v16l-8-4-8 4V5z"/></svg>' },
]

const why = [
  { title: '科学的计算内核', desc: '基于基础代谢率（BMR）与每日总消耗（TDEE），结合身高、体重、年龄与活动量精确推算，不是拍脑袋的数字。' },
  { title: 'AI 真正懂你的身体', desc: '方案会考虑你的疾病禁忌与营养阈值，自动生成可执行的食谱建议，而不是千篇一律的通用模板。' },
  { title: '三大专区，各走各的路', desc: '健康饮食、减脂、增肌目标不同，策略也不同。选对自己的专区，让每一步都走在正确的方向上。' },
]

const scenes = {
  lose: {
    icon: '◐', label: '减脂', title: '科学减脂，稳稳掉秤', color: '#2ECC71',
    lead: '以合理的热量缺口为核心，保证营养不流失，让减重可持续、不反弹。',
    points: ['自动计算安全热量缺口', '高蛋白低脂食谱优先推荐', '体重曲线与目标进度实时追踪'],
    percent: 72, metricLabel: '目标完成度', metricNote: '平均 8 周达成阶段性目标',
  },
  gain: {
    icon: '◑', label: '增肌', title: '增肌塑形，吃够每一克蛋白', color: '#3498DB',
    lead: '以蛋白质摄入和热量盈余为重点，配合训练目标，让每一分努力都有回报。',
    points: ['蛋白质优先的食谱组合', '合理热量盈余，避免多余脂肪', '追踪每日三大营养素配比'],
    percent: 65, metricLabel: '蛋白达标率', metricNote: '科学配比，肌肉长得扎实',
  },
  healthy: {
    icon: '◒', label: '健康饮食', title: '均衡营养，日常好习惯', color: '#BA7517',
    lead: '不追求极端数字，关注饮食结构与长期习惯，把健康变成生活的一部分。',
    points: ['均衡的三大营养素结构', '疾病禁忌与过敏提醒', '温和可持续的日常建议'],
    percent: 88, metricLabel: '营养均衡度', metricNote: '让好好吃饭成为自然的事',
  },
}

const sceneList = computed(() => [
  { key: 'lose', ...scenes.lose }, { key: 'gain', ...scenes.gain }, { key: 'healthy', ...scenes.healthy },
])
const currentScene = computed(() => scenes[activeScene.value])

const steps = [
  { title: '填写身体数据', desc: '身高、体重、年龄、活动量与目标，几分钟即可完成。' },
  { title: '获取专属方案', desc: 'AI 根据你的情况，生成热量目标与饮食建议。' },
  { title: '记录每日三餐', desc: '选食材、记重量，热量与营养自动汇总。' },
  { title: '查看变化调整', desc: '用数据看懂趋势，让方案跟着你的进步一起进化。' },
]

let observer = null
function onScroll() {
  isScrolled.value = window.scrollY > 24
}
function closeMenu() {
  menuOpen.value = false
}

onMounted(() => {
  window.addEventListener('scroll', onScroll, { passive: true })
  onScroll()
  requestAnimationFrame(() => { heroReady.value = true })

  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  observer = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (e.isIntersecting) {
        e.target.classList.add('revealed')
        observer.unobserve(e.target)
      }
    })
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' })
  rootRef.value?.querySelectorAll('.reveal').forEach((el) => observer.observe(el))
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll)
  observer?.disconnect()
})
</script>

<style scoped>
.landing { --green: #2ECC71; --green-dark: #1a9e56; overflow: hidden; background: #F7F6F3; }

/* 通用 */
.btn { display: inline-flex; align-items: center; justify-content: center; gap: 8px; text-decoration: none; border-radius: 8px; font-weight: 600; cursor: pointer; border: 1px solid transparent; transition: transform .2s ease, box-shadow .2s ease, background .2s ease, border-color .2s ease; }
.btn:active { transform: scale(.97); }
.btn-lg { padding: 14px 26px; font-size: 15px; }
.arrow { transition: transform .2s ease; }
.btn:hover .arrow, .link-arrow:hover span { transform: translateX(4px); }
.btn-dark { background: #111; color: #fff; }
.btn-dark:hover { background: #333; box-shadow: 0 8px 20px rgba(0,0,0,.18); transform: translateY(-2px); }
.btn-ghost { background: transparent; color: #111; }
.btn-ghost:hover { background: #EDECE7; }
.btn-outline { background: transparent; border-color: #D5D4CE; color: #111; }
.btn-outline:hover { border-color: #111; background: #fff; transform: translateY(-2px); }
.btn-light { background: #fff; color: #111; }
.btn-light:hover { transform: translateY(-2px); box-shadow: 0 10px 26px rgba(0,0,0,.22); }
.btn-outline-light { background: transparent; border-color: rgba(255,255,255,.4); color: #fff; }
.btn-outline-light:hover { border-color: #fff; background: rgba(255,255,255,.08); }
.reveal { opacity: 0; transform: translateY(28px); transition: opacity .7s cubic-bezier(.2,.7,.2,1) var(--d, 0s), transform .7s cubic-bezier(.2,.7,.2,1) var(--d, 0s); }
.reveal.revealed { opacity: 1; transform: none; }

/* 顶部导航 */
.site-header { position: fixed; inset: 0 0 auto; height: 68px; z-index: 100; transition: background .3s ease, border-color .3s ease, box-shadow .3s ease; border-bottom: 1px solid transparent; }
.site-header.scrolled { background: rgba(247,246,243,.82); backdrop-filter: saturate(180%) blur(16px); -webkit-backdrop-filter: saturate(180%) blur(16px); border-color: #E6E5DF; }
.header-inner { max-width: 1160px; height: 100%; margin: 0 auto; padding: 0 24px; display: flex; align-items: center; gap: 32px; }
.brand { display: flex; align-items: center; gap: 10px; text-decoration: none; }
.brand-mark { width: 34px; height: 34px; background: #111; color: #fff; border-radius: 9px; display: flex; align-items: center; justify-content: center; font-size: 17px; font-weight: 700; }
.brand-name { font-size: 18px; font-weight: 700; color: #111; letter-spacing: .02em; }
.nav-links { display: flex; align-items: center; gap: 28px; flex: 1; }
.nav-links > a { color: #555; font-size: 14px; font-weight: 500; text-decoration: none; transition: color .2s; position: relative; }
.nav-links > a::after { content: ''; position: absolute; left: 0; bottom: -6px; width: 0; height: 1.5px; background: #111; transition: width .25s ease; }
.nav-links > a:hover { color: #111; }
.nav-links > a:hover::after { width: 100%; }
.nav-actions { display: flex; align-items: center; gap: 10px; }
.nav-actions .btn { padding: 9px 18px; font-size: 13px; }
.nav-actions-mobile { display: none; }
.menu-toggle { display: none; flex-direction: column; gap: 5px; background: none; border: none; cursor: pointer; padding: 6px; margin-left: auto; }
.menu-toggle span { width: 22px; height: 2px; background: #111; border-radius: 2px; transition: transform .3s ease, opacity .3s ease; }
.nav-open .menu-toggle span:nth-child(1) { transform: translateY(7px) rotate(45deg); }
.nav-open .menu-toggle span:nth-child(2) { opacity: 0; }
.nav-open .menu-toggle span:nth-child(3) { transform: translateY(-7px) rotate(-45deg); }

/* 首屏 */
.hero { position: relative; min-height: 100vh; display: flex; align-items: center; padding: 120px 24px 80px; }
.hero-glow { position: absolute; width: 780px; height: 780px; top: -280px; right: -160px; background: radial-gradient(circle, rgba(46,204,113,.15) 0%, rgba(46,204,113,.04) 40%, transparent 68%); pointer-events: none; }
.hero-grid-bg { position: absolute; inset: 0; background-image: linear-gradient(rgba(0,0,0,.028) 1px, transparent 1px), linear-gradient(90deg, rgba(0,0,0,.028) 1px, transparent 1px); background-size: 48px 48px; mask-image: linear-gradient(to bottom, rgba(0,0,0,.7), transparent 78%); -webkit-mask-image: linear-gradient(to bottom, rgba(0,0,0,.7), transparent 78%); pointer-events: none; }
.hero-inner { position: relative; max-width: 1160px; margin: 0 auto; width: 100%; display: grid; grid-template-columns: 1.05fr 1fr; gap: 64px; align-items: center; }
.hero-copy { opacity: 0; transform: translateY(24px); transition: opacity .8s ease, transform .8s cubic-bezier(.2,.7,.2,1); }
.hero-copy.ready { opacity: 1; transform: none; }
.eyebrow { display: inline-flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 600; color: var(--green-dark); background: rgba(46,204,113,.1); border: 1px solid rgba(46,204,113,.22); padding: 7px 14px; border-radius: 999px; margin-bottom: 26px; }
.eyebrow .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--green); box-shadow: 0 0 0 4px rgba(46,204,113,.15); }
.hero-title { font-size: clamp(44px, 6vw, 76px); line-height: 1.08; font-weight: 800; letter-spacing: -.03em; color: #111; margin-bottom: 24px; }
.hero-title .accent { position: relative; color: var(--green-dark); white-space: nowrap; }
.hero-title .accent::after { content: ''; position: absolute; left: 2px; right: 2px; bottom: 4px; height: 10px; background: rgba(46,204,113,.2); border-radius: 4px; z-index: -1; }
.hero-desc { font-size: 17px; line-height: 1.8; color: #666; margin-bottom: 34px; }
.hero-actions { display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 30px; }
.hero-trust { display: flex; gap: 22px; flex-wrap: wrap; font-size: 13px; color: #777; }
.hero-trust .check, .scene-points .check { color: var(--green-dark); font-weight: 700; margin-right: 5px; }

/* 产品预览 */
.hero-visual { position: relative; opacity: 0; transform: translateY(36px) scale(.97); transition: opacity .9s ease .15s, transform .9s cubic-bezier(.2,.7,.2,1) .15s; }
.hero-visual.ready { opacity: 1; transform: none; }
.app-card { background: #fff; border-radius: 18px; border: 1px solid #E6E5DF; box-shadow: 0 30px 70px rgba(20,30,20,.14), 0 4px 14px rgba(0,0,0,.05); overflow: hidden; }
.app-topbar { height: 40px; background: #FBFAF8; border-bottom: 1px solid #EEEDE8; display: flex; align-items: center; padding: 0 16px; gap: 14px; }
.app-dots { display: flex; gap: 6px; }
.app-dots i { width: 9px; height: 9px; border-radius: 50%; background: #DDD; }
.app-dots i:first-child { background: #F0A0A0; }
.app-dots i:nth-child(2) { background: #EAD08A; }
.app-url { font-size: 11px; color: #AAA; }
.app-body { padding: 22px; }
.app-greeting { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.app-hi { font-size: 17px; font-weight: 700; color: #111; }
.app-sub { font-size: 11px; color: #999; margin-top: 2px; }
.app-avatar { width: 38px; height: 38px; border-radius: 50%; background: #111; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 700; }
.app-ring-row { display: flex; align-items: center; gap: 22px; padding: 16px; background: #F8FBF9; border: 1px solid #EAF3ED; border-radius: 14px; margin-bottom: 14px; }
.app-ring { position: relative; width: 108px; height: 108px; flex-shrink: 0; }
.app-ring svg { width: 100%; height: 100%; }
.app-ring-text { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.app-ring-text strong { font-size: 22px; color: #111; line-height: 1; }
.app-ring-text small { font-size: 10px; color: #999; margin-top: 4px; }
.app-ring-info { flex: 1; display: flex; flex-direction: column; gap: 11px; }
.app-info-line { display: flex; justify-content: space-between; font-size: 12px; }
.app-info-line span { color: #888; }
.app-info-line strong { color: #111; }
.app-info-line strong.green { color: var(--green-dark); }
.app-meals { display: grid; grid-template-columns: repeat(4,1fr); gap: 8px; margin-bottom: 14px; }
.app-meal { border: 1px solid #EEEDE8; border-radius: 9px; padding: 10px 6px; text-align: center; display: flex; flex-direction: column; gap: 3px; }
.app-meal span { font-size: 10px; color: #999; }
.app-meal b { font-size: 12px; color: #111; }
.app-meal.done { background: #F4FBF6; border-color: #CDEBD8; }
.app-meal.done b { color: var(--green-dark); }
.app-chart { border: 1px solid #EEEDE8; border-radius: 12px; padding: 14px; }
.app-chart-head { display: flex; justify-content: space-between; font-size: 12px; color: #555; margin-bottom: 8px; }
.app-chart-head .green { color: var(--green-dark); font-weight: 700; }
.app-chart svg { width: 100%; height: 54px; }
.float-badge { position: absolute; display: flex; align-items: center; gap: 10px; background: #fff; border: 1px solid #EAE9E3; border-radius: 12px; padding: 10px 14px; box-shadow: 0 12px 30px rgba(0,0,0,.12); animation: float 5s ease-in-out infinite; }
.float-badge b { font-size: 12px; color: #111; display: block; }
.float-badge small { font-size: 10px; color: #999; }
.badge-ai { top: -22px; left: -30px; }
.badge-streak { bottom: 8%; right: -34px; animation-delay: -2.5s; }
.badge-ic { width: 30px; height: 30px; border-radius: 8px; background: rgba(46,204,113,.12); color: var(--green-dark); display: flex; align-items: center; justify-content: center; font-size: 16px; }
.badge-fire { font-size: 20px; }
@keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
.scroll-hint { position: absolute; bottom: 30px; left: 50%; transform: translateX(-50%); display: flex; flex-direction: column; align-items: center; gap: 8px; font-size: 11px; color: #AAA; text-decoration: none; }
.mouse { width: 22px; height: 34px; border: 1.5px solid #CCC; border-radius: 12px; display: flex; justify-content: center; padding-top: 6px; }
.mouse i { width: 3px; height: 7px; background: #AAA; border-radius: 3px; animation: scroll 1.8s ease-in-out infinite; }
@keyframes scroll { 0% { transform: translateY(0); opacity: 1; } 70%,100% { transform: translateY(12px); opacity: 0; } }

/* 数据条 */
.stats-strip { background: #fff; border-top: 1px solid #EEEDE8; border-bottom: 1px solid #EEEDE8; }
.stats-inner { max-width: 1160px; margin: 0 auto; padding: 34px 24px; display: grid; grid-template-columns: repeat(4,1fr); }
.stat-item { text-align: center; display: flex; flex-direction: column; gap: 4px; border-right: 1px solid #EEEDE8; }
.stat-item:last-child { border-right: none; }
.stat-item strong { font-size: 34px; font-weight: 800; color: #111; letter-spacing: -.02em; }
.stat-item span { font-size: 13px; color: #888; }

/* 通用 section */
.section { max-width: 1160px; margin: 0 auto; padding: 110px 24px; }
.section-head { text-align: center; max-width: 620px; margin: 0 auto 56px; }
.section-tag { display: inline-block; font-size: 12px; font-weight: 700; color: var(--green-dark); letter-spacing: .12em; text-transform: uppercase; margin-bottom: 16px; }
.section-tag.light { color: #6EE7A5; }
.section-title { font-size: clamp(30px, 4vw, 46px); font-weight: 800; line-height: 1.2; letter-spacing: -.02em; color: #111; margin-bottom: 16px; }
.section-desc { font-size: 16px; line-height: 1.75; color: #777; }

/* 核心功能 */
.feature-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 18px; }
.feature-card { position: relative; background: #fff; border: 1px solid #EAE9E3; border-radius: 16px; padding: 30px 28px; transition: transform .3s cubic-bezier(.2,.7,.2,1), box-shadow .3s ease, border-color .3s ease; overflow: hidden; }
.feature-card::before { content: ''; position: absolute; inset: auto 0 0 0; height: 3px; background: var(--green); transform: scaleX(0); transition: transform .35s ease; }
.feature-card:hover { transform: translateY(-6px); box-shadow: 0 18px 40px rgba(20,30,20,.09); border-color: #D5EADB; }
.feature-card:hover::before { transform: scaleX(1); }
.feature-icon { width: 48px; height: 48px; border-radius: 12px; background: #F0FAF4; color: var(--green-dark); display: flex; align-items: center; justify-content: center; margin-bottom: 20px; }
.feature-icon svg { width: 24px; height: 24px; }
.feature-card h3 { font-size: 18px; font-weight: 700; color: #111; margin-bottom: 10px; }
.feature-card p { font-size: 14px; line-height: 1.7; color: #777; margin: 0; }
.feature-index { position: absolute; top: 22px; right: 24px; font-size: 13px; font-weight: 700; color: #E5E4DE; }

/* 差异化 */
.why-section { background: #111; color: #fff; max-width: none; }
.why-inner { max-width: 1160px; margin: 0 auto; display: grid; grid-template-columns: 1fr 1fr; gap: 80px; align-items: start; }
.why-head .section-title { color: #fff; }
.why-head .section-desc { color: #9A9A94; }
.why-list { display: flex; flex-direction: column; gap: 4px; }
.why-item { display: flex; gap: 22px; padding: 24px 0; border-bottom: 1px solid rgba(255,255,255,.1); }
.why-item:last-child { border-bottom: none; }
.why-num { font-size: 15px; font-weight: 700; color: var(--green); flex-shrink: 0; padding-top: 3px; }
.why-text h3 { font-size: 18px; font-weight: 700; margin-bottom: 8px; color: #fff; }
.why-text p { font-size: 14px; line-height: 1.75; color: #9A9A94; margin: 0; }

/* 使用场景 */
.scene-box { background: #fff; border: 1px solid #EAE9E3; border-radius: 20px; overflow: hidden; box-shadow: 0 12px 40px rgba(20,30,20,.05); }
.scene-tabs { display: flex; gap: 4px; padding: 10px; background: #FBFAF8; border-bottom: 1px solid #EEEDE8; }
.scene-tabs button { flex: 1; display: flex; align-items: center; justify-content: center; gap: 8px; padding: 14px; font-size: 15px; font-weight: 600; color: #888; background: transparent; border: none; border-radius: 10px; cursor: pointer; transition: background .25s ease, color .25s ease, box-shadow .25s ease; }
.scene-tabs button:hover { color: #111; background: #F1F0EB; }
.scene-tabs button.active { color: #111; background: #fff; box-shadow: 0 2px 10px rgba(0,0,0,.07); }
.scene-tab-ic { font-size: 17px; }
.scene-panel { padding: 48px; }
.scene-content { display: grid; grid-template-columns: 1.2fr .8fr; gap: 48px; align-items: center; }
.scene-enter-active, .scene-leave-active { transition: opacity .3s ease, transform .3s ease; }
.scene-enter-from { opacity: 0; transform: translateY(12px); }
.scene-leave-to { opacity: 0; transform: translateY(-12px); }
.scene-copy h3 { font-size: 28px; font-weight: 800; color: #111; margin-bottom: 12px; }
.scene-lead { font-size: 15px; line-height: 1.75; color: #777; margin-bottom: 22px; }
.scene-points { list-style: none; display: flex; flex-direction: column; gap: 12px; margin-bottom: 26px; }
.scene-points li { font-size: 14px; color: #444; }
.link-arrow { color: var(--green-dark); font-weight: 700; font-size: 14px; text-decoration: none; }
.link-arrow span { display: inline-block; transition: transform .2s ease; }
.metric-ring { position: relative; width: 170px; height: 170px; margin: 0 auto 14px; }
.metric-ring svg { width: 100%; height: 100%; }
.metric-progress { transition: stroke-dashoffset .6s cubic-bezier(.2,.7,.2,1); }
.metric-text { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.metric-text strong { font-size: 36px; font-weight: 800; color: #111; line-height: 1; }
.metric-text small { font-size: 11px; color: #999; margin-top: 6px; }
.scene-metric p { text-align: center; font-size: 13px; color: #888; margin: 0; }

/* 使用流程 */
.steps { display: grid; grid-template-columns: repeat(4,1fr); gap: 20px; }
.step { position: relative; }
.step-num { font-size: 40px; font-weight: 800; color: #E3E2DC; line-height: 1; margin-bottom: 18px; }
.step-line { position: absolute; top: 20px; left: 56px; right: -20px; height: 1px; background: repeating-linear-gradient(90deg,#CCC 0 5px,transparent 5px 10px); }
.step h3 { font-size: 17px; font-weight: 700; color: #111; margin-bottom: 8px; }
.step p { font-size: 14px; line-height: 1.7; color: #777; margin: 0; }

/* 底部 CTA */
.cta-section { max-width: 1160px; margin: 0 auto 110px; padding: 0 24px; }
.cta-inner { position: relative; background: #111; color: #fff; border-radius: 24px; padding: 80px 40px; text-align: center; overflow: hidden; }
.cta-glow { position: absolute; width: 600px; height: 600px; top: -320px; left: 50%; transform: translateX(-50%); background: radial-gradient(circle, rgba(46,204,113,.22), transparent 65%); pointer-events: none; }
.cta-inner > *:not(.cta-glow) { position: relative; }
.cta-inner h2 { font-size: clamp(32px, 5vw, 52px); font-weight: 800; letter-spacing: -.02em; margin-bottom: 16px; }
.cta-inner p { font-size: 16px; color: #A5A5A0; margin-bottom: 32px; }
.cta-actions { display: flex; gap: 14px; justify-content: center; flex-wrap: wrap; }

/* 页脚 */
.site-footer { border-top: 1px solid #E6E5DF; background: #fff; }
.footer-inner { max-width: 1160px; margin: 0 auto; padding: 36px 24px; display: flex; align-items: center; gap: 24px; flex-wrap: wrap; }
.footer-brand { display: flex; align-items: center; gap: 12px; }
.footer-brand strong { font-size: 16px; color: #111; }
.footer-brand p { font-size: 12px; color: #999; margin: 0; }
.footer-copy { flex: 1; font-size: 12px; color: #999; text-align: center; }
.footer-admin { font-size: 12px; color: #888; text-decoration: none; }
.footer-admin:hover { color: #111; }

/* 响应式 */
@media (max-width: 900px) {
  .hero-inner { grid-template-columns: 1fr; gap: 48px; }
  .hero-copy { text-align: center; }
  .hero-actions, .hero-trust { justify-content: center; }
  .hero-visual { max-width: 520px; margin: 0 auto; }
  .feature-grid { grid-template-columns: repeat(2,1fr); }
  .why-inner { grid-template-columns: 1fr; gap: 40px; }
  .scene-content { grid-template-columns: 1fr; }
  .steps { grid-template-columns: repeat(2,1fr); row-gap: 36px; }
  .step-line { display: none; }
}
@media (max-width: 720px) {
  .nav-links { position: fixed; top: 68px; left: 0; right: 0; background: #fff; flex-direction: column; align-items: stretch; gap: 0; padding: 12px 24px 24px; border-bottom: 1px solid #E6E5DF; box-shadow: 0 20px 40px rgba(0,0,0,.08); transform: translateY(-120%); opacity: 0; transition: transform .3s ease, opacity .3s ease; }
  .nav-links.open { transform: translateY(0); opacity: 1; }
  .nav-links > a { padding: 14px 0; border-bottom: 1px solid #F0EFEA; }
  .nav-links > a::after { display: none; }
  .nav-actions { display: none; }
  .nav-actions-mobile { display: flex; gap: 10px; margin-top: 18px; }
  .nav-actions-mobile .btn { flex: 1; padding: 12px; }
  .menu-toggle { display: flex; }
}
@media (max-width: 560px) {
  .hero { padding: 104px 18px 72px; }
  .hero-title { font-size: 42px; }
  .hero-desc { font-size: 15px; }
  .desktop-break { display: none; }
  .btn-lg { padding: 13px 20px; font-size: 14px; }
  .hero-trust { gap: 12px 18px; font-size: 12px; }
  .stats-inner { grid-template-columns: repeat(2,1fr); gap: 24px 0; }
  .stat-item:nth-child(2) { border-right: none; }
  .stat-item strong { font-size: 28px; }
  .section { padding: 72px 18px; }
  .feature-grid { grid-template-columns: 1fr; }
  .scene-panel { padding: 24px 20px; }
  .scene-tabs button { font-size: 13px; padding: 11px 6px; }
  .scene-copy h3 { font-size: 23px; }
  .steps { grid-template-columns: 1fr; gap: 28px; }
  .cta-section { padding: 0 18px; margin-bottom: 72px; }
  .cta-inner { padding: 56px 22px; border-radius: 18px; }
  .footer-copy { text-align: left; flex-basis: 100%; }
  .float-badge { transform: scale(.8); }
  .badge-ai { top: -18px; left: -6px; }
  .badge-streak { right: -8px; }
}
@media (prefers-reduced-motion: reduce) {
  .reveal, .hero-copy, .hero-visual { opacity: 1 !important; transform: none !important; transition: none !important; }
  .float-badge, .scroll-hint .mouse i { animation: none; }
  .hero-glow { display: none; }
}
</style>
