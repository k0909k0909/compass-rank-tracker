from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path.cwd()
APP_PATH = ROOT / "src" / "App.tsx"
CSS_PATH = ROOT / "src" / "style-improvements.css"

if not APP_PATH.is_file() or not CSS_PATH.is_file():
    raise SystemExit("src/App.tsx と src/style-improvements.css が見つかりません。package.json があるプロジェクトのルートで実行してください。")

app = APP_PATH.read_text(encoding="utf-8")
css = CSS_PATH.read_text(encoding="utf-8")


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"修正箇所「{label}」を一意に特定できません（検出数: {count}）。ファイルはまだ変更していません。")
    return source.replace(old, new, 1)


# 全置換をメモリ上で完了してから、最後にファイルへ反映します。
app = replace_once(
    app,
    "import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'",
    "import { Fragment, createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'",
    "React Fragment import"
)
app = replace_once(
    app,
    "const storageKey = 'compass-rank-tracker-v1'\nconst recordDraftStorageKey = `${storageKey}-record-draft`",
    "const storageKey = 'compass-rank-tracker-v1'\n"
    "const recordDraftStorageKey = `${storageKey}-record-draft`\n"
    "// デモ専用データは通常アカウントの保存領域と分離します。\n"
    "const demoStorageKey = `${storageKey}-demo-v1`\n"
    "const demoRecordDraftStorageKey = `${storageKey}-demo-record-draft`",
    "demo storage keys"
)
app = replace_once(
    app,
    "function loadRecordDraft(): RecordDraft | null {\n  try {\n    const raw = localStorage.getItem(recordDraftStorageKey)",
    "function loadRecordDraft(key = recordDraftStorageKey): RecordDraft | null {\n  try {\n    const raw = localStorage.getItem(key)",
    "separate demo record draft"
)
app = replace_once(
    app,
    "function loadStore(): Store {\n"
    "  try {\n"
    "    const raw = localStorage.getItem(storageKey)\n"
    "    if (raw) return normalizeStore(JSON.parse(raw) as Partial<Store>)\n"
    "  } catch { /* 壊れたローカルデータは初期値で開始 */ }\n"
    "  return freshStore()\n"
    "}\n"
    "function resultLabel(result: Result)",
    """function loadStore(): Store {
  try {
    const raw = localStorage.getItem(storageKey)
    if (raw) return normalizeStore(JSON.parse(raw) as Partial<Store>)
  } catch { /* 壊れたローカルデータは初期値で開始 */ }
  return freshStore()
}

// 紹介用デモには架空の戦績を表示します。Supabaseや通常アカウントには保存しません。
function createDemoStore(): Store {
  const base = freshStore()
  const demoHeroNames = [
    'リリカ', 'ソーン=ユーリエフ', 'Voidoll', 'リリカ', '初音ミク', 'ポロロッチョ',
    'Voidoll', 'リリカ', 'ソーン=ユーリエフ', '初音ミク', 'リリカ', 'ポロロッチョ',
    'ソーン=ユーリエフ', 'Voidoll', 'リリカ', '初音ミク', 'ポロロッチョ', 'リリカ'
  ]
  const resultCycle: Result[] = [
    'win', 'loss', 'win', 'win', 'loss', 'draw', 'win', 'loss', 'win',
    'win', 'loss', 'win', 'draw', 'win', 'loss', 'win', 'win', 'loss'
  ]
  const matches: Match[] = demoHeroNames.map((heroName, index) => {
    const played = new Date()
    played.setDate(played.getDate() - Math.floor(index / 2))
    played.setHours(22 - (index % 2) - Math.floor(index / 4), index % 2 ? 30 : 0, 0, 0)
    const playedAt = new Date(played.getTime() - played.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
    const hero = initialHeroes.find(item => item.name === heroName)
    const result = resultCycle[index % resultCycle.length]
    const mode: Mode = index % 5 === 4 ? 'フリバ' : 'バトアリ'
    const rankChange = mode === 'バトアリ' ? (result === 'win' ? 20 : result === 'loss' ? -20 : 0) : null
    return {
      id: `demo-match-${index + 1}`,
      playedAt,
      season: mode === 'バトアリ' ? seasonLabelFromDate(playedAt) : '',
      heroName,
      heroRole: hero?.role ?? 'アタッカー',
      mapName: initialMaps[(index * 3) % initialMaps.length],
      result,
      rankPoints: null,
      memo: '',
      rankChange,
      mode,
      rankBeforeTier: 5,
      rankBeforePoints: 240,
      rankAfterTier: 5,
      rankAfterPoints: 240 + (rankChange ?? 0)
    }
  })
  const widgets = defaultDashboardWidgets.map(widget => {
    if (widget.id === 'hero-info') return { ...widget, heroName: 'リリカ' }
    if (widget.id === 'personal-note') return { ...widget, body: '○○までに○○使いを目指す' }
    return { ...widget }
  })
  return normalizeStore({
    ...base,
    matches,
    initialRankPoints: 2240,
    currentRankTier: 5,
    currentRankPoints: 240,
    activeSeason: seasonLabelFromDate(nowLocalInput()),
    heroBaseStats: {
      'リリカ': { battles: 180, wins: 96 },
      'ソーン=ユーリエフ': { battles: 95, wins: 48 },
      'Voidoll': { battles: 72, wins: 39 },
      '初音ミク': { battles: 55, wins: 31 }
    },
    dashboardWidgets: widgets
  })
}

function loadDemoStore(): Store {
  try {
    const raw = localStorage.getItem(demoStorageKey)
    if (raw) return normalizeStore(JSON.parse(raw) as Partial<Store>)
  } catch { /* デモ用データが壊れている場合はサンプルを再作成 */ }
  return createDemoStore()
}
function resultLabel(result: Result)""",
    "isolated demo store"
)
app = replace_once(
    app,
    "function TrackerApp() {\n"
    "  const cloud = useContext(CloudContext)\n"
    "  const [store, setStore] = useState<Store>(loadStore)\n"
    "  const storeRef = useRef(store)\n"
    "  const savedDraft = useMemo(() => loadRecordDraft(), [])",
    "function TrackerApp({ demoMode = false }: { demoMode?: boolean } = {}) {\n"
    "  const cloud = useContext(CloudContext)\n"
    "  const activeRecordDraftKey = demoMode ? demoRecordDraftStorageKey : recordDraftStorageKey\n"
    "  const [store, setStore] = useState<Store>(() => demoMode ? loadDemoStore() : loadStore())\n"
    "  const storeRef = useRef(store)\n"
    "  const savedDraft = useMemo(() => loadRecordDraft(activeRecordDraftKey), [activeRecordDraftKey])",
    "TrackerApp demo initialization"
)
app = replace_once(
    app,
    "  useEffect(() => { localStorage.setItem(storageKey, JSON.stringify(store)); cloud?.saveCloudStore(store) }, [store])",
    "  useEffect(() => {\n"
    "    try { localStorage.setItem(demoMode ? demoStorageKey : storageKey, JSON.stringify(store)) } catch { /* 保存領域が利用できない場合は省略 */ }\n"
    "    if (!demoMode) cloud?.saveCloudStore(store)\n"
    "  }, [store])",
    "isolate demo saves"
)
app = replace_once(
    app,
    "      localStorage.setItem(recordDraftStorageKey, JSON.stringify({",
    "      localStorage.setItem(activeRecordDraftKey, JSON.stringify({",
    "isolate demo drafts"
)
app = replace_once(
    app,
    "  }, [page, form, editingId, recordSlide, lockAlly1, lockAlly2, rankTierDraft, rankPointsDraft, selectedHeroDetailName])",
    "  }, [page, form, editingId, recordSlide, lockAlly1, lockAlly2, rankTierDraft, rankPointsDraft, selectedHeroDetailName, activeRecordDraftKey])",
    "demo draft dependency"
)
app = replace_once(
    app,
    "notify(type === 'heroInfo' ? '指定ヒーロー情報は最大3体まで登録できます。' : '自由記載は最大3件まで登録できます。')",
    "notify(type === 'heroInfo' ? 'ヒーローの情報は最大3体まで登録できます。' : 'メモ等は最大3件まで登録できます。')",
    "widget limit wording"
)
app = replace_once(
    app,
    "{ type: 'heroInfo', label: '指定ヒーローの情報', description: '最大3体を横スライド。ホーム上で検索・変更可能', size: '横2' },",
    "{ type: 'heroInfo', label: 'ヒーローの情報', description: '1件は横1。2件以上は横スライドで表示。ホーム上で変更可能', size: '横1／複数時は横2' },",
    "hero editor label"
)
app = replace_once(
    app,
    "{ type: 'note', label: '自由記載', description: '最大3件を横スライド。ホーム上で編集可能', size: '横2' },",
    "{ type: 'note', label: 'メモ等', description: '1件は横1。2件以上は横スライドで表示。ホーム上で編集可能', size: '横1／複数時は横2' },",
    "note editor label"
)
app = replace_once(app, "<span>ヒーロー情報・自由記載は各3件まで</span>", "<span>ヒーローの情報・メモ等は各3件まで</span>", "add panel labels")
app = replace_once(app, "追加できる項目はありません。ヒーロー情報と自由記載は最大3件まで登録できます。", "追加できる項目はありません。ヒーローの情報とメモ等は最大3件まで登録できます。", "add panel empty text")
app = replace_once(app, "追加できる標準項目はすべて配置済みです。ヒーロー情報と自由記載は複数追加できます。", "追加できる標準項目はすべて配置済みです。ヒーローの情報とメモ等は複数追加できます。", "editor library text")
old_note_placeholder = 'placeholder="自由に記載できます。例：11月中にリリカ使いを達成する"'
if app.count(old_note_placeholder) != 2:
    raise RuntimeError("メモの例文を2か所で確認できません。ファイルはまだ変更していません。")
app = app.replace(old_note_placeholder, 'placeholder="例：○○までに○○使いを達成する"')
app = replace_once(
    app,
    "            const wide = widget.type === 'heroInfo' || widget.type === 'note' || widget.type === 'recentMatches'",
    "            const wide = (repeatableGroup && group.length > 1) || widget.type === 'recentMatches'",
    "group width when one item"
)
old_group = """            return <div key={key} data-dashboard-widget-id={widget.id} className={`dashboard-widget-sortable ${wide ? 'is-wide' : ''} ${tall ? 'is-tall' : ''} ${dashboardDraggingId === widget.id ? 'is-dragging' : ''} ${dashboardDropTargetId === widget.id ? 'is-drop-target' : ''}`}>
              <DashboardWidgetCard widget={widget} carouselWidgets={group} store={store} currentRankState={currentRankState}
                sortedMatches={sortedMatches} monthlyStats={monthlyStats} editMode={dashboardEditMode}
                onUpdate={updateDashboardWidget} onRemove={removeDashboardWidget} onOpenHistory={() => setPage('history')}
                onDragStart={handleDashboardDragStart} onDragMove={handleDashboardDragMove} onDragEnd={handleDashboardDragEnd} onDragCancel={handleDashboardDragCancel}
              />
            </div>"""
new_group = """            return <Fragment key={key}>
              <div data-dashboard-widget-id={widget.id} className={`dashboard-widget-sortable ${wide ? 'is-wide' : ''} ${tall ? 'is-tall' : ''} ${dashboardDraggingId === widget.id ? 'is-dragging' : ''} ${dashboardDropTargetId === widget.id ? 'is-drop-target' : ''}`}>
                <DashboardWidgetCard widget={widget} carouselWidgets={group} store={store} currentRankState={currentRankState}
                  sortedMatches={sortedMatches} monthlyStats={monthlyStats} editMode={dashboardEditMode}
                  onUpdate={updateDashboardWidget} onRemove={removeDashboardWidget} onOpenHistory={() => setPage('history')}
                  onDragStart={handleDashboardDragStart} onDragMove={handleDashboardDragMove} onDragEnd={handleDashboardDragEnd} onDragCancel={handleDashboardDragCancel}
                />
              </div>
              {repeatableGroup && group.length === 1 && <div className="dashboard-widget-add-tile">
                <button type="button" aria-label={widget.type === 'heroInfo' ? 'ヒーローの情報を追加' : 'メモ等を追加'} onClick={() => addDashboardWidget(widget.type)}>
                  <Plus size={23}/><span>追加</span>
                </button>
              </div>}
            </Fragment>"""
app = replace_once(app, old_group, new_group, "single widget add tile")
app = replace_once(
    app,
    "  const wide = widget.type === 'heroInfo' || widget.type === 'note' || widget.type === 'recentMatches'",
    "  const wide = ((widget.type === 'heroInfo' || widget.type === 'note') && slides.length > 1) || widget.type === 'recentMatches'",
    "card width when one item"
)
app = replace_once(app, "<h3>指定ヒーローの情報</h3>", "<h3>ヒーローの情報</h3>", "hero heading")
app = replace_once(
    app,
    '<div className="dashboard-widget-heading note-widget-header"><div><span className="widget-kicker">PERSONAL NOTE</span><h3>{currentSlide.showHeading && currentSlide.heading?.trim() ? currentSlide.heading : \'自由記載\'}</h3></div><button type="button" className="icon-button note-edit-trigger" aria-label="自由記載を編集" title="内容を編集" onClick={() => setNoteEditing(current => !current)}><Pencil size={15}/></button></div>',
    '<div className="dashboard-widget-heading note-widget-header"><div>{currentSlide.showHeading && currentSlide.heading?.trim() ? <h3>{currentSlide.heading}</h3> : null}</div><button type="button" className="icon-button note-edit-trigger" aria-label="メモを編集" title="内容を編集" onClick={() => setNoteEditing(current => !current)}><Pencil size={15}/></button></div>',
    "hide note category on home"
)
app = replace_once(
    app,
    '<span>{slideIndex + 1} / {slides.length}</span><button type="button" aria-label="次のヒーロー" onClick={() => changeSlide(1)}><ChevronRight size={16}/></button></div></div>}',
    '<span>{slideIndex + 1} / {slides.length}</span><button type="button" aria-label="次のヒーロー" onClick={() => changeSlide(1)}><ChevronRight size={16}/></button><button type="button" className="icon-button widget-carousel-remove" aria-label="表示中のヒーロー情報を削除" title="このヒーロー情報を削除" onClick={() => onRemove?.(currentSlide.id)}><Trash2 size={14}/></button></div></div>}',
    "hero carousel delete button"
)
app = replace_once(app, 'aria-label="前の自由記載"', 'aria-label="前のメモ"', 'note previous slide accessible label')

app = replace_once(
    app,
    '<span>{slideIndex + 1} / {slides.length}</span><button type="button" aria-label="次の自由記載" onClick={() => changeSlide(1)}><ChevronRight size={16}/></button></div></div>}',
    '<span>{slideIndex + 1} / {slides.length}</span><button type="button" aria-label="次のメモ" onClick={() => changeSlide(1)}><ChevronRight size={16}/></button><button type="button" className="icon-button widget-carousel-remove" aria-label="表示中のメモを削除" title="このメモを削除" onClick={() => onRemove?.(currentSlide.id)}><Trash2 size={14}/></button></div></div>}',
    "note carousel delete button"
)
app = replace_once(
    app,
    "  const [mode, setMode] = useState<'login' | 'signup'>('login')\n  const [message, setMessage] = useState('')",
    "  const [mode, setMode] = useState<'login' | 'signup'>('login')\n  const [demoMode, setDemoMode] = useState(false)\n  const [message, setMessage] = useState('')",
    "demo login state"
)
app = replace_once(
    app,
    "    e.preventDefault(); setMessage('')\n    if (!supabase) return",
    "    e.preventDefault(); setMessage('')\n"
    "    // dummyログインはSupabase認証ではなく、分離された端末内デモだけを開きます。\n"
    "    if (mode === 'login' && email.trim().toLowerCase() === 'dummy' && password === '01100011') {\n"
    "      setDemoMode(true)\n"
    "      setMessage('')\n"
    "      return\n"
    "    }\n"
    "    if (!supabase) return",
    "demo login credential route"
)
app = replace_once(
    app,
    "  if (!supabase) return <div className=\"auth-shell\">",
    "  if (demoMode) return <><div className=\"cloud-user-bar demo-user-bar\">{themeToggle}<span>デモモード · サンプルデータはこの端末内だけに保存されます</span><button type=\"button\" onClick={() => setDemoMode(false)}>デモを終了</button></div><TrackerApp demoMode /></>\n"
    "  if (!supabase) return <div className=\"auth-shell\">",
    "demo mode render"
)
app = replace_once(
    app,
    '<input type="email" required autoComplete="email" value={email} onChange={e => setEmail(e.target.value)} />',
    '<input type="text" inputMode="email" required autoComplete="email" placeholder="メールアドレスまたは dummy" value={email} onChange={e => setEmail(e.target.value)} />',
    "allow dummy login ID"
)

marker = "/* HOME REPEATABLE WIDGETS + LOCAL DEMO MODE v1 */"
if marker in css:
    raise RuntimeError("CSSには今回の改修マーカーがすでにあります。二重適用を中止しました。")
css_addition = r'''

/* HOME REPEATABLE WIDGETS + LOCAL DEMO MODE v1 */
.dashboard-widget-add-tile { min-width: 0; min-height: 174px; display: flex; }
.dashboard-widget-add-tile button {
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px;
  width: 100%; min-width: 0; min-height: 174px; padding: 14px;
  border: 1px dashed var(--accent-line, #2e6470); border-radius: 16px;
  background: var(--surface, #131b2e); color: var(--accent-strong, #35d4e4);
  font-size: 10px; font-weight: 800; transition: background .15s, border-color .15s;
}
.dashboard-widget-add-tile button:hover { border-color: var(--accent, #39e6f2); background: var(--accent-soft, #14313a); }
.widget-carousel-remove { flex: 0 0 28px; width: 28px; height: 27px; min-width: 28px; padding: 4px; border: 1px solid var(--line, #293c4b); color: #e98796; }
.widget-carousel-remove:hover { border-color: #a34b60; background: #482b3c; color: #ffc0ca; }
.note-widget-header > div { min-width: 0; flex: 1 1 auto; }
.demo-user-bar { gap: 12px; }
.demo-user-bar > span { flex: 1 1 auto; text-align: right; }
.demo-user-bar button { white-space: nowrap; }
@media (max-width: 760px) {
  .dashboard-widget-add-tile, .dashboard-widget-add-tile button { min-height: 160px; }
  .dashboard-widget-add-tile button { border-radius: 12px; }
  .demo-user-bar { gap: 7px; padding-inline: 9px; font-size: 8px; }
  .demo-user-bar > span { text-align: left; line-height: 1.45; }
  .demo-user-bar button { padding: 5px 7px; font-size: 8px; }
}
'''
css = css.rstrip() + "\n" + css_addition

# すべての置換が成功した後でバックアップを作成し、2ファイルを更新します。
backup_dir = ROOT / ".patch-backups"
backup_dir.mkdir(exist_ok=True)
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
shutil.copy2(APP_PATH, backup_dir / f"App.tsx.before-home-demo-{stamp}")
shutil.copy2(CSS_PATH, backup_dir / f"style-improvements.css.before-home-demo-{stamp}")
APP_PATH.write_text(app, encoding="utf-8")
CSS_PATH.write_text(css, encoding="utf-8")

print("改修を適用しました。")
print("変更ファイル: src/App.tsx / src/style-improvements.css")
print("バックアップ: .patch-backups/")
print("- 表示名を「ヒーローの情報」「メモ等」に変更")
print("- メモの分類名をホーム画面から非表示")
print("- 例文を「○○までに○○使いを達成する」に変更")
print("- 1件時は横1カード＋追加タイル、2件以上は従来の横スライド")
print("- スライド中の項目を削除できるボタンを追加")
print("- dummy / 01100011 は端末内サンプルデータだけを開くデモログイン")
print("次は npm run build で確認してください。")
