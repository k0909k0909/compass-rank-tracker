#!/usr/bin/env python3
"""
Apply the mobile hero-log layout repair to the #Compass rank tracker.
Run this file from the repository's main branch.
The script creates timestamped backups before changing either source file.
"""

from datetime import datetime
from pathlib import Path
import subprocess
import sys

APP_PATH = Path("src/App.tsx")
CSS_PATH = Path("src/style-improvements.css")
CSS_MARKER = "/* MOBILE HERO LOG REPAIR: compact tables and reliably scrollable bottom navigation */"

CSS_PATCH = r"""

/* MOBILE HERO LOG REPAIR: compact tables and reliably scrollable bottom navigation */
@media (max-width: 700px) {
  .sidebar nav {
    display: flex;
    flex-wrap: nowrap;
    justify-content: flex-start;
    width: 100%;
    min-width: 0;
    gap: 2px;
    overflow-x: auto;
    overflow-y: hidden;
    touch-action: pan-x;
    overscroll-behavior-x: contain;
    -webkit-overflow-scrolling: touch;
    scroll-snap-type: x proximity;
    scrollbar-width: none;
  }
  .sidebar nav::-webkit-scrollbar { display: none; }
  .sidebar nav .nav-item {
    flex: 0 0 76px;
    min-width: 76px;
    scroll-snap-align: start;
  }

  .hero-log-page,
  .hero-log-page > .content-card,
  .hero-log-table-wrap,
  .hero-detail-table-wrap {
    min-width: 0;
    max-width: 100%;
  }
  .hero-log-table-wrap,
  .hero-detail-table-wrap {
    overflow-x: visible;
  }

  /* Fit the hero totals table to the phone width. */
  .hero-log-table.hero-log-main-table {
    width: 100%;
    min-width: 0;
    table-layout: fixed;
  }
  .hero-log-table.hero-log-main-table th,
  .hero-log-table.hero-log-main-table td {
    padding: 8px 4px;
    font-size: 9px;
    white-space: normal;
    overflow-wrap: anywhere;
  }
  .hero-log-table.hero-log-main-table th:first-child,
  .hero-log-table.hero-log-main-table td:first-child {
    width: 36%;
    text-align: left;
  }
  .hero-log-table.hero-log-main-table th:nth-child(2),
  .hero-log-table.hero-log-main-table td:nth-child(2),
  .hero-log-table.hero-log-main-table th:nth-child(3),
  .hero-log-table.hero-log-main-table td:nth-child(3) {
    width: 13%;
    text-align: center;
  }
  .hero-log-table.hero-log-main-table th:nth-child(4),
  .hero-log-table.hero-log-main-table td:nth-child(4) {
    width: 16%;
    text-align: center;
  }
  .hero-log-table.hero-log-main-table th:last-child,
  .hero-log-table.hero-log-main-table td:last-child {
    width: 22%;
    text-align: center;
  }
  .hero-log-name {
    min-width: 0;
    gap: 2px;
    overflow-wrap: anywhere;
  }
  .hero-log-name strong {
    font-size: 9px;
    white-space: normal;
  }
  .hero-log-name small { font-size: 8px; }
  .hero-log-row-actions {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 3px;
    justify-items: stretch;
  }
  .hero-log-table.hero-log-main-table .hero-log-detail-button {
    width: 100%;
    min-width: 0;
    padding: 5px 2px;
    font-size: 9px;
  }
  .hero-log-table.hero-log-main-table .hero-log-edit-button {
    width: 100%;
    min-width: 0;
    height: 26px;
    flex: 0 0 auto;
  }

  /* Fit the hero detail breakdown table to the phone width. */
  .hero-log-table.hero-detail-table {
    width: 100%;
    min-width: 0;
    table-layout: fixed;
  }
  .hero-log-table.hero-detail-table th,
  .hero-log-table.hero-detail-table td {
    padding: 8px 5px;
    font-size: 9px;
  }
  .hero-log-table.hero-detail-table th:first-child,
  .hero-log-table.hero-detail-table td:first-child {
    width: 46%;
    white-space: normal;
    overflow-wrap: anywhere;
    text-align: left;
  }
  .hero-log-table.hero-detail-table th:nth-child(2),
  .hero-log-table.hero-detail-table td:nth-child(2),
  .hero-log-table.hero-detail-table th:nth-child(3),
  .hero-log-table.hero-detail-table td:nth-child(3),
  .hero-log-table.hero-detail-table th:nth-child(4),
  .hero-log-table.hero-detail-table td:nth-child(4) {
    width: 18%;
    text-align: right;
    white-space: nowrap;
  }
  .hero-detail-tabs {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 5px;
  }
  .hero-detail-tabs button {
    min-width: 0;
    padding: 8px 4px;
    font-size: 9px;
  }
  .hero-detail-sort-controls {
    justify-content: space-between;
    align-items: end;
    gap: 8px;
  }
}
"""

def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()

def main() -> int:
    root = Path.cwd()

    if not (root / ".git").exists():
        print("エラー: リポジトリのルートフォルダで実行してください。")
        print("例: compass-rank-tracker フォルダに移動してから実行します。")
        return 1

    try:
        branch = run_git("branch", "--show-current")
    except Exception as exc:
        print(f"Gitの状態を確認できません: {exc}")
        return 1

    if branch != "main":
        print(f"安全のため中止しました。現在のブランチは '{branch}' です。")
        print("main ブランチに切り替えてから、もう一度実行してください。")
        return 1

    for rel in (APP_PATH, CSS_PATH):
        if not (root / rel).is_file():
            print(f"エラー: {rel} が見つかりません。")
            return 1

    # Do not overwrite unrelated local edits in the files being patched.
    try:
        changed = run_git("diff", "--name-only", "--", str(APP_PATH), str(CSS_PATH))
    except Exception as exc:
        print(f"変更状態を確認できません: {exc}")
        return 1

    if changed:
        print("安全のため中止しました。次のファイルに未コミットの変更があります:")
        print(changed)
        print("先に変更をコミットするか、内容を退避してください。")
        return 1

    app_file = root / APP_PATH
    css_file = root / CSS_PATH
    app_text = app_file.read_text(encoding="utf-8")
    css_text = css_file.read_text(encoding="utf-8")

    old_label = "設定・バックアップ"
    label_count = app_text.count(old_label)
    if label_count == 0:
        print("エラー: App.tsx に '設定・バックアップ' が見つかりません。")
        print("想定と異なるコードの可能性があるため、変更していません。")
        return 1

    if CSS_MARKER in css_text:
        print("エラー: 今回の修正CSSはすでに追加されています。二重追加を防ぐため中止しました。")
        return 1

    backup_dir = root / ".patch-backups" / datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir.mkdir(parents=True, exist_ok=False)
    (backup_dir / "App.tsx").write_text(app_text, encoding="utf-8")
    (backup_dir / "style-improvements.css").write_text(css_text, encoding="utf-8")

    app_text_new = app_text.replace(old_label, "設定・その他")
    css_text_new = css_text.rstrip() + "\n" + CSS_PATCH + "\n"

    app_file.write_text(app_text_new, encoding="utf-8")
    css_file.write_text(css_text_new, encoding="utf-8")

    print("修正を適用しました。")
    print(f"- App.tsx: '設定・バックアップ' を {label_count} か所 '設定・その他' に変更")
    print("- style-improvements.css: スマホ向けレイアウト修正を追加")
    print(f"- 元ファイルのバックアップ: {backup_dir}")
    print("")
    print("次に、以下を実行してビルド確認してください:")
    print("  npm run build")
    print("")
    print("ビルドが成功したら、GitHubへ反映します。")
    return 0

if __name__ == "__main__":
    sys.exit(main())
