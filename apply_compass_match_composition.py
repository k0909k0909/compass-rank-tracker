#!/usr/bin/env python3
"""Apply the match-mode, team-composition, and rank-display improvements.

Run from the root of the compass-rank-tracker repository:
    python3 apply_compass_match_composition.py
    npm run build

The script edits only src/App.tsx, src/style-improvements.css, and src/theme.css.
It makes timestamped backups before writing and refuses to write if an expected
source section does not match, so a partial patch is not left behind.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys

ROOT = Path.cwd()
APP = ROOT / "src" / "App.tsx"
IMPROVEMENTS = ROOT / "src" / "style-improvements.css"
THEME = ROOT / "src" / "theme.css"

for required in (APP, IMPROVEMENTS, THEME):
    if not required.is_file():
        print(f"エラー: {required.relative_to(ROOT) if required.is_relative_to(ROOT) else required} が見つかりません。リポジトリ直下で実行してください。", file=sys.stderr)
        sys.exit(1)

app = APP.read_text(encoding="utf-8")
extra_css = IMPROVEMENTS.read_text(encoding="utf-8")
theme_css = THEME.read_text(encoding="utf-8")
marker = "/* COMPASS MATCH COMPOSITION IMPROVEMENTS v1 */"
if marker in extra_css or "COMPASS MATCH COMPOSITION THEME v1" in theme_css:
    print("この改善はすでに適用済みのようです。ファイルは変更していません。")
    sys.exit(0)

changes: list[str] = []
def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"適用できません: {label} の元コードが1か所ではありません（{count}か所）。ファイルはまだ書き換えていません。")
    changes.append(label)
    return source.replace(old, new, 1)

try:
    # Types and non-breaking additions to older saved match records.
    app = replace_once(app,
        "type Mode = 'バトアリ' | 'フリバ'",
        "type Mode = 'バトアリ' | 'フリバ' | 'カスタム'",
        "モード型にカスタムを追加")
    app = replace_once(app,
        "  heroName: string\n  heroRole: Role\n  mapName: string",
        "  heroName: string\n  heroRole: Role\n  /** 任意のチーム構成。旧記録では未設定 */\n  enemyHeroNames?: string[]\n  allyHeroNames?: string[]\n  mapName: string",
        "試合データに敵味方構成を追加")

    # Icons, slide state, team composition state. The first hero defaults to the
    # latest recorded hero; all existing filter handlers already clear it.
    app = replace_once(app,
        "import { Activity, BarChart3, CalendarDays, Download, FileUp, Gauge, History, Minus, Pencil, Plus, Search, Settings, Shield, Star, Sun, Moon, Swords, Trash2, Trophy, X } from 'lucide-react'",
        "import { Activity, BarChart3, CalendarDays, Download, FileUp, Gauge, History, Lock, Minus, Pencil, Plus, Search, Settings, Shield, Star, Sun, Moon, Swords, Trash2, Trophy, Unlock, X } from 'lucide-react'",
        "ロックアイコンを追加")
    app = replace_once(app,
        "  const [favoritesOnly, setFavoritesOnly] = useState(false)\n  const importRef = useRef<HTMLInputElement>(null)\n  const heroSelectRef = useRef<HTMLSelectElement>(null)\n  const [form, setForm] = useState({\n    playedAt: nowLocalInput(), seasonEnabled: false, seasonLabel: store.activeSeason ?? seasonLabelFromDate(nowLocalInput()), mode: (store.lastMode ?? 'バトアリ') as Mode,\n    heroName: '', mapName: store.maps[0] ?? '', result: 'win' as Result,\n    rankDirection: 'plus' as 'plus' | 'minus', rankDelta: '0', memo: ''\n  })",
        "  const [favoritesOnly, setFavoritesOnly] = useState(false)\n  const [recordSlide, setRecordSlide] = useState<1 | 2>(1)\n  const [lockAllies, setLockAllies] = useState(false)\n  const slideTouchStartX = useRef<number | null>(null)\n  const importRef = useRef<HTMLInputElement>(null)\n  const heroSelectRef = useRef<HTMLSelectElement>(null)\n  const [form, setForm] = useState({\n    playedAt: nowLocalInput(), seasonEnabled: false, seasonLabel: store.activeSeason ?? seasonLabelFromDate(nowLocalInput()), mode: (store.lastMode ?? 'バトアリ') as Mode,\n    heroName: [...store.matches].sort((a, b) => b.playedAt.localeCompare(a.playedAt))[0]?.heroName ?? '', mapName: store.maps[0] ?? '', result: 'win' as Result,\n    rankDirection: 'plus' as 'plus' | 'minus', rankDelta: '0', memo: '',\n    enemyHeroNames: ['', '', ''], allyHeroNames: ['', '']\n  })",
        "記録フォームにチーム構成・スライド状態を追加")

    # Mode selection: season/rank logic is Battle Arena only. Custom matches are
    # saved normally, but do not change rank points.
    app = replace_once(app,
        "{(['バトアリ', 'フリバ'] as Mode[]).map(mode => <button type=\"button\" key={mode} className={`result-choice ${form.mode === mode ? 'selected win' : ''}`} onClick={() => setForm(old => ({ ...old, mode, seasonEnabled: mode === 'フリバ' ? false : old.seasonEnabled }))}>{mode}</button>)}",
        "{(['バトアリ', 'フリバ', 'カスタム'] as Mode[]).map(mode => <button type=\"button\" key={mode} className={`result-choice ${form.mode === mode ? 'selected win' : ''}`} onClick={() => setForm(old => ({ ...old, mode, seasonEnabled: mode !== 'バトアリ' ? false : old.seasonEnabled }))}>{mode}</button>)}",
        "対戦モードにカスタムを追加")
    app = replace_once(app,
        "<label className={`season-check ${form.mode === 'フリバ' ? 'season-disabled' : ''}`}><input type=\"checkbox\" disabled={form.mode === 'フリバ'} checked={form.mode === 'バトアリ' && form.seasonEnabled}",
        "<label className={`season-check ${form.mode !== 'バトアリ' ? 'season-disabled' : ''}`}><input type=\"checkbox\" disabled={form.mode !== 'バトアリ'} checked={form.mode === 'バトアリ' && form.seasonEnabled}",
        "シーズン入力をバトアリ限定に")
    app = replace_once(app,
        "<small className=\"small-note\">500pt到達で昇格し、ポイントが残っている間の減少は0ptで止まります。0ptで減少した場合のみ降格します。</small>\n            ",
        "",
        "ランクポイントの説明文を削除")
    app = replace_once(app,
        "<strong>フリバではランクポイントは変動しません。</strong><span>現在のランクは記録・確認のみ行います。</span>",
        "<strong>{form.mode}ではランクポイントは変動しません。</strong><span>現在のランクは記録・確認のみ行います。</span>",
        "フリバ・カスタムのランク注記を調整")
    app = replace_once(app,
        "<option value=\"フリバ\">フリバ</option></select>",
        "<option value=\"フリバ\">フリバ</option><option value=\"カスタム\">カスタム</option></select>",
        "戦績一覧のモード絞込みにカスタムを追加")

    # Correct the label without doubling the suffix if already correct.
    if "今月はリセット済み" not in app:
        app = replace_once(app, "今月はリセット済", "今月はリセット済み", "リセット済み表記を修正")

    # Make current rank and season read as one stronger primary statistic.
    app = replace_once(app,
        "<StatCard icon={<BarChart3 size={19}/>} label=\"現在のランク\" value={`S${currentRankState.tier}`} sub={`${currentRankState.points} pt · ${store.activeSeason ?? 'シーズン未設定'}`} />",
        "<div className=\"stat-card current-rank-stat-card\"><div className=\"stat-top\"><span>現在のランク</span><span className=\"stat-icon\"><BarChart3 size={19}/></span></div><strong>{`S${currentRankState.tier} · ${currentRankState.points}pt`}</strong><small>{store.activeSeason ?? 'シーズン未設定'}</small></div>",
        "ホームのランク・ポイント表示を強調")

    # Keep the previous hero selected on a fresh form, while retaining the
    # already implemented behavior that resets to '—' on filters/search.
    app = replace_once(app,
        "setForm({ playedAt: nowLocalInput(), seasonEnabled: false, seasonLabel: store.activeSeason ?? seasonLabelFromDate(nowLocalInput()), mode: store.lastMode ?? 'バトアリ', heroName: '', mapName: store.maps[0] ?? '', result: 'win', rankDirection: 'plus', rankDelta: '0', memo: '' })\n    setRankTierDraft",
        "setRecordSlide(1)\n    setForm({ playedAt: nowLocalInput(), seasonEnabled: false, seasonLabel: store.activeSeason ?? seasonLabelFromDate(nowLocalInput()), mode: store.lastMode ?? 'バトアリ', heroName: sortedMatches[0]?.heroName ?? '', mapName: store.maps[0] ?? '', result: 'win', rankDirection: 'plus', rankDelta: '0', memo: '', enemyHeroNames: ['', '', ''], allyHeroNames: lockAllies ? form.allyHeroNames : ['', ''] })\n    setRankTierDraft",
        "新規記録で前回ヒーローを初期選択")
    app = replace_once(app,
        "function beginEditMatch(match: Match) {\n    setEditingId(match.id)",
        "function beginEditMatch(match: Match) {\n    setRecordSlide(1)\n    setEditingId(match.id)",
        "編集画面を1ページ目から開く")
    app = replace_once(app,
        "mode: match.mode ?? 'バトアリ', heroName: match.heroName, mapName: match.mapName, result: match.result, rankDirection: (match.rankChange ?? (match.result === 'loss' ? -1 : 1)) < 0 ? 'minus' : 'plus', rankDelta: String(Math.abs(match.rankChange ?? 0)), memo: match.memo ?? '' })",
        "mode: match.mode ?? 'バトアリ', heroName: match.heroName, mapName: match.mapName, result: match.result, rankDirection: (match.rankChange ?? (match.result === 'loss' ? -1 : 1)) < 0 ? 'minus' : 'plus', rankDelta: String(Math.abs(match.rankChange ?? 0)), memo: match.memo ?? '', enemyHeroNames: [...(match.enemyHeroNames ?? []), '', '', ''].slice(0, 3), allyHeroNames: [...(match.allyHeroNames ?? []), '', ''].slice(0, 2) })",
        "既存記録のチーム構成を編集フォームへ読み込み")

    # Helper for setting an individual ally/enemy slot.
    app = replace_once(app,
        "  function notify(message: string) { setToast(message); window.setTimeout(() => setToast(''), 2600) }",
        "  function setTeamHero(side: 'enemyHeroNames' | 'allyHeroNames', index: number, name: string) {\n    setForm(old => {\n      const names = [...old[side]]\n      names[index] = name\n      return { ...old, [side]: names }\n    })\n  }\n\n  function notify(message: string) { setToast(message); window.setTimeout(() => setToast(''), 2600) }",
        "チーム構成の入力ハンドラーを追加")

    # Save optional team fields in each match. Missing arrays in legacy records
    # remain valid because these properties are optional.
    app = replace_once(app,
        "heroName: hero.name, heroRole: hero.role, mapName: form.mapName, result: form.result,\n      rankPoints: rankStateToTotal(rankAfter), rankChange: requestedChange, mode: form.mode, memo: form.memo.trim(),",
        "heroName: hero.name, heroRole: hero.role, mapName: form.mapName, result: form.result,\n      enemyHeroNames: form.enemyHeroNames.filter(Boolean), allyHeroNames: form.allyHeroNames.filter(Boolean),\n      rankPoints: rankStateToTotal(rankAfter), rankChange: requestedChange, mode: form.mode, memo: form.memo.trim(),",
        "敵味方構成を試合データへ保存")
    app = replace_once(app,
        "    const wasEditing = editingId !== null\n    setEditingId(null)",
        "    const wasEditing = editingId !== null\n    setRecordSlide(1)\n    setEditingId(null)",
        "保存後にスライドをリセット")
    app = replace_once(app,
        "setForm(old => ({ playedAt: nextDate, seasonEnabled: old.mode === 'バトアリ' ? old.seasonEnabled : false,\n        seasonLabel: storeRef.current.activeSeason ?? seasonLabelFromDate(nextDate), mode: old.mode, heroName: '',\n        mapName: old.mapName || storeRef.current.maps[0] || '', result: 'win', rankDirection: 'plus', rankDelta: '0', memo: '' }))",
        "setForm(old => ({ playedAt: nextDate, seasonEnabled: old.mode === 'バトアリ' ? old.seasonEnabled : false,\n        seasonLabel: storeRef.current.activeSeason ?? seasonLabelFromDate(nextDate), mode: old.mode, heroName: hero.name,\n        mapName: old.mapName || storeRef.current.maps[0] || '', result: 'win', rankDirection: 'plus', rankDelta: '0', memo: '', enemyHeroNames: ['', '', ''], allyHeroNames: lockAllies ? old.allyHeroNames : ['', ''] }))",
        "連続記録時に前回ヒーローを維持し味方ロックに対応")
    app = replace_once(app,
        "'フリバの試合を記録しました。次の試合を入力できます'",
        "`${form.mode}の試合を記録しました。次の試合を入力できます`",
        "カスタムモードの保存完了メッセージを修正")

    # Turn the existing form into two horizontal slides. The first retains all
    # match/rank inputs; page 2 has optional team slots, memo, and save actions.
    app = replace_once(app,
        "        <form onSubmit={saveMatch} className=\"match-form\">\n          {editingId && <div className=\"field field-wide\"><label>試合日時（分まで）</label><input type=\"datetime-local\" required value={form.playedAt} onChange={e => setForm({ ...form, playedAt: e.target.value })}/></div>}",
        "        <form onSubmit={saveMatch} className=\"match-form\" onTouchStart={e => { slideTouchStartX.current = e.touches[0]?.clientX ?? null }} onTouchEnd={e => { const startX = slideTouchStartX.current; slideTouchStartX.current = null; if (startX == null) return; const delta = (e.changedTouches[0]?.clientX ?? startX) - startX; if (delta < -55) setRecordSlide(2); else if (delta > 55) setRecordSlide(1) }}>\n          <div className=\"match-slide-viewport\"><div className={`match-slide-track ${recordSlide === 2 ? 'show-team-page' : ''}`}><div className=\"match-slide match-slide-primary\">\n          {editingId && <div className=\"field field-wide\"><label>試合日時（分まで）</label><input type=\"datetime-local\" required={recordSlide === 1} value={form.playedAt} onChange={e => setForm({ ...form, playedAt: e.target.value })}/></div>}",
        "記録フォームに左右スワイプする2ページ構造を追加")

    # The native required check must not try to focus controls in the
    # off-screen first slide when the user submits from slide two.
    app = replace_once(app,
        "<select ref={heroSelectRef} className=\"hero-select\" required value={form.heroName}",
        "<select ref={heroSelectRef} className=\"hero-select\" required={recordSlide === 1} value={form.heroName}",
        "スライド外の必須選択で保存を妨げないようにする")
    app = replace_once(app,
        "<select required value={form.mapName}",
        "<select required={recordSlide === 1} value={form.mapName}",
        "スライド外のマップ必須選択で保存を妨げないようにする")

    form_tail_old = '''          <div className="field field-wide"><label>メモ <small>任意</small></label><textarea rows={3} placeholder="味方編成、反省点、気づいたことなど" value={form.memo} onChange={e => setForm({ ...form, memo: e.target.value })}/></div>
          <div className="form-actions"><button type="button" className="secondary-button" onClick={() => { setEditingId(null); setPage('dashboard') }}>キャンセル</button><button type="submit" className="primary-button">{editingId ? <><Pencil size={17}/> 変更を保存</> : <><Plus size={17}/> 記録を保存して次へ</>}</button></div>
        </form>'''
    form_tail_new = '''          <div className="record-slide-nav" aria-label="記録ページの移動">
            <div className="record-slide-steps"><span className="record-slide-step active">1 基本情報</span><span className="record-slide-step">2 チーム構成</span></div>
            <button type="button" className="secondary-button" onClick={() => setRecordSlide(2)}>次へ：チーム構成 →</button>
          </div>
          </div><div className="match-slide match-slide-teams">
          <div className="record-slide-nav team-page-nav" aria-label="記録ページの移動">
            <button type="button" className="secondary-button" onClick={() => setRecordSlide(1)}>← 基本情報へ戻る</button>
            <span className="record-slide-step active">2 チーム構成</span>
          </div>
          <div className="team-page-heading"><h4>チーム構成</h4><p>敵チーム3人、味方チームは自分以外の2人を任意で記録できます。横にスワイプしてページを移動できます。</p></div>
          <div className="team-composition-grid">
            <section className="team-composition-side">
              <h4>敵チーム <small>任意・最大3人</small></h4>
              <div className="team-select-list">
                {Array.from({ length: 3 }, (_, index) => <label key={`enemy-${index}`}><span>敵 {index + 1}</span><select value={form.enemyHeroNames[index] ?? ''} onChange={e => setTeamHero('enemyHeroNames', index, e.target.value)}><option value="">— 未選択 —</option>{store.heroes.map(hero => <option key={hero.name} value={hero.name}>{hero.name}</option>)}</select></label>)}
              </div>
            </section>
            <section className="team-composition-side">
              <div className="team-side-header"><h4>味方チーム <small>自分以外の2人</small></h4><button type="button" className={`ally-lock-toggle ${lockAllies ? 'locked' : ''}`} aria-label={lockAllies ? '味方ヒーローの固定を解除' : '味方ヒーローを固定'} aria-pressed={lockAllies} title={lockAllies ? '固定中：記録後も味方ヒーローを保持' : '固定すると記録後も味方ヒーローを保持'} onClick={() => setLockAllies(value => !value)}>{lockAllies ? <Lock size={16}/> : <Unlock size={16}/>}<span>{lockAllies ? '固定中' : '固定'}</span></button></div>
              <div className="team-select-list">
                {Array.from({ length: 2 }, (_, index) => <label key={`ally-${index}`}><span>味方 {index + 1}</span><select value={form.allyHeroNames[index] ?? ''} onChange={e => setTeamHero('allyHeroNames', index, e.target.value)}><option value="">— 未選択 —</option>{store.heroes.map(hero => <option key={hero.name} value={hero.name}>{hero.name}</option>)}</select></label>)}
              </div>
              <p className="team-lock-help">{lockAllies ? '固定中：記録後もこの2人の選択を保持します。' : '固定はオフです。記録後に味方の選択をリセットします。'}</p>
            </section>
          </div>
          <div className="field field-wide"><label>メモ <small>任意</small></label><textarea rows={3} placeholder="味方編成、反省点、気づいたことなど" value={form.memo} onChange={e => setForm({ ...form, memo: e.target.value })}/></div>
          <div className="form-actions"><button type="button" className="secondary-button" onClick={() => { setEditingId(null); setRecordSlide(1); setPage('dashboard') }}>キャンセル</button><button type="submit" className="primary-button">{editingId ? <><Pencil size={17}/> 変更を保存</> : <><Plus size={17}/> 記録を保存して次へ</>}</button></div>
          </div></div>
        </form>'''
    app = replace_once(app, form_tail_old, form_tail_new, "チーム構成2ページ目と味方固定ボタンを追加")

except RuntimeError as exc:
    print(str(exc), file=sys.stderr)
    sys.exit(2)

css_addition = r'''\n\n/* COMPASS MATCH COMPOSITION IMPROVEMENTS v1 */
.match-form { display: block; }
.mode-selection-column .mode-options { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.match-slide-viewport { width: 100%; overflow: hidden; touch-action: pan-y; }
.match-slide-track { display: flex; align-items: flex-start; width: 200%; transition: transform .3s cubic-bezier(.2,.8,.2,1); }
.match-slide-track.show-team-page { transform: translateX(-50%); }
.match-slide { flex: 0 0 50%; width: 50%; min-width: 0; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); align-content: start; gap: 18px 16px; padding: 2px 1px; }
.match-slide > .field-wide, .match-slide > .record-slide-nav, .match-slide > .team-page-heading, .match-slide > .team-composition-grid { grid-column: 1 / -1; }
.record-slide-nav { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; border-top: 1px solid var(--line, #303951); padding-top: 15px; margin-top: 4px; }
.record-slide-steps { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.record-slide-step { display: inline-flex; align-items: center; min-height: 29px; padding: 6px 10px; border-radius: 8px; background: var(--surface-muted, #0b1320); color: var(--text-muted, #829aa8); font-size: 10px; font-weight: 700; }
.record-slide-step.active { color: var(--accent-strong, #009bad); background: var(--accent-soft, #def8fa); }
.team-page-nav { border-top: 0; padding-top: 0; margin-bottom: 2px; }
.team-page-heading h4 { margin: 0 0 5px; font-size: 15px; color: var(--text-main, inherit); }
.team-page-heading p { margin: 0; color: var(--text-muted, #829aa8); font-size: 11px; line-height: 1.7; }
.team-composition-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.team-composition-side { min-width: 0; padding: 14px; border: 1px solid var(--line, #303951); background: var(--surface, #101725); border-radius: 12px; }
.team-composition-side h4 { margin: 0; color: var(--text-main, inherit); font-size: 12px; display: flex; align-items: center; flex-wrap: wrap; gap: 7px; }
.team-composition-side h4 small { color: var(--text-muted, #829aa8); font-size: 10px; font-weight: 500; }
.team-side-header { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 12px; }
.team-select-list { display: grid; gap: 10px; }
.team-select-list label { display: grid; grid-template-columns: 48px minmax(0, 1fr); align-items: center; gap: 8px; min-width: 0; color: var(--text-soft, #b5cbd5); font-size: 11px; }
.team-select-list select { min-width: 0; width: 100%; }
.ally-lock-toggle { display: inline-flex; align-items: center; justify-content: center; gap: 6px; flex: 0 0 auto; border: 1px solid var(--line, #293c4b); border-radius: 9px; background: var(--surface-raised, #141f30); color: var(--text-soft, #b5cbd5); padding: 7px 9px; font-size: 10px; font-weight: 800; }
.ally-lock-toggle svg { width: 15px; height: 15px; }
.ally-lock-toggle.locked { color: var(--accent-strong, #04bfd0); background: var(--accent-soft, #10313a); border-color: var(--accent-line, #24616c); }
.team-lock-help { margin: 10px 0 0; color: var(--text-muted, #829aa8); font-size: 10px; line-height: 1.6; }
.current-rank-stat-card > strong { font-size: clamp(18px, 2.3vw, 27px) !important; line-height: 1.35; letter-spacing: -.035em; white-space: nowrap; }
.current-rank-stat-card > small { display: block; margin-top: 5px; font-size: 10px; }
@media (max-width: 700px) {
  .match-slide { grid-template-columns: minmax(0, 1fr); gap: 15px; }
  .team-composition-grid { grid-template-columns: minmax(0, 1fr); }
  .record-slide-nav { align-items: stretch; }
  .record-slide-nav > .secondary-button { flex: 1 1 auto; }
  .record-slide-steps { width: 100%; }
  .current-rank-stat-card > strong { font-size: clamp(18px, 5vw, 24px) !important; }
}
'''.replace('\\n','\n')

theme_addition = r'''\n\n/* COMPASS MATCH COMPOSITION THEME v1: improve checkbox contrast in light mode */
html[data-theme="light"] .season-check {
  color: #213640;
  background: #ffffff;
  border-color: #9ab7c0;
  box-shadow: 0 2px 8px rgba(25, 87, 103, .08);
}
html[data-theme="light"] .season-check span { color: #213640; }
html[data-theme="light"] .season-check small { color: #536e78; }
html[data-theme="light"] .season-check input { accent-color: #007f90; outline-offset: 2px; }
html[data-theme="light"] .season-check:focus-within { border-color: #007f90; box-shadow: 0 0 0 3px rgba(0, 184, 202, .16); }
html[data-theme="light"] .season-check.season-disabled { background: #eaf1f3; }
'''.replace('\\n','\n')
extra_css += css_addition
theme_css += theme_addition

# Sanity checks before writing: these ensure all requested feature hooks exist.
for text_fragment, label in [
    ("enemyHeroNames: form.enemyHeroNames.filter(Boolean)", "敵構成保存"),
    ("allyHeroNames: lockAllies ? old.allyHeroNames : ['', '']", "味方固定"),
    ("recordSlide === 2 ? 'show-team-page' : ''", "2ページ切替"),
    ("<option value=\"カスタム\">カスタム</option>", "カスタム選択"),
    ("current-rank-stat-card", "ホームのランク表示"),
]:
    if text_fragment not in app:
        raise SystemExit(f"内部確認に失敗しました: {label}。ファイルはまだ書き換えていません。")

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup_dir = ROOT / f".compass-match-backup-{stamp}"
backup_dir.mkdir()
for f in (APP, IMPROVEMENTS, THEME):
    shutil.copy2(f, backup_dir / f.name)
APP.write_text(app, encoding="utf-8")
IMPROVEMENTS.write_text(extra_css, encoding="utf-8")
THEME.write_text(theme_css, encoding="utf-8")
print("改善を適用しました。")
print("変更内容:")
for change in changes:
    print(f"  - {change}")
print(f"バックアップ: {backup_dir.relative_to(ROOT)}")
print("次に npm run build と git diff --check を実行してください。")
