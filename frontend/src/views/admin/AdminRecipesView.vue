<template>
  <div class="page">
    <div class="admin-header">
      <h1 class="page-title">食谱管理</h1>
      <div style="display:flex;gap:8px;align-items:center">
        <router-link to="/admin/foods" class="btn btn-outline btn-sm">食材管理</router-link>
        <button class="btn btn-primary btn-sm" @click="openForm({})">新增食谱</button>
      </div>
    </div>

    <div v-if="!recipes.length" class="empty">暂无食谱</div>
    <table v-else class="table">
      <thead>
        <tr><th>名称</th><th>餐次</th><th>专区</th><th>烹饪方式</th><th>热量</th><th>操作</th></tr>
      </thead>
      <tbody>
        <tr v-for="r in recipes" :key="r.recipe_id">
          <td>{{ r.recipe_name }}</td>
          <td>{{ r.type }}</td>
          <td><span class="badge" :class="'badge-' + r.suitable_goals">{{ r.suitable_goals }}</span></td>
          <td>{{ r.cook_method }}</td>
          <td>{{ r.total_calorie }}kcal<span v-if="r.added_calorie" class="cook-extra">含烹饪+{{ r.added_calorie }}</span></td>
          <td>
            <button class="btn btn-sm btn-outline" @click="openForm(r)">编辑</button>
            <button class="btn btn-sm btn-danger" style="margin-left:4px" @click="delRecipe(r.recipe_id)">删除</button>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="modal-content" style="max-width:700px">
        <h2 class="modal-title">{{ editingRecipe?.recipe_id ? '编辑食谱' : '新增食谱' }}</h2>

        <div class="grid-2">
          <div class="form-group">
            <label>名称</label>
            <input v-model="form.recipe_name" class="input" required>
          </div>
          <div class="form-group">
            <label>餐次</label>
            <select v-model="form.type" class="input">
              <option value="早餐">早餐</option>
              <option value="午餐">午餐</option>
              <option value="晚餐">晚餐</option>
              <option value="加餐">加餐</option>
            </select>
          </div>
        </div>
        <div class="grid-2">
          <div class="form-group">
            <label>适合专区</label>
            <select v-model="form.suitable_goals" class="input">
              <option value="healthy">健康饮食</option>
              <option value="lose_weight">减脂</option>
              <option value="gain_muscle">增肌</option>
            </select>
          </div>
          <div class="form-group">
            <label>烹饪方式</label>
            <select v-model="form.cook_method" class="input">
              <option v-for="cm in cookingMethods" :key="cm" :value="cm">{{ cm }}</option>
            </select>
          </div>
        </div>
        <div class="grid-2">
          <div class="form-group">
            <label>用油 (g)</label>
            <input v-model.number="form.oil_g" class="input" type="number" min="0" step="1" placeholder="如 15，不填按做法估算">
          </div>
          <div class="form-group">
            <label>用糖/酱料 (g)</label>
            <input v-model.number="form.sauce_g" class="input" type="number" min="0" step="1" placeholder="如 8，不填按做法估算">
          </div>
        </div>
        <div class="form-group">
          <label>简介</label>
          <textarea v-model="form.intro" class="input" rows="2"></textarea>
        </div>

        <h4>食材配比</h4>
        <div class="add-ingredient">
          <select v-model="addFoodId" class="input">
            <option value="" disabled>选择食材</option>
            <option v-for="f in allFoods" :key="f.food_id" :value="f.food_id">
              {{ f.food_name }}（{{ f.nutrition?.calorie || '?' }}kcal/100g）
            </option>
          </select>
          <input v-model.number="addWeight" class="input" type="number" placeholder="克数" style="max-width:100px">
          <button class="btn btn-sm btn-primary" @click="addIngredient">添加</button>
        </div>
        <div v-if="form.ingredients.length" style="margin-top:8px">
          <div v-for="(ing, i) in form.ingredients" :key="i" class="ing-row">
            <span>{{ ing.food_name }}</span>
            <span>{{ ing.weight }}g</span>
            <button class="btn btn-sm btn-danger" @click="form.ingredients.splice(i, 1)">删除</button>
          </div>
        </div>

        <div style="display:flex;gap:8px;margin-top:16px">
          <button class="btn btn-primary" @click="saveRecipe">{{ saving ? '保存中...' : '保存' }}</button>
          <button class="btn btn-outline" @click="showForm = false">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api/index.js'

const recipes = ref([])
const allFoods = ref([])
const cookingMethods = ref([])
const showForm = ref(false)
const editingRecipe = ref(null)
const saving = ref(false)
const addFoodId = ref('')
const addWeight = ref(100)

const form = ref({
  recipe_name: '', type: '午餐', suitable_goals: 'healthy',
  cook_method: '炒', intro: '', oil_g: 0, sauce_g: 0, ingredients: [],
})

const adminUser = JSON.parse(sessionStorage.getItem('admin') || '{}')
if (!adminUser.admin_id) window.location.href = '/admin/login'

async function loadData() {
  const [r, f] = await Promise.all([
    api.getRecipes(),
    api.getFoods(),
  ])
  recipes.value = r.data || []
  allFoods.value = f.data || []
}

function openForm(r) {
  editingRecipe.value = r
  form.value = {
    recipe_name: r.recipe_name || '',
    type: r.type || '午餐',
    suitable_goals: r.suitable_goals || 'healthy',
    cook_method: r.cook_method || '炒',
    intro: r.intro || '',
    ingredients: (r.ingredients || []).map(i => ({
      food_id: i.food_id,
      food_name: i.food_name,
      weight: i.weight,
    })),
  }
  showForm.value = true
}

function addIngredient() {
  const f = allFoods.value.find(x => x.food_id === addFoodId.value)
  if (!f) return
  if (form.value.ingredients.some(i => i.food_id === addFoodId.value)) return
  form.value.ingredients.push({
    food_id: f.food_id,
    food_name: f.food_name,
    weight: addWeight.value,
  })
  addFoodId.value = ''
  addWeight.value = 100
}

async function saveRecipe() {
  saving.value = true
  try {
    const data = {
      ...form.value,
      admin_id: adminUser.admin_id || 1,
    }
    if (editingRecipe.value?.recipe_id) {
      await api.updateRecipe(editingRecipe.value.recipe_id, data)
    } else {
      await api.createRecipe(data)
    }
    showForm.value = false
    loadData()
  } catch (e) {}
  finally { saving.value = false }
}

async function delRecipe(id) {
  if (!confirm('确定删除？')) return
  await api.deleteRecipe(id)
  loadData()
}

onMounted(async () => {
  await loadData()
  const cm = await api.getCookingMethods()
  if (cm.code === 200) cookingMethods.value = cm.data || []
})
</script>

<style scoped>
.admin-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.table {
  width: 100%; border-collapse: collapse; background: #fff; border-radius: var(--radius);
  overflow: hidden; box-shadow: var(--shadow);
}
.table th, .table td { padding: 10px 14px; text-align: left; font-size: 14px; }
.table th { background: var(--bg); font-weight: 600; }
.table td { border-top: 1px solid var(--border); }
.add-ingredient { display: flex; gap: 8px; margin-top: 8px; }
.ing-row { display: flex; gap: 12px; align-items: center; padding: 6px 0; border-bottom: 1px solid var(--border); font-size: 14px; }
.ing-row span:first-child { flex: 1; }
</style>
