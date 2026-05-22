/**
 * SvgIcon name → iconfont Symbol 的 id（与 iconfont.js 内 <symbol id="..."> 一致）
 * 未列出的 name 仍走 svgRegistry.js 矢量回退。
 */
export const iconfontSymbolIdByName = {
  folder: 'icon-weibiaoti-_huabanfuben',
  'folder-open': 'icon-fawenguanli',
  file: 'icon-wenjian',
  pdf: 'icon-Pdf',
  doc: 'icon-word',
  sheet: 'icon-excel',
  slide: 'icon-ppt',
  image: 'icon-tupian',
  video: 'icon-shipin',
  audio: 'icon-yinpin',
  archive: 'icon-yasuobao',
  text: 'icon-txt',
  pencil: 'icon-qianbi',
  trash: 'icon-a-shapetrash-openpressedtrue',
  refresh: 'icon-NMStubiao-',
  package: 'icon-qiche-cemian',
  lightning: 'icon-ptsxingnengceshiPTS',
  search: 'icon-sousuo',
  upload: 'icon-icon--shangchuan',
  pause: 'icon-zanting',
  play: 'icon-bofang',
  'notify-success': 'icon-chenggong',
  'notify-error': 'icon-71shibai',
  'notify-warning': 'icon-jinggao',
  'notify-info': 'icon-a-020_tishi'
}

export function getIconfontSymbolId(name) {
  return iconfontSymbolIdByName[name] || null
}
