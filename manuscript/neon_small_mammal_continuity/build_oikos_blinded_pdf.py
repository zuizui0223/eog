from __future__ import annotations

import re
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[2]
LANE = ROOT / "manuscript" / "neon_small_mammal_continuity"
SOURCE = LANE / "MANUSCRIPT_V1.md"
OUT = LANE / "generated" / "OIKOS_BLINDED_MAIN_V1.pdf"

PAGE_W, PAGE_H = A4
LEFT = 72
RIGHT = 54
TOP = 54
BOTTOM = 54
LINE_NUMBER_X = 32
FONT = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
FONT_SIZE = 10.5
LEADING = 21.0
TITLE_SIZE = 14.0
HEADING_SIZE = 12.0
MAX_WIDTH = PAGE_W - LEFT - RIGHT


def plain_markdown_lines(text: str) -> list[tuple[str, str]]:
    output: list[tuple[str, str]] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line:
            output.append(("blank", ""))
            continue
        if line.startswith("# "):
            output.append(("title", line[2:].strip()))
        elif line.startswith("## "):
            output.append(("heading", line[3:].strip()))
        elif line.startswith("### "):
            output.append(("subheading", line[4:].strip()))
        elif line.startswith("- "):
            output.append(("bullet", "• " + line[2:].strip()))
        else:
            cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
            cleaned = re.sub(r"\*(.*?)\*", r"\1", cleaned)
            cleaned = cleaned.replace(chr(96), "")
            output.append(("body", cleaned))
    return output


def wrap(text: str, font_name: str, font_size: float, width: float) -> list[str]:
    if not text:
        return [""]
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = word if not current else current + " " + word
        if stringWidth(trial, font_name, font_size) <= width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    lowered = text.lower()
    forbidden = ("github.com/", "orcid", "corresponding author", "mailto:")
    for token in forbidden:
        if token in lowered:
            raise RuntimeError(f"blinded manuscript contains forbidden identity token: {token}")
    if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text):
        raise RuntimeError("blinded manuscript contains an email address")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(OUT), pagesize=A4)
    pdf.setTitle("Blinded main text")
    pdf.setAuthor("")
    pdf.setSubject("Oikos initial submission - blinded main text")

    page = 1
    y = PAGE_H - TOP
    line_number = 1

    def footer() -> None:
        pdf.setFont(FONT, 9)
        pdf.drawCentredString(PAGE_W / 2, 28, f"Page {page}")

    def new_page() -> None:
        nonlocal page, y
        footer()
        pdf.showPage()
        page += 1
        y = PAGE_H - TOP

    for style, logical in plain_markdown_lines(text):
        if style == "blank":
            y -= LEADING / 2
            if y < BOTTOM + LEADING:
                new_page()
            continue

        if style == "title":
            font_name, font_size = FONT_BOLD, TITLE_SIZE
            before = LEADING / 2
        elif style in {"heading", "subheading"}:
            font_name, font_size = FONT_BOLD, HEADING_SIZE
            before = LEADING / 2
        else:
            font_name, font_size = FONT, FONT_SIZE
            before = 0

        y -= before
        indent = 16 if style == "bullet" else 0
        wrapped = wrap(logical, font_name, font_size, MAX_WIDTH - indent)

        for rendered in wrapped:
            if y < BOTTOM + LEADING:
                new_page()
            pdf.setFont(FONT, 7.5)
            pdf.drawRightString(LINE_NUMBER_X, y, str(line_number))
            pdf.setFont(font_name, font_size)
            pdf.drawString(LEFT + indent, y, rendered)
            line_number += 1
            y -= LEADING

        if style in {"title", "heading"}:
            y -= LEADING / 3

    footer()
    pdf.save()


if __name__ == "__main__":
    main()
