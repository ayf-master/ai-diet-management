import { get } from './request'

export function getDailyStats(userId, date) {
  return get(`/stats/daily?user_id=${userId}&date=${date}`)
}
export function getWeeklyStats(userId) {
  return get(`/stats/weekly?user_id=${userId}`)
}
