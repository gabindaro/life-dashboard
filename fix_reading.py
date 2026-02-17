"""
読了マーク修正スクリプト
日記本文で「読了」と書かれている本を、📚セクションの行にも「読了」を追加する。
また、本文中で「読み終えた」と書かれている場合も検出する。
"""
import re, sys
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

DIARY = Path(r"C:\Documents\Obsidian Vault\Main Vault\日記")
DRY_RUN = '--dry-run' in sys.argv

def find_reading_section(lines):
    """📚セクションの開始行と終了行を返す"""
    start = None
    for i, line in enumerate(lines):
        if '今日読んだ本' in line or '📚' in line:
            start = i
            continue
        if start is not None:
            if line.strip().startswith('#') or (line.strip() and not line.strip().startswith('-')):
                return start, i
    if start is not None:
        return start, len(lines)
    return None, None

def find_book_in_reading_section(lines, start, end, title):
    """📚セクション内で特定の本のある行番号を返す"""
    for i in range(start, end):
        if title in lines[i]:
            return i
    return None

def check_body_for_dokuryo(lines, title, rs_start, rs_end):
    """本文中で本タイトルと同じ行に読了があるか（📚セクション外のみ）"""
    for i, line in enumerate(lines):
        # Skip reading section itself
        if rs_start <= i < rs_end:
            continue
        # Must have book title AND 読了/読み終え on SAME line
        if title in line and ('読了' in line or '読み終え' in line):
            # Exclude "読了済み" (means previously finished, not this book)
            if '読了済み' in line:
                continue
            return True, i
    return False, -1

def main():
    total_fixes = 0
    fix_details = []
    
    for f in sorted(DIARY.glob("*.md")):
        m = re.match(r'(\d{4}-\d{2}-\d{2})', f.stem)
        if not m:
            continue
        date = m.group(1)
        text = f.read_text(encoding='utf-8')
        lines = text.splitlines()
        
        rs_start, rs_end = find_reading_section(lines)
        if rs_start is None:
            continue
        
        modified = False
        
        # Get all books from reading section
        for i in range(rs_start, rs_end):
            bm = re.search(r'\[\[(.+?)(?:\|.+?)?\]\]', lines[i])
            if not bm:
                continue
            title = bm.group(1)
            
            # Already marked as 読了?
            if '読了' in lines[i]:
                continue
            
            # Check body text for 読了 mention of this book
            found, body_line = check_body_for_dokuryo(lines, title, rs_start, rs_end)
            if found:
                # Add 読了 to the reading section line
                old_line = lines[i]
                # Insert 読了 after the [[book]] link
                new_line = old_line.replace(']]', ']]　読了', 1)
                lines[i] = new_line
                modified = True
                total_fixes += 1
                fix_details.append((date, title))
                print(f"  ✓ {date}: {title}")
                print(f"    OLD: {old_line.strip()}")
                print(f"    NEW: {new_line.strip()}")
        
        # Also handle: book mentioned with 読了 in body but NOT in reading section at all
        # (user mentioned 裁く眼 was "読み終えた" on 1/28 referring to 1/27)
        
        if modified and not DRY_RUN:
            f.write_text('\n'.join(lines), encoding='utf-8')
    
    print(f"\n合計: {total_fixes} 冊修正" + (" (DRY RUN)" if DRY_RUN else ""))
    return fix_details

if __name__ == '__main__':
    main()
