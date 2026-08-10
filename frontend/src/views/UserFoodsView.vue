<template>
  <div class="page">
    <div class="page-header" style="display:flex;justify-content:space-between;align-items:center">
      <div>
        <h1 class="page-title" style="margin-bottom:0">食材</h1>
        <p style="font-size:14px;color:var(--text-light);margin-top:4px">管理系统食材和你自定义的食材</p>
      </div>
      <button class="btn btn-primary btn-sm" @click="openForm({})">新增食材</button>
    </div>

    <div class="filter-bar">
      <select v-model="filterCat" class="input" style="max-width:140px">
        <option value="">全部分类</option>
        <option v-for="c in categories" :key="c.category_id" :value="c.category_id">{{ c.category_name }}</option>
      </select>
      <input v-model="filterKeyword" class="input" placeholder="搜索..." style="max-width:160px">
      <button class="btn btn-sm btn-primary" @click="loadFoods">搜索</button>
    </div>

    <div v-if="!foods.length && !initialLoading" class="empty">暂无食材</div>
    <table v-else class="table">
      <thead>
        <tr><th>名称</th><th>分类</th><th>热量/100g</th><th>蛋白质</th><th>脂肪</th><th>健康提示</th><th>来源</th><th>操作</th></tr>
      </thead>
      <TransitionGroup name="card" tag="tbody">
        <tr v-for="(f, i) in foods" :key="f.food_id" class="food-row" :style="{ '--i': i }" :class="{ 'is-system': !f.user_id }" @click="showDetail(f)">
          <td>{{ f.food_name }}</td>
          <td>{{ f.category_name }}</td>
          <td>{{ f.nutrition?.calorie || 0 }}kcal</td>
          <td>{{ f.nutrition?.protein || 0 }}g</td>
          <td>{{ f.nutrition?.fat || 0 }}g</td>
          <td>
            <span v-if="f.health_warning && f.health_warning.level !== 'ok'"
                  class="hw-badge" :class="'hw-' + f.health_warning.level"
                  :title="f.health_warning.reasons.join('\n')">⚠ {{ hwLabel(f.health_warning.level) }}</span>
            <span v-else class="hw-ok">—</span>
          </td>
          <td><span class="src-tag" :class="f.user_id ? 'src-mine' : 'src-system'">{{ f.user_id ? '我的' : '系统' }}</span></td>
          <td class="row-actions" @click.stop>
            <button class="btn btn-sm btn-outline" @click.stop="openForm(f)">编辑</button>
            <button class="btn btn-sm btn-danger" style="margin-left:4px" @click.stop="delFood(f)">删除</button>
          </td>
        </tr>
      </TransitionGroup>
    </table>

    <!-- 新增/编辑弹窗 -->
    <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="modal-content">
        <h2 class="modal-title">{{ editingFood?.food_id ? '编辑食材' : '新增食材' }}</h2>
        <div class="form-group">
          <label>名称</label>
          <input v-model="form.food_name" class="input" required>
        </div>
        <div class="form-group">
          <label>分类</label>
          <select v-model.number="form.category_id" class="input">
            <option v-for="c in categories" :key="c.category_id" :value="c.category_id">{{ c.category_name }}</option>
          </select>
        </div>
        <h4 style="margin:12px 0 8px">营养（每100g）</h4>
        <div class="grid-2">
          <div class="form-group"><label>热量(kcal)</label><input v-model.number="form.nutrition.calorie" class="input" type="number"></div>
          <div class="form-group"><label>蛋白质(g)</label><input v-model.number="form.nutrition.protein" class="input" type="number" step="0.1"></div>
          <div class="form-group"><label>脂肪(g)</label><input v-model.number="form.nutrition.fat" class="input" type="number" step="0.1"></div>
          <div class="form-group"><label>碳水(g)</label><input v-model.number="form.nutrition.carbohydrate" class="input" type="number" step="0.1"></div>
        </div>
        <div style="display:flex;gap:8px;margin-top:12px">
          <button class="btn btn-primary" @click="saveFood">{{ saving ? '保存中...' : '保存' }}</button>
          <button class="btn btn-outline" @click="showForm = false">取消</button>
        </div>
      </div>
    </div>

    <!-- 详情弹窗 -->
    <div v-if="detail" class="modal-overlay" @click.self="detail = null">
      <div class="modal-content detail-modal">
        <h2 class="modal-title">{{ detail.food_name }}</h2>
        <div class="detail-info">
          <span class="badge tag-healthy">{{ detail.category_name || '未分类' }}</span>
          <span class="src-tag" :class="detail.user_id ? 'src-mine' : 'src-system'">{{ detail.user_id ? '我的' : '系统' }}</span>
        </div>
        <div class="detail-stats">
          <div class="detail-stat"><strong>{{ detail.nutrition?.calorie || 0 }}</strong><small>kcal / 100g</small></div>
          <div class="detail-stat"><strong>{{ detail.nutrition?.protein || 0 }}g</strong><small>蛋白质</small></div>
          <div class="detail-stat"><strong>{{ detail.nutrition?.fat || 0 }}g</strong><small>脂肪</small></div>
          <div class="detail-stat"><strong>{{ detail.nutrition?.carbohydrate || 0 }}g</strong><small>碳水</small></div>
        </div>
        <div v-if="detail.health_warning && detail.health_warning.level !== 'ok'"
             class="detail-warn" :class="'dw-' + detail.health_warning.level">
          <strong>⚠ 健康提示（{{ hwLabel(detail.health_warning.level) }}）</strong>
          <ul><li v-for="(rs, i) in detail.health_warning.reasons" :key="i">{{ rs }}</li></ul>
        </div>
        <div style="display:flex;gap:8px;margin-top:16px">
          <button class="btn btn-primary" @click="openForm(detail); detail = null">编辑</button>
          <button class="btn btn-outline" @click="detail = null">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api/index.js'

const user = JSON.parse(sessionStorage.getItem('user') || '{}')

const foods = ref([])
const categories = ref([])
const filterCat = ref('')
const filterKeyword = ref('')
const initialLoading = ref(true)
const showForm = ref(false)
const editingFood = ref(null)
const saving = ref(false)
const detail = ref(null)

const form = ref({
  food_name: '', category_id: 1,
  nutrition: { calorie: 0, protein: 0, fat: 0, carbohydrate: 0 },
})

async function loadFoods() {
  const params = { user_id: user.user_id }
  if (filterCat.value) params.category_id = filterCat.value
  if (filterKeyword.value) params.keyword = filterKeyword.value
  const [f, c] = await Promise.all([
    api.getFoods(params),
    api.getFoodCategories(),
  ])
  foods.value = (f.data || []).map(fd => ({
    ...fd,
    category_name: (c.data || []).find(cat => cat.category_id === fd.category_id)?.category_name || '',
  }))
  categories.value = c.data || []
  initialLoading.value = false
}

function showDetail(f) {
  detail.value = f
}

function hwLabel(level) {
  return level === 'danger' ? '有害' : level === 'warn' ? '注意' : '安全'
}

function openForm(f) {
  editingFood.value = f
  form.value = {
    food_name: f.food_name || '',
    category_id: f.category_id || 1,
    nutrition: {
      calorie: f.nutrition?.calorie || 0,
      protein: f.nutrition?.protein || 0,
      fat: f.nutrition?.fat || 0,
      carbohydrate: f.nutrition?.carbohydrate || 0,
    },
  }
  showForm.value = true
}

async function saveFood() {
  saving.value = true
  try {
    const data = { ...form.value, user_id: user.user_id }
    const res = editingFood.value?.food_id
      ? await api.updateFood(editingFood.value.food_id, data)
      : await api.createFood(data)
    if (res.code !== 200) {
      alert(res.msg || '保存失败')
      return
    }
    showForm.value = false
    loadFoods()
  } catch (e) {
    alert(e?.message || '网络错误')
  }
  finally { saving.value = false }
}

async function delFood(f) {
  if (!confirm('确定删除？')) return
  await api.deleteFood(f.food_id, user.user_id)
  loadFoods()
}

onMounted(loadFoods)
</script>

<style scoped>
.filter-bar { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
.table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; }
.table th, .table td { padding: 10px 14px; text-align: left; font-size: 14px; }
.table th { background: #F7F6F3; font-weight: 600; }
.table td { border-top: 1px solid #EAEAEA; }
.food-row { cursor: pointer; transition: background 0.15s; }
.food-row:hover { background: #F7F9FB; }
.is-system td:first-child { font-weight: 400; }
.row-actions { white-space: nowrap; }
.src-tag { font-size: 11px; padding: 2px 8px; border-radius: 4px; }
.src-system { background: #EDF3EC; color: #346538; }
.src-mine { background: #E1F3FE; color: #1F6C9F; }
.badge { font-size: 10px; padding: 2px 8px; border-radius: 999px; text-transform: uppercase; letter-spacing: 0.03em; }
.tag-healthy { background: #E1F3FE; color: #1F6C9F; }

/* 详情弹窗 */
.detail-modal .detail-info { display: flex; gap: 8px; align-items: center; margin: 10px 0; }
.detail-modal .detail-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin: 12px 0; }
.detail-modal .detail-stat { text-align: center; padding: 8px 6px; background: #F7F6F3; border-radius: 8px; }
.detail-modal .detail-stat strong { display: block; font-size: 15px; }
.detail-modal .detail-stat small { font-size: 10px; color: var(--text-light); }
/* ── 行入场（级联，逐条由上到下淡入） ── */
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
.table tbody { position: relative; }

.form-group label { text-transform: none; letter-spacing: normal; }

/* ── 健康警告标 ── */
.hw-badge { font-size: 11px; padding: 2px 8px; border-radius: 4px; cursor: help; white-space: nowrap; }
.hw-warn { background: #FDF1E3; color: #d9730d; }
.hw-danger { background: #FDEBEC; color: #9F2F2D; }
.hw-ok { color: #ccc; font-size: 13px; }
.detail-warn { margin-top: 12px; padding: 10px 12px; border-radius: 8px; font-size: 13px; line-height: 1.6; }
.dw-warn { background: #FDF1E3; color: #9a5b15; }
.dw-danger { background: #FDEBEC; color: #9F2F2D; }
.detail-warn ul { margin: 6px 0 0; padding-left: 18px; }
</style>
