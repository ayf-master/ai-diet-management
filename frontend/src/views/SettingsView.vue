<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title" style="margin-bottom:0">账号设置</h1>
    </div>

    <div class="settings-layout">
      <!-- 左侧分组导航 -->
      <aside class="settings-nav">
        <div class="nav-group">
          <div class="nav-group-title">个人资料</div>
          <button class="nav-item" :class="{ active: activeSection === 'avatar' }" @click="goSection('avatar')">我的头像</button>
          <button class="nav-item" :class="{ active: activeSection === 'account' }" @click="goSection('account')">账号信息</button>
        </div>
        <div class="nav-group">
          <div class="nav-group-title">饮食偏好</div>
          <button class="nav-item" :class="{ active: activeSection === 'zones' }" @click="goSection('zones')">我的专区</button>
          <button class="nav-item" :class="{ active: activeSection === 'cook' }" @click="goSection('cook')">我的烹饪偏好</button>
        </div>
        <div class="nav-group">
          <div class="nav-group-title">健康设置</div>
          <button class="nav-item" :class="{ active: activeSection === 'health' }" @click="goSection('health')">我的健康禁忌</button>
        </div>
      </aside>

      <!-- 右侧内容区 -->
      <div class="settings-content">
        <section id="sec-avatar" class="settings-section">
          <h2 class="section-title">我的头像</h2>
          <p class="section-desc">点击下方按钮更换头像，支持 JPG / PNG / WebP / GIF</p>
          <div class="card settings-card">
            <div class="avatar-row">
              <div class="avatar-wrap" :class="{ uploading: uploadingAvatar }">
                <img v-if="avatarUrl" :src="avatarUrl" class="avatar-img" alt="头像" />
                <div v-else class="avatar-fallback">{{ avatarLetter }}</div>
                <div v-if="uploadingAvatar" class="avatar-mask">上传中...</div>
              </div>
              <div class="avatar-actions">
                <button class="btn btn-sm btn-outline" @click="chooseAvatar" :disabled="uploadingAvatar">更换头像</button>
                <button v-if="avatarUrl" class="btn btn-sm btn-text" @click="removeAvatar" :disabled="uploadingAvatar">移除</button>
              </div>
            </div>
            <input ref="avatarInput" type="file" accept="image/jpeg,image/png,image/webp,image/gif" style="display:none" @change="onAvatarChange" />
            <p v-if="avatarMsg" class="saved-msg">{{ avatarMsg }}</p>
          </div>
        </section>

        <section id="sec-account" class="settings-section">
          <h2 class="section-title">账号信息</h2>
          <p class="section-desc">当前登录账号的基础资料</p>
          <div class="card settings-card">
            <div class="info-row"><span>账号</span><span>{{ user.account }}</span></div>
            <div class="info-row"><span>昵称</span><span>{{ user.nickname }}</span></div>
            <div class="info-row"><span>BMI</span><span>{{ user.bmi }}</span></div>
            <div class="info-row"><span>推荐热量</span><span>{{ user.recommend_cal }} kcal/日</span></div>
          </div>
        </section>

        <section id="sec-zones" class="settings-section">
          <h2 class="section-title">我的专区</h2>
          <p class="section-desc">选择你关注的饮食专区，首页将展示对应分区的食谱</p>
          <div class="card settings-card">
            <div class="zone-checkboxes">
              <label v-for="z in zoneOptions" :key="z.key" class="zone-checkbox">
                <input type="checkbox" :value="z.key" v-model="selectedZones">
                <span class="check-indicator"></span>
                <span class="check-label">{{ z.label }}</span>
              </label>
            </div>

            <div v-if="cooldownDays > 0" class="cooldown-notice">
              专区修改需间隔30天，还剩 <strong>{{ cooldownDays }}</strong> 天
            </div>

            <button class="btn btn-primary" @click="saveZones"
              :disabled="saving || !hasChanged || cooldownDays > 0">
              {{ saving ? '保存中...' : '保存修改' }}
            </button>
            <p v-if="msg" class="saved-msg">{{ msg }}</p>
          </div>
        </section>

        <section id="sec-cook" class="settings-section">
          <h2 class="section-title">我的烹饪偏好</h2>
          <p class="section-desc">设置你常用的用油量与酱料热量，食谱将按你的方案计算「烹饪增加的热量」。留空即使用系统默认。</p>
          <div class="card settings-card">
            <div class="cook-pref-table">
              <div class="cook-pref-head">
                <span>烹饪方式</span><span>油 (g/100g)</span><span>酱料 (kcal/100g)</span><span></span>
              </div>
              <div v-for="c in cookPrefs" :key="c.cook_method" class="cook-pref-row">
                <span class="cp-method">{{ c.cook_method }}<small v-if="c.is_custom" class="cp-custom">自定义</small></span>
                <input v-model.number="c.oil_per_100g" @input="c.is_custom = true" class="input cp-input" type="number" min="0" step="0.5">
                <input v-model.number="c.sauce_kcal_per_100g" @input="c.is_custom = true" class="input cp-input" type="number" min="0" step="1">
                <button v-if="c.is_custom" class="btn btn-sm btn-outline" @click="resetOne(c)">重置</button>
                <span v-else></span>
              </div>
            </div>

            <button class="btn btn-primary" @click="saveCookPrefs"
              :disabled="savingCook">{{ savingCook ? '保存中...' : '保存修改' }}</button>
            <button class="btn btn-outline" style="margin-left:8px" @click="resetAll" :disabled="savingCook">全部重置为默认</button>
            <p v-if="cookMsg" class="saved-msg">{{ cookMsg }}</p>
          </div>
        </section>

        <section id="sec-health" class="settings-section">
          <h2 class="section-title">我的健康禁忌</h2>
          <p class="section-desc">勾选你患有的疾病，系统会在食材/食谱上标注对你有害的警告，并让 AI 方案避开相关禁忌。</p>
          <div class="card settings-card">
            <div v-if="!allDiseases.length" class="empty-tip">暂无可选疾病</div>
            <div v-else class="disease-list">
              <div v-for="d in allDiseases" :key="d.disease_id" class="disease-row">
                <label class="zone-checkbox" :title="d.forbid_desc">
                  <input type="checkbox" :value="d.disease_id" v-model="selectedDiseaseIds">
                  <span class="check-indicator"></span>
                  <span class="check-label">{{ d.disease_name }}</span>
                </label>
                <input
                  v-if="selectedDiseaseIds.includes(d.disease_id)"
                  v-model="diseaseRemarks[d.disease_id]"
                  class="input remark-input"
                  placeholder="备注：如轻度高血压，2026年体检发现"
                />
              </div>
            </div>

            <button class="btn btn-primary" @click="saveMyHealth"
              :disabled="savingHealth || !hasHealthChanged">{{ savingHealth ? '保存中...' : '保存修改' }}</button>
            <p v-if="healthMsg" class="saved-msg">{{ healthMsg }}</p>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/index.js'
import { getDiseases, getUserDiseases, addUserDisease, updateUserDisease, deleteUserDisease } from '../api/user.js'

const router = useRouter()
let user = JSON.parse(sessionStorage.getItem('user') || '{}')
if (!user.user_id) router.push('/login')

// 左侧导航与滚动高亮
const activeSection = ref('avatar')
const sectionKeys = ['avatar', 'account', 'zones', 'cook', 'health']
let observer = null

function goSection(key) {
  activeSection.value = key
  const el = document.getElementById('sec-' + key)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

const zoneOptions = [
  { key: 'healthy', label: '健康饮食' },
  { key: 'lose_weight', label: '减脂专区' },
  { key: 'gain_muscle', label: '增肌专区' },
]

const selectedZones = ref([])
const cooldownDays = ref(0)
const saving = ref(false)
const msg = ref('')
const hasChanged = ref(false)

const origZones = ref([])

// 我的健康禁忌
const allDiseases = ref([])
const selectedDiseaseIds = ref([])
const origDiseaseIds = ref([])
const diseaseRemarks = ref({})      // disease_id -> 备注
const origDiseaseRemarks = ref({})  // 原始备注基线
const udMap = ref({})               // disease_id -> user_disease 记录 id
const savingHealth = ref(false)
const healthMsg = ref('')
const hasHealthChanged = computed(() => {
  const idsChanged =
    JSON.stringify(selectedDiseaseIds.value.slice().sort()) !==
    JSON.stringify(origDiseaseIds.value.slice().sort())
  if (idsChanged) return true
  for (const id of selectedDiseaseIds.value) {
    const cur = (diseaseRemarks.value[id] || '').trim()
    const orig = (origDiseaseRemarks.value[id] || '').trim()
    if (cur !== orig) return true
  }
  return false
})

// 头像
const rawAvatarUrl = ref('')
const avatarInput = ref(null)
const uploadingAvatar = ref(false)
const avatarMsg = ref('')

const avatarLetter = computed(() => (user.nickname || user.account || '用户')[0])
const avatarUrl = computed(() => {
  if (!rawAvatarUrl.value) return ''
  if (rawAvatarUrl.value.startsWith('http')) return rawAvatarUrl.value
  return `http://localhost:9876${rawAvatarUrl.value}`
})

watch(selectedZones, (val) => {
  hasChanged.value = JSON.stringify(val.slice().sort()) !== JSON.stringify(origZones.value.slice().sort())
}, { deep: true })

// 我的烹饪偏好
const cookPrefs = ref([])
const savingCook = ref(false)
const cookMsg = ref('')

onMounted(async () => {
  const res = await api.getUserProfile(user.user_id)
  if (res.code === 200) {
    const goals = res.data.diet_goals || [res.data.diet_goal || 'healthy']
    selectedZones.value = [...goals]
    origZones.value = [...goals]
    rawAvatarUrl.value = res.data.avatar_url || ''
  }
  await loadCookPrefs()
  await loadMyHealth()

  // 设置 IntersectionObserver 实现滚动高亮
  observer = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        activeSection.value = e.target.id.replace('sec-', '')
      }
    })
  }, { rootMargin: '-20% 0px -70% 0px', threshold: 0 })
  sectionKeys.forEach(k => {
    const el = document.getElementById('sec-' + k)
    if (el) observer.observe(el)
  })
})

onBeforeUnmount(() => {
  if (observer) observer.disconnect()
})

async function loadMyHealth() {
  const [d, ud] = await Promise.all([
    getDiseases(),
    getUserDiseases(user.user_id),
  ])
  allDiseases.value = d.code === 200 ? (d.data || []) : []
  const list = ud.code === 200 ? (ud.data || []) : []
  selectedDiseaseIds.value = list.map(x => x.disease_id)
  origDiseaseIds.value = [...selectedDiseaseIds.value]
  const map = {}
  const remarks = {}
  list.forEach(x => {
    map[x.disease_id] = x.id
    remarks[x.disease_id] = x.remark || ''
  })
  udMap.value = map
  diseaseRemarks.value = { ...remarks }
  origDiseaseRemarks.value = { ...remarks }
}

async function saveMyHealth() {
  savingHealth.value = true; healthMsg.value = ''
  const toAdd = selectedDiseaseIds.value.filter(id => !origDiseaseIds.value.includes(id))
  const toDel = origDiseaseIds.value.filter(id => !selectedDiseaseIds.value.includes(id))
  const toUpdate = origDiseaseIds.value.filter(id =>
    selectedDiseaseIds.value.includes(id) &&
    (diseaseRemarks.value[id] || '').trim() !== (origDiseaseRemarks.value[id] || '').trim()
  )
  try {
    for (const id of toAdd) {
      await addUserDisease({
        user_id: user.user_id,
        disease_id: id,
        remark: diseaseRemarks.value[id] || null,
      })
    }
    for (const id of toDel) {
      const udId = udMap.value[id]
      if (udId) await deleteUserDisease(udId)
    }
    for (const id of toUpdate) {
      const udId = udMap.value[id]
      if (udId) await updateUserDisease(udId, { remark: diseaseRemarks.value[id] || null })
    }
    const ud = await getUserDiseases(user.user_id)
    const list = ud.code === 200 ? (ud.data || []) : []
    const map = {}
    const remarks = {}
    list.forEach(x => {
      map[x.disease_id] = x.id
      remarks[x.disease_id] = x.remark || ''
    })
    udMap.value = map
    diseaseRemarks.value = { ...remarks }
    origDiseaseRemarks.value = { ...remarks }
    selectedDiseaseIds.value = list.map(x => x.disease_id)
    origDiseaseIds.value = [...selectedDiseaseIds.value]
    healthMsg.value = '健康禁忌已保存！'
  } catch (e) {
    healthMsg.value = '网络错误'
  } finally {
    savingHealth.value = false
  }
}

function chooseAvatar() {
  if (avatarInput.value) avatarInput.value.click()
}

async function onAvatarChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    avatarMsg.value = '请选择图片文件'
    return
  }
  if (file.size > 5 * 1024 * 1024) {
    avatarMsg.value = '图片大小不能超过 5MB'
    return
  }
  uploadingAvatar.value = true
  avatarMsg.value = ''
  try {
    const r = await api.uploadAvatar(user.user_id, file)
    if (r.code === 200) {
      rawAvatarUrl.value = r.data.avatar_url
      user.avatar_url = r.data.avatar_url
      sessionStorage.setItem('user', JSON.stringify(user))
      avatarMsg.value = '头像上传成功！'
    } else {
      avatarMsg.value = r.msg || '上传失败'
    }
  } catch (err) {
    avatarMsg.value = '网络错误'
  } finally {
    uploadingAvatar.value = false
    if (avatarInput.value) avatarInput.value.value = ''
  }
}

async function removeAvatar() {
  if (!user.user_id) return
  try {
    const r = await api.removeAvatar(user.user_id)
    if (r.code === 200) {
      rawAvatarUrl.value = ''
      user.avatar_url = ''
      sessionStorage.setItem('user', JSON.stringify(user))
      avatarMsg.value = '头像已移除'
    } else {
      avatarMsg.value = r.msg || '移除失败'
    }
  } catch (e) {
    avatarMsg.value = '网络错误'
  }
}

async function loadCookPrefs() {
  const r = await api.getUserCookingPrefs(user.user_id)
  if (r.code === 200) cookPrefs.value = r.data || []
}

async function saveCookPrefs() {
  savingCook.value = true; cookMsg.value = ''
  try {
    const prefs = cookPrefs.value
      .filter(c => c.is_custom)
      .map(c => ({ cook_method: c.cook_method, oil_per_100g: c.oil_per_100g, sauce_kcal_per_100g: c.sauce_kcal_per_100g }))
    const r = await api.saveUserCookingPrefs(user.user_id, prefs)
    if (r.code === 200) { cookMsg.value = '烹饪偏好已保存！'; await loadCookPrefs() }
    else cookMsg.value = r.msg
  } catch (e) { cookMsg.value = '网络错误' }
  finally { savingCook.value = false }
}

async function resetOne(c) {
  savingCook.value = true; cookMsg.value = ''
  try {
    const prefs = cookPrefs.value
      .filter(x => x.is_custom && x !== c)
      .map(x => ({ cook_method: x.cook_method, oil_per_100g: x.oil_per_100g, sauce_kcal_per_100g: x.sauce_kcal_per_100g }))
    const r = await api.saveUserCookingPrefs(user.user_id, prefs)
    cookMsg.value = r.code === 200 ? '已重置该做法' : r.msg
    await loadCookPrefs()
  } catch (e) { cookMsg.value = '网络错误' }
  finally { savingCook.value = false }
}

async function resetAll() {
  savingCook.value = true; cookMsg.value = ''
  try {
    const r = await api.resetUserCookingPrefs(user.user_id)
    cookMsg.value = r.code === 200 ? '已重置为系统默认' : r.msg
    await loadCookPrefs()
  } catch (e) { cookMsg.value = '网络错误' }
  finally { savingCook.value = false }
}

async function saveZones() {
  saving.value = true; msg.value = ''
  try {
    const res = await api.updateUserZones({
      user_id: user.user_id,
      diet_goals: selectedZones.value,
    })
    if (res.code === 200) {
      msg.value = '专区更新成功！'
      cooldownDays.value = 30
      origZones.value = [...selectedZones.value]
      user.diet_goals = [...selectedZones.value]
      user.diet_goal = selectedZones.value[0]
      sessionStorage.setItem('user', JSON.stringify(user))
    } else {
      msg.value = res.msg
      if (res.data?.days_remaining) cooldownDays.value = res.data.days_remaining
    }
  } catch (e) { msg.value = '网络错误' }
  finally { saving.value = false }
}
</script>

<style scoped>
/* ── 整体布局：左导航 + 右内容 ── */
.settings-layout {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 28px;
  margin-top: 20px;
  align-items: start;
}
.settings-nav {
  position: sticky;
  top: 76px;            /* 留出顶部固定 NavBar(56px) + 20px 间距，避免被顶栏遮挡 */
  align-self: start;
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.nav-group { display: flex; flex-direction: column; gap: 2px; }
.nav-group-title {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-light);
  letter-spacing: .04em;
  padding: 0 12px 6px;
}
.nav-item {
  display: block;
  width: 100%;
  text-align: left;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  color: var(--text);
  font-family: inherit;
  padding: 9px 12px;
  border-radius: 8px;
  border-left: 3px solid transparent;
  transition: background .15s, color .15s, border-color .15s;
}
.nav-item:hover { background: #F5F4F1; }
.nav-item.active {
  background: #EAF2EE;
  color: var(--primary);
  border-left-color: var(--primary);
  font-weight: 600;
}

.settings-content { display: flex; flex-direction: column; gap: 24px; min-width: 0; }
.settings-section { scroll-margin-top: 100px; }
.section-title { font-size: 18px; font-weight: 700; margin: 0 0 4px; }
.section-desc { font-size: 13px; color: var(--text-light); margin: 0 0 14px; }
.settings-card { max-width: none; width: 100%; }

/* ── 窄屏：导航移到顶部横向排列 ── */
@media (max-width: 880px) {
  .settings-layout { grid-template-columns: 1fr; gap: 16px; }
  .settings-nav {
    position: static;
    flex-direction: row;
    flex-wrap: wrap;
    gap: 8px;
  }
  .nav-group { flex-direction: row; flex-wrap: wrap; gap: 6px; }
  .nav-group-title { width: 100%; }
  .nav-item { width: auto; border-left: none; border-bottom: 2px solid transparent; }
  .nav-item.active { border-left: none; border-bottom-color: var(--primary); }
}
.settings-desc { font-size: 14px; color: var(--text-light); margin: 8px 0 16px; }
.zone-checkboxes { display: flex; flex-direction: column; gap: 10px; margin-bottom: 16px; }
.disease-list { display: flex; flex-direction: column; gap: 10px; margin-bottom: 16px; }
.disease-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.disease-row .zone-checkbox { margin: 0; flex-shrink: 0; }
.remark-input { flex: 1; min-width: 160px; font-size: 13px; padding: 5px 8px; border-radius: 6px; }
.zone-checkbox {
  display: flex; align-items: center; gap: 10px; cursor: pointer; font-size: 15px;
}
.zone-checkbox input { width: 18px; height: 18px; accent-color: var(--primary); }
.check-label { font-weight: 500; }
.cooldown-notice {
  font-size: 13px; color: var(--danger); background: #FDEBEC;
  padding: 8px 12px; border-radius: 6px; margin-bottom: 12px;
}
.saved-msg { font-size: 13px; color: var(--primary); margin-top: 8px; }

/* ── 头像 ── */
.avatar-row { display: flex; align-items: center; gap: 16px; }
.avatar-wrap {
  width: 72px; height: 72px; border-radius: 50%;
  overflow: hidden; position: relative;
  background: #111; color: #fff; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  border: 2px solid #EAEAEA;
}
.avatar-wrap.uploading { opacity: 0.7; }
.avatar-img { width: 100%; height: 100%; object-fit: cover; }
.avatar-fallback { font-size: 22px; font-weight: 700; }
.avatar-mask {
  position: absolute; inset: 0; background: rgba(0,0,0,0.5);
  color: #fff; font-size: 12px; display: flex;
  align-items: center; justify-content: center;
}
.avatar-actions { display: flex; flex-direction: column; gap: 8px; }
.btn-text { background: none; border: none; color: var(--text-light); cursor: pointer; font-size: 13px; padding: 0; text-align: left; }
.btn-text:hover { color: #E74C3C; }

.info-row {
  display: flex; justify-content: space-between; padding: 8px 0;
  border-bottom: 1px solid #EAEAEA; font-size: 14px;
}
.info-row:last-child { border-bottom: none; }
.info-row span:last-child { color: var(--text-light); }

/* ── 我的烹饪偏好 ── */
.cook-pref-table { margin-bottom: 16px; border: 1px solid #EAEAEA; border-radius: 8px; overflow: hidden; }
.cook-pref-head, .cook-pref-row {
  display: grid; grid-template-columns: 1.2fr 1fr 1fr 0.9fr; align-items: center;
  gap: 8px; padding: 8px 12px;
}
.cook-pref-head { background: #F7F6F3; font-size: 12px; color: var(--text-light); font-weight: 600; }
.cook-pref-row { border-top: 1px solid #EAEAEA; font-size: 14px; }
.cp-method { font-weight: 500; display: flex; align-items: center; gap: 6px; }
.cp-custom { font-size: 10px; color: #d9730d; background: #FDF1E3; padding: 1px 6px; border-radius: 999px; font-weight: 600; }
.cp-input { max-width: 100%; padding: 5px 8px; }

</style>
