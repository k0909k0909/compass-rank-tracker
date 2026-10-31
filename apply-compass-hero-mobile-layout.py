#!/usr/bin/env python3
"""Apply mobile layout and settings-label improvements to compass-rank-tracker."""
from pathlib import Path
import sys

ROOT = Path.cwd()
APP = ROOT / "src" / "App.tsx"
CSS = ROOT / "src" / "style-improvements.css"
APP_BACKUP = ROOT / "src" / "App.tsx.before-hero-mobile-layout.bak"
CSS_BACKUP = ROOT / "src" / "style-improvements.css.before-hero-mobile-layout.bak"
APP_MARKER = "/* compass-settings-label-v1 */"
CSS_MARKER = "/* compass-hero-mobile-compact-v1 */"


def fail(message: str) -> None:
    print(f"エラー: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if not APP.is_file() or not CSS.is_file():
        fail("リポジトリのルートで実行してください（src/App.tsx と src/style-improvements.css が必要です）。")

    app = APP.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")

    if APP_MARKER in app and CSS_MARKER in css:
        print("この改善はすでに適用されています。変更はありません。")
        return
    if APP_MARKER in app or CSS_MARKER in css:
        fail("一部だけ適用済みのようです。ファイルを変更せず停止しました。App.tsx と style-improvements.css を確認してください。")

    # 全箇所を準備段階で検証し、想定外のソースには書き込まない。
    nav_old = 'label="設定・バックアップ"'
    title_old = "settings: '設定・バックアップ'"
    battles_prompt = '`${name} の合計試合数を入力してください`'
    wins_prompt = '`${name} の合計勝ち数を入力してください`'
    if app.count(nav_old) != 1:
        fail(f"設定タブ名の位置を特定できません（{nav_old} の件数: {app.count(nav_old)}）。")
    if app.count(title_old) != 1:
        fail(f"設定画面タイトルの位置を特定できません（{title_old} の件数: {app.count(title_old)}）。")
    if app.count(battles_prompt) != 1 or app.count(wins_prompt) != 1:
        fail("ヒーロー成績修正の試合数・勝ち数入力欄を確認できません。最新コードか確認してください。")

    updated_app = app.replace(nav_old, 'label="設定・その他"', 1)
    updated_app = updated_app.replace(title_old, "settings: '設定・その他'", 1)
    updated_app = updated_app.replace(
        battles_prompt,
        '`${name} の合計試合数を入力してください（1/2）`', 1,
    )
    updated_app = updated_app.replace(
        wins_prompt,
        '`${name} の合計勝ち数を入力してください（2/2）`', 1,
    )
    updated_app += f"\n\n{APP_MARKER}\n"

    css_addition = r'''

/* compass-hero-mobile-compact-v1 */
@media (max-width: 700px) {
  /* 一覧：横スクロールをなくし、ヒーロー名と操作ボタンを同時に表示 */
  .hero-log-table-wrap,
  .hero-detail-table-wrap {
    width: 100%;
    max-width: 100%;
    overflow-x: hidden !important;
  }
  .hero-log-table,
  .hero-detail-table,
  .hero-log-main-table {
    width: 100% !important;
    min-width: 0 !important;
    table-layout: fixed;
    font-size: 9px;
  }
  .hero-log-table th,
  .hero-log-table td {
    padding: 7px 3px;
    font-size: 9px;
    line-height: 1.35;
  }
  .hero-log-table th {
    white-space: normal;
    overflow-wrap: anywhere;
  }
  .hero-log-name {
    min-width: 0;
    gap: 2px;
    white-space: normal;
    overflow-wrap: anywhere;
  }
  .hero-log-name strong { font-size: 9px; line-height: 1.35; }
  .hero-log-name small { font-size: 8px; }

  /* ヒーロー一覧の列幅 */
  .hero-log-main-table th:nth-child(1),
  .hero-log-main-table td:nth-child(1) { width: 31%; text-align: left; }
  .hero-log-main-table th:nth-child(2),
  .hero-log-main-table td:nth-child(2) { width: 14%; text-align: center; }
  .hero-log-main-table th:nth-child(3),
  .hero-log-main-table td:nth-child(3) { width: 14%; text-align: center; }
  .hero-log-main-table th:nth-child(4),
  .hero-log-main-table td:nth-child(4) { width: 15%; text-align: center; }
  .hero-log-main-table th:nth-child(5),
  .hero-log-main-table td:nth-child(5) { width: 26%; text-align: center; }
  .hero-log-main-table td:nth-child(2),
  .hero-log-main-table td:nth-child(3),
  .hero-log-main-table td:nth-child(4) { white-space: nowrap; }
  .hero-log-row-actions { justify-content: center; gap: 3px; }
  .hero-log-detail-button { min-width: 0; padding: 6px 5px; font-size: 9px; }
  .hero-log-edit-button {
    width: 29px;
    height: 29px;
    flex: 0 0 29px;
    padding: 5px;
  }
  .hero-log-edit-button svg { width: 14px; height: 14px; }

  /* 詳細：先頭列（マップ名・ヒーロー名）も折り返して常に表示 */
  .hero-detail-table th:first-child,
  .hero-detail-table td:first-child {
    width: 49%;
    text-align: left;
    white-space: normal;
    overflow-wrap: anywhere;
    word-break: normal;
  }
  .hero-detail-table th:nth-child(2),
  .hero-detail-table td:nth-child(2),
  .hero-detail-table th:nth-child(3),
  .hero-detail-table td:nth-child(3),
  .hero-detail-table th:nth-child(4),
  .hero-detail-table td:nth-child(4) { width: 17%; }
  .hero-detail-table th:not(:first-child),
  .hero-detail-table td:not(:first-child) {
    text-align: center;
    white-space: nowrap;
  }

  /* 詳細画面のタブ・集計表示も小さくまとめる */
  .hero-detail-tabs { display: flex; gap: 4px; margin-bottom: 10px; }
  .hero-detail-tabs button {
    flex: 1 1 0;
    min-width: 0;
    padding: 7px 3px;
    font-size: 9px;
    white-space: nowrap;
  }
  .hero-detail-summary { gap: 5px; margin: 10px 0; }
  .hero-detail-stat { gap: 4px; padding: 8px 6px; }
  .hero-detail-stat small { font-size: 8px; }
  .hero-detail-stat strong { font-size: 15px; }
  .hero-detail-controls,
  .hero-detail-sort-controls { gap: 7px; margin-bottom: 10px; }
  .hero-detail-controls label,
  .hero-detail-sort-controls label { gap: 4px; font-size: 9px; }
  .hero-detail-controls select,
  .hero-detail-sort-controls select { min-width: 0; width: 100%; padding: 8px 6px; font-size: 9px; }
  .hero-detail-sort-controls .secondary-button { padding: 7px 8px; font-size: 9px; }
  .hero-log-explanation { margin-bottom: 9px; font-size: 10px; line-height: 1.6; }
}
'''
    updated_css = css.rstrip() + css_addition + "\n"

    # Prepare both outputs before writing either file.
    if not APP_BACKUP.exists():
        APP_BACKUP.write_text(app, encoding="utf-8")
    if not CSS_BACKUP.exists():
        CSS_BACKUP.write_text(css, encoding="utf-8")
    APP.write_text(updated_app, encoding="utf-8")
    CSS.write_text(updated_css, encoding="utf-8")
    print("改善を適用しました。")
    print("変更: 設定・その他への名称変更、ヒーロー一覧・詳細のスマホ表示の省スペース化。")
    print("成績修正は合計試合数→合計勝ち数の順に入力する表示（1/2・2/2）にしました。")
    print("Supabaseのテーブル構成・保存データ形式は変更していません。")


if __name__ == "__main__":
    main()
