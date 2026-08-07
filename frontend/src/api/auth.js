import { post } from './request'

export function login(account, password) { return post('/login', { account, password }) }
export function register(data) { return post('/register', data) }
export function sendCode(account) { return post('/send-code', { account }) }
export function resetPassword(account, code, password) {
  return post('/reset-password', { account, code, password })
}
export function adminLogin(account, password) {
  return post('/admin/login', { account, password })
}
