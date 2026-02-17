"""
📈 月次トレンド比較レポート
月ごとの睡眠・運動・読書を前月比で比較し、Obsidianレポートを生成

使い方:
  python monthly_trend.py          # 最新月のレポート
  python monthly_trend.py 2026-01  # 指定月のレポート
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from datetime import datetime
from pathlib import Path
from collections import defaultdict

SCRIPT_DIR = Path(__file__).parent
VAULT_DIR = Path(r"C:\Documents\Obsidian Vault\Main Vault")

sys.path.insert(0, str(SCRIPT_DIR))
import life_dashboard as ld


def delta_str(current, previous, unit='', higher_is_better=True, is_pct=False):
    """変化量を↑↓矢印付きで表示"""
    if previous is None or previous == 0:
        return f"**{current}{unit}**（前月データなし）"
    diff = current - previous
    if is_pct:
        pct = diff
    else:
        pct = (diff / previous) * 100 if previous else 0
    
    if abs(diff) < 0.01:
        arrow = '→'
        color = '⚪'
    elif (diff > 0) == higher_is_better:
        arrow = '↑'
        color = '🟢'
    else:
        arrow = '↓'
        color = '🔴'
    
    sign = '+' if diff > 0 else ''
    if is_pct:
        return f"**{current}{unit}** {color}{arrow} {sign}{diff:.1f}pp"
    else:
        return f"**{current}{unit}** {color}{arrow} {sign}{diff:.1f}{unit}（{sign}{pct:.0f}%）"


def compute_month_stats(data, year_month):
    """指定月のデータを集計"""
    month_data = [d for d in data if d['date'][:7] == year_month]
    if not month_data:
        return None
    
    days = len(month_data)
    
    # 睡眠
    sleep_days = [d for d in month_data if d.get('hours')]
    hours = [d['hours'] for d in sleep_days]
    scores = [d['score'] for d in sleep_days if d.get('score')]
    bedtimes = [d.get('bedtime') for d in sleep_days if d.get('bedtime')]
    deep = [d['deep'] for d in sleep_days if d.get('deep')]
    
    avg_hours = sum(hours) / len(hours) if hours else 0
    avg_score = sum(scores) / len(scores) if scores else 0
    days_7h = sum(1 for h in hours if h >= 7)
    avg_deep = sum(deep) / len(deep) if deep else 0
    
    # 運動
    exercise_days = sum(1 for d in month_data if d.get('exercise'))
    
    # 歩数
    step_days = [d for d in month_data if d.get('steps')]
    avg_steps = sum(d['steps'] for d in step_days) / len(step_days) if step_days else 0
    
    # 読書
    books_touched = set()
    finished_titles = []
    for d in month_data:
        for b in d.get('books', []):
            books_touched.add(b['title'])
            if b.get('finished'):
                finished_titles.append(b['title'].split(' - ')[0])
    
    return {
        'month': year_month,
        'days': days,
        'sleep': {
            'avg_hours': round(avg_hours, 1),
            'avg_score': round(avg_score, 1),
            'days_7h': days_7h,
            'days_7h_pct': round(days_7h / len(sleep_days) * 100) if sleep_days else 0,
            'avg_deep': round(avg_deep, 1),
            'tracked': len(sleep_days),
        },
        'exercise': {
            'days': exercise_days,
            'rate': round(exercise_days / days * 100),
        },
        'steps': {
            'avg': round(avg_steps),
            'tracked': len(step_days),
        },
        'reading': {
            'touched': len(books_touched),
            'finished': len(finished_titles),
            'finished_titles': finished_titles,
        }
    }


def generate_trend_report(data, target_month=None):
    """月次トレンドレポートを生成"""
    # 全月を取得
    all_months = sorted(set(d['date'][:7] for d in data))
    
    if target_month is None:
        target_month = all_months[-1]
    
    idx = all_months.index(target_month) if target_month in all_months else -1
    if idx < 0:
        print(f"⚠️ {target_month} のデータがありません")
        return None, None
    
    current = compute_month_stats(data, target_month)
    previous = compute_month_stats(data, all_months[idx - 1]) if idx > 0 else None
    
    if not current:
        print(f"⚠️ {target_month} のデータがありません")
        return None, None
    
    c = current
    p = previous
    cs, ps = c['sleep'], p['sleep'] if p else {}
    ce, pe = c['exercise'], p['exercise'] if p else {}
    cst, pst = c['steps'], p['steps'] if p else {}
    cr, pr = c['reading'], p['reading'] if p else {}
    
    # ─── Obsidianレポート ───
    md = f"""---
tags: [月次トレンド, 自動生成]
month: {target_month}
---

# 📈 月次トレンド比較 {target_month}
"""
    if p:
        md += f"> **{target_month}** vs **{p['month']}** の比較\n\n"
    else:
        md += f"> **{target_month}** のデータ（前月比較なし）\n\n"
    
    # 睡眠
    md += "## 🌙 睡眠\n\n"
    md += "| 指標 | 今月 | 前月 | 変化 |\n|------|------|------|------|\n"
    
    def row(label, cur, prev, unit='', hib=True):
        prev_str = f"{prev}{unit}" if prev is not None else '—'
        if prev is not None:
            diff = cur - prev
            sign = '+' if diff > 0 else ''
            good = (diff > 0) == hib
            icon = '🟢' if good and abs(diff) > 0.01 else ('🔴' if not good and abs(diff) > 0.01 else '⚪')
            change = f"{icon} {sign}{diff:.1f}{unit}"
        else:
            change = '—'
        return f"| {label} | **{cur}{unit}** | {prev_str} | {change} |\n"
    
    md += row('平均睡眠', cs['avg_hours'], ps.get('avg_hours'), 'h')
    md += row('平均スコア', cs['avg_score'], ps.get('avg_score'), '点')
    md += row('7h以上達成率', cs['days_7h_pct'], ps.get('days_7h_pct'), '%')
    if cs['avg_deep']:
        md += row('平均深い睡眠', cs['avg_deep'], ps.get('avg_deep'), 'h')
    
    # 運動
    md += "\n## 💪 運動\n\n"
    md += "| 指標 | 今月 | 前月 | 変化 |\n|------|------|------|------|\n"
    md += row('筋トレ日数', ce['days'], pe.get('days'), '日')
    md += row('実施率', ce['rate'], pe.get('rate'), '%')
    
    # 歩数
    md += "\n## 🚶 歩数\n\n"
    md += "| 指標 | 今月 | 前月 | 変化 |\n|------|------|------|------|\n"
    
    avg_s = cst['avg']
    avg_p = pst.get('avg')
    prev_s = f"{avg_p:,}" if avg_p else '—'
    if avg_p and avg_p > 0:
        diff_s = avg_s - avg_p
        sign_s = '+' if diff_s > 0 else ''
        good_s = diff_s > 0
        icon_s = '🟢' if good_s and abs(diff_s) > 10 else ('🔴' if not good_s and abs(diff_s) > 10 else '⚪')
        change_s = f"{icon_s} {sign_s}{diff_s:,}歩"
    else:
        change_s = '—'
    md += f"| 平均歩数 | **{avg_s:,}歩** | {prev_s}歩 | {change_s} |\n"
    
    # 読書
    md += "\n## 📚 読書\n\n"
    md += "| 指標 | 今月 | 前月 | 変化 |\n|------|------|------|------|\n"
    md += row('読了冊数', cr['finished'], pr.get('finished'), '冊')
    md += row('読書中', cr['touched'], pr.get('touched'), '冊')
    
    if cr['finished_titles']:
        md += "\n### ✅ 今月の読了\n"
        for t in cr['finished_titles']:
            md += f"- {t}\n"
    
    # 総合評価
    md += "\n## 🏆 総合評価\n\n"
    if p:
        improvements = 0
        declines = 0
        
        checks = [
            (cs['avg_hours'], ps.get('avg_hours'), True),
            (cs['avg_score'], ps.get('avg_score'), True),
            (ce['days'], pe.get('days'), True),
            (cst['avg'], pst.get('avg'), True),
            (cr['finished'], pr.get('finished'), True),
        ]
        
        for cur, prev, _ in checks:
            if prev is not None and prev > 0:
                if cur > prev:
                    improvements += 1
                elif cur < prev:
                    declines += 1
        
        if improvements > declines:
            md += f"🟢 **全体的に改善** — {improvements}指標が向上、{declines}指標が低下\n"
        elif declines > improvements:
            md += f"🔴 **やや低下** — {declines}指標が低下、{improvements}指標が向上\n"
        else:
            md += f"⚪ **横ばい** — 大きな変化なし\n"
    
    md += f"\n---\n*自動生成: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n"
    
    return md, current


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    
    print("📈 月次トレンド比較レポート生成中...")
    data = ld.extract_all_data()
    
    md, current = generate_trend_report(data, target)
    if not md:
        return
    
    month = current['month']
    report_dir = VAULT_DIR / "月次トレンド"
    report_dir.mkdir(exist_ok=True)
    report_path = report_dir / f"月次トレンド_{month}.md"
    report_path.write_text(md, encoding='utf-8')
    print(f"   ✓ {report_path}")
    
    c = current
    print(f"\n   📊 {month} サマリー:")
    print(f"      🌙 睡眠: {c['sleep']['avg_hours']}h / スコア{c['sleep']['avg_score']}")
    print(f"      💪 筋トレ: {c['exercise']['days']}日（{c['exercise']['rate']}%）")
    print(f"      🚶 歩数: {c['steps']['avg']:,}歩")
    print(f"      📚 読了: {c['reading']['finished']}冊")
    
    print("\n✅ 完了！")


if __name__ == "__main__":
    main()
