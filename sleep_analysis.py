"""
🧠 睡眠相関分析
9ヶ月の日記データから「何が睡眠に一番影響してるか」を見つける
睡眠時間（200日分）をメイン指標、スコア（57日分）をサブ指標として使用
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from datetime import datetime
from pathlib import Path
from collections import defaultdict
import statistics

SCRIPT_DIR = Path(__file__).parent
VAULT_DIR = Path(r"C:\Documents\Obsidian Vault\Main Vault")

sys.path.insert(0, str(SCRIPT_DIR))
import life_dashboard as ld


def avg(lst):
    return statistics.mean(lst) if lst else 0

def fmt_compare(label, group_a, group_b, name_a, name_b, higher_is_better=True):
    """2グループの睡眠時間（+あればスコア）を比較して文字列を返す"""
    ha = avg([d['hours'] for d in group_a])
    hb = avg([d['hours'] for d in group_b])
    
    result = f'{name_a} **{ha:.1f}h** / {name_b} **{hb:.1f}h**'
    
    # Score if available in both
    sa_list = [d['score'] for d in group_a if d.get('score')]
    sb_list = [d['score'] for d in group_b if d.get('score')]
    if len(sa_list) >= 3 and len(sb_list) >= 3:
        sa, sb = avg(sa_list), avg(sb_list)
        result += f'（スコア: {sa:.0f} vs {sb:.0f}）'
    
    return result, abs(ha - hb)


def analyze():
    print("🧠 睡眠相関分析中...\n")
    data = ld.extract_all_data()
    
    sleep_data = [d for d in data if d.get('hours')]
    scored_data = [d for d in sleep_data if d.get('score')]
    print(f"  📊 分析対象: {len(sleep_data)}日分（うちスコアあり {len(scored_data)}日）\n")
    
    findings = []
    
    # ─── 1. 就寝時刻 vs 睡眠 ───
    bedtime_data = []
    for d in sleep_data:
        if d.get('bedtime'):
            try:
                bt = float(d['bedtime'])
                bedtime_data.append((d, bt))
            except (ValueError, TypeError):
                pass
    
    if bedtime_data:
        early = [d for d, bt in bedtime_data if bt <= 23.0]
        mid = [d for d, bt in bedtime_data if 23.0 < bt <= 24.0]
        late = [d for d, bt in bedtime_data if bt > 24.0]
        
        eh, mh, lh = avg([d['hours'] for d in early]), avg([d['hours'] for d in mid]), avg([d['hours'] for d in late])
        
        score_info = ''
        es = [d['score'] for d in early if d.get('score')]
        ls = [d['score'] for d in late if d.get('score')]
        if len(es) >= 3 and len(ls) >= 3:
            score_info = f'\n  スコア: 23時前 **{avg(es):.0f}**点 / 24時以降 **{avg(ls):.0f}**点'
        
        findings.append({
            'title': '⏰ 就寝時刻 vs 睡眠時間',
            'insight': f'23時前 **{eh:.1f}h**（{len(early)}日）/ 23-24時 **{mh:.1f}h**（{len(mid)}日）/ 24時以降 **{lh:.1f}h**（{len(late)}日）{score_info}',
            'detail': '',
            'impact': abs(eh - lh),
            'recommendation': '早く寝るほど長く眠れる' if eh > lh else '就寝時刻と睡眠時間の関連は薄い',
        })
    
    # ─── 2. 筋トレ vs 睡眠 ───
    ex_days = [d for d in sleep_data if d.get('exercise')]
    no_ex_days = [d for d in sleep_data if not d.get('exercise')]
    
    if ex_days and no_ex_days:
        result, impact = fmt_compare('筋トレ', ex_days, no_ex_days, '筋トレした日', 'しなかった日')
        findings.append({
            'title': '💪 筋トレ vs 睡眠',
            'insight': result,
            'detail': f'（{len(ex_days)}日 vs {len(no_ex_days)}日）',
            'impact': impact,
            'recommendation': '筋トレをすると睡眠時間が増える' if avg([d['hours'] for d in ex_days]) > avg([d['hours'] for d in no_ex_days]) else '筋トレは睡眠時間に大きく影響しない',
        })
    
    # ─── 3. 歩数 vs 睡眠 ───
    step_sleep = [d for d in sleep_data if d.get('steps')]
    if len(step_sleep) >= 10:
        step_sleep.sort(key=lambda d: d['steps'])
        n = len(step_sleep)
        low = step_sleep[:n//3]
        mid = step_sleep[n//3:2*n//3]
        high = step_sleep[2*n//3:]
        
        lh = avg([d['hours'] for d in low])
        mh = avg([d['hours'] for d in mid])
        hh = avg([d['hours'] for d in high])
        la = avg([d['steps'] for d in low])
        ha = avg([d['steps'] for d in high])
        
        findings.append({
            'title': '🚶 歩数 vs 睡眠',
            'insight': f'歩数少（{la:.0f}歩）**{lh:.1f}h** / 中 **{mh:.1f}h** / 歩数多（{ha:.0f}歩）**{hh:.1f}h**',
            'detail': f'（各{len(low)}/{len(mid)}/{len(high)}日）',
            'impact': abs(hh - lh),
            'recommendation': 'よく歩いた日は長く眠れる' if hh > lh else '歩数は睡眠時間に大きく影響しない',
        })
    
    # ─── 4. 曜日 vs 睡眠 ───
    dow_hours = defaultdict(list)
    dow_names = ['月', '火', '水', '木', '金', '土', '日']
    for d in sleep_data:
        dow = datetime.strptime(d['date'], '%Y-%m-%d').weekday()
        dow_hours[dow].append(d['hours'])
    
    dow_avg = {}
    for i in range(7):
        if i in dow_hours:
            dow_avg[dow_names[i]] = avg(dow_hours[i])
    
    best_dow = max(dow_avg, key=dow_avg.get)
    worst_dow = min(dow_avg, key=dow_avg.get)
    
    findings.append({
        'title': '📅 曜日 vs 睡眠時間',
        'insight': f'ベスト: **{best_dow}曜 {dow_avg[best_dow]:.1f}h** / ワースト: **{worst_dow}曜 {dow_avg[worst_dow]:.1f}h**',
        'detail': ' / '.join(f'{d}:{dow_avg[d]:.1f}h' for d in dow_names if d in dow_avg),
        'impact': dow_avg[best_dow] - dow_avg[worst_dow],
        'recommendation': f'{worst_dow}曜の睡眠が短い傾向。原因を探ろう',
    })
    
    # ─── 5. 前日の睡眠 → 翌日の睡眠 ───
    consecutive = []
    for i in range(1, len(data)):
        prev = data[i-1]
        curr = data[i]
        if prev.get('hours') and curr.get('hours'):
            d1 = datetime.strptime(prev['date'], '%Y-%m-%d')
            d2 = datetime.strptime(curr['date'], '%Y-%m-%d')
            if (d2 - d1).days == 1:
                consecutive.append((prev['hours'], curr['hours']))
    
    if len(consecutive) >= 10:
        consecutive.sort(key=lambda x: x[0])
        n = len(consecutive)
        short_prev = consecutive[:n//3]
        long_prev = consecutive[2*n//3:]
        
        short_next = avg([h for _, h in short_prev])
        long_next = avg([h for _, h in long_prev])
        short_hrs = avg([h for h, _ in short_prev])
        long_hrs = avg([h for h, _ in long_prev])
        
        findings.append({
            'title': '🔄 前日の睡眠 → 翌日の睡眠',
            'insight': f'前日短め（{short_hrs:.1f}h）→ 翌日 **{short_next:.1f}h** / 前日長め（{long_hrs:.1f}h）→ 翌日 **{long_next:.1f}h**',
            'detail': f'（各{len(short_prev)}/{len(long_prev)}ペア）',
            'impact': abs(long_next - short_next),
            'recommendation': '前日寝不足だと翌日は多く眠る（リバウンド効果）' if short_next > long_next else '前日の睡眠時間は翌日に影響する',
        })
    
    # ─── 6. 読書 vs 睡眠 ───
    read_days = [d for d in sleep_data if d.get('books')]
    no_read_days = [d for d in sleep_data if not d.get('books')]
    
    if read_days and no_read_days:
        result, impact = fmt_compare('読書', read_days, no_read_days, '読書した日', 'しなかった日')
        
        many = [d for d in read_days if len(d['books']) >= 3]
        detail = f'3冊以上読んだ日: **{avg([d["hours"] for d in many]):.1f}h**（{len(many)}日）' if many else ''
        
        findings.append({
            'title': '📚 読書 vs 睡眠',
            'insight': result,
            'detail': detail,
            'impact': impact,
            'recommendation': '読書する日は睡眠時間が長い' if avg([d['hours'] for d in read_days]) > avg([d['hours'] for d in no_read_days]) else '読書と睡眠の直接的な相関は薄い',
        })
    
    # ─── 7. 睡眠時間帯分布 ───
    hour_buckets = defaultdict(list)
    for d in sleep_data:
        h = d['hours']
        if h < 5: bucket = '5h未満'
        elif h < 6: bucket = '5-6h'
        elif h < 7: bucket = '6-7h'
        elif h < 8: bucket = '7-8h'
        elif h < 9: bucket = '8-9h'
        else: bucket = '9h以上'
        hour_buckets[bucket].append(d)
    
    bucket_order = ['5h未満', '5-6h', '6-7h', '7-8h', '8-9h', '9h以上']
    bucket_info = []
    for b in bucket_order:
        if b in hour_buckets:
            n = len(hour_buckets[b])
            pct = n / len(sleep_data) * 100
            scores = [d['score'] for d in hour_buckets[b] if d.get('score')]
            score_str = f'（スコア平均{avg(scores):.0f}）' if len(scores) >= 3 else ''
            bucket_info.append(f'{b}: {n}日（{pct:.0f}%）{score_str}')
    
    most_common = max(hour_buckets.items(), key=lambda x: len(x[1]))
    
    findings.append({
        'title': '⏱️ 睡眠時間帯の分布',
        'insight': f'最も多い時間帯: **{most_common[0]}**（{len(most_common[1])}日 / {len(most_common[1])/len(sleep_data)*100:.0f}%）',
        'detail': ' / '.join(bucket_info),
        'impact': 8,
        'recommendation': f'あなたのメイン睡眠ゾーンは {most_common[0]}',
    })
    
    # ─── 8. 月別トレンド ───
    monthly_hours = defaultdict(list)
    for d in sleep_data:
        monthly_hours[d['date'][:7]].append(d['hours'])
    
    monthly_avg = {m: avg(hours) for m, hours in monthly_hours.items()}
    months_sorted = sorted(monthly_avg.keys())
    
    if len(months_sorted) >= 4:
        first_half = avg([monthly_avg[m] for m in months_sorted[:len(months_sorted)//2]])
        last_half = avg([monthly_avg[m] for m in months_sorted[len(months_sorted)//2:]])
        trend = 'improving' if last_half > first_half else 'declining'
    
        findings.append({
            'title': '📈 睡眠時間の長期トレンド',
            'insight': f'前半平均 **{first_half:.1f}h** → 後半平均 **{last_half:.1f}h**',
            'detail': ' / '.join(f'{m}: {monthly_avg[m]:.1f}h' for m in months_sorted),
            'impact': abs(last_half - first_half),
            'recommendation': '睡眠時間は改善傾向！' if trend == 'improving' else '睡眠時間が減少傾向。注意。',
        })
    
    # ─── Sort by impact ───
    findings.sort(key=lambda f: f['impact'], reverse=True)
    
    # ─── Generate report ───
    md = f"""---
tags: [自己分析, 睡眠, 相関分析]
generated: {datetime.now().strftime('%Y-%m-%d')}
---

# 🧠 睡眠相関分析

> **{len(sleep_data)}日分**のデータから「何があなたの睡眠に最も影響しているか」を分析
> （スコアデータは {len(scored_data)}日分で補助的に使用）

## 🏆 インパクト順の発見

"""
    for i, f in enumerate(findings, 1):
        md += f"### {i}. {f['title']}\n\n"
        md += f"{f['insight']}\n\n"
        if f['detail']:
            md += f"_{f['detail']}_\n\n"
        md += f"**💡 {f['recommendation']}**\n\n---\n\n"
    
    md += f"\n*自動生成: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n"
    
    report_path = VAULT_DIR / "睡眠相関分析.md"
    report_path.write_text(md, encoding='utf-8')
    print(f"  ✓ レポート: {report_path}\n")
    
    print("  🏆 インパクト順:")
    for i, f in enumerate(findings, 1):
        clean = f['insight'].replace('**', '')
        print(f"    {i}. {f['title']}")
        print(f"       {clean}")
        print(f"       → {f['recommendation']}")
        print()
    
    print("✅ 完了！")


if __name__ == "__main__":
    analyze()
