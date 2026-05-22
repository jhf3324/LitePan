export function formatDate(value, fallback = '-') {
  if (!value) return fallback
  try {
    const d = new Date(value)
    if (isNaN(d.getTime())) return fallback
    return d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
  } catch {
    return fallback
  }
}

export function formatDateTime(value, fallback = '-') {
  if (!value) return fallback
  try {
    const d = new Date(value)
    if (isNaN(d.getTime())) return fallback
    return d.toLocaleString('zh-CN')
  } catch {
    return fallback
  }
}

export function formatFileSize(bytes) {
  if (bytes == null || bytes === '') return '-'
  const n = Number(bytes)
  if (isNaN(n)) return '-'
  if (n === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
  const k = 1024
  const i = Math.min(Math.floor(Math.log(n) / Math.log(k)), units.length - 1)
  const v = n / Math.pow(k, i)
  const decimals = i === 0 ? 0 : i >= 4 ? 2 : 2
  return v.toFixed(decimals) + ' ' + units[i]
}

/** 文件/目录大小：目录仅在 size>0 时显示（部分网盘会返回文件夹总占用）。 */
export function formatEntrySize(entry) {
  if (!entry) return '-'
  const size = Number(entry.size)
  if (entry.is_dir && (!Number.isFinite(size) || size <= 0)) return '-'
  return formatFileSize(size)
}
