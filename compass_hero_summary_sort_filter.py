from pathlib import Path
from datetime import datetime
import shutil
import sys

app_file = Path("src/App.tsx")
css_file = Path("src/style-improvements.css")
if not app_file.exists() or not css_file.exists():
    print("エラー: compass-rank-tracker のルートで実行してください。")
    sys.exit(1)

app = app_file.read_text(encoding="utf-8")
css = css_file.read_text(encoding="utf-8")
marker = "/* HERO SUMMARY SORT AND RECENT MATCH FILTER v1 */"
if marker in css:
    print("今回の改善はすでに適用されています。")
    sys.exit(0)

backup_dir = Path(".patch-backups") / datetime.now().strftime("%Y%m%d-%H%M%S")
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(app_file, backup_dir / "App.tsx")
shutil.copy2(css_file, backup_dir / "style-improvements.css")

anchor = "  const [heroDetailSortDirection, setHeroDetailSortDirection] = useState<'asc' | 'desc'>('desc')"
if anchor not in app:
    sys.exit("エラー: ソート状態の追加位置が見つかりません。")
app = app.replace(anchor, anchor + """
  const [heroSummarySortKey, setHeroSummarySortKey] = useState<'default' | 'battles' | 'wins' | 'winRate'>('default')
  const [heroSummarySortDirection, setHeroSummarySortDirection] = useState<'asc' | 'desc'>('desc')
  const [heroSummaryRecentCount, setHeroSummaryRecentCount] = useState<'all' | '10' | '50' | '100'>('all')""", 1)

old_summary = """  const heroSummaryRows = useMemo(() => store.heroes.map(hero => {
    const base = store.heroBaseStats?.[hero.name] ?? { battles: 0, wins: 0 }
    const recorded = store.matches.filter(match => match.heroName === hero.name)
    const battles = base.battles + recorded.length
    const wins = base.wins + recorded.filter(match => match.result === 'win').length
    return { ...hero, baseBattles: base.battles, baseWins: base.wins, totalBattles: battles, totalWins: wins, winRate: battles > 0 ? wins / battles * 100 : null }
  }).sort((a, b) => (heroOrderIndex.get(a.name) ?? Number.MAX_SAFE_INTEGER) - (heroOrderIndex.get(b.name) ?? Number.MAX_SAFE_INTEGER)), [store.heroes, store.heroBaseStats, store.matches])"""
new_summary = """  const heroSummaryRows = useMemo(() => {
    const rows = store.heroes.map(hero => {
      const base = store.heroBaseStats?.[hero.name] ?? { battles: 0, wins: 0 }
      let recorded = store.matches.filter(match => match.heroName === hero.name)
        .sort((a, b) => b.playedAt.localeCompare(a.playedAt))
      if (heroSummaryRecentCount !== 'all') recorded = recorded.slice(0, Number(heroSummaryRecentCount))
      // 日付のない手入力累計は、直近N戦の集計には含めません。
      const includeBase = heroSummaryRecentCount === 'all'
      const battles = (includeBase ? base.battles : 0) + recorded.length
      const wins = (includeBase ? base.wins : 0) + recorded.filter(match => match.result === 'win').length
      return { ...hero, totalBattles: battles, totalWins: wins, winRate: battles > 0 ? wins / battles * 100 : null }
    })
    const implementationOrder = (a: typeof rows[number], b: typeof rows[number]) =>
      (heroOrderIndex.get(a.name) ?? Number.MAX_SAFE_INTEGER) - (heroOrderIndex.get(b.name) ?? Number.MAX_SAFE_INTEGER)
    if (heroSummarySortKey === 'default') return rows.sort(implementationOrder)
    return rows.sort((a, b) => {
      const av = heroSummarySortKey === 'battles' ? a.totalBattles : heroSummarySortKey === 'wins' ? a.totalWins : a.winRate
      const bv = heroSummarySortKey === 'battles' ? b.totalBattles : heroSummarySortKey === 'wins' ? b.totalWins : b.winRate
      if (av === null || bv === null) {
        if (av === bv) return implementationOrder(a, b)
        return av === null ? 1 : -1
      }
      const difference = av - bv
      return difference === 0 ? implementationOrder(a, b) : heroSummarySortDirection === 'asc' ? difference : -difference
    })
  }, [store.heroes, store.heroBaseStats, store.matches, heroSummaryRecentCount, heroSummarySortKey, heroSummarySortDirection])"""
if old_summary not in app:
    sys.exit("エラー: 合計成績の集計コードが想定と異なります。App.tsx は変更していません。")
app = app.replace(old_summary, new_summary, 1)

old_ui = """          <div className="table-wrap hero-log-table-wrap"><table className="hero-log-table hero-log-main-table"><thead><tr><th>ヒーロー</th><th>試合数</th><th>勝ち数</th><th>勝率</th><th>操作</th></tr></thead><tbody>
            {heroSummaryRows.map(hero => <tr key={hero.name}>
              <td><div className="hero-log-name"><strong>{hero.name}</strong><small>{hero.role}</small></div></td>
              <td className="hero-log-number-cell">{hero.totalBattles.toLocaleString()}</td>
              <td className="hero-log-number-cell">{hero.totalWins.toLocaleString()}</td>
              <td className="hero-log-rate">{hero.winRate === null ? '—' : `${hero.winRate.toFixed(1)}%`}</td>
              <td><div className="hero-log-row-actions">
                <button type="button" className="secondary-button hero-log-detail-button" onClick={() => openHeroDetail(hero.name)}>詳細</button>
                <button type="button" className="icon-button hero-log-edit-button" aria-label={`${hero.name}の合計成績を修正`} title="合計成績を修正" onClick={() => editHeroTotalStats(hero.name)}><Pencil size={16}/></button>
              </div></td>
            </tr>)}
          </tbody></table></div>"""
new_ui = """          <div className="hero-summary-toolbar">
            <button type="button" className="secondary-button hero-summary-reset-button" onClick={() => { setHeroSummarySortKey('default'); setHeroSummarySortDirection('desc') }}>ソートリセット</button>
            <div className="hero-summary-filter-buttons" aria-label="集計する試合数">
              {(['all', '10', '50', '100'] as const).map(count => <button key={count} type="button"
                className={`hero-summary-filter-button ${heroSummaryRecentCount === count ? 'active' : ''}`}
                onClick={() => setHeroSummaryRecentCount(count)}
              >{count === 'all' ? '全試合' : `${count}戦`}</button>)}
            </div>
          </div>
          {heroSummaryRecentCount !== 'all' && <p className="hero-summary-filter-note">各ヒーローの直近{heroSummaryRecentCount}戦を集計しています。手入力した過去の累計成績は、試合日時がないためこの絞り込みには含まれません。</p>}
          <div className="table-wrap hero-log-table-wrap"><table className="hero-log-table hero-log-main-table"><thead><tr>
            <th>ヒーロー</th>
            <th><button type="button" className="hero-summary-sort-button" onClick={() => { setHeroSummarySortKey('battles'); setHeroSummarySortDirection(current => heroSummarySortKey === 'battles' ? (current === 'desc' ? 'asc' : 'desc') : 'desc') }}>試合数 {heroSummarySortKey === 'battles' ? (heroSummarySortDirection === 'desc' ? '↓' : '↑') : '↕'}</button></th>
            <th><button type="button" className="hero-summary-sort-button" onClick={() => { setHeroSummarySortKey('wins'); setHeroSummarySortDirection(current => heroSummarySortKey === 'wins' ? (current === 'desc' ? 'asc' : 'desc') : 'desc') }}>勝ち数 {heroSummarySortKey === 'wins' ? (heroSummarySortDirection === 'desc' ? '↓' : '↑') : '↕'}</button></th>
            <th><button type="button" className="hero-summary-sort-button" onClick={() => { setHeroSummarySortKey('winRate'); setHeroSummarySortDirection(current => heroSummarySortKey === 'winRate' ? (current === 'desc' ? 'asc' : 'desc') : 'desc') }}>勝率 {heroSummarySortKey === 'winRate' ? (heroSummarySortDirection === 'desc' ? '↓' : '↑') : '↕'}</button></th>
            <th>操作</th>
          </tr></thead><tbody>
            {heroSummaryRows.map(hero => <tr key={hero.name}>
              <td><div className="hero-log-name"><strong>{hero.name}</strong><small>{hero.role}</small></div></td>
              <td className="hero-log-number-cell">{hero.totalBattles.toLocaleString()}</td>
              <td className="hero-log-number-cell">{hero.totalWins.toLocaleString()}</td>
              <td className="hero-log-rate">{hero.winRate === null ? '—' : `${hero.winRate.toFixed(1)}%`}</td>
              <td><div className="hero-log-row-actions">
                <button type="button" className="secondary-button hero-log-detail-button" onClick={() => openHeroDetail(hero.name)}>詳細</button>
                <button type="button" className="icon-button hero-log-edit-button" aria-label={`${hero.name}の合計成績を修正`} title="合計成績を修正" onClick={() => editHeroTotalStats(hero.name)}><Pencil size={16}/></button>
              </div></td>
            </tr>)}
          </tbody></table></div>"""
if old_ui not in app:
    sys.exit("エラー: 合計成績テーブルの表示コードが想定と異なります。App.tsx は変更していません。")
app = app.replace(old_ui, new_ui, 1)

css_patch = r"""

/* HERO SUMMARY SORT AND RECENT MATCH FILTER v1 */
.hero-summary-toolbar { display:flex; justify-content:flex-end; align-items:center; flex-wrap:wrap; gap:8px; margin:0 0 12px; }
.hero-summary-filter-buttons { display:flex; flex-wrap:wrap; gap:5px; }
.hero-summary-filter-button, .hero-summary-sort-button { border:1px solid var(--line,#303951); border-radius:7px; background:var(--surface-muted,#0e1526); color:var(--text-soft,#b5cbd5); font-size:10px; font-weight:700; cursor:pointer; }
.hero-summary-filter-button { min-height:32px; padding:6px 10px; }
.hero-summary-filter-button.active { border-color:#e9822b; background:#4a2b18; color:#ffad62; }
.hero-summary-reset-button { min-height:32px; padding:6px 10px; font-size:10px; }
.hero-summary-sort-button { padding:5px 3px; border-color:transparent; background:transparent; color:inherit; white-space:nowrap; }
.hero-summary-sort-button:hover { color:var(--accent-strong,#04bfd0); }
.hero-summary-filter-note { margin:-3px 0 11px; color:var(--text-muted,#8e99b4); font-size:10px; line-height:1.6; }
@media (max-width:700px) {
  .hero-summary-toolbar { justify-content:flex-start; gap:6px; }
  .hero-summary-filter-buttons { flex:1 1 100%; }
  .hero-summary-filter-button { flex:1 1 auto; padding:6px 7px; }
  .hero-summary-reset-button { margin-left:auto; }
  .hero-log-table.hero-log-main-table .hero-summary-sort-button { font-size:8px; padding:3px 0; white-space:normal; }
}
"""
app_file.write_text(app, encoding="utf-8")
css_file.write_text(css.rstrip() + "\n" + css_patch, encoding="utf-8")
print("改善を適用しました。")
print("- 試合数・勝ち数・勝率の見出しタップで昇順／降順ソート")
print("- ソートリセットボタンを追加")
print("- 全試合／直近10戦／直近50戦／直近100戦の切り替えを追加")
print("- 直近N戦では各ヒーローのアプリ内記録を使用。手入力累計は含めません。")
print(f"- 変更前のバックアップ: {backup_dir}")
print("次に npm run build を実行してください。")
