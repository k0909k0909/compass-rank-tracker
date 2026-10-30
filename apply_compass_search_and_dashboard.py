from pathlib import Path
from datetime import datetime
import shutil
import sys

ROOT = Path.cwd()
APP = ROOT / 'src' / 'App.tsx'
THEME = ROOT / 'src' / 'theme.css'

if not APP.exists() or not THEME.exists():
    raise SystemExit('src/App.tsx または src/theme.css が見つかりません。リポジトリ直下で実行してください。')

app = APP.read_text(encoding='utf-8')
theme = THEME.read_text(encoding='utf-8')
original_app, original_theme = app, theme


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'適用を中止しました：{label} の一致箇所が {count} 件です。ファイルはまだ変更していません。')
    return text.replace(old, new, 1)


def replace_between(text: str, start: str, end: str, replacement: str, label: str) -> str:
    if text.count(start) != 1 or text.count(end) != 1:
        raise SystemExit(f'適用を中止しました：{label} の開始・終了位置を一意に特定できません。ファイルはまだ変更していません。')
    i = text.index(start)
    j = text.index(end, i)
    if j < i:
        raise SystemExit(f'適用を中止しました：{label} の位置関係が想定と異なります。ファイルはまだ変更していません。')
    return text[:i] + replacement + text[j:]

# 1) Hero aliases are stored in the existing synced/backed-up Hero object.
app = replace_once(
    app,
    "type Hero = { name: string; role: Role; favorite?: boolean }",
    "type Hero = { name: string; role: Role; favorite?: boolean; aliases?: string[] }",
    'Hero型への略称フィールド追加',
)

# 2) Add shared kana-normalized matching helper and a compact searchable dropdown.
helper = r'''function normalizeHeroSearchText(value: string) {
  return value.normalize('NFKC')
    .toLocaleLowerCase()
    .replace(/[\u30a1-\u30f6]/g, character => String.fromCharCode(character.charCodeAt(0) - 0x60))
    .replace(/[\s\u3000]/g, '')
}
function heroMatchesSearch(hero: Hero, query: string) {
  const needle = normalizeHeroSearchText(query)
  if (!needle) return true
  return [hero.name, ...(hero.aliases ?? [])].some(value => normalizeHeroSearchText(value).includes(needle))
}
'''
app = replace_once(app, 'function TrackerApp() {', helper + '\nfunction TrackerApp() {', '検索用かな正規化関数')

# 3) Remove obsolete home win-rate mode/limit and top hero search state/ref.
app = replace_once(app, "  const [dashboardWinMode, setDashboardWinMode] = useState<Mode>('バトアリ')\n  const [dashboardWinLimit, setDashboardWinLimit] = useState<'all' | '10' | '20' | '50' | '100'>('all')\n", '', 'ホーム勝率フィルター状態の削除')
app = replace_once(app, "  const [heroSearch, setHeroSearch] = useState('')\n", '', '個別検索欄の状態削除')
count_reset = app.count("    setHeroSearch('')\n")
if count_reset != 3:
    raise SystemExit(f'適用を中止しました：画面切替時の heroSearch リセット箇所が {count_reset} 件です。ファイルはまだ変更していません。')
app = app.replace("    setHeroSearch('')\n", '', 3)
app = replace_once(app, "  const heroSelectRef = useRef<HTMLSelectElement>(null)\n", '', 'ネイティブセレクト参照の削除')

old_derived = """  const dashboardWinMatches = useMemo(() => {
    const byMode = sortedMatches.filter(match => (match.mode ?? 'バトアリ') === dashboardWinMode)
    return dashboardWinLimit === 'all' ? byMode : byMode.slice(0, Number(dashboardWinLimit))
  }, [sortedMatches, dashboardWinMode, dashboardWinLimit])
  const dashboardWins = dashboardWinMatches.filter(match => match.result === 'win').length
  const dashboardLosses = dashboardWinMatches.filter(match => match.result === 'loss').length
  const dashboardWinRate = percent(dashboardWins, dashboardWins + dashboardLosses)
"""
new_derived = """  const todayMatches = sortedMatches.filter(match => match.playedAt.slice(0, 10) === today())
  const todayWins = todayMatches.filter(match => match.result === 'win').length
  const todayLosses = todayMatches.filter(match => match.result === 'loss').length
  const todayWinRate = percent(todayWins, todayWins + todayLosses)
  const allWins = store.matches.filter(match => match.result === 'win').length
  const allLosses = store.matches.filter(match => match.result === 'loss').length
  const allTimeWinRate = percent(allWins, allWins + allLosses)
"""
app = replace_once(app, old_derived, new_derived, 'ホーム勝率集計の置換')
app = replace_once(
    app,
    "  const currentMonth = today().slice(0, 7)\n  const currentMonthMatches = store.matches.filter(m => m.playedAt.slice(0, 7) === currentMonth)\n  const currentMonthWins = currentMonthMatches.filter(m => m.result === 'win').length\n  const currentMonthLosses = currentMonthMatches.filter(m => m.result === 'loss').length\n",
    '',
    '今月の試合カード専用集計の削除',
)

# Replace the five home cards in requested 1-2 / 3-4 / 5 order.
start = '        <div className="stats-grid">'
end = '\n        <div className="content-card">\n          <div className="section-heading"><div><h3>最近の試合</h3>'
new_grid = '''        <div className="stats-grid dashboard-stats-grid">
          <div className="stat-card current-rank-stat-card"><div className="stat-top"><span>現在のランク</span><span className="stat-icon"><BarChart3 size={19}/></span></div><strong>{`S${currentRankState.tier} · ${currentRankState.points}pt`}</strong><small>{store.activeSeason ?? 'シーズン未設定'}</small></div>
          <StatCard icon={<Trophy size={19}/>} label="今日の勝率" value={todayWinRate} sub={`${todayWins}勝 · ${todayLosses}敗`} />
          <StatCard icon={<Trophy size={19}/>} label="全体勝率" value={allTimeWinRate} sub={`${allWins}勝 · ${allLosses}敗`} />
          <StatCard icon={<CalendarDays size={19}/>} label="総試合数" value={`${store.matches.length}`} sub="記録した試合" />
          <StatCard icon={<Activity size={19}/>} label="現在の連続結果" value={currentStreak.count ? `${currentStreak.count}${currentStreak.result}` : '—'} sub={`最高連勝：${highestWinStreak}`} />
        </div>'''
app = replace_between(app, start, end, new_grid, 'ホーム統計カード')

# 4) Eliminate the native select opening when search input changes by using the same searchable dropdown component in all pickers.
app = replace_between(
    app,
    '  function openHeroSelect() {',
    '  function changeHeroRoleFilter(role: \'all\' | Role) {',
    '',
    'ネイティブヒーローセレクト自動オープン処理',
)
app = replace_between(
    app,
    '  function changeHeroRoleFilter(role: \'all\' | Role) {',
    '  function toggleFavorite(name: string) {',
    """  function changeHeroRoleFilter(role: 'all' | Role) {
    setHeroRoleFilter(role)
    setForm(old => ({ ...old, heroName: '' }))
  }
  function changeFavoritesOnly(checked: boolean) {
    setFavoritesOnly(checked)
    setForm(old => ({ ...old, heroName: '' }))
  }
""",
    'ヒーロー絞り込み変更時の処理',
)

visible_old = """  const visibleHeroes = useMemo(() => {
    const query = heroSearch.trim().toLocaleLowerCase()
    const isFiltering = Boolean(query) || heroRoleFilter !== 'all' || favoritesOnly
    const lastUsedHeroName = sortedMatches[0]?.heroName
    return store.heroes
      .filter(hero => (heroRoleFilter === 'all' || hero.role === heroRoleFilter)
        && (!favoritesOnly || Boolean(hero.favorite))
        && (!query || hero.name.toLocaleLowerCase().includes(query)))
      .sort((a, b) => {
        if (!isFiltering && lastUsedHeroName) {
          if (a.name === lastUsedHeroName) return -1
          if (b.name === lastUsedHeroName) return 1
        }
        return (heroOrderIndex.get(a.name) ?? Number.MAX_SAFE_INTEGER) - (heroOrderIndex.get(b.name) ?? Number.MAX_SAFE_INTEGER)
      })
  }, [store.heroes, heroSearch, heroRoleFilter, favoritesOnly, sortedMatches])
"""
visible_new = """  const visibleHeroes = useMemo(() => {
    const isFiltering = heroRoleFilter !== 'all' || favoritesOnly
    const lastUsedHeroName = sortedMatches[0]?.heroName
    return store.heroes
      .filter(hero => (heroRoleFilter === 'all' || hero.role === heroRoleFilter)
        && (!favoritesOnly || Boolean(hero.favorite)))
      .sort((a, b) => {
        if (!isFiltering && lastUsedHeroName) {
          if (a.name === lastUsedHeroName) return -1
          if (b.name === lastUsedHeroName) return 1
        }
        return (heroOrderIndex.get(a.name) ?? Number.MAX_SAFE_INTEGER) - (heroOrderIndex.get(b.name) ?? Number.MAX_SAFE_INTEGER)
      })
  }, [store.heroes, heroRoleFilter, favoritesOnly, sortedMatches])
"""
app = replace_once(app, visible_old, visible_new, 'メインヒーロー一覧の実装順ソート')

# Keep the filter area visually compact; the search appears inside the dropdown itself.
app = replace_once(
    app,
    '''<div className="field field-wide hero-picker-controls">
            <div className="hero-search-control"><label>使用ヒーローを検索</label><label className="search-field"><Search size={16}/><input value={heroSearch} onChange={e => handleHeroSearch(e.target.value)} placeholder="ヒーロー名を入力" /></label></div>
            <div className="hero-filter-control"><label>絞込み</label>''',
    '''<div className="field field-wide hero-picker-controls hero-picker-filters-only">
            <div className="hero-filter-control"><label>絞込み</label>''',
    'メインヒーロー検索欄をドロップダウン内へ移動',
)
app = replace_once(
    app,
    '''<div className="field field-wide hero-select-field"><label>使用ヒーロー（{visibleHeroes.length}人）</label>
            <div className="hero-select-row"><select ref={heroSelectRef} className="hero-select" required={recordSlide === 1} value={form.heroName} onChange={e => setForm({ ...form, heroName: e.target.value })}><option value="">—</option>{visibleHeroes.map(h => <option key={h.name} value={h.name}>{h.name}</option>)}</select>''',
    '''<div className="field field-wide hero-select-field"><label>使用ヒーロー（{visibleHeroes.length}人）</label>
            <div className="hero-select-row"><SearchableHeroDropdown value={form.heroName} heroes={visibleHeroes} onChange={name => setForm(old => ({ ...old, heroName: name }))} placeholder="ヒーローを検索・選択" />''',
    'メインヒーロー選択を検索可能なプルダウンへ置換',
)

# Team selections use the same compact dropdown/search, preserving implementation order and optionality.
app = replace_once(
    app,
    '''<select value={form.allyHeroNames[index] ?? ''} onChange={e => setTeamHero('allyHeroNames', index, e.target.value)}><option value="">— 未選択 —</option>{teamHeroOptions.map(hero => <option key={hero.name} value={hero.name}>{hero.name}</option>)}</select>''',
    '''<SearchableHeroDropdown value={form.allyHeroNames[index] ?? ''} heroes={teamHeroOptions} onChange={name => setTeamHero('allyHeroNames', index, name)} placeholder="— 未選択 —" />''',
    '味方ヒーロー選択を検索可能なプルダウンへ置換',
)
app = replace_once(
    app,
    '''<select value={form.enemyHeroNames[index] ?? ''} onChange={e => setTeamHero('enemyHeroNames', index, e.target.value)}><option value="">— 未選択 —</option>{teamHeroOptions.map(hero => <option key={hero.name} value={hero.name}>{hero.name}</option>)}</select>''',
    '''<SearchableHeroDropdown value={form.enemyHeroNames[index] ?? ''} heroes={teamHeroOptions} onChange={name => setTeamHero('enemyHeroNames', index, name)} placeholder="— 未選択 —" />''',
    '敵ヒーロー選択を検索可能なプルダウンへ置換',
)

# Add save button also to the first record slide.
app = replace_once(
    app,
    '''          <div className="record-slide-nav" aria-label="記録ページの移動">
            <div className="record-slide-steps"><span className="record-slide-step active">1 基本情報</span><span className="record-slide-step">2 チーム構成</span></div>
            <button type="button" className="secondary-button" onClick={() => setRecordSlide(2)}>次へ：チーム構成 →</button>
          </div>''',
    '''          <div className="record-slide-nav primary-slide-nav" aria-label="記録ページの移動">
            <div className="record-slide-steps"><span className="record-slide-step active">1 基本情報</span><span className="record-slide-step">2 チーム構成</span></div>
            <div className="record-slide-actions">
              <button type="submit" className="primary-button">{editingId ? <><Pencil size={17}/> 変更を保存</> : <><Plus size={17}/> 記録を保存</>}</button>
              <button type="button" className="secondary-button" onClick={() => setRecordSlide(2)}>次へ：チーム構成 →</button>
            </div>
          </div>''',
    '1ページ目への保存ボタン追加',
)

# 5) Per-hero alias editor in Settings. Aliases are part of the existing Store, so local/cloud/backup persistence is automatic.
app = replace_once(
    app,
    '  function addMap() {',
    '''  function editHeroAliases(hero: Hero) {
    const answer = window.prompt(
      `${hero.name} の略称を入力してください。複数ある場合は「,」または「、」で区切ります。\n空欄で保存すると略称を削除します。`,
      (hero.aliases ?? []).join(', '),
    )
    if (answer === null) return
    const seen = new Set<string>()
    const aliases = answer.split(/[,、，]/).map(value => value.trim()).filter(value => {
      const normalized = normalizeHeroSearchText(value)
      if (!normalized || normalized === normalizeHeroSearchText(hero.name) || seen.has(normalized)) return false
      seen.add(normalized)
      return true
    })
    setStore(current => ({
      ...current,
      heroes: current.heroes.map(item => item.name === hero.name ? { ...item, aliases: aliases.length ? aliases : undefined } : item),
    }))
    notify(aliases.length ? `${hero.name} の略称を保存しました` : `${hero.name} の略称を削除しました`)
  }

  function addMap() {''',
    'ヒーロー略称編集関数',
)
app = replace_once(
    app,
    '''<div className="catalog-list">{managedHeroes.map(h => <div className="catalog-item" key={h.name}><span>{h.name}</span><span className={`role-pill role-${roles.indexOf(h.role)}`}>{h.role}</span><button className="icon-button" aria-label={`${h.name}を削除`} onClick={() => removeHero(h.name)}><Trash2 size={16}/></button></div>)}</div>''',
    '''<div className="catalog-list">{managedHeroes.map(h => <div className="catalog-item hero-catalog-item" key={h.name}><span className="hero-catalog-name">{h.name}{h.aliases?.length ? <small className="hero-alias-summary">略称：{h.aliases.join('、')}</small> : null}</span><span className={`role-pill role-${roles.indexOf(h.role)}`}>{h.role}</span><button className="icon-button alias-edit-button" aria-label={`${h.name}の略称を設定`} title="略称を設定・編集" onClick={() => editHeroAliases(h)}><Pencil size={15}/></button><button className="icon-button" aria-label={`${h.name}を削除`} onClick={() => removeHero(h.name)}><Trash2 size={16}/></button></div>)}</div>''',
    'ヒーロー管理に略称編集を追加',
)

# Add ChevronDown icon for dropdown trigger.
app = replace_once(
    app,
    "import { Activity, BarChart3, CalendarDays, Download, FileUp, Gauge, History, Lock, Minus, Pencil, Plus, Search, Settings, Shield, Star, Sun, Moon, Swords, Trash2, Trophy, Unlock, X } from 'lucide-react'",
    "import { Activity, BarChart3, CalendarDays, ChevronDown, Download, FileUp, Gauge, History, Lock, Minus, Pencil, Plus, Search, Settings, Shield, Star, Sun, Moon, Swords, Trash2, Trophy, Unlock, X } from 'lucide-react'",
    '検索プルダウン用アイコン',
)

component = '''function SearchableHeroDropdown({ value, heroes, onChange, placeholder }: { value: string; heroes: Hero[]; onChange: (name: string) => void; placeholder: string }) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const filteredHeroes = useMemo(() => heroes.filter(hero => heroMatchesSearch(hero, query)), [heroes, query])
  const selectedHero = heroes.find(hero => hero.name === value)
  function chooseHero(name: string) {
    onChange(name)
    setQuery('')
    setOpen(false)
  }
  return <div className="hero-search-dropdown" onBlur={event => {
    const nextTarget = event.relatedTarget as Node | null
    if (!nextTarget || !event.currentTarget.contains(nextTarget)) setOpen(false)
  }}>
    <button type="button" className="hero-search-dropdown-trigger" aria-haspopup="listbox" aria-expanded={open} onClick={() => {
      if (!open) setQuery('')
      setOpen(current => !current)
    }}>
      <span className={selectedHero ? '' : 'hero-search-dropdown-placeholder'}>{selectedHero?.name ?? placeholder}</span>
      <ChevronDown size={16}/>
    </button>
    {open && <div className="hero-search-dropdown-menu">
      <label className="hero-search-dropdown-query"><Search size={15}/><input autoFocus value={query} onChange={event => setQuery(event.target.value)} onKeyDown={event => {
        if (event.key === 'Escape') { event.preventDefault(); setOpen(false) }
        if (event.key === 'Enter') {
          event.preventDefault()
          if (filteredHeroes.length === 1) chooseHero(filteredHeroes[0].name)
        }
      }} placeholder="ヒーロー名・略称で検索" /></label>
      <div className="hero-search-dropdown-options" role="listbox" aria-label="ヒーロー候補">
        <button type="button" role="option" aria-selected={!value} className={!value ? 'selected' : ''} onClick={() => chooseHero('')}><span>{placeholder}</span></button>
        {filteredHeroes.map(hero => <button type="button" role="option" aria-selected={value === hero.name} className={value === hero.name ? 'selected' : ''} key={hero.name} onClick={() => chooseHero(hero.name)}>
          <span>{hero.name}</span>{hero.aliases?.length ? <small>{hero.aliases.join('、')}</small> : null}
        </button>)}
        {filteredHeroes.length === 0 && <p className="hero-search-dropdown-empty">該当するヒーローがいません。略称も検索できます。</p>}
      </div>
    </div>}
  </div>
}

'''
app = replace_once(app, 'function NavItem(', component + 'function NavItem(', '検索可能なヒーロー選択コンポーネント')

# Add focused styles after the theme variables and existing site styles, in the last-loaded stylesheet.
css = r'''

/* Dashboard order: 1 2 / 3 4 / 5 */
.dashboard-stats-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.dashboard-stats-grid > .stat-card:last-child { grid-column: 1 / -1; }

/* Keep the hero filters compact; the search field appears only after opening a picker. */
.hero-picker-controls.hero-picker-filters-only { grid-template-columns: minmax(0, 1fr); }
.hero-select-row .hero-search-dropdown { flex: 1 1 auto; min-width: 0; }
.hero-search-dropdown { position: relative; width: 100%; min-width: 0; }
html[data-theme] .hero-search-dropdown-trigger {
  display: flex; align-items: center; justify-content: space-between; gap: 10px;
  width: 100%; min-width: 0; min-height: 40px; padding: 10px 12px;
  border: 1px solid var(--line); border-radius: 8px; background: var(--surface-raised);
  color: var(--text-main); text-align: left; font-size: 11px; cursor: pointer;
}
.hero-search-dropdown-trigger > span:first-child { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
html[data-theme] .hero-search-dropdown-trigger:hover,
html[data-theme] .hero-search-dropdown-trigger:focus-visible { border-color: var(--accent-strong); outline: none; box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 14%, transparent); }
.hero-search-dropdown-placeholder { color: var(--text-muted); }
.hero-search-dropdown-menu {
  position: absolute; z-index: 50; top: calc(100% + 5px); left: 0; right: 0;
  min-width: min(100%, 280px); padding: 8px; border: 1px solid var(--line); border-radius: 10px;
  background: var(--surface); box-shadow: 0 14px 38px var(--shadow); color: var(--text-main);
}
.hero-search-dropdown-query {
  display: flex; align-items: center; gap: 8px; padding: 0 9px; margin-bottom: 7px;
  border: 1px solid var(--line); border-radius: 7px; background: var(--surface-raised); color: var(--text-muted);
}
html[data-theme] .hero-search-dropdown-query input {
  min-width: 0; width: 100%; padding: 10px 0; border: 0; border-radius: 0;
  outline: none; box-shadow: none; background: transparent; color: var(--text-main); font-size: 11px;
}
html[data-theme] .hero-search-dropdown-query input:focus { border: 0 !important; box-shadow: none !important; }
.hero-search-dropdown-options { max-height: 230px; overflow: auto; overscroll-behavior: contain; display: grid; gap: 2px; }
html[data-theme] .hero-search-dropdown-options > button {
  display: flex; align-items: center; justify-content: space-between; gap: 8px; width: 100%; min-width: 0;
  padding: 9px 10px; border: 1px solid transparent; border-radius: 6px; background: transparent;
  color: var(--text-main); text-align: left; font-size: 11px; cursor: pointer;
}
html[data-theme] .hero-search-dropdown-options > button:hover,
html[data-theme] .hero-search-dropdown-options > button:focus-visible { outline: none; border-color: var(--accent-line); background: var(--accent-soft); }
html[data-theme] .hero-search-dropdown-options > button.selected { color: var(--accent-strong); background: var(--accent-soft); }
.hero-search-dropdown-options > button > span { overflow-wrap: anywhere; }
.hero-search-dropdown-options > button small { flex: 0 1 45%; color: var(--text-muted); font-size: 9px; text-align: right; overflow-wrap: anywhere; }
.hero-search-dropdown-empty { margin: 0; padding: 12px 10px; color: var(--text-muted); font-size: 10px; line-height: 1.7; }

/* Per-hero aliases stay editable without adding permanent controls to the main recorder. */
.hero-catalog-item { gap: 7px; }
.hero-catalog-name { min-width: 0; flex: 1 1 auto; overflow-wrap: anywhere; }
.hero-alias-summary { display: block; margin-top: 3px; color: var(--text-muted); font-size: 9px; line-height: 1.4; }
.hero-catalog-item .alias-edit-button { flex-shrink: 0; }

/* Save is available from the first slide as well as the team-composition slide. */
.primary-slide-nav { align-items: center; }
.record-slide-actions { display: flex; align-items: center; justify-content: flex-end; flex-wrap: wrap; gap: 8px; }
@media (max-width: 700px) {
  .dashboard-stats-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .dashboard-stats-grid > .stat-card:last-child { grid-column: 1 / -1; }
  .record-slide-actions { width: 100%; justify-content: stretch; }
  .record-slide-actions > button { flex: 1 1 auto; }
  .hero-search-dropdown-menu { min-width: 0; }
}
'''
marker = '/* COMPASS visual refresh: VOIDOLL light / BUGDOLL dark */'
if marker not in theme:
    raise SystemExit('適用を中止しました：src/theme.css の想定マーカーがありません。ファイルはまだ変更していません。')
if '/* Dashboard order: 1 2 / 3 4 / 5 */' in theme:
    raise SystemExit('この改善用CSSは既に追加されています。二重適用を防ぐため中止しました。')
theme = theme.rstrip() + css + '\n'

# Safety checks to catch missed replacements before touching disk.
for stale in ['dashboardWinMode', 'dashboardWinLimit', 'heroSearch', 'heroSelectRef', 'handleHeroSearch', 'openHeroSelect']:
    if stale in app:
        raise SystemExit(f'適用を中止しました：古い参照 {stale} が残っています。ファイルはまだ変更していません。')
for required in ['SearchableHeroDropdown', 'heroMatchesSearch', 'todayWinRate', 'allTimeWinRate', 'editHeroAliases', '記録を保存']:
    if required not in app:
        raise SystemExit(f'適用を中止しました：修正後の確認語句 {required} が見つかりません。ファイルはまだ変更していません。')

stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
backup_dir = Path('/tmp') / f'compass-search-dashboard-{stamp}'
backup_dir.mkdir(parents=True, exist_ok=False)
shutil.copy2(APP, backup_dir / 'App.tsx')
shutil.copy2(THEME, backup_dir / 'theme.css')
APP.write_text(app, encoding='utf-8')
THEME.write_text(theme, encoding='utf-8')
print('改善を適用しました。')
print(f'バックアップ: {backup_dir}')
print('変更ファイル: src/App.tsx, src/theme.css')
print('次に npm run build を実行してください。')
