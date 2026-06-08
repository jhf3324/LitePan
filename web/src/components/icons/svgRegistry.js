/**
 * 固定调色 SVG 片段（供 SvgIcon / 通知条使用），风格参考 Windows 11 彩色 Emoji。
 * 仅允许受控的 name 键，勿将用户输入直接作为 key。
 */
const NS = ' xmlns="http://www.w3.org/2000/svg"'

const SVG_MAP = {
  folder: `<svg viewBox="0 0 24 24"${NS}><path fill="#3B82F6" d="M2 5.5h8.2L11.5 8H22v2.5H2V5.5z"/><path fill="#FACC15" d="M2 9h9.3l1.3 2H22V20a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V9z"/><path fill="#EAB308" opacity=".35" d="M4 12h16v1H4z"/></svg>`,

  'folder-open': `<svg viewBox="0 0 24 24"${NS}><path fill="#CA8A04" d="M2 9h9l2 2h11v8H2V9z"/><path fill="#FDE047" d="M2 8h8.5L12 10h10v1.5H2V8z"/><path fill="#3B82F6" d="M2 6h8.2L11.5 8H22v2H2V6z"/></svg>`,

  file: `<svg viewBox="0 0 24 24"${NS}><path fill="#F1F5F9" stroke="#94A3B8" stroke-width="1" d="M8 2h6l5 5v15H8a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1z"/><path fill="#CBD5E1" d="M14 2v5h5"/></svg>`,

  pdf: `<svg viewBox="0 0 24 24"${NS}><path fill="#EF4444" d="M6 2h7l5 5v15H6V2z"/><path fill="#F1F5F9" d="M14 2v5h5"/><path fill="#fff" d="M8 11h8v1.5H8zm0 3h8v1.5H8zm0 3h5v1.5H8z"/></svg>`,

  doc: `<svg viewBox="0 0 24 24"${NS}><path fill="#2563EB" d="M6 2h7l5 5v15H6V2z"/><path fill="#DBEAFE" d="M14 2v5h5"/><path fill="#fff" d="M8 11h8v1.2H8zm0 2.6h8v1.2H8zm0 2.6h6v1.2H8z"/></svg>`,

  sheet: `<svg viewBox="0 0 24 24"${NS}><path fill="#16A34A" d="M6 2h7l5 5v15H6V2z"/><path fill="#DCFCE7" d="M14 2v5h5"/><path fill="#fff" d="M8 10h8v2H8zm0 3.5h8v2H8zm0 3.5h5v2H8z"/></svg>`,

  slide: `<svg viewBox="0 0 24 24"${NS}><path fill="#EA580C" d="M6 2h7l5 5v15H6V2z"/><path fill="#FFEDD5" d="M14 2v5h5"/><rect x="8" y="11" width="8" height="5" rx="0.5" fill="#fff"/><path fill="#FB923C" d="M9 14h3v2H9zm4-1h3v3h-3z"/></svg>`,

  image: `<svg viewBox="0 0 24 24"${NS}><rect x="3" y="4" width="18" height="16" rx="2" fill="#E0F2FE"/><rect x="3" y="4" width="18" height="16" rx="2" stroke="#38BDF8" stroke-width="1"/><path fill="#22C55E" d="M3 16l4-4 4 4 5-6 5 6v2H3z"/><circle cx="8.5" cy="9" r="1.5" fill="#FACC15"/></svg>`,

  video: `<svg viewBox="0 0 24 24"${NS}><rect x="2" y="6" width="16" height="12" rx="1.5" fill="#5B21B6"/><path stroke="#E9D5FF" stroke-width="1.2" d="M4 9h12M4 12h12M4 15h8"/><rect x="15" y="4" width="7" height="6" rx="1" fill="#1E1B4B"/><path fill="#C4B5FD" d="M17 6h3v2h-3z"/></svg>`,

  audio: `<svg viewBox="0 0 24 24"${NS}><circle cx="9" cy="17" r="3" fill="#DB2777"/><path fill="#F472B6" d="M12 5v10.2a3 3 0 1 0 2 2.8V7h5V5h-7z"/></svg>`,

  archive: `<svg viewBox="0 0 24 24"${NS}><path fill="#EA580C" d="M12 2 4 6v12l8 4 8-4V6l-8-4z"/><path fill="#FDBA74" d="M12 2v20"/><path fill="#C2410C" d="M8 8h8v3H8z"/><path fill="#FED7AA" d="M9 8h6l-1-2h-4l-1 2z"/></svg>`,

  text: `<svg viewBox="0 0 24 24"${NS}><path fill="#F8FAFC" stroke="#94A3B8" stroke-width="1" d="M7 3h10v18H7z"/><path stroke="#64748B" stroke-width="1.2" d="M9 7h6M9 10h6M9 13h4"/></svg>`,

  pencil: `<svg viewBox="0 0 24 24"${NS}><path fill="#FB923C" d="m15.5 5.5 3 3-9.5 9.5H6v-3L15.5 5.5z"/><path fill="#EA580C" d="m17 4 3 3-1.2 1.2-3-3L17 4z"/><path fill="#FDE68A" d="M5 19l1.5-1 2 2-1.5 1H5v-2z"/></svg>`,

  trash: `<svg viewBox="0 0 24 24"${NS}><path fill="#64748B" d="M9 3h6l1 2h5v2H3V5h5l1-2z"/><path fill="#94A3B8" d="M6 9h12v10a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V9z"/><path fill="#475569" d="M10 11h1v7h-1zm3 0h1v7h-1zm3 0h1v7h-1z"/></svg>`,

  'trash-button': `<svg viewBox="0 0 24 24"${NS}><path fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" d="M4 7h16"/><path fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" d="M9 7V5.6c0-.9.7-1.6 1.6-1.6h2.8c.9 0 1.6.7 1.6 1.6V7"/><path fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" d="M7 7l.8 11c.1 1.1 1 2 2.1 2h4.2c1.1 0 2-.9 2.1-2L17 7"/><path fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" d="M10 10.5v5.5M14 10.5v5.5"/></svg>`,

  'trash-row': `<svg viewBox="0 0 1024 1024"${NS}><path fill="#2B2B2B" d="M870.4 230.4a25.6 25.6 0 0 1 25.6 25.6v25.6a25.6 25.6 0 0 1-25.6 25.6h-51.2v486.4a102.4 102.4 0 0 1-102.4 102.4H307.2a102.4 102.4 0 0 1-102.4-102.4V307.2H153.6a25.6 25.6 0 0 1-25.6-25.6V256a25.6 25.6 0 0 1 25.6-25.6h716.8zM742.4 307.2h-460.8v486.4a25.6 25.6 0 0 0 20.992 25.1904L307.2 819.2h409.6a25.6 25.6 0 0 0 25.6-25.6V307.2z m-358.4-204.8h256a25.6 25.6 0 0 1 25.6 25.6V153.6a25.6 25.6 0 0 1-25.6 25.6h-256A25.6 25.6 0 0 1 358.4 153.6v-25.6a25.6 25.6 0 0 1 25.6-25.6z"/><path fill="#CF4C4D" d="M473.6 435.2v256a25.6 25.6 0 0 1-25.6 25.6h-25.6a25.6 25.6 0 0 1-25.6-25.6v-256a25.6 25.6 0 0 1 25.6-25.6h25.6a25.6 25.6 0 0 1 25.6 25.6zM627.2 435.2v256a25.6 25.6 0 0 1-25.6 25.6h-25.6a25.6 25.6 0 0 1-25.6-25.6v-256a25.6 25.6 0 0 1 25.6-25.6h25.6a25.6 25.6 0 0 1 25.6 25.6z"/></svg>`,

  refresh: `<svg viewBox="0 0 24 24"${NS}><path fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" d="M20 11a8 8 0 1 1-2.2-5.5"/><path fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" d="M20 4v5h-5"/></svg>`,

  package: `<svg viewBox="0 0 24 24"${NS}><path fill="#F97316" d="M12 2 4 7v10l8 4 8-4V7l-8-5z"/><path fill="#EA580C" d="M12 2v20"/><path fill="#FED7AA" d="M4 7l8 4 8-4-8-5-8 5z"/></svg>`,

  lightning: `<svg viewBox="0 0 24 24"${NS}><path fill="#EAB308" stroke="#CA8A04" stroke-width="0.5" d="M13 2 4 14h7l-1 8 10-12h-7l0-8z"/></svg>`,

  search: `<svg viewBox="0 0 24 24"${NS}><circle cx="10" cy="10" r="5.5" fill="none" stroke="#64748B" stroke-width="2"/><path stroke="#64748B" stroke-width="2" stroke-linecap="round" d="m14.5 14.5 5 5"/></svg>`,

  user: `<svg viewBox="0 0 24 24"${NS}><circle cx="12" cy="8" r="3.5" fill="#60A5FA"/><path fill="#3B82F6" d="M6 20v-1a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v1H6z"/></svg>`,

  monitor: `<svg viewBox="0 0 24 24"${NS}><rect x="4" y="4" width="16" height="11" rx="1.5" fill="#334155"/><rect x="6" y="6" width="12" height="7" rx="0.5" fill="#94A3B8"/><path fill="#475569" d="M9 18h6v2H9z"/><path fill="#64748B" d="M7 20h10v1H7z"/></svg>`,

  cloud: `<svg viewBox="0 0 24 24"${NS}><path fill="#7DD3FC" d="M6 17h12v1H6z"/><circle cx="8" cy="14" r="4" fill="#38BDF8"/><circle cx="12" cy="12" r="5" fill="#0EA5E9"/><circle cx="16" cy="14" r="4" fill="#38BDF8"/><circle cx="14" cy="16" r="3.5" fill="#7DD3FC"/></svg>`,

  upload: `<svg viewBox="0 0 24 24"${NS}><path fill="#E2E8F0" d="M4 18h16v2H4z"/><path fill="#2563EB" d="M12 4 8 10h3v8h2v-8h3L12 4z"/></svg>`,

  relay: `<svg viewBox="0 0 24 24"${NS}><path fill="none" stroke="#2563EB" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" d="M13 2 5 14h6l-1 8 9-12h-6z"/></svg>`,

  pause: `<svg viewBox="0 0 24 24"${NS}><rect x="6" y="5" width="4" height="14" rx="1" fill="#475569"/><rect x="14" y="5" width="4" height="14" rx="1" fill="#475569"/></svg>`,

  play: `<svg viewBox="0 0 24 24"${NS}><path fill="#475569" d="M9.5 6.5V17.5L18.5 12 9.5 6.5Z"/></svg>`,

  'chevron-down': `<svg viewBox="0 0 24 24"${NS}><path fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" d="m6 9 6 6 6-6"/></svg>`,

  'menu-dots': `<svg viewBox="0 0 24 24"${NS}><circle cx="6" cy="12" r="2" fill="#64748B"/><circle cx="12" cy="12" r="2" fill="#64748B"/><circle cx="18" cy="12" r="2" fill="#64748B"/></svg>`,

  'notify-success': `<svg viewBox="0 0 24 24"${NS}><circle cx="12" cy="12" r="9" fill="#22C55E"/><path fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" d="m7.5 12.5 3 3 6-6"/></svg>`,

  'notify-error': `<svg viewBox="0 0 24 24"${NS}><circle cx="12" cy="12" r="9" fill="#EF4444"/><path stroke="#fff" stroke-width="2.2" stroke-linecap="round" d="M8 8l8 8M16 8l-8 8"/></svg>`,

  'notify-warning': `<svg viewBox="0 0 24 24"${NS}><path fill="#F59E0B" d="M12 3 2 20h20L12 3z"/><path fill="#fff" d="M12 9v5"/><circle cx="12" cy="17.5" r="1.2" fill="#fff"/></svg>`,

  'notify-info': `<svg viewBox="0 0 24 24"${NS}><circle cx="12" cy="12" r="9" fill="#3B82F6"/><path fill="#fff" d="M12 8h.01v.01H12z"/><rect x="11" y="10.5" width="2" height="6" rx="0.5" fill="#fff"/></svg>`,

  copy: `<svg viewBox="0 0 24 24"${NS}><rect x="8" y="8" width="12" height="12" rx="2" fill="#E0E7FF"/><rect x="8" y="8" width="12" height="12" rx="2" fill="none" stroke="#6366F1" stroke-width="1.2"/><path fill="#818CF8" d="M6 4h9.5L18 6.5V18a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1z"/></svg>`
}

export function getSvg(name) {
  return SVG_MAP[name] || SVG_MAP.file
}

export function notifyIconName(type) {
  const m = {
    success: 'notify-success',
    error: 'notify-error',
    warning: 'notify-warning',
    info: 'notify-info'
  }
  return m[type] || 'notify-info'
}
