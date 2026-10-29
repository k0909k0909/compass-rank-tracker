#!/usr/bin/env python3
"""Apply the COMPASS white/black visual redesign to the Vite React app."""
from pathlib import Path
from datetime import datetime
import re
import shutil
import sys

ROOT = Path.cwd()
APP = ROOT / "src" / "App.tsx"
INDEX = ROOT / "index.html"
THEME = ROOT / "src" / "theme.css"
ASSET = ROOT / "src" / "assets" / "compass-note-mark.svg"
PUBLIC_ASSET = ROOT / "public" / "compass-note-mark.svg"

if not APP.is_file() or not INDEX.is_file():
    print("エラー: プロジェクトのルートで実行してください（src/App.tsx と index.html が見つかりません）。", file=sys.stderr)
    sys.exit(1)

app = APP.read_text(encoding="utf-8")
index = INDEX.read_text(encoding="utf-8")
if "compass-rank-tracker-theme-v1" in app and "import './theme.css'" in app:
    print("テーマ切替はすでに適用済みのようです。二重適用を避けて終了します。")
    sys.exit(0)

# Validate the source before touching files; a mismatch should fail safely.
required = [
    "export default function App() {",
    "import './style.css'",
    "import './style-improvements.css'",
    '<div className="cloud-user-bar"><span>{user.email} でログイン中 · 同期：{syncStatus}</span><button onClick={() => supabase.auth.signOut()}>ログアウト</button></div>',
    'if (!supabase) return <div className="auth-shell">',
    'if (!user) return <div className="auth-shell">',
    'if (!ready) return <div className="auth-shell">',
]
missing = [needle for needle in required if needle not in app]
if missing:
    print("エラー: App.tsx の構造が想定と異なるため、安全のため変更していません。", file=sys.stderr)
    print("見つからないパターン:", *missing, sep="\n- ", file=sys.stderr)
    sys.exit(2)

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = Path("/tmp") / f"compass-theme-redesign-backup-{stamp}"
backup.mkdir(parents=True, exist_ok=False)
for path in (APP, INDEX, THEME, ASSET, PUBLIC_ASSET):
    if path.exists() and path.is_file():
        dest = backup / path.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)

# Add icon and theme imports.
app, n = re.subn(r'\bStar, Swords\b', 'Star, Sun, Moon, Swords', app, count=1)
if n != 1:
    print("エラー: lucide-react の import を特定できませんでした。バックアップは作成済みです。", file=sys.stderr)
    print(f"バックアップ: {backup}", file=sys.stderr)
    sys.exit(3)
app = app.replace("import './style.css'\n", "import compassNoteMark from './assets/compass-note-mark.svg'\nimport './style.css'\n", 1)
app = app.replace("import './style-improvements.css'\n", "import './style-improvements.css'\nimport './theme.css'\n", 1)

# Use the supplied orange emblem in the sidebar and auth screens.
old_mark = '<div className="brand-mark"><Swords size={23}/></div>'
new_mark = '<div className="brand-mark"><img className="brand-mark-image" src={compassNoteMark} alt="" /></div>'
if old_mark not in app:
    print("エラー: ロゴ表示位置が見つかりませんでした。安全のため変更していません。", file=sys.stderr)
    print(f"バックアップ: {backup}", file=sys.stderr)
    sys.exit(4)
app = app.replace(old_mark, new_mark)

# Persistent theme preference: dark stays the default for existing users.
theme_code = '''export default function App() {
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
'''
app = app.replace('export default function App() {\n', theme_code, 1)

# Show the toggle at the top-left of auth screens and the login/sync bar.
app = app.replace('if (!supabase) return <div className="auth-shell">', 'if (!supabase) return <div className="auth-shell">{themeToggle}', 1)
app = app.replace('if (!user) return <div className="auth-shell">', 'if (!user) return <div className="auth-shell">{themeToggle}', 1)
app = app.replace('if (!ready) return <div className="auth-shell">', 'if (!ready) return <div className="auth-shell">{themeToggle}', 1)
old_bar = '<div className="cloud-user-bar"><span>{user.email} でログイン中 · 同期：{syncStatus}</span><button onClick={() => supabase.auth.signOut()}>ログアウト</button></div>'
new_bar = '<div className="cloud-user-bar">{themeToggle}<span className="cloud-login-status">{user.email} でログイン中 · 同期：{syncStatus}</span><button className="logout-button" onClick={() => supabase.auth.signOut()}>ログアウト</button></div>'
app = app.replace(old_bar, new_bar, 1)

logo_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 271 271" role="img" aria-label="コンパス戦績ノートのロゴ"><path d="M 136 67 L 135 67 L 34 168 L 34 169 L 135 270 L 162 243 L 162 242 L 129 209 L 129 208 L 202 135 L 202 133 Z M 136 122 L 147 133 L 147 135 L 102 180 L 100 180 L 89 169 L 89 168 L 135 122 Z M 135 0 L 1 134 L 0 134 L 0 135 L 27 162 L 28 162 L 28 161 L 54 135 L 55 135 L 55 134 L 62 127 L 63 127 L 64 125 L 135 54 L 216 135 L 214 136 L 142 208 L 142 209 L 169 236 L 270 135 L 270 134 L 136 0 Z" fill="#FF8808" fill-rule="evenodd"/></svg>'''

# Variable-based redesign; original data and app logic are unchanged.
theme_css = r'''/* COMPASS visual refresh: VOIDOLL light / BUGDOLL dark */
html[data-theme="dark"] {
  color-scheme: dark;
  --app-bg: #080c15;
  --surface: #101725;
  --surface-raised: #141f30;
  --surface-muted: #0b1320;
  --text-main: #edf9fc;
  --text-soft: #b5cbd5;
  --text-muted: #829aa8;
  --line: #293c4b;
  --accent: #39e6f2;
  --accent-strong: #04bfd0;
  --accent-text: #041218;
  --accent-soft: #10313a;
  --accent-line: #24616c;
  --shadow: rgba(0, 7, 15, .35);
  --grid-line: rgba(57, 230, 242, .045);
}
html[data-theme="light"] {
  color-scheme: light;
  --app-bg: #f1f9fb;
  --surface: #ffffff;
  --surface-raised: #f7fcfd;
  --surface-muted: #eaf4f7;
  --text-main: #1c2e39;
  --text-soft: #435d68;
  --text-muted: #6f8791;
  --line: #cbdde2;
  --accent: #00b8ca;
  --accent-strong: #009bad;
  --accent-text: #ffffff;
  --accent-soft: #def8fa;
  --accent-line: #8adce4;
  --shadow: rgba(35, 88, 104, .12);
  --grid-line: rgba(0, 154, 176, .05);
}
html[data-theme] { background: var(--app-bg); color: var(--text-main); }
html[data-theme] body {
  color: var(--text-main);
  background-image: radial-gradient(ellipse at 78% -15%, rgba(41, 213, 231, .12), transparent 37%),
    linear-gradient(var(--grid-line) 1px, transparent 1px),
    linear-gradient(90deg, var(--grid-line) 1px, transparent 1px);
  background-color: var(--app-bg);
  background-size: auto, 34px 34px, 34px 34px;
  transition: background-color .2s ease, color .2s ease;
}
html[data-theme] .app-shell, html[data-theme] .main-content { color: var(--text-main); }
html[data-theme] .sidebar {
  background: var(--surface);
  border-color: var(--line);
  box-shadow: 5px 0 24px var(--shadow);
}
html[data-theme] .brand-mark { background: transparent !important; box-shadow: none !important; border-radius: 0 !important; }
.brand-mark-image { display: block; width: 100%; height: 100%; object-fit: contain; }
html[data-theme] .brand-copy strong, html[data-theme] .topbar h1,
html[data-theme] .section-heading h3, html[data-theme] .stat-card,
html[data-theme] .content-card, html[data-theme] .future-card h3,
html[data-theme] .auth-card h1 { color: var(--text-main); }
html[data-theme] .brand-copy span, html[data-theme] .side-label,
html[data-theme] .sidebar-foot, html[data-theme] .section-heading p,
html[data-theme] .stat-card > small, html[data-theme] .mini-hero-role,
html[data-theme] .empty-inline, html[data-theme] .hint-row,
html[data-theme] .app-footer, html[data-theme] .small-note,
html[data-theme] .field label small, html[data-theme] .active-season-note { color: var(--text-muted); }
html[data-theme] .nav-item { color: var(--text-muted); }
html[data-theme] .nav-item:hover { background: var(--surface-muted); color: var(--text-main); }
html[data-theme] .nav-item.active {
  background: linear-gradient(90deg, rgba(41, 213, 231, .16), rgba(41, 213, 231, .035));
  color: var(--accent-strong);
}
html[data-theme] .nav-indicator { background: var(--accent); box-shadow: 0 0 10px rgba(41, 213, 231, .45); }
html[data-theme] .primary-button {
  color: var(--accent-text); background: linear-gradient(135deg, var(--accent), var(--accent-strong));
  border: 1px solid var(--accent-strong); box-shadow: 0 5px 17px rgba(0, 184, 202, .18);
}
html[data-theme] .primary-button:hover { filter: brightness(1.06); transform: translateY(-1px); }
html[data-theme] .secondary-button, html[data-theme] .danger-button {
  background: var(--surface-raised); color: var(--text-soft); border-color: var(--line);
}
html[data-theme] .secondary-button:hover { background: var(--surface-muted); border-color: var(--accent-line); color: var(--text-main); }
html[data-theme] .text-button { color: var(--accent-strong); }
html[data-theme] .text-button:hover { color: var(--accent); }
html[data-theme] .content-card, html[data-theme] .stat-card,
html[data-theme] .welcome-panel, html[data-theme] .rank-control-panel,
html[data-theme] .future-card {
  background: var(--surface); border-color: var(--line); box-shadow: 0 8px 28px var(--shadow);
}
html[data-theme] .content-card { border-radius: 15px; }
html[data-theme] .stat-card { position: relative; overflow: hidden; }
html[data-theme] .stat-card::before { content: ""; position: absolute; inset: 0 auto auto 0; height: 2px; width: 46px; background: var(--accent); opacity: .8; }
html[data-theme] .stat-card .stat-icon, html[data-theme] .round-icon, html[data-theme] .empty-icon {
  background: var(--accent-soft); color: var(--accent-strong);
}
html[data-theme] .stat-card > strong { color: var(--text-main); }
html[data-theme] .welcome-panel p, html[data-theme] .future-card p { color: var(--text-soft); }
html[data-theme] .match-table th, html[data-theme] .mini-table th { color: var(--text-muted); border-color: var(--line); }
html[data-theme] .match-table td, html[data-theme] .mini-table td { color: var(--text-soft); border-color: var(--line); }
html[data-theme] .hero-cell strong, html[data-theme] .mini-hero-name { color: var(--text-main); }
html[data-theme] .hero-cell small, html[data-theme] .date-cell, html[data-theme] .mini-hero-role { color: var(--text-muted); }
html[data-theme] .rate-cell { color: var(--accent-strong) !important; }
html[data-theme] .field label, html[data-theme] .rank-panel-heading { color: var(--text-main); }
html[data-theme] input, html[data-theme] select, html[data-theme] textarea,
html[data-theme] .field input, html[data-theme] .field select, html[data-theme] .field textarea,
html[data-theme] .catalog-add input, html[data-theme] .catalog-add select,
html[data-theme] .search-field {
  color: var(--text-main); background-color: var(--surface-raised); border-color: var(--line);
}
html[data-theme] input::placeholder, html[data-theme] textarea::placeholder { color: var(--text-muted); opacity: 1; }
html[data-theme] input:focus, html[data-theme] select:focus, html[data-theme] textarea:focus {
  border-color: var(--accent-strong) !important; box-shadow: 0 0 0 3px rgba(41, 213, 231, .14) !important;
}
html[data-theme] option { color: var(--text-main); background: var(--surface); }
html[data-theme] .result-choice { color: var(--text-soft); background: var(--surface-raised); border-color: var(--line); }
html[data-theme] .result-choice.selected.win { background: #dff8ed; color: #087a55; border-color: #35bd91; }
html[data-theme="dark"] .result-choice.selected.win { background: #12392f; color: #80f0c0; border-color: #35bd91; }
html[data-theme] .result-choice.selected.loss { background: #fff0f1; color: #bb364e; border-color: #ee8191; }
html[data-theme="dark"] .result-choice.selected.loss { background: #44222c; color: #ffadba; border-color: #ee8191; }
html[data-theme] .result-choice.selected.draw { background: var(--surface-muted); color: var(--text-main); border-color: var(--text-muted); }
html[data-theme] .role-filter-button, html[data-theme] .catalog-item,
html[data-theme] .favorite-filter, html[data-theme] .favorite-toggle {
  color: var(--text-soft); background: var(--surface-raised); border-color: var(--line);
}
html[data-theme] .role-filter-button.active, html[data-theme] .favorite-filter.active,
html[data-theme] .favorite-toggle.active {
  color: var(--accent-strong); border-color: var(--accent-line); background: var(--accent-soft);
}
html[data-theme] .table-wrap { border-color: var(--line); }
html[data-theme] .hint-row svg { color: var(--accent-strong); }
html[data-theme] .toast { background: var(--surface); color: var(--text-main); border: 1px solid var(--line); box-shadow: 0 8px 35px var(--shadow); }
html[data-theme] .toast button { color: var(--text-muted); }
html[data-theme] .toast-dot { background: var(--accent); }
html[data-theme] .auth-shell {
  background: radial-gradient(ellipse at 50% 0%, rgba(41, 213, 231, .15) 0, transparent 48%), var(--app-bg);
  color: var(--text-main); position: relative;
}
html[data-theme] .auth-card { background: var(--surface); border-color: var(--line); box-shadow: 0 24px 80px var(--shadow); }
html[data-theme] .auth-card p, html[data-theme] .auth-card ol { color: var(--text-soft); }
html[data-theme] .auth-card code { color: var(--accent-strong); }
html[data-theme] .auth-message { background: var(--accent-soft); color: var(--text-main) !important; }
html[data-theme] .cloud-user-bar {
  background: var(--surface); color: var(--text-soft); border-color: var(--line);
  justify-content: space-between; box-shadow: 0 2px 15px var(--shadow);
}
html[data-theme] .cloud-user-bar button:not(.theme-toggle) {
  background: var(--surface-raised); color: var(--text-main); border-color: var(--line);
}
html[data-theme] .cloud-user-bar button:not(.theme-toggle):hover { border-color: var(--accent-line); }
.theme-toggle {
  display: inline-flex; align-items: center; justify-content: center; gap: 7px; flex: 0 0 auto;
  padding: 7px 10px; min-height: 31px; border-radius: 9px; border: 1px solid var(--accent-line);
  background: var(--accent-soft); color: var(--accent-strong); font-size: 10px; font-weight: 800;
  letter-spacing: .01em; white-space: nowrap; transition: background .18s ease, border-color .18s ease, transform .18s ease;
}
.theme-toggle svg { width: 15px; height: 15px; }
.theme-toggle:hover { transform: translateY(-1px); border-color: var(--accent); }
.auth-shell > .theme-toggle { position: absolute; top: 16px; left: 18px; z-index: 2; }
.cloud-login-status { min-width: 0; margin-left: auto; text-align: right; overflow-wrap: anywhere; }
@media (max-width: 700px) {
  html[data-theme] .sidebar { background: var(--surface); border-top-color: var(--line); }
  .cloud-user-bar { align-items: center; gap: 8px; }
  .theme-toggle { padding: 6px 8px; font-size: 9px; }
  .cloud-login-status { flex: 1 1 100%; order: 3; text-align: left; margin: 0; }
  html[data-theme] .cloud-user-bar { flex-wrap: wrap; }
  html[data-theme] .top-add { box-shadow: none; }
  .auth-shell > .theme-toggle { top: 12px; left: 12px; }
}
'''

# Validate the favicon insertion before writing any changed files.
if 'rel="icon"' not in index:
    viewport = re.search(r'^[ \t]*<meta name="viewport"[^>]*?/?>[ \t]*$', index, re.MULTILINE)
    if not viewport:
        print("エラー: index.html の viewport 行が見つかりません。ソースの変更はまだ書き込んでいません。", file=sys.stderr)
        print(f"バックアップ: {backup}", file=sys.stderr)
        sys.exit(5)
    addition = '\n    <link rel="icon" type="image/svg+xml" href="./compass-note-mark.svg" />'
    index = index[:viewport.end()] + addition + index[viewport.end():]

if "import './theme.css'" not in app or "cloud-login-status" not in app or app.count('{themeToggle}') < 4:
    print("エラー: テーマ切替のコードがすべて挿入できませんでした。ファイルは書き込んでいません。", file=sys.stderr)
    print(f"バックアップ: {backup}", file=sys.stderr)
    sys.exit(6)

# The logo and theme stylesheet are additive; app logic, Supabase, and match storage stay intact.
THEME.parent.mkdir(parents=True, exist_ok=True)
ASSET.parent.mkdir(parents=True, exist_ok=True)
PUBLIC_ASSET.parent.mkdir(parents=True, exist_ok=True)
ASSET.write_text(logo_svg, encoding="utf-8")
PUBLIC_ASSET.write_text(logo_svg, encoding="utf-8")
THEME.write_text(theme_css, encoding="utf-8")
INDEX.write_text(index, encoding="utf-8")
APP.write_text(app, encoding="utf-8")
print("ライト／ダークテーマ、切替ボタン、ロゴを適用しました。")
print(f"バックアップ: {backup}")
print("次に npm run build を実行してから git diff --stat で変更内容を確認してください。")
