import { get, post, del } from './request'

export function getMealTypes() { return get('/meal-types') }
export function createMeal(data) { return post('/meals', data) }
export function getMeals(params = {}) {
  const q = new URLSearchParams(params).toString()
  return get(`/meals${q ? '?' + q : ''}`)
}
export function deleteMeal(id) { return del(`/meals/${id}`) }
