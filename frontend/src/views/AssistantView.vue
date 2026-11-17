<template>
  <div class="page assistant-page">
    <div class="assistant-header">
      <div>
        <h1 class="page-title">AI 饮食助手</h1>
        <p class="assistant-sub">基于你的资料和食谱库回答，热量由数据库重新计算。</p>
      </div>
      <span class="assistant-mode">只读工具 · 单轮</span>
    </div>

    <div class="chat-shell">
      <div ref="scrollEl" class="chat-scroll">
        <div v-for="(msg, index) in messages" :key="index" class="msg" :class="msg.role">
          <div class="avatar">{{ msg.role === 'user' ? userLetter : 'AI' }}</div>
          <div class="bubble-wrap">
            <div class="bubble">
              <div
                v-if="msg.role === 'assistant'"
                class="bubble-text"
                v-html="renderAnswer(msg.text)"
              ></div>
              <div v-else class="bubble-text">{{ msg.text }}</div>
            </div>
            <div v-if="msg.meta" class="msg-meta">
              <span class="status-pill" :class="'status-' + msg.meta.status">
                {{ statusLabel(msg.meta.status) }}
              </span>
              <span v-for="tool in msg.meta.tools" :key="tool" class="tool-chip">
                {{ toolLabel(tool) }}
              </span>
              <span v-if="msg.meta.latency" class="meta-time">{{ msg.meta.latency }}</span>
            </div>
          </div>
        </div>

        <div v-if="loading" class="msg assistant">
          <div class="avatar">AI</div>
          <div class="bubble typing"><span></span><span></span><span></span></div>
        </div>
      </div>

      <div v-if="showSuggestions" class="suggestions">
        <button
          v-for="item in suggestions"
          :key="item"
          class="suggestion"
          type="button"
          @click="send(item)"
        >
          {{ item }}
        </button>
      </div>

      <form class="composer" @submit.prevent="send()">
        <textarea
          ref="inputEl"
          v-model="draft"
          class="composer-input"
          rows="2"
          placeholder="问问你的饮食，例如：午餐可以吃什么？"
          :disabled="loading"
          @keydown.enter.exact.prevent="send()"
        ></textarea>
        <button class="btn btn-primary composer-btn" type="submit" :disabled="loading || !draft.trim()">
          {{ loading ? '查询中' : '发送' }}
        </button>
      </form>
      <p class="composer-hint">Enter 发送 · Shift + Enter 换行 · 每次提问独立，不携带上一轮上下文</p>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import api from '../api/index.js'

const user = JSON.parse(sessionStorage.getItem('user') || '{}')
const userLetter = (user.nickname || user.account || '我')[0]

const messages = ref([])
const draft = ref('')
const loading = ref(false)
const scrollEl = ref(null)
const inputEl = ref(null)

const suggestions = [
  '午餐可以吃什么？',
  '我的推荐热量是多少？',
  '番茄炒鸡蛋 200 克热量多少？',
]

const showSuggestions = computed(() => messages.value.length <= 1 && !loading.value)

onMounted(() => {
  messages.value = [{
    role: 'assistant',
    text: '你好，我是饮食助手。我可以查你的资料、搜食谱、按数据库计算营养。\n\n试试下面的问题，或者直接问我。',
  }]
  nextTick(() => inputEl.value?.focus())
})

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function renderAnswer(value) {
  return escapeHtml(value)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
}

function statusLabel(status) {
  const labels = {
    answered: '直接回答',
    tool_answered: '数据库查询',
    repaired: '已自动修复',
    degraded: '降级回答',
    invalid_request: '请求有误',
    unavailable: '服务未配置',
    model_error: '模型异常',
    error: '请求失败',
  }
  return labels[status] || status || '回答'
}

function toolLabel(name) {
  const labels = {
    get_user_profile: '用户资料',
    search_recipes: '食谱检索',
    calculate_recipe_nutrition: '营养计算',
  }
  return labels[name] || name
}

function latencyLabel(trace) {
  const total = (trace || []).reduce((sum, item) => sum + (item.latency_ms || 0), 0)
  if (!total) return ''
  return `${(total / 1000).toFixed(1)}s`
}

async function scrollToBottom() {
  await nextTick()
  const el = scrollEl.value
  if (el) el.scrollTop = el.scrollHeight
}

async function send(text) {
  const question = String(text ?? draft.value).trim()
  if (!question || loading.value) return

  draft.value = ''
  messages.value.push({ role: 'user', text: question })
  loading.value = true
  await scrollToBottom()

  try {
    const res = await api.assistantChat(question, user.user_id)
    const data = res.data || {}
    const answer = data.answer || res.msg || '这次没有拿到回答，请稍后再试。'
    const tools = [...new Set((data.tool_calls || []).filter((item) => item.ok).map((item) => item.name))]
    messages.value.push({
      role: 'assistant',
      text: answer,
      meta: {
        status: data.status || (res.code === 200 ? 'answered' : 'error'),
        tools,
        latency: latencyLabel(data.trace),
      },
    })
  } catch (error) {
    messages.value.push({
      role: 'assistant',
      text: '请求失败，请检查后端是否启动。',
      meta: { status: 'error', tools: [] },
    })
  } finally {
    loading.value = false
    await scrollToBottom()
    nextTick(() => inputEl.value?.focus())
  }
}
</script>

<style scoped>
.assistant-page { max-width: 900px; }
.assistant-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 16px; margin-bottom: 16px;
}
.assistant-header .page-title { margin-bottom: 4px; }
.assistant-sub { font-size: 13px; color: var(--text-light); }
.assistant-mode {
  flex-shrink: 0; margin-top: 4px; padding: 4px 10px;
  border: 1px solid var(--border); border-radius: 999px;
  font-size: 11px; color: var(--text-light); background: #fff;
}

.chat-shell {
  display: flex; flex-direction: column;
  height: calc(100vh - 230px); min-height: 520px;
  background: #fff; border: 1px solid var(--border); border-radius: 12px;
  overflow: hidden;
}
.chat-scroll {
  flex: 1; overflow-y: auto; padding: 24px 22px 12px;
  background: #FCFBF9;
}

.msg { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 18px; }
.msg.user { flex-direction: row-reverse; }
.avatar {
  flex-shrink: 0; width: 28px; height: 28px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: #111; color: #fff; font-size: 11px; font-weight: 700;
}
.msg.user .avatar { background: var(--accent); }
.bubble-wrap { max-width: 78%; min-width: 0; }
.msg.user .bubble-wrap { display: flex; flex-direction: column; align-items: flex-end; }
.bubble {
  padding: 11px 14px; border-radius: 2px 10px 10px 10px;
  background: #F1EFE9; color: var(--text);
  font-size: 14px; line-height: 1.75;
  word-break: break-word;
}
.msg.user .bubble {
  background: #111; color: #fff;
  border-radius: 10px 2px 10px 10px;
}
.bubble-text :deep(strong) { font-weight: 700; }
.msg.user .bubble-text { white-space: pre-wrap; }

.msg-meta { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin-top: 6px; }
.status-pill {
  padding: 2px 7px; border-radius: 999px;
  font-size: 10px; background: #EFEDE7; color: var(--text-light);
}
.status-tool_answered { background: #E8F1FB; color: #2D6DA3; }
.status-repaired { background: #E9F3EA; color: #4F7A52; }
.status-degraded { background: #FBF0E4; color: #A66A2C; }
.status-model_error, .status-error { background: #FBEAE8; color: #B24B3E; }
.tool-chip {
  padding: 2px 7px; border: 1px solid var(--border); border-radius: 999px;
  font-size: 10px; color: var(--text-light); background: #fff;
}
.meta-time { font-size: 10px; color: var(--text-muted); }

.typing { display: flex; align-items: center; gap: 4px; min-height: 24px; }
.typing span {
  width: 5px; height: 5px; border-radius: 50%; background: #A8A49A;
  animation: typing 1.2s infinite ease-in-out;
}
.typing span:nth-child(2) { animation-delay: 0.15s; }
.typing span:nth-child(3) { animation-delay: 0.3s; }
@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-3px); opacity: 1; }
}

.suggestions { display: flex; flex-wrap: wrap; gap: 8px; padding: 0 16px 10px; background: #fff; }
.suggestion {
  padding: 7px 11px; border: 1px solid var(--border); border-radius: 999px;
  background: #fff; color: var(--text-light); font-size: 12px; cursor: pointer;
  transition: all 0.15s;
}
.suggestion:hover { border-color: #999; color: var(--text); background: var(--bg); }

.composer {
  display: flex; align-items: flex-end; gap: 10px;
  padding: 10px 16px 8px; border-top: 1px solid var(--border); background: #fff;
}
.composer-input {
  flex: 1; min-height: 44px; max-height: 120px; resize: none;
  padding: 9px 12px; border: 1px solid var(--border); border-radius: 8px;
  font: inherit; font-size: 14px; line-height: 1.5; outline: none;
  background: #fff; color: var(--text);
}
.composer-input:focus { border-color: #999; }
.composer-btn { height: 42px; min-width: 72px; }
.composer-hint { padding: 0 16px 10px; font-size: 11px; color: var(--text-muted); }

@media (max-width: 768px) {
  .assistant-header { align-items: center; }
  .assistant-sub { max-width: 230px; }
  .chat-shell {
    height: calc(100dvh - var(--top-bar-h) - var(--bottom-nav-h) - 160px);
    min-height: 420px;
  }
  .chat-scroll { padding: 18px 14px 8px; }
  .bubble-wrap { max-width: 85%; }
  .bubble { font-size: 15px; }
  .suggestions { padding: 0 12px 8px; }
  .composer { padding: 8px 12px 6px; }
  .composer-hint { padding: 0 12px 8px; }
}
</style>
