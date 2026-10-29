#!/usr/bin/env python3
"""Apply follow-up fixes to the COMPASS match recording form.

Run from the repository root:
    python3 apply_compass_match_followup.py
    npm run build

Only src/App.tsx and src/theme.css are edited. Timestamped backups are made.
"""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
import shutil
import sys

ROOT = Path.cwd()
APP = ROOT / "src" / "App.tsx"
THEME = ROOT / "src" / "theme.css"
for p in (APP, THEME):
    if not p.is_file():
        sys.exit(f"エラー: {p} が見つかりません。リポジトリ直下で実行してください。")

app = APP.read_text(encoding="utf-8")
theme = THEME.read_text(encoding="utf-8")
marker = "/* COMPASS MATCH FOLLOW-UP v1 */"
if marker in app or marker in theme:
    sys.exit("この改善はすでに適用済みです。ファイルは変更していません。")

changes: list[str] = []
def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"適用を中止しました: {label} の元コードが1か所ではありません（{count}か所）。ファイルは変更していません。")
    changes.append(label)
    return source.replace(old, new, 1)

def remove_between(source: str, start: str, end: str, label: str) -> str:
    if source.count(start) != 1 or source.count(end) != 1:
        raise RuntimeError(f"適用を中止しました: {label} の範囲を一意に特定できません。ファイルは変更していません。")
    a = source.index(start)
    b = source.index(end, a)
    if b <= a:
        raise RuntimeError(f"適用を中止しました: {label} の範囲が不正です。ファイルは変更していません。")
    changes.append(label)
    return source[:a] + source[b:]

try:
    # Independent lock state per teammate.
    app = replace_once(app,
        "  const [lockAllies, setLockAllies] = useState(false)",
        "  const [lockAlly1, setLockAlly1] = useState(false)\n  const [lockAlly2, setLockAlly2] = useState(false)",
        "味方1・味方2のロック状態を分離")

    # Team hero choices use the same implementation order as the user's hero picker.
    app = replace_once(app,
        "  const selectedHero = store.heroes.find(hero => hero.name === form.heroName)",
        "  const selectedHero = store.heroes.find(hero => hero.name === form.heroName)\n  const teamHeroOptions = useMemo(() => [...store.heroes].sort((a, b) =>\n    (heroOrderIndex.get(a.name) ?? Number.MAX_SAFE_INTEGER) - (heroOrderIndex.get(b.name) ?? Number.MAX_SAFE_INTEGER)\n  ), [store.heroes])",
        "敵味方の候補を実装順に並び替え")

    # Top of the record form: remove title and auto-time explanation, show current rank/points here instead.
    app = replace_once(app,
        '<div className="section-heading"><div><h3>{editingId ? \'試合記録を編集\' : \'試合内容を入力\'}</h3><p>{editingId ? \'日時や結果、RPの変動を修正できます。\' : \'日時は保存時に自動で記録します。\'}</p></div><div className="round-icon"><Swords size={20}/></div></div>',
        '<div className="section-heading record-form-heading"><div className="record-current-rank"><span>現在のランク</span><strong>{`S${currentRankState.tier} · ${currentRankState.points}pt`}</strong></div><div className="round-icon"><Swords size={20}/></div></div>',
        "フォーム先頭に現在のランクとポイントを表示")

    # Make the mode selection full-width after removing the rank editor panel.
    app = replace_once(app,
        '<div className="field field-wide mode-rank-layout">',
        '<div className="field field-wide mode-selection-only">',
        "モード選択エリアを再配置")

    rank_panel = '''            <section className="rank-control-panel" aria-label="現在のランク設定">
              <div className="rank-panel-heading"><strong>現在のランク</strong><span>{formatRankState(normalizeRankState(Number(rankTierDraft) || currentRankState.tier, Number(rankPointsDraft) || 0))}</span></div>
              <div className="rank-edit-grid">
                <label>ランク<select aria-label="現在のランク" value={rankTierDraft} onChange={e => setRankTierDraft(e.target.value)}>{Array.from({ length: 9 }, (_, index) => index + 1).map(tier => <option key={tier} value={tier}>S{tier}</option>)}</select></label>
                <label>ポイント<input aria-label="現在のランクポイント" type="number" min="0" max="499" step="1" value={rankPointsDraft} onChange={e => setRankPointsDraft(e.target.value)} /></label>
              </div>
              <button type="button" className="secondary-button rank-save-button" onClick={saveCurrentRank}>ランクを保存</button>
              <div className="season-reset-control">
                {resetConfirmStep ? <>
                  <p>前回シーズンのランクを基準に、開始ランクを <strong>{`S${seasonStartRankFromPreviousTier(Number(rankTierDraft) || currentRankState.tier).tier}・250pt`}</strong> にします。現在の試合入力は保持します。</p>
                  <div className="season-reset-buttons"><button type="button" className="secondary-button" onClick={() => setResetConfirmStep(false)}>キャンセル</button><button type="button" className="danger-button" onClick={performSeasonReset}>リセットを確定</button></div>
                </> : <button type="button" className="season-reset-button" disabled={store.lastSeasonResetMonth === currentMonthKey()} onClick={() => setResetConfirmStep(true)}>{store.lastSeasonResetMonth === currentMonthKey() ? '今月はリセット済み' : 'シーズンリセット'}</button>}
              </div>
            </section>'''
    app = replace_once(app, rank_panel, '', "記録画面からランク編集・リセット操作を削除")

    # These handlers/state were only used by the removed rank editor. Rank calculation continues
    # to use the current stored rank and the existing rank draft values maintained internally.
    app = replace_once(app,
        "  const [resetConfirmStep, setResetConfirmStep] = useState(false)\n",
        "",
        "不要になったリセット確認stateを削除")
    app = remove_between(app, "  function saveCurrentRank() {", "  function saveMatch(e: React.FormEvent) {", "記録画面から削除したランク編集・リセット関数を削除")
    import re
    app, removed = re.subn(r"^\s*setResetConfirmStep\(false\)\s*\n", "", app, flags=re.MULTILINE)
    if removed:
        changes.append("不要なリセット確認state更新を削除")

    # Preserve empty slots in saved arrays, because ally slot 1 and slot 2 have independent locks.
    app = replace_once(app,
        "enemyHeroNames: form.enemyHeroNames.filter(Boolean), allyHeroNames: form.allyHeroNames.filter(Boolean),",
        "enemyHeroNames: [...form.enemyHeroNames], allyHeroNames: [...form.allyHeroNames],",
        "チーム構成をスロット位置を保ったまま保存")

    # Preserve each locked ally slot independently when starting or saving the next match.
    app = replace_once(app,
        "allyHeroNames: lockAllies ? form.allyHeroNames : ['', '']",
        "allyHeroNames: [lockAlly1 ? (form.allyHeroNames[0] ?? '') : '', lockAlly2 ? (form.allyHeroNames[1] ?? '') : '']",
        "新規記録で味方ごとのロック状態を保持")
    app = replace_once(app,
        "allyHeroNames: lockAllies ? old.allyHeroNames : ['', '']",
        "allyHeroNames: [lockAlly1 ? (old.allyHeroNames[0] ?? '') : '', lockAlly2 ? (old.allyHeroNames[1] ?? '') : '']",
        "連続記録で味方1・2を個別に保持")

    # Reorder team columns (allies first, enemies second) and place a separate lock button by each ally.
    old_grid = '''          <div className="team-composition-grid">
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
          </div>'''
    new_grid = '''          <div className="team-composition-grid">
            <section className="team-composition-side">
              <div className="team-side-header"><h4>味方チーム <small>自分以外の2人</small></h4></div>
              <div className="team-select-list ally-select-list">
                {Array.from({ length: 2 }, (_, index) => {
                  const locked = index === 0 ? lockAlly1 : lockAlly2
                  const toggleLock = () => index === 0 ? setLockAlly1(value => !value) : setLockAlly2(value => !value)
                  return <label key={`ally-${index}`}><span>味方 {index + 1}</span><div className="team-select-with-lock"><select value={form.allyHeroNames[index] ?? ''} onChange={e => setTeamHero('allyHeroNames', index, e.target.value)}><option value="">— 未選択 —</option>{teamHeroOptions.map(hero => <option key={hero.name} value={hero.name}>{hero.name}</option>)}</select><button type="button" className={`ally-lock-toggle ally-slot-lock ${locked ? 'locked' : ''}`} aria-label={locked ? `味方${index + 1}の固定を解除` : `味方${index + 1}を固定`} aria-pressed={locked} title={locked ? `味方${index + 1}は固定中` : `味方${index + 1}を固定`} onClick={toggleLock}>{locked ? <Lock size={16}/> : <Unlock size={16}/>}</button></div></label>
                })}
              </div>
              <p className="team-lock-help">{lockAlly1 && lockAlly2 ? '味方1・2を固定中です。' : lockAlly1 ? '味方1を固定中です。味方2は記録後にリセットされます。' : lockAlly2 ? '味方2を固定中です。味方1は記録後にリセットされます。' : 'ロックした味方だけ、記録後も選択を保持します。'}</p>
            </section>
            <section className="team-composition-side">
              <div className="team-side-header"><h4>敵チーム <small>任意・最大3人</small></h4></div>
              <div className="team-select-list">
                {Array.from({ length: 3 }, (_, index) => <label key={`enemy-${index}`}><span>敵 {index + 1}</span><select value={form.enemyHeroNames[index] ?? ''} onChange={e => setTeamHero('enemyHeroNames', index, e.target.value)}><option value="">— 未選択 —</option>{teamHeroOptions.map(hero => <option key={hero.name} value={hero.name}>{hero.name}</option>)}</select></label>)}
              </div>
            </section>
          </div>'''
    app = replace_once(app, old_grid, new_grid, "味方を左・敵を右に配置し、味方ごとのロックを追加")

    # Keep current-rank editing logic for calculations/data compatibility, but not rendered in the record form.
    # Fix high-contrast checkbox sizing: shared theme input rules otherwise make the native checkbox large/dim.
    theme += '''\n\n/* COMPASS MATCH FOLLOW-UP v1 */
html[data-theme="light"] .season-check {
  background: #fff;
  color: #183540;
  border: 1px solid #7da7b2;
  box-shadow: 0 2px 8px rgba(25, 87, 103, .10);
}
html[data-theme="light"] .season-check span { color: #183540; }
html[data-theme="light"] .season-check input[type="checkbox"] {
  appearance: auto !important;
  -webkit-appearance: checkbox !important;
  display: inline-block !important;
  flex: 0 0 18px;
  width: 18px !important;
  height: 18px !important;
  min-width: 18px;
  margin: 0 !important;
  padding: 0 !important;
  border: 2px solid #087f8c !important;
  border-radius: 4px;
  background: #fff !important;
  accent-color: #007f90;
  box-shadow: none !important;
  cursor: pointer;
}
html[data-theme="light"] .season-check input[type="checkbox"]:focus-visible { outline: 3px solid rgba(0, 127, 144, .28); outline-offset: 2px; }
html[data-theme="light"] .season-check input[type="checkbox"]:disabled { opacity: .55; cursor: not-allowed; }
.record-form-heading { min-height: 52px; }
.record-current-rank { display: flex; flex-direction: column; gap: 5px; }
.record-current-rank > span { color: var(--text-muted, #829aa8); font-size: 11px; font-weight: 700; }
.record-current-rank > strong { color: var(--text-main, inherit); font-size: clamp(21px, 2.4vw, 29px); line-height: 1.2; letter-spacing: -.025em; }
.mode-selection-only { width: 100%; max-width: 620px; }
.mode-selection-only .mode-selection-column { width: 100%; }
.mode-selection-only .season-check { align-self: flex-start; }
.team-select-with-lock { display: flex; align-items: stretch; gap: 6px; min-width: 0; }
.team-select-with-lock select { flex: 1 1 auto; min-width: 0; }
.ally-slot-lock { width: 39px; min-width: 39px; padding: 7px !important; }
.ally-slot-lock svg { width: 17px; height: 17px; }
html[data-theme="light"] .ally-slot-lock { background: #fff; color: #3c5963; border-color: #9ab7c0; }
html[data-theme="light"] .ally-slot-lock.locked { background: #def8fa; color: #007f90; border-color: #00a5b7; }
@media (max-width: 700px) {
  .record-current-rank > strong { font-size: 24px; }
  .mode-selection-only { max-width: none; }
}
'''
    # Sanity checks: no old single-lock state should remain, and the JSX structure should still have both team sides.
    for fragment, label in [
        ("const [lockAlly1, setLockAlly1] = useState(false)", "味方1ロック状態"),
        ("const [lockAlly2, setLockAlly2] = useState(false)", "味方2ロック状態"),
        ("teamHeroOptions.map(hero => <option", "実装順の候補"),
        ("record-current-rank", "ランク情報の表示位置"),
        ("ally-slot-lock", "個別ロックのボタン"),
    ]:
        if fragment not in (app + theme):
            raise RuntimeError(f"内部確認に失敗: {label}")
    if "lockAllies" in app:
        raise RuntimeError("旧ロック状態が残っています。ファイルは変更していません。")
except RuntimeError as exc:
    print(str(exc), file=sys.stderr)
    sys.exit(2)

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup_dir = ROOT / f".compass-followup-backup-{stamp}"
backup_dir.mkdir()
shutil.copy2(APP, backup_dir / APP.name)
shutil.copy2(THEME, backup_dir / THEME.name)
APP.write_text(app, encoding="utf-8")
THEME.write_text(theme, encoding="utf-8")
print("追加改善を適用しました。")
for item in changes:
    print(f"  - {item}")
print(f"バックアップ: {backup_dir.relative_to(ROOT)}")
print("次に npm run build と git diff --check を実行してください。")
