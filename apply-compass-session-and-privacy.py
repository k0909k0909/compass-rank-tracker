#!/usr/bin/env python3
"""Apply session-draft persistence, remembered hero/team defaults, and email hiding.

Run this from the repository root:
    python apply-compass-session-and-privacy.py

The script edits only src/App.tsx and creates its backup outside the repository.
"""
from datetime import datetime
from pathlib import Path
import shutil
import sys

APP_PATH = Path("src/App.tsx")
DRAFT_KEY_MARKER = "const recordDraftStorageKey = `${storageKey}-record-draft`"

def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(
            f"変更箇所「{label}」を一意に特定できませんでした（検出数: {count}）。"
            "ファイルは変更していません。GitHubの最新コードか確認してください。"
        )
    return source.replace(old, new, 1)

def main() -> int:
    if not APP_PATH.is_file():
        print("エラー: src/App.tsx が見つかりません。リポジトリのルートで実行してください。")
        return 1

    original = APP_PATH.read_text(encoding="utf-8")
    if DRAFT_KEY_MARKER in original:
        print("この改善はすでに適用されているようです。src/App.tsx は変更していません。")
        return 0

    updated = original
    updated = replace_once(
        updated,
        "  lastMode?: Mode\n  /** 現在のランク（S1〜S9） */",
        "  lastMode?: Mode\n"
        "  /** 次回の試合記録で初期選択するヒーロー */\n"
        "  lastUsedHeroName?: string\n"
        "  /** 次回の試合記録で引き継ぐ、固定中の味方ヒーロー */\n"
        "  lastLockedAllyHeroNames?: string[]\n"
        "  /** 味方1・2それぞれの固定状態 */\n"
        "  lastLockedAllySlots?: boolean[]\n"
        "  /** 現在のランク（S1〜S9） */",
        "Store型への記録引き継ぎ項目の追加",
    )
    updated = replace_once(
        updated,
        "const storageKey = 'compass-rank-tracker-v1'\n",
        "const storageKey = 'compass-rank-tracker-v1'\n"
        "const recordDraftStorageKey = `${storageKey}-record-draft`\n",
        "入力途中データ用の保存キー追加",
    )
    updated = replace_once(
        updated,
        "type RankState = { tier: number; points: number }\n",
        "type RecordDraft = {\n"
        "  page?: Page\n"
        "  editingId?: string | null\n"
        "  recordSlide?: 1 | 2\n"
        "  lockAlly1?: boolean\n"
        "  lockAlly2?: boolean\n"
        "  rankTierDraft?: string\n"
        "  rankPointsDraft?: string\n"
        "  form?: Record<string, any>\n"
        "}\n"
        "function loadRecordDraft(): RecordDraft | null {\n"
        "  try {\n"
        "    const raw = localStorage.getItem(recordDraftStorageKey)\n"
        "    if (!raw) return null\n"
        "    const parsed = JSON.parse(raw) as RecordDraft\n"
        "    return parsed && typeof parsed === 'object' ? parsed : null\n"
        "  } catch { return null }\n"
        "}\n"
        "type RankState = { tier: number; points: number }\n",
        "入力途中データの読み込み処理追加",
    )
    updated = replace_once(
        updated,
        "    lastMode: input?.lastMode === 'フリバ' ? 'フリバ' : 'バトアリ',\n"
        "    currentRankTier: inferredRank.tier, currentRankPoints: inferredRank.points,\n",
        "    lastMode: input?.lastMode === 'フリバ' ? 'フリバ' : 'バトアリ',\n"
        "    lastUsedHeroName: typeof input?.lastUsedHeroName === 'string' ? input.lastUsedHeroName : undefined,\n"
        "    lastLockedAllyHeroNames: Array.isArray(input?.lastLockedAllyHeroNames)\n"
        "      ? input.lastLockedAllyHeroNames.slice(0, 2).map(name => typeof name === 'string' ? name : '') : ['', ''],\n"
        "    lastLockedAllySlots: Array.isArray(input?.lastLockedAllySlots)\n"
        "      ? [Boolean(input.lastLockedAllySlots[0]), Boolean(input.lastLockedAllySlots[1])] : [false, false],\n"
        "    currentRankTier: inferredRank.tier, currentRankPoints: inferredRank.points,\n",
        "保存済みヒーロー・味方固定設定の読み込み",
    )
    updated = replace_once(
        updated,
        "  const [store, setStore] = useState<Store>(loadStore)\n"
        "  const storeRef = useRef(store)\n"
        "  const [rankTierDraft, setRankTierDraft] = useState(String(store.currentRankTier ?? 1))\n"
        "  const [rankPointsDraft, setRankPointsDraft] = useState(String(store.currentRankPoints ?? 0))\n"
        "  const [page, setPage] = useState<Page>('dashboard')\n"
        "  const [toast, setToast] = useState('')\n"
        "  const [editingId, setEditingId] = useState<string | null>(null)\n",
        "  const [store, setStore] = useState<Store>(loadStore)\n"
        "  const storeRef = useRef(store)\n"
        "  const savedDraft = useMemo(() => loadRecordDraft(), [])\n"
        "  const [rankTierDraft, setRankTierDraft] = useState(savedDraft?.rankTierDraft ?? String(store.currentRankTier ?? 1))\n"
        "  const [rankPointsDraft, setRankPointsDraft] = useState(savedDraft?.rankPointsDraft ?? String(store.currentRankPoints ?? 0))\n"
        "  const [page, setPage] = useState<Page>(() =>\n"
        "    ['dashboard', 'add', 'history', 'settings'].includes(savedDraft?.page ?? '') ? savedDraft!.page! : 'dashboard'\n"
        "  )\n"
        "  const [toast, setToast] = useState('')\n"
        "  const [editingId, setEditingId] = useState<string | null>(() => savedDraft?.editingId ?? null)\n",
        "ページ・編集中IDの復元",
    )
    updated = replace_once(
        updated,
        "  const [recordSlide, setRecordSlide] = useState<1 | 2>(1)\n"
        "  const [lockAlly1, setLockAlly1] = useState(false)\n"
        "  const [lockAlly2, setLockAlly2] = useState(false)\n",
        "  const [recordSlide, setRecordSlide] = useState<1 | 2>(() => savedDraft?.recordSlide === 2 ? 2 : 1)\n"
        "  const [lockAlly1, setLockAlly1] = useState(() => savedDraft?.lockAlly1 ?? Boolean(store.lastLockedAllySlots?.[0]))\n"
        "  const [lockAlly2, setLockAlly2] = useState(() => savedDraft?.lockAlly2 ?? Boolean(store.lastLockedAllySlots?.[1]))\n",
        "チーム構成ページと味方ロック状態の復元",
    )
    updated = replace_once(
        updated,
        "  const [form, setForm] = useState({\n"
        "    playedAt: nowLocalInput(), seasonEnabled: false, seasonLabel: store.activeSeason ?? seasonLabelFromDate(nowLocalInput()), mode: (store.lastMode ?? 'バトアリ') as Mode,\n"
        "    heroName: [...store.matches].sort((a, b) => b.playedAt.localeCompare(a.playedAt))[0]?.heroName ?? '', mapName: store.maps[0] ?? '', result: 'win' as Result,\n"
        "    rankDirection: 'plus' as 'plus' | 'minus', rankDelta: '0', memo: '',\n"
        "    enemyHeroNames: ['', '', ''], allyHeroNames: ['', '']\n"
        "  })\n",
        "  const [form, setForm] = useState(() => {\n"
        "    const defaults = {\n"
        "      playedAt: nowLocalInput(), seasonEnabled: false, seasonLabel: store.activeSeason ?? seasonLabelFromDate(nowLocalInput()), mode: (store.lastMode ?? 'バトアリ') as Mode,\n"
        "      heroName: store.lastUsedHeroName ?? [...store.matches].sort((a, b) => b.playedAt.localeCompare(a.playedAt))[0]?.heroName ?? '',\n"
        "      mapName: store.maps[0] ?? '', result: 'win' as Result,\n"
        "      rankDirection: 'plus' as 'plus' | 'minus', rankDelta: '0', memo: '',\n"
        "      enemyHeroNames: ['', '', ''],\n"
        "      allyHeroNames: [...(store.lastLockedAllyHeroNames ?? ['', '']), '', ''].slice(0, 2)\n"
        "    }\n"
        "    const draft = savedDraft?.form\n"
        "    if (!draft || typeof draft !== 'object') return defaults\n"
        "    const enemies = Array.isArray(draft.enemyHeroNames) ? draft.enemyHeroNames : defaults.enemyHeroNames\n"
        "    const allies = Array.isArray(draft.allyHeroNames) ? draft.allyHeroNames : defaults.allyHeroNames\n"
        "    return {\n"
        "      ...defaults, ...draft,\n"
        "      enemyHeroNames: [...enemies, '', '', ''].slice(0, 3),\n"
        "      allyHeroNames: [...allies, '', ''].slice(0, 2)\n"
        "    }\n"
        "  })\n",
        "試合フォームの復元と前回ヒーロー初期値",
    )
    updated = replace_once(
        updated,
        "  useEffect(() => { storeRef.current = store }, [store])\n"
        "  useEffect(() => { localStorage.setItem(storageKey, JSON.stringify(store)); cloud?.saveCloudStore(store) }, [store])\n",
        "  useEffect(() => { storeRef.current = store }, [store])\n"
        "  useEffect(() => { localStorage.setItem(storageKey, JSON.stringify(store)); cloud?.saveCloudStore(store) }, [store])\n"
        "  useEffect(() => {\n"
        "    try {\n"
        "      localStorage.setItem(recordDraftStorageKey, JSON.stringify({\n"
        "        page, form, editingId, recordSlide, lockAlly1, lockAlly2, rankTierDraft, rankPointsDraft\n"
        "      }))\n"
        "    } catch { /* localStorage が利用できない環境では下書き保存を省略 */ }\n"
        "  }, [page, form, editingId, recordSlide, lockAlly1, lockAlly2, rankTierDraft, rankPointsDraft])\n",
        "入力途中データの自動保存",
    )
    updated = replace_once(
        updated,
        "    setForm({ playedAt: nowLocalInput(), seasonEnabled: false, seasonLabel: store.activeSeason ?? seasonLabelFromDate(nowLocalInput()), mode: store.lastMode ?? 'バトアリ', heroName: sortedMatches[0]?.heroName ?? '', mapName: store.maps[0] ?? '', result: 'win', rankDirection: 'plus', rankDelta: '0', memo: '', enemyHeroNames: ['', '', ''], allyHeroNames: [lockAlly1 ? (form.allyHeroNames[0] ?? '') : '', lockAlly2 ? (form.allyHeroNames[1] ?? '') : ''] })\n",
        "    setForm({ playedAt: nowLocalInput(), seasonEnabled: false, seasonLabel: store.activeSeason ?? seasonLabelFromDate(nowLocalInput()), mode: store.lastMode ?? 'バトアリ', heroName: store.lastUsedHeroName ?? sortedMatches[0]?.heroName ?? '', mapName: store.maps[0] ?? '', result: 'win', rankDirection: 'plus', rankDelta: '0', memo: '', enemyHeroNames: ['', '', ''], allyHeroNames: [lockAlly1 ? (form.allyHeroNames[0] ?? '') : '', lockAlly2 ? (form.allyHeroNames[1] ?? '') : ''] })\n",
        "新規記録ボタンの前回ヒーロー初期値",
    )
    updated = replace_once(
        updated,
        "    }\n"
        "    if (editingId) {\n"
        "      const updated: Store = { ...storeRef.current, lastMode: form.mode, matches: storeRef.current.matches.map(m => m.id === editingId ? match : m) }\n",
        "    }\n"
        "    const nextLockedAllySlots = [lockAlly1, lockAlly2]\n"
        "    const nextLockedAllyHeroNames = [\n"
        "      lockAlly1 ? (form.allyHeroNames[0] ?? '') : '',\n"
        "      lockAlly2 ? (form.allyHeroNames[1] ?? '') : ''\n"
        "    ]\n"
        "    if (editingId) {\n"
        "      const updated: Store = { ...storeRef.current, lastMode: form.mode, matches: storeRef.current.matches.map(m => m.id === editingId ? match : m) }\n",
        "次回用の固定味方情報を保存分岐より前に作成",
    )
    updated = replace_once(
        updated,
        "    const wasEditing = editingId !== null\n"
        "    setRecordSlide(1)\n",
        "    const wasEditing = editingId !== null\n"
        "    setRecordSlide(1)\n",
        "保存処理後の編集状態判定",
    )
    updated = replace_once(
        updated,
        "        ...storeRef.current,\n"
        "        lastMode: form.mode,\n"
        "        matches: [match, ...storeRef.current.matches],\n",
        "        ...storeRef.current,\n"
        "        lastMode: form.mode,\n"
        "        lastUsedHeroName: hero.name,\n"
        "        lastLockedAllyHeroNames: nextLockedAllyHeroNames,\n"
        "        lastLockedAllySlots: nextLockedAllySlots,\n"
        "        matches: [match, ...storeRef.current.matches],\n",
        "新しい試合の保存時に前回選択を記録",
    )
    updated = replace_once(
        updated,
        "        mapName: old.mapName || storeRef.current.maps[0] || '', result: 'win', rankDirection: 'plus', rankDelta: '0', memo: '', enemyHeroNames: ['', '', ''], allyHeroNames: [lockAlly1 ? (old.allyHeroNames[0] ?? '') : '', lockAlly2 ? (old.allyHeroNames[1] ?? '') : ''] }))\n",
        "        mapName: old.mapName || storeRef.current.maps[0] || '', result: 'win', rankDirection: 'plus', rankDelta: '0', memo: '', enemyHeroNames: ['', '', ''], allyHeroNames: nextLockedAllyHeroNames }))\n",
        "記録直後の次フォームに固定味方を引き継ぐ",
    )
    updated = replace_once(
        updated,
        "<span className=\"cloud-login-status\">{user.email} でログイン中 · 同期：{syncStatus}</span>",
        "<span className=\"cloud-login-status\">ログイン中 · 同期：{syncStatus}</span>",
        "ログインメールアドレスを非表示",
    )

    for required in [
        "const recordDraftStorageKey = `${storageKey}-record-draft`",
        "localStorage.setItem(recordDraftStorageKey",
        "lastUsedHeroName: hero.name",
        "lastLockedAllySlots: nextLockedAllySlots",
        "cloud-login-status\">ログイン中 · 同期：",
    ]:
        if required not in updated:
            raise RuntimeError(f"最終確認に失敗しました: {required}")

    backup_dir = Path.home() / ".cache" / "compass-rank-tracker-backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"App.tsx.{datetime.now().strftime('%Y%m%d-%H%M%S')}.bak"
    shutil.copy2(APP_PATH, backup_path)
    APP_PATH.write_text(updated, encoding="utf-8")
    print("改善を適用しました: src/App.tsx")
    print(f"変更前バックアップ: {backup_path}")
    print("次に npm run build を実行して、ビルドエラーがないことを確認してください。")
    print("このスクリプト自体はリポジトリにコミットする必要はありません。")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        raise SystemExit(1)
