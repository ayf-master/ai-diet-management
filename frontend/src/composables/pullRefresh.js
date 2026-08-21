// 下拉刷新函数注册表（模块级单例）
// 同一时刻只有一个视图处于激活状态，由其注册自己的数据加载函数；
// PullRefresh 组件在用户下拉到位时调用 runPullRefresh() 触发该视图刷新。
let handler = null

export function registerPullRefresh(fn) {
  handler = fn
}

export function unregisterPullRefresh() {
  handler = null
}

export function runPullRefresh() {
  if (typeof handler === 'function') return handler()
  return Promise.resolve()
}
