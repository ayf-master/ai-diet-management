<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title" style="margin-bottom:0">数据统计</h1>
      <p style="font-size:14px;color:var(--text-light);margin-top:4px">追踪你的饮食和体重变化趋势</p>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon" style="background:var(--primary-glow);color:var(--primary)">&#9776;</div>
        <div>
          <p class="stat-label">今日摄入</p>
          <p class="stat-value">{{ daily?.total_cal || 0 }} <small>kcal</small></p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:rgba(52,152,219,0.1);color:var(--info)">&#9733;</div>
        <div>
          <p class="stat-label">周总热量</p>
          <p class="stat-value">{{ weekly?.total_cal || 0 }} <small>kcal</small></p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:rgba(243,156,18,0.1);color:var(--accent)">&#9736;</div>
        <div>
          <p class="stat-label">最新体重</p>
          <p class="stat-value">{{ latestWeight?.weight || '-' }} <small>kg</small></p>
        </div>
      </div>
    </div>

    <div class="chart-card card">
      <h3>周热量趋势</h3>
      <div class="chart-wrap"><canvas ref="weeklyChart"></canvas></div>
    </div>

    <div class="weight-form card">
      <h3>记录新体重</h3>
      <div class="weight-inputs">
        <input v-model.number="weightForm.weight" class="input" type="number" step="0.1" placeholder="体重 (kg)">
        <button class="btn btn-primary btn-sm" @click="recordWeight">记录</button>
      </div>
      <p v-if="weightMsg" class="success-msg">{{ weightMsg }}</p>
    </div>

    <div class="chart-card card">
      <h3>体重趋势</h3>
      <div class="chart-wrap"><canvas ref="weightChart"></canvas></div>
    </div>

    <div class="chart-card card">
      <div class="card-head">
        <h3>历史体重记录</h3>
        <div class="period-filter">
          <select v-model.number="selYear" class="input input-sm">
            <option v-for="y in yearOptions" :key="y" :value="y">{{ y }} 年</option>
          </select>
          <select v-model.number="selMonth" class="input input-sm">
            <option v-for="m in monthOptions" :key="m" :value="m">{{ m }} 月</option>
          </select>
        </div>
      </div>
      <div v-if="weightRows.length" class="weight-table-wrap">
        <table class="weight-table">
          <thead>
            <tr>
              <th>日期</th>
              <th>体重 (kg)</th>
              <th>较上次</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in weightRows" :key="r.measure_date">
              <td>{{ r.measure_date }}</td>
              <td>{{ r.weight }}</td>
              <td>
                <span v-if="r.delta === null" class="delta-flat">—</span>
                <span v-else-if="r.delta > 0" class="delta-up">▲ {{ r.delta }}</span>
                <span v-else-if="r.delta < 0" class="delta-down">▼ {{ Math.abs(r.delta) }}</span>
                <span v-else class="delta-flat">持平</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else class="empty-tip">暂无体重记录，先在上方的「记录新体重」添加一条吧～</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import api from '../api/index.js'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

const user = JSON.parse(sessionStorage.getItem('user') || '{}')

const daily = ref(null)
const weekly = ref(null)
const latestWeight = ref(null)
const weeklyChart = ref(null)
const weightChart = ref(null)
const weeklyChartInst = ref(null)
const weightChartInst = ref(null)
const weightForm = ref({ weight: '' })
const weightMsg = ref('')
const weightHistory = ref([])
const tableAll = ref([])

// 历史体重表格的月份 / 年份筛选
const now = new Date()
const selYear = ref(now.getFullYear())
const selMonth = ref(now.getMonth() + 1)
const yearOptions = ref(Array.from({ length: 5 }, (_, i) => now.getFullYear() - i))
const monthOptions = ref(Array.from({ length: 12 }, (_, i) => i + 1))

async function loadStats() {
  const today = new Date().toISOString().split('T')[0]
  const [d, w, lw] = await Promise.all([
    api.getDailyStats(user.user_id, today),
    api.getWeeklyStats(user.user_id),
    api.getLatestWeight(user.user_id),
  ])
  daily.value = d.data
  weekly.value = w.data
  latestWeight.value = lw.data
  await Promise.all([renderCharts(), loadTableHistory()])
}

async function loadTableHistory() {
  // 一次性拉取全部体重记录（足够覆盖多年），月份/年份筛选在前端完成，切选项即时生效、无需后端重启
  const res = await api.getWeightHistory(user.user_id, 1000)
  tableAll.value = res.data || []
}

async function recordWeight() {
  if (!weightForm.value.weight) return
  const res = await api.recordWeight({
    user_id: user.user_id,
    weight: weightForm.value.weight,
    measure_date: new Date().toISOString().split('T')[0],
  })
  if (res.code === 200) {
    weightMsg.value = '体重记录成功！'
    weightForm.value = { weight: '' }
    loadStats()
  }
}

function renderCharts() {
  if (weeklyChartInst.value) {
    weeklyChartInst.value.destroy()
    weeklyChartInst.value = null
  }
  if (weekly.value?.daily) {
    weeklyChartInst.value = new Chart(weeklyChart.value, {
      type: 'bar',
      data: {
        labels: weekly.value.daily.map(d => d.date.slice(5)),
        datasets: [{
          label: '摄入 (kcal)',
          data: weekly.value.daily.map(d => d.cal),
          backgroundColor: 'rgba(46, 204, 113, 0.5)',
          borderColor: '#2ECC71',
          borderWidth: 1,
          borderRadius: 4,
        }],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.04)' }, title: { display: true, text: 'kcal', color: '#999', font: { size: 12 } } } },
      },
    })
  }
  loadWeightChart()
}

async function loadWeightChart() {
  const res = await api.getWeightHistory(user.user_id, 30)
  const records = res.data || []
  weightHistory.value = records
  if (weightChartInst.value) {
    weightChartInst.value.destroy()
    weightChartInst.value = null
  }
  if (records.length > 1) {
    await nextTick()
    weightChartInst.value = new Chart(weightChart.value, {
      type: 'line',
      data: {
        labels: records.map(r => r.measure_date.slice(5)).reverse(),
        datasets: [{
          label: '体重 (kg)',
          data: records.map(r => r.weight).reverse(),
          borderColor: '#3498DB',
          backgroundColor: 'rgba(52,152,219,0.1)',
          fill: true, tension: 0.4,
          pointBackgroundColor: '#3498DB',
        }],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { grid: { color: 'rgba(0,0,0,0.04)' }, title: { display: true, text: 'kg', color: '#999', font: { size: 12 } } } },
      },
    })
  }
}

// 表格数据：按选中的年/月在前端筛选，再按日期倒序（最新在上），并计算相较上一条的变化量
const weightRows = computed(() => {
  const filtered = tableAll.value.filter(r => {
    const y = parseInt(r.measure_date.slice(0, 4), 10)
    const m = parseInt(r.measure_date.slice(5, 7), 10)
    return y === selYear.value && m === selMonth.value
  })
  // filtered 已按日期倒序；升序副本用于算差值
  const asc = [...filtered].slice().reverse()
  const deltaMap = {}
  for (let i = 0; i < asc.length; i++) {
    deltaMap[asc[i].measure_date] = i === 0 ? null : +(asc[i].weight - asc[i - 1].weight).toFixed(1)
  }
  return filtered.map(r => ({
    ...r,
    delta: deltaMap[r.measure_date],
  }))
})

onMounted(loadStats)
</script>

<style scoped>
.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
@media (max-width: 640px) { .stats-grid { grid-template-columns: 1fr; } }

.stat-card {
  background: #fff; border-radius: var(--radius); padding: 16px 18px;
  display: flex; align-items: center; gap: 14px;
  border: 1px solid var(--border-light); box-shadow: var(--shadow);
}
.stat-icon { width: 42px; height: 42px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 18px; }
.stat-label { font-size: 12px; color: var(--text-light); margin-bottom: 2px; }
.stat-value { font-size: 24px; font-weight: 700; color: var(--text); }
.stat-value small { font-size: 13px; color: var(--text-light); font-weight: 400; }

.chart-card { margin-top: 16px; }
.chart-card h3 { margin: 0; }
.card-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.period-filter { display: flex; gap: 8px; }
.input-sm { height: 34px; padding: 4px 8px; font-size: 13px; }
.chart-wrap { height: 240px; margin-top: 12px; position: relative; }

.weight-table-wrap { margin-top: 12px; max-height: 320px; overflow-y: auto; }
.weight-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.weight-table th, .weight-table td { padding: 10px 12px; text-align: left; border-bottom: 1px solid var(--border-light); }
.weight-table thead th { position: sticky; top: 0; background: #fafafa; color: var(--text-light); font-weight: 600; font-size: 13px; }
.weight-table tbody tr:hover { background: rgba(0,0,0,0.02); }
.delta-up { color: #E74C3C; font-weight: 600; }
.delta-down { color: #2ECC71; font-weight: 600; }
.delta-flat { color: var(--text-light); }
.empty-tip { margin-top: 12px; color: var(--text-light); font-size: 14px; }

.weight-form { margin-top: 16px; }
.weight-inputs { display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
.weight-inputs .input { max-width: 160px; }
.success-msg { font-size: 13px; color: var(--primary); margin-top: 6px; }
</style>
