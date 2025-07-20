import fitz  # PyMuPDF
from collections import defaultdict, Counter


import re
import fitz
from collections import Counter

def is_date_like(text):
    """
    Returns True if the string is a single or multiple date line.
    e.g. '18 JUNE 2013', '18 JUNE 2013 23 JULY 2013 6 NOV 2013'
    """
    if not text:
        return False

    # Normalize
    text = text.strip().upper()

    # Extract all 3-part date patterns (like '18 JUNE 2013')
    date_pattern = re.compile(r"\d{1,2} [A-Z]{3,10} \d{4}")
    matches = date_pattern.findall(text)

    # Count how many words are part of these matches
    total_words = len(text.split())
    total_date_words = len(matches) * 3  # each match is 3 words

    # If 90% or more of the words are dates, it's not a heading
    return total_words > 0 and total_date_words / total_words >= 0.9 and len(matches) >= 2

def merge_title_on_page1(page, size_threshold=11.5):
    """Extracts merged title text from page 1 based on largest fonts."""
    blocks = page.get_text("dict")["blocks"]
    title_parts = []

    for block in blocks:
        if block["type"] != 0:
            continue
        for line in block.get("lines", []):
            line_text = ""
            max_size = 0
            for span in line.get("spans", []):
                size = round(span["size"], 1)
                if size > size_threshold:
                    line_text += span["text"].strip() + " "
                    max_size = max(max_size, size)
            if line_text.strip():
                title_parts.append((max_size, line_text.strip()))

    # Sort by size descending and keep only top lines
    title_parts.sort(reverse=True, key=lambda x: x[0])
    top_lines = [t[1] for t in title_parts[:2]]  # take top 2 lines
    return "  ".join(top_lines).strip()


def extract_outline_from_page(page):
    """Returns list of (level, text) headings detected from a page."""
    blocks = page.get_text("dict")["blocks"]
    lines = []
    sizes = []

    for block in blocks:
        if block["type"] != 0:
            continue
        for line in block.get("lines", []):
            line_text = ""
            max_size = 0
            top = 0
            for span in line.get("spans", []):
                text = span["text"].strip()
                if not text:
                    continue
                line_text += text + " "
                max_size = max(max_size, round(span["size"], 1))
                top = span["origin"][1]
            if line_text.strip():
                lines.append({"text": line_text.strip(), "size": max_size, "top": top})
                sizes.append(max_size)

    size_counter = Counter(sizes)
    sorted_sizes = [s for s, _ in size_counter.items() if s > 11.5]
    sorted_sizes.sort(reverse=True)
    size_to_level = {}
    if len(sorted_sizes) > 0:
        size_to_level[sorted_sizes[0]] = "H1"
    if len(sorted_sizes) > 1:
        size_to_level[sorted_sizes[1]] = "H2"
    if len(sorted_sizes) > 2:
        size_to_level[sorted_sizes[2]] = "H3"

    headings = []
    buffer = ""
    last_level = None
    last_top = None
    for line in lines:
        level = size_to_level.get(line["size"])

        # Additional pattern-based override (useful if font size fails)
        if re.match(r"^\d+(\.\d+)*\s", line["text"]):
            dots = line["text"].count(".")
            if dots == 0:
                level = "H1"
            elif dots == 1:
                level = "H2"
            elif dots >= 2:
                level = "H3"

        if not level:
            continue

        if last_level == level and abs(line["top"] - last_top) <= 25:
            buffer += " " + line["text"]
        else:
            if buffer:
                headings.append((last_level, buffer.strip()))
            buffer = line["text"]
            last_level = level
            last_top = line["top"]

    # Flush last
    if buffer:
        merged_text = buffer.strip()
        if not is_date_like(merged_text):
            headings.append((last_level, merged_text))
    return headings
