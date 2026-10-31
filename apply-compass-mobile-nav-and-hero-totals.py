#!/usr/bin/env python3
"""Apply mobile navigation scrolling and absolute hero-total editing to the app."""
from __future__ import annotations

from pathlib import Path
import shutil
import sys

ROOT = Path.cwd()
APP = ROOT / "src" / "App.tsx"
CSS_MAIN = ROOT / "src" / "style.css"
CSS_EXTRA = ROOT / "src" / "style-improvements.css"
BACKUPS = {
    APP: ROOT / "src" / "App.tsx.before-mobile-nav-and-hero-totals.bak",
    CSS_MAIN: ROOT / "src" / "style.css.before-mobile-nav-and-hero-totals.bak",
    CSS_EXTRA: ROOT / "src" / "style-improvements.css.before-mobile-nav-and-hero-totals.bak",
}


def require_once(source: str, text: str, label: str) -> None:
    count = source.count(text)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}. No source files were changed.")


def main() -> int:
    missing = [str(path.relative_to(ROOT)) for path in (APP, CSS_MAIN, CSS_EXTRA) if not path.is_file()]
    if missing:
        print("必要なファイルが見つかりません: " + ", ".join(missing))
        print("package.json があるリポジトリ直下で実行してください。")
        return 1

    app = APP.read_text(encoding="utf-8")
    css_main = CSS_MAIN.read_text(encoding="utf-8")
    css_extra = CSS_EXTRA.read_text(encoding="utf-8")

    if "hero-total-edit-v2" in app and "mobile-bottom-nav-scroll-v2" in css_main and "hero-total-edit-v2" in css_extra:
        print("今回の修正はすでに適用されています。変更はありません。")
        return 0

    # Remove the previous draft-only editor state.
    draft_state = "  const [heroBaseDrafts, setHeroBaseDrafts] = useState<Record<string, { battles: string; wins: string }>>({})\n"
    require_once(app, draft_state, "heroBaseDrafts state")
    app = app.replace(draft_state, "", 1)

    # Replace the previous base-only data editor with an absolute-total editor.
    function_start = "  function updateHeroBaseDraft(name: string, field: 'battles' | 'wins', value: string) {\n"
    function_end = "  function openHeroDetail(name: string) {\n"
    if app.count(function_start) != 1 or app.count(function_end) != 1:
        raise RuntimeError("Hero editor function anchors were not unique. No source files were changed.")
    start = app.index(function_start)
    end = app.index(function_end, start)
    functions = '''  // 入力値は過去分ではなく、アプリ内の記録を含めた現在の合計値です。
  // 保存時にアプリ内記録分を差し引き、差分を heroBaseStats に補正値として保存します。
  // heroBaseStats は既存バックアップとの互換性を保ったまま、正負の補正値を保持します。
  // hero-total-edit-v2
  function editHeroTotalStats(name: string) {
    const summary = heroSummaryRows.find(hero => hero.name === name)
    if (!summary) return
    const battlesText = window.prompt(`${name} の合計試合数を入力してください`, String(summary.totalBattles))
    if (battlesText === null) return
    const winsText = window.prompt(`${name} の合計勝ち数を入力してください`, String(summary.totalWins))
    if (winsText === null) return
    if (!battlesText.trim() || !winsText.trim()) {
      notify('試合数と勝ち数を入力してください')
      return
    }
    const totalBattles = Number(battlesText)
    const totalWins = Number(winsText)
    if (!Number.isSafeInteger(totalBattles) || totalBattles < 0
      || !Number.isSafeInteger(totalWins) || totalWins < 0 || totalWins > totalBattles) {
      notify('試合数・勝ち数は0以上の整数で、勝ち数は試合数以下にしてください')
      return
    }
    const recorded = storeRef.current.matches.filter(match => match.heroName === name)
    const recordedWins = recorded.filter(match => match.result === 'win').length
    const heroBaseStats = { ...(storeRef.current.heroBaseStats ?? {}) }
    const adjustment = { battles: totalBattles - recorded.length, wins: totalWins - recordedWins }
    if (adjustment.battles === 0 && adjustment.wins === 0) delete heroBaseStats[name]
    else heroBaseStats[name] = adjustment
    const updated: Store = { ...storeRef.current, heroBaseStats }
    storeRef.current = updated
    setStore(updated)
    notify(`${name} の合計成績を修正しました`)
  }
'''
    app = app[:start] + functions + app[end:]

    # Replace the hero summary page, keeping the existing detailed breakdown page untouched.
    page_start_marker = "      {page === 'heroStats' && <section className=\"page-stack hero-log-page\">\n"
    page_end_marker = "      {page === 'heroDetail' && <section className=\"page-stack hero-log-page\">\n"
    if app.count(page_start_marker) != 1 or app.count(page_end_marker) != 1:
        raise RuntimeError("Hero summary page anchors were not unique. No source files were changed.")
    page_start = app.index(page_start_marker)
    page_end = app.index(page_end_marker, page_start)
    page = '''      {page === 'heroStats' && <section className="page-stack hero-log-page">
        <div className="content-card">
          <div className="section-heading"><div><h3>ヒーロー別の合計成績</h3><p>アプリ内の試合記録を含めた現在の合計です。</p></div><div className="round-icon"><Trophy size={20}/></div></div>
          <div className="table-wrap hero-log-table-wrap"><table className="hero-log-table hero-log-main-table"><thead><tr><th>ヒーロー</th><th>試合数</th><th>勝ち数</th><th>勝率</th><th>操作</th></tr></thead><tbody>
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
          </tbody></table></div>
        </div>
      </section>}

'''
    app = app[:page_start] + page + app[page_end:]

    # Mobile navigation lives in src/style.css, not style-improvements.css.
    old_nav = ".sidebar nav{height:100%;display:grid;grid-template-columns:repeat(4,1fr);gap:2px}"
    new_nav = ".sidebar nav{height:100%;width:100%;display:flex;gap:2px;overflow-x:auto;overflow-y:hidden;overscroll-behavior-x:contain;-webkit-overflow-scrolling:touch;scrollbar-width:none}.sidebar nav::-webkit-scrollbar{display:none}"
    require_once(css_main, old_nav, "mobile sidebar navigation rule")
    css_main = css_main.replace(old_nav, new_nav, 1)

    old_item = ".nav-item{flex-direction:column;justify-content:center;gap:4px;padding:4px 2px;border-radius:7px;font-size:9px}"
    new_item = ".nav-item{flex:0 0 76px;min-width:76px;flex-direction:column;justify-content:center;gap:4px;padding:4px 2px;border-radius:7px;font-size:9px}"
    require_once(css_main, old_item, "mobile navigation item rule")
    css_main = css_main.replace(old_item, new_item, 1)

    old_shell = ".app-shell{display:block;padding-bottom:66px}"
    new_shell = ".app-shell{display:block;padding-bottom:calc(72px + env(safe-area-inset-bottom))}"
    require_once(css_main, old_shell, "mobile app-shell bottom padding")
    css_main = css_main.replace(old_shell, new_shell, 1)

    if "/* mobile-bottom-nav-scroll-v2 */" not in css_main:
        css_main += '''

/* mobile-bottom-nav-scroll-v2 */
@media (max-width: 700px) {
  .sidebar nav { justify-content: flex-start; }
  .sidebar nav .nav-item { flex: 0 0 76px; }
}
'''

    if "/* hero-total-edit-v2 */" not in css_extra:
        css_extra += '''

/* hero-total-edit-v2 */
.hero-log-edit-button {
  width: 34px;
  height: 34px;
  flex: 0 0 34px;
  border: 1px solid var(--line, #293c4b);
  background: var(--surface-muted, #0b1320);
  color: var(--text-soft, #b5cbd5);
}
.hero-log-edit-button:hover {
  color: var(--accent-strong, #04bfd0);
  background: var(--accent-soft, #10313a);
  border-color: var(--accent-line, #24616c);
}
.hero-log-detail-button { min-width: 58px; }
'''

    # Back up all three files before writing. Never overwrite an existing backup.
    for original, backup in BACKUPS.items():
        if not backup.exists():
            shutil.copy2(original, backup)

    APP.write_text(app, encoding="utf-8")
    CSS_MAIN.write_text(css_main, encoding="utf-8")
    CSS_EXTRA.write_text(css_extra, encoding="utf-8")

    print("修正を適用しました。")
    print("変更ファイル: src/App.tsx、src/style.css、src/style-improvements.css")
    for backup in BACKUPS.values():
        print(f"バックアップ: {backup.relative_to(ROOT)}")
    print("次に npm run build を実行してください。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        raise SystemExit(1)
