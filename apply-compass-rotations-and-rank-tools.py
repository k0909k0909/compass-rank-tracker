from pathlib import Path
import re
import shutil

ROOT = Path.cwd()
APP = ROOT / "src" / "App.tsx"
if not APP.exists():
    raise SystemExit("src/App.tsx が見つかりません。Codespaces のリポジトリ直下で実行してください。")

source = APP.read_text(encoding="utf-8")
original = source


def replace_once(old: str, new: str, label: str) -> None:
    global source
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: 置換対象が1か所ではありません（{count}か所）。ファイルは変更していません。")
    source = source.replace(old, new, 1)


# 1) OCR library import
replace_once(
    "import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'\n",
    "import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'\nimport { createWorker } from 'tesseract.js'\n",
    "Tesseract.js import",
)

# 2) Store schema
replace_once(
    "  /** YYYY-MM。月ごとの自動リセット重複防止用 */\n  lastSeasonResetMonth?: string\n}",
    "  /** YYYY-MM。月ごとの自動リセット重複防止用 */\n  lastSeasonResetMonth?: string\n  /** バトアリのステージローテーション。日付ごとに4ステージを保存し、別月へ流用しない */\n  stageRotations?: Record<string, string[]>\n}",
    "Store.stageRotations",
)

# 3) Default November 2026 rotation data (read from the two supplied screenshots)
replace_once(
    "const storageKey = 'compass-rank-tracker-v1'",
    """const initialNovember2026StageRotations: Record<string, string[]> = {
  '2026-11-06': ['でらクランクストリート', 'けっこいスターパーク', '東西たかさん広場', '妖華帝都ケルパーズの散歩道'],
  '2026-11-09': ['でらクランクストリート', '光と闇のライブステージ', '太鼓で祭りだドーン！', 'マジきてる #夜光犯罪特区'],
  '2026-11-10': ['でらクランクストリート', 'グレートウォール', '立体交差のある風景', 'ジャンジャン麻雀の間'],
  '2026-11-11': ['でらクランクストリート', 'ちゅら島リゾート', 'かけだせ！じっぱか城', 'バリバリ！てげてげモーターウェイ'],
  '2026-11-12': ['でらクランクストリート', 'おいでやす鳥居通り', 'Hello :-) irregular World', 'なまらモーモーパーク'],
  // 画像表記「ってー！」は、既存マップ一覧の登録名「って〜！」に合わせています。
  '2026-11-13': ['でらクランクストリート', 'って〜！つっぺる工事現場', 'おっかねぇ！氷焔神域ケイオスブルク', 'いこっさ！ダイダイダイナソー博物館']
}
const storageKey = 'compass-rank-tracker-v1'""",
    "November 2026 seed rotation",
)

# 4) Normalize old store data without a rotation field, while preserving explicit empty/custom data.
replace_once(
    "  const resetMonth = typeof input?.lastSeasonResetMonth === 'string' && /^\\d{4}-\\d{2}$/.test(input.lastSeasonResetMonth)\n    ? input.lastSeasonResetMonth\n    : previousMonthKey()\n  return {",
    """  const resetMonth = typeof input?.lastSeasonResetMonth === 'string' && /^\\d{4}-\\d{2}$/.test(input.lastSeasonResetMonth)
    ? input.lastSeasonResetMonth
    : previousMonthKey()
  const stageRotations: Record<string, string[]> = {}
  if (input?.stageRotations && typeof input.stageRotations === 'object' && !Array.isArray(input.stageRotations)) {
    Object.entries(input.stageRotations).forEach(([date, names]) => {
      if (/^\\d{4}-\\d{2}-\\d{2}$/.test(date) && Array.isArray(names)) {
        stageRotations[date] = names.filter((name): name is string => typeof name === 'string').slice(0, 4)
      }
    })
  } else {
    Object.assign(stageRotations, initialNovember2026StageRotations)
  }
  return {""",
    "normalize stage rotations",
)
replace_once(
    "    activeSeason, lastSeasonResetMonth: resetMonth\n  }\n}",
    "    activeSeason, lastSeasonResetMonth: resetMonth, stageRotations\n  }\n}",
    "normalized Store return",
)
replace_once(
    "    currentRankTier: 1, currentRankPoints: 0,\n    activeSeason: seasonLabelFromMonthKey(previousMonth), lastSeasonResetMonth: previousMonth\n",
    "    currentRankTier: 1, currentRankPoints: 0,\n    activeSeason: seasonLabelFromMonthKey(previousMonth), lastSeasonResetMonth: previousMonth,\n    stageRotations: { ...initialNovember2026StageRotations }\n",
    "freshStore default rotations",
)

# 5) OCR parsing helper functions
replace_once(
    "function TrackerApp() {",
    """type RotationOcrCandidate = { date: string; maps: string[] }

function normalizeRotationOcrText(value: string) {
  return value.normalize('NFKC').replace(/[\\s\\u3000]/g, '').replace(/[～〜]/g, '〜')
}

function extractRotationCandidates(text: string, monthKey: string, mapNames: string[]): RotationOcrCandidate[] {
  const [yearText, monthText] = monthKey.split('-')
  const year = Number(yearText)
  const month = Number(monthText)
  if (!Number.isInteger(year) || !Number.isInteger(month) || month < 1 || month > 12) return []
  const headingPattern = new RegExp(`${month}月\\s*(\\d{1,2})日`, 'g')
  const headings = [...text.matchAll(headingPattern)]
  const candidates: RotationOcrCandidate[] = []
  headings.forEach((heading, index) => {
    const day = Number(heading[1])
    if (!Number.isInteger(day) || day < 1 || day > 31) return
    const start = (heading.index ?? 0) + heading[0].length
    const end = index + 1 < headings.length ? (headings[index + 1].index ?? text.length) : text.length
    const block = normalizeRotationOcrText(text.slice(start, end))
    const found = mapNames.map(name => {
      const normalized = normalizeRotationOcrText(name)
      const alternatives = [normalized, normalized.replace('って〜!', 'ってー!')]
      const positions = alternatives.map(candidate => block.indexOf(candidate)).filter(position => position >= 0)
      return { name, position: positions.length ? Math.min(...positions) : -1 }
    }).filter(item => item.position >= 0).sort((a, b) => a.position - b.position)
    const maps = found.map(item => item.name).filter((name, mapIndex, list) => list.indexOf(name) === mapIndex)
    if (maps.length > 0) {
      candidates.push({ date: `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`, maps })
    }
  })
  return candidates
}

function TrackerApp() {""",
    "OCR parsing helpers",
)

# 6) Add rotation editor and OCR state
replace_once(
    "  const [mapDraft, setMapDraft] = useState('')\n",
    """  const [mapDraft, setMapDraft] = useState('')
  const [rankRotationDateDraft, setRotationDateDraft] = useState('2026-11-06')
  const [rotationMonthDraft, setRotationMonthDraft] = useState('2026-11')
  const [rotationMapDrafts, setRotationMapDrafts] = useState<string[]>(() => [...(store.stageRotations?.['2026-11-06'] ?? ['', '', '', ''])])
  const [rotationOcrText, setRotationOcrText] = useState('')
  const [rotationOcrBusy, setRotationOcrBusy] = useState(false)
  const [rotationOcrStatus, setRotationOcrStatus] = useState('')
  const [rotationOcrCandidates, setRotationOcrCandidates] = useState<RotationOcrCandidate[]>([])
  const rotationImageRef = useRef<HTMLInputElement>(null)
""",
    "rotation editor state",
)

# 7) Calculate map options for the selected record date. Rotations apply only to Battle Arena.
replace_once(
    "  const selectedHero = store.heroes.find(hero => hero.name === form.heroName)\n",
    """  const selectedHero = store.heroes.find(hero => hero.name === form.heroName)
  const recordRotationDate = editingId ? form.playedAt.slice(0, 10) : today()
  const configuredRotationMaps = store.stageRotations?.[recordRotationDate]
  const validRotationMaps = Array.isArray(configuredRotationMaps)
    ? configuredRotationMaps.filter(name => store.maps.includes(name))
    : []
  const rotationApplied = form.mode === 'バトアリ' && configuredRotationMaps?.length === 4 && validRotationMaps.length === 4
  const availableRecordMaps = rotationApplied ? validRotationMaps : store.maps
  const availableRecordMapsKey = availableRecordMaps.join('\\u0000')
  useEffect(() => {
    if (availableRecordMaps.length > 0 && !availableRecordMaps.includes(form.mapName)) {
      setForm(current => current.mapName === form.mapName ? { ...current, mapName: availableRecordMaps[0] } : current)
    }
  }, [availableRecordMapsKey, form.mapName])
""",
    "Battle Arena map filtering",
)

# 8) Manual current-rank correction action
replace_once(
    "  function saveMatch(e: React.FormEvent) {",
    """  function applyManualRankCorrection() {
    const corrected = readRankDraft()
    if (!corrected) return
    const updated: Store = { ...storeRef.current, currentRankTier: corrected.tier, currentRankPoints: corrected.points }
    storeRef.current = updated
    setStore(updated)
    setRankTierDraft(String(corrected.tier))
    setRankPointsDraft(String(corrected.points))
    notify(`現在のランクを ${formatRankState(corrected)} に修正しました`)
  }

  function saveMatch(e: React.FormEvent) {""",
    "manual rank correction handler",
)

# 9) Validate map selection against active rotation when saving a match.
replace_once(
    "    if (!hero || !form.mapName) { notify('ヒーローとマップを選択してください'); return }",
    "    if (!hero || !form.mapName || !availableRecordMaps.includes(form.mapName)) { notify('ヒーローと、その日・モードで選択可能なマップを選んでください'); return }",
    "record map validation",
)

# 10) Add rotation management and OCR handlers after removeMap.
replace_once(
    "  function removeMap(name: string) {\n    if (store.matches.some(m => m.mapName === name)) { notify('試合記録に使用中のため削除できません'); return }\n    if (window.confirm(`「${name}」を一覧から削除しますか？`)) setStore(s => ({ ...s, maps: s.maps.filter(m => m !== name) }))\n  }\n",
    """  function removeMap(name: string) {
    if (store.matches.some(m => m.mapName === name)) { notify('試合記録に使用中のため削除できません'); return }
    if (window.confirm(`「${name}」を一覧から削除しますか？`)) setStore(s => ({ ...s, maps: s.maps.filter(m => m !== name) }))
  }

  function saveStageRotation() {
    if (!/^\\d{4}-\\d{2}-\\d{2}$/.test(rankRotationDateDraft)) { notify('対象日付を選択してください'); return }
    if (rankRotationDateDraft.slice(0, 7) !== rotationMonthDraft) { notify('登録する月と対象日付の月を一致させてください'); return }
    const maps = rotationMapDrafts.map(name => name.trim())
    if (maps.length !== 4 || maps.some(name => !name)) { notify('4つのステージをすべて選択してください'); return }
    if (new Set(maps).size !== 4) { notify('同じステージを重複して登録できません'); return }
    const updated: Store = { ...storeRef.current, stageRotations: { ...(storeRef.current.stageRotations ?? {}), [rankRotationDateDraft]: maps } }
    storeRef.current = updated
    setStore(updated)
    notify(`${rankRotationDateDraft} のステージローテーションを登録しました`)
  }

  function removeStageRotation(date: string) {
    if (!window.confirm(`${date} のステージローテーションを削除しますか？削除後、その日は全ステージが選択可能になります。`)) return
    const stageRotations = { ...(storeRef.current.stageRotations ?? {}) }
    delete stageRotations[date]
    const updated: Store = { ...storeRef.current, stageRotations }
    storeRef.current = updated
    setStore(updated)
    notify(`${date} のローテーションを削除しました`)
  }

  function registerOcrCandidate(candidate: RotationOcrCandidate) {
    if (candidate.maps.length !== 4) { notify(`${candidate.date} は4ステージすべてを特定できなかったため、手動で確認してください`); return }
    const updated: Store = { ...storeRef.current, stageRotations: { ...(storeRef.current.stageRotations ?? {}), [candidate.date]: candidate.maps } }
    storeRef.current = updated
    setStore(updated)
    setRotationDateDraft(candidate.date)
    setRotationMonthDraft(candidate.date.slice(0, 7))
    setRotationMapDrafts([...candidate.maps])
    notify(`${candidate.date} の4ステージを登録しました`)
  }

  async function recognizeRotationImages(files: File[]) {
    const imageFiles = files.filter(file => file.type.startsWith('image/'))
    if (imageFiles.length === 0) { notify('画像ファイルを選択してください'); return }
    if (imageFiles.some(file => file.size > 20 * 1024 * 1024)) { notify('画像サイズは1枚あたり20MB以下にしてください'); return }
    setRotationOcrBusy(true)
    setRotationOcrStatus('日本語OCRを準備しています…')
    setRotationOcrText('')
    setRotationOcrCandidates([])
    let terminateWorker: (() => Promise<void>) | undefined
    try {
      const worker = await createWorker(['jpn', 'eng'], 1, {
        logger: message => {
          if (message.status === 'recognizing text') {
            setRotationOcrStatus(`画像を読み取り中：${Math.round(message.progress * 100)}%`)
          } else if (message.status) {
            setRotationOcrStatus(message.status)
          }
        }
      })
      terminateWorker = () => worker.terminate()
      const recognizedParts: string[] = []
      for (const [index, file] of imageFiles.entries()) {
        setRotationOcrStatus(`${index + 1}/${imageFiles.length}枚目を読み取り中：${file.name}`)
        const result = await worker.recognize(file)
        recognizedParts.push(`【${file.name}】\n${result.data.text ?? ''}`)
      }
      const recognizedText = recognizedParts.join('\n\n')
      setRotationOcrText(recognizedText)
      setRotationOcrStatus(recognizedText.trim() ? '読み取り完了。文字を確認し「候補を抽出」を押してください。' : '文字を認識できませんでした。画像を変えるか手入力してください。')
    } catch (error) {
      const detail = error instanceof Error ? error.message : String(error)
      setRotationOcrStatus(`画像の読み取りに失敗しました：${detail}`)
    } finally {
      if (terminateWorker) {
        try { await terminateWorker() } catch { /* OCR worker cleanup */ }
      }
      setRotationOcrBusy(false)
    }
  }

  function extractOcrRotationCandidates() {
    const candidates = extractRotationCandidates(rotationOcrText, rotationMonthDraft, store.maps)
    setRotationOcrCandidates(candidates)
    if (candidates.length === 0) {
      setRotationOcrStatus('日付と登録済みマップ名を組み合わせた候補が見つかりませんでした。画像の文字起こしを修正して再実行してください。')
    } else {
      setRotationOcrStatus(`${candidates.length}日分の候補を抽出しました。各日付のステージ名を確認して登録してください。`)
    }
  }
""",
    "rotation and OCR handlers",
)

# 11) Map selector displays only the allowed four maps on registered Battle Arena dates.
replace_once(
    "          <div className=\"field field-wide\"><label>マップ</label><select required={recordSlide === 1} value={form.mapName} onChange={e => setForm({ ...form, mapName: e.target.value })}>{store.maps.map(m => <option key={m} value={m}>{m}</option>)}</select></div>",
    "          <div className=\"field field-wide\"><label>マップ</label><select required={recordSlide === 1} value={availableRecordMaps.includes(form.mapName) ? form.mapName : (availableRecordMaps[0] ?? '')} onChange={e => setForm({ ...form, mapName: e.target.value })}>{availableRecordMaps.map(m => <option key={m} value={m}>{m}</option>)}</select><small className=\"small-note\">{rotationApplied ? `${recordRotationDate} のバトアリは登録済みの4ステージのみ表示しています。` : `この日付のバトアリローテーションは未登録です。全マップを表示しています。フリバ・カスタムは常に全マップです。`}</small></div>",
    "record map dropdown",
)

# 12) Settings: rank correction and date-specific rotation editor with local OCR.
settings_anchor = """        <div className=\"content-card\">
          <div className=\"section-heading\"><div><h3>ヒーロー管理</h3><p>名前とロールを追加できます。削除は試合記録で未使用の場合のみ可能です。</p></div></div>"""
settings_insert = """        <div className=\"content-card\">
          <div className=\"section-heading\"><div><h3>現在のランク・ポイントを修正</h3><p>記録ミスなどで現在値がずれた場合に、正しい値へ直接変更できます。</p></div><div className=\"round-icon\"><Gauge size={20}/></div></div>
          <div className=\"catalog-add\">
            <select aria-label=\"現在のランク\" value={rankTierDraft} onChange={e => setRankTierDraft(e.target.value)}>{Array.from({ length: 9 }, (_, index) => <option key={index + 1} value={String(index + 1)}>S{index + 1}</option>)}</select>
            <input aria-label=\"現在のランクポイント\" type=\"number\" min=\"0\" max=\"499\" step=\"1\" value={rankPointsDraft} onChange={e => setRankPointsDraft(e.target.value)} placeholder=\"0〜499\" />
            <button className=\"primary-button\" onClick={applyManualRankCorrection}>現在ランクを修正</button>
          </div>
          <p className=\"small-note\">S1〜S9と、そのランク内の0〜499ptを入力してください。過去の試合履歴は書き換えず、現在ランクと次回記録の基準値だけを修正します。</p>
        </div>
        <div className=\"content-card\">
          <div className=\"section-heading\"><div><h3>ステージローテーション</h3><p>日付ごとにバトアリの4ステージを登録します。登録のない日やフリバ・カスタムでは全マップが選べます。</p></div><div className=\"round-icon\"><CalendarDays size={20}/></div></div>
          <div className=\"field field-wide\"><label>登録する月</label><input type=\"month\" value={rotationMonthDraft} onChange={e => setRotationMonthDraft(e.target.value)} /></div>
          <div className=\"field field-wide\"><label>対象日付</label><input type=\"date\" value={rankRotationDateDraft} onChange={e => {
            const date = e.target.value
            setRotationDateDraft(date)
            if (date) setRotationMonthDraft(date.slice(0, 7))
            setRotationMapDrafts(date && store.stageRotations?.[date] ? [...store.stageRotations[date]] : ['', '', '', ''])
          }} /></div>
          <div className=\"catalog-list\">
            {rotationMapDrafts.map((name, index) => <div className=\"catalog-item\" key={index}><span>ステージ {index + 1}</span><select aria-label={`ステージ${index + 1}`} value={name} onChange={e => setRotationMapDrafts(current => current.map((item, itemIndex) => itemIndex === index ? e.target.value : item))}><option value=\"\">選択してください</option>{store.maps.map(map => <option key={map} value={map}>{map}</option>)}</select></div>)}
          </div>
          <div className=\"backup-actions\"><button className=\"primary-button\" onClick={saveStageRotation}><Plus size={16}/> この日付の4ステージを登録</button></div>
          <p className=\"small-note\">シーズン初日の木曜日、土日、全ステージ対象の日は登録不要です。ローテーション対象日のみ登録してください。日付単位で保存するため、別の月へ自動流用されません。</p>
          <div className=\"section-heading\"><div><h4>登録済みローテーション</h4><p>登録した日付のみバトアリのマップ候補を制限します。</p></div></div>
          <div className=\"catalog-list\">{Object.entries(store.stageRotations ?? {}).sort(([a], [b]) => a.localeCompare(b)).map(([date, maps]) => <div className=\"catalog-item\" key={date}><span className=\"rotation-list-name\"><strong>{date}</strong><small>{maps.join(' ／ ')}</small></span><button className=\"icon-button\" aria-label={`${date}のローテーションを削除`} onClick={() => removeStageRotation(date)}><Trash2 size={16}/></button></div>)}{Object.keys(store.stageRotations ?? {}).length === 0 && <p className=\"empty-inline\">ローテーションはまだ登録されていません。</p>}</div>
          <div className=\"section-heading\"><div><h4>画像からローテーションを読み取る</h4><p>お知らせ画像を読み取り、日付ごとの4ステージ候補を作ります。</p></div></div>
          <div className=\"backup-actions\"><button type=\"button\" className=\"secondary-button\" onClick={() => rotationImageRef.current?.click()} disabled={rotationOcrBusy}><FileUp size={16}/> ローテーション画像を選択</button><input ref={rotationImageRef} hidden type=\"file\" accept=\"image/*\" multiple onChange={e => { const files = Array.from(e.target.files ?? []); if (files.length) void recognizeRotationImages(files); e.currentTarget.value = '' }} /></div>
          {rotationOcrStatus && <p className=\"small-note\">{rotationOcrStatus}</p>}
          <div className=\"field field-wide\"><label>読み取った文字（必要なら編集できます）</label><textarea rows={7} value={rotationOcrText} onChange={e => setRotationOcrText(e.target.value)} placeholder=\"画像を選択すると、ここに読み取った文字が表示されます。\" /></div>
          <div className=\"backup-actions\"><button type=\"button\" className=\"primary-button\" onClick={extractOcrRotationCandidates} disabled={rotationOcrBusy || !rotationOcrText.trim()}>候補を抽出</button></div>
          {rotationOcrCandidates.length > 0 && <div className=\"catalog-list\">{rotationOcrCandidates.map(candidate => <div className=\"catalog-item rotation-ocr-candidate\" key={candidate.date}><span className=\"rotation-list-name\"><strong>{candidate.date}（{candidate.maps.length}/4件）</strong><small>{candidate.maps.join(' ／ ') || 'マップ名を認識できませんでした'}</small></span>{candidate.maps.length === 4 ? <button className=\"primary-button\" onClick={() => registerOcrCandidate(candidate)}>この日を登録</button> : <small className=\"small-note\">不足分は手動入力してください</small>}</div>)}</div>}
          <p className=\"small-note\">OCRはこのブラウザ内で画像を処理します。初回は日本語の認識データを外部配信元から読み込むため、通信が必要です。画像の文字が誤認識されることがあるので、候補を確認してから登録してください。</p>
        </div>
        <div className=\"content-card\">
          <div className=\"section-heading\"><div><h3>ヒーロー管理</h3><p>名前とロールを追加できます。削除は試合記録で未使用の場合のみ可能です。</p></div></div>"""
replace_once(settings_anchor, settings_insert, "settings rank + rotation UI")

# 13) Show canonical names only in the selectable hero list. Alias matching remains in heroMatchesSearch().
replace_once(
    "          <span>{hero.name}</span>{hero.aliases?.length ? <small>{hero.aliases.join('、')}</small> : null}\n",
    "          <span>{hero.name}</span>\n",
    "hide hero aliases in dropdown choices",
)

if source == original:
    raise SystemExit("変更点がありませんでした。")

backup = APP.with_suffix(APP.suffix + ".before-rotations.bak")
if backup.exists():
    raise SystemExit(f"バックアップが既に存在します: {backup.name}。内容を確認してから再実行してください。")
shutil.copy2(APP, backup)
APP.write_text(source, encoding="utf-8")
print("App.tsx を更新しました。")
print(f"変更前バックアップ: {backup.name}")
print("次に npm install tesseract.js と npm run build を実行してください。")
