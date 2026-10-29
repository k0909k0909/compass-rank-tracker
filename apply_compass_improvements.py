from pathlib import Path
import time

ROOT = Path.cwd()
APP_PATH = ROOT / "src" / "App.tsx"
CSS_PATH = ROOT / "src" / "style-improvements.css"
if not APP_PATH.exists() or not CSS_PATH.exists():
    raise SystemExit("エラー: リポジトリのルートで実行してください（src/App.tsx と src/style-improvements.css が必要です）。")

app = APP_PATH.read_text(encoding="utf-8")
css = CSS_PATH.read_text(encoding="utf-8")
original_app, original_css = app, css

def replace_once(old: str, new: str, label: str) -> None:
    global app
    count = app.count(old)
    if count != 1:
        raise RuntimeError(f"変更を中止しました: {label} の一致数が1ではありません（{count}）。ファイルが想定版と異なる可能性があります。")
    app = app.replace(old, new, 1)

def replace_all(old: str, new: str, label: str) -> None:
    global app
    count = app.count(old)
    if count < 1:
        raise RuntimeError(f"変更を中止しました: {label} が見つかりません。ファイルが想定版と異なる可能性があります。")
    app = app.replace(old, new)

changes = [
("""  const [historyMode, setHistoryMode] = useState<'all' | Mode>('all')
  const [heroSearch, setHeroSearch] = useState('')""",
"""  const [historyMode, setHistoryMode] = useState<'all' | Mode>('all')
  const [dashboardWinMode, setDashboardWinMode] = useState<Mode>('バトアリ')
  const [dashboardWinLimit, setDashboardWinLimit] = useState<'all' | '10' | '20' | '50' | '100'>('all')
  const [heroSearch, setHeroSearch] = useState('')""", "ホームの勝率フィルター状態"),
("""  const [initialRankDraft, setInitialRankDraft] = useState(store.initialRankPoints == null ? '' : String(store.initialRankPoints))
  const importRef = useRef<HTMLInputElement>(null)""",
"""  const importRef = useRef<HTMLInputElement>(null)
  const heroSelectRef = useRef<HTMLSelectElement>(null)""", "旧設定用stateの削除とヒーローselect参照"),
("setInitialRankDraft(typeof restored.initialRankPoints === 'number' ? String(restored.initialRankPoints) : '')", "", "復元時の旧設定用state更新を削除"),
("""    heroName: store.heroes[0]?.name ?? '', mapName: store.maps[0] ?? '', result: 'win' as Result,""",
"""    heroName: '', mapName: store.maps[0] ?? '', result: 'win' as Result,""", "新規記録時のヒーロー初期値"),
("""  const wins = store.matches.filter(m => m.result === 'win').length
  const losses = store.matches.filter(m => m.result === 'loss').length
  const winRate = percent(wins, wins + losses)
  const currentRankState = normalizeRankState(store.currentRankTier ?? 1, store.currentRankPoints ?? 0)""",
"""  const dashboardWinMatches = useMemo(() => {
    const byMode = sortedMatches.filter(match => (match.mode ?? 'バトアリ') === dashboardWinMode)
    return dashboardWinLimit === 'all' ? byMode : byMode.slice(0, Number(dashboardWinLimit))
  }, [sortedMatches, dashboardWinMode, dashboardWinLimit])
  const dashboardWins = dashboardWinMatches.filter(match => match.result === 'win').length
  const dashboardLosses = dashboardWinMatches.filter(match => match.result === 'loss').length
  const dashboardWinRate = percent(dashboardWins, dashboardWins + dashboardLosses)
  const currentRankState = normalizeRankState(store.currentRankTier ?? 1, store.currentRankPoints ?? 0)""", "モード・直近試合数別の勝率集計"),
("""  const currentStreak = useMemo(() => {
    const chronological = [...store.matches].sort((a, b) => b.playedAt.localeCompare(a.playedAt))
    const first = chronological[0]?.result
    if (first !== 'win' && first !== 'loss') return { result: '—', count: 0 }
    let count = 0
    for (const match of chronological) { if (match.result !== first) break; count++ }
    return { result: first === 'win' ? '連勝' : '連敗', count }
  }, [store.matches])""",
"""  const currentStreak = useMemo(() => {
    const chronological = [...store.matches].sort((a, b) => b.playedAt.localeCompare(a.playedAt))
    const first = chronological[0]?.result
    if (first !== 'win' && first !== 'loss') return { result: '—', count: 0 }
    let count = 0
    for (const match of chronological) { if (match.result !== first) break; count++ }
    return { result: first === 'win' ? '連勝' : '連敗', count }
  }, [store.matches])
  const highestWinStreak = useMemo(() => {
    const chronological = [...store.matches].sort((a, b) => a.playedAt.localeCompare(b.playedAt))
    let current = 0, highest = 0
    for (const match of chronological) {
      if (match.result === 'win') { current += 1; highest = Math.max(highest, current) }
      else current = 0
    }
    return highest
  }, [store.matches])""", "最高連勝数の集計"),
("""  const visibleHeroes = useMemo(() => {
    const query = heroSearch.trim().toLocaleLowerCase()
    return store.heroes
      .filter(hero => (heroRoleFilter === 'all' || hero.role === heroRoleFilter)
        && (!favoritesOnly || Boolean(hero.favorite))
        && (!query || hero.name.toLocaleLowerCase().includes(query)))
      .sort((a, b) => (heroOrderIndex.get(a.name) ?? Number.MAX_SAFE_INTEGER) - (heroOrderIndex.get(b.name) ?? Number.MAX_SAFE_INTEGER))
  }, [store.heroes, heroSearch, heroRoleFilter, favoritesOnly])""",
"""  const visibleHeroes = useMemo(() => {
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
  }, [store.heroes, heroSearch, heroRoleFilter, favoritesOnly, sortedMatches])""", "前回使用ヒーローの並び順とフィルター時の解除"),
("""  const selectedHero = store.heroes.find(hero => hero.name === form.heroName)
  function toggleFavorite(name: string) {""",
"""  const selectedHero = store.heroes.find(hero => hero.name === form.heroName)
  function openHeroSelect() {
    const select = heroSelectRef.current as (HTMLSelectElement & { showPicker?: () => void }) | null
    if (!select) return
    try { if (select.showPicker) select.showPicker(); else { select.focus(); select.click() } }
    catch { select.focus(); select.click() }
  }
  function handleHeroSearch(value: string) {
    setHeroSearch(value)
    const query = value.trim().toLocaleLowerCase()
    const matches = store.heroes.filter(hero => (heroRoleFilter === 'all' || hero.role === heroRoleFilter)
      && (!favoritesOnly || Boolean(hero.favorite))
      && Boolean(query) && hero.name.toLocaleLowerCase().includes(query))
    setForm(old => ({ ...old, heroName: matches.length === 1 ? matches[0].name : '' }))
    if (matches.length !== 1) openHeroSelect()
  }
  function changeHeroRoleFilter(role: 'all' | Role) {
    setHeroRoleFilter(role)
    setForm(old => ({ ...old, heroName: '' }))
    openHeroSelect()
  }
  function changeFavoritesOnly(checked: boolean) {
    setFavoritesOnly(checked)
    setForm(old => ({ ...old, heroName: '' }))
    openHeroSelect()
  }
  function toggleFavorite(name: string) {""", "検索・ロール絞り込み・お気に入り時の選択動作"),
("""    setForm({ playedAt: nowLocalInput(), seasonEnabled: false, seasonLabel: store.activeSeason ?? seasonLabelFromDate(nowLocalInput()), mode: store.lastMode ?? 'バトアリ', heroName: store.heroes[0]?.name ?? '', mapName: store.maps[0] ?? '', result: 'win', rankDirection: 'plus', rankDelta: '0', memo: '' })""",
"""    setForm({ playedAt: nowLocalInput(), seasonEnabled: false, seasonLabel: store.activeSeason ?? seasonLabelFromDate(nowLocalInput()), mode: store.lastMode ?? 'バトアリ', heroName: '', mapName: store.maps[0] ?? '', result: 'win', rankDirection: 'plus', rankDelta: '0', memo: '' })""", "新規記録画面のヒーロー未選択状態"),
("""  function saveInitialRankPoints() {
    const text = initialRankDraft.trim()
    if (text === '') { setStore(s => ({ ...s, initialRankPoints: null })); notify('初期ランクポイントを未設定にしました'); return }
    const value = Number(text)
    if (!Number.isFinite(value)) { notify('初期ランクポイントは数値で入力してください'); return }
    const updated = { ...storeRef.current, initialRankPoints: value }
    storeRef.current = updated
    setStore(updated)
    notify('初期ランクポイントを保存しました（旧形式の記録用）')
  }
""", "", "旧ランク設定の保存処理を削除"),
("""        <div className="stats-grid">
          <StatCard icon={<Activity size={19}/>} label="総試合数" value={`${store.matches.length}`} sub="記録した試合" />
          <StatCard icon={<Trophy size={19}/>} label="勝率" value={winRate} sub={`${wins}勝 · ${losses}敗`} />
          <StatCard icon={<BarChart3 size={19}/>} label="現在のランク" value={`S${currentRankState.tier}`} sub={`${currentRankState.points}/499 pt · ${store.activeSeason ?? 'シーズン未設定'}`} />
          <StatCard icon={<CalendarDays size={19}/>} label="今月の試合" value={`${currentMonthMatches.length}`} sub={`${currentMonthWins}勝 · ${currentMonthLosses}敗`} />
          <StatCard icon={<Activity size={19}/>} label="現在の連続結果" value={currentStreak.count ? `${currentStreak.count}${currentStreak.result}` : '—'} sub="最新の記録から集計" />
          <StatCard icon={<Shield size={19}/>} label="登録ヒーロー" value={`${store.heroes.length}`} sub={`マップ ${store.maps.length} 件`} />
        </div>""",
"""        <div className="stats-grid">
          <StatCard icon={<Activity size={19}/>} label="総試合数" value={`${store.matches.length}`} sub="記録した試合" />
          <div className="stat-card win-rate-stat-card">
            <div className="stat-top"><span>勝率</span><span className="stat-icon"><Trophy size={19}/></span></div>
            <div className="win-rate-tabs" role="group" aria-label="勝率のモード">
              {(['フリバ', 'バトアリ'] as Mode[]).map(mode => <button type="button" key={mode} className={`win-rate-tab ${dashboardWinMode === mode ? 'active' : ''}`} aria-pressed={dashboardWinMode === mode} onClick={() => setDashboardWinMode(mode)}>{mode}</button>)}
            </div>
            <strong>{dashboardWinRate}</strong>
            <div className="win-rate-footer"><small>{dashboardWins}勝 · {dashboardLosses}敗</small><select aria-label="勝率の集計対象試合数" className="win-rate-limit" value={dashboardWinLimit} onChange={e => setDashboardWinLimit(e.target.value as 'all' | '10' | '20' | '50' | '100')}><option value="all">全試合</option><option value="10">直近10戦</option><option value="20">直近20戦</option><option value="50">直近50戦</option><option value="100">直近100戦</option></select></div>
          </div>
          <StatCard icon={<BarChart3 size={19}/>} label="現在のランク" value={`S${currentRankState.tier}`} sub={`${currentRankState.points} pt · ${store.activeSeason ?? 'シーズン未設定'}`} />
          <StatCard icon={<CalendarDays size={19}/>} label="今月の試合" value={`${currentMonthMatches.length}`} sub={`${currentMonthWins}勝 · ${currentMonthLosses}敗`} />
          <StatCard icon={<Activity size={19}/>} label="現在の連続結果" value={currentStreak.count ? `${currentStreak.count}${currentStreak.result}` : '—'} sub={`最高連勝：${highestWinStreak}`} />
        </div>""", "ホーム統計カードの変更"),
("""            <div className="hero-search-control"><label>使用ヒーローを検索</label><label className="search-field"><Search size={16}/><input value={heroSearch} onChange={e => setHeroSearch(e.target.value)} placeholder="ヒーロー名を入力" /></label></div>
            <div className="hero-filter-control"><label>絞込み</label>
              <div className="hero-role-buttons">{(['all', ...roles] as ('all' | Role)[]).map(role => <button type="button" key={role} className={`role-filter-button ${heroRoleFilter === role ? 'active' : ''}`} onClick={() => setHeroRoleFilter(role)}>{role === 'all' ? 'すべて' : role}</button>)}</div>
              <label className="favorite-filter"><input type="checkbox" checked={favoritesOnly} onChange={e => setFavoritesOnly(e.target.checked)}/><span><Star size={13}/> お気に入り</span></label>
            </div>""",
"""            <div className="hero-search-control"><label>使用ヒーローを検索</label><label className="search-field"><Search size={16}/><input value={heroSearch} onChange={e => handleHeroSearch(e.target.value)} placeholder="ヒーロー名を入力" /></label></div>
            <div className="hero-filter-control"><label>絞込み</label>
              <div className="hero-role-buttons">{(['all', ...roles] as ('all' | Role)[]).map(role => <button type="button" key={role} className={`role-filter-button ${heroRoleFilter === role ? 'active' : ''}`} onClick={() => changeHeroRoleFilter(role)}>{role === 'all' ? 'すべて' : role}</button>)}</div>
              <label className="favorite-filter"><input type="checkbox" checked={favoritesOnly} onChange={e => changeFavoritesOnly(e.target.checked)}/><span><Star size={13}/> お気に入り</span></label>
            </div>""", "ヒーロー検索と絞り込みのイベント"),
("""            <div className="hero-select-row"><select className="hero-select" required value={form.heroName} onChange={e => setForm({ ...form, heroName: e.target.value })}>{visibleHeroes.some(h => h.name === form.heroName) ? null : store.heroes.find(h => h.name === form.heroName) ? <option value={form.heroName}>{form.heroName}（現在の記録）</option> : null}{visibleHeroes.map(h => <option key={h.name} value={h.name}>{h.name}（{h.role}）</option>)}</select>""",
"""            <div className="hero-select-row"><select ref={heroSelectRef} className="hero-select" required value={form.heroName} onChange={e => setForm({ ...form, heroName: e.target.value })}><option value="">—</option>{visibleHeroes.map(h => <option key={h.name} value={h.name}>{h.name}</option>)}</select>""", "ヒーロー選択肢の先頭とロール表示を削除"),
("""          <div className="form-actions"><button type="button" className="secondary-button" onClick={() => { setEditingId(null); setPage('dashboard') }}>キャンセル</button><button type="submit" className="primary-button">{editingId ? <><Pencil size={17}/> 変更を保存</> : <><Plus size={17}/> 記録を保存</>}</button></div>""",
"""          <div className="form-actions"><button type="button" className="secondary-button" onClick={() => { setEditingId(null); setPage('dashboard') }}>キャンセル</button><button type="submit" className="primary-button">{editingId ? <><Pencil size={17}/> 変更を保存</> : <><Plus size={17}/> 記録を保存して次へ</>}</button></div>""", "保存ボタン文言"),
("""    const wasEditing = editingId !== null
    setEditingId(null)
    setPage('dashboard')
    notify(wasEditing ? '試合記録を更新しました' : rankedMatch ? `試合を記録しました（${formatRankState(rankAfter)}）` : 'フリバの試合を記録しました（ランク変動なし）')""",
"""    const wasEditing = editingId !== null
    setEditingId(null)
    if (wasEditing) {
      setPage('dashboard')
    } else {
      const nextDate = nowLocalInput()
      setHeroSearch('')
      setHeroRoleFilter('all')
      setFavoritesOnly(false)
      setForm(old => ({ playedAt: nextDate, seasonEnabled: old.mode === 'バトアリ' ? old.seasonEnabled : false,
        seasonLabel: storeRef.current.activeSeason ?? seasonLabelFromDate(nextDate), mode: old.mode, heroName: '',
        mapName: old.mapName || storeRef.current.maps[0] || '', result: 'win', rankDirection: 'plus', rankDelta: '0', memo: '' }))
      setPage('add')
    }
    notify(wasEditing ? '試合記録を更新しました' : rankedMatch ? `試合を記録しました（${formatRankState(rankAfter)}）。次の試合を入力できます` : 'フリバの試合を記録しました。次の試合を入力できます')""", "保存後の連続記録フロー"),
("""        <div className="content-card">
          <div className="section-heading"><div><h3>旧形式のランクポイント設定</h3><p>古い記録との互換用です。現在のランクは試合入力画面で編集できます。</p></div><div className="round-icon"><BarChart3 size={20}/></div></div>
          <div className="initial-rp-setting"><div className="field"><label>初期ランクポイント</label><input type="number" step="1" placeholder="例：1500" value={initialRankDraft} onChange={e => setInitialRankDraft(e.target.value)}/></div><button className="primary-button" onClick={saveInitialRankPoints}>初期RPを保存</button></div>
          <p className="small-note">新しい試合ではS1〜S9のランク規則を使用します。この設定は旧形式データの読み込み互換用として残しています。</p>
        </div>
""", "", "旧形式ランク設定カードを削除"),
]

for old, new, label in changes:
    replace_once(old, new, label)
replace_all("ポイント（0〜499）", "ポイント", "入力欄のランクポイント表記")
replace_all("S1〜S9の各ランクは0〜499pt。500pt到達で昇格し、ポイントが残っている間の減少は0ptで止まります。0ptで減少した場合のみ降格します。", "500pt到達で昇格し、ポイントが残っている間の減少は0ptで止まります。0ptで減少した場合のみ降格します。", "説明文のランクポイント表記")
replace_all("ランクポイントは0〜499の整数で入力してください", "有効なランクポイントを整数で入力してください", "エラー文のランクポイント表記")

if "initialRankDraft" in app:
    raise RuntimeError("変更を中止しました: initialRankDraft の参照が残っています。")
if 'label="登録ヒーロー"' in app or "value={winRate}" in app or "（{h.role}）</option>" in app:
    raise RuntimeError("変更を中止しました: 削除対象の古い表示が残っています。")
if ".win-rate-stat-card" in css:
    raise RuntimeError("変更を中止しました: 勝率タブ用CSSがすでにあります。二重適用を避けます。")

css += """

/* ホーム：勝率カード内の小さなモードタブと集計期間 */
.win-rate-stat-card { min-width: 0; }
.win-rate-tabs { display: flex; gap: 5px; margin: 8px 0 6px; }
.win-rate-tab { border: 1px solid #303951; border-radius: 6px; padding: 4px 8px; background: #0e1526; color: #9aa5c0; font-size: 10px; font-weight: 650; line-height: 1.3; cursor: pointer; }
.win-rate-tab.active { border-color: #8b7af5; background: #252044; color: #d6ccff; }
.win-rate-footer { display: flex; align-items: center; justify-content: space-between; gap: 6px; margin-top: 5px; }
.win-rate-footer small { min-width: 0; font-size: 10px; }
.win-rate-limit { max-width: 112px; min-width: 0; border: 1px solid #303951; border-radius: 6px; padding: 4px 5px; background: #0e1526; color: #b8c2d8; font-size: 10px; }
@media (max-width: 520px) { .win-rate-footer { align-items: flex-start; flex-direction: column; } .win-rate-limit { max-width: 100%; width: 100%; } }
"""

stamp = time.strftime("%Y%m%d-%H%M%S")
backup_dir = Path("/tmp") / f"compass-tracker-before-improvements-{stamp}"
backup_dir.mkdir(parents=True, exist_ok=False)
(backup_dir / "App.tsx").write_text(original_app, encoding="utf-8")
(backup_dir / "style-improvements.css").write_text(original_css, encoding="utf-8")
APP_PATH.write_text(app, encoding="utf-8")
CSS_PATH.write_text(css, encoding="utf-8")
print("変更を適用しました。")
print(f"バックアップ: {backup_dir}")
print("次に npm run build を実行してください。")
