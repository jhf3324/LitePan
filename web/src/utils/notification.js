import { getSvg, notifyIconName } from '../components/icons/svgRegistry.js'
import { getIconfontSymbolId } from '../components/icons/iconfontSymbolMap.js'

let notificationContainer = null
let notificationId = 0

function createContainer() {
  if (!notificationContainer) {
    notificationContainer = document.createElement('div')
    notificationContainer.id = 'notification-container'
    notificationContainer.className = 'notification-container'
    document.body.appendChild(notificationContainer)
  }
  return notificationContainer
}

function getIconHtml(type) {
  const svgName = notifyIconName(type)
  const sym = getIconfontSymbolId(svgName)
  if (sym) {
    return `<svg class="notification-icon-svg" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="22" height="22" viewBox="0 0 1024 1024" aria-hidden="true" focusable="false"><use href="#${sym}" xlink:href="#${sym}"></use></svg>`
  }
  return getSvg(svgName)
}

function escapeHtml(text) {
  if (text === null || text === undefined) return ''
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }
  return String(text).replace(/[&<>"']/g, match => map[match])
}

function show(message, type = 'info', duration = null) {
  if (duration === null) {
    const defaultDurations = {
      success: 3000,
      error: 5000,
      warning: 4000,
      info: 2000
    }
    duration = defaultDurations[type] || 4000
  }

  const container = createContainer()
  const notification = document.createElement('div')
  const id = ++notificationId

  notification.className = `notification ${type}`
  notification.setAttribute('data-id', id)
  notification.innerHTML = `
    <div class="notification-icon">${getIconHtml(type)}</div>
    <div class="notification-message">${escapeHtml(message)}</div>
  `

  container.appendChild(notification)

  setTimeout(() => {
    if (notification.parentNode) {
      notification.style.animation = 'notificationSlideOut 0.3s ease-in forwards'
      setTimeout(() => {
        if (notification.parentNode) {
          notification.remove()
        }
      }, 300)
    }
  }, duration - 300)

  return id
}

export const notification = {
  show,
  success: (message, duration) => show(message, 'success', duration),
  error: (message, duration) => show(message, 'error', duration),
  warning: (message, duration) => show(message, 'warning', duration),
  info: (message, duration) => show(message, 'info', duration)
}

window.appNotification = notification
