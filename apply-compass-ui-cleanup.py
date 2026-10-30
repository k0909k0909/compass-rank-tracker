from pathlib import Path
import sys

ROOT = Path.cwd()
APP = ROOT / "src" / "App.tsx"
VITE_CONFIG = ROOT / "vite.config.ts"
VITE_ENV = ROOT / "src" / "vite-env.d.ts"

required = [APP, VITE_CONFIG, VITE_ENV]
missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
if missing:
    raise SystemExit("必要なファイルが見つかりません: " + ", ".join(missing) + "\npackage.json のあるリポジトリ直下で実行してください。")

app = APP.read_text(encoding="utf-8")
vite_config = VITE_CONFIG.read_text(encoding="utf-8")
vite_env = VITE_ENV.read_text(encoding="utf-8")

replacements = [
    (
        '<small className="small-note">{rotationApplied ? `${recordRotationDate} のバトアリは登録済みの4ステージのみ表示しています。` : `この日付のバトアリローテーションは未登録です。全マップを表示しています。フリバ・カスタムは常に全マップです。`}</small>',
        '',
        "試合記録画面のローテーション説明",
    ),
    (
        '<div className="field field-wide freeba-rank-note"><strong>{form.mode}ではランクポイントは変動しません。</strong><span>現在のランクは記録・確認のみ行います。</span></div>',
        'null',
        "フリバ・カスタム時のランク説明",
    ),
    (
        '<div className="team-page-heading"><h4>チーム構成</h4><p>敵チーム3人、味方チームは自分以外の2人を任意で記録できます。横にスワイプしてページを移動できます。</p></div>',
        '<div className="team-page-heading"><h4>チーム構成</h4></div>',
        "チーム構成の説明文",
    ),
    (
        'placeholder="味方編成、反省点、気づいたことなど"',
        'placeholder="反省点、気づいたことなど"',
        "メモ欄のプレースホルダー",
    ),
    (
        '<div className="section-heading"><div><h3>ステージローテーション</h3><p>日付ごとにバトアリの4ステージを登録します。登録のない日やフリバ・カスタムでは全マップが選べます。</p></div><div className="round-icon"><CalendarDays size={20}/></div></div>',
        '<div className="section-heading"><div><h3>ステージローテーション</h3></div><div className="round-icon"><CalendarDays size={20}/></div></div>',
        "ステージローテーションの説明文",
    ),
    (
        '<p className="small-note">シーズン初日の木曜日、土日、全ステージ対象の日は登録不要です。ローテーション対象日のみ登録してください。日付単位で保存するため、別の月へ自動流用されません。</p>',
        '',
        "ステージローテーションの補足文",
    ),
]

for old, new, label in replacements:
    count = app.count(old)
    if count != 1:
        raise SystemExit(f"{label}の置換対象が1か所ではありません（{count}か所）。ファイルは変更していません。")

build_marker = "const CloudContext = createContext<CloudContextValue | null>(null)"
if app.count(build_marker) != 1:
    raise SystemExit("App.tsx の更新日時挿入位置を特定できません。ファイルは変更していません。")
if "appLastUpdatedAt" in app:
    raise SystemExit("最終更新日時の表示コードが既にあります。二重追加を避けるため終了します。")

settings_marker = '        <div className="content-card future-card"><div className="round-icon"><Activity size={20}/></div><div><h3>現在の機能</h3><p>試合日時、バトアリ／フリバ、リセット操作で切り替わるシーズン、実装時期順のヒーロー選択、お気に入り・ロール絞込み、S1〜S9のランク・ポイント管理、バックアップ・復元に対応しています。</p></div></div>\n      </section>}'
if app.count(settings_marker) != 1:
    raise SystemExit("設定画面の最下部を特定できません。ファイルは変更していません。")

expected_config = "export default defineConfig({\n  plugins: [react()],\n})"
if vite_config.count(expected_config) != 1:
    if "__APP_BUILD_AT__" in vite_config:
        raise SystemExit("vite.config.ts にビルド日時の設定が既にあります。二重追加を避けて終了します。")
    raise SystemExit("vite.config.ts の形式が想定と異なります。ファイルは変更していません。")

env_declaration = "declare const __APP_BUILD_AT__: string"
if env_declaration in vite_env:
    raise SystemExit("src/vite-env.d.ts に日時型宣言が既にあります。二重追加を避けて終了します。")

# All checks passed. Keep one-time backups before writing.
backup_paths = [APP, VITE_CONFIG, VITE_ENV]
for path in backup_paths:
    backup = path.with_name(path.name + ".before-ui-cleanup.bak")
    if backup.exists():
        raise SystemExit(f"バックアップファイルが既に存在します: {backup.name}\n上書きせず終了しました。")
for path in backup_paths:
    path.with_name(path.name + ".before-ui-cleanup.bak").write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

for old, new, _label in replacements:
    app = app.replace(old, new, 1)

app = app.replace(
    build_marker,
    build_marker + "\nconst appLastUpdatedAt = new Intl.DateTimeFormat('ja-JP', { timeZone: 'Asia/Tokyo', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date(__APP_BUILD_AT__))",
    1,
)
app = app.replace(
    settings_marker,
    settings_marker.replace("\n      </section>}", '\n        <p className="small-note" style={{ textAlign: \'right\', fontSize: \'0.75rem\' }}>最終更新日時：{appLastUpdatedAt}</p>\n      </section>}'),
    1,
)

vite_config = vite_config.replace(
    expected_config,
    "export default defineConfig({\n  plugins: [react()],\n  define: {\n    __APP_BUILD_AT__: JSON.stringify(new Date().toISOString()),\n  },\n})",
    1,
)
vite_env = vite_env.rstrip() + "\n\n" + env_declaration + "\n"

APP.write_text(app, encoding="utf-8")
VITE_CONFIG.write_text(vite_config, encoding="utf-8")
VITE_ENV.write_text(vite_env, encoding="utf-8")

print("画面の不要文言を削除し、最終更新日時の表示を追加しました。")
print("変更ファイル: src/App.tsx, vite.config.ts, src/vite-env.d.ts")
print("3つのバックアップ（*.before-ui-cleanup.bak）を作成しました。")
