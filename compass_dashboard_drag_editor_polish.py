from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parent
APP = ROOT / "src" / "App.tsx"

if not (ROOT / "package.json").is_file():
    raise SystemExit(
        "エラー: package.json が見つかりません。\n"
        "この Python ファイルを compass-rank-tracker の直下（package.json と同じ階層）に置いて実行してください。"
    )
if not APP.is_file():
    raise SystemExit("エラー: src/App.tsx が見つかりません。リポジトリのルートで実行してください。")

original = APP.read_text(encoding="utf-8")
updated = original

def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"修正を中止しました: {label} の対象箇所が1か所ではありません（{count}か所）。ファイルは変更していません。")
    return source.replace(old, new, 1)

# 1) 「ヒーローの情報」「メモ等」は1件だけでもホーム上で横2マスにする。
updated = replace_once(
    updated,
    "            const wide = (repeatableGroup && group.length > 1) || widget.type === 'recentMatches'",
    "            const wide = repeatableGroup || widget.type === 'recentMatches'",
    "ホーム画面のカード幅"
)
updated = replace_once(
    updated,
    "  const wide = ((widget.type === 'heroInfo' || widget.type === 'note') && slides.length > 1) || widget.type === 'recentMatches'",
    "  const wide = widget.type === 'heroInfo' || widget.type === 'note' || widget.type === 'recentMatches'",
    "カード本体の横幅"
)

# 2) 編集一覧では、項目名と操作部だけを表示する。項目内容の入力欄はホーム上で編集する。
updated = replace_once(
    updated,
    "    { type: 'heroInfo', label: 'ヒーローの情報', description: '1件は横1。2件以上は横スライドで表示。ホーム上で変更可能', size: '横1／複数時は横2' },",
    "    { type: 'heroInfo', label: 'ヒーローの情報', description: 'ホーム上でヒーローを切り替え。複数登録時は横スライドで表示', size: '横2' },",
    "ヒーロー情報の表示サイズ説明"
)
updated = replace_once(
    updated,
    "    { type: 'note', label: 'メモ等', description: '1件は横1。2件以上は横スライドで表示。ホーム上で編集可能', size: '横1／複数時は横2' },",
    "    { type: 'note', label: 'メモ等', description: 'ホーム上で内容を編集。複数登録時は横スライドで表示', size: '横2' },",
    "メモ等の表示サイズ説明"
)
updated = replace_once(
    updated,
    "className={`dashboard-editor-widget ${widget.type === 'heroInfo' || widget.type === 'note' || widget.type === 'recentMatches' ? 'wide' : ''} ${editorDraggingKey === dragKey ? 'is-dragging' : ''}`}",
    "className={`dashboard-editor-widget ${widget.type === 'recentMatches' ? 'wide' : ''} ${editorDraggingKey === dragKey ? 'is-dragging' : ''}`}",
    "編集一覧のカード配置"
)
updated = replace_once(
    updated,
    '<div className="dashboard-editor-widget-title"><strong>{catalog.label}</strong><span>{catalog.size}</span></div>',
    '<div className="dashboard-editor-widget-title"><strong>{catalog.label}</strong></div>',
    "編集一覧のタイトル表示"
)

hero_settings = '''                    {widget.type === 'heroInfo' && <div className="editor-widget-settings"><label>表示するヒーロー</label><select value={widget.heroName ?? ''} onChange={event => updateDashboardWidget(widget.id, { heroName: event.target.value })}><option value="">ヒーローを選択してください</option>{store.heroes.map(hero => <option key={hero.name} value={hero.name}>{hero.name}（{hero.role}）</option>)}</select></div>}
                    {widget.type === 'note' && <div className="editor-widget-settings note-editor-settings">
                      <label className="editor-heading-toggle"><input type="checkbox" checked={Boolean(widget.showHeading)} onChange={event => updateDashboardWidget(widget.id, { showHeading: event.target.checked })}/> 見出しを追加</label>
                      {widget.showHeading && <input value={widget.heading ?? ''} maxLength={80} placeholder="例：今月の目標" onChange={event => updateDashboardWidget(widget.id, { heading: event.target.value })}/ >}
                      <textarea rows={3} maxLength={3000} value={widget.body ?? ''} placeholder="例：○○までに○○使いを達成する" onChange={event => updateDashboardWidget(widget.id, { body: event.target.value })}/>
                    </div>}
'''.replace('/ >', '/>')
updated = replace_once(updated, hero_settings, "", "編集一覧内の詳細入力欄")

# 3) ドラッグ中、画面の上下端に近づいたらページを自動スクロールする。
updated = replace_once(
    updated,
    '''  function handleDashboardDragMove(event: React.PointerEvent<HTMLButtonElement>) {
    const drag = dashboardDragRef.current
    if (!drag || drag.pointerId !== event.pointerId) return
    if (!drag.moved && Math.hypot(event.clientX - drag.startX, event.clientY - drag.startY) > 8) {
      drag.moved = true
      setDashboardDraggingId(drag.id)
    }
    if (drag.moved) {
      const target = document.elementFromPoint(event.clientX, event.clientY)?.closest<HTMLElement>('[data-dashboard-widget-id]')''',
    '''  function handleDashboardDragMove(event: React.PointerEvent<HTMLButtonElement>) {
    const drag = dashboardDragRef.current
    if (!drag || drag.pointerId !== event.pointerId) return
    if (!drag.moved && Math.hypot(event.clientX - drag.startX, event.clientY - drag.startY) > 8) {
      drag.moved = true
      setDashboardDraggingId(drag.id)
    }
    if (drag.moved) {
      // ドラッグしたまま画面の上下端へ移動すると、ページを自動スクロールします。
      const edge = 88
      const bottomEdge = window.innerHeight - (window.innerWidth <= 700 ? 106 : 76)
      if (event.clientY < edge) {
        const speed = Math.min(22, Math.max(4, Math.ceil((edge - event.clientY) / 3)))
        window.scrollBy({ top: -speed, left: 0, behavior: 'auto' })
      } else if (event.clientY > bottomEdge) {
        const speed = Math.min(22, Math.max(4, Math.ceil((event.clientY - bottomEdge) / 3)))
        window.scrollBy({ top: speed, left: 0, behavior: 'auto' })
      }
      const target = document.elementFromPoint(event.clientX, event.clientY)?.closest<HTMLElement>('[data-dashboard-widget-id]')''',
    "ホーム画面ドラッグ中の自動スクロール"
)

# 編集モーダル内の並べ替えでも、リストの上下端でスクロールします。
updated = replace_once(
    updated,
    '''    if (!drag.moved && Math.hypot(event.clientX - drag.startX, event.clientY - drag.startY) > 7) {
      drag.moved = true
      setEditorDraggingKey(`${drag.scope}:${drag.id}`)
    }
  }
  function handleEditorPointerUp''',
    '''    if (!drag.moved && Math.hypot(event.clientX - drag.startX, event.clientY - drag.startY) > 7) {
      drag.moved = true
      setEditorDraggingKey(`${drag.scope}:${drag.id}`)
    }
    if (drag.moved) {
      const scrollContainer = event.currentTarget.closest<HTMLElement>('.dashboard-editor-content')
      if (scrollContainer) {
        const rect = scrollContainer.getBoundingClientRect()
        const edge = 64
        if (event.clientY < rect.top + edge) {
          const speed = Math.min(20, Math.max(4, Math.ceil((rect.top + edge - event.clientY) / 3)))
          scrollContainer.scrollTop -= speed
        } else if (event.clientY > rect.bottom - edge) {
          const speed = Math.min(20, Math.max(4, Math.ceil((event.clientY - (rect.bottom - edge)) / 3)))
          scrollContainer.scrollTop += speed
        }
      }
    }
  }
  function handleEditorPointerUp''',
    "編集モーダル内ドラッグの自動スクロール"
)

# 4) ログイン欄は元のように薄字の補助文を表示しない。
updated = replace_once(
    updated,
    'placeholder="メールアドレスまたは dummy" ',
    "",
    "ログイン欄のプレースホルダー"
)

if updated == original:
    raise SystemExit("変更箇所がありません。ファイルは変更していません。")

backup_dir = ROOT / ".patch-backups"
backup_dir.mkdir(exist_ok=True)
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup_path = backup_dir / f"App.tsx.before-dashboard-polish-{stamp}.bak"
shutil.copy2(APP, backup_path)
APP.write_text(updated, encoding="utf-8")

print("修正を適用しました。")
print("変更ファイル: src/App.tsx")
print(f"バックアップ: {backup_path.relative_to(ROOT)}")
print("内容:")
print("- ヒーローの情報・メモ等は1件でも横2マス")
print("- ログイン欄の薄字プレースホルダーを削除")
print("- ドラッグ中の画面上下端で自動スクロール")
print("- 編集一覧は項目タイトルと操作部分だけに簡略化")
print("")
print("次に npm run build でビルド確認してください。")
