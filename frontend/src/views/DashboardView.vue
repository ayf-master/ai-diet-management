<template>
  <div class="page">
    <div class="welcome-card">
      <div class="welcome-content">
        <div class="welcome-avatar">
          <img v-if="avatarUrl" :src="avatarUrl" class="avatar-img" alt="头像" />
          <span v-else>{{ (user.nickname || user.account)[0] }}</span>
        </div>
        <div>
          <h2>{{ user.nickname || user.account }}</h2>
          <p class="welcome-meta">
            BMI <strong>{{ user.bmi }}</strong> · 推荐 <strong>{{ user.recommend_cal }}</strong> kcal/日
          </p>
          <div class="welcome-zones">
            <span v-for="z in userZones" :key="z" class="badge" :class="'badge-' + z">{{ zoneLabel(z) }}</span>
          </div>
        </div>
      </div>
    </div>

    <p class="brand-line">一切为了你的健康</p>

    <!-- 模块1：今日热量进度 -->
    <div class="card dash-card" @click="go('/stats')">
      <div class="dash-head">
        <h3>今日热量</h3>
        <span class="dash-more">查看统计 ›</span>
      </div>
      <div class="cal-row">
        <div class="cal-ring">
          <svg viewBox="0 0 72 72" width="72" height="72">
            <circle cx="36" cy="36" r="28" fill="none" stroke="#EAEAEA" stroke-width="4"/>
            <circle cx="36" cy="36" r="28" fill="none" stroke="#111" stroke-width="4"
              :stroke-dasharray="176" :stroke-dashoffset="176 * (1 - ringPercent)"
              transform="rotate(-90 36 36)" stroke-linecap="round"/>
          </svg>
          <div class="cal-ring-text">{{ todayCal }}<small>/{{ recommend }}</small></div>
        </div>
        <div class="cal-info">
          <div class="cal-line">已摄入 <strong>{{ todayCal }}</strong> kcal</div>
          <div class="cal-line">今日还可摄入 <strong class="hl">{{ remaining }}</strong> kcal</div>
        </div>
      </div>
    </div>

    <!-- 模块2：今日待打卡餐段 -->
    <div class="card dash-card" @click="go('/meal')">
      <div class="dash-head">
        <h3>今日待打卡</h3>
        <span class="dash-more">去打卡 ›</span>
      </div>
      <div class="meal-seg">
        <div v-for="m in mealSegments" :key="m.name" class="seg" :class="{ done: m.done }">
          <span class="seg-name">{{ m.name }}</span>
          <span class="seg-cal">{{ m.done ? m.cal + 'kcal' : '未记录' }}</span>
        </div>
      </div>
    </div>

    <!-- 模块3：今日/本周数据速览 -->
    <div class="stat-row">
      <div class="card mini-stat" @click="go('/stats')">
        <p>今日摄入</p>
        <strong>{{ todayCal }} <small>kcal</small></strong>
      </div>
      <div class="card mini-stat" @click="go('/stats')">
        <p>本周总摄入</p>
        <strong>{{ weeklyTotal }} <small>kcal</small></strong>
      </div>
      <div class="card mini-stat" @click="go('/stats')">
        <p>最新体重</p>
        <strong>{{ latestWeight }} <small>kg</small></strong>
      </div>
    </div>

    <!-- 模块4：体重小趋势 -->
    <div class="card dash-card weight-card" @click="go('/stats')">
      <div class="dash-head">
        <h3>体重趋势（近 7 天）</h3>
        <span class="dash-more">查看统计 ›</span>
      </div>
      <div v-if="sparkRecords.length" class="spark-wrap" @mouseleave="hoverIdx = -1">
        <svg viewBox="0 0 300 120" class="spark">
          <defs>
            <linearGradient id="weightGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#3498DB" stop-opacity="0.25"/>
              <stop offset="100%" stop-color="#3498DB" stop-opacity="0"/>
            </linearGradient>
          </defs>
          <path :d="areaPath" fill="url(#weightGradient)" />
          <path :d="linePath" fill="none" stroke="#3498DB" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
          <circle
            v-for="(r, i) in sparkRecords" :key="i"
            :cx="r.x" :cy="r.y" r="4"
            fill="#fff" stroke="#3498DB" stroke-width="2.5"
            class="spark-dot" :class="{ active: hoverIdx === i }"
            @mouseenter="hoverIdx = i"
          />
          <text
            v-for="(r, i) in sparkRecords" :key="'d'+i"
            :x="r.x" y="108" text-anchor="middle" font-size="10" fill="#999"
          >{{ formatDate(r.measure_date) }}</text>
        </svg>
        <div v-if="hoverIdx >= 0" class="spark-tip" :style="tipStyle">
          <div class="tip-date">{{ sparkRecords[hoverIdx].measure_date }}</div>
          <div class="tip-weight">{{ sparkRecords[hoverIdx].weight }} kg</div>
        </div>
      </div>
      <p v-else class="empty-tip">暂无体重记录，去「统计」页记录一条吧～</p>
    </div>

    <!-- 模块5：目标进度 -->
    <div class="card dash-card" @click="go('/stats')">
      <div class="dash-head">
        <h3>目标进度</h3>
        <span class="dash-more">查看统计 ›</span>
      </div>
      <div class="goal-row">
        <span class="goal-val">{{ currentWeight }}kg</span>
        <div class="goal-bar"><div class="goal-fill" :style="{ width: progress + '%' }"></div></div>
        <span class="goal-val">{{ targetWeight }}kg</span>
      </div>
      <p class="goal-tip">还需减 <strong>{{ gap }}</strong> kg（已完成 {{ progress }}%）</p>
    </div>

    <!-- 模块6：智能建议 -->
    <div class="card dash-card suggest" @click="go('/meal')">
      <div class="dash-head"><h3>今日建议</h3></div>
      <p class="suggest-text">{{ suggestion }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/index.js'

const router = useRouter()
const user = JSON.parse(sessionStorage.getItem('user') || '{}')
if (!user.user_id) router.push('/login')

const go = (path) => router.push(path)

const avatarUrl = computed(() => {
  if (!user.avatar_url) return ''
  if (user.avatar_url.startsWith('http')) return user.avatar_url
  return `http://localhost:9876${user.avatar_url}`
})

const userZones = user.diet_goals || [user.diet_goal || 'healthy']

const recommend = user.recommend_cal || 0
const currentWeight = user.current_weight
const targetWeight = user.target_weight

const todayCal = ref(0)
const dailyMeals = ref([])
const weeklyTotal = ref(0)
const latestWeight = ref(currentWeight)
const weightHistory = ref([])
const mealTypes = ref([])
const hoverIdx = ref(-1)

const remaining = computed(() => Math.max(recommend - todayCal.value, 0))
const ringPercent = computed(() => Math.min(todayCal.value / (recommend || 1), 1))

const mealSegments = computed(() => {
  const recorded = {}
  dailyMeals.value.forEach(m => { recorded[m.meal_type] = m.cal })
  const types = mealTypes.value.length
    ? mealTypes.value
    : [{ type_name: '早餐' }, { type_name: '午餐' }, { type_name: '晚餐' }, { type_name: '加餐' }]
  return types.map(t => {
    const name = t.type_name
    const cal = recorded[name]
    return { name, done: cal != null, cal }
  })
})

// 目标进度：以最早一条体重记录为起点（无记录则用当前体重）
const startWeight = computed(() => {
  const arr = [...weightHistory.value].reverse()
  return arr.length ? arr[0].weight : currentWeight
})
const gap = computed(() => Math.max(+(currentWeight - targetWeight).toFixed(1), 0))
const progress = computed(() => {
  const start = startWeight.value
  if (start <= targetWeight) return 100
  const p = (start - currentWeight) / (start - targetWeight)
  return Math.max(0, Math.min(100, Math.round(p * 100)))
})

// 体重迷你图（近 7 天），带面积、数据点、日期标签、悬停提示
const sparkRecords = computed(() => {
  const arr = [...weightHistory.value].reverse().slice(-7)
  if (arr.length < 2) return []
  const vals = arr.map(r => r.weight)
  const min = Math.min(...vals), max = Math.max(...vals)
  const w = 300, h = 120, padTop = 24, padBottom = 28, padLR = 16
  const range = max - min || 1
  return arr.map((r, i) => {
    const x = padLR + (w - 2 * padLR) * (i / (arr.length - 1))
    const y = padTop + (h - padTop - padBottom) * (1 - (r.weight - min) / range)
    return { ...r, x, y }
  })
})

const linePath = computed(() => {
  if (!sparkRecords.value.length) return ''
  return sparkRecords.value.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ')
})

const areaPath = computed(() => {
  if (!sparkRecords.value.length) return ''
  const pts = sparkRecords.value
  const bottomY = 120 - 28
  const first = pts[0], last = pts[pts.length - 1]
  return `${linePath.value} L ${last.x.toFixed(1)} ${bottomY} L ${first.x.toFixed(1)} ${bottomY} Z`
})

const tipStyle = computed(() => {
  if (hoverIdx.value < 0) return {}
  const r = sparkRecords.value[hoverIdx.value]
  return { left: (r.x / 300 * 100) + '%', top: (r.y / 120 * 100) + '%' }
})

function formatDate(dateStr) {
  if (!dateStr) return ''
  const parts = dateStr.split('-')
  return parts.length >= 2 ? `${parts[1]}/${parts[2]}` : dateStr
}

const suggestion = computed(() => {
  const segs = mealSegments.value
  const done = segs.filter(m => m.done).length
  if (remaining.value <= 0) return '今日热量已达标，注意控制，晚餐建议轻食或少油。'
  if (done === 0) return `今天还没打卡哦，先去记录早餐吧，今日还可摄入 ${remaining.value}kcal。`
  if (done < segs.length) return `已记录 ${done} 餐，今日还可摄入 ${remaining.value}kcal，合理安排剩余餐段。`
  return `今日打卡完成！还可摄入 ${remaining.value}kcal，保持住～`
})

function zoneLabel(g) {
  if (!g) return '健康'
  if (g.includes('lose')) return '减脂'
  if (g.includes('gain')) return '增肌'
  return '健康饮食'
}

async function loadData() {
  const today = new Date().toISOString().split('T')[0]
  const [daily, weekly, lw, wh, mt] = await Promise.all([
    api.getDailyStats(user.user_id, today),
    api.getWeeklyStats(user.user_id),
    api.getLatestWeight(user.user_id),
    api.getWeightHistory(user.user_id, 7),
    api.getMealTypes(),
  ])
  todayCal.value = daily.data?.total_cal || 0
  dailyMeals.value = daily.data?.meals || []
  weeklyTotal.value = weekly.data?.total_cal || 0
  latestWeight.value = lw.data?.weight ?? currentWeight
  weightHistory.value = wh.data || []
  mealTypes.value = mt.data || []
}

onMounted(loadData)
</script>

<style scoped>
.welcome-card {
  border: 1px solid #EAEAEA; border-radius: 12px; padding: 20px 24px;
  background: #fff; display: flex; justify-content: space-between; align-items: center;
}
.welcome-content { display: flex; align-items: center; gap: 14px; }
.welcome-avatar {
  width: 42px; height: 42px; border-radius: 50%;
  background: #111; color: #fff; display: flex; align-items: center;
  justify-content: center; font-size: 16px; font-weight: 700;
  overflow: hidden; flex-shrink: 0;
}
.welcome-avatar .avatar-img { width: 100%; height: 100%; object-fit: cover; }
.welcome-meta { font-size: 13px; color: #787774; margin-top: 2px; }
.welcome-meta strong { color: #111; }
.welcome-zones { display: flex; gap: 4px; margin-top: 6px; }
.badge-healthy { background: #E1F3FE; color: #1F6C9F; }
.badge-lose_weight { background: #FDEBEC; color: #9F2F2D; }
.badge-gain_muscle { background: #EDF3EC; color: #346538; }
.badge { font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 500; }

.brand-line {
  font-family: 'Newsreader', 'Georgia', serif; font-size: 14px;
  color: #787774; font-style: italic; margin: 12px 0 16px;
}

.card { border: 1px solid #EAEAEA; border-radius: 12px; background: #fff; padding: 16px 18px; margin-bottom: 14px; }
.dash-card { cursor: pointer; transition: box-shadow 0.2s, transform 0.2s; }
.dash-card:hover { box-shadow: 0 4px 14px rgba(0,0,0,0.06); }
.dash-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.dash-head h3 { font-size: 15px; font-weight: 600; margin: 0; }
.dash-more { font-size: 12px; color: var(--primary, #1F6C9F); }

/* 今日热量 */
.cal-row { display: flex; align-items: center; gap: 18px; }
.cal-ring { position: relative; width: 72px; height: 72px; flex-shrink: 0; }
.cal-ring-text {
  position: absolute; inset: 0; display: flex; flex-direction: column;
  align-items: center; justify-content: center; font-size: 13px; font-weight: 700;
}
.cal-ring-text small { font-size: 9px; font-weight: 400; color: #787774; }
.cal-info { display: flex; flex-direction: column; gap: 6px; }
.cal-line { font-size: 14px; color: #555; }
.cal-line strong { font-size: 16px; color: #111; }
.cal-line .hl { color: #2ECC71; }

/* 待打卡餐段 */
.meal-seg { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
.seg {
  border: 1px solid #EAEAEA; border-radius: 8px; padding: 12px 10px; text-align: center;
  display: flex; flex-direction: column; gap: 4px;
}
.seg.done { background: #F4FBF6; border-color: #B7E4C7; }
.seg-name { font-size: 14px; font-weight: 600; }
.seg-cal { font-size: 12px; color: #999; }
.seg.done .seg-cal { color: #2E9E5B; }
@media (max-width: 640px) { .meal-seg { grid-template-columns: repeat(2, 1fr); } }

/* 数据速览 */
.stat-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.mini-stat { cursor: pointer; text-align: center; padding: 14px 10px; transition: box-shadow 0.2s; }
.mini-stat:hover { box-shadow: 0 4px 14px rgba(0,0,0,0.06); }
.mini-stat p { font-size: 12px; color: #999; margin: 0 0 6px; }
.mini-stat strong { font-size: 18px; color: #111; }
.mini-stat small { font-size: 11px; color: #999; font-weight: 400; }
@media (max-width: 640px) { .stat-row { grid-template-columns: 1fr; } }

/* 体重趋势 */
.weight-card { overflow: hidden; }
.spark-wrap { position: relative; height: 120px; }
.spark { width: 100%; height: 100%; display: block; }
.spark-dot { cursor: pointer; transition: r 0.2s, stroke-width 0.2s; }
.spark-dot.active { r: 6; stroke-width: 3; }
.spark-tip {
  position: absolute; transform: translate(-50%, -118%);
  background: #111; color: #fff; padding: 6px 10px; border-radius: 6px;
  font-size: 12px; pointer-events: none; white-space: nowrap; z-index: 10;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.spark-tip::after {
  content: ''; position: absolute; left: 50%; bottom: -4px;
  transform: translateX(-50%) rotate(45deg);
  width: 8px; height: 8px; background: #111;
}
.spark-tip .tip-date { font-size: 11px; color: #aaa; margin-bottom: 2px; }
.spark-tip .tip-weight { font-weight: 700; }

/* 目标进度 */
.goal-row { display: flex; align-items: center; gap: 12px; }
.goal-val { font-size: 14px; font-weight: 600; color: #111; flex-shrink: 0; }
.goal-bar { flex: 1; height: 10px; background: #EAEAEA; border-radius: 6px; overflow: hidden; }
.goal-fill { height: 100%; background: linear-gradient(90deg, #AED6F1, #3498DB); border-radius: 6px; transition: width 0.4s; }
.goal-tip { font-size: 13px; color: #787774; margin: 10px 0 0; }
.goal-tip strong { color: #111; }

/* 建议 */
.suggest { background: #FBFCFD; }
.suggest-text { font-size: 14px; color: #555; line-height: 1.7; margin: 0; }

.empty-tip { font-size: 13px; color: #999; margin: 4px 0 0; }
</style>
