"""読書データ分析（一時スクリプト）"""
import re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

DIARY = Path(r"C:\Documents\Obsidian Vault\Main Vault\日記")
books = {}

for f in sorted(DIARY.glob("*.md")):
    m = re.match(r'(\d{4}-\d{2}-\d{2})', f.stem)
    if not m:
        continue
    d = m.group(1)
    text = f.read_text(encoding='utf-8')
    in_r = False
    for line in text.splitlines():
        if '今日読んだ本' in line or '📚' in line:
            in_r = True
            continue
        if in_r:
            if line.strip().startswith('#') or (line.strip() and not line.strip().startswith('-')):
                break
            bm = re.search(r'\[\[(.+?)(?:\|.+?)?\]\]', line)
            if bm:
                title = bm.group(1)
                finished = '読了' in line
                if title not in books:
                    books[title] = {'first': d, 'last': d, 'finished': None, 'days_seen': 0}
                books[title]['last'] = d
                books[title]['days_seen'] += 1
                if finished:
                    books[title]['finished'] = d

finished_count = sum(1 for b in books.values() if b['finished'])
print(f"Total unique books: {len(books)}")
print(f"Finished: {finished_count}")
print()
for t, b in sorted(books.items(), key=lambda x: x[1]['first']):
    status = 'done:' + b['finished'] if b['finished'] else '...'
    print(f"{b['first']}~{b['last']} ({b['days_seen']}d) [{status}] {t}")
