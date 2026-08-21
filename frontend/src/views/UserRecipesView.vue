<template>
  <div class="page">
    <div class="page-header" style="display:flex;justify-content:space-between;align-items:center">
      <div>
        <h1 class="page-title" style="margin-bottom:0">食谱</h1>
        <p style="font-size:14px;color:var(--text-light);margin-top:4px">管理系统食谱和你自建的食谱</p>
      </div>
      <button class="btn btn-primary btn-sm" @click="openForm({})">新增食谱</button>
    </div>

    <div class="filter-bar">
      <select v-model="filterGoal" class="input" style="max-width:140px">
        <option value="">全部专区</option>
        <option value="healthy">健康饮食</option>
        <option value="lose_weight">减脂</option>
        <option value="gain_muscle">增肌</option>
      </select>
      <select v-model="filterType" class="input" style="max-width:120px">
        <option value="">全部餐次</option>
        <option value="早餐">早餐</option><option value="午餐">午餐</option>
        <option value="晚餐">晚餐</option><option value="加餐">加餐</option>
      </select>
      <input v-model="filterKeyword" class="input" placeholder="搜索..." style="max-width:160px">
      <button class="btn btn-sm btn-primary" @click="loadRecipes">搜索</button>
    </div>

    <div v-if="!recipes.length && !initialLoading" class="empty">暂无食谱</div>
    <div v-else>
      <TransitionGroup name="card" tag="div" class="recipe-grid">
        <div v-for="(r, i) in recipes" :key="r.recipe_id" class="recipe-card"
             :style="{ '--i': i }" @click="showDetail(r)">
        <div class="recipe-img" :style="imgStyle(r)"></div>
        <div class="recipe-body">
          <div class="recipe-top">
            <div class="recipe-tags">
              <span class="badge" :class="'tag-' + zoneKey(r)">{{ zoneLbl(r) }}</span>
              <span v-if="r.health_warning && r.health_warning.level !== 'ok'"
                    class="hw-badge" :class="'hw-' + r.health_warning.level"
                    :title="r.health_warning.reasons.join('\n')">⚠ {{ hwLabel(r.health_warning.level) }}</span>
            </div>
            <span class="src-tag" :class="r.user_id ? 'src-mine' : 'src-system'">{{ r.user_id ? '我的' : '系统' }}</span>
          </div>
          <h3>{{ r.recipe_name }}</h3>
          <p class="recipe-meta">{{ r.type }} · {{ r.total_calorie }}kcal<span v-if="r.added_calorie" class="cook-extra">（含烹饪{{ r.added_calorie }}kcal）</span> · {{ r.cook_method }}</p>
        </div>
        <div class="recipe-actions" @click.stop>
          <button class="btn btn-sm btn-outline" @click.stop="openForm(r)">编辑</button>
          <button class="btn btn-sm btn-danger" @click.stop="delRecipe(r)" style="margin-left:4px">删除</button>
        </div>
      </div>
      </TransitionGroup>
    </div>
      <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="modal-content" style="max-width:700px">
        <h2 class="modal-title">{{ editingRecipe?.recipe_id ? '编辑食谱' : '新增食谱' }}</h2>

        <div class="grid-2">
          <div class="form-group"><label>名称</label><input v-model="form.recipe_name" class="input" required></div>
          <div class="form-group"><label>餐次</label>
            <select v-model="form.type" class="input"><option>早餐</option><option>午餐</option><option>晚餐</option><option>加餐</option></select>
          </div>
        </div>
        <div class="grid-2">
          <div class="form-group"><label>专区</label>
            <select v-model="form.suitable_goals" class="input">
              <option value="healthy">健康饮食</option><option value="lose_weight">减脂</option><option value="gain_muscle">增肌</option>
            </select>
          </div>
          <div class="form-group"><label>烹饪方式</label>
            <select v-model="form.cook_method" class="input">
              <option v-for="cm in cookingMethods" :key="cm" :value="cm">{{ cm }}</option>
            </select>
          </div>
        </div>
        <div class="grid-2">
          <div class="form-group"><label>用油 (g)</label><input v-model.number="form.oil_g" class="input" type="number" min="0" step="1" placeholder="如 15，不填按做法估算"></div>
          <div class="form-group"><label>用糖/酱料 (g)</label><input v-model.number="form.sauce_g" class="input" type="number" min="0" step="1" placeholder="如 8，不填按做法估算"></div>
        </div>
        <div class="form-group"><label>简介</label><textarea v-model="form.intro" class="input" rows="2"></textarea></div>

        <h4 style="margin:12px 0 8px">食材配比</h4>
        <div class="add-ing">
          <select v-model="addFoodId" class="input">
            <option value="" disabled>选择食材</option>
            <option v-for="f in allFoods" :key="f.food_id" :value="f.food_id">
              {{ f.food_name }} ({{ f.nutrition?.calorie || '?' }}kcal)
            </option>
          </select>
          <input v-model.number="addWeight" class="input" type="number" placeholder="g" style="max-width:80px">
          <button class="btn btn-sm btn-primary" @click="addIngredient">+</button>
        </div>
        <div v-if="form.ingredients.length" class="ing-list">
          <div v-for="(ing, i) in form.ingredients" :key="i" class="ing-row">
            <span class="ing-name">{{ ing.food_name }}</span><span>{{ ing.weight }}g</span>
            <button class="btn btn-sm btn-danger" @click="form.ingredients.splice(i,1)" style="padding:2px 8px">x</button>
          </div>
        </div>

        <div style="display:flex;gap:8px;margin-top:16px">
          <button class="btn btn-primary" @click="saveRecipe">{{ saving ? '保存中...' : '保存' }}</button>
          <button class="btn btn-outline" @click="showForm = false">取消</button>
        </div>
      </div>
    </div>

    <div v-if="detail" class="modal-overlay" @click.self="detail = null">
      <div class="modal-content detail-modal">
        <div class="modal-img" :style="imgStyle(detail)">
          <span class="food-label">{{ detail.recipe_name }}</span>
        </div>
        <h2 class="modal-title">{{ detail.recipe_name }}</h2>
        <div class="detail-stats">
          <div class="detail-stat"><strong>{{ detail.total_calorie }}</strong><small>kcal</small></div>
          <div class="detail-stat"><strong>{{ detail.total_weight }}</strong><small>g</small></div>
          <div class="detail-stat"><strong>{{ detail.cook_method }}</strong><small>烹饪</small></div>
        </div>
        <p v-if="detail.intro" class="detail-desc">{{ detail.intro }}</p>
        <p v-if="detail.forbid_tips" class="detail-forbid">禁忌：{{ detail.forbid_tips }}</p>
        <div v-if="detail.health_warning && detail.health_warning.level !== 'ok'"
             class="detail-warn" :class="'dw-' + detail.health_warning.level">
          <strong>⚠ 健康提示（{{ hwLabel(detail.health_warning.level) }}）</strong>
          <ul><li v-for="(rs, i) in detail.health_warning.reasons" :key="i">{{ rs }}</li></ul>
        </div>
        <h4 style="margin:16px 0 8px">食材清单</h4>
        <div v-for="ing in detail.ingredients" :key="ing.food_id" class="detail-ing-row">
          <span class="detail-ing-name">{{ ing.food_name }}</span>
          <span class="detail-ing-weight">{{ ing.weight }}g</span>
          <span class="detail-ing-cal">{{ ing.calorie ?? '?' }}kcal</span>
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
import { ref, onMounted, onBeforeUnmount } from 'vue'
import api from '../api/index.js'
import { registerPullRefresh, unregisterPullRefresh } from '../composables/pullRefresh.js'

const user = JSON.parse(sessionStorage.getItem('user') || '{}')

const recipes = ref([])
const allFoods = ref([])
const cookingMethods = ref([])
const initialLoading = ref(true)
const fetching = ref(false)
const filterGoal = ref('')
const filterType = ref('')
const filterKeyword = ref('')
const showForm = ref(false)
const editingRecipe = ref(null)
const saving = ref(false)
const addFoodId = ref('')
const addWeight = ref(100)
const detail = ref(null)

const form = ref({
  recipe_name: '', type: '午餐', suitable_goals: 'healthy',
  cook_method: '炒', intro: '', oil_g: 0, sauce_g: 0, ingredients: [],
})

const foodTags = {
  '番茄炒鸡蛋': 'tomato,egg,stirfry', '清蒸鸡胸肉': 'chicken,breast,steamed',
  '水煮西兰花': 'broccoli,boiled', '全麦三明治': 'sandwich,whole,wheat',
  '燕麦牛奶粥': 'oatmeal,porridge,milk', '煎鸡胸肉沙拉': 'chicken,salad,grilled',
  '番茄牛腩汤': 'beef,tomato,soup', '香蕉酸奶': 'banana,yogurt',
  '早餐': 'breakfast,chinese', '午餐': 'lunch,chinese',
  '晚餐': 'dinner,chinese', '加餐': 'snack,food',
}

function imgStyle(r) {
  const tags = foodTags[r.recipe_name] || foodTags[r.type] || 'food,chinese'
  return { background: `url(https://loremflickr.com/400/200/${tags}?lock=${r.recipe_id||1}) center/cover no-repeat rgb(240,240,240)` }
}
function zoneKey(r) {
  const g = r.suitable_goals || ''
  if (g.includes('lose')) return 'lose'
  if (g.includes('gain')) return 'gain'
  return 'healthy'
}
function zoneLbl(r) {
  const g = r.suitable_goals || ''
  if (g.includes('lose')) return '减脂'
  if (g.includes('gain')) return '增肌'
  return '健康'
}

async function loadRecipes() {
  if (fetching.value) return
  fetching.value = true
  const params = { user_id: user.user_id }
  if (filterGoal.value) params.goal = filterGoal.value
  if (filterType.value) params.type = filterType.value
  if (filterKeyword.value) params.keyword = filterKeyword.value
  const [r, f, cm] = await Promise.all([
    api.getRecipes(params),
    api.getFoods({ user_id: user.user_id }),
    api.getCookingMethods(),
  ])
  recipes.value = r.data || []
  allFoods.value = f.data || []
  if (cm.code === 200) cookingMethods.value = cm.data || []
  initialLoading.value = false
  fetching.value = false
}

function openForm(r) {
  editingRecipe.value = r
  form.value = {
    recipe_name: r.recipe_name || '', type: r.type || '午餐',
    suitable_goals: r.suitable_goals || 'healthy', cook_method: r.cook_method || '炒',
    intro: r.intro || '',
    oil_g: r.oil_g || 0, sauce_g: r.sauce_g || 0,
    ingredients: (r.ingredients || []).map(i => ({ food_id: i.food_id, food_name: i.food_name, weight: i.weight })),
  }
  showForm.value = true
}

function showDetail(r) {
  detail.value = r
}

function hwLabel(level) {
  return level === 'danger' ? '有害' : level === 'warn' ? '注意' : '安全'
}

function addIngredient() {
  const f = allFoods.value.find(x => x.food_id === addFoodId.value)
  if (!f || form.value.ingredients.some(i => i.food_id === addFoodId.value)) return
  form.value.ingredients.push({ food_id: f.food_id, food_name: f.food_name, weight: addWeight.value })
  addFoodId.value = ''; addWeight.value = 100
}

async function saveRecipe() {
  saving.value = true
  try {
    const data = { ...form.value, user_id: user.user_id }
    if (editingRecipe.value?.recipe_id) {
      await api.updateRecipe(editingRecipe.value.recipe_id, data)
    } else {
      await api.createRecipe(data)
    }
    showForm.value = false
    loadRecipes()
  } catch (e) {}
  finally { saving.value = false }
}

async function delRecipe(r) {
  if (!confirm('确定删除？')) return
  await api.deleteRecipe(r.recipe_id, user.user_id)
  loadRecipes()
}

onMounted(() => {
  loadRecipes()
  registerPullRefresh(loadRecipes)
})
onBeforeUnmount(unregisterPullRefresh)
</script>

<style scoped>
.filter-bar { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
.recipe-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
@media (max-width:640px) { .recipe-grid { grid-template-columns: 1fr; } }
.recipe-card {
  border: 1px solid #EAEAEA; border-radius: 8px; overflow: hidden;
  cursor: pointer; background: #fff;
  transition: box-shadow 0.2s, transform 0.2s;
}
.recipe-card:hover { box-shadow: 0 4px 14px rgba(0,0,0,0.06); transform: translateY(-2px); }
.recipe-img { height: 130px; }
.recipe-body { padding: 10px 14px; }
.recipe-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.recipe-tags { display: flex; gap: 6px; align-items: center; }

/* ── 健康警告标（与食材页一致） ── */
.hw-badge { font-size: 10px; padding: 2px 6px; border-radius: 3px; cursor: help; white-space: nowrap; }
.hw-warn { background: #FDF1E3; color: #d9730d; }
.hw-danger { background: #FDEBEC; color: #9F2F2D; }
.detail-warn { margin-top: 10px; padding: 10px 12px; border-radius: 8px; font-size: 13px; line-height: 1.6; }
.dw-warn { background: #FDF1E3; color: #9a5b15; }
.dw-danger { background: #FDEBEC; color: #9F2F2D; }
.detail-warn ul { margin: 6px 0 0; padding-left: 18px; }
.recipe-card h3 { font-size: 15px; font-weight: 600; }
.recipe-meta { font-size: 12px; color: #787774; margin-top: 2px; }
.recipe-actions { padding: 6px 14px 10px; border-top: 1px solid #EAEAEA; }
.tag-lose { background: #FDEBEC; color: #9F2F2D; }
.tag-gain { background: #EDF3EC; color: #346538; }
.tag-healthy { background: #E1F3FE; color: #1F6C9F; }
.badge { font-size: 10px; padding: 2px 8px; border-radius: 999px; text-transform: uppercase; letter-spacing: 0.03em; }
.src-tag { font-size: 10px; padding: 2px 6px; border-radius: 3px; }
.src-system { background: #F7F6F3; color: #999; }
.src-mine { background: #EDF3EC; color: #346538; }
.add-ing { display: flex; gap: 6px; margin-top: 6px; }
.add-ing .input:first-child { flex: 1; }
.ing-list { margin-top: 8px; }
.ing-row { display: flex; gap: 8px; align-items: center; padding: 5px 0; border-bottom: 1px solid #EAEAEA; font-size: 14px; }
.ing-name { flex: 1; }

/* ── 卡片入场（级联） ── */
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
}
@keyframes card-out {
  to { opacity: 0; transform: scale(0.85) translateY(-6px); }
}
.card-move {
  transition: transform 0.35s ease;
}
.recipe-grid { position: relative; }

/* 详情弹窗样式 */
.detail-modal .modal-img {
  height: 200px; border-radius: 8px; display: flex; align-items: center; justify-content: center;
  margin-bottom: 16px; background-size: cover; background-position: center;
}
.detail-modal .food-label {
  font-size: 14px; font-weight: 600; color: var(--text);
  background: rgba(255,255,255,0.55); padding: 2px 10px; border-radius: 6px;
}
.detail-modal .detail-stats { display: flex; gap: 12px; margin: 12px 0; }
.detail-modal .detail-stat {
  text-align: center; padding: 8px 12px; background: var(--bg, #F7F6F3); border-radius: 8px; flex: 1;
}
.detail-modal .detail-stat strong { display: block; font-size: 16px; }
.detail-modal .detail-stat small { font-size: 11px; color: var(--text-light); }
.detail-modal .detail-desc { font-size: 14px; color: var(--text-light); margin: 8px 0; }
.detail-modal .detail-forbid { color: var(--danger); font-size: 13px; margin-top: 6px; }
.detail-modal .detail-ing-row { display: flex; gap: 12px; padding: 5px 0; border-bottom: 1px solid var(--border-light); font-size: 14px; }
.detail-modal .detail-ing-row:last-child { border-bottom: none; }
.detail-modal .detail-ing-name { flex: 1; }
.detail-modal .detail-ing-weight { color: var(--text-light); }
.detail-modal .detail-ing-cal { font-weight: 600; color: var(--primary); }
</style>
