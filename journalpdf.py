"""
ACM-Optimized PDF → Markdown Pipeline
--------------------------------------

Features:
1. True two-column reconstruction via bounding boxes
2. Batch directory conversion
3. Structured References extraction
4. Refactored object-oriented pipeline

Designed for ACM journals, proceedings, and similar scholarly PDFs.
"""

import re
import sys
import os
import argparse
import fitz  # PyMuPDF
from pathlib import Path
from datetime import datetime
from unidecode import unidecode


# ==========================================================
# Utility Functions
# ==========================================================

def normalize_unicode(text):
    text = unidecode(text)
    text = text.replace("ﬁ", "fi").replace("ﬂ", "fl")
    return text


def fix_hyphenation(text):
    text = re.sub(r'-\n([a-z])', r'\1', text)
    text = re.sub(r'([a-z])-\s+([a-z])', r'\1\2', text)
    return text


def clean_common_acm_artifacts(text):
    text = re.sub(r'\n?\d+\s+interaction[s]?\.*.*\n', '\n', text, flags=re.I)
    text = re.sub(r'ACM.*?\n', '', text)
    text = re.sub(r'Copyright.*?\n', '', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def flatten_block_text(text):
    """Collapse line-wrapped block content into single lines."""
    return re.sub(r'\s*\n\s*', ' ', text).strip()


# ==========================================================
# Core Pipeline Class
# ==========================================================

class ACMPDFConverter:

    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.raw_text = ""
        self.metadata = {}
        self.body_text = ""
        self.references = ""

    # ------------------------------------------------------
    # COLUMN-AWARE EXTRACTION
    # ------------------------------------------------------

    def extract_column_text(self):

        pages_text = []

        for page in self.doc:
            page_text = ""
            blocks = page.get_text("blocks")
            page_width = page.rect.width

            # Build cleaned text blocks with geometry
            text_blocks = []
            for b in blocks:
                x0, y0, x1, y1, text, *_ = b
                flattened = flatten_block_text(text)
                if not flattened:
                    continue
                text_blocks.append({
                    "x0": x0,
                    "y0": y0,
                    "y1": y1,
                    "height": max(1.0, y1 - y0),
                    "text": flattened,
                })

            if not text_blocks:
                pages_text.append(page_text)
                continue

            # Detect approximate columns by clustering block x-positions
            column_threshold = page_width * 0.12
            columns = []
            for block in sorted(text_blocks, key=lambda b: b["x0"]):
                if not columns:
                    columns.append({"center": block["x0"], "blocks": [block]})
                    continue

                nearest = min(columns, key=lambda c: abs(c["center"] - block["x0"]))
                if abs(nearest["center"] - block["x0"]) <= column_threshold:
                    nearest["blocks"].append(block)
                    n = len(nearest["blocks"])
                    nearest["center"] = ((nearest["center"] * (n - 1)) + block["x0"]) / n
                else:
                    columns.append({"center": block["x0"], "blocks": [block]})

            columns.sort(key=lambda c: c["center"])

            # Reconstruct paragraphs within each column
            for column in columns:
                ordered = sorted(column["blocks"], key=lambda b: (b["y0"], b["x0"]))
                paragraph_parts = []
                prev = None

                for block in ordered:
                    if prev is None:
                        paragraph_parts = [block["text"]]
                        prev = block
                        continue

                    vertical_gap = block["y0"] - prev["y1"]
                    same_paragraph_gap = vertical_gap <= max(6.0, prev["height"] * 0.8)

                    if same_paragraph_gap:
                        paragraph_parts.append(block["text"])
                    else:
                        paragraph = " ".join(paragraph_parts).strip()
                        if paragraph:
                            page_text += paragraph + "\n\n"
                        paragraph_parts = [block["text"]]

                    prev = block

                if paragraph_parts:
                    paragraph = " ".join(paragraph_parts).strip()
                    if paragraph:
                        page_text += paragraph + "\n\n"

            pages_text.append(page_text)

        self.raw_text = "\n".join(pages_text)

    # ------------------------------------------------------
    # TABLE EXTRACTION
    # ------------------------------------------------------

    def extract_tables_from_page(self, page):
        """
        Attempt to reconstruct tables using word-level bounding boxes.
        Returns list of (y_position, markdown_table_string)
        """

        words = page.get_text("words")
        if not words:
            return []

        # words format: (x0, y0, x1, y1, "word", block_no, line_no, word_no)
        words_sorted = sorted(words, key=lambda w: (round(w[1], 1), w[0]))

        rows = []
        current_row = []
        current_y = None

        # Group words into rows by vertical proximity
        for w in words_sorted:
            x0, y0, x1, y1, text, *_ = w

            if current_y is None:
                current_y = y0

            if abs(y0 - current_y) < 3:
                current_row.append(w)
            else:
                rows.append(current_row)
                current_row = [w]
                current_y = y0

        if current_row:
            rows.append(current_row)

        # Heuristic: detect rows with multiple column alignments
        # Build column alignment map
        column_positions = []

        for row in rows:
            x_positions = [round(w[0] / 10) * 10 for w in row]
            if len(x_positions) >= 2:
                column_positions.extend(x_positions)

        # Detect recurring X positions
        col_counts = {}
        for x in column_positions:
            col_counts[x] = col_counts.get(x, 0) + 1

        likely_columns = sorted([x for x, c in col_counts.items() if c > 3])

        # If insufficient structure, skip
        if len(likely_columns) < 2:
            return []

        markdown_tables = []

        # Build table rows
        table_rows = []
        for row in rows:
            row_cells = [""] * len(likely_columns)

            for w in row:
                x0 = round(w[0] / 10) * 10
                text = w[4]

                # Find closest column
                col_index = min(
                        range(len(likely_columns)),
                        key=lambda i: abs(likely_columns[i] - x0)
                )

                row_cells[col_index] += text + " "

            cleaned_cells = [c.strip() for c in row_cells]

            # Require at least two non-empty cells
            if sum(1 for c in cleaned_cells if c) >= 2:
                table_rows.append(cleaned_cells)

        # Require minimum rows
        if len(table_rows) < 2:
            return []

        # Build Markdown
        header = table_rows[0]
        separator = ["---"] * len(header)

        md = "\n"
        md += "| " + " | ".join(header) + " |\n"
        md += "| " + " | ".join(separator) + " |\n"

        for row in table_rows[1:]:
            md += "| " + " | ".join(row) + " |\n"

        md += "\n"

        markdown_tables.append((rows[0][0][1], md))

        return markdown_tables

    # ------------------------------------------------------
    # METADATA EXTRACTION
    # ------------------------------------------------------

    def extract_metadata(self):

        text = self.raw_text[:5000]

        # DOI
        doi_match = re.search(r'10\.\d{4,9}/[-._;()/:A-Z0-9]+', text, re.I)
        if doi_match:
            self.metadata["doi"] = doi_match.group(0)

        # Title (first large title-like line)
        lines = text.splitlines()
        for line in lines[:40]:
            if len(line.strip()) > 10 and not line.islower():
                self.metadata["title"] = line.strip()
                break

        # Authors
        author_candidates = re.findall(
            r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)',
            text[:3000]
        )
        if author_candidates:
            self.metadata["author"] = ", ".join(dict.fromkeys(author_candidates[:6]))

        # Year
        year_match = re.search(r'(19|20)\d{2}', text)
        if year_match:
            self.metadata["date"] = f"{year_match.group(0)}-01"

        self.metadata["source"] = "PDF"
        self.metadata["extracted"] = datetime.now().strftime("%Y-%m-%d")

    # ------------------------------------------------------
    # REFERENCE SECTION EXTRACTION
    # ------------------------------------------------------

    def extract_references(self):

        match = re.search(r'\nREFERENCES\n|\nReferences\n', self.raw_text)
        if match:
            parts = re.split(r'\nREFERENCES\n|\nReferences\n', self.raw_text, maxsplit=1)
            self.body_text = parts[0]
            self.references = parts[1]
        else:
            self.body_text = self.raw_text

    def format_references(self):
        if not self.references:
            return ""

        entries = re.split(r'\n\[\d+\]', self.references)
        formatted = "\n## References\n\n"

        for entry in entries:
            entry = entry.strip()
            if len(entry) > 5:
                formatted += f"- {entry}\n\n"

        return formatted

    # ------------------------------------------------------
    # CLEAN + STRUCTURE
    # ------------------------------------------------------

    def clean_and_structure(self):

        text = normalize_unicode(self.body_text)
        text = fix_hyphenation(text)
        text = clean_common_acm_artifacts(text)

        # Merge broken lines
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Detect uppercase headings
        lines = text.split("\n")
        structured = []
        for line in lines:
            if line.strip().isupper() and len(line.split()) < 12:
                structured.append(f"\n## {line.strip().title()}\n")
            else:
                structured.append(line)

        self.body_text = "\n".join(structured)

    # ------------------------------------------------------
    # YAML
    # ------------------------------------------------------

    def generate_yaml(self):
        yaml_lines = ["---"]
        for k, v in self.metadata.items():
            yaml_lines.append(f"{k}: \"{v}\"")
        yaml_lines.append("---\n")
        return "\n".join(yaml_lines)

    # ------------------------------------------------------
    # FULL CONVERSION
    # ------------------------------------------------------

    def convert(self):

        self.extract_column_text()
        self.extract_metadata()
        self.extract_references()
        self.clean_and_structure()

        markdown = self.generate_yaml()
        markdown += self.body_text.strip() + "\n\n"
        markdown += self.format_references()

        return markdown


# ==========================================================
# Batch Processing
# ==========================================================

def batch_convert(directory):
    pdf_files = list(Path(directory).glob("*.pdf"))

    for pdf in pdf_files:
        converter = ACMPDFConverter(str(pdf))
        output = converter.convert()

        output_path = pdf.with_suffix(".md")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output)

        print(f"Converted: {pdf.name} → {output_path.name}")


# ==========================================================
# CLI
# ==========================================================

def main():
    parser = argparse.ArgumentParser(description="ACM PDF → Markdown Converter")
    parser.add_argument("input", nargs="?", help="Input PDF file")
    parser.add_argument("output", nargs="?", help="Output Markdown file")
    parser.add_argument("--batch", help="Batch convert directory")

    args = parser.parse_args()

    if args.batch:
        batch_convert(args.batch)
        return

    if not args.input:
        print("Provide input PDF or use --batch")
        sys.exit(1)

    output_path = args.output or Path(args.input).with_suffix(".md")

    converter = ACMPDFConverter(args.input)
    markdown = converter.convert()

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"Conversion complete: {output_path}")


if __name__ == "__main__":
    main()
