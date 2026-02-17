"""
自動化スクリプト:
1. Garmin Connectから前日の歩数を取得→日記に書き込み
2. 日記の📚セクション→📒読書ノートへ自動転記
"""

import re
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = Path(__file__).parent
load_dotenv(SCRIPT_DIR / '.env')

DIARY_DIR = Path(r"C:\Documents\Obsidian Vault\Main Vault\日記")
READING_NOTE = Path(r"C:\Documents\Obsidian Vault\Main Vault\📚_読書メモ\📒読書ノート.md")


# =====================================================
# 1. Garmin歩数取得
# =====================================================

def fetch_garmin_steps(date_str: str) -> int | None:
    """Garmin Connectから指定日の歩数を取得"""
    email = os.getenv('GARMIN_EMAIL', '')
    password = os.getenv('GARMIN_PASSWORD', '')

    if not email or not password or 'ここに' in email:
        print("   ⚠️ .envファイルにGarminのログイン情報を設定してください")
        return None

    try:
        from garminconnect import Garmin
        client = Garmin(email, password)
        client.login()

        # 日別サマリーから歩数取得
        stats = client.get_stats(date_str)
        steps = stats.get('totalSteps', 0)
        return steps
    except Exception as e:
        print(f"   ⚠️ Garmin接続エラー: {e}")
        return None


def update_diary_steps(date_str: str, steps: int) -> bool:
    """日記ファイルに歩数を書き込み（既に記載がなければ）"""
    diary_file = DIARY_DIR / f"{date_str}.md"
    if not diary_file.exists():
        print(f"   ⚠️ 日記ファイルが見つかりません: {diary_file.name}")
        return False

    text = diary_file.read_text(encoding='utf-8')

    # 既に歩数が記載されていたらスキップ
    if re.search(r'歩数::\s*[\d,]+\s*歩', text):
        existing = re.search(r'歩数::\s*([\d,]+)\s*歩', text)
        print(f"   → {date_str}: 既に記載あり ({existing.group(1)}歩)")
        return False

    # 歩数::の行を探して更新、なければ適切な場所に追加
    steps_formatted = f"{steps:,}"

    if '歩数::' in text:
        # 空の歩数フィールドがある場合は埋める
        text = re.sub(r'歩数::\s*$', f'歩数:: {steps_formatted}歩', text, flags=re.MULTILINE)
        text = re.sub(r'歩数::\s*\n', f'歩数:: {steps_formatted}歩\n', text)
    else:
        # 気分::の後に追加
        if '気分::' in text:
            text = re.sub(r'(気分::.+?\n)', r'\1' + f'歩数:: {steps_formatted}歩\n', text)
        else:
            # 本文の先頭あたりに追加
            text = text + f'\n歩数:: {steps_formatted}歩\n'

    diary_file.write_text(text, encoding='utf-8')
    print(f"   ✓ {date_str}: {steps_formatted}歩 を書き込み")
    return True


def sync_garmin_steps():
    """前日の歩数を取得して日記に書き込む"""
    print("\n🦶 Garmin歩数を取得中...")
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    steps = fetch_garmin_steps(yesterday)
    if steps is not None:
        update_diary_steps(yesterday, steps)
    else:
        print("   → 歩数の取得をスキップしました")


# =====================================================
# 1b. Garminランニング取得
# =====================================================

def fetch_garmin_activities(date_str: str) -> list[dict]:
    """Garmin Connectから指定日のランニングアクティビティを取得"""
    email = os.getenv('GARMIN_EMAIL', '')
    password = os.getenv('GARMIN_PASSWORD', '')

    if not email or not password or 'ここに' in email:
        return []

    try:
        from garminconnect import Garmin
        client = Garmin(email, password)
        client.login()

        # 直近のアクティビティを取得
        activities = client.get_activities_by_date(date_str, date_str)
        runs = []
        for a in activities:
            atype = a.get('activityType', {}).get('typeKey', '')
            if 'running' in atype.lower() or 'ランニング' in a.get('activityName', ''):
                run = {
                    'name': a.get('activityName', 'ランニング'),
                    'distance_km': round(a.get('distance', 0) / 1000, 2),
                    'duration_min': round(a.get('duration', 0) / 60, 1),
                    'avg_pace': '',
                    'calories': a.get('calories', 0),
                    'avg_hr': a.get('averageHR', 0),
                }
                # ペース計算 (min/km)
                if run['distance_km'] > 0 and run['duration_min'] > 0:
                    pace = run['duration_min'] / run['distance_km']
                    pace_min = int(pace)
                    pace_sec = int((pace - pace_min) * 60)
                    run['avg_pace'] = f"{pace_min}'{pace_sec:02d}\""
                runs.append(run)
        return runs
    except Exception as e:
        print(f"   ⚠️ Garminアクティビティ取得エラー: {e}")
        return []


def update_diary_running(date_str: str, runs: list[dict]) -> bool:
    """日記ファイルにランニング記録を書き込み"""
    diary_file = DIARY_DIR / f"{date_str}.md"
    if not diary_file.exists():
        return False

    text = diary_file.read_text(encoding='utf-8')

    # 既にランニング記録があればスキップ
    if 'ランニング::' in text or '🏃' in text:
        print(f"   → {date_str}: ランニング記録は既に記載あり")
        return False

    # ランニング記録を組み立て
    run_lines = []
    for r in runs:
        parts = [f"{r['distance_km']}km", f"{r['duration_min']}分"]
        if r['avg_pace']:
            parts.append(f"ペース{r['avg_pace']}/km")
        if r['avg_hr']:
            parts.append(f"❤️{r['avg_hr']}bpm")
        run_lines.append(f"- 🏃 ランニング:: {' / '.join(parts)}")

    if not run_lines:
        return False

    run_text = '\n'.join(run_lines)

    # 歩数::の後、または朝のチェックインセクションに挿入
    if '歩数::' in text:
        text = re.sub(r'(歩数::.+?\n)', r'\1' + run_text + '\n', text)
    elif '📚 今日読んだ本' in text:
        text = text.replace('📚 今日読んだ本', run_text + '\n###### 📚 今日読んだ本')
    else:
        text = text.rstrip() + '\n' + run_text + '\n'

    diary_file.write_text(text, encoding='utf-8')
    for r in runs:
        print(f"   ✓ {date_str}: 🏃 {r['distance_km']}km / {r['duration_min']}分 / {r['avg_pace']}/km")
    return True


def sync_garmin_running():
    """前日のランニングアクティビティを取得して日記に書き込む"""
    print("\n🏃 Garminランニング記録を取得中...")
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    runs = fetch_garmin_activities(yesterday)
    if runs:
        update_diary_running(yesterday, runs)
    else:
        print("   → ランニング記録なし")



# =====================================================
# 2. 読書ノート自動転記
# =====================================================

def get_last_reading_note_date() -> str | None:
    """📒読書ノートの最後の日付エントリを取得"""
    if not READING_NOTE.exists():
        return None

    text = READING_NOTE.read_text(encoding='utf-8')
    dates = re.findall(r'\[\[(\d{4}-\d{2}-\d{2})\]\]', text)
    return dates[-1] if dates else None


def extract_reading_from_diary(date_str: str) -> list[str]:
    """日記ファイルから📚セクションの行を抽出"""
    diary_file = DIARY_DIR / f"{date_str}.md"
    if not diary_file.exists():
        return []

    text = diary_file.read_text(encoding='utf-8')
    lines = []
    in_reading = False

    for line in text.splitlines():
        if '今日読んだ本' in line or '📚' in line:
            in_reading = True
            continue
        if in_reading:
            # セクション終了の判定
            if line.strip().startswith('######') or line.strip() == '---':
                break
            stripped = line.strip()
            if stripped and stripped != '-':
                lines.append(line.rstrip())

    return lines


def sync_reading_notes():
    """日記の読書データを📒読書ノートに転記"""
    print("\n📚 読書ノートを同期中...")

    last_date = get_last_reading_note_date()
    if not last_date:
        print("   ⚠️ 読書ノートの既存データが見つかりません")
        return

    print(f"   → 最終エントリ: {last_date}")

    # 翌日から今日までの日記を探す
    start = datetime.strptime(last_date, '%Y-%m-%d') + timedelta(days=1)
    today = datetime.now()

    new_entries = []
    added_dates = 0

    current = start
    while current <= today:
        date_str = current.strftime('%Y-%m-%d')
        reading_lines = extract_reading_from_diary(date_str)

        if reading_lines:
            new_entries.append(f"\n[[{date_str}]]")
            for line in reading_lines:
                new_entries.append(line)
            added_dates += 1

        current += timedelta(days=1)

    if not new_entries:
        print("   → 新しいエントリはありません")
        return

    # 読書ノートに追記
    text = READING_NOTE.read_text(encoding='utf-8')
    text = text.rstrip() + '\n' + '\n'.join(new_entries) + '\n'
    READING_NOTE.write_text(text, encoding='utf-8')
    print(f"   ✓ {added_dates}日分のエントリを追加しました")


# =====================================================
# メイン
# =====================================================

if __name__ == "__main__":
    sync_garmin_steps()
    sync_garmin_running()
    sync_reading_notes()
    print("\n✅ 自動化処理完了！")
