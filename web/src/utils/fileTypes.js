const IMAGE_EXTENSIONS = new Set([
  'jpg',
  'jpeg',
  'png',
  'gif',
  'webp',
  'bmp',
  'avif'
])

const VIDEO_EXTENSIONS = new Set([
  'mp4',
  'mkv',
  'webm',
  'mov',
  'm4v',
  'avi',
  'flv',
  'rmvb'
])

const AUDIO_EXTENSIONS = new Set([
  'mp3',
  'm4a',
  'aac',
  'ogg',
  'opus',
  'wav',
  'flac'
])

const TEXT_EXTENSIONS = new Set([
  'txt',
  'md',
  'log',
  'json',
  'xml',
  'csv',
  'yml',
  'yaml',
  'ini',
  'conf',
  'srt',
  'vtt',
  'ass',
  'strm',
  'nfo',
  'm3u',
  'm3u8',
  'js',
  'ts',
  'vue',
  'css',
  'html',
  'py',
  'sh',
  'bat',
  'dockerfile',
  'gitignore'
])

export function getFileExtension(fileName = '') {
  const name = String(fileName || '').trim()
  const index = name.lastIndexOf('.')
  if (index <= 0 || index === name.length - 1) return ''
  return name.slice(index + 1).toLowerCase()
}

export function getPreviewKind(file) {
  if (!file || file.is_dir) return 'none'

  const ext = getFileExtension(file.name)
  if (IMAGE_EXTENSIONS.has(ext)) return 'image'
  if (VIDEO_EXTENSIONS.has(ext)) return 'video'
  if (AUDIO_EXTENSIONS.has(ext)) return 'audio'
  if (TEXT_EXTENSIONS.has(ext)) return 'text'
  if (ext === 'pdf') return 'pdf'

  return 'none'
}

export function canPreviewFile(file, enabledKinds = ['image', 'video', 'audio', 'text', 'pdf']) {
  return enabledKinds.includes(getPreviewKind(file))
}

export function getPreviewableFiles(files = [], enabledKinds = ['image', 'video', 'audio', 'text', 'pdf']) {
  return files.filter(file => canPreviewFile(file, enabledKinds))
}
