import { get, post, put, del } from './request'

export function getFoods(params = {}) {
  const q = new URLSearchParams(params).toString()
  return get(`/foods${q ? '?' + q : ''}`)
}
export function getFood(id) { return get(`/foods/${id}`) }
export function createFood(data) { return post('/foods', data) }
export function updateFood(id, data) { return put(`/foods/${id}`, data) }
export function deleteFood(id, userId) { return del(`/foods/${id}?user_id=${userId}`) }
export function getFoodCategories() { return get('/food-categories') }
