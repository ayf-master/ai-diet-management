import { get, post, put, del } from './request'

export function getRecipes(params = {}) {
  const q = new URLSearchParams(params).toString()
  return get(`/recipes${q ? '?' + q : ''}`)
}
export function getRecipe(id) { return get(`/recipes/${id}`) }
export function createRecipe(data) { return post('/recipes', data) }
export function updateRecipe(id, data) { return put(`/recipes/${id}`, data) }
export function deleteRecipe(id, userId) { return del(`/recipes/${id}?user_id=${userId}`) }
export function getCookingMethods() { return get('/cooking-methods') }
export function getUserCookingPrefs(userId) { return get(`/user-cooking-prefs?user_id=${userId}`) }
export function saveUserCookingPrefs(userId, prefs) { return put('/user-cooking-prefs', { user_id: userId, prefs }) }
export function resetUserCookingPrefs(userId) { return del(`/user-cooking-prefs?user_id=${userId}`) }
