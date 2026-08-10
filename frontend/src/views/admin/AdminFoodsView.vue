<template>
  <div class="page">
    <div class="admin-header">
      <h1 class="page-title">食材管理</h1>
      <div style="display:flex;gap:8px;align-items:center">
        <router-link to="/admin/recipes" class="btn btn-outline btn-sm">食谱管理</router-link>
        <button class="btn btn-primary btn-sm" @click="openForm({})">新增食材</button>
      </div>
    </div>

    <div class="filter-bar">
      <select v-model="filterCat" class="input" style="max-width:160px">
        <option value="">全部分类</option>
        <option v-for="c in categories" :key="c.category_id" :value="c.category_id">{{ c.category_name }}</option>
      </select>
      <input v-model="filterKeyword" class="input" placeholder="搜索食材..." style="max-width:200px">
      <button class="btn btn-sm btn-primary" @click="loadFoods">搜索</button>
    </div>

    <div v-if="!foods.length" class="empty">暂无食材</div>
    <table v-else class="table">
      <thead>
        <tr><th>名称</th><th>分类</th><th>热量/100g</th><th>蛋白质</th><th>脂肪</th><th>碳水</th><th>操作</th></tr>
      </thead>
      <TransitionGroup name="card" tag="tbody" appear>
        <tr v-for="(f, i) in foods" :key="f.food_id" :style="{ '--i': i }">
          <td>{{ f.food_name }}</td>
          <td>{{ f.category_name }}</td>
          <td>{{ f.nutrition?.calorie || 0 }}</td>
          <td>{{ f.nutrition?.protein || 0 }}g</td>
          <td>{{ f.nutrition?.fat || 0 }}g</td>
          <td>{{ f.nutrition?.carbohydrate || 0 }}g</td>
          <td>
            <button class="btn btn-sm btn-outline" @click="openForm(f)">编辑</button>
            <button class="btn btn-sm btn-danger" style="margin-left:4px" @click="delFood(f.food_id)">删除</button>
          </td>
        </tr>
      </TransitionGroup>
    </table>

    <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="modal-content">
        <h2 class="modal-title">{{ editingFood?.food_id ? '编辑食材' : '新增食材' }}</h2>
        <div class="form-group">
          <label>食材名称</label>
          <input v-model="form.food_name" class="input" required>
        </div>
        <div class="form-group">
          <label>分类</label>
          <select v-model.number="form.category_id" class="input">
            <option v-for="c in categories" :key="c.category_id" :value="c.category_id">{{ c.category_name }}</option>
          </select>
        </div>
        <div class="form-group">
          <label>单位</label>
          <input v-model="form.unit" class="input" placeholder="100g">
        </div>
        <h4>营养数据（每100g）</h4>
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api/index.js'

const foods = ref([])
const categories = ref([])
const filterCat = ref('')
const filterKeyword = ref('')
const showForm = ref(false)
const editingFood = ref(null)
const saving = ref(false)

const form = ref({
  food_name: '', category_id: 1, unit: '100g',
  nutrition: { calorie: 0, protein: 0, fat: 0, carbohydrate: 0 },
})

const adminUser = JSON.parse(sessionStorage.getItem('admin') || '{}')
if (!adminUser.admin_id) window.location.href = '/admin/login'

async function loadFoods() {
  const params = {}
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
}

function openForm(f) {
  editingFood.value = f
  form.value = {
    food_name: f.food_name || '',
    category_id: f.category_id || 1,
    unit: f.unit || '100g',
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
    if (editingFood.value?.food_id) {
      await api.updateFood(editingFood.value.food_id, form.value)
    } else {
      await api.createFood(form.value)
    }
    showForm.value = false
    loadFoods()
  } catch (e) {}
  finally { saving.value = false }
}

async function delFood(id) {
  if (!confirm('确定删除？')) return
  await api.deleteFood(id)
  loadFoods()
}

onMounted(loadFoods)
</script>

<style scoped>
.admin-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.filter-bar { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
.table {
  width: 100%; border-collapse: collapse; background: #fff; border-radius: var(--radius);
  overflow: hidden; box-shadow: var(--shadow);
}
.table th, .table td { padding: 10px 14px; text-align: left; font-size: 14px; }
.table th { background: var(--bg); font-weight: 600; }
.table td { border-top: 1px solid var(--border); }

/* 行入场（级联，逐条由上到下淡入，与用户页面一致） */
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
.card-move { transition: transform 0.35s ease; }
.table tbody { position: relative; }
</style>
