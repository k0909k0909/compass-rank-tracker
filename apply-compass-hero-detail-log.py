from pathlib import Path

APP = Path('src/App.tsx')
CSS = Path('src/style-improvements.css')


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: 置換元が1か所ではありません（{count}か所）。ファイルは変更していません。')
    return source.replace(old, new, 1)


def main() -> None:
    if not APP.exists() or not CSS.exists():
        raise SystemExit('src/App.tsx または src/style-improvements.css が見つかりません。リポジトリ直下で実行してください。')

    app = APP.read_text(encoding='utf-8')
    css = CSS.read_text(encoding='utf-8')
    if 'heroBaseStats?: Record<string, HeroBaseStat>' in app and 'ヒーロー詳細ログ' in app and 'hero-detail-log-styles-v1' in css:
        print('ヒーロー詳細ログはすでに追加されています。変更はありません。')
        return

    # すべてメモリ上で変更し、全置換箇所を検証してから書き込みます。
    updated = app
    updated = replace_once(
        updated,
        "type Hero = { name: string; role: Role; favorite?: boolean; aliases?: string[] }\n",
        "type Hero = { name: string; role: Role; favorite?: boolean; aliases?: string[] }\ntype HeroBaseStat = { battles: number; wins: number }\ntype HeroDetailSection = 'map' | 'ally' | 'enemy'\ntype HeroDetailSortKey = 'battles' | 'wins' | 'winRate'\ntype HeroDetailRow = { name: string; battles: number; wins: number; winRate: number | null; order: number }\n",
        'ヒーロー集計用の型'
    )
    updated = replace_once(
        updated,
        "  stageRotations?: Record<string, string[]>\n}\ntype Page = 'dashboard' | 'add' | 'history' | 'settings'\n",
        "  stageRotations?: Record<string, string[]>\n  /** アプリ導入前の累計試合数・勝ち数。アプリ内記録分と合算して表示 */\n  heroBaseStats?: Record<string, HeroBaseStat>\n}\ntype Page = 'dashboard' | 'add' | 'history' | 'settings' | 'heroStats' | 'heroDetail'\n",
        'StoreとPageの拡張'
    )
    updated = replace_once(
        updated,
        "  form?: Record<string, any>\n}\n",
        "  form?: Record<string, any>\n  selectedHeroDetailName?: string\n}\n",
        '下書きに詳細選択を保存'
    )
    updated = replace_once(
        updated,
        "  const stageRotations: Record<string, string[]> = {}\n",
        "  const heroBaseStats: Record<string, HeroBaseStat> = {}\n  if (input?.heroBaseStats && typeof input.heroBaseStats === 'object' && !Array.isArray(input.heroBaseStats)) {\n    Object.entries(input.heroBaseStats).forEach(([name, value]) => {\n      if (!value || typeof value !== 'object') return\n      const rawBattles = Number(value.battles)\n      const rawWins = Number(value.wins)\n      const battles = Number.isFinite(rawBattles) ? Math.max(0, Math.floor(rawBattles)) : 0\n      const wins = Number.isFinite(rawWins) ? Math.min(battles, Math.max(0, Math.floor(rawWins))) : 0\n      heroBaseStats[name] = { battles, wins }\n    })\n  }\n  const stageRotations: Record<string, string[]> = {}\n",
        '過去分統計の正規化'
    )
    updated = replace_once(
        updated,
        "    activeSeason, lastSeasonResetMonth: resetMonth, stageRotations\n",
        "    activeSeason, lastSeasonResetMonth: resetMonth, stageRotations, heroBaseStats\n",
        '正規化データへ過去分統計を追加'
    )
    updated = replace_once(
        updated,
        "    ['dashboard', 'add', 'history', 'settings'].includes(savedDraft?.page ?? '') ? savedDraft!.page! : 'dashboard'\n",
        "    ['dashboard', 'add', 'history', 'settings', 'heroStats', 'heroDetail'].includes(savedDraft?.page ?? '') ? savedDraft!.page! : 'dashboard'\n",
        '詳細画面の復元'
    )
    updated = replace_once(
        updated,
        "  const [historyMode, setHistoryMode] = useState<'all' | Mode>('all')\n",
        "  const [historyMode, setHistoryMode] = useState<'all' | Mode>('all')\n  const [selectedHeroDetailName, setSelectedHeroDetailName] = useState(savedDraft?.selectedHeroDetailName ?? '')\n  const [heroBaseDrafts, setHeroBaseDrafts] = useState<Record<string, { battles: string; wins: string }>>({})\n  const [heroDetailMode, setHeroDetailMode] = useState<'all' | Mode>('all')\n  const [heroDetailRecentCount, setHeroDetailRecentCount] = useState<'all' | '10' | '30' | '50' | '100'>('all')\n  const [heroDetailSection, setHeroDetailSection] = useState<HeroDetailSection>('map')\n  const [heroDetailSortKey, setHeroDetailSortKey] = useState<HeroDetailSortKey>('winRate')\n  const [heroDetailSortDirection, setHeroDetailSortDirection] = useState<'asc' | 'desc'>('desc')\n",
        'ヒーロー詳細ログの画面状態'
    )
    updated = replace_once(
        updated,
        "        page, form, editingId, recordSlide, lockAlly1, lockAlly2, rankTierDraft, rankPointsDraft\n",
        "        page, form, editingId, recordSlide, lockAlly1, lockAlly2, rankTierDraft, rankPointsDraft, selectedHeroDetailName\n",
        '詳細画面の下書き保存'
    )
    updated = replace_once(
        updated,
        "  }, [page, form, editingId, recordSlide, lockAlly1, lockAlly2, rankTierDraft, rankPointsDraft])\n",
        "  }, [page, form, editingId, recordSlide, lockAlly1, lockAlly2, rankTierDraft, rankPointsDraft, selectedHeroDetailName])\n",
        '詳細画面選択の下書き依存関係'
    )
    updated = replace_once(
        updated,
        "  const availableMonths = useMemo(() => [...new Set(store.matches.map(m => m.playedAt.slice(0, 7)))].sort((a, b) => b.localeCompare(a)), [store.matches])\n",
        "  const availableMonths = useMemo(() => [...new Set(store.matches.map(m => m.playedAt.slice(0, 7)))].sort((a, b) => b.localeCompare(a)), [store.matches])\n  const heroSummaryRows = useMemo(() => store.heroes.map(hero => {\n    const base = store.heroBaseStats?.[hero.name] ?? { battles: 0, wins: 0 }\n    const recorded = store.matches.filter(match => match.heroName === hero.name)\n    const battles = base.battles + recorded.length\n    const wins = base.wins + recorded.filter(match => match.result === 'win').length\n    return { ...hero, baseBattles: base.battles, baseWins: base.wins, totalBattles: battles, totalWins: wins, winRate: battles > 0 ? wins / battles * 100 : null }\n  }).sort((a, b) => (heroOrderIndex.get(a.name) ?? Number.MAX_SAFE_INTEGER) - (heroOrderIndex.get(b.name) ?? Number.MAX_SAFE_INTEGER)), [store.heroes, store.heroBaseStats, store.matches])\n  const selectedHeroDetail = store.heroes.find(hero => hero.name === selectedHeroDetailName)\n  const selectedHeroDetailRecords = useMemo(() => {\n    let records = store.matches.filter(match => match.heroName === selectedHeroDetailName && (heroDetailMode === 'all' || (match.mode ?? 'バトアリ') === heroDetailMode))\n      .sort((a, b) => b.playedAt.localeCompare(a.playedAt))\n    if (heroDetailRecentCount !== 'all') records = records.slice(0, Number(heroDetailRecentCount))\n    return records\n  }, [store.matches, selectedHeroDetailName, heroDetailMode, heroDetailRecentCount])\n  const heroDetailRows = useMemo<HeroDetailRow[]>(() => {\n    let names: string[]\n    if (heroDetailSection === 'map') {\n      names = [...new Set([...store.maps, ...selectedHeroDetailRecords.map(match => match.mapName)])]\n    } else {\n      const teamNames = selectedHeroDetailRecords.flatMap(match => heroDetailSection === 'ally' ? (match.allyHeroNames ?? []) : (match.enemyHeroNames ?? []))\n      names = [...new Set([...store.heroes.map(hero => hero.name), ...teamNames.filter(Boolean)])]\n        .sort((a, b) => (heroOrderIndex.get(a) ?? Number.MAX_SAFE_INTEGER) - (heroOrderIndex.get(b) ?? Number.MAX_SAFE_INTEGER) || a.localeCompare(b, 'ja'))\n    }\n    const rows = names.map((name, order) => {\n      const related = selectedHeroDetailRecords.filter(match => heroDetailSection === 'map'\n        ? match.mapName === name\n        : (heroDetailSection === 'ally' ? (match.allyHeroNames ?? []) : (match.enemyHeroNames ?? [])).includes(name))\n      const battles = related.length\n      const wins = related.filter(match => match.result === 'win').length\n      return { name, battles, wins, winRate: battles > 0 ? wins / battles * 100 : null, order }\n    })\n    return rows.sort((a, b) => {\n      if (a.battles === 0 && b.battles > 0) return 1\n      if (a.battles > 0 && b.battles === 0) return -1\n      if (a.battles === 0 && b.battles === 0) return a.order - b.order\n      const aValue = heroDetailSortKey === 'winRate' ? (a.winRate ?? 0) : heroDetailSortKey === 'wins' ? a.wins : a.battles\n      const bValue = heroDetailSortKey === 'winRate' ? (b.winRate ?? 0) : heroDetailSortKey === 'wins' ? b.wins : b.battles\n      const difference = aValue - bValue\n      return (heroDetailSortDirection === 'desc' ? -difference : difference) || a.order - b.order\n    })\n  }, [store.maps, store.heroes, selectedHeroDetailRecords, heroDetailSection, heroDetailSortKey, heroDetailSortDirection])\n",
        'ヒーロー集計・詳細内訳'
    )
    updated = replace_once(
        updated,
        "  function deleteMatch(id: string) {\n    if (!window.confirm('この試合記録を削除しますか？')) return\n    setStore(s => ({ ...s, matches: s.matches.filter(m => m.id !== id) }))\n  }\n",
        "  function deleteMatch(id: string) {\n    if (!window.confirm('この試合記録を削除しますか？')) return\n    setStore(s => ({ ...s, matches: s.matches.filter(m => m.id !== id) }))\n  }\n  function updateHeroBaseDraft(name: string, field: 'battles' | 'wins', value: string) {\n    const base = store.heroBaseStats?.[name] ?? { battles: 0, wins: 0 }\n    setHeroBaseDrafts(current => ({\n      ...current,\n      [name]: {\n        battles: current[name]?.battles ?? String(base.battles),\n        wins: current[name]?.wins ?? String(base.wins),\n        [field]: value\n      }\n    }))\n  }\n  function saveHeroBaseStats(name: string) {\n    const base = storeRef.current.heroBaseStats?.[name] ?? { battles: 0, wins: 0 }\n    const draft = heroBaseDrafts[name] ?? { battles: String(base.battles), wins: String(base.wins) }\n    const battles = Number(draft.battles)\n    const wins = Number(draft.wins)\n    if (!Number.isInteger(battles) || battles < 0 || !Number.isInteger(wins) || wins < 0 || wins > battles) {\n      notify('試合数・勝ち数は0以上の整数で、勝ち数は試合数以下にしてください')\n      return\n    }\n    const heroBaseStats = { ...(storeRef.current.heroBaseStats ?? {}) }\n    if (battles === 0 && wins === 0) delete heroBaseStats[name]\n    else heroBaseStats[name] = { battles, wins }\n    const updated: Store = { ...storeRef.current, heroBaseStats }\n    storeRef.current = updated\n    setStore(updated)\n    setHeroBaseDrafts(current => ({ ...current, [name]: { battles: String(battles), wins: String(wins) } }))\n    notify(`${name} の過去分データを保存しました`)\n  }\n  function openHeroDetail(name: string) {\n    setSelectedHeroDetailName(name)\n    setHeroDetailMode('all')\n    setHeroDetailRecentCount('all')\n    setHeroDetailSection('map')\n    setHeroDetailSortKey('winRate')\n    setHeroDetailSortDirection('desc')\n    setPage('heroDetail')\n  }\n",
        '過去分統計編集と詳細画面遷移'
    )
    updated = replace_once(
        updated,
        "        <NavItem active={page === 'history'} icon={<History size={18}/>} label=\"戦績一覧\" onClick={() => setPage('history')} />\n        <NavItem active={page === 'settings'} icon={<Settings size={18}/>} label=\"設定・バックアップ\" onClick={() => setPage('settings')} />\n",
        "        <NavItem active={page === 'history'} icon={<History size={18}/>} label=\"戦績一覧\" onClick={() => setPage('history')} />\n        <NavItem active={page === 'heroStats' || page === 'heroDetail'} icon={<Trophy size={18}/>} label=\"ヒーロー詳細ログ\" onClick={() => setPage('heroStats')} />\n        <NavItem active={page === 'settings'} icon={<Settings size={18}/>} label=\"設定・バックアップ\" onClick={() => setPage('settings')} />\n",
        'MENUへの追加'
    )
    updated = replace_once(
        updated,
        "        <div><h1>{({ dashboard: 'ホーム', add: '試合を記録', history: '戦績一覧', settings: '設定・バックアップ' } as Record<Page, string>)[page]}</h1></div>\n",
        "        <div><h1>{({ dashboard: 'ホーム', add: '試合を記録', history: '戦績一覧', settings: '設定・バックアップ', heroStats: 'ヒーロー詳細ログ', heroDetail: 'ヒーロー詳細ログ' } as Record<Page, string>)[page]}</h1></div>\n",
        '画面タイトルの追加'
    )

    hero_pages = r'''      {page === 'heroStats' && <section className="page-stack hero-log-page">
        <div className="content-card">
          <div className="section-heading"><div><h3>ヒーロー別の累計成績</h3><p>過去分の数値と、このアプリで記録した試合を合算して表示します。</p></div><div className="round-icon"><Trophy size={20}/></div></div>
          <p className="hero-log-explanation">「過去分」はアプリを使い始める前の累計です。過去分の試合数・勝ち数を入力して保存すると、今後このアプリで記録した試合数・勝ち数が自動で加算されます。勝率は合計勝ち数 ÷ 合計試合数です。</p>
          <div className="table-wrap hero-log-table-wrap"><table className="hero-log-table"><thead><tr><th>ヒーロー</th><th>過去分 試合数</th><th>過去分 勝ち数</th><th>合計試合数</th><th>合計勝ち数</th><th>勝率</th><th>詳細</th></tr></thead><tbody>
            {heroSummaryRows.map(hero => <tr key={hero.name}>
              <td><div className="hero-log-name"><strong>{hero.name}</strong><small>{hero.role}</small></div></td>
              <td><input className="hero-log-number-input" type="number" min="0" step="1" inputMode="numeric" aria-label={`${hero.name}の過去分試合数`} value={heroBaseDrafts[hero.name]?.battles ?? String(hero.baseBattles)} onChange={event => updateHeroBaseDraft(hero.name, 'battles', event.target.value)}/></td>
              <td><input className="hero-log-number-input" type="number" min="0" step="1" inputMode="numeric" aria-label={`${hero.name}の過去分勝ち数`} value={heroBaseDrafts[hero.name]?.wins ?? String(hero.baseWins)} onChange={event => updateHeroBaseDraft(hero.name, 'wins', event.target.value)}/></td>
              <td className="hero-log-number-cell">{hero.totalBattles.toLocaleString()}</td>
              <td className="hero-log-number-cell">{hero.totalWins.toLocaleString()}</td>
              <td className="hero-log-rate">{hero.winRate === null ? '—' : `${hero.winRate.toFixed(1)}%`}</td>
              <td><div className="hero-log-row-actions"><button className="secondary-button hero-log-save-button" onClick={() => saveHeroBaseStats(hero.name)}>過去分を保存</button><button className="primary-button hero-log-detail-button" onClick={() => openHeroDetail(hero.name)}>詳細を見る</button></div></td>
            </tr>)}
          </tbody></table></div>
        </div>
      </section>}

      {page === 'heroDetail' && <section className="page-stack hero-log-page">
        <div className="content-card">
          <div className="section-heading hero-detail-heading"><div><h3>{selectedHeroDetail?.name ?? selectedHeroDetailName} の詳細</h3><p>{selectedHeroDetail?.role ?? 'ヒーロー'} のマップ・味方・敵ヒーロー別成績</p></div><button className="secondary-button" onClick={() => setPage('heroStats')}>← 一覧へ戻る</button></div>
          <div className="hero-detail-controls">
            <label>モード<select value={heroDetailMode} onChange={event => setHeroDetailMode(event.target.value as 'all' | Mode)}><option value="all">すべて</option><option value="バトアリ">バトアリ</option><option value="フリバ">フリバ</option><option value="カスタム">カスタム</option></select></label>
            <label>対象試合<select value={heroDetailRecentCount} onChange={event => setHeroDetailRecentCount(event.target.value as typeof heroDetailRecentCount)}><option value="all">全試合</option><option value="10">直近10戦</option><option value="30">直近30戦</option><option value="50">直近50戦</option><option value="100">直近100戦</option></select></label>
          </div>
          <div className="hero-detail-summary">
            <div className="hero-detail-stat"><small>対象試合数</small><strong>{selectedHeroDetailRecords.length.toLocaleString()}</strong></div>
            <div className="hero-detail-stat"><small>勝ち数</small><strong>{selectedHeroDetailRecords.filter(match => match.result === 'win').length.toLocaleString()}</strong></div>
            <div className="hero-detail-stat"><small>勝率</small><strong>{selectedHeroDetailRecords.length ? `${(selectedHeroDetailRecords.filter(match => match.result === 'win').length / selectedHeroDetailRecords.length * 100).toFixed(1)}%` : '—'}</strong></div>
          </div>
          <p className="hero-log-explanation">この内訳はアプリ内に記録された試合から集計しています。手入力した過去分にはマップ・味方・敵の情報がないため、内訳には含めません。</p>
        </div>
        <div className="content-card">
          <div className="hero-detail-tabs">
            <button className={heroDetailSection === 'map' ? 'active' : ''} onClick={() => setHeroDetailSection('map')}>マップ別</button>
            <button className={heroDetailSection === 'ally' ? 'active' : ''} onClick={() => setHeroDetailSection('ally')}>味方ヒーロー別</button>
            <button className={heroDetailSection === 'enemy' ? 'active' : ''} onClick={() => setHeroDetailSection('enemy')}>敵ヒーロー別</button>
          </div>
          <div className="hero-detail-sort-controls">
            <label>並べ替え<select value={heroDetailSortKey} onChange={event => setHeroDetailSortKey(event.target.value as HeroDetailSortKey)}><option value="winRate">勝率</option><option value="wins">勝ち数</option><option value="battles">試合数</option></select></label>
            <button className="secondary-button" onClick={() => setHeroDetailSortDirection(current => current === 'desc' ? 'asc' : 'desc')}>{heroDetailSortDirection === 'desc' ? '降順 ↓' : '昇順 ↑'}</button>
          </div>
          <div className="table-wrap hero-detail-table-wrap"><table className="hero-log-table hero-detail-table"><thead><tr><th>{heroDetailSection === 'map' ? 'マップ' : heroDetailSection === 'ally' ? '味方ヒーロー' : '敵ヒーロー'}</th><th>試合数</th><th>勝ち数</th><th>勝率</th></tr></thead><tbody>
            {heroDetailRows.map(row => <tr key={row.name} className={row.battles === 0 ? 'hero-detail-no-data' : ''}><td>{row.name}</td><td>{row.battles > 0 ? row.battles.toLocaleString() : '—'}</td><td>{row.battles > 0 ? row.wins.toLocaleString() : '—'}</td><td>{row.winRate === null ? '—' : `${row.winRate.toFixed(1)}%`}</td></tr>)}
          </tbody></table></div>
        </div>
      </section>}

'''
    updated = replace_once(
        updated,
        "      {page === 'settings' && <section className=\"page-stack\">\n",
        hero_pages + "      {page === 'settings' && <section className=\"page-stack\">\n",
        'ヒーロー一覧・詳細画面の追加'
    )

    css_marker = '/* hero-detail-log-styles-v1 */'
    css_addition = '''

/* hero-detail-log-styles-v1 */
.hero-log-page { min-width: 0; }
.hero-log-explanation { margin: 0 0 14px; color: var(--text-muted, #8e99b4); font-size: 11px; line-height: 1.8; }
.hero-log-table-wrap, .hero-detail-table-wrap { width: 100%; overflow-x: auto; }
.hero-log-table { width: 100%; min-width: 850px; border-collapse: separate; border-spacing: 0; font-size: 11px; }
.hero-log-table th { padding: 11px 10px; color: var(--text-muted, #8e99b4); background: var(--surface-muted, #0b1320); text-align: left; white-space: nowrap; font-weight: 700; border-bottom: 1px solid var(--line, #293c4b); }
.hero-log-table td { padding: 9px 10px; color: var(--text-main, #edf9fc); border-bottom: 1px solid var(--line, #293c4b); vertical-align: middle; white-space: nowrap; }
.hero-log-name { display: flex; flex-direction: column; gap: 3px; min-width: 120px; }
.hero-log-name small { color: var(--text-muted, #829aa8); font-size: 10px; }
.hero-log-number-input { width: 86px; min-height: 34px; padding: 6px 8px; color: var(--text-main, #edf9fc); background: var(--surface-muted, #0b1320); border: 1px solid var(--line, #293c4b); border-radius: 7px; font-size: 11px; font-variant-numeric: tabular-nums; }
.hero-log-number-cell, .hero-log-rate { font-variant-numeric: tabular-nums; font-weight: 700; }
.hero-log-rate { color: var(--accent-strong, #04bfd0) !important; }
.hero-log-row-actions { display: flex; gap: 6px; align-items: center; }
.hero-log-save-button, .hero-log-detail-button { padding: 7px 9px; font-size: 10px; }
.hero-detail-heading { align-items: center; }
.hero-detail-controls, .hero-detail-sort-controls { display: flex; flex-wrap: wrap; gap: 12px; align-items: end; margin: 5px 0 16px; }
.hero-detail-controls label, .hero-detail-sort-controls label { display: grid; gap: 6px; color: var(--text-soft, #b5cbd5); font-size: 10px; font-weight: 700; }
.hero-detail-controls select, .hero-detail-sort-controls select { min-width: 145px; }
.hero-detail-summary { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin: 14px 0; }
.hero-detail-stat { display: flex; flex-direction: column; gap: 7px; padding: 13px; border: 1px solid var(--line, #293c4b); border-radius: 10px; background: var(--surface-muted, #0b1320); }
.hero-detail-stat small { color: var(--text-muted, #829aa8); font-size: 10px; }
.hero-detail-stat strong { color: var(--text-main, #edf9fc); font-size: 20px; font-variant-numeric: tabular-nums; }
.hero-detail-tabs { display: flex; flex-wrap: wrap; gap: 7px; margin-bottom: 16px; }
.hero-detail-tabs button { padding: 9px 13px; border: 1px solid var(--line, #293c4b); border-radius: 8px; color: var(--text-soft, #b5cbd5); background: var(--surface-muted, #0b1320); font-size: 10px; font-weight: 700; }
.hero-detail-tabs button.active { color: var(--accent-strong, #04bfd0); border-color: var(--accent-line, #24616c); background: var(--accent-soft, #10313a); }
.hero-detail-sort-controls { justify-content: flex-end; margin: 0 0 12px; }
.hero-detail-table { min-width: 520px; }
.hero-detail-table th:not(:first-child), .hero-detail-table td:not(:first-child) { text-align: right; }
.hero-detail-table .hero-detail-no-data td { color: var(--text-muted, #829aa8); }
@media (max-width: 700px) {
  .hero-log-table { min-width: 820px; }
  .hero-detail-summary { gap: 7px; }
  .hero-detail-stat { padding: 10px; }
  .hero-detail-stat strong { font-size: 17px; }
  .hero-detail-heading { align-items: flex-start; }
  .hero-detail-controls { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .hero-detail-controls label, .hero-detail-controls select { min-width: 0; width: 100%; }
}
'''
    if css_marker not in css:
        css = css.rstrip() + css_addition + '\n'

    # JSX/TSの編集がすべて通った後にだけ、元ファイルをバックアップして書き込みます。
    app_backup = APP.with_name('App.tsx.before-hero-detail-log.bak')
    css_backup = CSS.with_name('style-improvements.css.before-hero-detail-log.bak')
    if app_backup.exists() or css_backup.exists():
        raise SystemExit('バックアップファイルがすでに存在します。先に内容を確認してください。')
    app_backup.write_text(app, encoding='utf-8')
    css_backup.write_text(CSS.read_text(encoding='utf-8'), encoding='utf-8')
    APP.write_text(updated, encoding='utf-8')
    CSS.write_text(css, encoding='utf-8')
    print('ヒーロー詳細ログを追加しました。')
    print('変更ファイル: src/App.tsx, src/style-improvements.css')
    print('バックアップ: src/App.tsx.before-hero-detail-log.bak, src/style-improvements.css.before-hero-detail-log.bak')
    print('次に npm run build を実行し、成功を確認してください。')


if __name__ == '__main__':
    main()
