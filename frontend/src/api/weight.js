import { get, post } from './request'

export function recordWeight(data) { return post('/weight', data) }
export function getWeightHistory(userId, limit = 20) {
  return get(`/weight?user_id=${userId}&limit=${limit}`)
}
export function getLatestWeight(userId) {
  return get(`/weight/latest?user_id=${userId}`)
}
