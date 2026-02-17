"""
デイリーノート自動生成スクリプト
Obsidianの日記テンプレートに基づいて今日のノートを生成する

機能:
  - 前日へのリンク ← [[YYYY-MM-DD]]
  - 未完了タスクの繰り越し
  - 天気の自動取得（wttr.in）
  - 曜日の自動計算

使い方:
  python daily_note.py          # 今日のノートを生成
  python daily_note.py --date 2026-02-20  # 指定日のノートを生成
"""

import re
import sys
import argparse
import urllib.request
from pathlib import Path
from datetime import datetime, timedelta

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

DIARY_DIR = Path(r"C:\Documents\Obsidian Vault\Main Vault\日記")

DAY_NAMES = ['月', '火', '水', '木', '金', '土', '日']


def get_weather() -> str:
    """wttr.inから東京の天気を取得"""
    try:
        url = "https://wttr.in/Tokyo?format=%t+%C&lang=ja"
        req = urllib.request.Request(url, headers={'User-Agent': 'curl/7.68.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            weather = resp.read().decode('utf-8').strip()
            return weather
    except Exception as e:
        print(f"  ⚠️ 天気取得失敗: {e}")
        return ""


def get_uncompleted_tasks(prev_path: Path) -> list[str]:
    """前日のノートから未完了タスクを取得"""
    if not prev_path.exists():
        return []
    
    text = prev_path.read_text(encoding='utf-8')
    tasks = []
    for line in text.splitlines():
        # - [ ] で始まるタスクを取得
        stripped = line.strip()
        if stripped.startswith('- [ ]') and len(stripped) > 6:
            tasks.append(stripped)
    
    return tasks


def generate_note(target_date: datetime) -> str:
    """デイリーノートを生成"""
    date_str = target_date.strftime('%Y-%m-%d')
    month_str = target_date.strftime('%Y-%m')
    dow = DAY_NAMES[target_date.weekday()]
    
    # 前日
    prev_date = target_date - timedelta(days=1)
    prev_str = prev_date.strftime('%Y-%m-%d')
    
    # 天気取得
    weather = get_weather()
    
    # 未完了タスク繰り越し
    prev_path = DIARY_DIR / f"{prev_str}.md"
    uncompleted = get_uncompleted_tasks(prev_path)
    
    # ノート生成
    lines = [
        "---",
        f"date: {date_str}",
        "type: daily-note",
        "tags:",
        "  - daily",
        f'  - "#{month_str}"',
        f'  - "#{date_str}"',
        'sleep: ""',
        "行ったところ:",
        "  - ",
        "スクワット: ",
        "腹筋: ",
        "腕立て伏せ: ",
        "---",
        f"###### 🗓️ [[{date_str}]] ({dow})　← [[{prev_str}]]",
        "",
        "###### 🌅 朝のチェックイン",
        f"- 起床時刻::{prev_str} 就寝〜起床",
        f"- 気分::",
        f"- 天気::{weather}",
        "- 歩数::",
        "###### 📚 今日読んだ本",
        "- ",
        "",
        "###### 🍚",
        "- 朝、",
        "- 昼、",
        "- 夜、",
        "",
        "",
        "###### 📝 今日すること・あったこと",
        "- [[今日の学び]]",
        "- [[📒読書ノート]]",
        "- [[買う食料・日用品]]",
        "- [[すること]]",
        "- [[欲しいもの]]",
    ]
    
    # 未完了タスク繰り越し
    if uncompleted:
        lines.append(f"- **⬇️ 前日から繰り越し:**")
        for task in uncompleted:
            lines.append(f"  {task}")
    
    lines.append("")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="デイリーノート自動生成")
    parser.add_argument("--date", type=str, help="生成する日付 (YYYY-MM-DD)")
    args = parser.parse_args()
    
    if args.date:
        target = datetime.strptime(args.date, '%Y-%m-%d')
    else:
        target = datetime.now()
    
    date_str = target.strftime('%Y-%m-%d')
    dow = DAY_NAMES[target.weekday()]
    filepath = DIARY_DIR / f"{date_str}.md"
    
    print(f"📝 デイリーノート生成: {date_str} ({dow})")
    
    if filepath.exists():
        print(f"  ⚠️ {filepath.name} は既に存在します。上書きしますか？")
        answer = input("  [y/N] >> ").strip().lower()
        if answer != 'y':
            print("  スキップしました。")
            return
    
    # 前日チェック
    prev_date = target - timedelta(days=1)
    prev_path = DIARY_DIR / f"{prev_date.strftime('%Y-%m-%d')}.md"
    uncompleted = get_uncompleted_tasks(prev_path)
    if uncompleted:
        print(f"  📋 前日から繰り越すタスク: {len(uncompleted)}件")
        for t in uncompleted:
            print(f"     {t}")
    
    note = generate_note(target)
    filepath.write_text(note, encoding='utf-8')
    print(f"  ✓ 保存: {filepath}")
    print(f"  🔗 前日リンク: ← [[{prev_date.strftime('%Y-%m-%d')}]]")


if __name__ == "__main__":
    main()
