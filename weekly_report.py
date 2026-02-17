"""
週次レポート自動生成スクリプト
毎週月曜に実行し、先週のサマリーをObsidianに保存 + ダッシュボードを再生成する

使い方:
  python weekly_report.py
"""
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')


SCRIPT_DIR = Path(__file__).parent
VAULT_DIR = Path(r"C:\Documents\Obsidian Vault\Main Vault")


def get_week_range():
    """先週の月曜〜日曜の範囲を返す"""
    today = datetime.now()
    # 先週の月曜日
    last_monday = today - timedelta(days=today.weekday() + 7)
    last_sunday = last_monday + timedelta(days=6)
    return last_monday, last_sunday


def generate_weekly_summary():
    """life_dashboard.pyのデータ抽出機能を流用して週次サマリーを生成"""
    # life_dashboard.pyのextract_all_data()を呼ぶ
    sys.path.insert(0, str(SCRIPT_DIR))
    import life_dashboard as ld

    data = ld.extract_all_data()
    last_monday, last_sunday = get_week_range()

    # 先週のデータをフィルタ
    week_data = [
        d for d in data
        if last_monday.strftime('%Y-%m-%d') <= d['date'] <= last_sunday.strftime('%Y-%m-%d')
    ]

    if not week_data:
        print("⚠️ 先週のデータがありません")
        return None

    # 睡眠統計
    sleep_days = [d for d in week_data if d.get('hours')]
    sleep_hours = [d['hours'] for d in sleep_days]
    sleep_scores = [d['score'] for d in sleep_days if d.get('score')]
    
    avg_hours = sum(sleep_hours) / len(sleep_hours) if sleep_hours else 0
    avg_score = sum(sleep_scores) / len(sleep_scores) if sleep_scores else 0
    
    # 運動
    exercise_days = sum(1 for d in week_data if d.get('exercise'))
    
    # 歩数
    step_days = [d for d in week_data if d.get('steps')]
    avg_steps = sum(d['steps'] for d in step_days) / len(step_days) if step_days else 0
    
    # 読書
    books_read = set()
    finished_books = []
    for d in week_data:
        for b in d.get('books', []):
            books_read.add(b['title'])
            if b.get('finished'):
                finished_books.append(b['title'])

    # 最高/最低の日
    best_day = max(sleep_days, key=lambda d: d.get('score', 0)) if sleep_days else None
    worst_day = min(sleep_days, key=lambda d: d.get('score', 100)) if sleep_days else None

    return {
        'period': f"{last_monday.strftime('%Y-%m-%d')} 〜 {last_sunday.strftime('%Y-%m-%d')}",
        'week_num': last_monday.isocalendar()[1],
        'year': last_monday.year,
        'days': len(week_data),
        'sleep': {
            'avg_hours': round(avg_hours, 1),
            'avg_score': round(avg_score, 1) if avg_score else None,
            'best': {'date': best_day['date'], 'score': best_day.get('score'), 'hours': best_day['hours']} if best_day else None,
            'worst': {'date': worst_day['date'], 'score': worst_day.get('score'), 'hours': worst_day['hours']} if worst_day else None,
            'days_7h_plus': sum(1 for h in sleep_hours if h >= 7),
        },
        'exercise': {
            'days': exercise_days,
        },
        'steps': {
            'avg': round(avg_steps),
            'days_tracked': len(step_days),
        },
        'reading': {
            'books_touched': len(books_read),
            'finished': finished_books,
        },
    }


def format_report(summary):
    """サマリーをObsidianマークダウンに整形"""
    s = summary
    sl = s['sleep']
    
    md = f"""---
tags: [週次レポート, 自動生成]
week: {s['week_num']}
year: {s['year']}
---

# 📊 週次レポート W{s['week_num']}
**{s['period']}**

## 🌙 睡眠
| 項目 | 値 |
|------|-----|
| 平均睡眠 | **{sl['avg_hours']}h** |
| 平均スコア | **{sl['avg_score'] or '—'}** |
| 7h以上の日 | {sl['days_7h_plus']}/{s['days']}日 |
"""
    if sl['best']:
        md += f"| ベスト | {sl['best']['date']} ({sl['best']['hours']}h, スコア{sl['best']['score']}) |\n"
    if sl['worst']:
        md += f"| ワースト | {sl['worst']['date']} ({sl['worst']['hours']}h, スコア{sl['worst']['score']}) |\n"

    md += f"""
## 💪 運動
- 筋トレ: **{s['exercise']['days']}日** / {s['days']}日

## 🚶 歩数
- 平均: **{s['steps']['avg']:,}歩**（{s['steps']['days_tracked']}日計測）

## 📚 読書
- 読んだ本: **{s['reading']['books_touched']}冊**
"""
    if s['reading']['finished']:
        md += "- 読了:\n"
        for b in s['reading']['finished']:
            md += f"  - ✅ {b}\n"

    md += f"""
---
*自動生成: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
    return md


def main():
    print("📊 週次レポート生成中...")
    
    # 1. ダッシュボード再生成
    print("   🎨 ダッシュボード再生成...")
    result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "life_dashboard.py")],
        cwd=str(SCRIPT_DIR),
        capture_output=True, text=True, encoding='utf-8'
    )
    if result.returncode != 0:
        print(f"   ⚠️ ダッシュボード生成エラー: {result.stderr}")
    else:
        print("   ✓ ダッシュボード更新完了")

    # 2. 週次サマリー生成
    print("   📝 週次サマリー生成...")
    summary = generate_weekly_summary()
    if not summary:
        return

    # 3. Obsidianに保存
    report_md = format_report(summary)
    report_path = VAULT_DIR / f"週次レポート_W{summary['week_num']}_{summary['year']}.md"
    report_path.write_text(report_md, encoding='utf-8')
    print(f"   ✓ {report_path}")

    # 4. サマリー表示
    sl = summary['sleep']
    print(f"\n   📊 W{summary['week_num']} サマリー:")
    print(f"      🌙 睡眠: 平均{sl['avg_hours']}h / スコア{sl['avg_score']}")
    print(f"      💪 筋トレ: {summary['exercise']['days']}日")
    print(f"      🚶 歩数: 平均{summary['steps']['avg']:,}歩")
    print(f"      📚 読書: {summary['reading']['books_touched']}冊")
    if summary['reading']['finished']:
        print(f"      ✅ 読了: {', '.join(summary['reading']['finished'])}")

    print("\n✅ 週次レポート完了！")


if __name__ == "__main__":
    main()
