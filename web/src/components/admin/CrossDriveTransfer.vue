<template>
  <div class="cross-transfer">
    <!-- 方向卡片 -->
    <div class="flow-grid">
      <div
        v-for="r in routes"
        :key="r.id"
        class="flow-card"
        :class="{ active: activeId === r.id }"
        @click="selectRoute(r)"
      >
        <span v-if="r.bidirectional" class="fc-flag">双向</span>
        <div class="fc-body">
          <div class="fc-logos">
            <span class="fc-logo"><img :src="r.from.logo" :alt="r.from.name" @error="hideImg"></span>
            <span class="fc-conn">
              <i class="fc-dir fas" :class="r.bidirectional ? 'fa-right-left both' : 'fa-arrow-right-long'"></i>
            </span>
            <span class="fc-logo"><img :src="r.to.logo" :alt="r.to.name" @error="hideImg"></span>
          </div>
          <div class="fc-meta">
            <span class="fc-pill" :class="{ md5: r.method === 'md5' }">
              <i class="fas fa-fingerprint"></i>
              <span>{{ r.method_label }}</span>
            </span>
          </div>
        </div>
      </div>

      <!-- 更多组合占位 -->
      <div class="flow-card disabled" @click="notify('warning', '更多组合规划中')">
        <div class="fc-body">
          <div class="fc-logos">
            <span class="fc-logo placeholder"><i class="fas fa-ellipsis"></i></span>
            <span class="fc-conn">
              <i class="fc-dir plain fas fa-plus"></i>
            </span>
            <span class="fc-logo placeholder"><i class="fas fa-cloud"></i></span>
          </div>
          <div class="fc-meta">
            <span class="fc-pill muted">
              <i class="fas fa-screwdriver-wrench"></i>
              <span>更多组合</span>
            </span>
            <span class="fc-soon">规划中</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 两栏 + 中间箭头 -->
    <div class="transfer-row">
      <div class="panel src">
        <div class="panel-head">
          <span class="logo-chip s30"><img v-if="srcPan.logo" :src="srcPan.logo" :alt="srcPan.name" @error="hideImg"></span>
          <div class="panel-title">{{ srcPan.name || '源网盘' }}<small>读取文件指纹</small></div>
          <span class="panel-role">源</span>
        </div>
        <div class="panel-pick">
          <button class="combo" @click="openPicker('src')">
            <span class="c-ic"><i class="fas fa-hdd"></i></span>
            <span class="c-text" :class="{ placeholder: !src }">{{ src ? (src.accName + ' · ' + src.path) : '选择账号 · 目录' }}</span>
            <span class="c-caret"><i class="fas fa-chevron-down"></i></span>
          </button>
        </div>
        <div class="tree" ref="srcTreeRef">
          <div v-if="!srcTree || !srcTree.length" class="tree-empty">选择源目录并试探后显示文件结构</div>
          <CrossTransferTree v-else :nodes="srcTree" mode="src" :depth="0" />
        </div>
      </div>

      <div class="arrow-col">
        <button class="arrow-orb" :class="curRoute && curRoute.bidirectional ? 'swap' : 'locked'" @click="swap">
          <i class="fas" :class="curRoute && curRoute.bidirectional ? 'fa-right-left' : 'fa-arrow-right-long'"></i>
        </button>
        <span v-if="curRoute && curRoute.bidirectional" class="swap-hint">可交换方向</span>
      </div>

      <div class="panel dst">
        <div class="panel-head">
          <span class="logo-chip s30"><img v-if="dstPan.logo" :src="dstPan.logo" :alt="dstPan.name" @error="hideImg"></span>
          <div class="panel-title">{{ dstPan.name || '目标网盘' }}<small>秒传命中后转存</small></div>
          <span class="panel-role">目标</span>
        </div>
        <div class="panel-pick">
          <button class="combo" @click="openPicker('dst')">
            <span class="c-ic"><i class="fas fa-hdd"></i></span>
            <span class="c-text" :class="{ placeholder: !dst }">{{ dst ? (dst.accName + ' · ' + dst.path) : '选择账号 · 目录' }}</span>
            <span class="c-caret"><i class="fas fa-chevron-down"></i></span>
          </button>
        </div>
        <div class="tree">
          <div v-if="!dstTree || !dstTree.length" class="tree-empty">秒传完成后显示已转存文件</div>
          <CrossTransferTree v-else :nodes="dstTree" mode="dst" :depth="0" />
        </div>
      </div>
    </div>

    <!-- 操作条 -->
    <div class="footer">
      <div class="metrics">
        <div class="metric"><span class="n">{{ metrics.total }}</span> <span class="l">扫描文件</span></div>
        <div class="metric"><span class="n ok">{{ metrics.ok }}</span> <span class="l">可秒传</span></div>
        <div class="metric"><span class="n no">{{ metrics.no }}</span> <span class="l">不可秒传</span></div>
        <div class="metric"><span class="n">{{ metrics.done }}</span> <span class="l">已转存</span></div>
        <div class="progress"><div :style="{ width: barWidth + '%' }"></div></div>
      </div>
      <div class="actions">
        <div class="seg">
          <i class="fas fa-triangle-exclamation"></i> <span class="seg-label">冲突</span>
          <select v-model="conflict">
            <option value="rename">自动重命名</option>
            <option value="overwrite">覆盖</option>
          </select>
        </div>
        <button class="ct-btn ct-btn-primary" :disabled="!canProbe" @click="probe">
          <i class="fas fa-magnifying-glass"></i> {{ running === 'probe' ? '试探中…' : '试探可秒传' }}
        </button>
        <button class="ct-btn ct-btn-go" :disabled="!canStart" @click="start">
          <i class="fas fa-bolt"></i> {{ running === 'exec' ? '秒传中…' : '开始秒传' }}
        </button>
        <button class="ct-btn ct-btn-danger" :disabled="!!running" @click="reset()">
          <i class="fas fa-rotate-left"></i> 重置
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import axios from 'axios'
import { useModal } from '../../composables/useModal'
import CrossTransferTree from './CrossTransferTree.vue'
import CrossTransferPickerModal from './CrossTransferPickerModal.vue'

const { custom } = useModal()

const routes = ref([])
const activeId = ref('')
const swapped = ref(false)

const src = ref(null)        // { accId, accName, parentId, path }
const dst = ref(null)
const srcTree = ref(null)
const dstTree = ref(null)
const probeFiles = ref([])   // 扁平文件列表（含 reuse），执行秒传用

const conflict = ref('rename')
const running = ref('')      // '' | 'probe' | 'exec'
const barWidth = ref(0)
const metrics = reactive({ total: 0, ok: 0, no: 0, done: 0 })

const accounts = ref([])
const srcTreeRef = ref(null)

const curRoute = computed(() => routes.value.find(r => r.id === activeId.value) || null)
const srcDriver = computed(() => {
  if (!curRoute.value) return ''
  return swapped.value ? curRoute.value.to.driver : curRoute.value.from.driver
})
const dstDriver = computed(() => {
  if (!curRoute.value) return ''
  return swapped.value ? curRoute.value.from.driver : curRoute.value.to.driver
})
const srcPan = computed(() => panOf(srcDriver.value))
const dstPan = computed(() => panOf(dstDriver.value))

const canProbe = computed(() => !!src.value && !!dst.value && !running.value)
const canStart = computed(() => !running.value && metrics.ok > 0 && probeFiles.value.some(f => f.reuse === true))

function panOf(driver) {
  const r = curRoute.value
  if (!r) return {}
  if (r.from.driver === driver) return r.from
  if (r.to.driver === driver) return r.to
  return {}
}
function accountsFor(driver) {
  return accounts.value.filter(a => a.driver_type === driver && a.is_active !== false)
}

const hideImg = (e) => { e.target.style.display = 'none' }
const notify = (type, msg) => { window.appNotification?.[type]?.(msg) }

// ===== 卡片 =====
function selectRoute(r) {
  activeId.value = r.id
  swapped.value = false
  reset()
}
function swap() {
  if (!curRoute.value || !curRoute.value.bidirectional) return
  swapped.value = !swapped.value
  reset()
  notify('success', `已交换方向：${srcPan.value.name} → ${dstPan.value.name}`)
}

// ===== 选择账号 + 目录（复用 FolderSelectorModal）=====
async function openPicker(mode) {
  const driver = mode === 'src' ? srcDriver.value : dstDriver.value
  const panName = panOf(driver).name || driver
  const accs = accountsFor(driver)
  if (!accs.length) {
    notify('warning', `没有可用的${panName}账号，请先到「存储管理」添加`)
    return
  }
  const cur = mode === 'src' ? src.value : dst.value
  try {
    const result = await custom({
      title: '',
      size: null,
      closable: false,
      hideFooter: true,
      bodyClass: 'modal-body-flush',
      component: CrossTransferPickerModal,
      componentProps: {
        mode,
        panName,
        accounts: accs,
        initialAccId: cur?.accId || accs[0]?.id || '',
        initialPath: cur?.path || ''
      }
    })
    if (!result) return
    const sel = { accId: result.accId, accName: result.accName, parentId: result.parentId, path: result.path }
    if (mode === 'src') {
      src.value = sel
      srcTree.value = null
      probeFiles.value = []
    } else {
      dst.value = sel
    }
    dstTree.value = null
    resetMetrics()
  } catch (e) {
    // 用户取消，忽略
  }
}

// ===== 试探（先扫描秒列文件树，再流式逐文件试探）=====
async function probe() {
  if (!src.value || !dst.value || !curRoute.value) return
  running.value = 'probe'
  barWidth.value = 8
  srcTree.value = null
  resetMetrics()

  let scan
  try {
    const resp = await axios.post('/api/cross-transfer/scan', {
      source_account_id: src.value.accId,
      source_parent_id: src.value.parentId,
      method: curRoute.value.method
    })
    if (!resp.data || !resp.data.success) {
      notify('error', resp.data?.message || '扫描失败')
      running.value = ''
      barWidth.value = 0
      return
    }
    scan = resp.data.data
  } catch (e) {
    notify('error', '扫描失败: ' + (e.response?.data?.message || e.message))
    running.value = ''
    barWidth.value = 0
    return
  }

  decorateTree(scan.tree)
  srcTree.value = scan.tree
  probeFiles.value = scan.files || []
  metrics.total = scan.total
  metrics.ok = 0
  metrics.no = 0
  metrics.done = 0
  if (scan.truncated) notify('warning', `文件较多，仅扫描前 ${scan.total} 个`)

  // rel_path -> 树文件节点，方便流式更新
  const nodeMap = {}
  const walk = (nodes) => { for (const n of nodes || []) { if (n.type === 'dir') walk(n.children); else nodeMap[n.rel_path] = n } }
  walk(srcTree.value)
  const fileMap = {}
  probeFiles.value.forEach(f => { fileMap[f.rel_path] = f })

  const orderedPaths = probeFiles.value.map(f => f.rel_path)
  const setNodeRun = (relPath, run) => {
    const node = nodeMap[relPath]
    if (!node) return
    if (run) node.state = 'run'
    else delete node.state
  }
  const clearAllRun = () => {
    for (const p of orderedPaths) setNodeRun(p, false)
  }
  const scrollToFile = (relPath) => {
    nextTick(() => {
      const root = srcTreeRef.value
      if (!root || !relPath) return
      const el = root.querySelector(`[data-rel-path="${CSS.escape(relPath)}"]`)
      if (el) el.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
    })
  }
  if (orderedPaths.length) {
    setNodeRun(orderedPaths[0], true)
    scrollToFile(orderedPaths[0])
  }

  let processed = 0
  try {
    const resp = await fetch('/api/cross-transfer/probe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify({
        target_account_id: dst.value.accId,
        target_parent_id: dst.value.parentId,
        method: curRoute.value.method,
        files: probeFiles.value.map(f => ({ rel_path: f.rel_path, name: f.name, size: f.size, hash: f.hash }))
      })
    })
    if (!resp.ok || !resp.body) {
      notify('error', `试探失败 (HTTP ${resp.status})`)
      return
    }
    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      let idx
      while ((idx = buffer.indexOf('\n')) >= 0) {
        const line = buffer.slice(0, idx).trim()
        buffer = buffer.slice(idx + 1)
        if (!line) continue
        let msg
        try { msg = JSON.parse(line) } catch { continue }
        if (msg.event === 'item') {
          const relPath = msg.rel_path
          const node = nodeMap[relPath]
          setNodeRun(relPath, false)
          if (node) {
            node.reuse = msg.reuse
            delete node.state
          }
          const f = fileMap[relPath]
          if (f) f.reuse = msg.reuse
          if (msg.reuse) metrics.ok++; else metrics.no++
          processed++
          barWidth.value = metrics.total ? Math.round(processed / metrics.total * 100) : 0
          const nextPath = orderedPaths[processed]
          if (nextPath) {
            setNodeRun(nextPath, true)
            scrollToFile(nextPath)
          }
        } else if (msg.event === 'end') {
          metrics.ok = msg.ok
          metrics.no = msg.no
        } else if (msg.event === 'error') {
          notify('error', msg.message || '试探失败')
        }
      }
    }
    notify('success', `试探完成，可秒传 ${metrics.ok}/${metrics.total}`)
  } catch (e) {
    notify('error', '试探失败: ' + (e.message || e))
  } finally {
    clearAllRun()
    running.value = ''
    setTimeout(() => { barWidth.value = 0 }, 500)
  }
}

// ===== 开始秒传 =====
async function start() {
  const files = probeFiles.value.filter(f => f.reuse === true)
  if (!files.length) return
  running.value = 'exec'
  barWidth.value = 30
  try {
    const resp = await axios.post('/api/cross-transfer/execute', {
      target_account_id: dst.value.accId,
      target_parent_id: dst.value.parentId,
      method: curRoute.value.method,
      files: files.map(f => ({ rel_path: f.rel_path, rel_dir: f.rel_dir, name: f.name, size: f.size, hash: f.hash })),
      conflict: conflict.value
    })
    if (!resp.data || !resp.data.success) {
      notify('error', resp.data?.message || '秒传失败')
      return
    }
    const data = resp.data.data
    metrics.done = data.done
    applyTransferResults(data.results)
    buildDstTree(data.results, files)
    barWidth.value = 100
    notify(data.done === data.total ? 'success' : 'warning', `秒传完成 ${data.done}/${data.total}`)
  } catch (e) {
    notify('error', '秒传失败: ' + (e.response?.data?.message || e.message))
  } finally {
    running.value = ''
    setTimeout(() => { barWidth.value = 0 }, 600)
  }
}

// ===== 工具 =====
function decorateTree(nodes) {
  for (const n of nodes || []) {
    if (n.type === 'dir') { n.open = true; decorateTree(n.children) }
    else { n.transferred = false }
  }
}
function applyTransferResults(results) {
  const okPaths = new Set(results.filter(r => r.success).map(r => r.rel_path))
  const walk = (nodes) => {
    for (const n of nodes || []) {
      if (n.type === 'dir') walk(n.children)
      else if (okPaths.has(n.rel_path)) n.transferred = true
    }
  }
  walk(srcTree.value)
}
function buildDstTree(results, files) {
  const fileByPath = Object.fromEntries(files.map(f => [f.rel_path, f]))
  const tree = []
  const ensureDir = (segments) => {
    let list = tree
    let parent = null
    for (const seg of segments) {
      let node = list.find(x => x.type === 'dir' && x.name === seg)
      if (!node) { node = { id: 'd_' + seg + '_' + list.length, type: 'dir', name: seg, open: true, children: [] }; list.push(node) }
      parent = node
      list = node.children
    }
    return parent ? parent.children : tree
  }
  results.filter(r => r.success).forEach((r, idx) => {
    const f = fileByPath[r.rel_path] || {}
    const segments = (f.rel_dir || '').split('/').filter(Boolean)
    const bucket = ensureDir(segments)
    bucket.push({ id: 'f_' + idx, type: 'file', name: r.name, size: f.size || 0 })
  })
  dstTree.value = tree.length ? tree : null
}

function resetMetrics() { metrics.total = 0; metrics.ok = 0; metrics.no = 0; metrics.done = 0 }
function reset() {
  if (running.value) return
  src.value = null
  dst.value = null
  srcTree.value = null
  dstTree.value = null
  probeFiles.value = []
  barWidth.value = 0
  resetMetrics()
}

async function loadRoutes() {
  try {
    const resp = await axios.get('/api/cross-transfer/routes')
    if (resp.data && resp.data.success) {
      routes.value = resp.data.data || []
      if (routes.value.length && !activeId.value) activeId.value = routes.value[0].id
    }
  } catch (e) {
    notify('error', '获取线路失败: ' + (e.response?.data?.message || e.message))
  }
}
async function loadAccounts() {
  try {
    const resp = await axios.get('/api/admin/accounts')
    if (resp.data && resp.data.success) accounts.value = resp.data.data || []
  } catch (e) {
    notify('error', '获取账号失败: ' + (e.response?.data?.message || e.message))
  }
}

onMounted(() => { loadRoutes(); loadAccounts() })
</script>

<style scoped>
.cross-transfer {
  color: var(--text-main);
  --fc-track: #e2e8f0;
  --fc-dir-bg: var(--card-bg);
  --fc-dir-border: var(--border-color);
  --fc-pill-bg: rgba(76,116,223,.1);
  --fc-pill-fg: #2952cc;
  --fc-pill-md5-bg: rgba(124,58,237,.1);
  --fc-pill-md5-fg: #6d28d9;
}

/* 卡片：双行布局，尺寸介于 demo(大) 与 6列单行(小) 之间 */
.flow-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(168px, 1fr));
  gap: 10px;
}
.flow-card {
  position: relative; border-radius: 14px; background: var(--card-bg); cursor: pointer; user-select: none; overflow: hidden;
  border: 1px solid var(--border-color); box-shadow: 0 6px 18px rgba(15,23,42,.05); outline: 2px solid transparent;
  transition: box-shadow .18s ease, outline-color .18s ease, transform .18s ease;
}
.flow-card:hover { transform: translateY(-1px); box-shadow: 0 10px 26px rgba(15,23,42,.1); }
.flow-card.active { outline-color: var(--primary-color); box-shadow: 0 10px 28px rgba(76,116,223,.18); }
.flow-card.disabled { opacity: .55; cursor: not-allowed; transform: none; }
.fc-body { padding: 10px 12px; display: flex; flex-direction: column; gap: 7px; }
.fc-logos { display: flex; align-items: center; }
.fc-logo { width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; flex: 0 0 auto; }
.fc-logo img { width: 36px; height: 36px; object-fit: contain; border-radius: 9px; }
.fc-logo.placeholder { width: 36px; height: 36px; border-radius: 9px; background: var(--app-bg); color: var(--text-secondary); font-size: 14px; display: flex; align-items: center; justify-content: center; }
.fc-conn { flex: 1; height: 2px; margin: 0 8px; background: var(--fc-track); position: relative; }
.fc-dir {
  position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%);
  width: 22px; height: 22px; border-radius: 999px;
  background: var(--fc-dir-bg); border: 1px solid var(--fc-dir-border); color: var(--primary-color);
  font-size: 10px; display: flex; align-items: center; justify-content: center;
  box-shadow: 0 1px 4px rgba(15,23,42,.08);
}
.fc-dir.both { color: #7c3aed; border-color: #ddd6fe; }
.fc-dir.plain { color: var(--text-secondary); }
.fc-meta { display: flex; align-items: center; justify-content: center; gap: 6px; min-height: 22px; }
.fc-pill {
  font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 999px;
  display: inline-flex; align-items: center; gap: 5px; white-space: nowrap;
  background: var(--fc-pill-bg); color: var(--fc-pill-fg);
}
.fc-pill i { font-size: 10px; flex-shrink: 0; }
.fc-pill.md5 { background: var(--fc-pill-md5-bg); color: var(--fc-pill-md5-fg); }
.fc-pill.muted { background: var(--app-bg); color: var(--text-secondary); }
.fc-soon { font-size: 10px; color: var(--text-secondary); background: var(--app-bg); padding: 2px 8px; border-radius: 999px; }
.fc-flag { position: absolute; top: 8px; right: 8px; font-size: 10px; font-weight: 700; letter-spacing: .3px; padding: 2px 7px; border-radius: 999px; background: rgba(124,58,237,.12); color: #7c3aed; }

/* logo 徽标 */
.logo-chip { display: inline-flex; align-items: center; justify-content: center; flex: 0 0 auto; }
.logo-chip img { object-fit: contain; border-radius: 7px; }
.logo-chip.s30 { width: 30px; height: 30px; } .logo-chip.s30 img { width: 30px; height: 30px; }

/* 两栏 */
.transfer-row { display: grid; grid-template-columns: 1fr 52px 1fr; gap: 12px; margin-top: 10px; align-items: stretch; }
.panel { background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 16px; min-width: 0; box-shadow: 0 6px 18px rgba(15,23,42,.05); overflow: hidden; display: flex; flex-direction: column; }
.panel .panel-head { border-top: 3px solid var(--primary-color); }
.panel.dst .panel-head { border-top-color: #ff8c42; }
.panel-head { padding: 13px 16px; border-bottom: 1px solid var(--border-color); display: flex; align-items: center; gap: 10px; }
.panel-title { font-weight: 700; }
.panel-title small { display: block; font-weight: 500; font-size: 12px; color: var(--text-secondary); }
.panel-role { margin-left: auto; font-size: 11px; font-weight: 700; padding: 3px 9px; border-radius: 999px; }
.panel.src .panel-role { background: rgba(76,116,223,.12); color: #2952cc; }
.panel.dst .panel-role { background: rgba(255,140,66,.16); color: #c2410c; }
.panel-pick { padding: 12px 16px; border-bottom: 1px solid var(--border-color); }
.combo { width: 100%; border: none; border-radius: 10px; padding: 11px 14px; background: var(--app-bg); color: var(--text-main); font-size: 14px; cursor: pointer; display: flex; align-items: center; gap: 10px; text-align: left; transition: background .15s; }
.combo:hover { background: rgba(127,127,127,.12); }
.combo .c-ic { color: var(--primary-color); flex: 0 0 auto; }
.combo .c-text { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.combo .c-text.placeholder { color: var(--text-secondary); }
.combo .c-caret { color: var(--text-secondary); flex: 0 0 auto; }
.tree { padding: 6px; height: 300px; overflow: auto; }
.tree-empty { color: var(--text-secondary); padding: 28px 12px; text-align: center; }

.arrow-col { display: flex; align-items: center; justify-content: center; flex-direction: column; }
.arrow-orb { width: 40px; height: 40px; border-radius: 999px; color: #fff; font-size: 15px; border: none; background: linear-gradient(135deg, var(--primary-color), var(--primary-color-end)); display: flex; align-items: center; justify-content: center; box-shadow: 0 8px 20px rgba(76,116,223,.3); transition: transform .2s ease, box-shadow .2s ease; }
.arrow-orb.swap { cursor: pointer; background: linear-gradient(135deg, #7c3aed, #4c74df); }
.arrow-orb.swap:hover { transform: rotate(180deg); box-shadow: 0 10px 24px rgba(124,58,237,.4); }
.arrow-orb.locked { cursor: default; }
.swap-hint { margin-top: 8px; font-size: 11px; color: #7c3aed; white-space: nowrap; }

/* 操作条 */
.footer { margin-top: 10px; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 16px; box-shadow: 0 6px 18px rgba(15,23,42,.05); padding: 10px 16px; display: flex; align-items: center; justify-content: space-between; gap: 14px; flex-wrap: wrap; }
.metrics { display: flex; align-items: center; gap: 18px; flex-wrap: wrap; font-size: 13px; color: var(--text-secondary); }
.metric .n { font-size: 20px; font-weight: 700; color: var(--text-main); }
.metric .n.ok { color: #16a34a; }
.metric .n.no { color: #94a3b8; }
.metric .l { font-size: 12px; }
.progress { width: 220px; height: 8px; border-radius: 999px; background: var(--app-bg); border: 1px solid var(--border-color); overflow: hidden; }
.progress > div { height: 100%; width: 0; border-radius: 999px; background: linear-gradient(90deg, #16a34a, var(--primary-color)); transition: width .18s ease; }
.actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.seg { display: flex; align-items: center; gap: 7px; font-size: 13px; color: var(--text-secondary); white-space: nowrap; }
.seg-label { white-space: nowrap; }
.seg select { height: 38px; border: 1px solid var(--border-color); border-radius: 10px; padding: 0 10px; font-size: 13px; background: var(--card-bg); color: var(--text-main); }

/* 按钮（独立命名，避免与全局 .btn 冲突）*/
.ct-btn { display: inline-flex; align-items: center; gap: 8px; padding: 10px 16px; border: 1px solid var(--border-color); border-radius: 10px; background: var(--card-bg); color: var(--text-regular); font-size: 14px; font-weight: 600; cursor: pointer; transition: filter .2s, opacity .2s; white-space: nowrap; }
.ct-btn:disabled { opacity: .5; cursor: not-allowed; }
.ct-btn-primary { background: linear-gradient(135deg, var(--primary-color), var(--primary-color-end)); border-color: transparent; color: #fff; box-shadow: 0 2px 6px rgba(76,116,223,.22); }
.ct-btn-primary:not(:disabled):hover { filter: brightness(1.06); }
.ct-btn-go { background: linear-gradient(135deg, #16a34a, #22c55e); border-color: transparent; color: #fff; box-shadow: 0 2px 6px rgba(22,163,74,.22); }
.ct-btn-go:not(:disabled):hover { filter: brightness(1.06); }
.ct-btn-danger { background: rgba(239,68,68,.1); border-color: rgba(239,68,68,.3); color: #dc2626; }
.ct-btn-danger:not(:disabled):hover { background: rgba(239,68,68,.18); }

:global(:root[data-theme="dark"]) .cross-transfer {
  --fc-track: #3d4f6f;
  --fc-dir-border: #4a5568;
  --fc-pill-bg: rgba(76,116,223,.18);
  --fc-pill-fg: #93c5fd;
  --fc-pill-md5-bg: rgba(124,58,237,.2);
  --fc-pill-md5-fg: #c4b5fd;
}

@media (min-width: 1400px) {
  .flow-grid { grid-template-columns: repeat(6, minmax(0, 1fr)); }
}
@media (max-width: 720px) {
  .flow-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 1080px) {
  .transfer-row { grid-template-columns: 1fr; }
  .arrow-col { transform: rotate(90deg); margin: 2px 0; }
  .swap-hint { display: none; }
  .progress { width: 100%; }
}
</style>
