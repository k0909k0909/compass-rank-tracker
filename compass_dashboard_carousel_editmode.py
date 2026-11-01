from pathlib import Path
from datetime import datetime
import re

ROOT = Path.cwd()
APP = ROOT / "src" / "App.tsx"
CSS = ROOT / "src" / "style-improvements.css"
MARKER = "/* COMPASS DASHBOARD CAROUSEL + IN-PLACE EDIT v2 */"

if not APP.is_file() or not CSS.is_file():
    raise SystemExit("安全確認：src/App.tsx または src/style-improvements.css が見つかりません。リポジトリ直下で実行してください。")

app_original = APP.read_text(encoding="utf-8")
css_original = CSS.read_text(encoding="utf-8")
if MARKER in css_original or MARKER in app_original:
    raise SystemExit("安全確認：この改修パッチは既に適用されているようです。重ねて実行しません。")

app = app_original
css = css_original

def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"安全確認：{label} の一致数が1ではありません（{count}）。ファイルは変更していません。")
    return source.replace(old, new, 1)

# 1) アイコン追加
old = "import { Activity, BarChart3, CalendarDays, ChevronDown, ChevronUp, Download, FileUp, Gauge, GripVertical, History, LayoutDashboard, Lock, Menu, Minus, Pencil, Plus, Search, Settings, Shield, Star, Sun, Moon, Swords, Trash2, Trophy, Unlock, X } from 'lucide-react'"
new = "import { Activity, BarChart3, CalendarDays, Check, ChevronDown, ChevronLeft, ChevronRight, ChevronUp, Download, FileUp, Gauge, GripVertical, History, LayoutDashboard, Lock, Menu, Minus, Pencil, Plus, Search, Settings, Shield, Star, Sun, Moon, Swords, Trash2, Trophy, Unlock, X } from 'lucide-react'"
app = replace_once(app, old, new, "lucide-react import")

# 2) 初期ヒーロー枠を実装順の先頭に設定
app = replace_once(app, "  { id: 'hero-info', type: 'heroInfo', heroName: '' },", "  { id: 'hero-info', type: 'heroInfo', heroName: '十文字アタリ' },", "初期ヒーロー情報")
app = replace_once(
    app,
    "      heroName: typeof item.heroName === 'string' ? item.heroName.slice(0, 100) : '',",
    "      heroName: type === 'heroInfo' ? (typeof item.heroName === 'string' && item.heroName.trim() ? item.heroName.slice(0, 100) : (heroImplementationOrder[0] ?? '')) : (typeof item.heroName === 'string' ? item.heroName.slice(0, 100) : ''),",
    "空欄ヒーローの初期選択"
)

# 3) 編集状態とホーム上ドラッグ状態
app = replace_once(
    app,
    "  const [dashboardEditorOpen, setDashboardEditorOpen] = useState(false)\n  const [dashboardEditorTab, setDashboardEditorTab] = useState<'home' | 'menu'>('home')\n  const editorSortDragRef = useRef<{ scope: 'home' | 'menu'; id: string; pointerId: number; startX: number; startY: number; moved: boolean } | null>(null)\n  const [editorDraggingKey, setEditorDraggingKey] = useState('')",
    "  const [dashboardEditorOpen, setDashboardEditorOpen] = useState(false)\n  const [dashboardEditorTab, setDashboardEditorTab] = useState<'home' | 'menu'>('menu')\n  const [dashboardEditMode, setDashboardEditMode] = useState(false)\n  const [dashboardAddMenuOpen, setDashboardAddMenuOpen] = useState(false)\n  const dashboardDragRef = useRef<{ id: string; pointerId: number; startX: number; startY: number; moved: boolean } | null>(null)\n  const [dashboardDraggingId, setDashboardDraggingId] = useState('')\n  const [dashboardDropTargetId, setDashboardDropTargetId] = useState('')\n  const editorSortDragRef = useRef<{ scope: 'home' | 'menu'; id: string; pointerId: number; startX: number; startY: number; moved: boolean } | null>(null)\n  const [editorDraggingKey, setEditorDraggingKey] = useState('')",
    "ホーム編集state"
)

# 4) 画面遷移時はホーム編集モードを閉じる
app = replace_once(
    app,
    "  useEffect(() => { storeRef.current = store }, [store])\n  useEffect(() => { localStorage.setItem(storageKey, JSON.stringify(store)); cloud?.saveCloudStore(store) }, [store])",
    "  useEffect(() => { storeRef.current = store }, [store])\n  useEffect(() => { localStorage.setItem(storageKey, JSON.stringify(store)); cloud?.saveCloudStore(store) }, [store])\n  useEffect(() => {\n    if (page !== 'dashboard') { setDashboardEditMode(false); setDashboardAddMenuOpen(false) }\n  }, [page])",
    "画面遷移時の編集終了"
)

# 5) リピート項目の追加数を最大3件に制限
old = """  function addDashboardWidget(type: DashboardWidgetType) {
    setStore(current => {
      const items = [...(current.dashboardWidgets ?? defaultDashboardWidgets)]
      if (!repeatableDashboardWidgetTypes.includes(type) && items.some(widget => widget.type === type)) return current
      const id = `${type}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`
      const widget: DashboardWidget = { id, type }
      if (type === 'winRate') widget.period = 'today'
      if (type === 'popularHero') widget.period = 'all'
      if (type === 'heroInfo') widget.heroName = ''
      items.push(widget)
      return { ...current, dashboardWidgets: items }
    })
  }"""
new = """  function addDashboardWidget(type: DashboardWidgetType) {
    const currentItems = store.dashboardWidgets ?? defaultDashboardWidgets
    const repeatedCount = currentItems.filter(widget => widget.type === type).length
    if (repeatableDashboardWidgetTypes.includes(type) && repeatedCount >= 3) {
      notify(type === 'heroInfo' ? '指定ヒーロー情報は最大3体まで登録できます。' : '自由記載は最大3件まで登録できます。')
      return
    }
    if (!repeatableDashboardWidgetTypes.includes(type) && currentItems.some(widget => widget.type === type)) return
    setStore(current => {
      const items = [...(current.dashboardWidgets ?? defaultDashboardWidgets)]
      if (repeatableDashboardWidgetTypes.includes(type) && items.filter(widget => widget.type === type).length >= 3) return current
      if (!repeatableDashboardWidgetTypes.includes(type) && items.some(widget => widget.type === type)) return current
      const id = `${type}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`
      const widget: DashboardWidget = { id, type }
      if (type === 'winRate') widget.period = 'today'
      if (type === 'popularHero') widget.period = 'all'
      if (type === 'heroInfo') widget.heroName = heroImplementationOrder[0] ?? ''
      if (type === 'note') { widget.showHeading = false; widget.heading = ''; widget.body = '' }
      items.push(widget)
      return { ...current, dashboardWidgets: items }
    })
  }"""
app = replace_once(app, old, new, "addDashboardWidget")

# 6) ヒーロー情報・自由記載をグループとして並べ替える
old = """  function reorderDashboardWidgets(sourceId: string, targetId: string, before = true) {
    setStore(current => {
      const items = [...(current.dashboardWidgets ?? [])]
      const sourceIndex = items.findIndex(item => item.id === sourceId)
      if (sourceIndex < 0 || sourceId === targetId) return current
      const [moved] = items.splice(sourceIndex, 1)
      const targetIndex = items.findIndex(item => item.id === targetId)
      if (targetIndex < 0) return current
      items.splice(targetIndex + (before ? 0 : 1), 0, moved)
      return { ...current, dashboardWidgets: items }
    })
  }"""
new = """  function reorderDashboardWidgets(sourceId: string, targetId: string, before = true) {
    setStore(current => {
      const items = [...(current.dashboardWidgets ?? [])]
      const groups: DashboardWidget[][] = []
      const groupMap = new Map<string, DashboardWidget[]>()
      for (const item of items) {
        const key = repeatableDashboardWidgetTypes.includes(item.type) ? `type:${item.type}` : `id:${item.id}`
        let group = groupMap.get(key)
        if (!group) { group = []; groupMap.set(key, group); groups.push(group) }
        group.push(item)
      }
      const sourceIndex = groups.findIndex(group => group.some(item => item.id === sourceId))
      const targetIndex = groups.findIndex(group => group.some(item => item.id === targetId))
      if (sourceIndex < 0 || targetIndex < 0 || sourceIndex === targetIndex) return current
      const [moved] = groups.splice(sourceIndex, 1)
      const adjustedTargetIndex = groups.findIndex(group => group.some(item => item.id === targetId))
      if (adjustedTargetIndex < 0) return current
      groups.splice(adjustedTargetIndex + (before ? 0 : 1), 0, moved)
      return { ...current, dashboardWidgets: groups.flat() }
    })
  }"""
app = replace_once(app, old, new, "reorderDashboardWidgets")

# 7) ホーム上でカードを直接ドラッグするイベント
anchor = "  function moveDashboardWidget(id: string, offset: number) {"
handlers = """  function handleDashboardDragStart(id: string, event: React.PointerEvent<HTMLButtonElement>) {
    if (event.pointerType === 'mouse' && event.button !== 0) return
    event.preventDefault()
    dashboardDragRef.current = { id, pointerId: event.pointerId, startX: event.clientX, startY: event.clientY, moved: false }
    event.currentTarget.setPointerCapture(event.pointerId)
  }
  function handleDashboardDragMove(event: React.PointerEvent<HTMLButtonElement>) {
    const drag = dashboardDragRef.current
    if (!drag || drag.pointerId !== event.pointerId) return
    if (!drag.moved && Math.hypot(event.clientX - drag.startX, event.clientY - drag.startY) > 8) {
      drag.moved = true
      setDashboardDraggingId(drag.id)
    }
    if (drag.moved) {
      const target = document.elementFromPoint(event.clientX, event.clientY)?.closest<HTMLElement>('[data-dashboard-widget-id]')
      const targetId = target?.dataset.dashboardWidgetId ?? ''
      setDashboardDropTargetId(targetId !== drag.id ? targetId : '')
    }
  }
  function handleDashboardDragEnd(event: React.PointerEvent<HTMLButtonElement>) {
    const drag = dashboardDragRef.current
    if (!drag || drag.pointerId !== event.pointerId) return
    if (drag.moved) {
      const target = document.elementFromPoint(event.clientX, event.clientY)?.closest<HTMLElement>('[data-dashboard-widget-id]')
      const targetId = target?.dataset.dashboardWidgetId ?? ''
      if (target && targetId && targetId !== drag.id) {
        const rect = target.getBoundingClientRect()
        const centerY = rect.top + rect.height / 2
        const centerX = rect.left + rect.width / 2
        const before = Math.abs(event.clientY - centerY) > rect.height * 0.22
          ? event.clientY < centerY
          : event.clientX < centerX
        reorderDashboardWidgets(drag.id, targetId, before)
      }
    }
    dashboardDragRef.current = null
    setDashboardDraggingId('')
    setDashboardDropTargetId('')
  }
  function handleDashboardDragCancel() {
    dashboardDragRef.current = null
    setDashboardDraggingId('')
    setDashboardDropTargetId('')
  }

"""
app = replace_once(app, anchor, handlers + anchor, "ホームドラッグハンドラー挿入位置")

# 8) widget catalogの説明とグループ・追加可能リスト
old = """    { type: 'heroInfo', label: '指定ヒーローの情報', description: '勝率・使用数・称号までの進捗。複数追加可能', size: '横2' },
    { type: 'note', label: '自由記載', description: '目標やメモ。複数追加可能', size: '横2' },
    { type: 'monthly', label: '月別成績', description: '今月から直近6か月をスライド表示', size: '横1' },
    { type: 'recentMatches', label: '直近の試合履歴', description: '最新5試合。横2・縦2', size: '横2・縦2' }
  ]

  return <div className=\"app-shell\">"""
new = """    { type: 'heroInfo', label: '指定ヒーローの情報', description: '最大3体を横スライド。ホーム上で検索・変更可能', size: '横2' },
    { type: 'note', label: '自由記載', description: '最大3件を横スライド。ホーム上で編集可能', size: '横2' },
    { type: 'monthly', label: '月別成績', description: '今月から直近6か月をスライド表示', size: '横1' },
    { type: 'recentMatches', label: '直近の試合履歴', description: '最新5試合。横2・縦2', size: '横2・縦2' }
  ]
  const dashboardWidgetGroups = (() => {
    const groups: DashboardWidget[][] = []
    const repeated = new Map<DashboardWidgetType, DashboardWidget[]>()
    for (const item of (store.dashboardWidgets ?? defaultDashboardWidgets)) {
      if (repeatableDashboardWidgetTypes.includes(item.type)) {
        const group = repeated.get(item.type)
        if (group) group.push(item)
        else { const next = [item]; repeated.set(item.type, next); groups.push(next) }
      } else groups.push([item])
    }
    return groups
  })()
  const availableWidgetCatalog = widgetCatalog.filter(item => {
    const count = (store.dashboardWidgets ?? []).filter(widget => widget.type === item.type).length
    return repeatableDashboardWidgetTypes.includes(item.type) ? count < 3 : count === 0
  })

  return <div className=\"app-shell\">"""
app = replace_once(app, old, new, "widgetCatalog・groups")

# 9) 上部ボタンをホーム画面編集モードの切り替えに変更
old = "          {page === 'dashboard' && <button type=\"button\" className=\"secondary-button dashboard-edit-trigger\" onClick={() => { setDashboardEditorTab('home'); setDashboardEditorOpen(true) }}><Pencil size={15}/> ホーム・メニューの編集</button>}"
new = "          {page === 'dashboard' && <button type=\"button\" className=\"secondary-button dashboard-edit-trigger\" onClick={() => { if (dashboardEditMode) { setDashboardEditMode(false); setDashboardAddMenuOpen(false) } else setDashboardEditMode(true) }}><Pencil size={15}/> {dashboardEditMode ? '編集を終了' : 'ホーム・メニューの編集'}</button>}"
app = replace_once(app, old, new, "ホーム編集ボタン")

# 10) ホーム画面のカードをその場でドラッグできるグリッドに変更
old = """      {page === 'dashboard' && <section className=\"page-stack\">
        <div className=\"dashboard-widget-grid\">
          {(store.dashboardWidgets ?? defaultDashboardWidgets).map(widget => <DashboardWidgetCard
            key={widget.id} widget={widget} store={store} currentRankState={currentRankState}
            sortedMatches={sortedMatches} monthlyStats={monthlyStats}
            onUpdate={updateDashboardWidget} onOpenHistory={() => setPage('history')}
          />)}
          {(store.dashboardWidgets ?? []).length === 0 && <div className=\"dashboard-empty-layout\"><LayoutDashboard size={28}/><strong>ホーム画面が空です</strong><span>「ホーム・メニューの編集」から表示したい項目を追加できます。</span></div>}
        </div>
        <div className=\"hint-row\"><Shield size={17}/><span>{cloud ? 'ログイン中のアカウントにホーム画面と試合記録を同期します。別の端末でも同じ配置を利用できます。' : '端末を変える前にバックアップを保存してください。'}</span></div>
      </section>}"""
new = """      {page === 'dashboard' && <section className={`page-stack ${dashboardEditMode ? 'dashboard-is-editing' : ''}`}>
        {dashboardEditMode && <div className=\"dashboard-edit-toolbar\">
          <div className=\"dashboard-edit-toolbar-copy\"><strong>ホーム画面を編集中</strong><span>各カード上部の「移動」をつかんで、置きたい場所へドラッグしてください。</span></div>
          <div className=\"dashboard-edit-toolbar-actions\">
            <button type=\"button\" className=\"secondary-button\" onClick={() => setDashboardAddMenuOpen(current => !current)}><Plus size={15}/> 項目を追加</button>
            <button type=\"button\" className=\"secondary-button\" onClick={() => { setDashboardEditorTab('menu'); setDashboardEditorOpen(true) }}><Menu size={15}/> メニュー欄を編集</button>
            <button type=\"button\" className=\"primary-button\" onClick={() => { setDashboardEditMode(false); setDashboardAddMenuOpen(false) }}><Check size={15}/> 完了</button>
          </div>
          {dashboardAddMenuOpen && <div className=\"dashboard-add-panel\">
            <div className=\"dashboard-add-panel-heading\"><strong>ホームに追加する項目</strong><span>ヒーロー情報・自由記載は各3件まで</span></div>
            <div className=\"dashboard-add-panel-grid\">{availableWidgetCatalog.map(item => <button type=\"button\" className=\"dashboard-add-option\" key={item.type} onClick={() => addDashboardWidget(item.type)}><span><strong>{item.label}</strong><small>{item.description}</small></span><Plus size={17}/></button>)}
              {availableWidgetCatalog.length === 0 && <p className=\"dashboard-add-panel-empty\">追加できる項目はありません。ヒーロー情報と自由記載は最大3件まで登録できます。</p>}
            </div>
          </div>}
        </div>}
        <div className=\"dashboard-widget-grid\">
          {dashboardWidgetGroups.map(group => {
            const widget = group[0]
            const repeatableGroup = repeatableDashboardWidgetTypes.includes(widget.type)
            const key = repeatableGroup ? `widget-group-${widget.type}` : widget.id
            const wide = widget.type === 'heroInfo' || widget.type === 'note' || widget.type === 'recentMatches'
            const tall = widget.type === 'recentMatches'
            return <div key={key} data-dashboard-widget-id={widget.id} className={`dashboard-widget-sortable ${wide ? 'is-wide' : ''} ${tall ? 'is-tall' : ''} ${dashboardDraggingId === widget.id ? 'is-dragging' : ''} ${dashboardDropTargetId === widget.id ? 'is-drop-target' : ''}`}>
              <DashboardWidgetCard widget={widget} carouselWidgets={group} store={store} currentRankState={currentRankState}
                sortedMatches={sortedMatches} monthlyStats={monthlyStats} editMode={dashboardEditMode}
                onUpdate={updateDashboardWidget} onRemove={removeDashboardWidget} onOpenHistory={() => setPage('history')}
                onDragStart={handleDashboardDragStart} onDragMove={handleDashboardDragMove} onDragEnd={handleDashboardDragEnd} onDragCancel={handleDashboardDragCancel}
              />
            </div>
          })}
          {dashboardWidgetGroups.length === 0 && <div className=\"dashboard-empty-layout\"><LayoutDashboard size={28}/><strong>ホーム画面が空です</strong><span>編集モードの「項目を追加」から表示したい項目を追加できます。</span></div>}
        </div>
        <div className=\"hint-row\"><Shield size={17}/><span>{cloud ? 'ログイン中のアカウントにホーム画面と試合記録を同期します。別の端末でも同じ配置を利用できます。' : '端末を変える前にバックアップを保存してください。'}</span></div>
      </section>}"""
app = replace_once(app, old, new, "ホーム画面グリッド")

# 11) メニュー編集モーダルをメニュー専用に
app = replace_once(app, "<h2 id=\"dashboard-editor-title\">ホーム・メニューの編集</h2><p>配置や表示項目は自動で保存されます。</p>", "<h2 id=\"dashboard-editor-title\">メニュー欄の編集</h2><p>サイドメニューの順番を変更できます。変更は自動で保存されます。</p>", "メニュー編集モーダル見出し")
old_tabs = """          <div className=\"dashboard-editor-tabs\" role=\"tablist\" aria-label=\"編集する場所\">
            <button type=\"button\" role=\"tab\" aria-selected={dashboardEditorTab === 'home'} className={dashboardEditorTab === 'home' ? 'active' : ''} onClick={() => setDashboardEditorTab('home')}><LayoutDashboard size={16}/> ホーム画面</button>
            <button type=\"button\" role=\"tab\" aria-selected={dashboardEditorTab === 'menu'} className={dashboardEditorTab === 'menu' ? 'active' : ''} onClick={() => setDashboardEditorTab('menu')}><Menu size={16}/> メニュー欄</button>
          </div>"""
app = replace_once(app, old_tabs, "          <div className=\"dashboard-editor-menu-label\"><Menu size={16}/><span>サイドメニュー</span></div>", "メニュー編集タブ")

# 12) DashboardWidgetCardをカルーセル・ホーム上編集対応版に差し替え
start_marker = "type DashboardWidgetCardProps = {"
end_marker = "\nfunction NavItem({ active, icon, label, onClick }"
start = app.find(start_marker)
end = app.find(end_marker, start + 1)
if start < 0 or end < 0:
    raise SystemExit("安全確認：DashboardWidgetCard の開始・終了位置が見つかりません。ファイルは変更していません。")
component = r'''type DashboardWidgetCardProps = {
  widget: DashboardWidget
  carouselWidgets?: DashboardWidget[]
  store: Store
  currentRankState: RankState
  sortedMatches: Match[]
  monthlyStats: MonthlyStat[]
  editMode?: boolean
  onUpdate: (id: string, changes: Partial<DashboardWidget>) => void
  onRemove?: (id: string) => void
  onOpenHistory: () => void
  onDragStart?: (id: string, event: React.PointerEvent<HTMLButtonElement>) => void
  onDragMove?: (event: React.PointerEvent<HTMLButtonElement>) => void
  onDragEnd?: (event: React.PointerEvent<HTMLButtonElement>) => void
  onDragCancel?: () => void
}
function DashboardWidgetCard({ widget, carouselWidgets, store, currentRankState, sortedMatches, monthlyStats, editMode = false, onUpdate, onRemove, onOpenHistory, onDragStart, onDragMove, onDragEnd, onDragCancel }: DashboardWidgetCardProps) {
  const slides = carouselWidgets?.length ? carouselWidgets : [widget]
  const [slideIndex, setSlideIndex] = useState(0)
  const [noteEditing, setNoteEditing] = useState(false)
  const swipeStartX = useRef<number | null>(null)
  useEffect(() => { setSlideIndex(index => Math.min(index, Math.max(0, slides.length - 1))) }, [slides.length])
  const currentSlide = slides[slideIndex] ?? widget
  useEffect(() => { setNoteEditing(false) }, [currentSlide.id])
  const wide = widget.type === 'heroInfo' || widget.type === 'note' || widget.type === 'recentMatches'
  const tall = widget.type === 'recentMatches'
  const period = widget.period ?? (widget.type === 'popularHero' ? 'all' : 'today')
  const periodMatches = period === 'today'
    ? sortedMatches.filter(match => match.playedAt.slice(0, 10) === today())
    : period === 'month'
      ? sortedMatches.filter(match => match.playedAt.slice(0, 7) === currentMonthKey())
      : sortedMatches
  const importedTotals = period === 'all'
    ? Object.values(store.heroBaseStats ?? {}).reduce((totals, stat) => ({ battles: totals.battles + stat.battles, wins: totals.wins + stat.wins }), { battles: 0, wins: 0 })
    : { battles: 0, wins: 0 }
  const periodWins = periodMatches.filter(match => match.result === 'win').length + importedTotals.wins
  const periodLosses = periodMatches.filter(match => match.result === 'loss').length + Math.max(0, importedTotals.battles - importedTotals.wins)
  const periodDraws = periodMatches.filter(match => match.result === 'draw').length
  const periodBattleCount = periodMatches.length + importedTotals.battles
  const winRate = percent(periodWins, periodWins + periodLosses)
  const resultText = `${periodWins}勝 ${periodLosses}敗${periodDraws ? ` ${periodDraws}分` : ''}`
  const allBaseUsage = Object.values(store.heroBaseStats ?? {}).reduce((sum, stat) => sum + stat.battles, 0)
  const totalHeroUsage = periodMatches.length + (period === 'all' ? allBaseUsage : 0)
  const popularHeroRows = store.heroes.map(item => {
    const recent = period === 'today' ? sortedMatches.filter(match => match.heroName === item.name && match.playedAt.slice(0, 10) === today()) : period === 'month' ? sortedMatches.filter(match => match.heroName === item.name && match.playedAt.slice(0, 7) === currentMonthKey()) : sortedMatches.filter(match => match.heroName === item.name)
    const count = recent.length + (period === 'all' ? (store.heroBaseStats?.[item.name]?.battles ?? 0) : 0)
    return { name: item.name, count, rate: totalHeroUsage > 0 ? Math.round(count / totalHeroUsage * 100) : 0 }
  }).filter(item => item.count > 0).sort((a, b) => b.count - a.count || a.name.localeCompare(b.name, 'ja')).slice(0, 4)
  const orderedHeroOptions = [...store.heroes].sort((a, b) =>
    (heroOrderIndex.get(a.name) ?? Number.MAX_SAFE_INTEGER) - (heroOrderIndex.get(b.name) ?? Number.MAX_SAFE_INTEGER)
    || a.name.localeCompare(b.name, 'ja')
  )
  const hero = widget.type === 'heroInfo' ? store.heroes.find(item => item.name === currentSlide.heroName) : undefined
  const heroBase = hero ? (store.heroBaseStats?.[hero.name] ?? { battles: 0, wins: 0 }) : { battles: 0, wins: 0 }
  const heroMatches = hero ? store.matches.filter(match => match.heroName === hero.name) : []
  const heroBattles = heroBase.battles + heroMatches.length
  const heroWins = heroBase.wins + heroMatches.filter(match => match.result === 'win').length
  const heroRate = percent(heroWins, heroBattles)
  const nextMilestone = heroBattles < 1000 ? 1000 : heroBattles < 5000 ? 5000 : heroBattles < 10000 ? 10000 : null
  const remaining = nextMilestone === null ? 0 : Math.max(0, nextMilestone - heroBattles)
  const milestoneStart = nextMilestone === 1000 ? 0 : nextMilestone === 5000 ? 1000 : 5000
  const progress = nextMilestone === null ? 100 : Math.max(0, Math.min(100, (heroBattles - milestoneStart) / (nextMilestone - milestoneStart) * 100))
  const canCarousel = (widget.type === 'heroInfo' || widget.type === 'note') && slides.length > 1
  function changeSlide(offset: number) {
    if (slides.length <= 1) return
    setSlideIndex(index => (index + offset + slides.length) % slides.length)
  }
  function onCardTouchStart(event: React.TouchEvent<HTMLElement>) {
    const target = event.target as HTMLElement
    if (target.closest('button,input,select,textarea,a')) { swipeStartX.current = null; return }
    swipeStartX.current = event.touches[0]?.clientX ?? null
  }
  function onCardTouchEnd(event: React.TouchEvent<HTMLElement>) {
    const startX = swipeStartX.current
    swipeStartX.current = null
    if (startX === null || !canCarousel) return
    const endX = event.changedTouches[0]?.clientX ?? startX
    const delta = endX - startX
    if (delta < -38) changeSlide(1)
    else if (delta > 38) changeSlide(-1)
  }

  return <article className={`dashboard-widget-card ${wide ? 'is-wide' : ''} ${tall ? 'is-tall' : ''} widget-${widget.type} ${editMode ? 'is-editing' : ''}`} onTouchStart={onCardTouchStart} onTouchEnd={onCardTouchEnd}>
    {editMode && <div className="dashboard-widget-manage-bar">
      <button type="button" className="dashboard-widget-drag-handle" aria-label="この項目をつかんでホーム内を移動" onPointerDown={event => onDragStart?.(widget.id, event)} onPointerMove={onDragMove} onPointerUp={onDragEnd} onPointerCancel={onDragCancel}><GripVertical size={15}/> <span>移動</span></button>
      <span className="dashboard-widget-edit-label">ホーム配置を編集中</span>
      <button type="button" className="icon-button dashboard-widget-remove" aria-label="この項目を削除" title="ホームから削除" onClick={() => onRemove?.(currentSlide.id)}><Trash2 size={15}/></button>
    </div>}
    {widget.type === 'rank' && <>
      <div className="dashboard-widget-heading"><div><span className="widget-kicker">RANK STATUS</span><h3>現在のランク</h3></div><span className="dashboard-widget-icon"><BarChart3 size={18}/></span></div>
      <strong className="dashboard-widget-primary-value">{`S${currentRankState.tier} · ${currentRankState.points}pt`}</strong>
      <p className="dashboard-widget-subline">{store.activeSeason ?? 'シーズン未設定'}</p>
    </>}
    {widget.type === 'winRate' && <>
      <div className="dashboard-widget-heading"><div><span className="widget-kicker">BATTLE RECORD</span><h3>勝率</h3></div><span className="dashboard-widget-icon"><Trophy size={18}/></span></div>
      <div className="widget-period-tabs" aria-label="勝率の集計期間">{(['today', 'month', 'all'] as DashboardPeriod[]).map(value => <button type="button" key={value} className={period === value ? 'active' : ''} onClick={() => onUpdate(widget.id, { period: value })}>{value === 'today' ? '今日' : value === 'month' ? '今月' : '全体'}</button>)}</div>
      <strong className="dashboard-widget-primary-value">{winRate}</strong>
      <p className="dashboard-widget-subline">{periodBattleCount}試合 · {resultText}</p>
    </>}
    {widget.type === 'streak' && <>
      <div className="dashboard-widget-heading"><div><span className="widget-kicker">CURRENT STREAK</span><h3>連勝数</h3></div><span className="dashboard-widget-icon"><Activity size={18}/></span></div>
      {(() => {
        const first = sortedMatches[0]?.result
        let count = 0
        if (first === 'win' || first === 'loss') for (const match of sortedMatches) { if (match.result !== first) break; count++ }
        const current = first === 'win' ? `${count}連勝` : first === 'loss' ? `${count}連敗` : '—'
        let run = 0, highest = 0
        for (const match of [...sortedMatches].reverse()) { if (match.result === 'win') { run++; highest = Math.max(highest, run) } else run = 0 }
        return <><strong className="dashboard-widget-primary-value">{current}</strong><p className="dashboard-widget-subline">最高連勝：{highest}</p></>
      })()}
    </>}
    {widget.type === 'popularHero' && <>
      <div className="dashboard-widget-heading"><div><span className="widget-kicker">HERO USAGE</span><h3>使用率の高いヒーロー</h3></div><span className="dashboard-widget-icon"><Star size={18}/></span></div>
      <div className="widget-period-tabs" aria-label="ヒーロー使用数の集計期間">{(['today', 'month', 'all'] as DashboardPeriod[]).map(value => <button type="button" key={value} className={period === value ? 'active' : ''} onClick={() => onUpdate(widget.id, { period: value })}>{value === 'today' ? '今日' : value === 'month' ? '今月' : '全体'}</button>)}</div>
      <div className="popular-hero-list">
        {popularHeroRows.map((item, index) => <div className="popular-hero-row" key={item.name}><span className="popular-hero-rank">{index + 1}</span><strong>{item.name}</strong><span>{item.count.toLocaleString()}回 · {item.rate}%</span></div>)}
        {popularHeroRows.length === 0 && <p className="dashboard-widget-empty">この期間の使用記録はありません。</p>}
      </div>
    </>}
    {widget.type === 'heroInfo' && <>
      <div className="dashboard-widget-heading hero-info-heading"><div><span className="widget-kicker">HERO PROFILE</span><h3>指定ヒーローの情報</h3></div>{hero && <span className="hero-role-chip">{hero.role}</span>}</div>
      <div className="hero-info-selector-row"><label>ヒーローを検索・選択</label><SearchableHeroDropdown value={currentSlide.heroName ?? ''} heroes={orderedHeroOptions} onChange={name => onUpdate(currentSlide.id, { heroName: name })} placeholder="ヒーロー名で検索"/></div>
      {hero ? <>
        <div className="hero-info-selected-name">{hero.name}</div>
        <div className="hero-info-metrics"><div><span>勝率</span><strong>{heroRate}</strong></div><div><span>使用数</span><strong>{heroBattles.toLocaleString()}回</strong></div><div><span>勝ち数</span><strong>{heroWins.toLocaleString()}勝</strong></div></div>
        <div className="hero-title-progress"><div className="hero-title-progress-label"><span>{heroBattles >= 10000 ? `万戦${hero.name}使い 達成` : heroBattles >= 5000 ? `殿堂入り${hero.name}使い 達成` : heroBattles >= 1000 ? `${hero.name}使い 達成` : `${hero.name}使いまであと${remaining.toLocaleString()}戦`}</span><strong>{Math.floor(progress)}%</strong></div><div className="hero-title-progress-track"><span style={{ width: `${progress}%` }}/></div>
          {heroBattles >= 10000 ? <small>万戦称号を達成しています。</small> : heroBattles >= 5000 ? <small>万戦{hero.name}使いまであと{remaining.toLocaleString()}戦</small> : heroBattles >= 1000 ? <small>殿堂入りまであと{remaining.toLocaleString()}戦 · 万戦まであと{(10000 - heroBattles).toLocaleString()}戦</small> : <small>1,000回使用で「{hero.name}使い」を獲得</small>}
        </div>
      </> : <p className="dashboard-widget-empty">上の検索欄から表示するヒーローを選択してください。</p>}
      {canCarousel && <div className="widget-carousel-controls"><div className="widget-carousel-dots">{slides.map((item, index) => <button type="button" key={item.id} className={slideIndex === index ? 'active' : ''} aria-label={`${index + 1}体目を表示`} onClick={() => setSlideIndex(index)}/>)}</div><div className="widget-carousel-arrows"><button type="button" aria-label="前のヒーロー" onClick={() => changeSlide(-1)}><ChevronLeft size={16}/></button><span>{slideIndex + 1} / {slides.length}</span><button type="button" aria-label="次のヒーロー" onClick={() => changeSlide(1)}><ChevronRight size={16}/></button></div></div>}
    </>}
    {widget.type === 'note' && <>
      <div className="dashboard-widget-heading note-widget-header"><div><span className="widget-kicker">PERSONAL NOTE</span><h3>{currentSlide.showHeading && currentSlide.heading?.trim() ? currentSlide.heading : '自由記載'}</h3></div><button type="button" className="icon-button note-edit-trigger" aria-label="自由記載を編集" title="内容を編集" onClick={() => setNoteEditing(current => !current)}><Pencil size={15}/></button></div>
      {noteEditing ? <div className="note-home-editor">
        <label className="editor-heading-toggle"><input type="checkbox" checked={Boolean(currentSlide.showHeading)} onChange={event => onUpdate(currentSlide.id, { showHeading: event.target.checked })}/> 見出しを追加</label>
        {currentSlide.showHeading && <input value={currentSlide.heading ?? ''} maxLength={80} placeholder="例：今月の目標" onChange={event => onUpdate(currentSlide.id, { heading: event.target.value })}/>}
        <textarea rows={4} maxLength={3000} value={currentSlide.body ?? ''} placeholder="自由に記載できます。例：11月中にリリカ使いを達成する" onChange={event => onUpdate(currentSlide.id, { body: event.target.value })}/>
        <button type="button" className="secondary-button note-editor-done" onClick={() => setNoteEditing(false)}>編集を閉じる</button>
      </div> : <p className={`note-widget-body ${currentSlide.body?.trim() ? '' : 'is-empty'}`}>{currentSlide.body?.trim() || '編集ボタンから目標やメモを入力できます。'}</p>}
      {canCarousel && <div className="widget-carousel-controls"><div className="widget-carousel-dots">{slides.map((item, index) => <button type="button" key={item.id} className={slideIndex === index ? 'active' : ''} aria-label={`${index + 1}件目を表示`} onClick={() => setSlideIndex(index)}/>)}</div><div className="widget-carousel-arrows"><button type="button" aria-label="前の自由記載" onClick={() => changeSlide(-1)}><ChevronLeft size={16}/></button><span>{slideIndex + 1} / {slides.length}</span><button type="button" aria-label="次の自由記載" onClick={() => changeSlide(1)}><ChevronRight size={16}/></button></div></div>}
    </>}
    {widget.type === 'monthly' && <>
      <div className="dashboard-widget-heading"><div><span className="widget-kicker">MONTHLY RECORD</span><h3>月別成績</h3></div><span className="dashboard-widget-icon"><CalendarDays size={18}/></span></div>
      <div className="monthly-widget-track" aria-label="直近6か月の月別成績を左右にスライドして表示">{monthlyStats.map(item => <div className="monthly-widget-month" key={item.month}>
        <strong>{`${Number(item.month.slice(5, 7))}月`}</strong><span>{item.month.slice(0, 4)}年</span>
        <div className="monthly-widget-rate">{item.rate}</div><small>{item.total}試合 · {item.wins}勝 {item.losses}敗{item.draws ? ` ${item.draws}分` : ''}</small>
      </div>)}</div>
      <p className="monthly-widget-hint">左右にスライドして過去の月を確認</p>
    </>}
    {widget.type === 'recentMatches' && <>
      <div className="dashboard-widget-heading"><div><span className="widget-kicker">LATEST BATTLES</span><h3>直近の試合履歴</h3></div><button type="button" className="text-button" onClick={onOpenHistory}>すべて見る →</button></div>
      {sortedMatches.length ? <div className="recent-widget-list">{sortedMatches.slice(0, 5).map(match => <div className="recent-widget-row" key={match.id}>
        <div className="recent-widget-date">{formatDateTime(match.playedAt)}</div>
        <div className="recent-widget-main"><strong>{match.heroName}</strong><span>{match.mode ?? 'バトアリ'} · {match.mapName}</span></div>
        <span className={`result-pill ${match.result}`}>{resultLabel(match.result)}</span>
      </div>)}</div> : <p className="dashboard-widget-empty">試合を記録すると、ここに履歴が表示されます。</p>}
    </>}
  </article>
}
'''
app = app[:start] + component + app[end:]

# 13) CSS追記
css_addition = r'''

/* COMPASS DASHBOARD CAROUSEL + IN-PLACE EDIT v2 */
.dashboard-edit-toolbar {
  position: relative; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;
  gap: 12px; padding: 14px 16px; margin-bottom: 14px; border: 1px solid var(--accent-line, #2e6470);
  border-radius: 14px; background: linear-gradient(125deg, var(--accent-soft, #14313a), var(--surface, #121b2e));
}
.dashboard-edit-toolbar-copy { display: grid; gap: 4px; min-width: 180px; }
.dashboard-edit-toolbar-copy strong { color: var(--text-main, #edf3fb); font-size: 11px; }
.dashboard-edit-toolbar-copy span { color: var(--text-muted, #8d9ab0); font-size: 9px; line-height: 1.5; }
.dashboard-edit-toolbar-actions { display: flex; flex-wrap: wrap; align-items: center; gap: 7px; }
.dashboard-edit-toolbar-actions button { display: inline-flex; align-items: center; justify-content: center; gap: 5px; min-height: 34px; padding: 7px 10px; font-size: 9px; }
.dashboard-add-panel { flex: 1 1 100%; padding-top: 12px; border-top: 1px solid var(--accent-line, #2e6470); }
.dashboard-add-panel-heading { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin-bottom: 9px; }
.dashboard-add-panel-heading strong { color: var(--text-main, #edf3fb); font-size: 10px; }
.dashboard-add-panel-heading span { color: var(--text-muted, #8d9ab0); font-size: 8px; }
.dashboard-add-panel-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 7px; }
.dashboard-add-option { display: flex; align-items: center; justify-content: space-between; gap: 10px; min-width: 0; padding: 10px 11px; border: 1px solid var(--line, #293c4b); border-radius: 10px; background: var(--surface-raised, #141f30); color: var(--accent-strong, #04bfd0); text-align: left; }
.dashboard-add-option > span { display: grid; gap: 4px; min-width: 0; }
.dashboard-add-option strong { color: var(--text-main, #edf3fb); font-size: 9px; }
.dashboard-add-option small { color: var(--text-muted, #8d9ab0); font-size: 8px; line-height: 1.5; }
.dashboard-add-option:hover { border-color: var(--accent, #39e6f2); background: var(--accent-soft, #10313a); }
.dashboard-add-panel-empty { grid-column: 1 / -1; margin: 0; padding: 10px; color: var(--text-muted, #8d9ab0); font-size: 9px; }
.dashboard-widget-sortable { position: relative; min-width: 0; }
.dashboard-widget-sortable.is-wide { grid-column: 1 / -1; }
.dashboard-widget-sortable.is-tall { min-height: 350px; }
.dashboard-widget-sortable.is-dragging { z-index: 5; opacity: .58; transform: scale(.985); }
.dashboard-widget-sortable.is-drop-target > .dashboard-widget-card { outline: 2px dashed var(--accent-strong, #04bfd0); outline-offset: 3px; transform: translateY(2px); }
.dashboard-widget-card { height: 100%; }
.dashboard-widget-card.is-editing { padding-top: 15px; border-style: dashed; border-color: var(--accent-line, #2e6470); }
.dashboard-widget-manage-bar { display: flex; align-items: center; gap: 8px; min-height: 30px; margin: 0 0 12px; padding-bottom: 9px; border-bottom: 1px solid var(--line, #293c4b); }
.dashboard-widget-drag-handle { display: inline-flex; align-items: center; justify-content: center; gap: 4px; min-height: 29px; padding: 5px 9px; border: 1px solid var(--accent-line, #2e6470); border-radius: 8px; background: var(--accent-soft, #10313a); color: var(--accent-strong, #04bfd0); font-size: 9px; font-weight: 800; cursor: grab; touch-action: none; user-select: none; }
.dashboard-widget-drag-handle:active { cursor: grabbing; }
.dashboard-widget-edit-label { flex: 1 1 auto; color: var(--text-muted, #8d9ab0); font-size: 8px; }
.dashboard-widget-remove { flex: 0 0 29px; width: 29px; height: 29px; min-width: 29px; padding: 5px; color: #e98796; }
.dashboard-widget-sortable:focus-within { z-index: 18; }
.dashboard-widget-card.widget-heroInfo, .dashboard-widget-card.widget-note { touch-action: pan-y; }
.dashboard-widget-card.widget-heroInfo { overflow: visible; }
.dashboard-widget-card.widget-heroInfo::before { border-radius: 16px 0 0 0; }
.hero-info-heading { margin-bottom: 8px; }
.hero-info-selector-row { display: grid; grid-template-columns: minmax(105px, .32fr) minmax(0, 1fr); align-items: center; gap: 10px; margin: 8px 0 4px; }
.hero-info-selector-row > label { color: var(--text-muted, #8d9ab0); font-size: 9px; font-weight: 750; }
.hero-info-selector-row .hero-search-dropdown { min-width: 0; width: 100%; }
.hero-info-selected-name { margin: 7px 0 0; color: var(--text-main, #edf3fb); font-size: 11px; font-weight: 800; }
.hero-info-metrics { margin-top: 10px; }
.widget-carousel-controls { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-top: 13px; padding-top: 9px; border-top: 1px solid var(--line, #293c4b); }
.widget-carousel-dots { display: inline-flex; align-items: center; gap: 6px; }
.widget-carousel-dots button { width: 7px; height: 7px; padding: 0; border: 0; border-radius: 999px; background: var(--line, #41536a); }
.widget-carousel-dots button.active { width: 19px; background: var(--accent-strong, #04bfd0); }
.widget-carousel-arrows { display: inline-flex; align-items: center; gap: 8px; }
.widget-carousel-arrows button { display: grid; place-items: center; width: 28px; height: 27px; padding: 0; border: 1px solid var(--line, #293c4b); border-radius: 7px; background: var(--surface-raised, #141f30); color: var(--text-soft, #b5cbd5); }
.widget-carousel-arrows button:hover { border-color: var(--accent-line, #2e6470); color: var(--accent-strong, #04bfd0); }
.widget-carousel-arrows span { color: var(--text-muted, #8d9ab0); font-size: 8px; font-variant-numeric: tabular-nums; }
.note-widget-header { align-items: center; }
.note-edit-trigger { flex: 0 0 30px; width: 30px; height: 30px; min-width: 30px; padding: 6px; }
.note-home-editor { display: grid; gap: 9px; margin-top: 8px; }
.note-home-editor input:not([type='checkbox']), .note-home-editor textarea { width: 100%; min-width: 0; padding: 10px 11px; border: 1px solid var(--line, #354158); border-radius: 9px; outline: none; background: var(--surface-raised, #141f30); color: var(--text-main, #edf3fb); font-size: 10px; }
.note-home-editor textarea { resize: vertical; line-height: 1.7; }
.note-home-editor input:focus, .note-home-editor textarea:focus { border-color: var(--accent, #39e6f2); box-shadow: 0 0 0 3px var(--accent-soft, #10313a); }
.note-editor-done { justify-self: end; padding: 7px 10px; font-size: 9px; }
.dashboard-editor-menu-label { display: flex; align-items: center; gap: 8px; padding: 12px 25px; border-bottom: 1px solid var(--line, #2a354b); color: var(--accent-strong, #04bfd0); font-size: 10px; font-weight: 800; }
@media (max-width: 760px) {
  .dashboard-edit-toolbar { align-items: flex-start; padding: 12px; }
  .dashboard-edit-toolbar-actions { width: 100%; }
  .dashboard-edit-toolbar-actions button { flex: 1 1 auto; padding-inline: 7px; }
  .dashboard-add-panel-grid { grid-template-columns: minmax(0, 1fr); }
  .dashboard-widget-card.is-editing { padding-top: 12px; }
  .dashboard-widget-manage-bar { margin-bottom: 9px; padding-bottom: 7px; }
  .hero-info-selector-row { grid-template-columns: minmax(0, 1fr); gap: 6px; }
  .hero-info-selector-row > label { font-size: 8px; }
  .dashboard-editor-menu-label { padding: 10px 15px; }
}
@media (max-width: 390px) {
  .dashboard-edit-toolbar-actions button { font-size: 8px; }
  .dashboard-widget-drag-handle { padding-inline: 7px; }
  .dashboard-widget-edit-label { font-size: 7px; }
  .hero-info-selector-row .hero-search-dropdown-trigger { min-height: 34px; }
}
'''
css = css.rstrip() + "\n" + css_addition

# 14) 旧ホーム編集タブは表示させない。メニュー編集を開くときだけmenuを選択するため、分岐は安全に残す。
# JSX内のホーム編集モーダルは到達不能になり、ホーム編集は実画面上で行う。

# 差分を作成する前に最低限の整合性を再確認
required_app = [
    "function handleDashboardDragStart(",
    "const dashboardWidgetGroups = (() => {",
    "heroes={orderedHeroOptions}",
    "const importedTotals = period === 'all'",
    "className={`page-stack ${dashboardEditMode ? 'dashboard-is-editing' : ''}`}"
]
for token in required_app:
    if token not in app:
        raise SystemExit(f"安全確認：変更後App.tsxに必要な要素がありません：{token}。ファイルは変更していません。")
if css.count(MARKER) != 1:
    raise SystemExit("安全確認：CSS改修マーカーが正しくありません。ファイルは変更していません。")

# 元ファイルを退避し、すべての検査が通ってから2ファイルを書き込む
backup_dir = ROOT / ".patch-backups" / datetime.now().strftime("%Y%m%d-%H%M%S-dashboard-carousel")
backup_dir.mkdir(parents=True, exist_ok=False)
(backup_dir / "App.tsx.before").write_text(app_original, encoding="utf-8")
(backup_dir / "style-improvements.css.before").write_text(css_original, encoding="utf-8")
APP.write_text(app, encoding="utf-8")
CSS.write_text(css, encoding="utf-8")

print("適用しました。")
print("変更ファイル：src/App.tsx、src/style-improvements.css")
print(f"バックアップ：{backup_dir}")
print("変更内容：ホーム上ドラッグ配置、ヒーロー/自由記載の最大3件カルーセル、ホーム上の検索・編集、全体勝率への過去累計反映")
