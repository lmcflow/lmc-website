#!/usr/bin/env python3
"""Служебные страницы lmcflow.com (#1032) — lmc. Текст — пакет codex-author (editor PASS), форма — её «да»
(#1032:37993): простая колонка в стиле текущей страницы, шапка и подвал как есть. Шаг 1: /privacy и /app.

    python3 tools/build-service-pages.py --site <чекаут сайта> --src <пакет текстов .md> --effective "2 October 2026"

Цель — ЯВНЫЙ чекаут (--site), не угадывается. Повторный запуск даёт те же байты: ссылки и стиль подвала
вставляются один раз (ревью codex-web WEB-1032-1)."""
import argparse, html, pathlib, re
ap = argparse.ArgumentParser()
ap.add_argument("--site", required=True, type=pathlib.Path)
ap.add_argument("--src", required=True, type=pathlib.Path)
ap.add_argument("--effective", required=True, help="дата вступления политики = дата выкладки")
a = ap.parse_args()
SITE, SRC, EFFECTIVE = a.site.resolve(), a.src, a.effective
assert (SITE / "index.html").exists() and (SITE / "CNAME").exists(), f"{SITE}: не чекаут сайта"
PAGES = {"privacy": ("Privacy policy — LMC Flow", "How LMC Flow handles information from this website, email and LMC Flow Analytics."),
         "app": ("LMC Flow Analytics — LMC Flow", "LMC Flow Analytics: what the application does and how to contact us.")}

def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: f'<a href="{html.escape(m.group(2))}">{m.group(1)}</a>', t)

def md(body):
    out, para, items = [], [], []
    def flush():
        if para: out.append(f"<p>{inline(' '.join(para))}</p>"); para.clear()
        if items: out.append("<ul>" + "".join(f"<li>{inline(i)}</li>" for i in items) + "</ul>"); items.clear()
    for line in body.splitlines():
        s = line.rstrip()
        if not s: flush(); continue
        m = re.match(r"^(#{1,3}) (.+)$", s)
        if m: flush(); n = len(m.group(1)); out.append(f"<h{n}>{inline(m.group(2))}</h{n}>"); continue
        if s.startswith("- "):
            if para: flush()
            items.append(s[2:]); continue
        if items and line.startswith("  "): items[-1] += " " + s.strip(); continue
        para.append(s.strip())
    flush()
    return "\n".join(out)

src = SRC.read_text()
bodies = {}
for name in PAGES:
    m = re.search(rf"^## Page: /{name}\n(.*?)(?=^---$|\Z)", src, re.S | re.M)
    bodies[name] = m.group(1).strip()
    assert "{" not in bodies[name] and "/legal" not in bodies[name], f"{name}: плейсхолдер или ссылка на /legal"

idx = (SITE / "index.html").read_text()
style = idx[idx.index("<style>"):idx.index("</style>") + len("</style>")]
header = idx[idx.index("<header>"):idx.index("</header>") + len("</header>")]
mobile = re.search(r'<div class="mobile-menu" id="mobileMenu">.*?</div>', idx, re.S).group(0)
footer = idx[idx.index("<footer>"):idx.index("</footer>") + len("</footer>")]
script = idx[idx.rindex("<script>"):idx.rindex("</script>") + len("</script>")]
fonts = "\n".join(l for l in idx.splitlines() if "fonts.g" in l)
for a in ("#about", "#services", "#contact", "#top"):
    header = header.replace(f'href="{a}"', f'href="/{a}"'); mobile = mobile.replace(f'href="{a}"', f'href="/{a}"')
PAGE_CSS = """<style>
  .doc { max-width: 720px; margin: 0 auto; padding: 152px 48px 96px; color: var(--ice); }
  .doc h1 { font-size: 2.4rem; font-weight: 600; letter-spacing: -0.02em; line-height: 1.1; margin: 0 0 12px; }
  .doc .effective { font-size: 0.8rem; letter-spacing: 1.5px; text-transform: uppercase; color: rgba(238, 242, 246, 0.6); margin: 0 0 40px; }
  .doc h2 { font-size: 1.15rem; font-weight: 600; margin: 44px 0 12px; }
  .doc h3 { font-size: 1rem; font-weight: 600; margin: 28px 0 8px; }
  .doc p, .doc li { font-size: 1rem; line-height: 1.7; color: rgba(238, 242, 246, 0.82); }
  .doc p { margin: 0 0 14px; }
  .doc ul { margin: 0 0 16px; padding-left: 20px; }
  .doc li { margin: 0 0 8px; }
  .doc a { color: var(--ice); text-decoration: underline; text-underline-offset: 3px; }
  .doc strong { color: var(--ice); font-weight: 600; }
  @media (max-width: 720px) { .doc { padding: 120px 24px 72px; } .doc h1 { font-size: 1.9rem; } }
</style>"""

LINKS = '<nav class="footer-links" aria-label="Information"><a href="/privacy">Privacy</a><span aria-hidden="true">·</span><a href="/app">LMC Flow Analytics</a></nav>'
def footer_with_links(f):
    f = re.sub(r'<nav class="footer-links".*?</nav>\n?\s*', "", f, flags=re.S)       # снять прежние — вставить один раз
    return f.replace('<div class="footer-text">', LINKS + '\n  <div class="footer-text">', 1)
FOOTER_CSS_RULES = """
  /* footer-links (#1032) */
  .footer-links { display: flex; gap: 12px; font-size: 0.75rem; letter-spacing: 1.5px; color: rgba(238, 242, 246, 0.6); }
  .footer-links a { color: rgba(238, 242, 246, 0.6); text-decoration: none; }
  .footer-links a:hover, .footer-links a:focus-visible { color: var(--ice); }
"""
FOOTER_CSS = "<style>" + FOOTER_CSS_RULES + "</style>"
style = style.replace(FOOTER_CSS_RULES, "")                                 # снять ровно вставленное
style = style.replace("</style>", FOOTER_CSS_RULES + "</style>", 1)
footer = footer_with_links(footer)

for name, (title, desc) in PAGES.items():
    body = md(bodies[name])
    if name == "privacy":                    # дата вступления — у политики; у страницы приложения её нет
        body = body.replace("</h1>", f'</h1>\n<p class="effective">Effective {html.escape(EFFECTIVE)}</p>', 1)
    page = (f'<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>{html.escape(title)}</title>\n'
            f'<meta name="description" content="{html.escape(desc)}">\n<link rel="canonical" href="https://lmcflow.com/{name}">\n'
            f'{fonts}\n{style}\n{PAGE_CSS}\n</head>\n<body>\n{header}\n{mobile}\n'
            f'<main class="doc">\n{body}\n</main>\n{footer}\n{script}\n</body>\n</html>\n')
    d = SITE / name; d.mkdir(exist_ok=True); (d / "index.html").write_text(page)
    print("ok", name, len(page))
# подвал главной — те же ссылки и стиль, ровно по одному разу
old_footer = idx[idx.index("<footer>"):idx.index("</footer>") + len("</footer>")]
idx2 = idx.replace(old_footer, footer, 1)
idx2 = idx2.replace(FOOTER_CSS_RULES, "")
idx2 = idx2.replace("</style>", FOOTER_CSS_RULES + "</style>", 1)
if idx2 != idx:
    (SITE / "index.html").write_text(idx2)
print("ok index footer")
