const API_BASE = 'http://localhost:9876/api'

// 登录后 token 存在 sessionStorage，所有请求自动带上
function authHeader() {
  const token = sessionStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export async function request(method, path, body = null) {
  const options = {
    method,
    headers: { 'Content-Type': 'application/json', ...authHeader() },
  }
  if (body) options.body = JSON.stringify(body)
  try {
    const res = await fetch(`${API_BASE}${path}`, options)
    const ct = res.headers.get('content-type') || ''
    if (ct.includes('application/json')) {
      const data = await res.json()
      // 令牌过期/无效：清掉本地登录态，下一次操作会回到登录页
      if (res.status === 401 && sessionStorage.getItem('token')
          && !path.startsWith('/login') && !path.startsWith('/admin/login')) {
        sessionStorage.removeItem('token')
      }
      return data
    }
    const text = await res.text()
    console.warn(`[API] ${method} ${path} 返回非 JSON:`, text.slice(0, 200))
    return { code: res.status, msg: `服务器错误 (${res.status})，请检查后端是否已重启` }
  } catch (e) {
    console.error(`[API] ${method} ${path} 请求失败:`, e.message)
    if (e.message?.includes('Failed to fetch') || e.message?.includes('NetworkError')) {
      return { code: 0, msg: '无法连接服务器，请确保后端已启动 (端口 9876)' }
    }
    return { code: 0, msg: '网络错误' }
  }
}

export function get(path) { return request('GET', path) }
export function post(path, body) { return request('POST', path, body) }
export function put(path, body) { return request('PUT', path, body) }
export function del(path) { return request('DELETE', path) }

export async function postForm(path, formData) {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: authHeader(),
      body: formData,
    })
    const ct = res.headers.get('content-type') || ''
    if (ct.includes('application/json')) {
      return res.json()
    }
    const text = await res.text()
    console.warn(`[API] POST ${path} 返回非 JSON:`, text.slice(0, 200))
    return { code: res.status, msg: `服务器错误 (${res.status})` }
  } catch (e) {
    console.error(`[API] POST ${path} 请求失败:`, e.message)
    return { code: 0, msg: '网络错误' }
  }
}
