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
import pymupdf as fitz  # PyMuPDF
from pathlib import Path
from datetime import datetime
from unidecode import unidecode


# ==========================================================
# Utility Functions
# ==========================================================

def normalize_unicode(text):
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("’", "'").replace("‘", "'")
    text = unidecode(text)
    text = text.replace("ﬁ", "fi").replace("ﬂ", "fl")
    return text


def fix_hyphenation(text):
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)
    text = re.sub(r'(\w)-\s+(\w)', r'\1\2', text)
    return text


def clean_common_acm_artifacts(text):
    text = re.sub(
        r'\d+\s*i\s*n\s*t\s*e\s*r\s*a\s*c\s*t\s*i\s*o\s*n\s*s.*?\n',
        '',
        text,
        flags=re.I
    )
    # Remove ACM permission/copyright boilerplate (appears at column bottoms).
    # Replace with a single space so surrounding sentences are joined correctly.
    text = re.sub(
        r'\s*Permission to make digital or hard copies.*?\$[\d.]+\.\s*',
        ' ',
        text,
        flags=re.S
    )
    text = re.sub(r'^ACM\b.*?$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^Copyright\b.*?$', '', text, flags=re.MULTILINE)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def flatten_block_text(text):
    """Collapse line-wrapped block content into single lines."""
    return re.sub(r'\s*\n\s*', ' ', text).strip()


def get_spans(page):
    data = page.get_text("dict")
    spans = []
    for block in data["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span["text"].strip()
                if not text:
                    continue

                spans.append({
                    "text": text,
                    "size": span["size"],
                    "y": span["bbox"][1],
                    "x": span["bbox"][0]
                })

    return spans


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

    def get_content_blocks(self, page):
        """
        Extract text blocks from a page using span-level data.
        If a PDF block begins with bold spans followed by normal spans, the
        leading bold text is split off as a heading sub-block and the remaining
        text becomes a body sub-block.  Bold text that appears only in the
        middle of a block (inline bold) is NOT split out — it stays part of the
        body paragraph to avoid fragmenting content.
        Returns list of (x0, y0, x1, y1, text, is_heading) tuples.
        """
        data = page.get_text("dict")

        # Estimate body text size as the most common font size among non-bold spans.
        body_size_counts: dict[int, int] = {}
        for raw_block in data["blocks"]:
            if "lines" not in raw_block:
                continue
            for line in raw_block["lines"]:
                for span in line["spans"]:
                    if span["text"].strip() and "Bold" not in span.get("font", ""):
                        sz = round(span["size"])
                        body_size_counts[sz] = body_size_counts.get(sz, 0) + 1
        body_size = max(body_size_counts, key=body_size_counts.get) if body_size_counts else 9

        result = []
        for raw_block in data["blocks"]:
            if "lines" not in raw_block:
                continue
            bx0, by0, bx1, by1 = raw_block["bbox"]
            heading_spans = []
            body_spans = []
            in_leading_bold = True  # True until we see a non-heading span

            for line in raw_block["lines"]:
                for span in line["spans"]:
                    bold = "Bold" in span.get("font", "")
                    # A span qualifies as part of the leading heading only if it is
                    # bold AND its size is notably larger than the body text size.
                    is_heading_span = bold and span["size"] > body_size + 1
                    if not span["text"].strip():
                        if in_leading_bold and heading_spans:
                            heading_spans.append(span)
                        else:
                            body_spans.append(span)
                        continue
                    if in_leading_bold and is_heading_span:
                        heading_spans.append(span)
                    else:
                        in_leading_bold = False
                        body_spans.append(span)

            if heading_spans:
                heading_text = "".join(s["text"] for s in heading_spans).strip()
                if heading_text:
                    hx0 = heading_spans[0]["bbox"][0]
                    hy0 = heading_spans[0]["bbox"][1]
                    result.append((hx0, hy0, bx1, by1, heading_text, True))

            if body_spans:
                body_text = "".join(s["text"] for s in body_spans).strip()
                if body_text:
                    non_empty = [s for s in body_spans if s["text"].strip()]
                    bspan_x0 = non_empty[0]["bbox"][0] if non_empty else bx0
                    bspan_y0 = non_empty[0]["bbox"][1] if non_empty else by0
                    result.append((bspan_x0, bspan_y0, bx1, by1, body_text, False))

        return result

    def extract_column_text(self):

        pages_text = []

        for page in self.doc:

            page_text = ""
            tables = self.extract_tables_from_page(page)

            # Use span-level block splitting to separate headings from body text
            content_blocks = self.get_content_blocks(page)

            # Collect x positions from all non-empty blocks for column detection
            x_positions = [b[0] for b in content_blocks if b[4].strip()]
            if not x_positions:
                pages_text.append("")
                continue
            x_positions.sort()

            # Exclude running headers and footers
            page_height = page.rect.height
            top_margin = page_height * 0.08
            bottom_margin = page_height * 0.92
            page_width = page.rect.width

            filtered_blocks = []

            for b in content_blocks:
                x0, y0, x1, y1, text, is_heading = b
                width = x1 - x0

                if not text.strip():
                    continue

                # Reject spaced letter headings resulting from graphic design software
                tokens = text.strip().split()
                if len(tokens) >= 6 and sum(len(t) == 1 for t in tokens) / len(tokens) > 0.6:
                    continue

                # Reject narrow blocks (likely callouts or sidebars)
                if width < page_width * 0.30:
                    continue

                # Remove header zone
                if y0 < top_margin:
                    continue

                # Remove footer zone
                if y1 > bottom_margin:
                    continue

                filtered_blocks.append(b)

            # Cluster x positions by simple gap detection to detect columns
            columns = []
            current_cluster = [x_positions[0]]

            for x in x_positions[1:]:
                if abs(x - current_cluster[-1]) < 40:  # tolerance
                    current_cluster.append(x)
                else:
                    columns.append(current_cluster)
                    current_cluster = [x]

            columns.append(current_cluster)

            # Determine column centers
            column_centers = [sum(cluster) / len(cluster) for cluster in columns]
            column_blocks = [[] for _ in column_centers]

            for b in filtered_blocks:
                x0, y0, x1, y1, text, is_heading = b

                if not text.strip():
                    continue

                # Remove right-margin sidebars
                if x0 > page_width * 0.75:
                    continue

                # Assign block to nearest column center
                distances = [abs(x0 - center) for center in column_centers]
                col_index = distances.index(min(distances))
                column_blocks[col_index].append((y0, text, is_heading))

            for col in column_blocks:
                page_text += self._assemble_column_blocks(col)

            # Append tables at end of page (simplified insertion)
            for _, table_md in tables:
                page_text += table_md

            pages_text.append(page_text)

        self.raw_text = "\n".join(pages_text)
    
    # ------------------------------------------------------
    # TABLE RECONSTRUCTION
    # ------------------------------------------------------

    def _assemble_column_blocks(self, blocks):
        """
        Reconstruct semantic paragraphs from column blocks.
        Each block is a (y0, text, is_heading) tuple.
        Heading blocks become # Markdown headings; body blocks are merged into
        paragraphs. Suppresses cumulative block expansion artifacts.
        """
        if not blocks:
            return ""

        blocks.sort(key=lambda x: x[0])

        assembled = []  # list of (kind, text) where kind is "heading" or "body"
        current = None
        current_is_heading = False
        previous_flattened = None

        for _, text, is_heading in blocks:
            flattened = flatten_block_text(text)
            if not flattened:
                continue

            # Figure/table captions are bold in the PDF but are body text, not headings
            if is_heading and re.match(r'^(Figure|Table|Fig\.|Appendix)\b', flattened):
                is_heading = False

            # Cumulative expansion: adopt the expanded body version to preserve content.
            # Heading blocks are never expanded this way.
            if not is_heading and previous_flattened and flattened.startswith(previous_flattened):
                previous_flattened = flattened
                if not current_is_heading:
                    current = flattened
                continue

            previous_flattened = flattened

            if is_heading:
                if current:
                    assembled.append(("heading" if current_is_heading else "body", current.strip()))
                current = flattened
                current_is_heading = True
            elif current_is_heading or current is None or current.rstrip().endswith(('.', '?', '!', ':')):
                if current:
                    assembled.append(("heading" if current_is_heading else "body", current.strip()))
                current = flattened
                current_is_heading = False
            else:
                current += " " + flattened

        if current:
            assembled.append(("heading" if current_is_heading else "body", current.strip()))

        parts = []
        for kind, text in assembled:
            parts.append(f"# {text}" if kind == "heading" else text)

        return "\n\n".join(parts) + "\n\n"

    # ------------------------------------------------------
    # TABLE EXTRACTION
    # ------------------------------------------------------

    def extract_tables_from_page(self, page):

        # ... table building functionality in the works ...

        return []

    # ------------------------------------------------------
    # METADATA EXTRACTION
    # ------------------------------------------------------

    def extract_metadata(self):

        text = self.raw_text[:5000]

        # DOI
        doi_match = re.search(r'10\.\d{4,9}/[-._;()/:A-Z0-9]+', text, re.I)
        if doi_match:
            self.metadata["doi"] = doi_match.group(0)

        # Title is not being extracted here. That's done in detect_title()

        # Authors in detect_authors()

        self.metadata["source"] = "PDF"
        self.metadata["extracted"] = datetime.now().strftime("%Y-%m-%d")

    # ------------------------------------------------------
    # AUTHOR AND CO-AUTHORS EXTRACTION
    # ------------------------------------------------------

    def detect_authors(self, spans, title_y):
        name_pattern = re.compile(
            r'\b[A-Z][a-z]+(?:\s[A-Z]\.)?\s[A-Z][a-z]+(?:\s(?:van|de|von)\s[A-Z][a-z]+)?'
        )
        candidates = []
        for s in spans:
            # Only look near title area
            if s["y"] < title_y + 80 or s["y"] > title_y + 260:
                continue
            matches = name_pattern.findall(s["text"])
            for m in matches:
                candidates.append(m)
        authors = list(dict.fromkeys(candidates))
        if authors:
            self.metadata["author"] = authors[:6]

    # ------------------------------------------------------
    # TITLE AND SUBTITLE EXTRACTION
    # ------------------------------------------------------

    def detect_title(self, spans):
        # Only consider top region of page
        top_spans = [s for s in spans if s["y"] < 350]
        if not top_spans:
            return None, None, None
        # Sort by font size
        spans_sorted = sorted(top_spans, key=lambda s: -s["size"])
        largest = spans_sorted[0]["size"]
        # Allow a wider tolerance
        title_spans = [
            s for s in top_spans
            if largest - 2 <= s["size"] <= largest
        ]
        if not title_spans:
            return None, None, None
        # Sort in reading order
        title_spans.sort(key=lambda s: (s["y"], s["x"]))
        title = " ".join(s["text"] for s in title_spans)
        title_y = min(s["y"] for s in title_spans)
        return title, title_y, largest

    def detect_subtitle(self, spans, title_y):
        candidates = [
            s for s in spans
            if title_y < s["y"] < title_y + 120
            and 9 < s["size"] < 13
        ]
        candidates.sort(key=lambda s: (s["y"], s["x"]))
        lines = []
        for s in candidates[:6]:
            lines.append(s["text"])
        if not lines:
            return None
        return " ".join(lines)

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

        # Detect list-like structures based on indentation and line length
        lines = text.split("\n")
        processed = []

        for line in lines:

            stripped = line.strip()

            if not stripped:
                processed.append("")
                continue

            # bullet or enumerated list markers
            if (
                stripped.startswith(("•", "-", "*"))
                or re.match(r"^\d+\.", stripped)
                or re.match(r"^[A-Za-z]\)", stripped)
            ):
                processed.append("* " + stripped.lstrip("•-* ").strip())
                continue

            processed.append(line)

        text = "\n".join(processed)

        # Ensure that each bullet starts on its own line.
        text = re.sub(r'\s*\*\s+', r'\n* ', text) # Any resultant double line breaks are stripped away again below.

        # Merge lines inside paragraphs
        text = re.sub(r'(?<!\n)\n(?!\n|[-*•])', ' ', text)

        # Collapse excessive blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Detect uppercase headings
        lines = text.split("\n")
        structured = []
        for line in lines:
            if (line.strip().isupper() and len(line.split()) < 12
                    and not line.strip().startswith('#')):
                structured.append(f"\n# {line.strip()}\n")
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

        # --------------------------------
        # 1. Extract column text
        # --------------------------------
        self.extract_column_text()

        # --------------------------------
        # 2. Metadata detection from first page
        # --------------------------------
        first_page = self.doc[0]
        spans = get_spans(first_page)

        if spans:
            title, title_y, title_size = self.detect_title(spans)
            if title:
                self.metadata["title"] = title
                subtitle = self.detect_subtitle(spans, title_y)
                if subtitle:
                    self.metadata["subtitle"] = subtitle
                self.detect_authors(spans, title_y)

        # --------------------------------
        # 3. Extract remaining metadata
        # --------------------------------
        self.extract_metadata()

        # --------------------------------
        # 4. Split references
        # --------------------------------
        self.extract_references()

        # --------------------------------
        # 5. Clean body text
        # --------------------------------
        self.clean_and_structure()

        # --------------------------------
        # 6. Build final markdown
        # --------------------------------
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