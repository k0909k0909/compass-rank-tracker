import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { createClient, type User } from '@supabase/supabase-js'
import { Activity, BarChart3, CalendarDays, Download, FileUp, Gauge, History, Minus, Pencil, Plus, Search, Settings, Shield, Star, Swords, Trash2, Trophy, X } from 'lucide-react'
import './style.css'
import './style-improvements.css'

type Role = 'アタッカー' | 'ガンナー' | 'タンク' | 'スプリンター'
type Result = 'win' | 'loss' | 'draw'
type Mode = 'バトアリ' | 'フリバ'
type Hero = { name: string; role: Role; favorite?: boolean }
type Match = {
  id: string
  playedAt: string
  season: string
  heroName: string
  heroRole: Role
  mapName: string
  result: Result
  /** 旧データ互換：試合後の合計RP */
  rankPoints: number | null
  memo: string
  /** 新データ：この試合で増減したRP */
  rankChange?: number | null
  /** 旧データでは未設定 */
  mode?: Mode
}
type Store = {
  matches: Match[]
  heroes: Hero[]
  maps: string[]
  initialRankPoints?: number | null
  lastMode?: Mode
}
type Page = 'dashboard' | 'add' | 'history' | 'settings'
type CloudContextValue = { saveCloudStore: (store: Store) => void; syncStatus: string }
const CloudContext = createContext<CloudContextValue | null>(null)

// Appliv Gamesのロール別一覧と、やぎシミュの掲載ヒーローを参考にした初期一覧。
// 新ヒーローは設定画面から追加でき、初回起動時にもこの一覧を補完します。
const heroNamesByRole: Record<Role, string[]> = {
  'スプリンター': [
    '十文字アタリ', 'Voidoll', 'ニコラ テスラ', 'コクリコット ブランシュ', 'かけだし勇者', '輝龍院きらら', '零夜', 'ピエール77世',
    'アル・ダハブ＝アルカティア', '某＜なにがし＞', 'チーちゃん', 'ーペルリニエ', '初音ミク', '春麗', 'ザック＆レイチェル', 'アクア',
    '中島敦', 'ジョーカー', 'アスナ', 'ラム', 'ベル・クラネル', 'パワー', 'キルア=ゾルディック', '上条当麻', 'セイバー', '一姫'
  ],
  'アタッカー': [
    '双挽乃保', '桜華忠臣', "マルコス'55", 'マリア=S=レオンブルク', 'アダム=ユーリエフ', 'ポロロッチョ', 'デビルミント鬼龍 デルミン',
    'ルルカ', '狐ヶ咲甘色', 'イグニス=ウィル=ウィスプ', 'ステリア・ララ・シルワ', 'クー・シー', 'コラプス', 'シャルル・リヒター',
    'ソル=バッドガイ', 'リュウ', 'レム', 'カイ=キスク', 'リヴァイ', 'セイバーオルタ', 'アイズ・ヴァレンシュタイン', 'ノクティス', 'キリト',
    '2B', 'リムル=テンペスト', '御坂美琴', 'デンジ', 'ターニャ・デグレチャフ', 'ボンドルド', 'ゴン=フリークス', 'シャドウ', 'アーチャー',
    'タココ'
  ],
  'ガンナー': [
    'リリカ', 'ルチアーノ', '深川まとい', 'サーティーン', 'メグメグ', 'イスタカ', 'ソーン=ユーリエフ', 'ニーズヘッグ', 'ゲームバズーカガール',
    '糸廻輪廻', 'Bugdoll', '天空王 ぶれいずどらごん', 'みりぽゆ', 'メルーニャ・ランチェルナ', 'ディズィー', 'エミリア', '鏡音リン',
    '猫宮ひなた', '岡部倫太郎', 'ギルガメッシュ', '芥川龍之介', 'アインズ・ウール・ゴウン', 'アクセラレータ', 'ロキシー・ミグルディア',
    'ロックマン.EXE＆光熱斗', 'シノン', 'ランサー', 'レゼ'
  ],
  'タンク': [
    'ジャスティス ハンコック', 'ジャンヌ ダルク', 'グスタフ ハイドリヒ', 'ヴィオレッタ ノワール', 'トマス', '青春アリス', 'ラヴィ・シュシュマルシュ',
    'アミスター=バランディン', 'ファースト', '鏡音レン', 'モノクマ', 'めぐみん', '佐藤四郎兵衛忠信', 'ライザリン・シュタウト', 'ポプ子＆ピピ美', '鬼ヶ式うら', 'エドワード・エルリック'
  ]
}
const roles: Role[] = ['アタッカー', 'ガンナー', 'タンク', 'スプリンター']
// 標準ヒーローは実装順を優先して選択欄に表示します。
const heroImplementationOrder = [
  // オリジナルヒーローの実装順（アタリから）
  '十文字アタリ', 'ジャスティス ハンコック', 'リリカ', '双挽乃保', '桜華忠臣', 'ジャンヌ ダルク', "マルコス'55", 'ルチアーノ', 'Voidoll',
  '深川まとい', 'グスタフ ハイドリヒ', 'ニコラ テスラ', 'ヴィオレッタ ノワール', 'コクリコット ブランシュ', 'マリア=S=レオンブルク',
  'アダム=ユーリエフ', 'サーティーン', 'かけだし勇者', 'メグメグ', 'イスタカ', '輝龍院きらら', 'ポロロッチョ', 'ソーン=ユーリエフ',
  'デビルミント鬼龍 デルミン', 'トマス', '零夜', 'ルルカ', 'ピエール77世', '狐ヶ咲甘色', 'ニーズヘッグ', 'ゲームバズーカガール',
  '青春アリス', 'イグニス=ウィル=ウィスプ', '糸廻輪廻', 'Bugdoll', 'ステリア・ララ・シルワ', 'ラヴィ・シュシュマルシュ',
  'アル・ダハブ＝アルカティア', '天空王 ぶれいずどらごん', '某＜なにがし＞', 'クー・シー', 'アミスター=バランディン', '鬼ヶ式うら', 'コラプス',
  'みりぽゆ', 'チーちゃん', 'ーペルリニエ', 'メルーニャ・ランチェルナ', 'ファースト', 'シャルル・リヒター', '一姫', 'エドワード・エルリック', 'タココ',
  // コラボヒーローは参考一覧の実装順
  'ソル=バッドガイ', 'ディズィー', '初音ミク', 'リュウ', '春麗', 'エミリア', 'レム', 'カイ=キスク', '鏡音リン', '鏡音レン',
  'ザック＆レイチェル', 'モノクマ', 'アクア', 'めぐみん', 'リヴァイ', '猫宮ひなた', '岡部倫太郎', 'セイバーオルタ', 'ギルガメッシュ',
  '佐藤四郎兵衛忠信', 'アイズ・ヴァレンシュタイン', 'ノクティス', '中島敦', '芥川龍之介', 'ライザリン・シュタウト', 'ジョーカー',
  'アインズ・ウール・ゴウン', 'キリト', 'アスナ', 'ラム', '2B', 'リムル=テンペスト', '御坂美琴', 'アクセラレータ', 'ベル・クラネル',
  'ロキシー・ミグルディア', 'ロックマン.EXE＆光熱斗', 'デンジ', 'パワー', 'シノン', 'ターニャ・デグレチャフ', 'ボンドルド',
  'ゴン=フリークス', 'キルア=ゾルディック', '上条当麻', 'シャドウ', 'ポプ子＆ピピ美', 'セイバー', 'アーチャー', 'ランサー', 'レゼ'
]
const heroOrderIndex = new Map(heroImplementationOrder.map((name, index) => [name, index]))
const initialHeroes: Hero[] = Object.entries(heroNamesByRole).flatMap(([role, names]) => names.map(name => ({ name, role: role as Role })))
  .filter((hero, index, list) => list.findIndex(item => item.name === hero.name) === index)

const initialMaps = [
  'でらクランクストリート', 'けっこいスターパーク', '東西たかさん広場', 'グレートウォール',
  '立体交差のある風景', '光と闇のライブステージ', '妖華帝都ケルパーズの散歩道', 'ちゅら島リゾート',
  'って〜！つっぺる工事現場', '太鼓で祭りだドーン！', 'おいでやす鳥居通り', 'かけだせ！じっぱか城',
  'どっひゃぁ〜！なっから遺跡', 'Castle of the Silver Feet', 'マジきてる #夜光犯罪特区',
  'Hello :-) irregular World', 'なまらモーモーパーク', 'おっかねぇ！氷焔神域ケイオスブルク',
  'バリバリ！てげてげモーターウェイ', 'いこっさ！ダイダイダイナソー博物館', 'ジャンジャン麻雀の間', 'ぼちぼちボッチ墓地（毒）'
]
const storageKey = 'compass-rank-tracker-v1'
const nowLocalInput = () => {
  const now = new Date()
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000)
  return local.toISOString().slice(0, 16)
}
const today = () => nowLocalInput().slice(0, 10)
const normalizeDateTime = (value: string | undefined) => {
  if (!value) return nowLocalInput()
  // 旧データの日付のみの値も、日時入力欄で編集できる形にする。
  return value.length === 10 ? `${value}T00:00` : value.slice(0, 16)
}
const seasonLabelFromDate = (dateTime: string) => {
  const [year, month] = dateTime.slice(0, 7).split('-')
  return year && month ? `${year}年${Number(month)}月シーズン` : ''
}
const mergeHeroes = (saved: Hero[] | undefined | null): Hero[] => {
  const merged = new Map<string, Hero>()
  initialHeroes.forEach(hero => merged.set(hero.name, hero))
  // お気に入りは維持しつつ、標準ヒーローのロールは初期定義で補正します。
  ;(saved ?? []).forEach(hero => {
    if (hero && typeof hero.name === 'string' && roles.includes(hero.role)) {
      const canonical = merged.get(hero.name)
      merged.set(hero.name, canonical ? { ...hero, role: canonical.role } : hero)
    }
  })
  return [...merged.values()]
}
function loadStore(): Store {
  try {
    const raw = localStorage.getItem(storageKey)
    if (raw) {
      const parsed = JSON.parse(raw) as Partial<Store>
      return {
        ...parsed,
        matches: Array.isArray(parsed.matches) ? parsed.matches : [],
        heroes: mergeHeroes(parsed.heroes),
        maps: Array.isArray(parsed.maps) && parsed.maps.length ? parsed.maps : initialMaps,
        initialRankPoints: typeof parsed.initialRankPoints === 'number' ? parsed.initialRankPoints : null,
        lastMode: parsed.lastMode === 'フリバ' ? 'フリバ' : 'バトアリ'
      }
    }
  } catch { /* 壊れたローカルデータは初期値で開始 */ }
  return { matches: [], heroes: initialHeroes, maps: initialMaps, initialRankPoints: null, lastMode: 'バトアリ' }
}
function resultLabel(result: Result) { return result === 'win' ? '勝ち' : result === 'loss' ? '負け' : '引き分け' }
function percent(n: number, d: number) { return d ? `${Math.round(n / d * 100)}%` : '—' }
function formatDateTime(value: string) {
  const normalized = normalizeDateTime(value)
  return normalized.replace('T', ' ')
}
function signedText(value: number | null | undefined) {
  if (value == null) return '—'
  return value > 0 ? `+${value.toLocaleString()}` : value.toLocaleString()
}
function calculateRankBefore(matches: Match[], initialRankPoints: number | null | undefined, before: string, excludeId?: string): number | null {
  const earlier = matches.filter(match => match.id !== excludeId && match.playedAt < before).sort((a, b) => a.playedAt.localeCompare(b.playedAt))
  const latestSnapshot = [...earlier].reverse().find(match => typeof match.rankPoints === 'number')
  if (latestSnapshot) {
    let total = latestSnapshot.rankPoints as number
    for (const match of earlier) {
      if (match.playedAt > latestSnapshot.playedAt && typeof match.rankChange === 'number') total += match.rankChange
    }
    return total
  }
  if (typeof initialRankPoints !== 'number') return null
  return initialRankPoints + earlier.reduce((sum, match) => sum + (typeof match.rankChange === 'number' ? match.rankChange : 0), 0)
}

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
  const [historyMode, setHistoryMode] = useState<'all' | Mode>('all')
  const [heroSearch, setHeroSearch] = useState('')
  const [heroRoleFilter, setHeroRoleFilter] = useState<'all' | Role>('all')
  const [favoritesOnly, setFavoritesOnly] = useState(false)
  const [initialRankDraft, setInitialRankDraft] = useState(store.initialRankPoints == null ? '' : String(store.initialRankPoints))
  const importRef = useRef<HTMLInputElement>(null)
  const [form, setForm] = useState({
    playedAt: nowLocalInput(), seasonEnabled: false, mode: (store.lastMode ?? 'バトアリ') as Mode,
    heroName: store.heroes[0]?.name ?? '', mapName: store.maps[0] ?? '', result: 'win' as Result,
    rankDirection: 'plus' as 'plus' | 'minus', rankDelta: '0', memo: ''
  })
  const [heroDraft, setHeroDraft] = useState('')
  const [heroRoleDraft, setHeroRoleDraft] = useState<Role>('アタッカー')
  const [mapDraft, setMapDraft] = useState('')

  useEffect(() => { localStorage.setItem(storageKey, JSON.stringify(store)); cloud?.saveCloudStore(store) }, [store])
  const sortedMatches = useMemo(() => [...store.matches].sort((a, b) => b.playedAt.localeCompare(a.playedAt)), [store.matches])
  const wins = store.matches.filter(m => m.result === 'win').length
  const losses = store.matches.filter(m => m.result === 'loss').length
  const winRate = percent(wins, wins + losses)
  const latestRank = useMemo(() => {
    const ordered = [...store.matches].sort((a, b) => a.playedAt.localeCompare(b.playedAt))
    const latestSnapshot = [...ordered].reverse().find(match => typeof match.rankPoints === 'number')
    if (latestSnapshot) {
      return (latestSnapshot.rankPoints as number) + ordered.reduce((sum, match) => sum + (match.playedAt > latestSnapshot.playedAt && typeof match.rankChange === 'number' ? match.rankChange : 0), 0)
    }
    if (typeof store.initialRankPoints !== 'number') return null
    return store.initialRankPoints + ordered.reduce((sum, match) => sum + (typeof match.rankChange === 'number' ? match.rankChange : 0), 0)
  }, [store.matches, store.initialRankPoints])
  const currentMonth = today().slice(0, 7)
  const currentMonthMatches = store.matches.filter(m => m.playedAt.slice(0, 7) === currentMonth)
  const currentMonthWins = currentMonthMatches.filter(m => m.result === 'win').length
  const currentMonthLosses = currentMonthMatches.filter(m => m.result === 'loss').length
  const currentStreak = useMemo(() => {
    const chronological = [...store.matches].sort((a, b) => b.playedAt.localeCompare(a.playedAt))
    const first = chronological[0]?.result
    if (first !== 'win' && first !== 'loss') return { result: '—', count: 0 }
    let count = 0
    for (const match of chronological) { if (match.result !== first) break; count++ }
    return { result: first === 'win' ? '連勝' : '連敗', count }
  }, [store.matches])
  const monthlyStats = useMemo(() => {
    const buckets = new Map<string, Match[]>()
    for (const match of store.matches) { const month = match.playedAt.slice(0, 7); buckets.set(month, [...(buckets.get(month) ?? []), match]) }
    return [...buckets.entries()].sort((a, b) => b[0].localeCompare(a[0])).slice(0, 6).map(([month, matches]) => ({
      month, total: matches.length, wins: matches.filter(m => m.result === 'win').length, losses: matches.filter(m => m.result === 'loss').length,
      draws: matches.filter(m => m.result === 'draw').length, rate: percent(matches.filter(m => m.result === 'win').length, matches.filter(m => m.result !== 'draw').length)
    }))
  }, [store.matches])
  const heroStats = useMemo(() => {
    const buckets = new Map<string, Match[]>()
    for (const match of store.matches) buckets.set(match.heroName, [...(buckets.get(match.heroName) ?? []), match])
    return [...buckets.entries()].map(([name, matches]) => ({ name, role: matches[0].heroRole, total: matches.length, wins: matches.filter(m => m.result === 'win').length, losses: matches.filter(m => m.result === 'loss').length, draws: matches.filter(m => m.result === 'draw').length, rate: percent(matches.filter(m => m.result === 'win').length, matches.filter(m => m.result !== 'draw').length) })).sort((a, b) => b.total - a.total || a.name.localeCompare(b.name, 'ja'))
  }, [store.matches])
  const availableMonths = useMemo(() => [...new Set(store.matches.map(m => m.playedAt.slice(0, 7)))].sort((a, b) => b.localeCompare(a)), [store.matches])
  const filteredMatches = useMemo(() => {
    const query = historyQuery.trim().toLocaleLowerCase()
    return sortedMatches.filter(m => (historyResult === 'all' || m.result === historyResult) && (historyHero === 'all' || m.heroName === historyHero) && (historyMonth === 'all' || m.playedAt.startsWith(historyMonth)) && (historyMode === 'all' || (m.mode ?? 'バトアリ') === historyMode) && (!query || `${m.heroName} ${m.mapName} ${m.memo} ${m.season} ${m.mode ?? ''}`.toLocaleLowerCase().includes(query)))
  }, [sortedMatches, historyQuery, historyResult, historyHero, historyMonth, historyMode])
  const visibleHeroes = useMemo(() => {
    const query = heroSearch.trim().toLocaleLowerCase()
    return store.heroes
      .filter(hero => (heroRoleFilter === 'all' || hero.role === heroRoleFilter)
        && (!favoritesOnly || Boolean(hero.favorite))
        && (!query || hero.name.toLocaleLowerCase().includes(query)))
      .sort((a, b) => (heroOrderIndex.get(a.name) ?? Number.MAX_SAFE_INTEGER) - (heroOrderIndex.get(b.name) ?? Number.MAX_SAFE_INTEGER))
  }, [store.heroes, heroSearch, heroRoleFilter, favoritesOnly])
  const managedHeroes = useMemo(() => [...store.heroes].sort((a, b) =>
    roles.indexOf(a.role) - roles.indexOf(b.role)
    || (heroOrderIndex.get(a.name) ?? Number.MAX_SAFE_INTEGER) - (heroOrderIndex.get(b.name) ?? Number.MAX_SAFE_INTEGER)
  ), [store.heroes])
  const selectedHero = store.heroes.find(hero => hero.name === form.heroName)
  function toggleFavorite(name: string) {
    setStore(current => ({ ...current, heroes: current.heroes.map(hero => hero.name === name ? { ...hero, favorite: !hero.favorite } : hero) }))
  }

  function notify(message: string) { setToast(message); window.setTimeout(() => setToast(''), 2600) }
  function startNewMatch() {
    setEditingId(null)
    setHeroSearch('')
    setHeroRoleFilter('all')
    setFavoritesOnly(false)
    setForm({ playedAt: nowLocalInput(), seasonEnabled: false, mode: store.lastMode ?? 'バトアリ', heroName: store.heroes[0]?.name ?? '', mapName: store.maps[0] ?? '', result: 'win', rankDirection: 'plus', rankDelta: '0', memo: '' })
    setPage('add')
  }
  function beginEditMatch(match: Match) {
    setEditingId(match.id)
    setHeroSearch('')
    setHeroRoleFilter('all')
    setFavoritesOnly(false)
    setForm({ playedAt: normalizeDateTime(match.playedAt), seasonEnabled: Boolean(match.season) && (match.mode ?? 'バトアリ') === 'バトアリ', mode: match.mode ?? 'バトアリ', heroName: match.heroName, mapName: match.mapName, result: match.result, rankDirection: (match.rankChange ?? (match.result === 'loss' ? -1 : 1)) < 0 ? 'minus' : 'plus', rankDelta: String(Math.abs(match.rankChange ?? 0)), memo: match.memo ?? '' })
    setPage('add')
  }
  function changeResult(result: Result) {
    setForm(old => ({ ...old, result, rankDirection: result === 'loss' ? 'minus' : 'plus', rankDelta: result === 'draw' ? '0' : old.rankDelta }))
  }
  function saveMatch(e: React.FormEvent) {
    e.preventDefault()
    const hero = store.heroes.find(h => h.name === form.heroName)
    if (!hero || !form.mapName) { notify('ヒーローとマップを選択してください'); return }
    if (editingId && !form.playedAt) { notify('試合日時を入力してください'); return }
    const recordedAt = editingId ? normalizeDateTime(form.playedAt) : nowLocalInput()
    const amountText = form.rankDelta.trim()
    const amount = amountText === '' ? 0 : Number(amountText)
    if (!Number.isFinite(amount) || amount < 0) { notify('RP変動は0以上の数値で入力してください'); return }
    const signedChange = form.result === 'draw' ? 0 : (form.rankDirection === 'minus' ? -Math.abs(amount) : Math.abs(amount))
    const previousRank = calculateRankBefore(store.matches, store.initialRankPoints, recordedAt, editingId ?? undefined)
    const calculatedTotal = previousRank == null ? null : previousRank + signedChange
    const match: Match = {
      id: editingId ?? crypto.randomUUID(), playedAt: recordedAt,
      season: form.mode === 'バトアリ' && form.seasonEnabled ? seasonLabelFromDate(recordedAt) : '',
      heroName: hero.name, heroRole: hero.role, mapName: form.mapName, result: form.result,
      rankPoints: calculatedTotal, rankChange: signedChange, mode: form.mode, memo: form.memo.trim()
    }
    if (editingId) setStore(s => ({ ...s, lastMode: form.mode, matches: s.matches.map(m => m.id === editingId ? match : m) }))
    else setStore(s => ({ ...s, lastMode: form.mode, matches: [match, ...s.matches] }))
    const wasEditing = editingId !== null
    setEditingId(null)
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
        setStore({ ...data, matches: data.matches, heroes: mergeHeroes(data.heroes), maps: data.maps, initialRankPoints: typeof data.initialRankPoints === 'number' ? data.initialRankPoints : null, lastMode: data.lastMode === 'フリバ' ? 'フリバ' : 'バトアリ' })
        setInitialRankDraft(typeof data.initialRankPoints === 'number' ? String(data.initialRankPoints) : '')
        notify('バックアップを復元しました')
      } catch { notify('ファイルを読み込めませんでした。正しいバックアップか確認してください') }
    }
    reader.readAsText(file)
  }
  function saveInitialRankPoints() {
    const text = initialRankDraft.trim()
    if (text === '') { setStore(s => ({ ...s, initialRankPoints: null })); notify('初期ランクポイントを未設定にしました'); return }
    const value = Number(text)
    if (!Number.isFinite(value)) { notify('初期ランクポイントは数値で入力してください'); return }
    setStore(s => ({ ...s, initialRankPoints: value }))
    notify('初期ランクポイントを保存しました')
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
        <NavItem active={page === 'dashboard'} icon={<Gauge size={18}/>} label="ホーム" onClick={() => setPage('dashboard')} />
        <NavItem active={page === 'add'} icon={<Plus size={18}/>} label="試合を記録" onClick={startNewMatch} />
        <NavItem active={page === 'history'} icon={<History size={18}/>} label="戦績一覧" onClick={() => setPage('history')} />
        <NavItem active={page === 'settings'} icon={<Settings size={18}/>} label="設定・バックアップ" onClick={() => setPage('settings')} />
      </nav>
      <div className="sidebar-foot"><Shield size={15}/> {cloud ? `クラウド同期：${cloud.syncStatus}` : 'この端末に保存'}</div>
    </aside>
    <main className="main-content">
      <header className="topbar">
        <div><h1>{({ dashboard: 'ホーム', add: '試合を記録', history: '戦績一覧', settings: '設定・バックアップ' } as Record<Page, string>)[page]}</h1></div>
        <button className="primary-button top-add" onClick={startNewMatch}><Plus size={17}/> 試合を追加</button>
      </header>

      {page === 'dashboard' && <section className="page-stack">
        <div className="stats-grid">
          <StatCard icon={<Activity size={19}/>} label="総試合数" value={`${store.matches.length}`} sub="記録した試合" />
          <StatCard icon={<Trophy size={19}/>} label="勝率" value={winRate} sub={`${wins}勝 · ${losses}敗`} />
          <StatCard icon={<BarChart3 size={19}/>} label="現在のランクポイント" value={latestRank == null ? '—' : latestRank.toLocaleString()} sub={store.initialRankPoints == null ? '初期RP未設定' : `初期RP ${store.initialRankPoints.toLocaleString()}`} />
          <StatCard icon={<CalendarDays size={19}/>} label="今月の試合" value={`${currentMonthMatches.length}`} sub={`${currentMonthWins}勝 · ${currentMonthLosses}敗`} />
          <StatCard icon={<Activity size={19}/>} label="現在の連続結果" value={currentStreak.count ? `${currentStreak.count}${currentStreak.result}` : '—'} sub="最新の記録から集計" />
          <StatCard icon={<Shield size={19}/>} label="登録ヒーロー" value={`${store.heroes.length}`} sub={`マップ ${store.maps.length} 件`} />
        </div>
        <div className="content-card">
          <div className="section-heading"><div><h3>最近の試合</h3><p>直近に記録した試合を表示します</p></div><button className="text-button" onClick={() => setPage('history')}>すべて見る →</button></div>
          {sortedMatches.length ? <MatchTable matches={sortedMatches.slice(0, 5)} onEdit={beginEditMatch} onDelete={deleteMatch}/> : <EmptyState onAdd={startNewMatch}/>}
        </div>
        <div className="analytics-grid">
          <div className="content-card analytics-card">
            <div className="section-heading"><div><h3>月別成績</h3><p>直近6か月分の記録を集計</p></div></div>
            {monthlyStats.length ? <div className="table-wrap"><table className="mini-table"><thead><tr><th>月</th><th>試合</th><th>勝敗</th><th>勝率</th></tr></thead><tbody>{monthlyStats.map(m => <tr key={m.month}><td>{m.month}</td><td>{m.total}</td><td>{m.wins}勝 {m.losses}敗{m.draws ? ` ${m.draws}分` : ''}</td><td className="rate-cell">{m.rate}</td></tr>)}</tbody></table></div> : <p className="empty-inline">試合を記録すると月別成績が表示されます。</p>}
          </div>
          <div className="content-card analytics-card">
            <div className="section-heading"><div><h3>ヒーロー別成績</h3><p>使用回数の多い順</p></div></div>
            {heroStats.length ? <div className="table-wrap"><table className="mini-table"><thead><tr><th>ヒーロー</th><th>試合</th><th>勝率</th></tr></thead><tbody>{heroStats.slice(0, 6).map(h => <tr key={h.name}><td><span className="mini-hero-name">{h.name}</span><small className="mini-hero-role">{h.role}</small></td><td>{h.total}</td><td className="rate-cell">{h.rate}</td></tr>)}</tbody></table></div> : <p className="empty-inline">試合を記録するとヒーロー別成績が表示されます。</p>}
          </div>
        </div>
        <div className="hint-row"><Shield size={17}/><span>{cloud ? 'ログイン中のアカウントに記録を同期します。別の端末でも同じアカウントでログインしてください。' : '端末を変える前にバックアップを保存してください。'}</span></div>
      </section>}

      {page === 'add' && <section className="content-card form-card">
        <div className="section-heading"><div><h3>{editingId ? '試合記録を編集' : '試合内容を入力'}</h3><p>{editingId ? '日時や結果、RPの変動を修正できます。' : '日時は保存時に自動で記録します。'}</p></div><div className="round-icon"><Swords size={20}/></div></div>
        <form onSubmit={saveMatch} className="match-form">
          {editingId && <div className="field field-wide"><label>試合日時（分まで）</label><input type="datetime-local" required value={form.playedAt} onChange={e => setForm({ ...form, playedAt: e.target.value })}/></div>}
          <div className="field field-wide"><label>モード</label><div className="result-options mode-options">
            {(['バトアリ', 'フリバ'] as Mode[]).map(mode => <button type="button" key={mode} className={`result-choice ${form.mode === mode ? 'selected win' : ''}`} onClick={() => setForm(old => ({ ...old, mode, seasonEnabled: mode === 'フリバ' ? false : old.seasonEnabled }))}>{mode}</button>)}
          </div>
          <label className={`season-check ${form.mode === 'フリバ' ? 'season-disabled' : ''}`}><input type="checkbox" disabled={form.mode === 'フリバ'} checked={form.mode === 'バトアリ' && form.seasonEnabled} onChange={e => setForm(old => ({ ...old, seasonEnabled: e.target.checked }))}/><span>シーズン</span></label></div>
          <div className="field field-wide hero-picker-controls">
            <div className="hero-search-control"><label>使用ヒーローを検索</label><label className="search-field"><Search size={16}/><input value={heroSearch} onChange={e => setHeroSearch(e.target.value)} placeholder="ヒーロー名を入力" /></label></div>
            <div className="hero-filter-control"><label>絞込み</label>
              <div className="hero-role-buttons">{(['all', ...roles] as ('all' | Role)[]).map(role => <button type="button" key={role} className={`role-filter-button ${heroRoleFilter === role ? 'active' : ''}`} onClick={() => setHeroRoleFilter(role)}>{role === 'all' ? 'すべて' : role}</button>)}</div>
              <label className="favorite-filter"><input type="checkbox" checked={favoritesOnly} onChange={e => setFavoritesOnly(e.target.checked)}/><span><Star size={13}/> お気に入り</span></label>
            </div>
          </div>
          <div className="field field-wide hero-select-field"><label>使用ヒーロー（{visibleHeroes.length}人）</label>
            <div className="hero-select-row"><select className="hero-select" required value={form.heroName} onChange={e => setForm({ ...form, heroName: e.target.value })}>{visibleHeroes.some(h => h.name === form.heroName) ? null : store.heroes.find(h => h.name === form.heroName) ? <option value={form.heroName}>{form.heroName}（現在の記録）</option> : null}{visibleHeroes.map(h => <option key={h.name} value={h.name}>{h.name}（{h.role}）</option>)}</select>
              <button type="button" className={`favorite-toggle ${selectedHero?.favorite ? 'is-favorite' : ''}`} disabled={!selectedHero} aria-label={selectedHero?.favorite ? 'お気に入りを解除' : 'お気に入りに登録'} aria-pressed={Boolean(selectedHero?.favorite)} title={selectedHero?.favorite ? 'お気に入りを解除' : 'お気に入りに登録'} onClick={() => selectedHero && toggleFavorite(selectedHero.name)}><Star size={18} fill={selectedHero?.favorite ? 'currentColor' : 'none'}/></button>
            </div>
            {visibleHeroes.length === 0 && <small className="small-note">条件に一致するヒーローがいません。検索や絞込みを変更してください。</small>}
          </div>
          <div className="field field-wide"><label>マップ</label><select required value={form.mapName} onChange={e => setForm({ ...form, mapName: e.target.value })}>{store.maps.map(m => <option key={m} value={m}>{m}</option>)}</select></div>
          <div className="field field-wide"><label>試合結果</label><div className="result-options">
            {(['win', 'loss', 'draw'] as Result[]).map(r => <button type="button" key={r} className={`result-choice ${form.result === r ? `selected ${r}` : ''}`} onClick={() => changeResult(r)}>{resultLabel(r)}</button>)}
          </div></div>
          <div className="field field-wide"><label>ランクポイントの増減 <small>任意・実際の増減量を入力</small></label>
            <div className="rp-change-control"><div className="rp-direction-buttons"><button type="button" className={`result-choice ${form.rankDirection === 'plus' ? 'selected win' : ''}`} onClick={() => setForm({ ...form, rankDirection: 'plus' })}><Plus size={16}/> 増加</button><button type="button" className={`result-choice ${form.rankDirection === 'minus' ? 'selected loss' : ''}`} onClick={() => setForm({ ...form, rankDirection: 'minus' })}><Minus size={16}/> 減少</button></div><input aria-label="RP変動量" type="number" min="0" step="1" placeholder="0" value={form.rankDelta} onChange={e => setForm({ ...form, rankDelta: e.target.value })}/><strong className={form.result === 'draw' ? '' : form.rankDirection === 'minus' ? 'negative-rp' : 'positive-rp'}>{form.result === 'draw' ? '±0' : form.rankDirection === 'minus' ? `−${Math.abs(Number(form.rankDelta) || 0).toLocaleString()}` : `+${Math.abs(Number(form.rankDelta) || 0).toLocaleString()}`}</strong></div>
            <small className="small-note">勝ちを選ぶと「増加」、負けを選ぶと「減少」が自動選択されます。実際のRP変動に合わせて符号と数値を変更できます。引き分けはRP変動を0として記録します。</small>
            <small className="small-note">試合後のRP合計：{(() => { const before = calculateRankBefore(store.matches, store.initialRankPoints, editingId ? normalizeDateTime(form.playedAt) : nowLocalInput(), editingId ?? undefined); const change = form.result === 'draw' ? 0 : (form.rankDirection === 'minus' ? -1 : 1) * Math.abs(Number(form.rankDelta) || 0); return before == null ? '初期RPを設定すると計算できます' : (before + change).toLocaleString() })()}</small>
          </div>
          <div className="field field-wide"><label>メモ <small>任意</small></label><textarea rows={3} placeholder="味方編成、反省点、気づいたことなど" value={form.memo} onChange={e => setForm({ ...form, memo: e.target.value })}/></div>
          <div className="form-actions"><button type="button" className="secondary-button" onClick={() => { setEditingId(null); setPage('dashboard') }}>キャンセル</button><button type="submit" className="primary-button">{editingId ? <><Pencil size={17}/> 変更を保存</> : <><Plus size={17}/> 記録を保存</>}</button></div>
        </form>
      </section>}

      {page === 'history' && <section className="content-card">
        <div className="section-heading"><div><h3>すべての戦績</h3><p>{filteredMatches.length} 件表示 / 全 {store.matches.length} 件</p></div><button className="primary-button" onClick={startNewMatch}><Plus size={17}/> 試合を追加</button></div>
        <div className="history-filters">
          <label className="search-field"><Search size={16}/><input value={historyQuery} onChange={e => setHistoryQuery(e.target.value)} placeholder="ヒーロー・マップ・メモを検索" /></label>
          <select aria-label="結果で絞り込み" value={historyResult} onChange={e => setHistoryResult(e.target.value as 'all' | Result)}><option value="all">すべての結果</option><option value="win">勝ち</option><option value="loss">負け</option><option value="draw">引き分け</option></select>
          <select aria-label="ヒーローで絞り込み" value={historyHero} onChange={e => setHistoryHero(e.target.value)}><option value="all">すべてのヒーロー</option>{store.heroes.map(h => <option key={h.name} value={h.name}>{h.name}</option>)}</select>
          <select aria-label="月で絞り込み" value={historyMonth} onChange={e => setHistoryMonth(e.target.value)}><option value="all">すべての月</option>{availableMonths.map(m => <option key={m} value={m}>{m}</option>)}</select>
          <select aria-label="モードで絞り込み" value={historyMode} onChange={e => setHistoryMode(e.target.value as 'all' | Mode)}><option value="all">すべてのモード</option><option value="バトアリ">バトアリ</option><option value="フリバ">フリバ</option></select>
        </div>
        {filteredMatches.length ? <MatchTable matches={filteredMatches} onEdit={beginEditMatch} onDelete={deleteMatch}/> : store.matches.length ? <p className="empty-inline">条件に一致する記録がありません。絞り込み条件を変更してください。</p> : <EmptyState onAdd={startNewMatch}/>}
      </section>}

      {page === 'settings' && <section className="page-stack">
        <div className="content-card">
          <div className="section-heading"><div><h3>ランクポイント設定</h3><p>最初に記録する時点のRPを入力してください。</p></div><div className="round-icon"><BarChart3 size={20}/></div></div>
          <div className="initial-rp-setting"><div className="field"><label>初期ランクポイント</label><input type="number" step="1" placeholder="例：1500" value={initialRankDraft} onChange={e => setInitialRankDraft(e.target.value)}/></div><button className="primary-button" onClick={saveInitialRankPoints}>初期RPを保存</button></div>
          <p className="small-note">初期RPと試合ごとの増減量から、試合後のRP合計を計算します。過去の記録に保存されたRP合計は維持されます。</p>
        </div>
        <div className="content-card">
          <div className="section-heading"><div><h3>バックアップと復元</h3><p>記録データを JSON ファイルとして保存できます。</p></div><div className="round-icon"><Shield size={20}/></div></div>
          <div className="backup-actions"><button className="primary-button" onClick={exportData}><Download size={17}/> バックアップを保存</button><button className="secondary-button" onClick={() => importRef.current?.click()}><FileUp size={17}/> バックアップから復元</button><input ref={importRef} hidden type="file" accept="application/json,.json" onChange={e => { importData(e.target.files?.[0]); e.currentTarget.value = '' }}/></div>
          <p className="small-note">復元すると現在のデータはバックアップの内容に置き換わります。必要に応じて先にバックアップを保存してください。</p>
        </div>
        <div className="content-card">
          <div className="section-heading"><div><h3>ヒーロー管理</h3><p>名前とロールを追加できます。削除は試合記録で未使用の場合のみ可能です。</p></div></div>
          <div className="catalog-add"><input value={heroDraft} placeholder="ヒーロー名" onChange={e => setHeroDraft(e.target.value)} onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addHero())}/><select value={heroRoleDraft} onChange={e => setHeroRoleDraft(e.target.value as Role)}>{roles.map(r => <option key={r}>{r}</option>)}</select><button className="primary-button" onClick={addHero}><Plus size={16}/> 追加</button></div>
          <div className="catalog-list">{managedHeroes.map(h => <div className="catalog-item" key={h.name}><span>{h.name}</span><span className={`role-pill role-${roles.indexOf(h.role)}`}>{h.role}</span><button className="icon-button" aria-label={`${h.name}を削除`} onClick={() => removeHero(h.name)}><Trash2 size={16}/></button></div>)}</div>
        </div>
        <div className="content-card">
          <div className="section-heading"><div><h3>マップ管理</h3><p>マップを追加できます。削除は試合記録で未使用の場合のみ可能です。</p></div></div>
          <div className="catalog-add"><input value={mapDraft} placeholder="マップ名" onChange={e => setMapDraft(e.target.value)} onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addMap())}/><button className="primary-button" onClick={addMap}><Plus size={16}/> 追加</button></div>
          <div className="catalog-list map-list">{store.maps.map(m => <div className="catalog-item" key={m}><span>{m}</span><button className="icon-button" aria-label={`${m}を削除`} onClick={() => removeMap(m)}><Trash2 size={16}/></button></div>)}</div>
        </div>
        <div className="content-card future-card"><div className="round-icon"><Activity size={20}/></div><div><h3>現在の機能</h3><p>試合日時（分単位）、モード、月ごとのシーズン記録、実装順のヒーロー選択、お気に入り・ロール絞込み、RP増減、初期RP、バックアップ・復元に対応しています。</p></div></div>
      </section>}
      <footer className="app-footer">コンパス戦績ノート <span>·</span> Version 0.2.0</footer>
    </main>
    {toast && <div className="toast"><span className="toast-dot"/>{toast}<button onClick={() => setToast('')} aria-label="閉じる"><X size={15}/></button></div>}
  </div>
}

function NavItem({ active, icon, label, onClick }: { active: boolean; icon: React.ReactNode; label: string; onClick: () => void }) {
  return <button className={`nav-item ${active ? 'active' : ''}`} onClick={onClick}>{icon}<span>{label}</span>{active && <span className="nav-indicator"/>}</button>
}
function StatCard({ icon, label, value, sub }: { icon: React.ReactNode; label: string; value: string; sub: string }) {
  return <div className="stat-card"><div className="stat-top"><span>{label}</span><span className="stat-icon">{icon}</span></div><strong>{value}</strong><small>{sub}</small></div>
}
function EmptyState({ onAdd }: { onAdd: () => void }) {
  return <div className="empty-state"><div className="empty-icon"><History size={24}/></div><h4>まだ試合記録がありません</h4><p>最初の試合を記録して、戦績の分析を始めましょう。</p><button className="primary-button" onClick={onAdd}><Plus size={17}/> 最初の試合を記録</button></div>
}
function MatchTable({ matches, onEdit, onDelete }: { matches: Match[]; onEdit: (match: Match) => void; onDelete: (id: string) => void }) {
  return <div className="table-wrap"><table className="match-table"><thead><tr><th>日時</th><th>モード／シーズン</th><th>ヒーロー</th><th>マップ</th><th>結果</th><th>RP変動</th><th>RP合計</th><th>操作</th></tr></thead><tbody>{matches.map(m => <tr key={m.id}><td className="date-cell">{formatDateTime(m.playedAt)}</td><td><div className="hero-cell"><strong>{m.mode ?? 'バトアリ'}</strong><small>{m.season || '通常記録'}</small></div></td><td><div className="hero-cell"><strong>{m.heroName}</strong><small>{m.heroRole}</small></div></td><td className="map-cell">{m.mapName}</td><td><span className={`result-pill ${m.result}`}>{resultLabel(m.result)}</span></td><td className="rp-cell">{signedText(m.rankChange)}</td><td className="rp-cell">{m.rankPoints == null ? '—' : m.rankPoints.toLocaleString()}</td><td><div className="row-actions"><button className="icon-button edit-icon" aria-label={`${m.playedAt}の記録を編集`} title="編集" onClick={() => onEdit(m)}><Pencil size={15}/></button><button className="icon-button" aria-label="記録を削除" title="削除" onClick={() => onDelete(m.id)}><Trash2 size={15}/></button></div></td></tr>)}</tbody></table></div>
}

function readLocalStore(): Store | null {
  try {
    const raw = localStorage.getItem(storageKey)
    if (!raw) return null
    const parsed = JSON.parse(raw) as Partial<Store>
    if (!Array.isArray(parsed.matches) || !Array.isArray(parsed.heroes) || !Array.isArray(parsed.maps)) return null
    return { ...parsed, matches: parsed.matches, heroes: mergeHeroes(parsed.heroes), maps: parsed.maps, initialRankPoints: typeof parsed.initialRankPoints === 'number' ? parsed.initialRankPoints : null, lastMode: parsed.lastMode === 'フリバ' ? 'フリバ' : 'バトアリ' }
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
    supabase.auth.getSession().then(({ data }) => { if (active) setUser(data.session?.user ?? null) })
    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => setUser(session?.user ?? null))
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
        const payload = data.payload as Partial<Store>
        localStorage.setItem(storageKey, JSON.stringify({ ...payload, matches: Array.isArray(payload.matches) ? payload.matches : [], heroes: mergeHeroes(payload.heroes), maps: Array.isArray(payload.maps) && payload.maps.length ? payload.maps : initialMaps, initialRankPoints: typeof payload.initialRankPoints === 'number' ? payload.initialRankPoints : null, lastMode: payload.lastMode === 'フリバ' ? 'フリバ' : 'バトアリ' }))
        setSyncStatus('同期済み')
      } else {
        const local = readLocalStore() ?? { matches: [], heroes: initialHeroes, maps: initialMaps, initialRankPoints: null, lastMode: 'バトアリ' as Mode }
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
  if (!user) return <div className="auth-shell"><form className="auth-card" onSubmit={submitAuth}><div className="brand-mark"><Swords size={23}/></div><div className="eyebrow">RANK TRACKER CLOUD</div><h1>コンパス戦績ノート</h1><p>アカウントでログインすると、PC とスマホで記録を共有できます。</p><div className="field"><label>メールアドレス</label><input type="email" required autoComplete="email" value={email} onChange={e => setEmail(e.target.value)} /></div><div className="field"><label>パスワード（6文字以上）</label><input type="password" required minLength={6} autoComplete={mode === 'signup' ? 'new-password' : 'current-password'} value={password} onChange={e => setPassword(e.target.value)} /></div><button className="primary-button auth-submit" type="submit">{mode === 'login' ? 'ログイン' : 'アカウントを作成'}</button><button className="text-button auth-switch" type="button" onClick={() => { setMode(mode === 'login' ? 'signup' : 'login'); setMessage('') }}>{mode === 'login' ? '初めて使う方：アカウント作成' : 'すでにアカウントをお持ちの方：ログイン'}</button>{message && <p className="auth-message">{message}</p>}</form></div>
  if (!ready) return <div className="auth-shell"><div className="auth-card"><div className="brand-mark"><Swords size={23}/></div><h1>クラウドデータを準備中</h1><p>{syncStatus}。しばらくお待ちください。</p>{message && <p className="auth-message">{message}</p>}<button className="secondary-button" onClick={() => supabase.auth.signOut()}>ログアウト</button></div></div>
  return <CloudContext.Provider value={{ saveCloudStore, syncStatus }}><><div className="cloud-user-bar"><span>{user.email} でログイン中 · 同期：{syncStatus}</span><button onClick={() => supabase.auth.signOut()}>ログアウト</button></div><TrackerApp /></></CloudContext.Provider>
}
