<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title" style="margin-bottom:0">饮食打卡</h1>
      <p style="font-size:14px;color:var(--text-light);margin-top:4px">记录你每日的饮食摄入</p>
    </div>

    <div class="grid-2" style="align-items:start">
      <!-- 打卡表单 -->
      <div class="meal-form card">
        <h3 style="display:flex;align-items:center;gap:8px">
          <span style="font-size:18px">&#9776;</span> 记录一餐
        </h3>
        <div class="form-row">
          <div class="form-group">
            <label>日期</label>
            <input v-model="meal.date" class="input" type="date">
          </div>
          <div class="form-group">
            <label>餐次</label>
            <select v-model="meal.type_id" class="input">
              <option v-for="t in mealTypes" :key="t.type_id" :value="t.type_id">{{ t.type_name }}</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label>添加菜品</label>
          <select v-model="selectedRecipe" class="input" @change="onRecipeChange">
            <option value="" disabled>选择食谱</option>
            <option v-for="r in allRecipes" :key="r.recipe_id" :value="r.recipe_id">
              {{ r.recipe_name }} ({{ r.total_calorie }}kcal / 份)
            </option>
          </select>

          <div v-if="selectedRecipeObj" class="qty-box">
            <div class="qty-toggle">
              <button type="button" :class="{ active: mode === 'servings' }" @click="mode = 'servings'">按份数</button>
              <button type="button" :class="{ active: mode === 'grams' }" @click="mode = 'grams'">按克数</button>
            </div>

            <div class="qty-row">
              <template v-if="mode === 'servings'">
                <button type="button" class="step-btn" @click="stepServings(-0.5)">-</button>
                <input v-model.number="servings" class="input qty-input" type="number" min="0.5" step="0.5">
                <button type="button" class="step-btn" @click="stepServings(0.5)">+</button>
                <span class="qty-unit">份</span>
              </template>
              <template v-else>
                <input v-model.number="grams" class="input qty-input" type="number" min="1" step="10">
                <span class="qty-unit">g</span>
              </template>
              <button class="btn btn-primary btn-sm" @click="addDetail" style="margin-left:auto">加入</button>
            </div>

            <p class="std-hint">
              标准 1 份 = {{ selectedRecipeObj.total_weight }}g · {{ selectedRecipeObj.total_calorie }}kcal
              <span class="preview">→ 本次 {{ previewCal }}kcal</span>
            </p>
          </div>
        </div>

        <div v-if="details.length" class="detail-list">
          <div v-for="(d, i) in details" :key="i" class="detail-item">
            <div class="detail-main">
              <span class="detail-name">{{ d.name }} · {{ d.label }}</span>
              <span class="detail-cal">{{ d.cal }}kcal</span>
              <button class="btn btn-sm btn-danger" @click="details.splice(i, 1)" style="padding:2px 8px;font-size:11px">x</button>
            </div>
          </div>
          <div class="detail-total">合计：<strong>{{ totalCal }}</strong> kcal</div>
        </div>

        <button class="btn btn-primary btn-block" style="margin-top:12px" @click="submitMeal" :disabled="!details.length">
          {{ submitting ? '提交中...' : '提交打卡' }}
        </button>
        <p v-if="msg" class="msg" :class="{ success: msgOk }">{{ msg }}</p>
      </div>

      <!-- 今日记录 -->
      <div>
        <h3 style="margin-bottom:12px">今日记录</h3>
        <div v-if="todayMeals.length === 0" class="empty" style="padding:40px 16px">
          <svg class="empty-icon" viewBox="0 0 64 64" width="48" height="48" fill="none">
            <rect x="8" y="16" width="48" height="36" rx="6" stroke="#A0B8A4" stroke-width="1.5"/>
            <line x1="18" y1="28" x2="46" y2="28" stroke="#DCE8DE" stroke-width="2" stroke-linecap="round"/>
            <line x1="18" y1="36" x2="38" y2="36" stroke="#DCE8DE" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <p>今日暂无记录</p>
        </div>
        <TransitionGroup name="card" tag="div" class="meal-list">
          <div v-for="(m, i) in todayMeals" :key="m.record_id" class="meal-record card"
               :style="{ '--i': i }">
            <div class="meal-header">
              <span class="badge" :class="'badge-' + zoneClass(m)">{{ m.meal_type }}</span>
              <span class="meal-cal">{{ m.total_cal }}kcal</span>
              <button class="btn btn-sm btn-danger" @click="deleteMeal(m.record_id)" style="padding:2px 10px;font-size:11px">删除</button>
            </div>
            <div v-for="d in m.details" :key="d.detail_id" class="detail-item">
              <span class="detail-name">{{ d.recipe_name }}</span>
              <span class="detail-cal">{{ d.single_cal }}kcal</span>
            </div>
          </div>
        </TransitionGroup>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api/index.js'

const user = JSON.parse(sessionStorage.getItem('user') || '{}')

const mealTypes = ref([])
const allRecipes = ref([])
const todayMeals = ref([])
const selectedRecipe = ref('')
const mode = ref('servings')      // 'servings' | 'grams'
const servings = ref(1)
const grams = ref(100)
const details = ref([])
const submitting = ref(false)
const msg = ref('')
const msgOk = ref(false)

const meal = ref({
  date: new Date().toISOString().split('T')[0],
  type_id: 2,
})

const totalCal = computed(() => details.value.reduce((s, d) => s + d.cal, 0))

const selectedRecipeObj = computed(() =>
  allRecipes.value.find(x => x.recipe_id === selectedRecipe.value) || null
)

// 计算某选择对应的重量（克）
function calcWeight(r) {
  const stdWeight = r.total_weight || 100
  if (mode.value === 'servings') {
    return Math.round((servings.value || 1) * stdWeight)
  }
  return grams.value || stdWeight
}

// 实时预览热量
const previewCal = computed(() => {
  const r = selectedRecipeObj.value
  if (!r) return 0
  const stdWeight = r.total_weight || 100
  const w = calcWeight(r)
  return Math.round((r.total_calorie || 0) * w / stdWeight)
})

function zoneClass(m) { return 'healthy' }

function onRecipeChange() {
  const r = selectedRecipeObj.value
  mode.value = 'servings'
  servings.value = 1
  grams.value = r ? (r.total_weight || 100) : 100
}

function stepServings(delta) {
  const next = Math.round(((servings.value || 0) + delta) * 10) / 10
  servings.value = next < 0.5 ? 0.5 : next
}

function addDetail() {
  const r = selectedRecipeObj.value
  if (!r) return
  const stdWeight = r.total_weight || 100
  const weight = calcWeight(r)
  const label = mode.value === 'servings'
    ? `${servings.value || 1} 份`
    : `${weight}g`
  const cal = Math.round((r.total_calorie || 0) * weight / stdWeight)
  details.value.push({
    recipe_id: r.recipe_id,
    name: r.recipe_name,
    weight,
    label,
    cal,
  })
  selectedRecipe.value = ''
  mode.value = 'servings'
  servings.value = 1
  grams.value = 100
}

async function submitMeal() {
  submitting.value = true; msg.value = ''
  try {
    const res = await api.createMeal({
      user_id: user.user_id,
      meal_type_id: meal.value.type_id,
      eat_date: meal.value.date,
      details: details.value.map(d => ({ recipe_id: d.recipe_id, eat_weight: d.weight })),
    })
    if (res.code === 200) {
      msg.value = '打卡成功！' + totalCal.value + 'kcal'; msgOk.value = true
      details.value = []
      loadToday()
    } else { msg.value = res.msg; msgOk.value = false }
  } catch (e) { msg.value = '网络错误'; msgOk.value = false }
  finally { submitting.value = false }
}

async function deleteMeal(id) {
  if (!confirm('确定删除？')) return
  await api.deleteMeal(id)
  loadToday()
}

async function loadToday() {
  const today = new Date().toISOString().split('T')[0]
  const res = await api.getMeals({ user_id: user.user_id, date: today })
  todayMeals.value = res.data || []
}

onMounted(async () => {
  const mt = await api.getMealTypes()
  mealTypes.value = mt.data || []
  const r = await api.getRecipes()
  allRecipes.value = r.data || []
  loadToday()
})
</script>

<style scoped>
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

.qty-box { margin-top: 10px; padding: 10px 12px; background: var(--bg); border-radius: var(--radius-sm); }
.qty-toggle { display: inline-flex; border: 1px solid var(--border-light); border-radius: 999px; overflow: hidden; margin-bottom: 10px; }
.qty-toggle button {
  border: none; background: transparent; padding: 5px 16px; font-size: 13px;
  cursor: pointer; color: var(--text-light); transition: background 0.15s, color 0.15s;
}
.qty-toggle button.active { background: var(--primary); color: #fff; }

.qty-row { display: flex; align-items: center; gap: 8px; }
.qty-input { max-width: 90px; text-align: center; }
.step-btn {
  width: 30px; height: 32px; border: 1px solid var(--border-light); background: #fff;
  border-radius: var(--radius-sm); cursor: pointer; font-size: 16px; line-height: 1; color: var(--text);
}
.step-btn:hover { border-color: var(--primary); color: var(--primary); }
.qty-unit { font-size: 14px; color: var(--text-light); }

.std-hint { margin-top: 8px; font-size: 12px; color: #999; }
.std-hint .preview { color: var(--primary); font-weight: 600; margin-left: 4px; }

.detail-list { margin-top: 10px; padding: 10px; background: var(--bg); border-radius: var(--radius-sm); }
.detail-item {
  padding: 6px 0;
  border-bottom: 1px solid var(--border-light); font-size: 14px;
}
.detail-item:last-child { border-bottom: none; }
.detail-main { display: flex; gap: 8px; align-items: center; }
.detail-name { flex: 1; }
.detail-cal { color: var(--primary); font-weight: 600; font-size: 13px; }

.detail-total { text-align: right; margin-top: 6px; font-size: 15px; }

.meal-record { margin-bottom: 10px; }
.meal-header { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.meal-cal { font-weight: 700; color: var(--text); font-size: 14px; margin-left: auto; }

.msg { margin-top: 8px; font-size: 13px; }
.msg.success { color: var(--primary); }

.meal-list { position: relative; }
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
  position: absolute;
  width: 100%;
}
@keyframes card-out {
  to { opacity: 0; transform: scale(0.85) translateY(-6px); }
}
.card-move {
  transition: transform 0.35s ease;
}
</style>
