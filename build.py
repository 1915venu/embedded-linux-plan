"""
build.py — Convert Enhanced Plan markdown files to a static website.

Usage: python build.py
Run from the website/ directory, or the parent Enhanced_Plan/ directory.
"""

import sys
import io

# Fix Windows console encoding (cp1252 can't handle emojis)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os
import re
import json
import html
import markdown

# ===== CONFIGURATION =====

PAGES = [
    {"src": "00_README_ENHANCED.md",            "out": "00_readme.html",              "title": "README — Overview",                "icon": "🏠",  "section": "overview", "badge": ""},
    {"src": "01_Phase1_C_Revision.md",           "out": "01_phase1.html",              "title": "Phase 1: C Revision",              "icon": "⚙️",  "section": "phases",   "badge": "Days 0-3"},
    {"src": "02_Phase2_Linux_Fundamentals.md",   "out": "02_phase2.html",              "title": "Phase 2: Linux Fundamentals",      "icon": "🐧",  "section": "phases",   "badge": "Days 4-8"},
    {"src": "03_Phase3_Kernel_Modules.md",       "out": "03_phase3.html",              "title": "Phase 3: Kernel Modules",          "icon": "🧩",  "section": "phases",   "badge": "Days 9-13"},
    {"src": "04_Phase4_CharDriver_Project.md",   "out": "04_phase4.html",              "title": "Phase 4: Char Driver Project",     "icon": "💾",  "section": "phases",   "badge": "Days 14-22"},
    {"src": "05_Phase5_DeviceTree_Platform.md",  "out": "05_phase5.html",              "title": "Phase 5: Device Tree & Platform",  "icon": "🌳",  "section": "phases",   "badge": "Days 23-27"},
    {"src": "06_Phase6_I2C_Project.md",          "out": "06_phase6.html",              "title": "Phase 6: I2C Project",             "icon": "🔌",  "section": "phases",   "badge": "Days 28-37"},
    {"src": "07_Phase7_ThreadPool_Interview.md", "out": "07_phase7.html",              "title": "Phase 7: Thread Pool & Interview", "icon": "🎯",  "section": "phases",   "badge": "Days 38-40"},
    {"src": "08_Appendix_InterviewBank.md",      "out": "08_appendix_interviews.html", "title": "Appendix: Interview Bank",         "icon": "📝",  "section": "appendix", "badge": "150+ Q&A"},
    {"src": "09_Appendix_KernelInternals.md",    "out": "09_appendix_kernel.html",     "title": "Appendix: Kernel Internals",       "icon": "🔬",  "section": "appendix", "badge": ""},
    {"src": "10_Appendix_Debugging.md",          "out": "10_appendix_debugging.html",  "title": "Appendix: Debugging",              "icon": "🔧",  "section": "appendix", "badge": ""},
]

# ===== PATHS =====

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WEBSITE_DIR = SCRIPT_DIR  # build.py lives in website/
MD_DIR = os.path.dirname(SCRIPT_DIR)  # parent = Enhanced_Plan/


# ===== MARKDOWN CONVERSION =====

def convert_markdown(md_text):
    """Convert markdown text to HTML, with fenced_code, tables, toc."""
    md = markdown.Markdown(extensions=[
        'fenced_code',
        'tables',
        'toc',
        'smarty',
        'sane_lists',
    ], extension_configs={
        'toc': {
            'permalink': False,
            'toc_depth': '1-4',
        },
    })
    html_content = md.convert(md_text)

    # Extract TOC headings for search index
    headings = []
    if hasattr(md, 'toc_tokens'):
        def walk_toc(tokens):
            for t in tokens:
                headings.append({"text": t['name'], "id": t['id']})
                if t.get('children'):
                    walk_toc(t['children'])
        walk_toc(md.toc_tokens)

    return html_content, headings


def add_language_labels(html_content):
    """Add data-lang attribute to <pre> tags based on code block language."""
    # Markdown generates: <pre><code class="language-xxx">
    pattern = r'<pre><code class="language-(\w+)">'
    def replacer(m):
        lang = m.group(1)
        return f'<pre data-lang="{lang}"><code class="language-{lang}">'
    return re.sub(pattern, replacer, html_content)


# ===== SIDEBAR HTML =====

def build_sidebar_html(current_page_out):
    """Generate the sidebar navigation HTML."""
    sections = {
        "overview": "Getting Started",
        "phases": "Learning Phases",
        "appendix": "Appendices",
    }
    lines = []
    current_section = None

    for page in PAGES:
        if page["section"] != current_section:
            current_section = page["section"]
            lines.append(f'  <div class="sidebar-section-label">{sections[current_section]}</div>')

        active = ' active' if page["out"] == current_page_out else ''
        badge_html = f'<span class="link-badge">{html.escape(page["badge"])}</span>' if page["badge"] else ''
        lines.append(
            f'  <a class="sidebar-link{active}" href="{page["out"]}">'
            f'<span class="link-icon">{page["icon"]}</span>'
            f'<span>{html.escape(page["title"])}</span>'
            f'{badge_html}</a>'
        )

    return '\n'.join(lines)


# ===== PAGE NAV (prev / next) =====

def build_page_nav(index):
    """Generate prev/next navigation at the bottom of each page."""
    parts = []
    if index > 0:
        prev_p = PAGES[index - 1]
        parts.append(
            f'<a class="prev" href="{prev_p["out"]}">'
            f'<span class="nav-label">← Previous</span>'
            f'<span class="nav-title">{html.escape(prev_p["title"])}</span></a>'
        )
    if index < len(PAGES) - 1:
        next_p = PAGES[index + 1]
        parts.append(
            f'<a class="next" href="{next_p["out"]}">'
            f'<span class="nav-label">Next →</span>'
            f'<span class="nav-title">{html.escape(next_p["title"])}</span></a>'
        )
    return '\n'.join(parts)


# ===== SEARCH INDEX =====

def build_search_index(all_headings):
    """Build JSON search index for client-side search."""
    index = []
    for page, headings in all_headings:
        index.append({
            "title": page["title"],
            "url": page["out"],
            "headings": headings,
        })
    return json.dumps(index)


# ===== HTML TEMPLATE =====

def render_page(page, index, content_html, sidebar_html, search_index_json):
    """Wrap content in the full page HTML template."""
    page_nav_html = build_page_nav(index)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{html.escape(page['title'])} — Embedded Linux & Device Drivers Enhanced 40-Day Guide">
  <title>{html.escape(page['title'])} — Enhanced Plan</title>

  <!-- Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>

  <!-- Highlight.js for syntax highlighting -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>

  <!-- App styles -->
  <link rel="stylesheet" href="style.css">
</head>
<body>

  <!-- Progress Bar -->
  <div id="progress-bar"></div>

  <!-- Sidebar Overlay (mobile) -->
  <div class="sidebar-overlay"></div>

  <!-- Sidebar -->
  <nav class="sidebar">
    <div class="sidebar-brand">
      <h1>🐧 Embedded Linux</h1>
      <p>Enhanced 40-Day Guide</p>
    </div>
    <div class="sidebar-nav">
{sidebar_html}
    </div>
  </nav>

  <!-- Header -->
  <header class="header">
    <button class="hamburger" aria-label="Toggle sidebar">☰</button>
    <div class="header-title">
      <span class="emoji">{page["icon"]}</span> {html.escape(page["title"])}
    </div>
    <div class="header-search">
      <span class="search-icon">🔍</span>
      <input type="text" id="search-input" placeholder="Search topics..." autocomplete="off">
      <div class="search-results" id="search-results"></div>
    </div>
  </header>

  <!-- Main Content -->
  <main class="main-content">
    <div class="content-wrapper">
      {content_html}

      <!-- Page Navigation -->
      <div class="page-nav">
        {page_nav_html}
      </div>
    </div>
  </main>

  <!-- Back to Top -->
  <button class="back-to-top" aria-label="Back to top">↑</button>

  <!-- Search Index Data -->
  <script type="application/json" id="search-data">{search_index_json}</script>

  <!-- Scripts -->
  <script>hljs.highlightAll();</script>
  <script src="app.js"></script>
</body>
</html>'''


# ===== INDEX.HTML (redirect) =====

INDEX_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="refresh" content="0; url=00_readme.html">
  <title>Redirecting...</title>
</head>
<body>
  <p>Redirecting to <a href="00_readme.html">Overview</a>...</p>
</body>
</html>'''


# ===== MAIN BUILD =====

def main():
    print("🔨 Building Enhanced Plan website...")
    print(f"   Markdown source: {MD_DIR}")
    print(f"   Output dir:      {WEBSITE_DIR}")
    print()

    # Phase 1: Convert all markdown and collect headings
    all_headings = []  # [(page, headings), ...]
    all_content = []   # [(page, content_html), ...]

    for page in PAGES:
        src_path = os.path.join(MD_DIR, page["src"])
        if not os.path.exists(src_path):
            print(f"   ⚠️  SKIP: {page['src']} not found")
            continue

        with open(src_path, "r", encoding="utf-8") as f:
            md_text = f.read()

        content_html, headings = convert_markdown(md_text)
        content_html = add_language_labels(content_html)

        all_headings.append((page, headings))
        all_content.append((page, content_html))
        print(f"   ✅ Converted: {page['src']}  ({len(headings)} headings)")

    # Phase 2: Build search index
    search_index_json = build_search_index(all_headings)

    # Phase 3: Render each page with full template
    for i, (page, content_html) in enumerate(all_content):
        sidebar_html = build_sidebar_html(page["out"])
        full_html = render_page(page, i, content_html, sidebar_html, search_index_json)

        out_path = os.path.join(WEBSITE_DIR, page["out"])
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(full_html)
        print(f"   📄 Wrote: {page['out']}")

    # Phase 4: Write index.html
    index_path = os.path.join(WEBSITE_DIR, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(INDEX_HTML)
    print(f"   📄 Wrote: index.html")

    print()
    print(f"✨ Done! {len(all_content)} pages built.")
    print()
    print("To view the website, run:")
    print(f'   cd "{WEBSITE_DIR}"')
    print(f"   python -m http.server 8080")
    print(f"   Then open http://localhost:8080")


if __name__ == "__main__":
    main()
