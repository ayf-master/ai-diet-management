<template>
  <div class="page">
    <div class="page-header" style="display:flex;justify-content:space-between;align-items:center">
      <div>
        <h1 class="page-title" style="margin-bottom:0">AI 饮食方案</h1>
        <p style="font-size:14px;color:var(--text-light);margin-top:4px">智能生成个性化饮食计划</p>
      </div>
      <div style="display:flex;gap:8px">
        <button class="btn btn-primary btn-sm" @click="generatePlan" :disabled="genLoading">
          {{ genLoading ? '生成中...' : '生成方案' }}
        </button>
        <button class="btn btn-outline btn-sm" @click="generateRpt" :disabled="rptLoading">
          {{ rptLoading ? '生成中...' : '生成周报' }}
        </button>
      </div>
    </div>

    <p v-if="planMsg" class="plan-msg">{{ planMsg }}</p>

    <div class="grid-2" style="margin-top:24px">
      <div>
        <h3>历史方案</h3>
        <div v-if="!plans.length" class="empty" style="padding:30px 16px">
          <svg class="empty-icon" viewBox="0 0 64 64" width="40" height="40" fill="none">
            <rect x="8" y="16" width="48" height="36" rx="6" stroke="#A0B8A4" stroke-width="1.5"/>
            <line x1="18" y1="28" x2="46" y2="28" stroke="#DCE8DE" stroke-width="2"/>
            <line x1="18" y1="36" x2="38" y2="36" stroke="#DCE8DE" stroke-width="2"/>
          </svg>
          <p>暂无方案</p>
        </div>
        <TransitionGroup name="card" tag="div" class="history-list">
          <div v-for="(p, i) in plans" :key="p.plan_id" class="history-item" :style="{ '--i': i }">
            <div class="hi-body" @click="showPlan = p">
              <div class="hi-info">
                <span>{{ p.create_date }}</span>
                <span class="badge badge-gain">{{ p.total_cal || '-' }}kcal</span>
              </div>
              <span class="hi-view">点击查看</span>
            </div>
            <button class="hi-del" title="删除方案" @click.stop="removePlan(p)">✕</button>
          </div>
        </TransitionGroup>
      </div>
      <div>
        <h3>周报记录</h3>
        <div v-if="!reports.length" class="empty" style="padding:30px 16px">
          <svg class="empty-icon" viewBox="0 0 64 64" width="40" height="40" fill="none">
            <rect x="8" y="12" width="48" height="44" rx="6" stroke="#A0B8A4" stroke-width="1.5"/>
            <line x1="20" y1="24" x2="44" y2="24" stroke="#DCE8DE" stroke-width="2"/>
            <line x1="20" y1="32" x2="40" y2="32" stroke="#DCE8DE" stroke-width="2"/>
          </svg>
          <p>暂无周报</p>
        </div>
        <TransitionGroup name="card" tag="div" class="history-list">
          <div v-for="(r, i) in reports" :key="r.report_id" class="history-item" :style="{ '--i': i }">
            <div class="hi-body" @click="showReport = r">
              <div class="hi-info">
                <span>{{ r.start_date }} ~ {{ r.end_date }}</span>
                <span>{{ r.avg_daily_cal }}kcal/日</span>
              </div>
              <span class="hi-view">点击查看</span>
            </div>
            <button class="hi-del" title="删除周报" @click.stop="removeReport(r)">✕</button>
          </div>
        </TransitionGroup>
      </div>
    </div>

    <div v-if="showReport" class="modal-overlay" @click.self="showReport = null">
      <div class="modal-content">
        <h2 class="modal-title">AI 周报</h2>
        <div class="detail-stats">
          <div class="detail-stat"><strong>{{ showReport.start_date }}</strong><small>开始</small></div>
          <div class="detail-stat"><strong>{{ showReport.end_date }}</strong><small>结束</small></div>
          <div class="detail-stat"><strong>{{ showReport.avg_daily_cal }}</strong><small>日均kcal</small></div>
          <div class="detail-stat"><strong>{{ showReport.weight_diff }}</strong><small>体重变化kg</small></div>
        </div>
        <div class="report-comment">{{ showReport.ai_comment }}</div>
        <div v-if="showReport.suggest" class="report-suggest">
          <strong>建议：</strong>
          <p>{{ showReport.suggest }}</p>
        </div>
        <div class="modal-actions">
          <button class="btn btn-outline btn-sm" @click="removeReport(showReport, true)">删除</button>
          <button class="btn btn-primary btn-sm" @click="showReport = null">关闭</button>
        </div>
      </div>
    </div>

    <div v-if="showPlan" class="modal-overlay" @click.self="showPlan = null">
      <div class="modal-content">
        <h2 class="modal-title">
          <span style="font-size:18px">&#9733;</span>
          {{ showPlan.create_date }} 饮食方案
        </h2>
        <div class="detail-stats">
          <div class="detail-stat"><strong>{{ showPlan.total_cal || '-' }}</strong><small>kcal</small></div>
        </div>
        <p v-if="showPlan.forbid_food" class="plan-forbid">禁忌食材：{{ showPlan.forbid_food }}</p>
        <div v-if="planData.ok" class="plan-human">
          <div v-for="sec in planData.meals" :key="sec.key" class="plan-section">
            <div class="plan-section-title">{{ sec.label }}</div>
            <div v-for="(dish, di) in sec.dishes" :key="di" class="plan-dish">
              <div class="plan-dish-head">
                <span class="plan-dish-name">{{ dish.name }}</span>
              </div>
              <div class="plan-food-list">
                <div v-for="(item, idx) in dish.foods" :key="idx" class="plan-food">
                  <span>{{ item.name }}</span>
                  <span class="plan-food-weight">{{ item.weight }}g</span>
                </div>
              </div>
            </div>
          </div>
          <div v-if="planData.totalCal" class="plan-total">全天总计：{{ planData.totalCal }}kcal</div>
          <div v-if="planData.tips" class="plan-tips">{{ planData.tips }}</div>
        </div>
        <div v-else class="plan-content">
          <p class="plan-warn">⚠️ 该方案内容格式异常，无法美化展示，建议删除后重新生成一份。</p>
          <pre class="plan-raw">{{ showPlan.plan_content }}</pre>
        </div>
        <div class="modal-actions">
          <button class="btn btn-outline btn-sm" @click="removePlan(showPlan, true)">删除</button>
          <button class="btn btn-primary btn-sm" @click="showPlan = null">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api/index.js'

const user = JSON.parse(sessionStorage.getItem('user') || '{}')

const plans = ref([])
const reports = ref([])
const showPlan = ref(null)
const showReport = ref(null)
const genLoading = ref(false)
const rptLoading = ref(false)
const planMsg = ref('')

const planData = computed(() => parsePlan(showPlan.value?.plan_content || ''))

function parsePlan(text) {
  if (!text) return { ok: false }
  const cleaned = text
    .replace(/```json\s*/g, '')
    .replace(/```\s*/g, '')
    .trim()
  try {
    const data = JSON.parse(cleaned)
    if (!data || typeof data !== 'object') return { ok: false }

    const mealNames = {
      breakfast: '早餐',
      lunch: '午餐',
      dinner: '晚餐',
      snack: '加餐'
    }
    const meals = []
    for (const [key, label] of Object.entries(mealNames)) {
      const arr = data[key]
      if (Array.isArray(arr) && arr.length) {
        meals.push({ key, label, dishes: mealDishes(arr) })
      }
    }
    if (meals.length === 0) {
      for (const [key, value] of Object.entries(data)) {
        if (Array.isArray(value) && value.length) {
          meals.push({ key, label: mealNames[key] || key, dishes: mealDishes(value) })
        }
      }
    }
    return { ok: true, data, meals, totalCal: data.total_cal, tips: data.tips }
  } catch (e) {
    return { ok: false }
  }
}

function mealDishes(arr) {
  const hasNewFormat = arr.some((item) => Array.isArray(item.foods))
  if (hasNewFormat) {
    return arr.map(toDish)
  }
  // 老格式：把整餐食材合并成一个「推荐搭配」菜品
  return [{
    name: '推荐搭配',
    recipe: '',
    foods: arr.map((item) => ({
      name: item.food || item.name || JSON.stringify(item),
      weight: item.weight_g || item.weight || 0
    }))
  }]
}

function toDish(item) {
  // 新格式：{dish, foods:[{food, weight_g}]}
  if (Array.isArray(item.foods)) {
    return {
      name: item.dish || item.name || '菜品',
      foods: item.foods.map((f) => ({
        name: f.food || f.name || JSON.stringify(f),
        weight: f.weight_g || f.weight || 0
      }))
    }
  }
  // 兜底单食材
  if (item.food || item.name) {
    return {
      name: item.dish || item.name || '推荐搭配',
      foods: [{
        name: item.food || item.name,
        weight: item.weight_g || item.weight || 0
      }]
    }
  }
  return { name: '菜品', foods: [] }
}

async function loadHistory() {
  const [p, r] = await Promise.all([
    api.getPlans(user.user_id),
    api.getReports(user.user_id),
  ])
  plans.value = p.data || []
  reports.value = r.data || []
}

async function generatePlan() {
  genLoading.value = true; planMsg.value = ''
  try {
    const res = await api.generatePlan(user.user_id)
    if (res.code === 200) {
      planMsg.value = '方案生成成功！'
      await loadHistory()
      showPlan.value = plans.value[0] || null
    } else { planMsg.value = res.msg }
  } catch (e) { planMsg.value = '生成失败' }
  finally { genLoading.value = false }
}

async function generateRpt() {
  rptLoading.value = true; planMsg.value = ''
  try {
    const res = await api.generateReport(user.user_id)
    if (res.code === 200) {
      planMsg.value = '周报生成成功！'
      loadHistory()
    } else { planMsg.value = res.msg }
  } catch (e) { planMsg.value = '生成失败' }
  finally { rptLoading.value = false }
}

async function removePlan(p, fromModal = false) {
  if (!fromModal && !confirm('确定删除该方案？')) return
  const res = await api.deletePlan(p.plan_id)
  if (res.code === 200) {
    planMsg.value = '方案已删除'
    if (showPlan.value && showPlan.value.plan_id === p.plan_id) showPlan.value = null
    loadHistory()
  } else { planMsg.value = res.msg }
}

async function removeReport(r, fromModal = false) {
  if (!fromModal && !confirm('确定删除该周报？')) return
  const res = await api.deleteReport(r.report_id)
  if (res.code === 200) {
    planMsg.value = '周报已删除'
    if (showReport.value && showReport.value.report_id === r.report_id) showReport.value = null
    loadHistory()
  } else { planMsg.value = res.msg }
}

onMounted(loadHistory)
</script>

<style scoped>
.plan-msg { font-size: 14px; margin-bottom: 12px; color: var(--primary); }
.plan-card { margin-top: 12px; }
.plan-forbid { color: var(--danger); font-size: 13px; margin: 8px 0; }
.plan-content {
  font-size: 14px; line-height: 1.8; margin-top: 8px;
  padding: 14px; background: var(--bg); border-radius: var(--radius-sm);
}
.plan-warn { color: var(--danger); font-size: 13px; margin: 0 0 10px; }
.plan-raw {
  margin: 0; padding: 12px; background: #fff; border-radius: var(--radius-sm);
  font-size: 12px; line-height: 1.6; white-space: pre-wrap; word-break: break-all;
  max-height: 320px; overflow: auto; color: var(--text-light);
  border: 1px solid var(--border-light);
}
.history-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 14px; margin-bottom: 6px;
  background: #fff; border-radius: var(--radius-sm);
  border: 1px solid var(--border-light); font-size: 14px;
  transition: all 0.2s;
}
.hi-body {
  display: flex; justify-content: space-between; align-items: center;
  flex: 1; gap: 8px; cursor: pointer;
}
.hi-info { display: flex; align-items: center; gap: 8px; min-width: 0; }
.hi-view {
  flex-shrink: 0; font-size: 12px; color: var(--text-light);
  display: inline-flex; align-items: center; gap: 2px;
}
.history-item:hover .hi-view { color: var(--primary); }
.hi-del {
  flex-shrink: 0; width: 24px; height: 24px; margin-left: 10px;
  border: none; border-radius: 50%; background: transparent;
  color: var(--text-light); font-size: 13px; cursor: pointer;
  transition: all 0.2s;
}
.hi-del:hover { background: var(--danger); color: #fff; }
.history-item:hover {
  border-color: var(--primary-light);
  box-shadow: 0 0 0 2px var(--primary-glow);
}
/* ── 列表项逐条淡入（级联，由上到下） ── */
.card-enter-active {
  animation: card-in 0.4s ease-out both;
  animation-delay: calc(var(--i, 0) * 50ms);
}
@keyframes card-in {
  from { opacity: 0; transform: translateY(20px) scale(0.97); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}
.card-leave-active {
  animation: card-out 0.25s ease-in both;
}
@keyframes card-out {
  to { opacity: 0; transform: scale(0.85) translateY(-6px); }
}
.card-move {
  transition: transform 0.35s ease;
}
.history-list { position: relative; }
.detail-stats { display: flex; gap: 8px; margin: 12px 0; }
.detail-stat { text-align: center; padding: 8px; background: var(--bg); border-radius: var(--radius-sm); flex: 1; }
.detail-stat strong { display: block; font-size: 13px; }
.detail-stat small { font-size: 10px; color: var(--text-light); }
.report-comment {
  padding: 14px; background: var(--bg); border-radius: var(--radius-sm);
  font-size: 14px; line-height: 1.7;
}
.report-suggest { margin-top: 10px; font-size: 14px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; }
.plan-human { margin-top: 8px; }
.plan-section { background: var(--bg); border-radius: var(--radius-sm); padding: 12px 14px; margin-bottom: 10px; }
.plan-section-title { font-weight: 600; font-size: 15px; color: var(--text); margin-bottom: 8px; }
.plan-food-list { display: flex; flex-direction: column; gap: 6px; }
.plan-dish { padding: 8px 0; border-bottom: 1px dashed var(--border-light); }
.plan-dish:last-child { border-bottom: none; }
.plan-dish-head { display: flex; align-items: center; gap: 6px; margin-bottom: 6px; }
.plan-dish-name { font-weight: 600; font-size: 14px; color: var(--text); }
.plan-food { display: flex; justify-content: space-between; align-items: center; font-size: 14px; color: var(--text); }
.plan-food-weight { color: var(--text-light); font-size: 13px; }
.plan-total { font-size: 15px; font-weight: 600; text-align: right; margin: 10px 0; }
.plan-tips { font-size: 13px; color: var(--text-light); line-height: 1.7; padding: 12px; background: #fff; border-radius: var(--radius-sm); border: 1px solid var(--border-light); }
</style>
