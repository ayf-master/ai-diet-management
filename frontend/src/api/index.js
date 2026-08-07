// 命名导出（按需解构）
export * from './auth'
export * from './foods'
export * from './recipes'
export * from './meals'
export * from './stats'
export * from './weight'
export * from './ai'
export * from './user'

// ── 默认导出（兼容旧写法: import api from '@/api'; api.login()） ──
import * as Auth from './auth'
import * as Foods from './foods'
import * as Recipes from './recipes'
import * as Meals from './meals'
import * as Stats from './stats'
import * as Weight from './weight'
import * as AI from './ai'
import * as User from './user'

const api = { ...Auth, ...Foods, ...Recipes, ...Meals, ...Stats, ...Weight, ...AI, ...User }
export default api
