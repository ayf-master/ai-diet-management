import { get, post, del } from './request'

export function generatePlan(userId) { return post('/ai/plan', { user_id: userId }) }
export function getPlans(userId) { return get(`/ai/plan?user_id=${userId}`) }
export function generateReport(userId) { return post('/ai/report', { user_id: userId }) }
export function getReports(userId) { return get(`/ai/report?user_id=${userId}`) }
export function deletePlan(planId) { return del(`/ai/plan/${planId}`) }
export function deleteReport(reportId) { return del(`/ai/report/${reportId}`) }
