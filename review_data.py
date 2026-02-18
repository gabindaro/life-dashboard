"""月次振り返り用データ抽出"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from life_dashboard import extract_all_data, generate_sleep_report

data = extract_all_data()

feb = [d for d in data if d['date'].startswith('2026-02')]
jan = [d for d in data if d['date'].startswith('2026-01')]

def show_month(name, entries):
    print(f"\n=== {name} ===")
    sl = [d for d in entries if d.get('hours')]
    ex = [d for d in entries if d.get('exercise')]
    books = [b['title'] for d in entries for b in d.get('books', []) if b.get('finished')]
    steps = [d['steps'] for d in entries if d.get('steps')]
    
    if sl:
        hrs = [d['hours'] for d in sl]
        scores = [d['score'] for d in sl if 'score' in d]
        print(f"  睡眠記録: {len(sl)}日")
        print(f"  平均睡眠: {sum(hrs)/len(hrs):.2f}h")
        print(f"  最長: {max(hrs):.1f}h / 最短: {min(hrs):.1f}h")
        if scores:
            print(f"  平均スコア: {sum(scores)/len(scores):.1f}")
        beds = [d for d in sl if d.get('bedtime')]
        if beds:
            def td(t):
                h, m = map(int, t.split(':'))
                return (h + 24 if h < 12 else h) + m / 60
            avg_bed = sum(td(d['bedtime']) for d in beds) / len(beds)
            h = int(avg_bed)
            m = int((avg_bed % 1) * 60)
            if h >= 24: h -= 24
            print(f"  平均就寝: {h}:{m:02d}")
    
    print(f"  筋トレ: {len(ex)}日")
    if steps:
        print(f"  歩数: {len(steps)}日, 平均{sum(steps)//len(steps):,}歩")
    print(f"  読了: {len(books)}冊")
    for b in books:
        print(f"    - {b}")

show_month("2月 (途中)", feb)
show_month("1月", jan)

print("\n=== 気分メモ（2月直近7日） ===")
for d in sorted(feb, key=lambda x: x['date'], reverse=True)[:7]:
    mood = d.get('mood', '')
    date = d['date']
    if mood:
        short = mood[:120].replace('\n', ' ')
        print(f"  {date}: {short}")

report = generate_sleep_report(data)
print("\n=== 改善点 ===")
for i in report.get('improvements', []):
    print(f"  - {i}")
streaks = report.get('streaks', {})
print(f"  7h+連続: {streaks.get('days_7h_plus', 0)}日")

# 2月日別データ
print("\n=== 2月の日別データ ===")
for d in sorted(feb, key=lambda x: x['date']):
    h = f"{d['hours']:.1f}h" if d.get('hours') else "---"
    s = str(d.get('score', '')) if d.get('score') else ''
    bed = d.get('bedtime', '')
    ex = '💪' if d.get('exercise') else '  '
    st = f"{d['steps']:,}" if d.get('steps') else ''
    bk = '📚' if d.get('books') else '  '
    print(f"  {d['date']}  {h:>6}  {s:>3}  {bed:>5}  {ex}  {st:>7}  {bk}")
