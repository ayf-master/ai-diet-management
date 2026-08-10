import { get, post, put, del, postForm } from './request'

export function getUserProfile(userId) { return get(`/user/profile?user_id=${userId}`) }
export function updateUserZones(data) { return put('/user/zones', data) }

export function uploadAvatar(userId, file) {
  const formData = new FormData()
  formData.append('user_id', userId)
  formData.append('avatar', file)
  return postForm('/user/avatar', formData)
}

export function removeAvatar(userId) {
  return del(`/user/avatar?user_id=${userId}`)
}

export function getDiseases() { return get('/diseases') }
export function getUserDiseases(userId) { return get(`/user/diseases?user_id=${userId}`) }
export function addUserDisease(data) { return post('/user/diseases', data) }
export function updateUserDisease(id, data) { return put(`/user/diseases/${id}`, data) }
export function deleteUserDisease(id) { return del(`/user/diseases/${id}`) }
