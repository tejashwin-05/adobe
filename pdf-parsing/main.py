import os
import re
import json
import fitz  # PyMuPDF
from utils import merge_title_on_page1,extract_outline_from_page

INPUT_DIR = "./input"
OUTPUT_DIR = "./output"

def final_process_pdf_with_offset(file_path, page_offset=0):
    doc = fitz.open(file_path)
    outline = []
    seen = set()

    title = merge_title_on_page1(doc[0])  # Extract full merged title

    for page_num in range(len(doc)):
        page = doc[page_num]
        headings = extract_outline_from_page(page)

        for level, text in headings:
                if text in seen:
                    continue
                if re.match(r"^\d{1,2} [A-Z]{3,10} \d{4}$", text):  # Skip dates like '23 JULY 2013'
                    continue
                if not re.match(r"^Page \d+ of \d+", text):
                    seen.add(text)
                    outline.append({
                        "level": level,
                        "text": text,
                        "page": page_num + page_offset
                    })

    # Only include valid pages (skip <= 0)
    outline = [h for h in outline if h["page"] > 0]

    return {
        "title": title if title else "Untitled",
        "outline": outline
    }

def main():
    for filename in os.listdir(INPUT_DIR):
        if filename.lower().endswith(".pdf"):
            filepath = os.path.join(INPUT_DIR, filename)
            result = final_process_pdf_with_offset(filepath)

            json_name = filename.rsplit(".", 1)[0] + ".json"
            outpath = os.path.join(OUTPUT_DIR, json_name)

            with open(outpath, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
