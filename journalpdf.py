"""
ACM-Optimized PDF -> Markdown Pipeline
--------------------------------------

Features:
1. True two-column reconstruction via line-level bounding boxes
2. Batch directory conversion
3. Structured References extraction
4. Refactored object-oriented pipeline

Designed for ACM journals, proceedings, and similar scholarly PDFs.
"""

import re
import sys
import argparse
import pymupdf as fitz  # PyMuPDF
from pathlib import Path
from datetime import datetime
from unidecode import unidecode

HEADING_FONTS = {"GillSans-Bold"}
TITLE_FONT_PREFIXES = {"WatersTitling"}
AUTHOR_BIO_FONTS = {"GaramondThree-BoldSC"}
ABSTRACT_FONTS = {"OfficinaSans-BoldItalic"}
FOOTER_HEADER_FONTS = {"Gill-Blk", "Gill-Bk"}
REFERENCE_HEADING_TEXT = {"References", "REFERENCES"}


# ==========================================================
# Utility Functions
# ==========================================================

def normalize_unicode(text):
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = unidecode(text)
    text = text.replace("\ufb01", "fi").replace("\ufb02", "fl")
    return text


def fix_hyphenation(text):
    """Rejoin words split by end-of-line hyphens."""
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)
    text = re.sub(r'(\w)-\s+(\w)', r'\1\2', text)
    return text


def clean_common_acm_artifacts(text):
    text = re.sub(
        r'\d+\s*i\s*n\s*t\s*e\s*r\s*a\s*c\s*t\s*i\s*o\s*n\s*s.*?\n',
        '', text, flags=re.I
    )
    text = re.sub(
        r'\s*Permission to make digital or hard copies.*?\$[\d.]+\.\s*',
        ' ', text, flags=re.S
    )
    text = re.sub(r'^ACM\b.*?$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^Copyright\b.*?$', '', text, flags=re.MULTILINE)
    text = re.sub(
        r'^\s*\u00a9\s*\d{4}\s+ACM\b.*$', '', text, flags=re.MULTILINE
    )
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def _font_matches(font_name, font_set):
    """Check if a font name matches any prefix in a font set."""
    return any(prefix in font_name for prefix in font_set)


def spans_to_text_line(spans):
    """
    Join spans from a single PDF line into text with proper spacing.
    Adjacent spans within the same line typically need spaces between them
    only when the previous span doesn't end with a space and the next
    doesn't start with punctuation.
    """
    if not spans:
        return ""
    parts = []
    for i, s in enumerate(spans):
        t = s["text"]
        if i > 0 and t and parts:
            prev = parts[-1]
            # Don't add space if previous ends with space/hyphen
            if prev and not prev.endswith((" ", "-")):
                # Don't add space if current starts with punctuation
                if not t.startswith((" ", ",", ".", ";", ":", ")", "]", "'")):
                    # Check if this is a continuation of a word
                    # (e.g., drop cap "D" + "rudgery")
                    prev_char = prev[-1] if prev else ""
                    first_char = t[0] if t else ""
                    if prev_char.isupper() and first_char.islower():
                        # Likely a drop cap continuation, no space
                        pass
                    else:
                        parts.append(" ")
        parts.append(t)
    return "".join(parts).strip()


def get_spans(page):
    """Get flat list of spans with position info for metadata detection."""
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
                    "font": span.get("font", ""),
                    "y": span["bbox"][1],
                    "x": span["bbox"][0],
                    "bbox": span["bbox"],
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
        self.author_bios = ""

    # ------------------------------------------------------
    # LINE-LEVEL EXTRACTION
    # ------------------------------------------------------

    def _estimate_body_size(self, data):
        """Find the most common non-bold font size on a page."""
        counts = {}
        for block in data["blocks"]:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    font = span.get("font", "")
                    if (span["text"].strip()
                            and "Bold" not in font
                            and not _font_matches(font, TITLE_FONT_PREFIXES)
                            and not _font_matches(font, ABSTRACT_FONTS)):
                        sz = round(span["size"])
                        counts[sz] = counts.get(sz, 0) + 1
        return max(counts, key=counts.get) if counts else 10

    def get_page_lines(self, page):
        """
        Extract individual text lines with classification metadata.
        Returns list of dicts: x0, y0, x1, y1, text, line_type, spans.
        line_type is one of: heading, body, abstract, figure_caption,
        reference_heading, author_bio, title, author_byline,
        footer_header, noise.
        """
        data = page.get_text("dict")
        body_size = self._estimate_body_size(data)
        page_width = page.rect.width
        lines = []
        for raw_block in data["blocks"]:
            if "lines" not in raw_block:
                continue
            for raw_line in raw_block["lines"]:
                line_spans = [s for s in raw_line["spans"] if s["text"]]
                if not line_spans:
                    continue
                text = spans_to_text_line(line_spans)
                if not text:
                    continue
                x0, y0, x1, y1 = raw_line["bbox"]
                first_font = line_spans[0].get("font", "")
                first_size = line_spans[0]["size"]
                line_type = self._classify_line(
                    text, line_spans, first_font, first_size,
                    body_size, x0, x1, page_width
                )
                lines.append({
                    "x0": x0, "y0": y0, "x1": x1, "y1": y1,
                    "text": text, "line_type": line_type,
                    "font": first_font, "size": first_size,
                    "body_size": body_size, "spans": line_spans,
                })
        return lines

    def _classify_line(self, text, spans, first_font, first_size,
                       body_size, x0, x1, page_width):
        """Classify a line by its role in the document."""
        # Footer/header
        if _font_matches(first_font, FOOTER_HEADER_FONTS):
            return "footer_header"
        # Title font
        if _font_matches(first_font, TITLE_FONT_PREFIXES):
            return "title"
        # Abstract/intro blurb font
        if _font_matches(first_font, ABSTRACT_FONTS):
            return "abstract"
        # Decorative noise (single-char non-alnum)
        stripped = text.strip()
        if len(stripped) <= 2 and not stripped.isalnum():
            return "noise"
        # Reference heading in non-heading font (e.g., GaramondThree-BoldSC)
        # Check before narrow-block filter since "References" can be narrow.
        if (stripped in REFERENCE_HEADING_TEXT
                and _font_matches(first_font, AUTHOR_BIO_FONTS)):
            return "reference_heading"
        # Very narrow blocks (margin labels, sidebar text)
        width = x1 - x0
        if width < page_width * 0.08:
            return "noise"
        # Section heading: all spans are heading font at body size+
        non_empty = [s for s in spans if s["text"].strip()]
        all_heading_font = all(
            _font_matches(s.get("font", ""), HEADING_FONTS)
            and round(s["size"]) >= body_size
            for s in non_empty
        )
        if all_heading_font and not re.match(r'^(Figure|Table|Fig\.)\s', text):
            # Distinguish section headings from figure captions
            if stripped in REFERENCE_HEADING_TEXT:
                return "reference_heading"
            return "heading"
        # Figure/table caption (bold heading font, smaller size)
        if (all(_font_matches(s.get("font", ""), HEADING_FONTS)
                for s in non_empty)
                and first_size < body_size):
            return "figure_caption"
        if re.match(r'^(Figure|Table|Fig\.)\s+\d', text):
            return "figure_caption"
        # Author bio line (bold small-caps name font)
        if (_font_matches(first_font, AUTHOR_BIO_FONTS)
                and first_size <= body_size + 1
                and stripped not in REFERENCE_HEADING_TEXT):
            return "author_bio"
        # Author byline (italic, larger than body, near title area)
        if ("Italic" in first_font and first_size > body_size + 2
                and "Semibold" not in first_font
                and "Bold" not in first_font):
            return "author_byline"
        return "body"

    # ------------------------------------------------------
    # COLUMN-AWARE EXTRACTION
    # ------------------------------------------------------

    def extract_column_text(self):
        """Build reading-order text from all pages."""
        pages_text = []
        for page in self.doc:
            page_height = page.rect.height
            page_width = page.rect.width
            top_margin = page_height * 0.08
            bottom_margin = page_height * 0.93
            lines = self.get_page_lines(page)
            # Filter non-content lines
            filtered = []
            for ln in lines:
                lt = ln["line_type"]
                if lt in ("footer_header", "title", "noise",
                          "author_byline"):
                    continue
                if ln["y0"] < top_margin and lt != "abstract":
                    continue
                if ln["y1"] > bottom_margin:
                    continue
                filtered.append(ln)
            if not filtered:
                pages_text.append("")
                continue
            page_text = self._order_page_lines(
                filtered, page_width
            )
            pages_text.append(page_text)
        self.raw_text = "\n".join(pages_text)

    def _order_page_lines(self, lines, page_width):
        """
        Order lines in reading order for a page.
        Detects two-column regions and orders left-then-right within them.
        """
        mid_x = page_width / 2
        gutter_margin = 20  # tolerance for column assignment
        # Classify each line as left, right, or full-width
        for ln in lines:
            w = ln["x1"] - ln["x0"]
            if (ln["x0"] < mid_x - gutter_margin
                    and ln["x1"] > mid_x + gutter_margin
                    and w > page_width * 0.55):
                ln["_col"] = "full"
            elif ln["x0"] < mid_x - gutter_margin:
                ln["_col"] = "left"
            else:
                ln["_col"] = "right"
        # Find where two-column layout begins: first y where there are
        # both left and right lines overlapping vertically
        col_start_y = self._find_column_start(lines)
        # Split lines into pre-column and column regions
        pre_column = [ln for ln in lines if ln["y0"] < col_start_y]
        in_column = [ln for ln in lines if ln["y0"] >= col_start_y]
        # Pre-column: group abstract lines first (they flow into body),
        # then remaining lines by y position.
        abstract_lines = [ln for ln in pre_column
                          if ln["line_type"] == "abstract"]
        other_pre = [ln for ln in pre_column
                     if ln["line_type"] != "abstract"]
        abstract_lines.sort(key=lambda ln: (ln["y0"], ln["x0"]))
        other_pre.sort(key=lambda ln: (ln["y0"], ln["x0"]))
        pre_column = abstract_lines + other_pre
        # In-column: left col top-to-bottom, then right col top-to-bottom
        left_col = [ln for ln in in_column if ln["_col"] in ("left", "full")]
        right_col = [ln for ln in in_column if ln["_col"] == "right"]
        left_col.sort(key=lambda ln: ln["y0"])
        right_col.sort(key=lambda ln: ln["y0"])
        ordered = pre_column + left_col + right_col
        return self._lines_to_markdown(ordered)

    def _find_column_start(self, lines):
        """
        Find the y coordinate where two-column layout begins.
        This is the first y where left and right lines coexist at
        overlapping vertical positions.
        """
        left_lines = sorted(
            [ln for ln in lines if ln["_col"] == "left"],
            key=lambda ln: ln["y0"]
        )
        right_lines = sorted(
            [ln for ln in lines if ln["_col"] == "right"],
            key=lambda ln: ln["y0"]
        )
        if not left_lines or not right_lines:
            # No two-column layout; return a large value
            return float("inf")
        # For each left line, check if any right line overlaps vertically
        # within a tolerance band
        band = 30  # vertical overlap tolerance
        for ll in left_lines:
            for rl in right_lines:
                # Check if they overlap: ll.y0..ll.y1 overlaps rl.y0..rl.y1
                overlap = (
                    ll["y0"] <= rl["y1"] + band
                    and rl["y0"] <= ll["y1"] + band
                )
                if overlap:
                    # Skip if the left line is abstract (it's an intro blurb,
                    # not a true column)
                    if ll["line_type"] == "abstract":
                        continue
                    return min(ll["y0"], rl["y0"])
        return float("inf")

    def _lines_to_markdown(self, lines):
        """
        Convert ordered lines into markdown text.
        Merges consecutive body lines into paragraphs.
        """
        if not lines:
            return ""
        paragraphs = []
        current_lines = []
        current_kind = "body"

        def flush():
            nonlocal current_lines, current_kind
            if not current_lines:
                return
            text = " ".join(current_lines).strip()
            text = re.sub(r' +', ' ', text)
            if text:
                paragraphs.append((current_kind, text))
            current_lines = []
            current_kind = "body"

        prev_line = None
        for ln in lines:
            text = ln["text"].strip()
            if not text:
                continue
            lt = ln["line_type"]
            # Figure captions - skip (lower priority per instructions)
            if lt == "figure_caption":
                continue
            # Reference heading
            if lt == "reference_heading":
                flush()
                paragraphs.append(("ref_heading", text))
                prev_line = ln
                continue
            # Section heading
            if lt == "heading":
                flush()
                paragraphs.append(("heading", text))
                prev_line = ln
                continue
            # Author bio: each bio starts with a bold name
            if lt == "author_bio":
                # If we're already collecting a bio and this starts a new
                # name, flush
                if current_kind == "author_bio" and current_lines:
                    first_span_font = ln["spans"][0].get("font", "")
                    if _font_matches(first_span_font, AUTHOR_BIO_FONTS):
                        flush()
                elif current_kind != "author_bio":
                    flush()
                current_kind = "author_bio"
                current_lines.append(text)
                prev_line = ln
                continue
            # Abstract text: treat as body (it flows into the first paragraph)
            if lt == "abstract":
                lt = "body"
            # Body text
            if current_kind not in ("body",):
                flush()
            current_lines.append(text)
            prev_line = ln
        flush()
        # Format to markdown
        parts = []
        for kind, text in paragraphs:
            if kind == "heading":
                parts.append(f"# {text}")
            elif kind == "ref_heading":
                parts.append(f"# {text}")
            elif kind == "author_bio":
                parts.append(text)
            else:
                parts.append(text)
        return "\n\n".join(parts) + "\n\n"

    # ------------------------------------------------------
    # TABLE EXTRACTION
    # ------------------------------------------------------

    def extract_tables_from_page(self, page):
        return []

    # ------------------------------------------------------
    # METADATA EXTRACTION
    # ------------------------------------------------------

    def extract_metadata(self):
        text = self.raw_text[:5000]
        doi_match = re.search(r'10\.\d{4,9}/[-._;()/:A-Z0-9]+', text, re.I)
        if doi_match:
            self.metadata["doi"] = doi_match.group(0)
        self.metadata["source"] = "PDF"
        self.metadata["extracted"] = datetime.now().strftime("%Y-%m-%d")

    # ------------------------------------------------------
    # AUTHOR AND CO-AUTHORS EXTRACTION
    # ------------------------------------------------------

    def detect_authors(self, spans, title_y):
        """Detect author names near the title using font and position."""
        # First try: look for italic spans near title (ACM author bylines)
        byline_spans = [
            s for s in spans
            if "Italic" in s.get("font", "")
            and s["size"] > 12
            and abs(s["y"] - title_y) < 200
        ]
        if byline_spans:
            byline_text = " ".join(s["text"] for s in sorted(
                byline_spans, key=lambda s: (s["y"], s["x"])
            ))
            # Extract names from byline
            name_pat = re.compile(
                r'[A-Z][a-z]+(?:\s[A-Z]\.)?'
                r'\s[A-Z][a-z]+(?:-[A-Z][a-z]+)?'
            )
            names = name_pat.findall(byline_text)
            if names:
                self.metadata["author"] = list(dict.fromkeys(names))[:10]
                return
        # Fallback: general name pattern
        name_pattern = re.compile(
            r'\b[A-Z][a-z]+(?:\s[A-Z]\.)?'
            r'\s[A-Z][a-z]+(?:\s(?:van|de|von)\s[A-Z][a-z]+)?'
        )
        candidates = []
        for s in spans:
            if s["y"] < title_y - 50 or s["y"] > title_y + 260:
                continue
            if s["size"] < 10:
                continue
            candidates.extend(name_pattern.findall(s["text"]))
        authors = list(dict.fromkeys(candidates))
        if authors:
            self.metadata["author"] = authors[:10]

    # ------------------------------------------------------
    # TITLE AND SUBTITLE EXTRACTION
    # ------------------------------------------------------

    def detect_title(self, spans):
        """Find the title as the largest font text in the top region."""
        top_spans = [s for s in spans if s["y"] < 350]
        if not top_spans:
            return None, None, None
        # Look specifically for title font spans
        title_font_spans = [
            s for s in top_spans
            if _font_matches(s.get("font", ""), TITLE_FONT_PREFIXES)
        ]
        if title_font_spans:
            title_font_spans.sort(key=lambda s: (s["y"], s["x"]))
            # Join text, handling drop caps (large initial + smaller rest)
            title = self._join_title_spans(title_font_spans)
            title_y = min(s["y"] for s in title_font_spans)
            largest = max(s["size"] for s in title_font_spans)
            return title, title_y, largest
        # Fallback: largest font spans
        spans_sorted = sorted(top_spans, key=lambda s: -s["size"])
        largest = spans_sorted[0]["size"]
        title_spans = [
            s for s in top_spans
            if largest - 2 <= s["size"] <= largest
        ]
        if not title_spans:
            return None, None, None
        title_spans.sort(key=lambda s: (s["y"], s["x"]))
        title = " ".join(s["text"] for s in title_spans)
        title_y = min(s["y"] for s in title_spans)
        return title, title_y, largest

    def _join_title_spans(self, spans):
        """
        Join title spans, handling decorative drop caps.
        A drop cap is a single uppercase letter at much larger size
        followed by the rest of the word at normal title size.
        """
        if not spans:
            return ""
        parts = []
        for i, s in enumerate(spans):
            t = s["text"]
            if i > 0 and parts:
                prev_text = parts[-1]
                # If previous is a single uppercase letter (drop cap)
                # and current starts with lowercase, join directly
                if (len(prev_text) == 1 and prev_text.isupper()
                        and t and t[0].islower()):
                    parts.append(t)
                    continue
                # Otherwise add space if needed
                if prev_text and not prev_text.endswith(" "):
                    parts.append(" ")
            parts.append(t)
        return "".join(parts).strip()

    def detect_subtitle(self, spans, title_y):
        candidates = [
            s for s in spans
            if title_y < s["y"] < title_y + 120
            and 9 < s["size"] < 13
        ]
        candidates.sort(key=lambda s: (s["y"], s["x"]))
        lines = [s["text"] for s in candidates[:6]]
        if not lines:
            return None
        return " ".join(lines)

    # ------------------------------------------------------
    # REFERENCE SECTION EXTRACTION
    # ------------------------------------------------------

    def extract_references(self):
        """Split body text from references section."""
        patterns = [
            r'\n# References\n',
            r'\n# REFERENCES\n',
            r'\nReferences\n',
            r'\nREFERENCES\n',
        ]
        for pat in patterns:
            match = re.search(pat, self.raw_text)
            if match:
                self.body_text = self.raw_text[:match.start()]
                self.references = self.raw_text[match.end():]
                return
        self.body_text = self.raw_text

    def format_references(self):
        """Format references as numbered list items."""
        if not self.references:
            return ""
        text = self.references.strip()
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text)
        # Detect where author bios begin (Name (email) is a...)
        bio_match = re.search(
            r'\b[A-Z][a-z]+ (?:[A-Z]\. )?[A-Z][a-z]+'
            r'(?:-[A-Z][a-z]+)?\s*\([^)]+@[^)]+\)\s+is\s',
            text
        )
        ref_text = text
        self.author_bios = ""
        if bio_match:
            ref_text = text[:bio_match.start()].strip()
            self.author_bios = text[bio_match.start():].strip()
        # Split on numbered reference pattern: "N. Author"
        entries = re.split(r'(?=\b\d{1,2}\.\s+[A-Z])', ref_text)
        formatted = "# References\n"
        for entry in entries:
            entry = entry.strip()
            if not entry or len(entry) < 10:
                continue
            entry = re.sub(r'^\d{1,2}\.\s+', '', entry)
            entry = fix_hyphenation(entry)
            formatted += f"{entry}\n"
        return formatted

    def format_author_bios(self):
        """Format author bio section with bold names."""
        if not self.author_bios:
            return ""
        text = self.author_bios.strip()
        # Remove copyright notices
        text = re.sub(
            r'\s*\u00a9\s*\d{4}\s+ACM\b.*$', '', text
        )
        text = re.sub(
            r'\s*\(c\)\s*\d{4}\s+ACM\b.*$', '', text, flags=re.I
        )
        # Split on email pattern (each bio starts with Name (email))
        entries = re.split(
            r'(?=\b[A-Z][a-z]+ (?:[A-Z]\. )?[A-Z][a-z]+'
            r'(?:-[A-Z][a-z]+)?\s*\([^)]+@[^)]+\))',
            text
        )
        formatted = "\n------\n\n"
        for entry in entries:
            entry = entry.strip()
            if not entry:
                continue
            # Bold the name (text before the parenthetical email)
            entry = re.sub(
                r'^([A-Z][a-z]+ (?:[A-Z]\. )?[A-Z][a-z]+(?:-[A-Z][a-z]+)?)',
                r'**\1**',
                entry
            )
            formatted += f"{entry}\n"
        formatted += "\n------"
        return formatted

    # ------------------------------------------------------
    # CLEAN + STRUCTURE
    # ------------------------------------------------------

    def clean_and_structure(self):
        text = normalize_unicode(self.body_text)
        text = fix_hyphenation(text)
        text = clean_common_acm_artifacts(text)
        # Remove figure caption lines that leaked through
        text = re.sub(r'^Figure:.*$', '', text, flags=re.MULTILINE)
        # Remove parenthetical sidebar noise like "(TLG, LOC, more)"
        text = re.sub(r'\(TLG,?\s*LOC,?\s*more\)\s*', '', text)
        # Fix URLs broken across lines (e.g., "www.perseus. tufts.edu")
        text = re.sub(
            r'(www\.\w+)\.\s+(\w+\.\w+)', r'\1.\2', text
        )
        # Merge lines inside paragraphs (single newlines become spaces)
        text = re.sub(r'(?<!\n)\n(?!\n|[-*\u2022#])', ' ', text)
        # Collapse excessive blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Merge paragraph fragments split across page boundaries:
        # If a paragraph doesn't end with sentence-ending punctuation,
        # merge it with the following non-heading paragraph.
        text = self._merge_split_paragraphs(text)
        self.body_text = text

    def _merge_split_paragraphs(self, text):
        """
        Merge consecutive body paragraphs that were split at page
        boundaries. A paragraph ending without sentence-ending
        punctuation is joined with the next paragraph if the next
        paragraph doesn't start with a heading marker.
        """
        paragraphs = text.split("\n\n")
        merged = []
        i = 0
        while i < len(paragraphs):
            para = paragraphs[i]
            stripped = para.strip()
            # Never merge headings forward or backward
            is_heading = stripped.startswith('#')
            # If this is a body paragraph that doesn't end with sentence
            # punctuation, merge with the next non-heading paragraph.
            while (i + 1 < len(paragraphs)
                   and stripped
                   and not is_heading
                   and not stripped.endswith(('.', '?', '!', ':', '"'))
                   and not stripped.endswith("''")
                   and not paragraphs[i + 1].strip().startswith('#')
                   and paragraphs[i + 1].strip()):
                i += 1
                para = para.rstrip() + " " + paragraphs[i].lstrip()
                stripped = para.strip()
            merged.append(para)
            i += 1
        return "\n\n".join(merged)

    # ------------------------------------------------------
    # YAML
    # ------------------------------------------------------

    def generate_yaml(self):
        yaml_lines = ["---"]
        for k, v in self.metadata.items():
            if isinstance(v, list):
                yaml_lines.append(f"{k}:")
                for item in v:
                    yaml_lines.append(f'  - "{item}"')
            else:
                yaml_lines.append(f'{k}: "{v}"')
        yaml_lines.append("---\n")
        return "\n".join(yaml_lines)

    # ------------------------------------------------------
    # FULL CONVERSION
    # ------------------------------------------------------

    def convert(self):
        # 1. Extract column text
        self.extract_column_text()
        # 2. Metadata from first pages
        for pg_idx in range(min(2, len(self.doc))):
            spans = get_spans(self.doc[pg_idx])
            if not spans:
                continue
            title, title_y, title_size = self.detect_title(spans)
            if title:
                self.metadata["title"] = title
                subtitle = self.detect_subtitle(spans, title_y)
                if subtitle:
                    self.metadata["subtitle"] = subtitle
                self.detect_authors(spans, title_y)
                break
        # 3. Remaining metadata
        self.extract_metadata()
        # 4. Split references
        self.extract_references()
        # 5. Clean body
        self.clean_and_structure()
        # 6. Build markdown
        markdown = self.generate_yaml()
        markdown += self.body_text.strip() + "\n\n"
        refs = self.format_references()
        if refs:
            markdown += "\n" + refs
        bios = self.format_author_bios()
        if bios:
            markdown += "\n" + bios
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
        print(f"Converted: {pdf.name} -> {output_path.name}")


# ==========================================================
# CLI
# ==========================================================

def main():
    parser = argparse.ArgumentParser(
        description="ACM PDF -> Markdown Converter"
    )
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
