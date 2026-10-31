from pathlib import Path
from datetime import datetime
import shutil
import sys

ROOT = Path.cwd()
APP = ROOT / 'src' / 'App.tsx'
CSS = ROOT / 'src' / 'style-improvements.css'
MARKER = '/* COMPASS DASHBOARD CUSTOMIZATION v1 */'

if not APP.exists() or not CSS.exists():
    print('エラー：Codespacesのリポジトリ直下（package.jsonがある場所）で実行してください。')
    sys.exit(1)

app = APP.read_text(encoding='utf-8')
css = CSS.read_text(encoding='utf-8')
if MARKER in app or MARKER in css:
    print('この改築パッチは既に適用されています。二重適用を中止しました。')
    sys.exit(0)

required_app = [
    "import { Activity, BarChart3, CalendarDays, ChevronDown, Download, FileUp, Gauge, History, Lock, Minus, Pencil, Plus, Search, Settings, Shield, Star, Sun, Moon, Swords, Trash2, Trophy, Unlock, X } from 'lucide-react'",
    "type Page = 'dashboard' | 'add' | 'history' | 'settings' | 'heroStats' | 'heroDetail'",
    "  heroBaseStats?: Record<string, HeroBaseStat>\n}",
    "  return {\n    ...(input ?? {}), matches, heroes, maps, initialRankPoints,",
    "  const [toast, setToast] = useState('')",
    "  const monthlyStats = useMemo(() => {\n    const buckets = new Map<string, Match[]>()",
    "  return <div className=\"app-shell\">\n    <aside className=\"sidebar\">",
    "      <nav>\n        <NavItem active={page === 'dashboard'} icon={<Gauge size={18}/>} label=\"ホーム\" onClick={() => setPage('dashboard')} />\n        <NavItem active={page === 'add'} icon={<Plus size={18}/>} label=\"試合を記録\" onClick={startNewMatch} />\n        <NavItem active={page === 'history'} icon={<History size={18}/>} label=\"戦績一覧\" onClick={() => setPage('history')} />\n        <NavItem active={page === 'heroStats' || page === 'heroDetail'} icon={<Trophy size={18}/>} label=\"ヒーロー詳細ログ\" onClick={() => setPage('heroStats')} />\n        <NavItem active={page === 'settings'} icon={<Settings size={18}/>} label=\"設定・その他\" onClick={() => setPage('settings')} />\n      </nav>",
    "      <header className=\"topbar\">\n        <div><h1>{({ dashboard: 'ホーム', add: '試合を記録', history: '戦績一覧', settings: '設定・その他', heroStats: 'ヒーロー詳細ログ', heroDetail: 'ヒーロー詳細ログ' } as Record<Page, string>)[page]}</h1></div>\n        <button className=\"primary-button top-add\" onClick={startNewMatch}><Plus size={17}/> 試合を追加</button>\n      </header>",
    "      {page === 'dashboard' && <section className=\"page-stack\">\n        <div className=\"stats-grid dashboard-stats-grid\">",
    "        <div className=\"content-card\">\n          <div className=\"section-heading\"><div><h3>最近の試合</h3><p>直近に記録した試合を表示します</p></div><button className=\"text-button\" onClick={() => setPage('history')}>すべて見る →</button></div>\n          {sortedMatches.length ? <MatchTable matches={sortedMatches.slice(0, 5)} onEdit={beginEditMatch} onDelete={deleteMatch}/> : <EmptyState onAdd={startNewMatch}/>}\n        </div>\n        <div className=\"analytics-grid\">",
    "      {toast && <div className=\"toast\">",
]
missing = [x[:100].replace('\n','\\n') for x in required_app if x not in app]
if missing:
    print('安全確認：現在のApp.tsxが想定した版と一致しないため、変更していません。')
    for item in missing:
        print(' - ' + item)
    sys.exit(2)

# Backups are created before the first write.
backup_dir = ROOT / '.patch-backups' / datetime.now().strftime('%Y%m%d-%H%M%S-dashboard-overhaul')
backup_dir.mkdir(parents=True, exist_ok=False)
shutil.copy2(APP, backup_dir / 'App.tsx')
shutil.copy2(CSS, backup_dir / 'style-improvements.css')

# 1) Data model and safe defaults. These settings live inside the existing Store JSON payload;
#    no Supabase table or migration is changed.
app = app.replace(
    "type Page = 'dashboard' | 'add' | 'history' | 'settings' | 'heroStats' | 'heroDetail'\ntype CloudContextValue",
    """type Page = 'dashboard' | 'add' | 'history' | 'settings' | 'heroStats' | 'heroDetail'
type NavigationKey = 'dashboard' | 'add' | 'history' | 'heroStats' | 'settings'
type DashboardWidgetType = 'rank' | 'winRate' | 'streak' | 'popularHero' | 'heroInfo' | 'note' | 'monthly' | 'recentMatches'
type DashboardPeriod = 'today' | 'month' | 'all'
type DashboardWidget = {
  id: string
  type: DashboardWidgetType
  period?: DashboardPeriod
  heroName?: string
  showHeading?: boolean
  heading?: string
  body?: string
}
type MonthlyStat = { month: string; total: number; wins: number; losses: number; draws: number; rate: string }
type CloudContextValue"""
)
app = app.replace(
    "  heroBaseStats?: Record<string, HeroBaseStat>\n}",
    "  heroBaseStats?: Record<string, HeroBaseStat>\n  /** ホーム画面の配置。既存の保存データには初期配置を補います。 */\n  dashboardWidgets?: DashboardWidget[]\n  /** サイドメニューの表示順 */\n  menuOrder?: NavigationKey[]\n}",
    1
)

# Add defaults and normalizers immediately after the implementation-order map.
anchor = "const heroOrderIndex = new Map(heroImplementationOrder.map((name, index) => [name, index]))\n"
addition = r'''const defaultNavigationOrder: NavigationKey[] = ['dashboard', 'add', 'history', 'heroStats', 'settings']
const defaultDashboardWidgets: DashboardWidget[] = [
  { id: 'rank', type: 'rank' },
  { id: 'win-rate', type: 'winRate', period: 'today' },
  { id: 'streak', type: 'streak' },
  { id: 'popular-hero', type: 'popularHero', period: 'all' },
  { id: 'hero-info', type: 'heroInfo', heroName: '' },
  { id: 'personal-note', type: 'note', showHeading: false, heading: '', body: '' },
  { id: 'monthly', type: 'monthly' },
  { id: 'recent-matches', type: 'recentMatches' }
]
const dashboardWidgetTypes: DashboardWidgetType[] = ['rank', 'winRate', 'streak', 'popularHero', 'heroInfo', 'note', 'monthly', 'recentMatches']
const repeatableDashboardWidgetTypes: DashboardWidgetType[] = ['heroInfo', 'note']
function normalizeMenuOrder(value: unknown): NavigationKey[] {
  const valid = Array.isArray(value) ? value.filter((item): item is NavigationKey => defaultNavigationOrder.includes(item as NavigationKey)) : []
  return [...new Set([...valid, ...defaultNavigationOrder])]
}
function normalizeDashboardWidgets(value: unknown): DashboardWidget[] {
  if (!Array.isArray(value)) return defaultDashboardWidgets.map(widget => ({ ...widget }))
  const seenIds = new Set<string>()
  const seenSingletons = new Set<DashboardWidgetType>()
  return value.slice(0, 80).flatMap((raw, index) => {
    if (!raw || typeof raw !== 'object') return []
    const item = raw as Record<string, unknown>
    if (typeof item.type !== 'string' || !dashboardWidgetTypes.includes(item.type as DashboardWidgetType)) return []
    const type = item.type as DashboardWidgetType
    if (!repeatableDashboardWidgetTypes.includes(type) && seenSingletons.has(type)) return []
    if (!repeatableDashboardWidgetTypes.includes(type)) seenSingletons.add(type)
    let id = typeof item.id === 'string' && item.id.trim() ? item.id.trim().slice(0, 100) : `${type}-${index}`
    if (seenIds.has(id)) id = `${id}-${index}`
    seenIds.add(id)
    const period = item.period === 'today' || item.period === 'month' || item.period === 'all' ? item.period : undefined
    return [{
      id, type, period,
      heroName: typeof item.heroName === 'string' ? item.heroName.slice(0, 100) : '',
      showHeading: Boolean(item.showHeading),
      heading: typeof item.heading === 'string' ? item.heading.slice(0, 80) : '',
      body: typeof item.body === 'string' ? item.body.slice(0, 3000) : ''
    }]
  })
}
'''
if anchor not in app:
    raise RuntimeError('implementation-order anchor missing')
app = app.replace(anchor, anchor + addition, 1)

# Fresh stores and normalized old/backed-up stores get safe widget/menu defaults.
app = app.replace(
    "    stageRotations: { ...initialNovember2026StageRotations }\n  }\n}",
    "    stageRotations: { ...initialNovember2026StageRotations },\n    dashboardWidgets: defaultDashboardWidgets.map(widget => ({ ...widget })), menuOrder: [...defaultNavigationOrder]\n  }\n}",
    1
)
app = app.replace(
    "    activeSeason, lastSeasonResetMonth: resetMonth, stageRotations, heroBaseStats\n  }\n}",
    "    activeSeason, lastSeasonResetMonth: resetMonth, stageRotations, heroBaseStats,\n    dashboardWidgets: normalizeDashboardWidgets(input?.dashboardWidgets), menuOrder: normalizeMenuOrder(input?.menuOrder)\n  }\n}",
    1
)

# 2) Editor state, sorting interactions, and store update functions.
app = app.replace(
    "  const [toast, setToast] = useState('')\n",
    """  const [toast, setToast] = useState('')
  const [dashboardEditorOpen, setDashboardEditorOpen] = useState(false)
  const [dashboardEditorTab, setDashboardEditorTab] = useState<'home' | 'menu'>('home')
  const editorSortDragRef = useRef<{ scope: 'home' | 'menu'; id: string; pointerId: number; startX: number; startY: number; moved: boolean } | null>(null)
  const [editorDraggingKey, setEditorDraggingKey] = useState('')
""",
    1
)

# 3) Monthly dashboard data: always six calendar months, current month first (even when empty).
old_monthly = """  const monthlyStats = useMemo(() => {
    const buckets = new Map<string, Match[]>()
    for (const match of store.matches) { const month = match.playedAt.slice(0, 7); buckets.set(month, [...(buckets.get(month) ?? []), match]) }
    return [...buckets.entries()].sort((a, b) => b[0].localeCompare(a[0])).slice(0, 6).map(([month, matches]) => ({
      month, total: matches.length, wins: matches.filter(m => m.result === 'win').length, losses: matches.filter(m => m.result === 'loss').length,
      draws: matches.filter(m => m.result === 'draw').length, rate: percent(matches.filter(m => m.result === 'win').length, matches.filter(m => m.result !== 'draw').length)
    }))
  }, [store.matches])"""
new_monthly = """  const monthlyStats = useMemo<MonthlyStat[]>(() => {
    const now = new Date()
    return Array.from({ length: 6 }, (_, index) => {
      const date = new Date(now.getFullYear(), now.getMonth() - index, 1)
      const month = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
      const matches = store.matches.filter(match => match.playedAt.startsWith(month))
      const wins = matches.filter(match => match.result === 'win').length
      const losses = matches.filter(match => match.result === 'loss').length
      const draws = matches.filter(match => match.result === 'draw').length
      return { month, total: matches.length, wins, losses, draws, rate: percent(wins, wins + losses) }
    })
  }, [store.matches])"""
if old_monthly not in app:
    raise RuntimeError('monthlyStats block did not match')
app = app.replace(old_monthly, new_monthly, 1)

# 4) Add menu/widget operations and data for render immediately before the app-shell return.
return_anchor = "  return <div className=\"app-shell\">\n    <aside className=\"sidebar\">"
operations = r'''  function updateDashboardWidget(id: string, changes: Partial<DashboardWidget>) {
    setStore(current => ({ ...current, dashboardWidgets: (current.dashboardWidgets ?? defaultDashboardWidgets).map(widget => widget.id === id ? { ...widget, ...changes } : widget) }))
  }
  function addDashboardWidget(type: DashboardWidgetType) {
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
  }
  function removeDashboardWidget(id: string) {
    setStore(current => ({ ...current, dashboardWidgets: (current.dashboardWidgets ?? []).filter(widget => widget.id !== id) }))
  }
  function reorderDashboardWidgets(sourceId: string, targetId: string, before = true) {
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
  }
  function moveDashboardWidget(id: string, offset: number) {
    setStore(current => {
      const items = [...(current.dashboardWidgets ?? [])]
      const index = items.findIndex(item => item.id === id)
      const target = index + offset
      if (index < 0 || target < 0 || target >= items.length) return current
      ;[items[index], items[target]] = [items[target], items[index]]
      return { ...current, dashboardWidgets: items }
    })
  }
  function reorderMenuItems(sourceId: NavigationKey, targetId: NavigationKey, before = true) {
    setStore(current => {
      const items = [...normalizeMenuOrder(current.menuOrder)]
      const sourceIndex = items.indexOf(sourceId)
      if (sourceIndex < 0 || sourceId === targetId) return current
      items.splice(sourceIndex, 1)
      const targetIndex = items.indexOf(targetId)
      if (targetIndex < 0) return current
      items.splice(targetIndex + (before ? 0 : 1), 0, sourceId)
      return { ...current, menuOrder: items }
    })
  }
  function moveMenuItem(id: NavigationKey, offset: number) {
    setStore(current => {
      const items = [...normalizeMenuOrder(current.menuOrder)]
      const index = items.indexOf(id)
      const target = index + offset
      if (index < 0 || target < 0 || target >= items.length) return current
      ;[items[index], items[target]] = [items[target], items[index]]
      return { ...current, menuOrder: items }
    })
  }
  function handleEditorPointerDown(scope: 'home' | 'menu', id: string, event: React.PointerEvent<HTMLButtonElement>) {
    if (event.pointerType === 'mouse' && event.button !== 0) return
    event.preventDefault()
    editorSortDragRef.current = { scope, id, pointerId: event.pointerId, startX: event.clientX, startY: event.clientY, moved: false }
    event.currentTarget.setPointerCapture(event.pointerId)
  }
  function handleEditorPointerMove(event: React.PointerEvent<HTMLButtonElement>) {
    const drag = editorSortDragRef.current
    if (!drag || drag.pointerId !== event.pointerId) return
    if (!drag.moved && Math.hypot(event.clientX - drag.startX, event.clientY - drag.startY) > 7) {
      drag.moved = true
      setEditorDraggingKey(`${drag.scope}:${drag.id}`)
    }
  }
  function handleEditorPointerUp(event: React.PointerEvent<HTMLButtonElement>) {
    const drag = editorSortDragRef.current
    if (!drag || drag.pointerId !== event.pointerId) return
    if (drag.moved) {
      const target = document.elementFromPoint(event.clientX, event.clientY)?.closest<HTMLElement>('[data-editor-sort-id]')
      if (target && target.dataset.editorSortScope === drag.scope) {
        const targetId = target.dataset.editorSortId ?? ''
        const rect = target.getBoundingClientRect()
        const before = event.clientY < rect.top + rect.height / 2
        if (drag.scope === 'home') reorderDashboardWidgets(drag.id, targetId, before)
        else reorderMenuItems(drag.id as NavigationKey, targetId as NavigationKey, before)
      }
    }
    editorSortDragRef.current = null
    setEditorDraggingKey('')
  }
  function handleEditorPointerCancel() {
    editorSortDragRef.current = null
    setEditorDraggingKey('')
  }

  const navigationEntries: { key: NavigationKey; label: string; icon: React.ReactNode; action: () => void }[] = [
    { key: 'dashboard', label: 'ホーム', icon: <Gauge size={18}/>, action: () => setPage('dashboard') },
    { key: 'add', label: '試合を記録', icon: <Plus size={18}/>, action: startNewMatch },
    { key: 'history', label: '戦績一覧', icon: <History size={18}/>, action: () => setPage('history') },
    { key: 'heroStats', label: 'ヒーロー詳細ログ', icon: <Trophy size={18}/>, action: () => setPage('heroStats') },
    { key: 'settings', label: '設定・その他', icon: <Settings size={18}/>, action: () => setPage('settings') }
  ]
  const orderedNavigationEntries = normalizeMenuOrder(store.menuOrder).map(key => navigationEntries.find(item => item.key === key)!).filter(Boolean)
  const widgetCatalog: { type: DashboardWidgetType; label: string; description: string; size: string }[] = [
    { type: 'rank', label: '現在のランク', description: '現在のランクとポイント', size: '横1' },
    { type: 'winRate', label: '勝率', description: '今日・今月・全体を切り替え', size: '横1' },
    { type: 'streak', label: '連勝数', description: '現在の連勝・連敗と最高連勝', size: '横1' },
    { type: 'popularHero', label: '使用率の高いヒーロー', description: '今日・今月・全体を切り替え', size: '横1' },
    { type: 'heroInfo', label: '指定ヒーローの情報', description: '勝率・使用数・称号までの進捗。複数追加可能', size: '横2' },
    { type: 'note', label: '自由記載', description: '目標やメモ。複数追加可能', size: '横2' },
    { type: 'monthly', label: '月別成績', description: '今月から直近6か月をスライド表示', size: '横1' },
    { type: 'recentMatches', label: '直近の試合履歴', description: '最新5試合。横2・縦2', size: '横2・縦2' }
  ]
'''
if return_anchor not in app:
    raise RuntimeError('app-shell return anchor missing')
app = app.replace(return_anchor, operations + '\n' + return_anchor, 1)

# 5) Replace static navigation with the saved/reorderable navigation list.
old_nav = """      <nav>
        <NavItem active={page === 'dashboard'} icon={<Gauge size={18}/>} label="ホーム" onClick={() => setPage('dashboard')} />
        <NavItem active={page === 'add'} icon={<Plus size={18}/>} label="試合を記録" onClick={startNewMatch} />
        <NavItem active={page === 'history'} icon={<History size={18}/>} label="戦績一覧" onClick={() => setPage('history')} />
        <NavItem active={page === 'heroStats' || page === 'heroDetail'} icon={<Trophy size={18}/>} label="ヒーロー詳細ログ" onClick={() => setPage('heroStats')} />
        <NavItem active={page === 'settings'} icon={<Settings size={18}/>} label="設定・その他" onClick={() => setPage('settings')} />
      </nav>"""
new_nav = """      <nav>
        {orderedNavigationEntries.map(item => <NavItem key={item.key} active={page === item.key || (item.key === 'heroStats' && page === 'heroDetail')} icon={item.icon} label={item.label} onClick={item.action} />)}
      </nav>"""
if old_nav not in app:
    raise RuntimeError('static navigation block did not match')
app = app.replace(old_nav, new_nav, 1)

# 6) The edit button sits between the page title and the match-add action.
old_topbar = """      <header className="topbar">
        <div><h1>{({ dashboard: 'ホーム', add: '試合を記録', history: '戦績一覧', settings: '設定・その他', heroStats: 'ヒーロー詳細ログ', heroDetail: 'ヒーロー詳細ログ' } as Record<Page, string>)[page]}</h1></div>
        <button className="primary-button top-add" onClick={startNewMatch}><Plus size={17}/> 試合を追加</button>
      </header>"""
new_topbar = """      <header className="topbar">
        <div><h1>{({ dashboard: 'ホーム', add: '試合を記録', history: '戦績一覧', settings: '設定・その他', heroStats: 'ヒーロー詳細ログ', heroDetail: 'ヒーロー詳細ログ' } as Record<Page, string>)[page]}</h1></div>
        <div className="topbar-actions">
          {page === 'dashboard' && <button type="button" className="secondary-button dashboard-edit-trigger" onClick={() => { setDashboardEditorTab('home'); setDashboardEditorOpen(true) }}><Pencil size={15}/> ホーム・メニューの編集</button>}
          <button className="primary-button top-add" onClick={startNewMatch}><Plus size={17}/> 試合を追加</button>
        </div>
      </header>"""
if old_topbar not in app:
    raise RuntimeError('topbar block did not match')
app = app.replace(old_topbar, new_topbar, 1)

# 7) Replace the old fixed dashboard with a user-configurable two-column widget canvas.
start_dashboard = "      {page === 'dashboard' && <section className=\"page-stack\">\n        <div className=\"stats-grid dashboard-stats-grid\">"
end_dashboard = "      </section>}\n\n      {page === 'add' && <section className=\"content-card form-card\">"
start = app.find(start_dashboard)
end = app.find(end_dashboard, start)
if start < 0 or end < 0:
    raise RuntimeError('dashboard section boundaries did not match')
new_dashboard = r'''      {page === 'dashboard' && <section className="page-stack">
        <div className="dashboard-widget-grid">
          {(store.dashboardWidgets ?? defaultDashboardWidgets).map(widget => <DashboardWidgetCard
            key={widget.id} widget={widget} store={store} currentRankState={currentRankState}
            sortedMatches={sortedMatches} monthlyStats={monthlyStats}
            onUpdate={updateDashboardWidget} onOpenHistory={() => setPage('history')}
          />)}
          {(store.dashboardWidgets ?? []).length === 0 && <div className="dashboard-empty-layout"><LayoutDashboard size={28}/><strong>ホーム画面が空です</strong><span>「ホーム・メニューの編集」から表示したい項目を追加できます。</span></div>}
        </div>
        <div className="hint-row"><Shield size={17}/><span>{cloud ? 'ログイン中のアカウントにホーム画面と試合記録を同期します。別の端末でも同じ配置を利用できます。' : '端末を変える前にバックアップを保存してください。'}</span></div>
      </section>}

'''
app = app[:start] + new_dashboard + app[end + len("      </section>}\n\n"):]

# 8) Insert the polished editor dialog before the toast. It supports touch/mouse dragging and arrow controls.
editor_markup = r'''      {dashboardEditorOpen && <div className="dashboard-editor-backdrop" role="presentation" onClick={() => setDashboardEditorOpen(false)}>
        <section className="dashboard-editor-modal" role="dialog" aria-modal="true" aria-labelledby="dashboard-editor-title" onClick={event => event.stopPropagation()}>
          <header className="dashboard-editor-header">
            <div><span className="dashboard-editor-eyebrow">PERSONALIZE YOUR TRACKER</span><h2 id="dashboard-editor-title">ホーム・メニューの編集</h2><p>配置や表示項目は自動で保存されます。</p></div>
            <button type="button" className="icon-button dashboard-editor-close" aria-label="編集を閉じる" onClick={() => setDashboardEditorOpen(false)}><X size={19}/></button>
          </header>
          <div className="dashboard-editor-tabs" role="tablist" aria-label="編集する場所">
            <button type="button" role="tab" aria-selected={dashboardEditorTab === 'home'} className={dashboardEditorTab === 'home' ? 'active' : ''} onClick={() => setDashboardEditorTab('home')}><LayoutDashboard size={16}/> ホーム画面</button>
            <button type="button" role="tab" aria-selected={dashboardEditorTab === 'menu'} className={dashboardEditorTab === 'menu' ? 'active' : ''} onClick={() => setDashboardEditorTab('menu')}><Menu size={16}/> メニュー欄</button>
          </div>
          {dashboardEditorTab === 'home' ? <div className="dashboard-editor-content">
            <section className="dashboard-editor-section">
              <div className="dashboard-editor-section-heading"><div><h3>配置中の項目</h3><p>つまみを長押ししてドラッグすると順番を変更できます。上下ボタンでも移動できます。</p></div><span className="editor-count">{(store.dashboardWidgets ?? []).length}項目</span></div>
              <div className="dashboard-editor-grid">
                {(store.dashboardWidgets ?? []).map((widget, index) => {
                  const catalog = widgetCatalog.find(item => item.type === widget.type)!
                  const dragKey = `home:${widget.id}`
                  return <article key={widget.id} data-editor-sort-id={widget.id} data-editor-sort-scope="home" className={`dashboard-editor-widget ${widget.type === 'heroInfo' || widget.type === 'note' || widget.type === 'recentMatches' ? 'wide' : ''} ${editorDraggingKey === dragKey ? 'is-dragging' : ''}`}>
                    <div className="dashboard-editor-widget-head">
                      <button type="button" className="editor-drag-handle" aria-label={`${catalog.label}をドラッグして並べ替え`} onPointerDown={event => handleEditorPointerDown('home', widget.id, event)} onPointerMove={handleEditorPointerMove} onPointerUp={handleEditorPointerUp} onPointerCancel={handleEditorPointerCancel}><GripVertical size={18}/></button>
                      <div className="dashboard-editor-widget-title"><strong>{catalog.label}</strong><span>{catalog.size}</span></div>
                      <div className="editor-widget-actions">
                        <button type="button" className="icon-button compact-editor-action" aria-label="上へ移動" title="上へ" disabled={index === 0} onClick={() => moveDashboardWidget(widget.id, -1)}><ChevronUp size={15}/></button>
                        <button type="button" className="icon-button compact-editor-action" aria-label="下へ移動" title="下へ" disabled={index === (store.dashboardWidgets ?? []).length - 1} onClick={() => moveDashboardWidget(widget.id, 1)}><ChevronDown size={15}/></button>
                        <button type="button" className="icon-button compact-editor-action remove-editor-action" aria-label={`${catalog.label}を削除`} title="ホームから削除" onClick={() => removeDashboardWidget(widget.id)}><Trash2 size={15}/></button>
                      </div>
                    </div>
                    {widget.type === 'heroInfo' && <div className="editor-widget-settings"><label>表示するヒーロー</label><select value={widget.heroName ?? ''} onChange={event => updateDashboardWidget(widget.id, { heroName: event.target.value })}><option value="">ヒーローを選択してください</option>{store.heroes.map(hero => <option key={hero.name} value={hero.name}>{hero.name}（{hero.role}）</option>)}</select></div>}
                    {widget.type === 'note' && <div className="editor-widget-settings note-editor-settings">
                      <label className="editor-heading-toggle"><input type="checkbox" checked={Boolean(widget.showHeading)} onChange={event => updateDashboardWidget(widget.id, { showHeading: event.target.checked })}/> 見出しを追加</label>
                      {widget.showHeading && <input value={widget.heading ?? ''} maxLength={80} placeholder="例：今月の目標" onChange={event => updateDashboardWidget(widget.id, { heading: event.target.value })}/>}
                      <textarea rows={3} maxLength={3000} value={widget.body ?? ''} placeholder="自由に記載できます。例：11月中にリリカ使いを達成する" onChange={event => updateDashboardWidget(widget.id, { body: event.target.value })}/>
                    </div>}
                  </article>
                })}
                {(store.dashboardWidgets ?? []).length === 0 && <div className="editor-no-widgets">まだ項目がありません。下の一覧から追加してください。</div>}
              </div>
            </section>
            <section className="dashboard-editor-section dashboard-widget-library-section">
              <div className="dashboard-editor-section-heading"><div><h3>項目を追加</h3><p>追加後、上の配置一覧から並べ替えや内容の編集ができます。</p></div></div>
              <div className="dashboard-widget-library">
                {widgetCatalog.filter(item => repeatableDashboardWidgetTypes.includes(item.type) || !(store.dashboardWidgets ?? []).some(widget => widget.type === item.type)).map(item => <div className="dashboard-widget-library-item" key={item.type}>
                  <div><strong>{item.label}</strong><span>{item.description}</span><small>{item.size}</small></div>
                  <button type="button" className="secondary-button" onClick={() => addDashboardWidget(item.type)}><Plus size={15}/> 追加</button>
                </div>)}
                {widgetCatalog.every(item => !repeatableDashboardWidgetTypes.includes(item.type) && (store.dashboardWidgets ?? []).some(widget => widget.type === item.type)) && <p className="editor-library-complete">追加できる標準項目はすべて配置済みです。ヒーロー情報と自由記載は複数追加できます。</p>}
              </div>
            </section>
          </div> : <div className="dashboard-editor-content menu-editor-content">
            <section className="dashboard-editor-section">
              <div className="dashboard-editor-section-heading"><div><h3>メニューの並び順</h3><p>ドラッグ、または上下ボタンで順番を変更できます。メニュー項目自体は削除されません。</p></div></div>
              <div className="menu-editor-list">
                {normalizeMenuOrder(store.menuOrder).map((key, index) => {
                  const item = navigationEntries.find(entry => entry.key === key)!
                  const dragKey = `menu:${key}`
                  return <article key={key} data-editor-sort-id={key} data-editor-sort-scope="menu" className={`menu-editor-item ${editorDraggingKey === dragKey ? 'is-dragging' : ''}`}>
                    <button type="button" className="editor-drag-handle" aria-label={`${item.label}をドラッグして並べ替え`} onPointerDown={event => handleEditorPointerDown('menu', key, event)} onPointerMove={handleEditorPointerMove} onPointerUp={handleEditorPointerUp} onPointerCancel={handleEditorPointerCancel}><GripVertical size={18}/></button>
                    <span className="menu-editor-icon">{item.icon}</span><strong>{item.label}</strong>
                    <div className="editor-widget-actions">
                      <button type="button" className="icon-button compact-editor-action" aria-label="上へ移動" title="上へ" disabled={index === 0} onClick={() => moveMenuItem(key, -1)}><ChevronUp size={15}/></button>
                      <button type="button" className="icon-button compact-editor-action" aria-label="下へ移動" title="下へ" disabled={index === normalizeMenuOrder(store.menuOrder).length - 1} onClick={() => moveMenuItem(key, 1)}><ChevronDown size={15}/></button>
                    </div>
                  </article>
                })}
              </div>
            </section>
          </div>}
          <footer className="dashboard-editor-footer"><span><Shield size={14}/> 変更はこのアカウントに自動保存されます</span><button type="button" className="primary-button" onClick={() => setDashboardEditorOpen(false)}>完了</button></footer>
        </section>
      </div>}
'''
# Add the editor immediately before the toast, which is a single-line conditional element.
toast_anchor = "    {toast && <div className=\"toast\">"
if toast_anchor not in app:
    raise RuntimeError('toast insertion anchor missing')
app = app.replace(toast_anchor, editor_markup + '\n' + toast_anchor, 1)

# 9) Add the reusable dashboard tile renderer before NavItem.
component_anchor = "function NavItem({ active, icon, label, onClick }"
widget_component = r'''type DashboardWidgetCardProps = {
  widget: DashboardWidget
  store: Store
  currentRankState: RankState
  sortedMatches: Match[]
  monthlyStats: MonthlyStat[]
  onUpdate: (id: string, changes: Partial<DashboardWidget>) => void
  onOpenHistory: () => void
}
function DashboardWidgetCard({ widget, store, currentRankState, sortedMatches, monthlyStats, onUpdate, onOpenHistory }: DashboardWidgetCardProps) {
  const wide = widget.type === 'heroInfo' || widget.type === 'note' || widget.type === 'recentMatches'
  const tall = widget.type === 'recentMatches'
  const period = widget.period ?? (widget.type === 'popularHero' ? 'all' : 'today')
  const periodLabel = period === 'today' ? '今日' : period === 'month' ? '今月' : '全体'
  const periodMatches = period === 'today'
    ? sortedMatches.filter(match => match.playedAt.slice(0, 10) === today())
    : period === 'month'
      ? sortedMatches.filter(match => match.playedAt.slice(0, 7) === currentMonthKey())
      : sortedMatches
  const periodWins = periodMatches.filter(match => match.result === 'win').length
  const periodLosses = periodMatches.filter(match => match.result === 'loss').length
  const periodDraws = periodMatches.filter(match => match.result === 'draw').length
  const winRate = percent(periodWins, periodWins + periodLosses)
  const resultText = `${periodWins}勝 ${periodLosses}敗${periodDraws ? ` ${periodDraws}分` : ''}`
  const allBaseUsage = Object.values(store.heroBaseStats ?? {}).reduce((sum, stat) => sum + stat.battles, 0)
  const totalHeroUsage = periodMatches.length + (period === 'all' ? allBaseUsage : 0)
  const popularHeroRows = store.heroes.map(item => {
    const recent = period === 'today' ? sortedMatches.filter(match => match.heroName === item.name && match.playedAt.slice(0, 10) === today()) : period === 'month' ? sortedMatches.filter(match => match.heroName === item.name && match.playedAt.slice(0, 7) === currentMonthKey()) : sortedMatches.filter(match => match.heroName === item.name)
    const count = recent.length + (period === 'all' ? (store.heroBaseStats?.[item.name]?.battles ?? 0) : 0)
    return { name: item.name, count, rate: totalHeroUsage > 0 ? Math.round(count / totalHeroUsage * 100) : 0 }
  }).filter(item => item.count > 0).sort((a, b) => b.count - a.count || a.name.localeCompare(b.name, 'ja')).slice(0, 4)
  const hero = widget.type === 'heroInfo' ? store.heroes.find(item => item.name === widget.heroName) : undefined
  const heroBase = hero ? (store.heroBaseStats?.[hero.name] ?? { battles: 0, wins: 0 }) : { battles: 0, wins: 0 }
  const heroMatches = hero ? store.matches.filter(match => match.heroName === hero.name) : []
  const heroBattles = heroBase.battles + heroMatches.length
  const heroWins = heroBase.wins + heroMatches.filter(match => match.result === 'win').length
  const heroRate = percent(heroWins, heroBattles)
  const nextMilestone = heroBattles < 1000 ? 1000 : heroBattles < 5000 ? 5000 : heroBattles < 10000 ? 10000 : null
  const remaining = nextMilestone === null ? 0 : Math.max(0, nextMilestone - heroBattles)
  const milestoneStart = nextMilestone === 1000 ? 0 : nextMilestone === 5000 ? 1000 : 5000
  const progress = nextMilestone === null ? 100 : Math.max(0, Math.min(100, (heroBattles - milestoneStart) / (nextMilestone - milestoneStart) * 100))

  return <article className={`dashboard-widget-card ${wide ? 'is-wide' : ''} ${tall ? 'is-tall' : ''} widget-${widget.type}`}>
    {widget.type === 'rank' && <>
      <div className="dashboard-widget-heading"><div><span className="widget-kicker">RANK STATUS</span><h3>現在のランク</h3></div><span className="dashboard-widget-icon"><BarChart3 size={18}/></span></div>
      <strong className="dashboard-widget-primary-value">{`S${currentRankState.tier} · ${currentRankState.points}pt`}</strong>
      <p className="dashboard-widget-subline">{store.activeSeason ?? 'シーズン未設定'}</p>
    </>}
    {widget.type === 'winRate' && <>
      <div className="dashboard-widget-heading"><div><span className="widget-kicker">BATTLE RECORD</span><h3>勝率</h3></div><span className="dashboard-widget-icon"><Trophy size={18}/></span></div>
      <div className="widget-period-tabs" aria-label="勝率の集計期間">{(['today', 'month', 'all'] as DashboardPeriod[]).map(value => <button type="button" key={value} className={period === value ? 'active' : ''} onClick={() => onUpdate(widget.id, { period: value })}>{value === 'today' ? '今日' : value === 'month' ? '今月' : '全体'}</button>)}</div>
      <strong className="dashboard-widget-primary-value">{winRate}</strong>
      <p className="dashboard-widget-subline">{periodMatches.length}試合 · {resultText}</p>
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
      <div className="dashboard-widget-heading"><div><span className="widget-kicker">HERO PROFILE</span><h3>{hero?.name ?? 'ヒーロー情報'}</h3></div>{hero && <span className="hero-role-chip">{hero.role}</span>}</div>
      {hero ? <>
        <div className="hero-info-metrics"><div><span>勝率</span><strong>{heroRate}</strong></div><div><span>使用数</span><strong>{heroBattles.toLocaleString()}回</strong></div><div><span>勝ち数</span><strong>{heroWins.toLocaleString()}勝</strong></div></div>
        <div className="hero-title-progress"><div className="hero-title-progress-label"><span>{heroBattles >= 10000 ? `万戦${hero.name}使い 達成` : heroBattles >= 5000 ? `殿堂入り${hero.name}使い 達成` : heroBattles >= 1000 ? `${hero.name}使い 達成` : `${hero.name}使いまであと${remaining.toLocaleString()}戦`}</span><strong>{Math.floor(progress)}%</strong></div><div className="hero-title-progress-track"><span style={{ width: `${progress}%` }}/></div>
          {heroBattles >= 10000 ? <small>万戦称号を達成しています。</small> : heroBattles >= 5000 ? <small>万戦{hero.name}使いまであと{remaining.toLocaleString()}戦</small> : heroBattles >= 1000 ? <small>殿堂入りまであと{remaining.toLocaleString()}戦 · 万戦まであと{(10000 - heroBattles).toLocaleString()}戦</small> : <small>1,000回使用で「{hero.name}使い」を獲得</small>}
        </div>
      </> : <p className="dashboard-widget-empty">編集画面から表示するヒーローを選択してください。</p>}
    </>}
    {widget.type === 'note' && <>
      {widget.showHeading && widget.heading?.trim() && <span className="note-widget-heading">{widget.heading}</span>}
      <p className={`note-widget-body ${widget.body?.trim() ? '' : 'is-empty'}`}>{widget.body?.trim() || '編集画面から目標やメモを入力できます。'}</p>
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
if component_anchor not in app:
    raise RuntimeError('NavItem component anchor missing')
app = app.replace(component_anchor, widget_component + component_anchor, 1)

# 10) Update icon imports.
old_import = "import { Activity, BarChart3, CalendarDays, ChevronDown, Download, FileUp, Gauge, History, Lock, Minus, Pencil, Plus, Search, Settings, Shield, Star, Sun, Moon, Swords, Trash2, Trophy, Unlock, X } from 'lucide-react'"
new_import = "import { Activity, BarChart3, CalendarDays, ChevronDown, ChevronUp, Download, FileUp, Gauge, GripVertical, History, LayoutDashboard, Lock, Menu, Minus, Pencil, Plus, Search, Settings, Shield, Star, Sun, Moon, Swords, Trash2, Trophy, Unlock, X } from 'lucide-react'"
app = app.replace(old_import, new_import, 1)

# 11) Add the matching premium, responsive layout styles.
css_addition = r'''

/* COMPASS DASHBOARD CUSTOMIZATION v1 */
.topbar { gap: 14px; }
.topbar-actions { display: flex; align-items: center; justify-content: flex-end; gap: 9px; min-width: 0; }
.dashboard-edit-trigger { display: inline-flex; align-items: center; justify-content: center; gap: 7px; min-height: 38px; padding: 8px 12px; white-space: nowrap; }
.dashboard-widget-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); grid-auto-flow: row; gap: 15px; align-items: stretch; }
.dashboard-widget-card { position: relative; min-width: 0; min-height: 174px; padding: 20px 21px; border: 1px solid var(--line, #303951); border-radius: 16px; background: var(--surface, #131b2e); color: var(--text-main, #edf3fb); box-shadow: 0 8px 28px var(--shadow, #0002); overflow: hidden; }
.dashboard-widget-card::before { content: ''; position: absolute; inset: 0 auto auto 0; height: 2px; width: 54px; background: var(--accent, #19c8d8); opacity: .9; }
.dashboard-widget-card.is-wide { grid-column: 1 / -1; }
.dashboard-widget-card.is-tall { min-height: 350px; }
.dashboard-widget-heading { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 13px; }
.dashboard-widget-heading h3 { margin: 4px 0 0; color: var(--text-main, #edf3fb); font-size: 13px; font-weight: 750; letter-spacing: -.015em; }
.widget-kicker { display: block; color: var(--text-muted, #8794aa); font-size: 8px; font-weight: 800; letter-spacing: .15em; }
.dashboard-widget-icon { display: grid; place-items: center; flex: 0 0 34px; width: 34px; height: 34px; border: 1px solid var(--accent-line, #2e6470); border-radius: 11px; background: var(--accent-soft, #14313a); color: var(--accent-strong, #35d4e4); }
.dashboard-widget-primary-value { display: block; margin: 15px 0 5px; color: var(--text-main, #fff); font-size: clamp(25px, 2.5vw, 34px); font-weight: 800; letter-spacing: -.045em; line-height: 1.2; }
.dashboard-widget-subline { margin: 7px 0 0; color: var(--text-muted, #96a2b8); font-size: 10px; line-height: 1.65; }
.widget-period-tabs { display: inline-flex; align-items: center; gap: 4px; padding: 3px; border: 1px solid var(--line, #303951); border-radius: 9px; background: var(--surface-raised, #0e1526); }
.widget-period-tabs button { border: 0; border-radius: 6px; padding: 5px 10px; background: transparent; color: var(--text-muted, #8e9bb0); font-size: 9px; font-weight: 700; }
.widget-period-tabs button.active { background: var(--accent-soft, #15363e); color: var(--accent-strong, #42d8e7); box-shadow: inset 0 0 0 1px var(--accent-line, #2c6872); }
.popular-hero-list { display: grid; gap: 7px; margin-top: 11px; }
.popular-hero-row { display: grid; grid-template-columns: 22px minmax(0, 1fr) auto; align-items: center; gap: 8px; min-width: 0; padding: 7px 9px; border: 1px solid var(--line, #29354b); border-radius: 9px; background: var(--surface-raised, #0f1729); }
.popular-hero-rank { display: grid; place-items: center; width: 20px; height: 20px; border-radius: 6px; background: var(--accent-soft, #15363e); color: var(--accent-strong, #42d8e7); font-size: 9px; font-weight: 800; }
.popular-hero-row strong { overflow: hidden; color: var(--text-main, #edf3fb); font-size: 10px; text-overflow: ellipsis; white-space: nowrap; }
.popular-hero-row > span:last-child { color: var(--text-muted, #93a0b5); font-size: 9px; font-variant-numeric: tabular-nums; }
.dashboard-widget-empty { margin: 20px 0 6px; color: var(--text-muted, #8794aa); font-size: 10px; line-height: 1.8; }
.hero-role-chip { padding: 5px 9px; border: 1px solid var(--accent-line, #2e6470); border-radius: 999px; background: var(--accent-soft, #14313a); color: var(--accent-strong, #35d4e4); font-size: 9px; font-weight: 700; }
.hero-info-metrics { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 9px; margin: 12px 0 17px; }
.hero-info-metrics > div { display: grid; gap: 5px; min-width: 0; padding: 11px 13px; border: 1px solid var(--line, #29354b); border-radius: 10px; background: var(--surface-raised, #0f1729); }
.hero-info-metrics span { color: var(--text-muted, #8d9ab0); font-size: 9px; }
.hero-info-metrics strong { overflow: hidden; color: var(--text-main, #f2f6fb); font-size: 20px; font-weight: 800; text-overflow: ellipsis; white-space: nowrap; }
.hero-title-progress { display: grid; gap: 7px; }
.hero-title-progress-label { display: flex; justify-content: space-between; align-items: center; gap: 10px; color: var(--text-main, #e9eff8); font-size: 10px; font-weight: 700; }
.hero-title-progress-label strong { color: var(--accent-strong, #42d8e7); font-variant-numeric: tabular-nums; }
.hero-title-progress-track { height: 7px; overflow: hidden; border-radius: 999px; background: var(--surface-muted, #273149); }
.hero-title-progress-track span { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, var(--accent, #17b9d0), var(--accent-strong, #44dce8)); transition: width .2s ease; }
.hero-title-progress small { color: var(--text-muted, #91a0b6); font-size: 9px; }
.note-widget-heading { display: block; margin-bottom: 12px; color: var(--text-muted, #8c9ab1); font-size: 10px; font-weight: 800; letter-spacing: .04em; }
.note-widget-body { margin: 0; color: var(--text-main, #eaf0f8); font-size: 12px; line-height: 1.9; white-space: pre-wrap; overflow-wrap: anywhere; }
.note-widget-body.is-empty { color: var(--text-muted, #8c9ab1); }
.monthly-widget-track { display: flex; gap: 9px; overflow-x: auto; overscroll-behavior-x: contain; scroll-snap-type: x mandatory; scrollbar-width: thin; padding: 1px 1px 9px; -webkit-overflow-scrolling: touch; }
.monthly-widget-month { display: grid; grid-template-columns: 1fr auto; align-content: start; gap: 5px 8px; flex: 0 0 100%; min-width: 0; padding: 14px; border: 1px solid var(--line, #29354b); border-radius: 11px; background: var(--surface-raised, #0f1729); scroll-snap-align: start; }
.monthly-widget-month > strong { color: var(--text-main, #edf3fb); font-size: 13px; }
.monthly-widget-month > span { color: var(--text-muted, #8d9ab0); font-size: 9px; text-align: right; }
.monthly-widget-rate { grid-column: 1 / -1; color: var(--accent-strong, #42d8e7); font-size: 26px; font-weight: 850; letter-spacing: -.04em; }
.monthly-widget-month small { grid-column: 1 / -1; color: var(--text-muted, #8d9ab0); font-size: 9px; }
.monthly-widget-hint { margin: 5px 0 0; color: var(--text-muted, #8794aa); font-size: 8px; text-align: right; }
.widget-monthly { min-height: 245px; }
.widget-recentMatches { min-height: 350px; }
.recent-widget-list { display: grid; }
.recent-widget-row { display: grid; grid-template-columns: 116px minmax(0, 1fr) auto; align-items: center; gap: 13px; min-width: 0; padding: 12px 4px; border-top: 1px solid var(--line, #29354b); }
.recent-widget-date { color: var(--text-muted, #8c9ab0); font-size: 9px; font-variant-numeric: tabular-nums; white-space: nowrap; }
.recent-widget-main { display: grid; min-width: 0; gap: 4px; }
.recent-widget-main strong { overflow: hidden; color: var(--text-main, #edf3fb); font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.recent-widget-main span { overflow: hidden; color: var(--text-muted, #8c9ab0); font-size: 9px; text-overflow: ellipsis; white-space: nowrap; }
.dashboard-empty-layout { display: grid; grid-column: 1 / -1; place-items: center; gap: 9px; min-height: 190px; padding: 24px; border: 1px dashed var(--line, #35445d); border-radius: 15px; color: var(--text-muted, #8d9ab0); text-align: center; }
.dashboard-empty-layout strong { color: var(--text-main, #edf3fb); font-size: 13px; }
.dashboard-empty-layout span { font-size: 10px; }

.dashboard-editor-backdrop { position: fixed; inset: 0; z-index: 30; display: grid; place-items: center; padding: 22px; background: rgba(3, 8, 17, .72); backdrop-filter: blur(9px); -webkit-backdrop-filter: blur(9px); }
.dashboard-editor-modal { display: flex; flex-direction: column; width: min(980px, 100%); max-height: min(92vh, 920px); overflow: hidden; border: 1px solid var(--line, #35435b); border-radius: 20px; background: var(--surface, #121b2e); color: var(--text-main, #edf3fb); box-shadow: 0 28px 100px rgba(0,0,0,.48); }
.dashboard-editor-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 18px; padding: 23px 25px 18px; border-bottom: 1px solid var(--line, #2a354b); }
.dashboard-editor-eyebrow { color: var(--accent-strong, #42d8e7); font-size: 8px; font-weight: 850; letter-spacing: .17em; }
.dashboard-editor-header h2 { margin: 6px 0 4px; color: var(--text-main, #edf3fb); font-size: 19px; letter-spacing: -.025em; }
.dashboard-editor-header p { margin: 0; color: var(--text-muted, #8d9ab0); font-size: 10px; }
.dashboard-editor-close { flex: 0 0 36px; width: 36px; height: 36px; }
.dashboard-editor-tabs { display: flex; gap: 7px; padding: 13px 25px; border-bottom: 1px solid var(--line, #2a354b); }
.dashboard-editor-tabs button { display: inline-flex; align-items: center; justify-content: center; gap: 7px; min-height: 36px; padding: 8px 13px; border: 1px solid transparent; border-radius: 9px; background: transparent; color: var(--text-muted, #8d9ab0); font-size: 10px; font-weight: 750; }
.dashboard-editor-tabs button.active { border-color: var(--accent-line, #2e6470); background: var(--accent-soft, #14313a); color: var(--accent-strong, #42d8e7); }
.dashboard-editor-content { min-height: 0; overflow: auto; padding: 20px 25px 24px; }
.dashboard-editor-section + .dashboard-editor-section { margin-top: 24px; }
.dashboard-editor-section-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
.dashboard-editor-section-heading h3 { margin: 0 0 5px; color: var(--text-main, #edf3fb); font-size: 12px; }
.dashboard-editor-section-heading p { margin: 0; color: var(--text-muted, #8d9ab0); font-size: 9px; line-height: 1.6; }
.editor-count { flex: 0 0 auto; padding: 5px 9px; border: 1px solid var(--line, #303951); border-radius: 999px; color: var(--text-muted, #96a3b8); font-size: 9px; }
.dashboard-editor-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.dashboard-editor-widget { min-width: 0; padding: 13px; border: 1px solid var(--line, #2c374f); border-radius: 12px; background: var(--surface-raised, #10182a); transition: border-color .15s, opacity .15s, transform .15s; }
.dashboard-editor-widget.wide { grid-column: 1 / -1; }
.dashboard-editor-widget.is-dragging, .menu-editor-item.is-dragging { opacity: .55; border-color: var(--accent, #19c8d8); transform: scale(.99); }
.dashboard-editor-widget-head { display: flex; align-items: center; gap: 9px; min-width: 0; }
.editor-drag-handle { display: grid; place-items: center; flex: 0 0 30px; width: 30px; height: 32px; padding: 0; border: 1px solid var(--line, #344158); border-radius: 8px; background: var(--surface, #131d31); color: var(--text-muted, #96a3b8); cursor: grab; touch-action: none; }
.editor-drag-handle:active { cursor: grabbing; color: var(--accent-strong, #42d8e7); border-color: var(--accent-line, #2e6470); }
.dashboard-editor-widget-title { display: grid; flex: 1 1 auto; min-width: 0; gap: 3px; }
.dashboard-editor-widget-title strong { color: var(--text-main, #edf3fb); font-size: 10px; }
.dashboard-editor-widget-title span { color: var(--text-muted, #8d9ab0); font-size: 8px; }
.editor-widget-actions { display: inline-flex; align-items: center; gap: 3px; flex: 0 0 auto; }
.compact-editor-action { width: 28px; height: 28px; min-width: 28px; padding: 5px; border-radius: 7px; }
.compact-editor-action:disabled { opacity: .28; cursor: default; }
.remove-editor-action { color: #ec8491; }
.editor-widget-settings { display: grid; gap: 7px; margin: 12px 0 1px 39px; }
.editor-widget-settings > label:not(.editor-heading-toggle) { color: var(--text-muted, #96a3b8); font-size: 9px; font-weight: 700; }
.editor-widget-settings select, .editor-widget-settings input:not([type='checkbox']), .editor-widget-settings textarea { width: 100%; min-width: 0; padding: 9px 10px; border: 1px solid var(--line, #354158); border-radius: 8px; outline: none; background: var(--surface, #121b2e); color: var(--text-main, #edf3fb); font-size: 10px; }
.editor-widget-settings select:focus, .editor-widget-settings input:focus, .editor-widget-settings textarea:focus { border-color: var(--accent, #19c8d8); box-shadow: 0 0 0 3px var(--accent-soft, #14313a); }
.editor-heading-toggle { display: inline-flex; align-items: center; gap: 7px; color: var(--text-soft, #c0c9d8); font-size: 9px; }
.editor-heading-toggle input { accent-color: var(--accent, #19c8d8); }
.note-editor-settings textarea { resize: vertical; line-height: 1.6; }
.editor-no-widgets { grid-column: 1 / -1; padding: 24px; border: 1px dashed var(--line, #354158); border-radius: 10px; color: var(--text-muted, #8d9ab0); font-size: 10px; text-align: center; }
.dashboard-widget-library { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 9px; }
.dashboard-widget-library-item { display: flex; align-items: center; justify-content: space-between; gap: 10px; min-width: 0; padding: 12px; border: 1px solid var(--line, #2c374f); border-radius: 11px; background: var(--surface-raised, #10182a); }
.dashboard-widget-library-item > div { display: grid; min-width: 0; gap: 4px; }
.dashboard-widget-library-item strong { color: var(--text-main, #edf3fb); font-size: 10px; }
.dashboard-widget-library-item span { color: var(--text-muted, #8d9ab0); font-size: 8px; line-height: 1.5; }
.dashboard-widget-library-item small { color: var(--accent-strong, #42d8e7); font-size: 8px; font-weight: 750; }
.dashboard-widget-library-item .secondary-button { display: inline-flex; align-items: center; gap: 4px; flex: 0 0 auto; padding: 7px 9px; font-size: 9px; }
.editor-library-complete { grid-column: 1 / -1; margin: 0; padding: 12px; border-radius: 9px; background: var(--surface-raised, #10182a); color: var(--text-muted, #8d9ab0); font-size: 9px; line-height: 1.7; }
.menu-editor-list { display: grid; gap: 8px; max-width: 680px; }
.menu-editor-item { display: flex; align-items: center; gap: 12px; padding: 11px 13px; border: 1px solid var(--line, #2c374f); border-radius: 11px; background: var(--surface-raised, #10182a); transition: border-color .15s, opacity .15s; }
.menu-editor-icon { display: grid; place-items: center; flex: 0 0 34px; width: 34px; height: 34px; border-radius: 9px; background: var(--accent-soft, #14313a); color: var(--accent-strong, #42d8e7); }
.menu-editor-item > strong { flex: 1 1 auto; color: var(--text-main, #edf3fb); font-size: 11px; }
.dashboard-editor-footer { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 13px 25px; border-top: 1px solid var(--line, #2a354b); background: var(--surface, #121b2e); }
.dashboard-editor-footer > span { display: inline-flex; align-items: center; gap: 7px; color: var(--text-muted, #8d9ab0); font-size: 9px; }
.dashboard-editor-footer .primary-button { min-width: 100px; }

@media (max-width: 760px) {
  .topbar { align-items: flex-start; flex-wrap: wrap; }
  .topbar-actions { width: 100%; justify-content: flex-start; }
  .dashboard-edit-trigger { flex: 1 1 auto; padding: 8px 9px; font-size: 9px; }
  .top-add { flex: 0 0 auto; }
  .dashboard-widget-grid { gap: 9px; }
  .dashboard-widget-card { min-height: 160px; padding: 14px 13px; border-radius: 12px; }
  .dashboard-widget-card.is-tall { min-height: 340px; }
  .dashboard-widget-heading { gap: 7px; margin-bottom: 10px; }
  .dashboard-widget-heading h3 { font-size: 11px; }
  .dashboard-widget-icon { flex-basis: 29px; width: 29px; height: 29px; border-radius: 9px; }
  .dashboard-widget-icon svg { width: 15px; height: 15px; }
  .dashboard-widget-primary-value { margin-top: 12px; font-size: clamp(20px, 6vw, 28px); }
  .dashboard-widget-subline { font-size: 9px; }
  .widget-period-tabs { gap: 2px; }
  .widget-period-tabs button { padding: 5px 7px; font-size: 8px; }
  .popular-hero-list { gap: 5px; margin-top: 8px; }
  .popular-hero-row { grid-template-columns: 19px minmax(0, 1fr) auto; gap: 5px; padding: 6px; }
  .popular-hero-rank { width: 18px; height: 18px; }
  .popular-hero-row strong { font-size: 8px; }
  .popular-hero-row > span:last-child { font-size: 8px; }
  .hero-info-metrics { gap: 6px; margin: 8px 0 12px; }
  .hero-info-metrics > div { padding: 9px 8px; }
  .hero-info-metrics strong { font-size: 16px; }
  .hero-info-metrics span { font-size: 8px; }
  .hero-title-progress-label { font-size: 9px; }
  .hero-title-progress small { font-size: 8px; }
  .note-widget-body { font-size: 10px; }
  .monthly-widget-month { padding: 11px; }
  .monthly-widget-rate { font-size: 23px; }
  .monthly-widget-month small { font-size: 8px; }
  .recent-widget-row { grid-template-columns: minmax(75px, 90px) minmax(0, 1fr) auto; gap: 7px; padding: 10px 0; }
  .recent-widget-date { font-size: 8px; }
  .recent-widget-main strong { font-size: 9px; }
  .recent-widget-main span { font-size: 8px; }
  .recent-widget-row .result-pill { padding: 4px 6px; font-size: 8px; }
  .dashboard-editor-backdrop { padding: 8px; place-items: end center; }
  .dashboard-editor-modal { width: 100%; max-height: 94vh; border-radius: 17px 17px 12px 12px; }
  .dashboard-editor-header { padding: 18px 16px 14px; }
  .dashboard-editor-header h2 { font-size: 16px; }
  .dashboard-editor-tabs { padding: 10px 15px; }
  .dashboard-editor-content { padding: 15px; }
  .dashboard-editor-grid, .dashboard-widget-library { grid-template-columns: minmax(0, 1fr); }
  .dashboard-editor-widget.wide { grid-column: auto; }
  .dashboard-editor-widget { padding: 11px; }
  .editor-widget-settings { margin-left: 0; }
  .dashboard-widget-library-item { padding: 10px; }
  .dashboard-editor-footer { padding: 11px 15px; }
  .dashboard-editor-footer > span { font-size: 8px; }
}
@media (max-width: 390px) {
  .topbar-actions { gap: 6px; }
  .dashboard-edit-trigger { font-size: 8px; }
  .top-add { padding: 8px 9px; font-size: 9px; }
  .dashboard-widget-card { padding: 12px 10px; }
  .widget-period-tabs button { padding-inline: 5px; }
  .hero-info-metrics strong { font-size: 14px; }
  .recent-widget-row { grid-template-columns: 72px minmax(0, 1fr) auto; gap: 5px; }
  .recent-widget-date { font-size: 7px; }
}
'''
css = css.rstrip() + '\n\n' + css_addition + '\n'

# Safety checks before writing: all key features must be present exactly once.
checks = [
    "type DashboardWidget = {", "function normalizeDashboardWidgets(value: unknown)",
    "dashboardWidgets: normalizeDashboardWidgets(input?.dashboardWidgets)",
    "function addDashboardWidget(type: DashboardWidgetType)",
    "data-editor-sort-scope=\"home\"", "data-editor-sort-scope=\"menu\"",
    "<DashboardWidgetCard", "function DashboardWidgetCard(", "COMPASS DASHBOARD CUSTOMIZATION v1"
]
missing = [item for item in checks if item not in app + css]
if missing:
    print('安全確認：生成した変更内容に不足があります。ファイルへ書き込んでいません。')
    for item in missing: print(' - ' + item)
    sys.exit(3)

APP.write_text(app, encoding='utf-8')
CSS.write_text(css, encoding='utf-8')
print('改築パッチを適用しました。')
print(f'バックアップ：{backup_dir.relative_to(ROOT)}')
print('変更ファイル：src/App.tsx / src/style-improvements.css')
print('追加内容：メニュー並べ替え、ホーム編集画面、ドラッグ配置、8種類のウィジェット、6か月スライド、ヒーロー称号進捗')
print('Supabaseのテーブル・マイグレーションには変更を加えていません。')
