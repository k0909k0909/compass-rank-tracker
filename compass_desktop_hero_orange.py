from pathlib import Path
from datetime import datetime
import shutil
import sys

ROOT = Path.cwd()
APP = ROOT / "src" / "App.tsx"
CSS = ROOT / "src" / "style-improvements.css"
MARKER = "/* DESKTOP HERO LOG + COMPASS ORANGE MODE UPDATE v1 */"

if not APP.exists() or not CSS.exists():
    print("エラー: リポジトリのルートで実行してください。src/App.tsx または src/style-improvements.css が見つかりません。")
    sys.exit(1)

css = CSS.read_text(encoding="utf-8")
if MARKER in css:
    print("この改善はすでに適用されています。ファイルは変更していません。")
    sys.exit(0)

backup_dir = ROOT / ".patch-backups" / datetime.now().strftime("%Y%m%d-%H%M%S")
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(CSS, backup_dir / "style-improvements.css")

patch = r"""

/* DESKTOP HERO LOG + COMPASS ORANGE MODE UPDATE v1 */

/* PCでもヒーロー合計成績の表を画面幅に収め、操作列を見切れさせない。 */
@media (min-width: 701px) {
  .hero-log-table.hero-log-main-table {
    width: 100%;
    min-width: 0;
    table-layout: fixed;
  }

  .hero-log-table.hero-log-main-table th,
  .hero-log-table.hero-log-main-table td {
    padding: 9px 7px;
    white-space: normal;
    overflow-wrap: anywhere;
  }

  .hero-log-table.hero-log-main-table th:first-child,
  .hero-log-table.hero-log-main-table td:first-child {
    width: 32%;
    text-align: left;
  }

  .hero-log-table.hero-log-main-table th:nth-child(2),
  .hero-log-table.hero-log-main-table td:nth-child(2),
  .hero-log-table.hero-log-main-table th:nth-child(3),
  .hero-log-table.hero-log-main-table td:nth-child(3) {
    width: 12%;
    text-align: center;
  }

  .hero-log-table.hero-log-main-table th:nth-child(4),
  .hero-log-table.hero-log-main-table td:nth-child(4) {
    width: 14%;
    text-align: center;
  }

  .hero-log-table.hero-log-main-table th:last-child,
  .hero-log-table.hero-log-main-table td:last-child {
    width: 30%;
    text-align: center;
  }

  .hero-log-name {
    min-width: 0;
    overflow-wrap: anywhere;
  }

  .hero-log-row-actions {
    display: flex;
    flex-wrap: nowrap;
    justify-content: center;
    gap: 5px;
  }

  .hero-log-row-actions .hero-log-detail-button {
    min-width: 56px;
    padding: 7px 8px;
  }

  .hero-log-row-actions .hero-log-edit-button {
    width: 34px;
    min-width: 34px;
    flex: 0 0 34px;
  }
}

/* 試合記録画面で選択中のモードを、コンパスのロゴに近いオレンジにする。 */
html[data-theme] .mode-options .result-choice.selected.win {
  color: #ffad62 !important;
  border-color: #f28a32 !important;
  background: #4a2b18 !important;
  box-shadow: 0 0 0 1px rgba(242, 138, 50, .12);
}

html[data-theme="light"] .mode-options .result-choice.selected.win {
  color: #a94d08 !important;
  border-color: #e9822b !important;
  background: #fff0df !important;
  box-shadow: 0 0 0 1px rgba(233, 130, 43, .12);
}
"""

CSS.write_text(css.rstrip() + "\n" + patch, encoding="utf-8")

print("改善を適用しました。")
print("- PCのヒーロー合計成績表を画面幅に収め、詳細・編集ボタンの見切れを防止")
print("- 試合記録の選択中モード（バトアリ／フリバ／カスタム）をオレンジに変更")
print(f"- 変更前のCSSバックアップ: {backup_dir}")
print("次に npm run build を実行してください。")
