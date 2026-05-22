/**
 * 文件类型 → SvgIcon 的 name（与 svgRegistry 键一致，贴近 Windows Segoe UI Emoji 配色）。
 */
export function getFileIconKind(file) {
  if (!file || file.is_dir) return 'folder'

  const ext = file.name.split('.').pop()?.toLowerCase() || ''

  const map = {
    pdf: 'pdf',
    doc: 'doc',
    docx: 'doc',
    xls: 'sheet',
    xlsx: 'sheet',
    ppt: 'slide',
    pptx: 'slide',
    jpg: 'image',
    jpeg: 'image',
    png: 'image',
    gif: 'image',
    webp: 'image',
    bmp: 'image',
    svg: 'image',
    mp4: 'video',
    avi: 'video',
    mkv: 'video',
    mov: 'video',
    webm: 'video',
    flv: 'video',
    mp3: 'audio',
    wav: 'audio',
    flac: 'audio',
    aac: 'audio',
    m4a: 'audio',
    ogg: 'audio',
    zip: 'archive',
    rar: 'archive',
    '7z': 'archive',
    tar: 'archive',
    gz: 'archive',
    tgz: 'archive',
    txt: 'text',
    md: 'text',
    log: 'text',
    json: 'text',
    xml: 'text',
    csv: 'text',
    yml: 'text',
    yaml: 'text'
  }

  return map[ext] || 'file'
}
