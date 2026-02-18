"""
📖 読書知識連結分析
242冊の読書ノートから、本と本のつながりを発見する
- 感想・気づきのキーワードで共通テーマを抽出
- ジャンル横断の意外なつながりを見つける
- 著者ネットワーク分析
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
import re, yaml

VAULT_DIR = Path(r"C:\Documents\Obsidian Vault\Main Vault")
BOOK_DIR = VAULT_DIR / "📚_読書メモ"


def parse_book(filepath):
    """1冊の読書ノートをパースして辞書を返す"""
    text = filepath.read_text(encoding='utf-8')
    book = {
        'file': filepath,
        'link': filepath.stem,
        'title': filepath.stem.split(' - ')[0].strip(),
        'author': '',
        'category': '',
        'review': '',
        'learning': '',
        'quotes': '',
        'finished': '',
    }
    
    # Frontmatter
    fm_match = re.match(r'^---\n(.*?)\n---', text, re.DOTALL)
    if fm_match:
        try:
            fm = yaml.safe_load(fm_match.group(1))
            authors = fm.get('author', [])
            if isinstance(authors, list):
                book['author'] = ', '.join(str(a) for a in authors if a)
            else:
                book['author'] = str(authors) if authors else ''
            
            cat = fm.get('category', [])
            if isinstance(cat, list):
                book['category'] = ', '.join(str(c) for c in cat if c)
            else:
                book['category'] = str(cat) if cat else ''
            
            book['finished'] = str(fm.get('読了日', ''))
        except:
            pass
    
    # Content sections
    review = re.search(r'感想\s*\n+(.*?)(?=\n---|\n######|\Z)', text, re.DOTALL)
    learning = re.search(r'気づき・学び\s*\n+(.*?)(?=\n---|\n######|\Z)', text, re.DOTALL)
    quotes = re.search(r'(?:印象に残ったフレーズ|引用)\s*\n+(.*?)(?=\n---|\n######|\Z)', text, re.DOTALL)
    
    if review:
        t = review.group(1).strip()
        if t not in ('', '-', '- '):
            book['review'] = t
    if learning:
        t = learning.group(1).strip()
        if t not in ('', '-', '- '):
            book['learning'] = t
    if quotes:
        t = quotes.group(1).strip()
        if t not in ('', '-', '- ', '>', '> '):
            book['quotes'] = t
    
    book['all_text'] = ' '.join([book['review'], book['learning'], book['quotes']])
    return book


# テーマキーワード辞書（日本語 → テーマ）
THEME_KEYWORDS = {
    '睡眠': ['睡眠', '眠', '不眠', '就寝', '覚醒', '安眠', '目覚め', '夜中'],
    '人間の本質': ['人間', '人間性', '本質', '本能', '欲望', '弱さ', '闇', '心理', '真理', '哲学'],
    '成長・学び': ['学び', '成長', '勉強', '努力', '挑戦', '継続', '習慣', '練習', 'スキル', '上達', '学習'],
    '人間関係': ['人間関係', '信頼', '友情', '家族', '親子', '恋愛', '絆', '孤独', '裏切り', 'コミュニケーション'],
    '生と死': ['死', '生きる', '命', '人生', '死生観', '覚悟', '無常', '運命'],
    '社会・制度': ['社会', '政治', '法律', '制度', '格差', '差別', '権力', '組織', '資本', '経済'],
    '日本文化': ['日本', '文化', '歴史', '伝統', '仏教', '禅', '武士', '古代', '近代'],
    '健康・身体': ['健康', '運動', '筋トレ', '体', 'ウォーキング', '食事', '栄養', '身体', 'ストレス'],
    '仕事・ビジネス': ['仕事', 'ビジネス', 'マネジメント', 'リーダーシップ', '経営', '営業', '生産性', 'キャリア'],
    '知識・思考': ['思考', '知識', '哲学', '科学', '論理', '分析', '知性', '認知', 'AI', 'テクノロジー'],
    '物語の力': ['物語', '小説', 'ミステリー', '推理', 'トリック', '伏線', '叙述', '驚き', '犯人', '動機'],
    '自由・生き方': ['自由', '生き方', '選択', '決断', '価値観', '幸福', '幸せ', '充実', 'やりたいこと'],
    '記録・ノート': ['記録', 'ノート', 'メモ', '日記', '書く', '文章', '読書', '読む', '言葉', '記憶'],
}


def find_themes(text):
    """テキストからテーマを検出"""
    found = []
    for theme, keywords in THEME_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score >= 2:
            found.append((theme, score))
    found.sort(key=lambda x: -x[1])
    return found


def analyze():
    print("📖 読書知識連結分析中...\n")
    
    files = sorted(BOOK_DIR.glob('*.md'))
    books = []
    for f in files:
        if f.name.startswith('00_'):
            continue
        b = parse_book(f)
        if b['all_text'].strip():
            books.append(b)
    
    print(f"  📚 分析対象: {len(books)}冊（コンテンツあり）\n")
    
    # ─── 1. テーマ分析 ───
    theme_books = defaultdict(list)
    for b in books:
        themes = find_themes(b['all_text'])
        b['themes'] = themes
        for theme, score in themes:
            theme_books[theme].append((b, score))
    
    # Sort themes by book count
    theme_ranking = sorted(theme_books.items(), key=lambda x: -len(x[1]))
    
    # ─── 2. ジャンル横断つながり ───
    cross_genre = []
    for theme, theme_book_list in theme_ranking:
        genres_in_theme = set()
        for b, _ in theme_book_list:
            genres_in_theme.add(b['category'].split(',')[0].strip() if b['category'] else 'Unknown')
        if len(genres_in_theme) >= 3:
            cross_genre.append((theme, theme_book_list, genres_in_theme))
    
    # ─── 3. 著者別テーマ多様性 ───
    author_books = defaultdict(list)
    for b in books:
        if b['author']:
            for a in b['author'].split(','):
                a = a.strip()
                if a:
                    author_books[a].append(b)
    
    multi_book_authors = {a: bks for a, bks in author_books.items() if len(bks) >= 3}
    
    # ─── 4. 時系列テーマ変遷 ───
    monthly_themes = defaultdict(lambda: Counter())
    for b in books:
        if b['finished'] and b['finished'] != 'None':
            month = b['finished'][:7]
            if month and len(month) == 7:
                for theme, score in b.get('themes', []):
                    monthly_themes[month][theme] += score
    
    # ─── Generate Report ───
    md = f"""---
tags: [自己分析, 読書, 知識連結]
generated: {datetime.now().strftime('%Y-%m-%d')}
---

# 📖 読書知識連結マップ

> **{len(books)}冊**の感想・気づき・引用から、ジャンルを超えたテーマのつながりを可視化

## 🗺️ あなたの読書を貫くテーマ TOP10

"""
    print("  🗺️ テーマ TOP10:")
    for i, (theme, tbooks) in enumerate(theme_ranking[:10], 1):
        top_books = sorted(tbooks, key=lambda x: -x[1])[:5]
        md += f"### {i}. {theme}（{len(tbooks)}冊）\n\n"
        md += f"代表的な本: {', '.join(b['title'][:25] for b, _ in top_books)}\n\n"
        print(f"    {i}. {theme}: {len(tbooks)}冊")
    
    # Cross-genre connections
    md += "\n## 🔗 ジャンルを超えたつながり\n\n"
    md += "> 全く違うジャンルの本なのに、共通テーマで繋がっている組み合わせ\n\n"
    
    print("\n  🔗 ジャンル横断発見:")
    for theme, tbooks, genres in cross_genre[:5]:
        md += f"### 「{theme}」で繋がる本たち\n\n"
        md += f"*{len(genres)}ジャンルから{len(tbooks)}冊が集結*\n\n"
        
        # Group by genre
        by_genre = defaultdict(list)
        for b, score in tbooks:
            g = b['category'].split(',')[0].strip() if b['category'] else 'Unknown'
            by_genre[g].append(b)
        
        for genre, genre_books in sorted(by_genre.items(), key=lambda x: -len(x[1])):
            titles = ', '.join(b['title'][:30] for b in genre_books[:3])
            md += f"- **{genre}**: {titles}\n"
        
        # Show interesting quote if available
        quoted = [b for b, _ in tbooks if b['quotes']]
        if quoted:
            snippet = quoted[0]['quotes'][:150].replace('\n', ' ')
            md += f"\n> 💬 {quoted[0]['title'][:20]}より:\n> {snippet}...\n"
        
        md += "\n---\n\n"
        print(f"    「{theme}」: {len(tbooks)}冊 × {len(genres)}ジャンル")
    
    # Author analysis
    if multi_book_authors:
        md += "\n## ✍️ よく読む著者とそのテーマ\n\n"
        print("\n  ✍️ 多読著者:")
        for author, auth_books in sorted(multi_book_authors.items(), key=lambda x: -len(x[1]))[:8]:
            all_themes = Counter()
            for b in auth_books:
                for theme, score in b.get('themes', []):
                    all_themes[theme] += score
            
            top_themes = [t for t, _ in all_themes.most_common(3)]
            
            md += f"### {author}（{len(auth_books)}冊）\n\n"
            md += f"テーマ傾向: {', '.join(top_themes) if top_themes else '（テーマ未分類）'}\n\n"
            md += f"読んだ本: {', '.join(b['title'][:25] for b in auth_books[:5])}\n\n"
            print(f"    {author}: {len(auth_books)}冊 → {', '.join(top_themes[:2]) if top_themes else '-'}")
    
    # Monthly theme evolution
    if monthly_themes:
        md += "\n## 📅 テーマの時系列変遷\n\n"
        md += "| 月 | 主要テーマ |\n|---|---|\n"
        for month in sorted(monthly_themes.keys()):
            top = monthly_themes[month].most_common(3)
            themes_str = ', '.join(f'{t}' for t, _ in top)
            md += f"| {month} | {themes_str} |\n"
    
    # Key insight
    md += f"""

## 💡 あなたの読書から見えるもの

"""
    # Calculate dominant themes
    all_theme_counts = Counter()
    for b in books:
        for theme, score in b.get('themes', []):
            all_theme_counts[theme] += score
    
    top3 = all_theme_counts.most_common(3)
    if top3:
        md += f"あなたの読書を最も強く貫くテーマは **「{top3[0][0]}」「{top3[1][0]}」「{top3[2][0]}」** です。\n\n"
        md += "ミステリーを楽しみながらも、実は「人間とは何か」「どう生きるか」という問いが通底しています。\n\n"
    
    md += f"\n*自動生成: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n"
    
    report_path = VAULT_DIR / "読書知識連結マップ.md"
    report_path.write_text(md, encoding='utf-8')
    print(f"\n  ✓ レポート: {report_path}")
    print("\n✅ 完了！")


if __name__ == "__main__":
    analyze()
