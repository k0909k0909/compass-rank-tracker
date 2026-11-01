from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parent
APP = ROOT / "src" / "App.tsx"
CSS = ROOT / "src" / "style-improvements.css"

if not (ROOT / "package.json").is_file():
    raise SystemExit("エラー: package.json が見つかりません。リポジトリ直下で実行してください。")
if not APP.is_file() or not CSS.is_file():
    raise SystemExit("エラー: src/App.tsx または src/style-improvements.css が見つかりません。")

app_original = APP.read_text(encoding="utf-8")
css_original = CSS.read_text(encoding="utf-8")
app = app_original
css = css_original

def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise SystemExit(
            f"修正を中止しました: {label} の対象箇所が1か所ではありません（{count}か所）。"
            "ファイルは変更していません。"
        )
    return source.replace(old, new, 1)

# 1件だけでも横2マス。すでに修正済みの場合はそのまま。
old_width = "            const wide = (repeatableGroup && group.length > 1) || widget.type === 'recentMatches'"
if old_width in app:
    app = replace_once(
        app, old_width,
        "            const wide = repeatableGroup || widget.type === 'recentMatches'",
        "ヒーロー情報・メモの横幅"
    )

# ホームに独立して表示していた追加用カードを削除。
old_add_tile = '''              {repeatableGroup && group.length === 1 && <div className="dashboard-widget-add-tile">
                <button type="button" aria-label={widget.type === 'heroInfo' ? 'ヒーローの情報を追加' : 'メモ等を追加'} onClick={() => addDashboardWidget(widget.type)}>
                  <Plus size={23}/><span>追加</span>
                </button>
              </div>}
'''
app = replace_once(app, old_add_tile, "", "ホーム上の別カード型追加枠")

# カード内から同じ種類の枠を追加可能にする。
app = replace_once(
    app,
    "                  onUpdate={updateDashboardWidget} onRemove={removeDashboardWidget} onOpenHistory={() => setPage('history')}",
    "                  onUpdate={updateDashboardWidget} onRemove={removeDashboardWidget} onAdd={addDashboardWidget} onOpenHistory={() => setPage('history')}",
    "カードへの追加処理の受け渡し"
)
app = replace_once(
    app,
    "  onRemove?: (id: string) => void\n  onOpenHistory: () => void",
    "  onRemove?: (id: string) => void\n  onAdd?: (type: DashboardWidgetType) => void\n  onOpenHistory: () => void",
    "カードの追加処理プロパティ"
)
app = replace_once(
    app,
    "function DashboardWidgetCard({ widget, carouselWidgets, store, currentRankState, sortedMatches, monthlyStats, editMode = false, onUpdate, onRemove, onOpenHistory, onDragStart, onDragMove, onDragEnd, onDragCancel }: DashboardWidgetCardProps)",
    "function DashboardWidgetCard({ widget, carouselWidgets, store, currentRankState, sortedMatches, monthlyStats, editMode = false, onUpdate, onRemove, onAdd, onOpenHistory, onDragStart, onDragMove, onDragEnd, onDragCancel }: DashboardWidgetCardProps)",
    "カードの追加処理受け取り"
)

old_hero_controls = '''      {canCarousel && <div className="widget-carousel-controls"><div className="widget-carousel-dots">{slides.map((item, index) => <button type="button" key={item.id} className={slideIndex === index ? 'active' : ''} aria-label={`${index + 1}体目を表示`} onClick={() => setSlideIndex(index)}/>)}</div><div className="widget-carousel-arrows"><button type="button" aria-label="前のヒーロー" onClick={() => changeSlide(-1)}><ChevronLeft size={16}/></button><span>{slideIndex + 1} / {slides.length}</span><button type="button" aria-label="次のヒーロー" onClick={() => changeSlide(1)}><ChevronRight size={16}/></button><button type="button" className="icon-button widget-carousel-remove" aria-label="表示中のヒーロー情報を削除" title="このヒーロー情報を削除" onClick={() => onRemove?.(currentSlide.id)}><Trash2 size={14}/></button></div></div>}
'''
new_hero_controls = '''      {(canCarousel || slides.length < 3) && <div className="widget-carousel-controls">
        <div className="widget-carousel-dots">{canCarousel ? slides.map((item, index) => <button type="button" key={item.id} className={slideIndex === index ? 'active' : ''} aria-label={`${index + 1}体目を表示`} onClick={() => setSlideIndex(index)}/>) : <span className="widget-carousel-dots-spacer"/>}</div>
        <div className="widget-carousel-arrows">
          {canCarousel && <><button type="button" aria-label="前のヒーロー" onClick={() => changeSlide(-1)}><ChevronLeft size={16}/></button><span>{slideIndex + 1} / {slides.length}</span><button type="button" aria-label="次のヒーロー" onClick={() => changeSlide(1)}><ChevronRight size={16}/></button><button type="button" className="icon-button widget-carousel-remove" aria-label="表示中のヒーロー情報を削除" title="このヒーロー情報を削除" onClick={() => onRemove?.(currentSlide.id)}><Trash2 size={14}/></button></>}
          {slides.length < 3 && <button type="button" className="widget-carousel-add" aria-label="ヒーローの情報を追加" title="ヒーローの情報を追加" onClick={() => onAdd?.('heroInfo')}><Plus size={15}/></button>}
        </div>
      </div>}
'''
app = replace_once(app, old_hero_controls, new_hero_controls, "ヒーロー情報カード内の追加ボタン")

old_note_controls = '''      {canCarousel && <div className="widget-carousel-controls"><div className="widget-carousel-dots">{slides.map((item, index) => <button type="button" key={item.id} className={slideIndex === index ? 'active' : ''} aria-label={`${index + 1}件目を表示`} onClick={() => setSlideIndex(index)}/>)}</div><div className="widget-carousel-arrows"><button type="button" aria-label="前のメモ" onClick={() => changeSlide(-1)}><ChevronLeft size={16}/></button><span>{slideIndex + 1} / {slides.length}</span><button type="button" aria-label="次のメモ" onClick={() => changeSlide(1)}><ChevronRight size={16}/></button><button type="button" className="icon-button widget-carousel-remove" aria-label="表示中のメモを削除" title="このメモを削除" onClick={() => onRemove?.(currentSlide.id)}><Trash2 size={14}/></button></div></div>}
'''
new_note_controls = '''      {(canCarousel || slides.length < 3) && <div className="widget-carousel-controls">
        <div className="widget-carousel-dots">{canCarousel ? slides.map((item, index) => <button type="button" key={item.id} className={slideIndex === index ? 'active' : ''} aria-label={`${index + 1}件目を表示`} onClick={() => setSlideIndex(index)}/>) : <span className="widget-carousel-dots-spacer"/>}</div>
        <div className="widget-carousel-arrows">
          {canCarousel && <><button type="button" aria-label="前のメモ" onClick={() => changeSlide(-1)}><ChevronLeft size={16}/></button><span>{slideIndex + 1} / {slides.length}</span><button type="button" aria-label="次のメモ" onClick={() => changeSlide(1)}><ChevronRight size={16}/></button><button type="button" className="icon-button widget-carousel-remove" aria-label="表示中のメモを削除" title="このメモを削除" onClick={() => onRemove?.(currentSlide.id)}><Trash2 size={14}/></button></>}
          {slides.length < 3 && <button type="button" className="widget-carousel-add" aria-label="メモを追加" title="メモを追加" onClick={() => onAdd?.('note')}><Plus size={15}/></button>}
        </div>
      </div>}
'''
app = replace_once(app, old_note_controls, new_note_controls, "メモカード内の追加ボタン")

css_marker = "/* HOME REPEATABLE WIDGETS + LOCAL DEMO MODE v1 */"
if css_marker not in css:
    raise SystemExit("修正を中止しました: CSSの追加位置が見つかりません。ファイルは変更していません。")
css_addition = '''

/* INLINE ADD CONTROL FOR REPEATABLE DASHBOARD CARDS */
.widget-carousel-dots-spacer { display: block; min-width: 1px; min-height: 8px; }
.widget-carousel-arrows .widget-carousel-add {
  display: grid;
  place-items: center;
  width: 29px;
  height: 28px;
  padding: 0;
  border: 1px dashed var(--accent-line, #2e6470);
  border-radius: 7px;
  background: var(--accent-soft, #14313a);
  color: var(--accent-strong, #35d4e4);
}
.widget-carousel-arrows .widget-carousel-add:hover {
  border-style: solid;
  border-color: var(--accent, #39e6f2);
  background: var(--surface-raised, #141f30);
}
'''
if "/* INLINE ADD CONTROL FOR REPEATABLE DASHBOARD CARDS */" not in css:
    css = css.rstrip() + "\n" + css_addition

if app == app_original and css == css_original:
    raise SystemExit("変更箇所がありません。ファイルは変更していません。")

backup_dir = ROOT / ".patch-backups"
backup_dir.mkdir(exist_ok=True)
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
app_backup = backup_dir / f"App.tsx.before-inline-widget-add-{stamp}.bak"
css_backup = backup_dir / f"style-improvements.css.before-inline-widget-add-{stamp}.bak"
shutil.copy2(APP, app_backup)
shutil.copy2(CSS, css_backup)
APP.write_text(app, encoding="utf-8")
CSS.write_text(css, encoding="utf-8")

print("修正を適用しました。")
print("- ヒーローの情報・メモ等は1件でも横2マス")
print("- ホーム上の独立した追加用カードを削除")
print("- 各カードの右下に＋ボタンを設置")
print("- ＋から同種カードを追加すると、2件目・3件目をスワイプ表示")
print("- 3件登録済みの場合は＋ボタンを非表示")
print(f"バックアップ: {app_backup.relative_to(ROOT)}")
print(f"バックアップ: {css_backup.relative_to(ROOT)}")
