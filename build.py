#!/usr/bin/env python3
"""Render Atlas legal markdown (../legal/*.md) into the static site's
privacy/ and terms/ pages. Re-run after editing the markdown:

    python3 website/build.py

Handles the markdown subset our docs use: #/##/### headings, **bold**,
- bullet lists, > blockquotes, --- rules, [text](url) links, and
paragraphs (single newlines inside a paragraph become <br>).
"""
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEGAL = ROOT.parent / "legal"

PAGES = [
    {"src": "privacy-policy.md", "out": "privacy", "title": "Privacy Policy",
     "other_label": "Terms of Service", "other_href": "/terms"},
    {"src": "terms-of-service.md", "out": "terms", "title": "Terms of Service",
     "other_label": "Privacy Policy", "other_href": "/privacy"},
]

LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")


def inline(text: str) -> str:
    """Escape HTML, then re-apply links and bold from the markdown."""
    # Protect link targets before escaping by tokenizing.
    links = []

    def stash(m):
        links.append((m.group(1), m.group(2)))
        return f"\x00LINK{len(links) - 1}\x00"

    text = LINK_RE.sub(stash, text)
    text = html.escape(text)
    text = BOLD_RE.sub(r"<strong>\1</strong>", text)
    for i, (label, url) in enumerate(links):
        anchor = f'<a href="{html.escape(url)}">{html.escape(label)}</a>'
        text = text.replace(f"\x00LINK{i}\x00", anchor)
    return text


def render(md: str) -> str:
    lines = md.split("\n")
    out = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped == "---":
            out.append("<hr>")
            i += 1
            continue

        if stripped.startswith("### "):
            out.append(f"<h3>{inline(stripped[4:])}</h3>")
            i += 1
            continue
        if stripped.startswith("## "):
            out.append(f"<h2>{inline(stripped[3:])}</h2>")
            i += 1
            continue
        if stripped.startswith("# "):
            out.append(f"<h1>{inline(stripped[2:])}</h1>")
            i += 1
            continue

        if stripped.startswith("> "):
            buf = []
            while i < n and lines[i].strip().startswith("> "):
                buf.append(lines[i].strip()[2:])
                i += 1
            out.append(f"<blockquote>{inline(' '.join(buf))}</blockquote>")
            continue

        if stripped.startswith("- "):
            buf = []
            while i < n and lines[i].strip().startswith("- "):
                buf.append(f"<li>{inline(lines[i].strip()[2:])}</li>")
                i += 1
            out.append("<ul>" + "".join(buf) + "</ul>")
            continue

        # paragraph: gather consecutive non-blank, non-structural lines
        buf = []
        while i < n:
            s = lines[i].strip()
            if (not s or s == "---" or s.startswith(("#", "> ", "- "))):
                break
            buf.append(inline(s))
            i += 1
        out.append("<p>" + "<br>".join(buf) + "</p>")
    return "\n".join(out)


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="index, follow">
<title>{title} — Atlas Astrology</title>
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="icon" href="/assets/apple-touch-icon.png">
<link rel="stylesheet" href="/style.css">
</head>
<body>
<main class="doc">
  <nav class="doc-nav">
    <a class="home" href="/"><img src="/assets/apple-touch-icon.png" alt="">Atlas</a>
    <span class="other"><a href="{other_href}">{other_label}</a></span>
  </nav>
  {body}
  <div class="footer">
    <p>&copy; 2026 Atlas Astrology LLC</p>
    <p><a href="/privacy">Privacy Policy</a> &middot; <a href="/terms">Terms of Service</a> &middot; <a href="mailto:hello@atlasastrology.app">hello@atlasastrology.app</a></p>
  </div>
</main>
</body>
</html>
"""


def main():
    for page in PAGES:
        md = (LEGAL / page["src"]).read_text(encoding="utf-8")
        body = render(md)
        out_html = TEMPLATE.format(
            title=page["title"],
            other_href=page["other_href"],
            other_label=page["other_label"],
            body=body,
        )
        out_path = ROOT / page["out"] / "index.html"
        out_path.write_text(out_html, encoding="utf-8")
        print(f"wrote {out_path.relative_to(ROOT.parent)}")


if __name__ == "__main__":
    main()
