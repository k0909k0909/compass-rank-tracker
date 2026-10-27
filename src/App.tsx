import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { createClient, type User } from '@supabase/supabase-js'
import { Activity, BarChart3, CalendarDays, Download, FileUp, Gauge, History, Pencil, Plus, Search, Settings, Shield, Swords, Trash2, Trophy, X } from 'lucide-react'
import './style.css'

type Role = 'アタッカー' | 'ガンナー' | 'タンク' | 'スプリンター'
type Result = 'win' | 'loss' | 'draw'
type Hero = { name: string; role: Role }
type Match = {
  id: string; playedAt: string; season: string; heroName: string; heroRole: Role;
  mapName: string; result: Result; rankPoints: number | null; memo: string
}
type Store = { matches: Match[]; heroes: Hero[]; maps: string[] }
type Page = 'dashboard' | 'add' | 'history' | 'settings'
type CloudContextValue = { saveCloudStore: (store: Store) => void; syncStatus: string }
const CloudContext = createContext<CloudContextValue | null>(null)

const initialHeroes: Hero[] = [
  { name: 'サーティーン', role: 'ガンナー' },
  { name: 'ファースト', role: 'タンク' },
  { name: 'ギルガメッシュ', role: 'ガンナー' },
  { name: 'アーチャー', role: 'アタッカー' },
  { name: 'エドワード・エルリック', role: 'タンク' },
  { name: 'タココ', role: 'アタッカー' },
  { name: '初音ミク', role: 'スプリンター' },
  { name: '鏡音レン', role: 'タンク' },
  { name: 'ポロロッチョ', role: 'アタッカー' },
  { name: 'ポプ子＆ピピ美', role: 'タンク' },
]
const initialMaps = [
  'でらクランクストリート','けっこいスターパーク','東西たかさん広場','グレートウォール',
  '立体交差のある風景','光と闇のライブステージ','妖華帝都ケルパーズの散歩道','ちゅら島リゾート',
  'って〜！つっぺる工事現場','太鼓で祭りだドーン！','おいでやす鳥居通り','かけだせ！じっぱか城',
  'どっひゃぁ〜！なっから遺跡','Castle of the Silver Feet','マジきてる #夜光犯罪特区',
  'Hello :-) irregular World','なまらモーモーパーク','おっかねぇ！氷焔神域ケイオスブルク',
  'バリバリ！てげてげモーターウェイ','いこっさ！ダイダイダイナソー博物館','ジャンジャン麻雀の間','ぼちぼちボッチ墓地（毒）'
]
const roles: Role[] = ['アタッカー', 'ガンナー', 'タンク', 'スプリンター']
const storageKey = 'compass-rank-tracker-v1'
const today = () => new Date().toLocaleDateString('sv-SE')

function loadStore(): Store {
  try {
    const raw = localStorage.getItem(storageKey)
    if (raw) {
      const parsed = JSON.parse(raw) as Store
      return { matches: parsed.matches ?? [], heroes: parsed.heroes?.length ? parsed.heroes : initialHeroes, maps: parsed.maps?.length ? parsed.maps : initialMaps }
    }
  } catch { /* broken local data: start clean */ }
  return { matches: [], heroes: initialHeroes, maps: initialMaps }
}
function resultLabel(result: Result) { return result === 'win' ? '勝ち' : result === 'loss' ? '負け' : '引き分け' }
function percent(n: number, d: number) { return d ? `${Math.round(n / d * 100)}%` : '—' }

function TrackerApp() {
  const cloud = useContext(CloudContext)
  const [store, setStore] = useState<Store>(loadStore)
  const [page, setPage] = useState<Page>('dashboard')
  const [toast, setToast] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [historyQuery, setHistoryQuery] = useState('')
  const [historyResult, setHistoryResult] = useState<'all' | Result>('all')
  const [historyHero, setHistoryHero] = useState('all')
  const [historyMonth, setHistoryMonth] = useState('all')
  const importRef = useRef<HTMLInputElement>(null)
  const [form, setForm] = useState({
    playedAt: today(), season: '', heroName: initialHeroes[0].name, mapName: initialMaps[0],
    result: 'win' as Result, rankPoints: '', memo: ''
  })
  const [heroDraft, setHeroDraft] = useState('')
  const [heroRoleDraft, setHeroRoleDraft] = useState<Role>('アタッカー')
  const [mapDraft, setMapDraft] = useState('')

  useEffect(() => { localStorage.setItem(storageKey, JSON.stringify(store)); cloud?.saveCloudStore(store) }, [store])
  const sortedMatches = useMemo(() => [...store.matches].sort((a,b) => b.playedAt.localeCompare(a.playedAt)), [store.matches])
  const wins = store.matches.filter(m => m.result === 'win').length
  const losses = store.matches.filter(m => m.result === 'loss').length
  const winRate = percent(wins, wins + losses)
  const latestRank = [...store.matches].filter(m => m.rankPoints !== null).sort((a,b) => b.playedAt.localeCompare(a.playedAt))[0]?.rankPoints
  const currentMonth = today().slice(0, 7)
  const currentMonthMatches = store.matches.filter(m => m.playedAt.slice(0, 7) === currentMonth)
  const currentMonthWins = currentMonthMatches.filter(m => m.result === 'win').length
  const currentMonthLosses = currentMonthMatches.filter(m => m.result === 'loss').length
  const currentStreak = useMemo(() => {
    const chronological = [...store.matches].sort((a,b) => b.playedAt.localeCompare(a.playedAt))
    const first = chronological[0]?.result
    if (first !== 'win' && first !== 'loss') return { result: '—', count: 0 }
    let count = 0
    for (const match of chronological) { if (match.result !== first) break; count++ }
    return { result: first === 'win' ? '連勝' : '連敗', count }
  }, [store.matches])
  const monthlyStats = useMemo(() => {
    const buckets = new Map<string, Match[]>()
    for (const match of store.matches) { const month = match.playedAt.slice(0, 7); buckets.set(month, [...(buckets.get(month) ?? []), match]) }
    return [...buckets.entries()].sort((a,b) => b[0].localeCompare(a[0])).slice(0, 6).map(([month, matches]) => ({
      month, total: matches.length, wins: matches.filter(m => m.result === 'win').length, losses: matches.filter(m => m.result === 'loss').length,
      draws: matches.filter(m => m.result === 'draw').length, rate: percent(matches.filter(m => m.result === 'win').length, matches.filter(m => m.result !== 'draw').length)
    }))
  }, [store.matches])
  const heroStats = useMemo(() => {
    const buckets = new Map<string, Match[]>()
    for (const match of store.matches) buckets.set(match.heroName, [...(buckets.get(match.heroName) ?? []), match])
    return [...buckets.entries()].map(([name, matches]) => ({ name, role: matches[0].heroRole, total: matches.length, wins: matches.filter(m => m.result === 'win').length, losses: matches.filter(m => m.result === 'loss').length, draws: matches.filter(m => m.result === 'draw').length, rate: percent(matches.filter(m => m.result === 'win').length, matches.filter(m => m.result !== 'draw').length) })).sort((a,b) => b.total-a.total || a.name.localeCompare(b.name, 'ja'))
  }, [store.matches])
  const availableMonths = useMemo(() => [...new Set(store.matches.map(m => m.playedAt.slice(0, 7)))].sort((a,b) => b.localeCompare(a)), [store.matches])
  const filteredMatches = useMemo(() => {
    const query = historyQuery.trim().toLocaleLowerCase()
    return sortedMatches.filter(m => (historyResult === 'all' || m.result === historyResult) && (historyHero === 'all' || m.heroName === historyHero) && (historyMonth === 'all' || m.playedAt.startsWith(historyMonth)) && (!query || `${m.heroName} ${m.mapName} ${m.memo} ${m.season}`.toLocaleLowerCase().includes(query)))
  }, [sortedMatches, historyQuery, historyResult, historyHero, historyMonth])

  function notify(message: string) { setToast(message); window.setTimeout(() => setToast(''), 2600) }
  function startNewMatch() {
    setEditingId(null)
    setForm({ playedAt: today(), season: '', heroName: store.heroes[0]?.name ?? '', mapName: store.maps[0] ?? '', result: 'win', rankPoints: '', memo: '' })
    setPage('add')
  }
  function beginEditMatch(match: Match) {
    setEditingId(match.id)
    setForm({ playedAt: match.playedAt, season: match.season, heroName: match.heroName, mapName: match.mapName, result: match.result, rankPoints: match.rankPoints === null ? '' : String(match.rankPoints), memo: match.memo })
    setPage('add')
  }
  function saveMatch(e: React.FormEvent) {
    e.preventDefault()
    const hero = store.heroes.find(h => h.name === form.heroName)
    if (!hero || !form.mapName) { notify('ヒーローとマップを選択してください'); return }
    const pointsText = form.rankPoints.trim()
    const pointsValue = pointsText === '' ? null : Number(pointsText)
    if (pointsValue !== null && !Number.isFinite(pointsValue)) { notify('ランクポイントは数値で入力してください'); return }
    const match: Match = {
      id: editingId ?? crypto.randomUUID(), playedAt: form.playedAt, season: form.season.trim(),
      heroName: hero.name, heroRole: hero.role, mapName: form.mapName, result: form.result,
      rankPoints: pointsValue, memo: form.memo.trim()
    }
    if (editingId) setStore(s => ({ ...s, matches: s.matches.map(m => m.id === editingId ? match : m) }))
    else setStore(s => ({ ...s, matches: [match, ...s.matches] }))
    const wasEditing = editingId !== null
    setEditingId(null)
    setForm(f => ({ ...f, season: '', rankPoints: '', memo: '' }))
    setPage('dashboard')
    notify(wasEditing ? '試合記録を更新しました' : '試合を記録しました')
  }
  function deleteMatch(id: string) {
    if (!window.confirm('この試合記録を削除しますか？')) return
    setStore(s => ({ ...s, matches: s.matches.filter(m => m.id !== id) }))
  }
  function exportData() {
    const blob = new Blob([JSON.stringify({ version: 1, exportedAt: new Date().toISOString(), ...store }, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = `compass-record-${today()}.json`; a.click()
    URL.revokeObjectURL(url); notify('バックアップを保存しました')
  }
  function importData(file?: File) {
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => {
      try {
        const data = JSON.parse(String(reader.result))
        if (!Array.isArray(data.matches) || !Array.isArray(data.heroes) || !Array.isArray(data.maps)) throw new Error()
        if (!window.confirm('現在のデータをバックアップ内容で置き換えます。よろしいですか？')) return
        setStore({ matches: data.matches, heroes: data.heroes, maps: data.maps })
        notify('バックアップを復元しました')
      } catch { notify('ファイルを読み込めませんでした。正しいバックアップか確認してください') }
    }
    reader.readAsText(file)
  }
  function addHero() {
    const name = heroDraft.trim()
    if (!name) return
    if (store.heroes.some(h => h.name === name)) { notify('同じ名前のヒーローが登録済みです'); return }
    setStore(s => ({ ...s, heroes: [...s.heroes, { name, role: heroRoleDraft }] }))
    setHeroDraft(''); notify('ヒーローを追加しました')
  }
  function addMap() {
    const name = mapDraft.trim()
    if (!name) return
    if (store.maps.includes(name)) { notify('同じ名前のマップが登録済みです'); return }
    setStore(s => ({ ...s, maps: [...s.maps, name] }))
    setMapDraft(''); notify('マップを追加しました')
  }
  function removeHero(name: string) {
    if (store.matches.some(m => m.heroName === name)) { notify('試合記録に使用中のため削除できません'); return }
    if (window.confirm(`「${name}」を一覧から削除しますか？`)) setStore(s => ({ ...s, heroes: s.heroes.filter(h => h.name !== name) }))
  }
  function removeMap(name: string) {
    if (store.matches.some(m => m.mapName === name)) { notify('試合記録に使用中のため削除できません'); return }
    if (window.confirm(`「${name}」を一覧から削除しますか？`)) setStore(s => ({ ...s, maps: s.maps.filter(m => m !== name) }))
  }

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand-mark"><Swords size={23}/></div>
      <div className="brand-copy"><strong>コンパス戦績ノート</strong><span>RANK TRACKER</span></div>
      <div className="side-label">MENU</div>
      <nav>
        <NavItem active={page==='dashboard'} icon={<Gauge size={18}/>} label="ダッシュボード" onClick={() => setPage('dashboard')} />
        <NavItem active={page==='add'} icon={<Plus size={18}/>} label="試合を記録" onClick={startNewMatch} />
        <NavItem active={page==='history'} icon={<History size={18}/>} label="戦績一覧" onClick={() => setPage('history')} />
        <NavItem active={page==='settings'} icon={<Settings size={18}/>} label="設定・バックアップ" onClick={() => setPage('settings')} />
      </nav>
      <div className="sidebar-foot"><Shield size={15}/> {cloud ? `クラウド同期：${cloud.syncStatus}` : 'この端末に保存'}</div>
    </aside>
    <main className="main-content">
      <header className="topbar">
        <div><div className="eyebrow">#コンパス MATCH LOG</div><h1>{({dashboard:'ダッシュボード', add:'試合を記録', history:'戦績一覧', settings:'設定・バックアップ'} as Record<Page,string>)[page]}</h1></div>
        <button className="primary-button top-add" onClick={startNewMatch}><Plus size={17}/> 試合を追加</button>
      </header>

      {page === 'dashboard' && <section className="page-stack">
        <div className="welcome-panel">
          <div><span className="panel-kicker">YOUR BATTLE RECORD</span><h2>戦績を、次の勝利につなげよう。</h2><p>試合結果とランクポイントを記録して、プレイの傾向を見つけましょう。</p></div>
          <div className="welcome-icon"><Trophy size={39}/></div>
        </div>
        <div className="stats-grid">
          <StatCard icon={<Activity size={19}/>} label="総試合数" value={`${store.matches.length}`} sub="記録した試合" />
          <StatCard icon={<Trophy size={19}/>} label="勝率" value={winRate} sub={`${wins}勝 · ${losses}敗`} />
          <StatCard icon={<BarChart3 size={19}/>} label="最新ランクポイント" value={latestRank == null ? '—' : latestRank.toLocaleString()} sub="記録済みの最新値" />
          <StatCard icon={<CalendarDays size={19}/>} label="今月の試合" value={`${currentMonthMatches.length}`} sub={`${currentMonthWins}勝 · ${currentMonthLosses}敗`} />
          <StatCard icon={<Activity size={19}/>} label="現在の連続結果" value={currentStreak.count ? `${currentStreak.count}${currentStreak.result}` : '—'} sub="最新の記録から集計" />
          <StatCard icon={<Shield size={19}/>} label="登録ヒーロー" value={`${store.heroes.length}`} sub={`マップ ${store.maps.length} 件`} />
        </div>
        <div className="content-card">
          <div className="section-heading"><div><h3>最近の試合</h3><p>直近に記録した試合を表示します</p></div><button className="text-button" onClick={() => setPage('history')}>すべて見る →</button></div>
          {sortedMatches.length ? <MatchTable matches={sortedMatches.slice(0,5)} onEdit={beginEditMatch} onDelete={deleteMatch}/> : <EmptyState onAdd={startNewMatch} />}
        </div>
        <div className="analytics-grid">
          <div className="content-card analytics-card">
            <div className="section-heading"><div><h3>月別成績</h3><p>直近6か月分の記録を集計</p></div></div>
            {monthlyStats.length ? <div className="table-wrap"><table className="mini-table"><thead><tr><th>月</th><th>試合</th><th>勝敗</th><th>勝率</th></tr></thead><tbody>{monthlyStats.map(m=><tr key={m.month}><td>{m.month}</td><td>{m.total}</td><td>{m.wins}勝 {m.losses}敗{m.draws ? ` ${m.draws}分` : ''}</td><td className="rate-cell">{m.rate}</td></tr>)}</tbody></table></div> : <p className="empty-inline">試合を記録すると月別成績が表示されます。</p>}
          </div>
          <div className="content-card analytics-card">
            <div className="section-heading"><div><h3>ヒーロー別成績</h3><p>使用回数の多い順</p></div></div>
            {heroStats.length ? <div className="table-wrap"><table className="mini-table"><thead><tr><th>ヒーロー</th><th>試合</th><th>勝率</th></tr></thead><tbody>{heroStats.slice(0,6).map(h=><tr key={h.name}><td><span className="mini-hero-name">{h.name}</span><small className="mini-hero-role">{h.role}</small></td><td>{h.total}</td><td className="rate-cell">{h.rate}</td></tr>)}</tbody></table></div> : <p className="empty-inline">試合を記録するとヒーロー別成績が表示されます。</p>}
          </div>
        </div>
        <div className="hint-row"><Shield size={17}/><span>{cloud ? 'ログイン中のアカウントに記録を同期します。別の端末でも同じアカウントでログインしてください。' : '端末を変える前にバックアップを保存してください。'}</span></div>
      </section>}

      {page === 'add' && <section className="content-card form-card">
        <div className="section-heading"><div><h3>{editingId ? '試合記録を編集' : '試合内容を入力'}</h3><p>わかる項目だけでも記録できます。</p></div><div className="round-icon"><Swords size={20}/></div></div>
        <form onSubmit={saveMatch} className="match-form">
          <div className="field"><label>試合日</label><input type="date" required value={form.playedAt} onChange={e=>setForm({...form,playedAt:e.target.value})}/></div>
          <div className="field"><label>シーズン <small>任意</small></label><input value={form.season} placeholder="例：2026年10月" onChange={e=>setForm({...form,season:e.target.value})}/></div>
          <div className="field"><label>使用ヒーロー</label><select required value={form.heroName} onChange={e=>setForm({...form,heroName:e.target.value})}>{store.heroes.map(h=><option key={h.name} value={h.name}>{h.name}（{h.role}）</option>)}</select></div>
          <div className="field"><label>マップ</label><select required value={form.mapName} onChange={e=>setForm({...form,mapName:e.target.value})}>{store.maps.map(m=><option key={m}>{m}</option>)}</select></div>
          <div className="field field-wide"><label>試合結果</label><div className="result-options">
            {(['win','loss','draw'] as Result[]).map(r=><button type="button" key={r} className={`result-choice ${form.result===r?'selected '+r:''}`} onClick={()=>setForm({...form,result:r})}>{resultLabel(r)}</button>)}
          </div></div>
          <div className="field"><label>ランクポイント <small>任意</small></label><input type="number" step="1" placeholder="例：1250" value={form.rankPoints} onChange={e=>setForm({...form,rankPoints:e.target.value})}/></div>
          <div className="field field-wide"><label>メモ <small>任意</small></label><textarea rows={3} placeholder="味方編成、反省点、気づいたことなど" value={form.memo} onChange={e=>setForm({...form,memo:e.target.value})}/></div>
          <div className="form-actions"><button type="button" className="secondary-button" onClick={()=>{setEditingId(null);setPage('dashboard')}}>キャンセル</button><button type="submit" className="primary-button">{editingId ? <><Pencil size={17}/> 変更を保存</> : <><Plus size={17}/> 記録を保存</>}</button></div>
        </form>
      </section>}

      {page === 'history' && <section className="content-card">
        <div className="section-heading"><div><h3>すべての戦績</h3><p>{filteredMatches.length} 件表示 / 全 {store.matches.length} 件</p></div><button className="primary-button" onClick={startNewMatch}><Plus size={17}/> 試合を追加</button></div>
        <div className="history-filters">
          <label className="search-field"><Search size={16}/><input value={historyQuery} onChange={e=>setHistoryQuery(e.target.value)} placeholder="ヒーロー・マップ・メモを検索" /></label>
          <select aria-label="結果で絞り込み" value={historyResult} onChange={e=>setHistoryResult(e.target.value as 'all' | Result)}><option value="all">すべての結果</option><option value="win">勝ち</option><option value="loss">負け</option><option value="draw">引き分け</option></select>
          <select aria-label="ヒーローで絞り込み" value={historyHero} onChange={e=>setHistoryHero(e.target.value)}><option value="all">すべてのヒーロー</option>{store.heroes.map(h=><option key={h.name} value={h.name}>{h.name}</option>)}</select>
          <select aria-label="月で絞り込み" value={historyMonth} onChange={e=>setHistoryMonth(e.target.value)}><option value="all">すべての月</option>{availableMonths.map(m=><option key={m} value={m}>{m}</option>)}</select>
        </div>
        {filteredMatches.length ? <MatchTable matches={filteredMatches} onEdit={beginEditMatch} onDelete={deleteMatch}/> : store.matches.length ? <p className="empty-inline">条件に一致する記録がありません。絞り込み条件を変更してください。</p> : <EmptyState onAdd={startNewMatch}/> }
      </section>}

      {page === 'settings' && <section className="page-stack">
        <div className="content-card">
          <div className="section-heading"><div><h3>バックアップと復元</h3><p>記録データを JSON ファイルとして保存できます。</p></div><div className="round-icon"><Shield size={20}/></div></div>
          <div className="backup-actions"><button className="primary-button" onClick={exportData}><Download size={17}/> バックアップを保存</button><button className="secondary-button" onClick={()=>importRef.current?.click()}><FileUp size={17}/> バックアップから復元</button><input ref={importRef} hidden type="file" accept="application/json,.json" onChange={e=>{importData(e.target.files?.[0]);e.currentTarget.value=''}}/></div>
          <p className="small-note">復元すると現在のデータはバックアップの内容に置き換わります。必要に応じて先にバックアップを保存してください。</p>
        </div>
        <div className="content-card">
          <div className="section-heading"><div><h3>ヒーロー管理</h3><p>名前とロールを追加できます。削除は試合記録で未使用の場合のみ可能です。</p></div></div>
          <div className="catalog-add"><input value={heroDraft} placeholder="ヒーロー名" onChange={e=>setHeroDraft(e.target.value)} onKeyDown={e=>e.key==='Enter'&&(e.preventDefault(),addHero())}/><select value={heroRoleDraft} onChange={e=>setHeroRoleDraft(e.target.value as Role)}>{roles.map(r=><option key={r}>{r}</option>)}</select><button className="primary-button" onClick={addHero}><Plus size={16}/> 追加</button></div>
          <div className="catalog-list">{store.heroes.map(h=><div className="catalog-item" key={h.name}><span>{h.name}</span><span className={`role-pill role-${roles.indexOf(h.role)}`}>{h.role}</span><button className="icon-button" aria-label={`${h.name}を削除`} onClick={()=>removeHero(h.name)}><Trash2 size={16}/></button></div>)}</div>
        </div>
        <div className="content-card">
          <div className="section-heading"><div><h3>マップ管理</h3><p>マップを追加できます。削除は試合記録で未使用の場合のみ可能です。</p></div></div>
          <div className="catalog-add"><input value={mapDraft} placeholder="マップ名" onChange={e=>setMapDraft(e.target.value)} onKeyDown={e=>e.key==='Enter'&&(e.preventDefault(),addMap())}/><button className="primary-button" onClick={addMap}><Plus size={16}/> 追加</button></div>
          <div className="catalog-list map-list">{store.maps.map(m=><div className="catalog-item" key={m}><span>{m}</span><button className="icon-button" aria-label={`${m}を削除`} onClick={()=>removeMap(m)}><Trash2 size={16}/></button></div>)}</div>
        </div>
        <div className="content-card future-card"><div className="round-icon"><Activity size={20}/></div><div><h3>現在の機能</h3><p>試合記録の編集・削除、キーワード検索、結果／ヒーロー／月での絞り込み、月別成績、ヒーロー別勝率、連勝・連敗の表示を利用できます。保存・同期の表示を確認しながら使い、定期的にJSONバックアップを保存してください。</p></div></div>
      </section>}
      <footer className="app-footer">コンパス戦績ノート <span>·</span> Version 0.1.0</footer>
    </main>
    {toast && <div className="toast"><span className="toast-dot"/>{toast}<button onClick={()=>setToast('')} aria-label="閉じる"><X size={15}/></button></div>}
  </div>
}

function NavItem({ active, icon, label, onClick }: {active:boolean; icon:React.ReactNode; label:string; onClick:()=>void}) {
  return <button className={`nav-item ${active?'active':''}`} onClick={onClick}>{icon}<span>{label}</span>{active&&<span className="nav-indicator"/>}</button>
}
function StatCard({icon,label,value,sub}:{icon:React.ReactNode;label:string;value:string;sub:string}) {
  return <div className="stat-card"><div className="stat-top"><span>{label}</span><span className="stat-icon">{icon}</span></div><strong>{value}</strong><small>{sub}</small></div>
}
function EmptyState({onAdd}:{onAdd:()=>void}) {
  return <div className="empty-state"><div className="empty-icon"><History size={24}/></div><h4>まだ試合記録がありません</h4><p>最初の試合を記録して、戦績の分析を始めましょう。</p><button className="primary-button" onClick={onAdd}><Plus size={17}/> 最初の試合を記録</button></div>
}
function MatchTable({matches,onEdit,onDelete}:{matches:Match[];onEdit:(match:Match)=>void;onDelete:(id:string)=>void}) {
  return <div className="table-wrap"><table className="match-table"><thead><tr><th>日付</th><th>ヒーロー</th><th>マップ</th><th>結果</th><th>RP</th><th>操作</th></tr></thead><tbody>{matches.map(m=><tr key={m.id}><td className="date-cell">{m.playedAt}</td><td><div className="hero-cell"><strong>{m.heroName}</strong><small>{m.heroRole}</small></div></td><td className="map-cell">{m.mapName}</td><td><span className={`result-pill ${m.result}`}>{resultLabel(m.result)}</span></td><td className="rp-cell">{m.rankPoints===null?'—':m.rankPoints.toLocaleString()}</td><td><div className="row-actions"><button className="icon-button edit-icon" aria-label={`${m.playedAt}の記録を編集`} title="編集" onClick={()=>onEdit(m)}><Pencil size={15}/></button><button className="icon-button" aria-label="記録を削除" title="削除" onClick={()=>onDelete(m.id)}><Trash2 size={15}/></button></div></td></tr>)}</tbody></table></div>
}


function readLocalStore(): Store | null {
  try {
    const raw = localStorage.getItem(storageKey)
    if (!raw) return null
    const parsed = JSON.parse(raw) as Partial<Store>
    if (!Array.isArray(parsed.matches) || !Array.isArray(parsed.heroes) || !Array.isArray(parsed.maps)) return null
    return { matches: parsed.matches, heroes: parsed.heroes, maps: parsed.maps }
  } catch { return null }
}

export default function App() {
  const url = import.meta.env.VITE_SUPABASE_URL as string | undefined
  const key = (import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY || import.meta.env.VITE_SUPABASE_ANON_KEY) as string | undefined
  const [user, setUser] = useState<User | null>(null)
  const [ready, setReady] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [mode, setMode] = useState<'login' | 'signup'>('login')
  const [message, setMessage] = useState('')
  const [syncStatus, setSyncStatus] = useState('準備中')
  const timer = useRef<number | undefined>(undefined)
  const supabase = useMemo(() => url && key ? createClient(url, key) : null, [url, key])

  useEffect(() => {
    if (!supabase) return
    let active = true
    supabase.auth.getSession().then(({ data }) => {
      if (active) setUser(data.session?.user ?? null)
    })
    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null)
    })
    return () => { active = false; listener.subscription.unsubscribe() }
  }, [supabase])

  useEffect(() => {
    let active = true
    async function prepare() {
      if (!supabase || !user) { setReady(false); return }
      setReady(false); setSyncStatus('読み込み中')
      const { data, error } = await supabase.from('user_data').select('payload').eq('user_id', user.id).maybeSingle()
      if (!active) return
      if (error) { setMessage(`クラウドデータを読み込めませんでした：${error.message}`); setSyncStatus('エラー'); return }
      if (data?.payload && typeof data.payload === 'object') {
        localStorage.setItem(storageKey, JSON.stringify(data.payload))
        setSyncStatus('同期済み')
      } else {
        const local = readLocalStore() ?? { matches: [], heroes: initialHeroes, maps: initialMaps }
        const { error: saveError } = await supabase.from('user_data').upsert({ user_id: user.id, payload: local, updated_at: new Date().toISOString() }, { onConflict: 'user_id' })
        if (!active) return
        if (saveError) { setMessage(`初回データ保存に失敗しました：${saveError.message}`); setSyncStatus('エラー'); return }
        localStorage.setItem(storageKey, JSON.stringify(local)); setSyncStatus('同期済み')
      }
      setReady(true)
    }
    void prepare()
    return () => { active = false; if (timer.current) window.clearTimeout(timer.current) }
  }, [supabase, user])

  const saveCloudStore = useCallback((store: Store) => {
    if (!supabase || !user || !ready) return
    if (timer.current) window.clearTimeout(timer.current)
    setSyncStatus('保存中')
    timer.current = window.setTimeout(() => {
      void supabase.from('user_data').upsert({ user_id: user.id, payload: store, updated_at: new Date().toISOString() }, { onConflict: 'user_id' })
        .then(({ error }) => setSyncStatus(error ? 'エラー' : '同期済み'))
    }, 650)
  }, [supabase, user, ready])

  async function submitAuth(e: React.FormEvent) {
    e.preventDefault(); setMessage('')
    if (!supabase) return
    const result = mode === 'signup'
      ? await supabase.auth.signUp({ email: email.trim(), password })
      : await supabase.auth.signInWithPassword({ email: email.trim(), password })
    if (result.error) { setMessage(result.error.message); return }
    if (mode === 'signup' && !result.data.session) setMessage('確認メールが送信された場合は、メール内の案内に従ってからログインしてください。')
    else setMessage('ログインしました。クラウドデータを読み込んでいます。')
  }

  if (!supabase) return <div className="auth-shell"><div className="auth-card"><div className="brand-mark"><Swords size={23}/></div><h1>クラウド同期の設定</h1><p>Supabase の接続情報がまだ設定されていません。公開設定後に、このアプリを利用できるようになります。</p><ol><li>Supabase プロジェクトを作成</li><li>SQL Editor で <code>supabase/migrations/001_initial_schema.sql</code> を実行</li><li>プロジェクトの URL と Publishable key をホスティング設定に登録</li></ol><p className="small-note">この設定画面は、接続情報を入力する前の状態です。</p></div></div>
  if (!user) return <div className="auth-shell"><form className="auth-card" onSubmit={submitAuth}><div className="brand-mark"><Swords size={23}/></div><div className="eyebrow">RANK TRACKER CLOUD</div><h1>コンパス戦績ノート</h1><p>アカウントでログインすると、PC とスマホで記録を共有できます。</p><div className="field"><label>メールアドレス</label><input type="email" required autoComplete="email" value={email} onChange={e=>setEmail(e.target.value)} /></div><div className="field"><label>パスワード（6文字以上）</label><input type="password" required minLength={6} autoComplete={mode==='signup'?'new-password':'current-password'} value={password} onChange={e=>setPassword(e.target.value)} /></div><button className="primary-button auth-submit" type="submit">{mode==='login'?'ログイン':'アカウントを作成'}</button><button className="text-button auth-switch" type="button" onClick={()=>{setMode(mode==='login'?'signup':'login');setMessage('')}}>{mode==='login'?'初めて使う方：アカウント作成':'すでにアカウントをお持ちの方：ログイン'}</button>{message && <p className="auth-message">{message}</p>}</form></div>
  if (!ready) return <div className="auth-shell"><div className="auth-card"><div className="brand-mark"><Swords size={23}/></div><h1>クラウドデータを準備中</h1><p>{syncStatus}。しばらくお待ちください。</p>{message && <p className="auth-message">{message}</p>}<button className="secondary-button" onClick={()=>supabase.auth.signOut()}>ログアウト</button></div></div>
  return <CloudContext.Provider value={{ saveCloudStore, syncStatus }}><><div className="cloud-user-bar"><span>{user.email} でログイン中 · 同期：{syncStatus}</span><button onClick={()=>supabase.auth.signOut()}>ログアウト</button></div><TrackerApp /></></CloudContext.Provider>
}
