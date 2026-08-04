"""Dependency-free Markdown -> styled HTML for the operator documentation pages
(/ops/formulas, /ops/integration).

Renders the subset of Markdown actually used in docs/*.md — headers, GFM tables, fenced
and inline code, bold, blockquotes, ordered/unordered lists (with soft-wrapped continuation
lines), horizontal rules, and paragraphs — into HTML styled to match docs/Realify-Architecture.html.

Deliberately tiny and self-contained: these pages must render with only the stdlib, so the
container needs no markdown dependency. The .md files remain the single source of truth; edits
to them reflect on the served pages with no regeneration step.
"""
import html as _html
import re

_BULLET_RE = re.compile(r'^(\s*)[-*]\s+(.*)$')
_ORDERED_RE = re.compile(r'^(\s*)\d+\.\s+(.*)$')
_HEADER_RE = re.compile(r'^(#{1,6})\s+(.*)$')
_HR_RE = re.compile(r'^(-{3,}|\*{3,}|_{3,})$')
_TABLE_SEP_RE = re.compile(r'^\s*\|?[\s:\-|]+\|?\s*$')


def _inline(text):
    """Escape, then apply inline markup. Escaping first means code/cell content is safe."""
    t = _html.escape(text)
    t = re.sub(r'`([^`]+)`', lambda m: '<code>' + m.group(1) + '</code>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', t)
    return t


def _split_row(line):
    s = line.strip()
    if s.startswith('|'):
        s = s[1:]
    if s.endswith('|'):
        s = s[:-1]
    return [c.strip() for c in s.split('|')]


def render_markdown(md):
    lines = md.replace('\r\n', '\n').split('\n')
    n = len(lines)
    out = []
    para = []

    def flush_para():
        if para:
            out.append('<p>' + _inline(' '.join(para).strip()) + '</p>')
            para.clear()

    i = 0
    while i < n:
        line = lines[i]
        stripped = line.strip()

        # fenced code block
        if stripped.startswith('```'):
            flush_para()
            i += 1
            code = []
            while i < n and not lines[i].strip().startswith('```'):
                code.append(lines[i])
                i += 1
            i += 1  # consume closing fence
            out.append('<pre><code>' + _html.escape('\n'.join(code)) + '</code></pre>')
            continue

        # horizontal rule
        if _HR_RE.match(stripped):
            flush_para()
            out.append('<hr>')
            i += 1
            continue

        # header
        m = _HEADER_RE.match(stripped)
        if m:
            flush_para()
            lvl = len(m.group(1))
            out.append('<h%d>%s</h%d>' % (lvl, _inline(m.group(2)), lvl))
            i += 1
            continue

        # table: header row followed by a |---|---| separator
        if '|' in line and i + 1 < n and _TABLE_SEP_RE.match(lines[i + 1]) and '-' in lines[i + 1]:
            flush_para()
            header = _split_row(line)
            i += 2
            body_rows = []
            while i < n and '|' in lines[i] and lines[i].strip():
                body_rows.append(_split_row(lines[i]))
                i += 1
            th = ''.join('<th>' + _inline(c) + '</th>' for c in header)
            trs = ''
            for r in body_rows:
                cells = (r + [''] * len(header))[:len(header)]
                trs += '<tr>' + ''.join('<td>' + _inline(c) + '</td>' for c in cells) + '</tr>'
            out.append('<table><thead><tr>' + th + '</tr></thead><tbody>' + trs + '</tbody></table>')
            continue

        # blockquote (consecutive > lines)
        if stripped.startswith('>'):
            flush_para()
            quote = []
            while i < n and lines[i].strip().startswith('>'):
                quote.append(lines[i].strip().lstrip('>').strip())
                i += 1
            out.append('<blockquote>' + _inline(' '.join(quote)) + '</blockquote>')
            continue

        # unordered list (absorb soft-wrapped continuation lines)
        if _BULLET_RE.match(line):
            flush_para()
            items = []
            while i < n:
                bm = _BULLET_RE.match(lines[i])
                if bm:
                    items.append(bm.group(2).rstrip())
                    i += 1
                elif lines[i].strip() and (lines[i].startswith('  ') or lines[i].startswith('\t')) \
                        and not _ORDERED_RE.match(lines[i]) and items:
                    items[-1] += ' ' + lines[i].strip()
                    i += 1
                else:
                    break
            out.append('<ul>' + ''.join('<li>' + _inline(it) + '</li>' for it in items) + '</ul>')
            continue

        # ordered list (absorb soft-wrapped continuation lines)
        if _ORDERED_RE.match(line):
            flush_para()
            items = []
            while i < n:
                om = _ORDERED_RE.match(lines[i])
                if om:
                    items.append(om.group(2).rstrip())
                    i += 1
                elif lines[i].strip() and (lines[i].startswith('   ') or lines[i].startswith('\t')) \
                        and not _BULLET_RE.match(lines[i]) and items:
                    items[-1] += ' ' + lines[i].strip()
                    i += 1
                else:
                    break
            out.append('<ol>' + ''.join('<li>' + _inline(it) + '</li>' for it in items) + '</ol>')
            continue

        # blank line ends a paragraph
        if not stripped:
            flush_para()
            i += 1
            continue

        # default: paragraph text
        para.append(stripped)
        i += 1

    flush_para()
    return '\n'.join(out)


_STYLE = """
<style>
  :root{
    --navy:#1F3864; --blue:#2E75B6; --green:#0F6E4F; --purple:#6A1B9A;
    --grey:#5b6675; --ink:#16202e; --line:#dbe2ec; --bg:#ffffff;
    --panel:#f6f8fb; --panel2:#eef3f9; --code:#0b1f3a;
  }
  *{box-sizing:border-box}
  html{-webkit-text-size-adjust:100%}
  body{margin:0; background:var(--bg); color:var(--ink);
    font-family:"Inter",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    font-size:15px; line-height:1.62; letter-spacing:.002em;}
  .wrap{max-width:980px; margin:0 auto; padding:54px 40px 120px}
  .bar{height:6px; border-radius:4px;
    background:linear-gradient(90deg,var(--blue) 0 33%,var(--green) 33% 66%,var(--purple) 66% 100%); margin-bottom:22px}
  .eyebrow{font:600 11px/1 "SF Mono",ui-monospace,monospace; letter-spacing:.18em; text-transform:uppercase; color:var(--blue); margin-bottom:8px}
  h1,h2,h3,h4{line-height:1.22; color:var(--navy); font-weight:700; letter-spacing:-.01em}
  h1{font-size:30px; margin:4px 0 6px}
  h2{font-size:24px; margin:54px 0 6px; padding-top:14px; border-top:1px solid var(--line)}
  h3{font-size:18px; margin:30px 0 4px; color:#243a5e}
  h4{font-size:14.5px; margin:20px 0 2px; color:#33405a}
  p{margin:10px 0}
  a{color:var(--blue)}
  code,.mono{font-family:"SF Mono",ui-monospace,"JetBrains Mono","Roboto Mono",Menlo,Consolas,monospace}
  code{background:var(--panel2); color:var(--code); padding:1px 5px; border-radius:4px; font-size:.86em}
  pre{background:var(--code); color:#e9eef6; padding:14px 16px; border-radius:10px; overflow:auto; margin:14px 0; font-size:12.5px; line-height:1.5}
  pre code{background:none; color:inherit; padding:0; font-size:inherit}
  blockquote{border-left:3px solid var(--blue); background:var(--panel); padding:10px 16px; border-radius:0 8px 8px 0; margin:16px 0; color:#26344c; font-size:14px}
  ul,ol{margin:8px 0; padding-left:22px} li{margin:5px 0}
  hr{height:1px; background:var(--line); border:0; margin:30px 0}
  table{border-collapse:collapse; width:100%; font-size:13px; margin:14px 0}
  th,td{border:1px solid var(--line); padding:7px 10px; text-align:left; vertical-align:top}
  th{background:var(--panel2); color:var(--navy); font-weight:600; font-size:11.5px; letter-spacing:.04em; text-transform:uppercase}
  td code{font-size:12px}
  .footer{margin-top:48px; padding-top:14px; border-top:1px solid var(--line); color:var(--grey); font-size:12px}
</style>
"""


def render_page(title, md, eyebrow="Realify · Operator documentation"):
    body = render_markdown(md)
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<meta name='robots' content='noindex, nofollow'>"
        "<title>Realify · " + _html.escape(title) + "</title>"
        + _STYLE +
        "</head><body><div class='wrap'>"
        "<div class='bar'></div>"
        "<div class='eyebrow'>" + _html.escape(eyebrow) + "</div>"
        + body +
        "<div class='footer'>Rendered from the repository Markdown source — the document of record. "
        "Internal · key-gated · excluded from crawlers.</div>"
        "</div></body></html>"
    )
