import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { createClient, type User } from '@supabase/supabase-js'
import { Activity, BarChart3, CalendarDays, ChevronDown, Download, FileUp, Gauge, History, Lock, Minus, Pencil, Plus, Search, Settings, Shield, Star, Sun, Moon, Swords, Trash2, Trophy, Unlock, X } from 'lucide-react'
import compassNoteMark from './assets/compass-note-mark.svg'
import './style.css'
import './style-improvements.css'
import './theme.css'

type Role = 'アタッカー' | 'ガンナー' | 'タンク' | 'スプリンター'
type Result = 'win' | 'loss' | 'draw'
type Mode = 'バトアリ' | 'フリバ' | 'カスタム'
type Hero = { name: string; role: Role; favorite?: boolean; aliases?: string[] }
type Match = {
  id: string
  playedAt: string
  season: string
  heroName: string
  heroRole: Role
  /** 任意のチーム構成。旧記録では未設定 */
  enemyHeroNames?: string[]
  allyHeroNames?: string[]
  mapName: string
  result: Result
  /** 旧データ互換：試合後の合計RP */
  rankPoints: number | null
  memo: string
  /** 新データ：この試合で増減したRP */
  rankChange?: number | null
  /** 旧データでは未設定 */
  mode?: Mode
  /** 新ランク仕様：試合前後のランクを保存。旧記録では未設定 */
  rankBeforeTier?: number
  rankBeforePoints?: number
  rankAfterTier?: number
  rankAfterPoints?: number
}
type Store = {
  matches: Match[]
  heroes: Hero[]
  maps: string[]
  initialRankPoints?: number | null
  lastMode?: Mode
  /** 次回の試合記録で初期選択するヒーロー */
  lastUsedHeroName?: string
  /** 次回の試合記録で引き継ぐ、固定中の味方ヒーロー */
  lastLockedAllyHeroNames?: string[]
  /** 味方1・2それぞれの固定状態 */
  lastLockedAllySlots?: boolean[]
  /** 現在のランク（S1〜S9） */
  currentRankTier?: number
  /** 現在のランク内ポイント */
  currentRankPoints?: number
  /** リセット操作で確定した現在のシーズン */
  activeSeason?: string
  /** YYYY-MM。月ごとの自動リセット重複防止用 */
  lastSeasonResetMonth?: string
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
  // 2016/12/17 初期ヒーロー
  '十文字アタリ', 'ジャスティス ハンコック', 'リリカ', '双挽乃保', '桜華忠臣', 'ジャンヌ ダルク', "マルコス'55", 'ルチアーノ', 'Voidoll', '深川まとい',
  // 2017
  'ソル=バッドガイ', 'ディズィー', 'グスタフ ハイドリヒ', 'ニコラ テスラ', '初音ミク', 'ヴィオレッタ ノワール', 'コクリコット ブランシュ', 'リュウ', '春麗',
  'マリア=S=レオンブルク', 'アダム=ユーリエフ', 'サーティーン', 'かけだし勇者', 'エミリア', 'レム',
  // 2018
  'カイ=キスク', 'メグメグ', '鏡音リン', '鏡音レン', 'イスタカ', 'ザック＆レイチェル', '輝龍院きらら', 'モノクマ', 'ポロロッチョ', 'アクア', 'めぐみん',
  // 2019
  'ソーン=ユーリエフ', 'リヴァイ', 'デビルミント鬼龍 デルミン', 'トマス', '猫宮ひなた', '岡部倫太郎', '零夜', 'セイバーオルタ', 'ギルガメッシュ',
  // 2020
  'ルルカ', 'ピエール77世', '佐藤四郎兵衛忠信', 'アイズ・ヴァレンシュタイン', '狐ヶ咲甘色', 'ノクティス', 'ニーズヘッグ',
  // 2021
  '中島敦', '芥川龍之介', 'ゲームバズーカガール', 'ライザリン・シュタウト', '青春アリス', 'ジョーカー', 'イグニス=ウィル=ウィスプ', 'アインズ・ウール・ゴウン', '糸廻輪廻', 'キリト', 'アスナ',
  // 2022
  'Bugdoll', 'ステリア・ララ・シルワ', 'ラム', '2B', 'ラヴィ・シュシュマルシュ', 'リムル=テンペスト', 'アル・ダハブ＝アルカティア', '御坂美琴', 'アクセラレータ',
  // 2023
  '天空王 ぶれいずどらごん', 'ベル・クラネル', 'ロキシー・ミグルディア', '某＜なにがし＞', 'ロックマン.EXE＆光熱斗', 'クー・シー', 'パワー', 'デンジ',
  // 2024
  'アミスター=バランディン', 'シノン', 'ターニャ・デグレチャフ', '鬼ヶ式うら', 'コラプス', 'ボンドルド', 'みりぽゆ', 'ゴン=フリークス', 'キルア=ゾルディック',
  // 2025。オリジナル・コラボを実装時期順に混在させる
  'チーちゃん', '上条当麻', 'ーペルリニエ', 'シャドウ', 'ポプ子＆ピピ美', 'メルーニャ・ランチェルナ', 'セイバー', 'アーチャー', 'ランサー',
  // 2026
  'ファースト', 'レゼ', 'シャルル・リヒター', '一姫', 'エドワード・エルリック', 'タココ'
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
const recordDraftStorageKey = `${storageKey}-record-draft`
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
type RecordDraft = {
  page?: Page
  editingId?: string | null
  recordSlide?: 1 | 2
  lockAlly1?: boolean
  lockAlly2?: boolean
  rankTierDraft?: string
  rankPointsDraft?: string
  form?: Record<string, any>
}
function loadRecordDraft(): RecordDraft | null {
  try {
    const raw = localStorage.getItem(recordDraftStorageKey)
    if (!raw) return null
    const parsed = JSON.parse(raw) as RecordDraft
    return parsed && typeof parsed === 'object' ? parsed : null
  } catch { return null }
}
type RankState = { tier: number; points: number }
const MIN_RANK = 1
const MAX_RANK = 9
const MAX_RANK_POINTS = 499
const MAX_TOTAL_RANK_POINTS = 4499
const clampInteger = (value: number, min: number, max: number) => Math.max(min, Math.min(max, Math.trunc(Number.isFinite(value) ? value : min)))
const normalizeRankState = (tier: number, points: number): RankState => ({
  tier: clampInteger(tier, MIN_RANK, MAX_RANK),
  points: clampInteger(points, 0, MAX_RANK_POINTS)
})
const rankStateToTotal = (state: RankState) => (state.tier - 1) * 500 + state.points
const rankStateFromLegacyTotal = (total: number): RankState => {
  const bounded = clampInteger(total, 0, MAX_TOTAL_RANK_POINTS)
  return { tier: Math.floor(bounded / 500) + 1, points: bounded % 500 }
}
const formatRankState = (state: RankState) => `S${state.tier} · ${state.points}pt`
/** このゲームの仕様：ポイントが残っている間の敗北ではランクを下げず、0で止める。0からの敗北で初めて降格する。 */
function applyRankChange(before: RankState, change: number): RankState {
  const state = normalizeRankState(before.tier, before.points)
  const delta = Math.trunc(Number.isFinite(change) ? change : 0)
  if (delta >= 0) return rankStateFromLegacyTotal(Math.min(MAX_TOTAL_RANK_POINTS, rankStateToTotal(state) + delta))
  const loss = Math.abs(delta)
  if (state.points > 0) return { tier: state.tier, points: Math.max(0, state.points - loss) }
  if (state.tier === MIN_RANK) return { tier: MIN_RANK, points: 0 }
  return { tier: state.tier - 1, points: clampInteger(500 - loss, 0, MAX_RANK_POINTS) }
}
function seasonStartRankFromPreviousTier(previousTier: number): RankState {
  if (previousTier <= 4) return { tier: 1, points: 250 }
  if (previousTier <= 7) return { tier: 2, points: 250 }
  return { tier: 3, points: 250 }
}
function monthFromSeasonLabel(label: string | undefined): string | null {
  if (!label) return null
  const match = label.match(/^(\d{4})年(\d{1,2})月シーズン$/)
  if (!match) return null
  return `${match[1]}-${String(Number(match[2])).padStart(2, '0')}`
}
const currentMonthKey = () => today().slice(0, 7)
function previousMonthKey(): string {
  const now = new Date()
  const previous = new Date(now.getFullYear(), now.getMonth() - 1, 1)
  return `${previous.getFullYear()}-${String(previous.getMonth() + 1).padStart(2, '0')}`
}
function seasonLabelFromMonthKey(monthKey: string): string {
  const [year, month] = monthKey.split('-')
  return year && month ? `${year}年${Number(month)}月シーズン` : ''
}
const freshStore = (): Store => {
  // リセットするまでは前月シーズンを維持し、12日以降の自動リセット対象にする。
  const previousMonth = previousMonthKey()
  return {
    matches: [], heroes: initialHeroes, maps: initialMaps, initialRankPoints: null, lastMode: 'バトアリ',
    currentRankTier: 1, currentRankPoints: 0,
    activeSeason: seasonLabelFromMonthKey(previousMonth), lastSeasonResetMonth: previousMonth
  }
}
const mergeHeroes = (saved: Hero[] | undefined | null): Hero[] => {
  const merged = new Map<string, Hero>()
  initialHeroes.forEach(hero => merged.set(hero.name, hero))
  // お気に入りは維持しつつ、標準ヒーローのロールは最新定義で補正します。
  ;(saved ?? []).forEach(hero => {
    if (hero && typeof hero.name === 'string' && roles.includes(hero.role)) {
      const canonical = merged.get(hero.name)
      merged.set(hero.name, canonical ? { ...hero, role: canonical.role } : hero)
    }
  })
  return [...merged.values()]
}
function normalizeStore(input: Partial<Store> | null | undefined): Store {
  const matches = Array.isArray(input?.matches) ? input.matches : []
  const heroes = mergeHeroes(input?.heroes)
  const maps = Array.isArray(input?.maps) && input.maps.length ? input.maps : initialMaps
  const initialRankPoints = typeof input?.initialRankPoints === 'number' ? input.initialRankPoints : null
  const chronological = [...matches].sort((a, b) => a.playedAt.localeCompare(b.playedAt))
  let inferredRank: RankState
  if (Number.isInteger(input?.currentRankTier) && Number(input?.currentRankTier) >= MIN_RANK && Number(input?.currentRankTier) <= MAX_RANK
    && Number.isInteger(input?.currentRankPoints) && Number(input?.currentRankPoints) >= 0 && Number(input?.currentRankPoints) <= MAX_RANK_POINTS) {
    inferredRank = normalizeRankState(Number(input?.currentRankTier), Number(input?.currentRankPoints))
  } else {
    const latestSnapshot = [...chronological].reverse().find(match => typeof match.rankPoints === 'number')
    let legacyTotal: number | null = null
    if (latestSnapshot && typeof latestSnapshot.rankPoints === 'number') {
      legacyTotal = latestSnapshot.rankPoints + chronological
        .filter(match => match.playedAt > latestSnapshot.playedAt && typeof match.rankChange === 'number')
        .reduce((sum, match) => sum + Number(match.rankChange || 0), 0)
    } else if (initialRankPoints !== null) {
      legacyTotal = initialRankPoints + chronological.reduce((sum, match) => sum + (typeof match.rankChange === 'number' ? match.rankChange : 0), 0)
    }
    inferredRank = legacyTotal === null ? { tier: 1, points: 0 } : rankStateFromLegacyTotal(legacyTotal)
  }
  const now = nowLocalInput()
  const latestSeason = [...chronological].reverse().find(match => typeof match.season === 'string' && match.season.trim())?.season
  const activeSeason = typeof input?.activeSeason === 'string' && input.activeSeason.trim()
    ? input.activeSeason
    : latestSeason || seasonLabelFromDate(now)
  // 旧版にはリセット履歴がないため、今月のリセット未実施として移行します。
  // 12日以降なら初回表示時に一度だけ自動リセットされます。
  const resetMonth = typeof input?.lastSeasonResetMonth === 'string' && /^\d{4}-\d{2}$/.test(input.lastSeasonResetMonth)
    ? input.lastSeasonResetMonth
    : previousMonthKey()
  return {
    ...(input ?? {}), matches, heroes, maps, initialRankPoints,
    lastMode: input?.lastMode === 'フリバ' ? 'フリバ' : 'バトアリ',
    lastUsedHeroName: typeof input?.lastUsedHeroName === 'string' ? input.lastUsedHeroName : undefined,
    lastLockedAllyHeroNames: Array.isArray(input?.lastLockedAllyHeroNames)
      ? input.lastLockedAllyHeroNames.slice(0, 2).map(name => typeof name === 'string' ? name : '') : ['', ''],
    lastLockedAllySlots: Array.isArray(input?.lastLockedAllySlots)
      ? [Boolean(input.lastLockedAllySlots[0]), Boolean(input.lastLockedAllySlots[1])] : [false, false],
    currentRankTier: inferredRank.tier, currentRankPoints: inferredRank.points,
    activeSeason, lastSeasonResetMonth: resetMonth
  }
}
function loadStore(): Store {
  try {
    const raw = localStorage.getItem(storageKey)
    if (raw) return normalizeStore(JSON.parse(raw) as Partial<Store>)
  } catch { /* 壊れたローカルデータは初期値で開始 */ }
  return freshStore()
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
function normalizeHeroSearchText(value: string) {
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

function TrackerApp() {
  const cloud = useContext(CloudContext)
  const [store, setStore] = useState<Store>(loadStore)
  const storeRef = useRef(store)
  const savedDraft = useMemo(() => loadRecordDraft(), [])
  const [rankTierDraft, setRankTierDraft] = useState(savedDraft?.rankTierDraft ?? String(store.currentRankTier ?? 1))
  const [rankPointsDraft, setRankPointsDraft] = useState(savedDraft?.rankPointsDraft ?? String(store.currentRankPoints ?? 0))
  const [page, setPage] = useState<Page>(() =>
    ['dashboard', 'add', 'history', 'settings'].includes(savedDraft?.page ?? '') ? savedDraft!.page! : 'dashboard'
  )
  const [toast, setToast] = useState('')
  const [editingId, setEditingId] = useState<string | null>(() => savedDraft?.editingId ?? null)
  const [historyQuery, setHistoryQuery] = useState('')
  const [historyResult, setHistoryResult] = useState<'all' | Result>('all')
  const [historyHero, setHistoryHero] = useState('all')
  const [historyMonth, setHistoryMonth] = useState('all')
  const [historyMode, setHistoryMode] = useState<'all' | Mode>('all')
  const [heroRoleFilter, setHeroRoleFilter] = useState<'all' | Role>('all')
  const [favoritesOnly, setFavoritesOnly] = useState(false)
  const [recordSlide, setRecordSlide] = useState<1 | 2>(() => savedDraft?.recordSlide === 2 ? 2 : 1)
  const [lockAlly1, setLockAlly1] = useState(() => savedDraft?.lockAlly1 ?? Boolean(store.lastLockedAllySlots?.[0]))
  const [lockAlly2, setLockAlly2] = useState(() => savedDraft?.lockAlly2 ?? Boolean(store.lastLockedAllySlots?.[1]))
  const slideTouchStartX = useRef<number | null>(null)
  const importRef = useRef<HTMLInputElement>(null)
  const [form, setForm] = useState(() => {
    const defaults = {
      playedAt: nowLocalInput(), seasonEnabled: false, seasonLabel: store.activeSeason ?? seasonLabelFromDate(nowLocalInput()), mode: (store.lastMode ?? 'バトアリ') as Mode,
      heroName: store.lastUsedHeroName ?? [...store.matches].sort((a, b) => b.playedAt.localeCompare(a.playedAt))[0]?.heroName ?? '',
      mapName: store.maps[0] ?? '', result: 'win' as Result,
      rankDirection: 'plus' as 'plus' | 'minus', rankDelta: '0', memo: '',
      enemyHeroNames: ['', '', ''],
      allyHeroNames: [...(store.lastLockedAllyHeroNames ?? ['', '']), '', ''].slice(0, 2)
    }
    const draft = savedDraft?.form
    if (!draft || typeof draft !== 'object') return defaults
    const enemies = Array.isArray(draft.enemyHeroNames) ? draft.enemyHeroNames : defaults.enemyHeroNames
    const allies = Array.isArray(draft.allyHeroNames) ? draft.allyHeroNames : defaults.allyHeroNames
    return {
      ...defaults, ...draft,
      enemyHeroNames: [...enemies, '', '', ''].slice(0, 3),
      allyHeroNames: [...allies, '', ''].slice(0, 2)
    }
  })
  const [heroDraft, setHeroDraft] = useState('')
  const [heroRoleDraft, setHeroRoleDraft] = useState<Role>('アタッカー')
  const [mapDraft, setMapDraft] = useState('')

  useEffect(() => { storeRef.current = store }, [store])
  useEffect(() => { localStorage.setItem(storageKey, JSON.stringify(store)); cloud?.saveCloudStore(store) }, [store])
  useEffect(() => {
    try {
      localStorage.setItem(recordDraftStorageKey, JSON.stringify({
        page, form, editingId, recordSlide, lockAlly1, lockAlly2, rankTierDraft, rankPointsDraft
      }))
    } catch { /* localStorage が利用できない環境では下書き保存を省略 */ }
  }, [page, form, editingId, recordSlide, lockAlly1, lockAlly2, rankTierDraft, rankPointsDraft])
  useEffect(() => {
    const checkAutomaticSeasonReset = () => {
      const current = storeRef.current
      const date = today()
      const month = date.slice(0, 7)
      const day = Number(date.slice(8, 10))
      if (day < 12 || current.lastSeasonResetMonth === month) return
      const startRank = seasonStartRankFromPreviousTier(current.currentRankTier ?? 1)
      const season = seasonLabelFromDate(nowLocalInput())
      const updated: Store = { ...current, currentRankTier: startRank.tier, currentRankPoints: startRank.points, activeSeason: season, lastSeasonResetMonth: month }
      storeRef.current = updated
      setStore(updated)
      setRankTierDraft(String(startRank.tier))
      setRankPointsDraft(String(startRank.points))
      notify(`${season}へ自動リセットしました（S${startRank.tier}・250pt）`)
    }
    checkAutomaticSeasonReset()
    const interval = window.setInterval(checkAutomaticSeasonReset, 60 * 60 * 1000)
    return () => window.clearInterval(interval)
  }, [])
  const sortedMatches = useMemo(() => [...store.matches].sort((a, b) => b.playedAt.localeCompare(a.playedAt)), [store.matches])
  const todayMatches = sortedMatches.filter(match => match.playedAt.slice(0, 10) === today())
  const todayWins = todayMatches.filter(match => match.result === 'win').length
  const todayLosses = todayMatches.filter(match => match.result === 'loss').length
  const todayWinRate = percent(todayWins, todayWins + todayLosses)
  const allWins = store.matches.filter(match => match.result === 'win').length
  const allLosses = store.matches.filter(match => match.result === 'loss').length
  const allTimeWinRate = percent(allWins, allWins + allLosses)
  const currentRankState = normalizeRankState(store.currentRankTier ?? 1, store.currentRankPoints ?? 0)
  const currentStreak = useMemo(() => {
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
  const managedHeroes = useMemo(() => [...store.heroes].sort((a, b) =>
    roles.indexOf(a.role) - roles.indexOf(b.role)
    || (heroOrderIndex.get(a.name) ?? Number.MAX_SAFE_INTEGER) - (heroOrderIndex.get(b.name) ?? Number.MAX_SAFE_INTEGER)
  ), [store.heroes])
  const selectedHero = store.heroes.find(hero => hero.name === form.heroName)
  const teamHeroOptions = useMemo(() => [...store.heroes].sort((a, b) =>
    (heroOrderIndex.get(a.name) ?? Number.MAX_SAFE_INTEGER) - (heroOrderIndex.get(b.name) ?? Number.MAX_SAFE_INTEGER)
  ), [store.heroes])
  function changeHeroRoleFilter(role: 'all' | Role) {
    setHeroRoleFilter(role)
    setForm(old => ({ ...old, heroName: '' }))
  }
  function changeFavoritesOnly(checked: boolean) {
    setFavoritesOnly(checked)
    setForm(old => ({ ...old, heroName: '' }))
  }
  function toggleFavorite(name: string) {
    setStore(current => ({ ...current, heroes: current.heroes.map(hero => hero.name === name ? { ...hero, favorite: !hero.favorite } : hero) }))
  }

  function setTeamHero(side: 'enemyHeroNames' | 'allyHeroNames', index: number, name: string) {
    setForm(old => {
      const names = [...old[side]]
      names[index] = name
      return { ...old, [side]: names }
    })
  }

  function notify(message: string) { setToast(message); window.setTimeout(() => setToast(''), 2600) }
  function startNewMatch() {
    setEditingId(null)
    setHeroRoleFilter('all')
    setFavoritesOnly(false)
    setRecordSlide(1)
    setForm({ playedAt: nowLocalInput(), seasonEnabled: false, seasonLabel: store.activeSeason ?? seasonLabelFromDate(nowLocalInput()), mode: store.lastMode ?? 'バトアリ', heroName: store.lastUsedHeroName ?? sortedMatches[0]?.heroName ?? '', mapName: store.maps[0] ?? '', result: 'win', rankDirection: 'plus', rankDelta: '0', memo: '', enemyHeroNames: ['', '', ''], allyHeroNames: [lockAlly1 ? (form.allyHeroNames[0] ?? '') : '', lockAlly2 ? (form.allyHeroNames[1] ?? '') : ''] })
    setRankTierDraft(String(store.currentRankTier ?? 1))
    setRankPointsDraft(String(store.currentRankPoints ?? 0))
    setPage('add')
  }
  function beginEditMatch(match: Match) {
    setRecordSlide(1)
    setEditingId(match.id)
    setHeroRoleFilter('all')
    setFavoritesOnly(false)
    setForm({ playedAt: normalizeDateTime(match.playedAt), seasonEnabled: Boolean(match.season) && (match.mode ?? 'バトアリ') === 'バトアリ', seasonLabel: match.season || store.activeSeason || seasonLabelFromDate(nowLocalInput()), mode: match.mode ?? 'バトアリ', heroName: match.heroName, mapName: match.mapName, result: match.result, rankDirection: (match.rankChange ?? (match.result === 'loss' ? -1 : 1)) < 0 ? 'minus' : 'plus', rankDelta: String(Math.abs(match.rankChange ?? 0)), memo: match.memo ?? '', enemyHeroNames: [...(match.enemyHeroNames ?? []), '', '', ''].slice(0, 3), allyHeroNames: [...(match.allyHeroNames ?? []), '', ''].slice(0, 2) })
    setPage('add')
  }
  function changeResult(result: Result) {
    setForm(old => ({ ...old, result, rankDirection: result === 'loss' ? 'minus' : 'plus', rankDelta: result === 'draw' ? '0' : old.rankDelta }))
  }
  function readRankDraft(): RankState | null {
    const tier = Number(rankTierDraft)
    const points = Number(rankPointsDraft)
    if (!Number.isInteger(tier) || tier < MIN_RANK || tier > MAX_RANK) {
      notify('ランクはS1〜S9から選択してください')
      return null
    }
    if (!Number.isInteger(points) || points < 0 || points > MAX_RANK_POINTS) {
      notify('有効なランクポイントを整数で入力してください')
      return null
    }
    return { tier, points }
  }
  function saveMatch(e: React.FormEvent) {
    e.preventDefault()
    const hero = store.heroes.find(h => h.name === form.heroName)
    if (!hero || !form.mapName) { notify('ヒーローとマップを選択してください'); return }
    if (editingId && !form.playedAt) { notify('試合日時を入力してください'); return }
    const recordedAt = editingId ? normalizeDateTime(form.playedAt) : nowLocalInput()
    const amountText = form.rankDelta.trim()
    const amount = amountText === '' ? 0 : Number(amountText)
    if (!Number.isFinite(amount) || amount < 0 || !Number.isInteger(amount)) { notify('RP変動は0以上の整数で入力してください'); return }
    const rankedMatch = form.mode === 'バトアリ'
    const requestedChange = form.result === 'draw' || !rankedMatch ? 0 : (form.rankDirection === 'minus' ? -Math.abs(amount) : Math.abs(amount))
    const existingMatch = editingId ? store.matches.find(m => m.id === editingId) : undefined
    const parsedDraft = readRankDraft()
    if (!parsedDraft) return
    const rankBefore = existingMatch && Number.isInteger(existingMatch.rankBeforeTier) && Number.isInteger(existingMatch.rankBeforePoints)
      ? normalizeRankState(Number(existingMatch.rankBeforeTier), Number(existingMatch.rankBeforePoints))
      : existingMatch && typeof existingMatch.rankPoints === 'number'
        ? rankStateFromLegacyTotal(existingMatch.rankPoints - (typeof existingMatch.rankChange === 'number' ? existingMatch.rankChange : 0))
        : rankedMatch ? parsedDraft : currentRankState
    const rankAfter = rankedMatch ? applyRankChange(rankBefore, requestedChange) : rankBefore
    const season = form.mode === 'バトアリ' && form.seasonEnabled
      ? (editingId ? (form.seasonLabel || store.activeSeason || seasonLabelFromDate(recordedAt)) : (store.activeSeason || seasonLabelFromDate(recordedAt)))
      : ''
    const match: Match = {
      id: editingId ?? crypto.randomUUID(), playedAt: recordedAt,
      season,
      heroName: hero.name, heroRole: hero.role, mapName: form.mapName, result: form.result,
      enemyHeroNames: [...form.enemyHeroNames], allyHeroNames: [...form.allyHeroNames],
      rankPoints: rankStateToTotal(rankAfter), rankChange: requestedChange, mode: form.mode, memo: form.memo.trim(),
      rankBeforeTier: rankBefore.tier, rankBeforePoints: rankBefore.points,
      rankAfterTier: rankAfter.tier, rankAfterPoints: rankAfter.points
    }
    const nextLockedAllySlots = [lockAlly1, lockAlly2]
    const nextLockedAllyHeroNames = [
      lockAlly1 ? (form.allyHeroNames[0] ?? '') : '',
      lockAlly2 ? (form.allyHeroNames[1] ?? '') : ''
    ]
    if (editingId) {
      const updated: Store = { ...storeRef.current, lastMode: form.mode, matches: storeRef.current.matches.map(m => m.id === editingId ? match : m) }
      storeRef.current = updated
      setStore(updated)
    } else {
      const updated: Store = {
        ...storeRef.current,
        lastMode: form.mode,
        lastUsedHeroName: hero.name,
        lastLockedAllyHeroNames: nextLockedAllyHeroNames,
        lastLockedAllySlots: nextLockedAllySlots,
        matches: [match, ...storeRef.current.matches],
        ...(rankedMatch ? { currentRankTier: rankAfter.tier, currentRankPoints: rankAfter.points } : {})
      }
      storeRef.current = updated
      setStore(updated)
      if (rankedMatch) {
        setRankTierDraft(String(rankAfter.tier))
        setRankPointsDraft(String(rankAfter.points))
      }
    }
    const wasEditing = editingId !== null
    setRecordSlide(1)
    setEditingId(null)
    if (wasEditing) {
      setPage('dashboard')
    } else {
      const nextDate = nowLocalInput()
        setHeroRoleFilter('all')
      setFavoritesOnly(false)
      setForm(old => ({ playedAt: nextDate, seasonEnabled: old.mode === 'バトアリ' ? old.seasonEnabled : false,
        seasonLabel: storeRef.current.activeSeason ?? seasonLabelFromDate(nextDate), mode: old.mode, heroName: hero.name,
        mapName: old.mapName || storeRef.current.maps[0] || '', result: 'win', rankDirection: 'plus', rankDelta: '0', memo: '', enemyHeroNames: ['', '', ''], allyHeroNames: nextLockedAllyHeroNames }))
      setPage('add')
    }
    notify(wasEditing ? '試合記録を更新しました' : rankedMatch ? `試合を記録しました（${formatRankState(rankAfter)}）。次の試合を入力できます` : `${form.mode}の試合を記録しました。次の試合を入力できます`)
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
        const restored = normalizeStore(data as Partial<Store>)
        storeRef.current = restored
        setStore(restored)
        setRankTierDraft(String(restored.currentRankTier ?? 1))
        setRankPointsDraft(String(restored.currentRankPoints ?? 0))
        
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
  function editHeroAliases(hero: Hero) {
    const answer = window.prompt(
      `${hero.name} の略称を入力してください。複数ある場合は「,」または「、」で区切ります。
空欄で保存すると略称を削除します。`,
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
      <div className="brand-mark"><img className="brand-mark-image" src={compassNoteMark} alt="" /></div>
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
        <div className="stats-grid dashboard-stats-grid">
          <div className="stat-card current-rank-stat-card"><div className="stat-top"><span>現在のランク</span><span className="stat-icon"><BarChart3 size={19}/></span></div><strong>{`S${currentRankState.tier} · ${currentRankState.points}pt`}</strong><small>{store.activeSeason ?? 'シーズン未設定'}</small></div>
          <StatCard icon={<Trophy size={19}/>} label="今日の勝率" value={todayWinRate} sub={`${todayWins}勝 · ${todayLosses}敗`} />
          <StatCard icon={<Trophy size={19}/>} label="全体勝率" value={allTimeWinRate} sub={`${allWins}勝 · ${allLosses}敗`} />
          <StatCard icon={<CalendarDays size={19}/>} label="総試合数" value={`${store.matches.length}`} sub="記録した試合" />
          <StatCard icon={<Activity size={19}/>} label="現在の連続結果" value={currentStreak.count ? `${currentStreak.count}${currentStreak.result}` : '—'} sub={`最高連勝：${highestWinStreak}`} />
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
        <div className="section-heading record-form-heading"><div className="record-current-rank"><span>現在のランク</span><strong>{`S${currentRankState.tier} · ${currentRankState.points}pt`}</strong></div><div className="round-icon"><Swords size={20}/></div></div>
        <form onSubmit={saveMatch} className="match-form" onTouchStart={e => { slideTouchStartX.current = e.touches[0]?.clientX ?? null }} onTouchEnd={e => { const startX = slideTouchStartX.current; slideTouchStartX.current = null; if (startX == null) return; const delta = (e.changedTouches[0]?.clientX ?? startX) - startX; if (delta < -55) setRecordSlide(2); else if (delta > 55) setRecordSlide(1) }}>
          <div className="match-slide-viewport"><div className={`match-slide-track ${recordSlide === 2 ? 'show-team-page' : ''}`}><div className="match-slide match-slide-primary">
          {editingId && <div className="field field-wide"><label>試合日時（分まで）</label><input type="datetime-local" required={recordSlide === 1} value={form.playedAt} onChange={e => setForm({ ...form, playedAt: e.target.value })}/></div>}
          <div className="field field-wide mode-selection-only">
            <div className="mode-selection-column">
              <label>モード</label>
              <div className="result-options mode-options">
                {(['バトアリ', 'フリバ', 'カスタム'] as Mode[]).map(mode => <button type="button" key={mode} className={`result-choice ${form.mode === mode ? 'selected win' : ''}`} onClick={() => setForm(old => ({ ...old, mode, seasonEnabled: mode !== 'バトアリ' ? false : old.seasonEnabled }))}>{mode}</button>)}
              </div>
              <label className={`season-check ${form.mode !== 'バトアリ' ? 'season-disabled' : ''}`}><input type="checkbox" disabled={form.mode !== 'バトアリ'} checked={form.mode === 'バトアリ' && form.seasonEnabled} onChange={e => setForm(old => ({ ...old, seasonEnabled: e.target.checked }))}/><span>シーズン</span></label>
              <small className="active-season-note">現在のシーズン：{store.activeSeason ?? '未設定'}</small>
            </div>

          </div>
          <div className="field field-wide hero-picker-controls hero-picker-filters-only">
            <div className="hero-filter-control"><label>絞込み</label>
              <div className="hero-role-buttons">{(['all', ...roles] as ('all' | Role)[]).map(role => <button type="button" key={role} className={`role-filter-button ${heroRoleFilter === role ? 'active' : ''}`} onClick={() => changeHeroRoleFilter(role)}>{role === 'all' ? 'すべて' : role}</button>)}</div>
              <label className="favorite-filter"><input type="checkbox" checked={favoritesOnly} onChange={e => changeFavoritesOnly(e.target.checked)}/><span><Star size={13}/> お気に入り</span></label>
            </div>
          </div>
          <div className="field field-wide hero-select-field"><label>使用ヒーロー（{visibleHeroes.length}人）</label>
            <div className="hero-select-row"><SearchableHeroDropdown value={form.heroName} heroes={visibleHeroes} onChange={name => setForm(old => ({ ...old, heroName: name }))} placeholder="ヒーローを検索・選択" />
              <button type="button" className={`favorite-toggle ${selectedHero?.favorite ? 'is-favorite' : ''}`} disabled={!selectedHero} aria-label={selectedHero?.favorite ? 'お気に入りを解除' : 'お気に入りに登録'} aria-pressed={Boolean(selectedHero?.favorite)} title={selectedHero?.favorite ? 'お気に入りを解除' : 'お気に入りに登録'} onClick={() => selectedHero && toggleFavorite(selectedHero.name)}><Star size={18} fill={selectedHero?.favorite ? 'currentColor' : 'none'}/></button>
            </div>
            {visibleHeroes.length === 0 && <small className="small-note">条件に一致するヒーローがいません。検索や絞込みを変更してください。</small>}
          </div>
          <div className="field field-wide"><label>マップ</label><select required={recordSlide === 1} value={form.mapName} onChange={e => setForm({ ...form, mapName: e.target.value })}>{store.maps.map(m => <option key={m} value={m}>{m}</option>)}</select></div>
          <div className="field field-wide"><label>試合結果</label><div className="result-options">
            {(['win', 'loss', 'draw'] as Result[]).map(r => <button type="button" key={r} className={`result-choice ${form.result === r ? `selected ${r}` : ''}`} onClick={() => changeResult(r)}>{resultLabel(r)}</button>)}
          </div></div>
          {form.mode === 'バトアリ' ? <div className="field field-wide"><label>ランクポイントの増減 <small>実際の増減量を入力</small></label>
            <div className="rp-change-control"><div className="rp-direction-buttons"><button type="button" className={`result-choice ${form.rankDirection === 'plus' ? 'selected win' : ''}`} onClick={() => setForm({ ...form, rankDirection: 'plus' })}><Plus size={16}/> 増加</button><button type="button" className={`result-choice ${form.rankDirection === 'minus' ? 'selected loss' : ''}`} onClick={() => setForm({ ...form, rankDirection: 'minus' })}><Minus size={16}/> 減少</button></div><input aria-label="RP変動量" type="number" min="0" step="1" placeholder="0" value={form.rankDelta} onChange={e => setForm({ ...form, rankDelta: e.target.value })}/><strong className={form.result === 'draw' ? '' : form.rankDirection === 'minus' ? 'negative-rp' : 'positive-rp'}>{form.result === 'draw' ? '±0' : form.rankDirection === 'minus' ? `−${Math.abs(Number(form.rankDelta) || 0).toLocaleString()}` : `+${Math.abs(Number(form.rankDelta) || 0).toLocaleString()}`}</strong></div>
            <small className="small-note">試合後の予測ランク：{(() => { const before = normalizeRankState(Number(rankTierDraft) || currentRankState.tier, Number(rankPointsDraft) || 0); const delta = form.result === 'draw' ? 0 : (form.rankDirection === 'minus' ? -1 : 1) * Math.abs(Number(form.rankDelta) || 0); return formatRankState(applyRankChange(before, delta)) })()}</small>
          </div> : <div className="field field-wide freeba-rank-note"><strong>{form.mode}ではランクポイントは変動しません。</strong><span>現在のランクは記録・確認のみ行います。</span></div>}
          <div className="record-slide-nav primary-slide-nav" aria-label="記録ページの移動">
            <div className="record-slide-steps"><span className="record-slide-step active">1 基本情報</span><span className="record-slide-step">2 チーム構成</span></div>
            <div className="record-slide-actions">
              <button type="submit" className="primary-button">{editingId ? <><Pencil size={17}/> 変更を保存</> : <><Plus size={17}/> 記録を保存</>}</button>
              <button type="button" className="secondary-button" onClick={() => setRecordSlide(2)}>次へ：チーム構成 →</button>
            </div>
          </div>
          </div><div className="match-slide match-slide-teams">
          <div className="record-slide-nav team-page-nav" aria-label="記録ページの移動">
            <button type="button" className="secondary-button" onClick={() => setRecordSlide(1)}>← 基本情報へ戻る</button>
            <span className="record-slide-step active">2 チーム構成</span>
          </div>
          <div className="team-page-heading"><h4>チーム構成</h4><p>敵チーム3人、味方チームは自分以外の2人を任意で記録できます。横にスワイプしてページを移動できます。</p></div>
          <div className="team-composition-grid">
            <section className="team-composition-side">
              <div className="team-side-header"><h4>味方チーム <small>自分以外の2人</small></h4></div>
              <div className="team-select-list ally-select-list">
                {Array.from({ length: 2 }, (_, index) => {
                  const locked = index === 0 ? lockAlly1 : lockAlly2
                  const toggleLock = () => index === 0 ? setLockAlly1(value => !value) : setLockAlly2(value => !value)
                  return <label key={`ally-${index}`}><span>味方 {index + 1}</span><div className="team-select-with-lock"><SearchableHeroDropdown value={form.allyHeroNames[index] ?? ''} heroes={teamHeroOptions} onChange={name => setTeamHero('allyHeroNames', index, name)} placeholder="— 未選択 —" /><button type="button" className={`ally-lock-toggle ally-slot-lock ${locked ? 'locked' : ''}`} aria-label={locked ? `味方${index + 1}の固定を解除` : `味方${index + 1}を固定`} aria-pressed={locked} title={locked ? `味方${index + 1}は固定中` : `味方${index + 1}を固定`} onClick={toggleLock}>{locked ? <Lock size={16}/> : <Unlock size={16}/>}</button></div></label>
                })}
              </div>
              <p className="team-lock-help">{lockAlly1 && lockAlly2 ? '味方1・2を固定中です。' : lockAlly1 ? '味方1を固定中です。味方2は記録後にリセットされます。' : lockAlly2 ? '味方2を固定中です。味方1は記録後にリセットされます。' : 'ロックした味方だけ、記録後も選択を保持します。'}</p>
            </section>
            <section className="team-composition-side">
              <div className="team-side-header"><h4>敵チーム <small>任意・最大3人</small></h4></div>
              <div className="team-select-list">
                {Array.from({ length: 3 }, (_, index) => <label key={`enemy-${index}`}><span>敵 {index + 1}</span><SearchableHeroDropdown value={form.enemyHeroNames[index] ?? ''} heroes={teamHeroOptions} onChange={name => setTeamHero('enemyHeroNames', index, name)} placeholder="— 未選択 —" /></label>)}
              </div>
            </section>
          </div>
          <div className="field field-wide"><label>メモ <small>任意</small></label><textarea rows={3} placeholder="味方編成、反省点、気づいたことなど" value={form.memo} onChange={e => setForm({ ...form, memo: e.target.value })}/></div>
          <div className="form-actions"><button type="button" className="secondary-button" onClick={() => { setEditingId(null); setRecordSlide(1); setPage('dashboard') }}>キャンセル</button><button type="submit" className="primary-button">{editingId ? <><Pencil size={17}/> 変更を保存</> : <><Plus size={17}/> 記録を保存して次へ</>}</button></div>
          </div></div></div>
        </form>
      </section>}

      {page === 'history' && <section className="content-card">
        <div className="section-heading"><div><h3>すべての戦績</h3><p>{filteredMatches.length} 件表示 / 全 {store.matches.length} 件</p></div><button className="primary-button" onClick={startNewMatch}><Plus size={17}/> 試合を追加</button></div>
        <div className="history-filters">
          <label className="search-field"><Search size={16}/><input value={historyQuery} onChange={e => setHistoryQuery(e.target.value)} placeholder="ヒーロー・マップ・メモを検索" /></label>
          <select aria-label="結果で絞り込み" value={historyResult} onChange={e => setHistoryResult(e.target.value as 'all' | Result)}><option value="all">すべての結果</option><option value="win">勝ち</option><option value="loss">負け</option><option value="draw">引き分け</option></select>
          <select aria-label="ヒーローで絞り込み" value={historyHero} onChange={e => setHistoryHero(e.target.value)}><option value="all">すべてのヒーロー</option>{store.heroes.map(h => <option key={h.name} value={h.name}>{h.name}</option>)}</select>
          <select aria-label="月で絞り込み" value={historyMonth} onChange={e => setHistoryMonth(e.target.value)}><option value="all">すべての月</option>{availableMonths.map(m => <option key={m} value={m}>{m}</option>)}</select>
          <select aria-label="モードで絞り込み" value={historyMode} onChange={e => setHistoryMode(e.target.value as 'all' | Mode)}><option value="all">すべてのモード</option><option value="バトアリ">バトアリ</option><option value="フリバ">フリバ</option><option value="カスタム">カスタム</option></select>
        </div>
        {filteredMatches.length ? <MatchTable matches={filteredMatches} onEdit={beginEditMatch} onDelete={deleteMatch}/> : store.matches.length ? <p className="empty-inline">条件に一致する記録がありません。絞り込み条件を変更してください。</p> : <EmptyState onAdd={startNewMatch}/>}
      </section>}

      {page === 'settings' && <section className="page-stack">
        <div className="content-card">
          <div className="section-heading"><div><h3>バックアップと復元</h3><p>記録データを JSON ファイルとして保存できます。</p></div><div className="round-icon"><Shield size={20}/></div></div>
          <div className="backup-actions"><button className="primary-button" onClick={exportData}><Download size={17}/> バックアップを保存</button><button className="secondary-button" onClick={() => importRef.current?.click()}><FileUp size={17}/> バックアップから復元</button><input ref={importRef} hidden type="file" accept="application/json,.json" onChange={e => { importData(e.target.files?.[0]); e.currentTarget.value = '' }}/></div>
          <p className="small-note">復元すると現在のデータはバックアップの内容に置き換わります。必要に応じて先にバックアップを保存してください。</p>
        </div>
        <div className="content-card">
          <div className="section-heading"><div><h3>ヒーロー管理</h3><p>名前とロールを追加できます。削除は試合記録で未使用の場合のみ可能です。</p></div></div>
          <div className="catalog-add"><input value={heroDraft} placeholder="ヒーロー名" onChange={e => setHeroDraft(e.target.value)} onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addHero())}/><select value={heroRoleDraft} onChange={e => setHeroRoleDraft(e.target.value as Role)}>{roles.map(r => <option key={r}>{r}</option>)}</select><button className="primary-button" onClick={addHero}><Plus size={16}/> 追加</button></div>
          <div className="catalog-list">{managedHeroes.map(h => <div className="catalog-item hero-catalog-item" key={h.name}><span className="hero-catalog-name">{h.name}{h.aliases?.length ? <small className="hero-alias-summary">略称：{h.aliases.join('、')}</small> : null}</span><span className={`role-pill role-${roles.indexOf(h.role)}`}>{h.role}</span><button className="icon-button alias-edit-button" aria-label={`${h.name}の略称を設定`} title="略称を設定・編集" onClick={() => editHeroAliases(h)}><Pencil size={15}/></button><button className="icon-button" aria-label={`${h.name}を削除`} onClick={() => removeHero(h.name)}><Trash2 size={16}/></button></div>)}</div>
        </div>
        <div className="content-card">
          <div className="section-heading"><div><h3>マップ管理</h3><p>マップを追加できます。削除は試合記録で未使用の場合のみ可能です。</p></div></div>
          <div className="catalog-add"><input value={mapDraft} placeholder="マップ名" onChange={e => setMapDraft(e.target.value)} onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addMap())}/><button className="primary-button" onClick={addMap}><Plus size={16}/> 追加</button></div>
          <div className="catalog-list map-list">{store.maps.map(m => <div className="catalog-item" key={m}><span>{m}</span><button className="icon-button" aria-label={`${m}を削除`} onClick={() => removeMap(m)}><Trash2 size={16}/></button></div>)}</div>
        </div>
        <div className="content-card future-card"><div className="round-icon"><Activity size={20}/></div><div><h3>現在の機能</h3><p>試合日時、バトアリ／フリバ、リセット操作で切り替わるシーズン、実装時期順のヒーロー選択、お気に入り・ロール絞込み、S1〜S9のランク・ポイント管理、バックアップ・復元に対応しています。</p></div></div>
      </section>}
      <footer className="app-footer">コンパス戦績ノート <span>·</span> Version 0.2.0</footer>
    </main>
    {toast && <div className="toast"><span className="toast-dot"/>{toast}<button onClick={() => setToast('')} aria-label="閉じる"><X size={15}/></button></div>}
  </div>
}

function SearchableHeroDropdown({ value, heroes, onChange, placeholder }: { value: string; heroes: Hero[]; onChange: (name: string) => void; placeholder: string }) {
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
  return <div className="table-wrap"><table className="match-table"><thead><tr><th>日時</th><th>モード／シーズン</th><th>ヒーロー</th><th>マップ</th><th>結果</th><th>RP変動</th><th>試合後ランク</th><th>操作</th></tr></thead><tbody>{matches.map(m => <tr key={m.id}><td className="date-cell">{formatDateTime(m.playedAt)}</td><td><div className="hero-cell"><strong>{m.mode ?? 'バトアリ'}</strong><small>{m.season || '通常記録'}</small></div></td><td><div className="hero-cell"><strong>{m.heroName}</strong><small>{m.heroRole}</small></div></td><td className="map-cell">{m.mapName}</td><td><span className={`result-pill ${m.result}`}>{resultLabel(m.result)}</span></td><td className="rp-cell">{signedText(m.rankChange)}</td><td className="rp-cell">{Number.isInteger(m.rankAfterTier) && Number.isInteger(m.rankAfterPoints) ? formatRankState(normalizeRankState(Number(m.rankAfterTier), Number(m.rankAfterPoints))) : m.rankPoints == null ? '—' : formatRankState(rankStateFromLegacyTotal(m.rankPoints))}</td><td><div className="row-actions"><button className="icon-button edit-icon" aria-label={`${m.playedAt}の記録を編集`} title="編集" onClick={() => onEdit(m)}><Pencil size={15}/></button><button className="icon-button" aria-label="記録を削除" title="削除" onClick={() => onDelete(m.id)}><Trash2 size={15}/></button></div></td></tr>)}</tbody></table></div>
}

function readLocalStore(): Store | null {
  try {
    const raw = localStorage.getItem(storageKey)
    if (!raw) return null
    const parsed = JSON.parse(raw) as Partial<Store>
    if (!Array.isArray(parsed.matches) || !Array.isArray(parsed.heroes) || !Array.isArray(parsed.maps)) return null
    return normalizeStore(parsed)
  } catch { return null }
}

export default function App() {
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    try {
      return localStorage.getItem('compass-rank-tracker-theme-v1') === 'light' ? 'light' : 'dark'
    } catch { return 'dark' }
  })
  useEffect(() => {
    document.documentElement.dataset.theme = theme
    try { localStorage.setItem('compass-rank-tracker-theme-v1', theme) } catch { /* storage may be unavailable */ }
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', theme === 'light' ? '#f1f9fb' : '#080c15')
  }, [theme])
  const themeToggle = <button type="button" className="theme-toggle" onClick={() => setTheme(current => current === 'dark' ? 'light' : 'dark')} aria-label={theme === 'dark' ? 'ライトモードに切り替え' : 'ダークモードに切り替え'}>
    {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
    <span>{theme === 'dark' ? 'ライトモード' : 'ダークモード'}</span>
  </button>
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
        const payload = normalizeStore(data.payload as Partial<Store>)
        localStorage.setItem(storageKey, JSON.stringify(payload))
        setSyncStatus('同期済み')
      } else {
        const local = readLocalStore() ?? freshStore()
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

  if (!supabase) return <div className="auth-shell">{themeToggle}<div className="auth-card"><div className="brand-mark"><img className="brand-mark-image" src={compassNoteMark} alt="" /></div><h1>クラウド同期の設定</h1><p>Supabase の接続情報がまだ設定されていません。公開設定後に、このアプリを利用できるようになります。</p><ol><li>Supabase プロジェクトを作成</li><li>SQL Editor で <code>supabase/migrations/001_initial_schema.sql</code> を実行</li><li>プロジェクトの URL と Publishable key をホスティング設定に登録</li></ol><p className="small-note">この設定画面は、接続情報を入力する前の状態です。</p></div></div>
  if (!user) return <div className="auth-shell">{themeToggle}<form className="auth-card" onSubmit={submitAuth}><div className="brand-mark"><img className="brand-mark-image" src={compassNoteMark} alt="" /></div><div className="eyebrow">RANK TRACKER CLOUD</div><h1>コンパス戦績ノート</h1><p>アカウントでログインすると、PC とスマホで記録を共有できます。</p><div className="field"><label>メールアドレス</label><input type="email" required autoComplete="email" value={email} onChange={e => setEmail(e.target.value)} /></div><div className="field"><label>パスワード（6文字以上）</label><input type="password" required minLength={6} autoComplete={mode === 'signup' ? 'new-password' : 'current-password'} value={password} onChange={e => setPassword(e.target.value)} /></div><button className="primary-button auth-submit" type="submit">{mode === 'login' ? 'ログイン' : 'アカウントを作成'}</button><button className="text-button auth-switch" type="button" onClick={() => { setMode(mode === 'login' ? 'signup' : 'login'); setMessage('') }}>{mode === 'login' ? '初めて使う方：アカウント作成' : 'すでにアカウントをお持ちの方：ログイン'}</button>{message && <p className="auth-message">{message}</p>}</form></div>
  if (!ready) return <div className="auth-shell">{themeToggle}<div className="auth-card"><div className="brand-mark"><img className="brand-mark-image" src={compassNoteMark} alt="" /></div><h1>クラウドデータを準備中</h1><p>{syncStatus}。しばらくお待ちください。</p>{message && <p className="auth-message">{message}</p>}<button className="secondary-button" onClick={() => supabase.auth.signOut()}>ログアウト</button></div></div>
  return <CloudContext.Provider value={{ saveCloudStore, syncStatus }}><><div className="cloud-user-bar">{themeToggle}<span className="cloud-login-status">ログイン中 · 同期：{syncStatus}</span><button className="logout-button" onClick={() => supabase.auth.signOut()}>ログアウト</button></div><TrackerApp /></></CloudContext.Provider>
}
