# Alpha Version 3 - 2026-04-04
"""
ACM-Optimized PDF -> Markdown Pipeline
--------------------------------------

Features:
1. True three-layer architecture (PDF -> Document Model -> Markdown)
2. Type-safe classification with Enums
3. Heuristic paragraph and heading level detection
4. Structured Document Object Model (DOM)

Designed for ACM journals, proceedings, and similar scholarly PDFs.
"""

import re
import sys
import argparse
import pymupdf as fitz  # PyMuPDF
from enum import Enum, auto
from pathlib import Path
from datetime import datetime
from unidecode import unidecode
from datetime import datetime

HEADING_FONTS = {"GillSans-Bold"}
TITLE_FONT_PREFIXES = {"WatersTitling"}
# AUTHOR_BIO_FONTS = {"GaramondThree-BoldSC"}
ABSTRACT_FONTS = {"OfficinaSans-BoldItalic"}
FOOTER_HEADER_FONTS = {"Gill-Blk", "Gill-Bk"}
REFERENCE_HEADING_TEXT = {"References", "REFERENCES"}
FRONTMATTER_Y_LIMIT = 600


# ==========================================================
# Enums and Model Classes (Alpha Version 2)
# ==========================================================

class LineType(Enum):
    HEADING = auto()
    BODY = auto()
    ABSTRACT = auto()
    FIGURE_CAPTION = auto()
    REFERENCE_HEADING = auto()
    AUTHOR_BIO = auto()
    TITLE = auto()
    AUTHOR_BYLINE = auto()
    FOOTER_HEADER = auto()
    NOISE = auto()


class BlockType(Enum):
    PARAGRAPH = auto()
    HEADING = auto()
    REFERENCE_HEADING = auto()
    AUTHOR_BIO = auto()
    TITLE = auto()
    AUTHOR_BYLINE = auto()
    ABSTRACT = auto()


class Block:
    def __init__(self, type: BlockType, text: str, level: int = None):
        self.type = type
        self.text = text
        self.level = level  # for headings

class FrontMatter:
    def __init__(self):
        self.title = None
        self.subtitle = None
        # structured authors
        self.authors = []       # list[str]
        # structured affiliations
        self.affiliations = []  # list[str]
        # other metadata
        self.doi = None
        self.published_date = None
        self.conference = None
        self.body_start_y = None
        # optional raw capture (debugging)
        self._raw_lines = []

class Document:
    def __init__(self):
        self.frontmatter = FrontMatter()
        self.blocks: list[Block] = []
        self.metadata = {}


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


def clean_common_artifacts(text):
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


def normalize_whitespace(text):
    return re.sub(r"\s+", " ", text).strip()


def yaml_quote(text):
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'

def dateform(x):
    if x is None:
        return ""
    if isinstance(x, str):
        try: # Parse date
            x = datetime.strptime(x, "%d %B %Y")
        except ValueError: # fallback
            return x
    return x.strftime("%Y-%m-%d")

# def _font_matches(font_name, font_set):
#     """Check if a font name matches any prefix in a font set."""
#     return any(prefix in font_name for prefix in font_set)


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

class PdfConverter:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.first_page_body_start_y = None

    # ------------------------------------------------------
    # LINE-LEVEL EXTRACTION
    # ------------------------------------------------------

    # def _estimate_body_size(self, data):
    #     """Find the most common non-bold font size on a page."""
    #     counts = {}
    #     for block in data["blocks"]:
    #         if "lines" not in block:
    #             continue
    #         for line in block["lines"]:
    #             for span in line["spans"]:
    #                 font = span.get("font", "")
    #                 if (span["text"].strip()
    #                         and "Bold" not in font
    #                         and not _font_matches(font, TITLE_FONT_PREFIXES)
    #                         and not _font_matches(font, ABSTRACT_FONTS)):
    #                     sz = round(span["size"])
    #                     counts[sz] = counts.get(sz, 0) + 1
    #     return max(counts, key=counts.get) if counts else 10

    def get_page_lines(self, page):
        """
        Extract individual text lines with classification metadata.
        Returns list of dicts: x0, y0, x1, y1, text, line_type (LineType), spans.
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
            return LineType.FOOTER_HEADER
        # Title font
        if _font_matches(first_font, TITLE_FONT_PREFIXES):
            return LineType.TITLE
        # Abstract/intro blurb font
        # if _font_matches(first_font, ABSTRACT_FONTS):
        #     return LineType.ABSTRACT
        text_norm = text.strip().lower()
        if re.fullmatch(r"abstract[:.\-–—]?", text_norm):
            return LineType.ABSTRACT
        # Decorative noise (single-char non-alnum)
        stripped = text.strip()
        if len(stripped) <= 2 and not stripped.isalnum():
            return LineType.NOISE
        # Reference heading in non-heading font (e.g., GaramondThree-BoldSC)
        # Check before narrow-block filter since "References" can be narrow.
        if (stripped in REFERENCE_HEADING_TEXT
                and _font_matches(first_font, AUTHOR_BIO_FONTS)):
            return LineType.REFERENCE_HEADING
        # Very narrow blocks (margin labels, sidebar text)
        width = x1 - x0
        if width < page_width * 0.08:
            return LineType.NOISE
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
                return LineType.REFERENCE_HEADING
            return LineType.HEADING
        # Figure/table caption (bold heading font, smaller size)
        if (all(_font_matches(s.get("font", ""), HEADING_FONTS)
                for s in non_empty)
                and first_size < body_size):
            return LineType.FIGURE_CAPTION
        if re.match(r'^(Figure|Table|Fig\.)\s+\d', text):
            return LineType.FIGURE_CAPTION
        # Author bio line (bold small-caps name font)
        if (_font_matches(first_font, AUTHOR_BIO_FONTS)
                and first_size <= body_size + 1
                and stripped not in REFERENCE_HEADING_TEXT):
            return LineType.AUTHOR_BIO
        # Author byline (italic, larger than body, near title area)
        if ("Italic" in first_font and first_size > body_size + 2
                and "Semibold" not in first_font
                and "Bold" not in first_font):
            return LineType.AUTHOR_BYLINE
        return LineType.BODY

    # ------------------------------------------------------
    # COLUMN-AWARE EXTRACTION
    # ------------------------------------------------------

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
        # Find where two-column layout begins
        col_start_y = self._find_column_start(lines)
        # Split lines into pre-column and column regions
        pre_column = [ln for ln in lines if ln["y0"] < col_start_y]
        in_column = [ln for ln in lines if ln["y0"] >= col_start_y]
        # Pre-column: group abstract lines first, then remaining lines
        abstract_lines = [ln for ln in pre_column
                          if ln["line_type"] is LineType.ABSTRACT]
        other_pre = [ln for ln in pre_column
                     if ln["line_type"] is not LineType.ABSTRACT]
        abstract_lines.sort(key=lambda ln: (ln["y0"], ln["x0"]))
        other_pre.sort(key=lambda ln: (ln["y0"], ln["x0"]))
        pre_column = abstract_lines + other_pre
        # In-column: left col top-to-bottom, then right col top-to-bottom
        left_col = [ln for ln in in_column if ln["_col"] in ("left", "full")]
        right_col = [ln for ln in in_column if ln["_col"] == "right"]
        left_col.sort(key=lambda ln: ln["y0"])
        right_col.sort(key=lambda ln: ln["y0"])
        return pre_column + left_col + right_col

    def _find_column_start(self, lines):
        """Find the y coordinate where two-column layout begins."""
        left_lines = sorted(
            [ln for ln in lines if ln["_col"] == "left"],
            key=lambda ln: ln["y0"]
        )
        right_lines = sorted(
            [ln for ln in lines if ln["_col"] == "right"],
            key=lambda ln: ln["y0"]
        )
        if not left_lines or not right_lines:
            return float("inf")
        band = 30  # vertical overlap tolerance
        for ll in left_lines:
            for rl in right_lines:
                overlap = (
                    ll["y0"] <= rl["y1"] + band
                    and rl["y0"] <= ll["y1"] + band
                )
                if overlap:
                    if ll["line_type"] is LineType.ABSTRACT:
                        continue
                    return min(ll["y0"], rl["y0"])
        return float("inf")

    # ------------------------------------------------------
    # ALPHA VERSION 2 PIPELINE
    # ------------------------------------------------------

    def extract_raw_lines(self):
        """Extract all content lines from the PDF in reading order."""
        all_ordered_lines = []
        for page_index, page in enumerate(self.doc):
            page_height = page.rect.height
            page_width = page.rect.width
            top_margin = page_height * 0.08
            bottom_margin = page_height * 0.93
            lines = self.get_page_lines(page)
            # Filter non-content lines
            filtered = []
            for ln in lines:
                lt = ln["line_type"]
                if lt in (LineType.FOOTER_HEADER, LineType.TITLE, LineType.NOISE,
                          LineType.AUTHOR_BYLINE):
                    continue
                if (page_index == 0 and self.first_page_body_start_y is not None
                        and ln["y0"] < self.first_page_body_start_y):
                    continue
                if ln["y0"] < top_margin and lt != LineType.ABSTRACT:
                    continue
                if ln["y1"] > bottom_margin:
                    continue
                filtered.append(ln)
            if not filtered:
                continue
            ordered = self._order_page_lines(filtered, page_width)
            all_ordered_lines.extend(ordered)
        return all_ordered_lines

    def build_document(self, lines, doc=None):
        """Transform raw lines into a structured Document object."""
        doc = doc or Document()
        if not lines:
            return doc

        groups = self._group_lines(lines)
        for group in groups:
            block = self._lines_to_block(group)
            if block:
                doc.blocks.append(block)
        return doc

    def _group_lines(self, lines):
        """Group consecutive lines into logical clusters."""
        if not lines:
            return []
        groups = []
        current_group = [lines[0]]
        for i in range(1, len(lines)):
            prev = lines[i-1]
            curr = lines[i]
            if self._is_block_break(prev, curr):
                groups.append(current_group)
                current_group = [curr]
            else:
                current_group.append(curr)
        if current_group:
            groups.append(current_group)
        return groups

    def _is_block_break(self, prev, curr):
        """Determine if there should be a break between two lines."""
        # Different line types always cause a break
        if prev["line_type"] != curr["line_type"]:
            return True
        # Specific break logic for body/abstract text
        if curr["line_type"] in (LineType.BODY, LineType.ABSTRACT):
            # Vertical gap heuristic
            vertical_gap = curr["y0"] - prev["y1"]
            # Indentation difference heuristic
            indent_diff = abs(curr["x0"] - prev["x0"])
            # Paragraph break if large gap or significant indent change
            if vertical_gap > prev["body_size"] * 1.2:
                return True
            if indent_diff > 10:
                return True
        # Headings are typically single-line or grouped by type
        if curr["line_type"] in (LineType.HEADING, LineType.REFERENCE_HEADING):
            return True
        return False

    def _heading(self, text):
        t = text.strip()
        # Reject lines that are too long to be headings. 
        if len(t.split()) > 12:
            return False
        # Reject sentences.
        if t.endswith('.') or t.endswith(','):
            return False
        # numbered headings
        if re.match(r'^\d+(\.\d+)*\s+[A-Z]', t):
            return True
        # all-caps headings
        if t.isupper() and 1 <= len(t.split()) <= 8:
            return True
        # subsections -- title case lines
        if (
                len(t.split()) <= 8
                and t[0].isupper()
                and not t.isupper()
            ):
            # Avoid false positives like author names
            if not any(word.islower() for word in t.split()):
                return False
            return True
        return False


    def _lines_to_block(self, group):
        """Convert a group of lines into a single Block."""
        if not group:
            return None
        lt = group[0]["line_type"]
        text = " ".join(ln["text"] for ln in group).strip()
        text = re.sub(r' +', ' ', text)
        if lt is LineType.HEADING:
            level = self._detect_heading_level(text)
            return Block(BlockType.HEADING, text, level=level)
        elif lt is LineType.REFERENCE_HEADING:
            return Block(BlockType.REFERENCE_HEADING, text, level=1)
        elif lt is LineType.AUTHOR_BIO:
            return Block(BlockType.AUTHOR_BIO, text)
        elif lt is LineType.ABSTRACT:
            return Block(BlockType.ABSTRACT, text)
        elif lt is LineType.BODY:
            if self._heading(text):
                level=self._headinglevel(text)
                return Block(BlockType.HEADING, text, level=level)
            return Block(BlockType.PARAGRAPH, text)
        return None

    def _headinglevel(self, text):
        t = text.strip()
        # numbered hierarchy
        match = re.match(r'^(\d+(?:\.\d+)*)\s+', t)
        if match:
            return len(match.group(1).split('.'))
        # abstract, always top-level
        if t.upper() == "ABSTRACT":
            return 1
        # default section level
        return 1

    def render_markdown(self, document):
        """Convert a Document object into a Markdown string."""
        parts = []
        for block in document.blocks:
            if block.type is BlockType.HEADING:
                prefix = "#" * (block.level or 1)
                parts.append(f"{prefix} {block.text}")
            elif block.type is BlockType.REFERENCE_HEADING:
                parts.append(f"# {block.text}")
            elif block.type in (BlockType.PARAGRAPH, BlockType.ABSTRACT,
                                BlockType.AUTHOR_BIO):
                parts.append(block.text)
        return "\n\n".join(parts) + "\n\n"

    # ------------------------------------------------------
    # TABLE EXTRACTION
    # ------------------------------------------------------

    def extract_tables_from_page(self, page):
        return []

    # ------------------------------------------------------
    # METADATA EXTRACTION
    # ------------------------------------------------------

    def extract_metadata(self, doc):
        """Extract DOI and system metadata from the document model."""
        # Use first few blocks for text-based metadata extraction
        text = "\n".join(b.text for b in doc.blocks[:15])
        # doi_match = re.search(r'10\.\d{4,9}/[-._;()/:A-Z0-9]+', text, re.I)
        # if doi_match:
        #     doc.frontmatter.doi = doi_match.group(0)
        # These aren't frontmatter because they're not about the document
        # itself.
        doc.metadata["source"] = "PDF"
        doc.metadata["date-extracted"] = datetime.now().strftime("%Y-%m-%d")

    def _clean_block_text(self, text):
        """Clean individual block text from common artifacts."""
        text = normalize_unicode(text)
        text = fix_hyphenation(text)
        text = clean_common_artifacts(text)
        # Remove figure caption remnants
        text = re.sub(r'^(Figure|Table|Fig\.)\s+\d.*$', '', text, flags=re.MULTILINE)
        # Remove parenthetical sidebar noise
        text = re.sub(r'\(TLG,?\s*LOC,?\s*more\)\s*', '', text)
        # Fix URLs broken across lines
        text = re.sub(r'(www\.\w+)\.\s+(\w+\.\w+)', r'\1.\2', text)
        return text.strip()

    # ------------------------------------------------------
    # AUTHOR AND CO-AUTHORS EXTRACTION
    # ------------------------------------------------------

    # def detect_authors(self, spans, title_y, doc):
    #     """Detect author names near the title using font and position."""
    #     # First try: look for italic spans near title (ACM author bylines)
    #     byline_spans = [
    #         s for s in spans
    #         if "Italic" in s.get("font", "")
    #         and s["size"] > 12
    #         and abs(s["y"] - title_y) < 200
    #     ]
    #     if byline_spans:
    #         byline_text = " ".join(s["text"] for s in sorted(
    #             byline_spans, key=lambda s: (s["y"], s["x"])
    #         ))
    #         # Extract names from byline
    #         name_pat = re.compile(
    #             r'[A-Z][a-z]+(?:\s[A-Z]\.)?'
    #             r'\s[A-Z][a-z]+(?:-[A-Z][a-z]+)?'
    #         )
    #         names = name_pat.findall(byline_text)
    #         if names:
    #             doc.frontmatter.authors = list(dict.fromkeys(names))[:10]
    #             return
        # Fallback: general name pattern
        # name_pattern = re.compile(
        #     r'\b[A-Z][a-z]+(?:\s[A-Z]\.)?'
        #     r'\s[A-Z][a-z]+(?:\s(?:van|de|von)\s[A-Z][a-z]+)?'
        # )
        # candidates = []
        # for s in spans:
        #     if s["y"] < title_y - 50 or s["y"] > title_y + 260:
        #         continue
        #     if s["size"] < 10:
        #         continue
        #     candidates.extend(name_pattern.findall(s["text"]))
        # authors = list(dict.fromkeys(candidates))
        # if authors:
        #     doc.frontmatter.authors = authors[:10]

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

    def _is_frontmatter_noise_line(self, text):
        text_lower = normalize_whitespace(text).lower()
        return (
            not text_lower
            or text_lower.startswith("latest updates:")
            or text_lower == "pdf download"
            or text_lower.startswith("total citations:")
            or text_lower.startswith("total downloads:")
            or text_lower.startswith("published:")
            or text_lower.startswith("accepted:")
            or text_lower.startswith("received:")
            or text_lower.startswith("citation in bibtex format")
            or text_lower.startswith("conference sponsors:")
            or text_lower.startswith("open access support provided by:")
            or text_lower in {"article", "research-article"}
            or text_lower.endswith(".pdf")
        )

    def _looks_like_affiliation(self, text):
        text_lower = normalize_whitespace(text).lower()
        affiliation_keywords = (
            "university", "institute", "college", "school", "department",
            "laboratory", "centre", "center", "faculty"
        )
        location_markers = ("united states", "germany", "singapore", "belgium", "usa")
        return (
            any(keyword in text_lower for keyword in affiliation_keywords)
            or any(marker in text_lower for marker in location_markers)
        )

    def _looks_like_person_name(self, text):
        candidate = normalize_whitespace(text).strip(" ,")
        if not candidate or len(candidate) < 5:
            return False
        if any(char.isdigit() for char in candidate):
            return False
        if self._looks_like_affiliation(candidate):
            return False
        if any(token in candidate.lower() for token in (
            "open access", "citation", "published", "accepted", "received"
        )):
            return False
        tokens = candidate.replace(",", " ").split()
        if len(tokens) < 2 or len(tokens) > 6:
            return False
        valid_tokens = 0
        for token in tokens:
            stripped = token.strip(".,")
            if not stripped:
                continue
            if len(stripped) == 1 and stripped.isalpha():
                valid_tokens += 1
                continue
            if stripped.isupper():
                valid_tokens += 1
                continue
            if stripped[:1].isupper() and stripped[1:].islower():
                valid_tokens += 1
                continue
        return valid_tokens == len(tokens)

    def _normalize_person_name(self, name):
        parts = []
        for token in normalize_whitespace(name).split():
            bare = token.strip(",")
            suffix = "," if token.endswith(",") else ""
            if len(bare) == 2 and bare[1] == "." and bare[0].isalpha():
                parts.append(f"{bare[0].upper()}.{suffix}")
            elif bare.isupper():
                parts.append(f"{bare.title()}{suffix}")
            else:
                parts.append(f"{bare}{suffix}")
        return " ".join(parts)

    def _extract_author_name_and_affiliation(self, text):
        cleaned = normalize_whitespace(text).strip(" ,")
        if not cleaned:
            return None, None
        if "," in cleaned:
            name_part, remainder = cleaned.split(",", 1)
            if self._looks_like_person_name(name_part):
                affiliation = normalize_whitespace(remainder.strip(" ,"))
                if affiliation and self._looks_like_affiliation(affiliation):
                    return self._normalize_person_name(name_part), affiliation
                return self._normalize_person_name(name_part), None
        if self._looks_like_person_name(cleaned):
            return self._normalize_person_name(cleaned), None
        return None, None

    def _join_frontmatter_lines(self, texts):
        parts = []
        for text in texts:
            cleaned = normalize_unicode(text).strip()
            if not cleaned:
                continue
            if parts and parts[-1].endswith("-"):
                parts[-1] = f"{parts[-1]}{cleaned}"
            else:
                parts.append(cleaned)
        return normalize_whitespace(" ".join(parts))

    def _detect_first_page_body_start(self, lines):
        sorted_lines = sorted(lines, key=lambda ln: (ln["y0"], ln["x0"]))
        for line in sorted_lines:
            text = normalize_whitespace(line["text"]).lower()
            if line["line_type"] is LineType.ABSTRACT or text == "abstract":
                return line["y0"]
        for line in sorted_lines:
            if line["line_type"] in (LineType.HEADING, LineType.REFERENCE_HEADING) and line["y0"] > 250:
                return line["y0"]
        lower_page_body_lines = [
            line for line in sorted_lines
            if line["line_type"] is LineType.BODY and line["y0"] > 350
        ]
        if len(lower_page_body_lines) >= 5:
            return min(line["y0"] for line in lower_page_body_lines)
        return float("inf")

    # ------------------------------------------------------
    # FRONTMATTER EXTRACTION
    # ------------------------------------------------------

    def extract_frontmatter(self, doc):
        """
        Extract structured frontmatter (title, authors, affiliations)
        from the first page before body processing.
        """
        first_page = self.doc[0]
        lines = self.get_page_lines(first_page)
        if not lines:
            return
        page_width = first_page.rect.width
        top_lines = [
            ln for ln in lines
            if ln["y0"] < FRONTMATTER_Y_LIMIT
        ]
        top_lines.sort(key=lambda ln: (ln["y0"], ln["x0"]))
        doc.frontmatter._raw_lines = [normalize_unicode(ln["text"]) for ln in top_lines]

        self.first_page_body_start_y = self._detect_first_page_body_start(lines)
        doc.frontmatter.body_start_y = self.first_page_body_start_y

        left_lines = [
            ln for ln in top_lines
            if ln["x0"] < page_width * 0.62
            and not self._is_frontmatter_noise_line(ln["text"])
        ]
        if not left_lines:
            return

        title_candidates = [ln for ln in left_lines if ln["y0"] > 120]
        if not title_candidates:
            return
        title_size = max(ln["size"] for ln in title_candidates)
        title_seed = next(
            (ln for ln in title_candidates if abs(ln["size"] - title_size) <= 0.5),
            None
        )
        if not title_seed:
            return

        title_lines = []
        for ln in title_candidates:
            if ln["y0"] < title_seed["y0"] - 2:
                continue
            if abs(ln["size"] - title_size) > 0.8:
                continue
            if ln["x0"] > page_width * 0.62:
                continue
            if title_lines and ln["y0"] - title_lines[-1]["y0"] > 22:
                break
            title_lines.append(ln)
        if not title_lines:
            return

        doc.frontmatter.title = self._join_frontmatter_lines(
            [ln["text"] for ln in title_lines]
        )
        title_end_y = max(ln["y1"] for ln in title_lines)

        open_access_line = next(
            (ln for ln in top_lines
             if "open access support provided by:" in ln["text"].lower()),
            None
        )
        author_band_end_y = (
            open_access_line["y0"]
            if open_access_line is not None
            else min(title_end_y + 170, FRONTMATTER_Y_LIMIT)
        )
        author_band = [
            ln for ln in left_lines
            if title_end_y < ln["y0"] < author_band_end_y
        ]

        authors = []
        affiliations = []
        for line in author_band:
            text = normalize_unicode(line["text"])
            if "@" in text or "http" in text:
                continue
            author_name, affiliation = self._extract_author_name_and_affiliation(text)
            if author_name and author_name not in authors:
                authors.append(author_name)
            if affiliation and affiliation not in affiliations:
                affiliations.append(affiliation)
        doc.frontmatter.authors = authors
        doc.frontmatter.affiliations = affiliations

        subtitle_lines = []
        first_author_y = min(
            (ln["y0"] for ln in author_band
             if self._extract_author_name_and_affiliation(normalize_unicode(ln["text"]))[0]),
            default=None
        )
        if first_author_y is not None:
            for line in left_lines:
                if not (title_end_y < line["y0"] < first_author_y):
                    continue
                if self._is_frontmatter_noise_line(line["text"]):
                    continue
                subtitle_lines.append(normalize_unicode(line["text"]))
        if subtitle_lines:
            doc.frontmatter.subtitle = self._join_frontmatter_lines(subtitle_lines)

        for line in top_lines:
            text = normalize_unicode(line["text"])
            match = re.search(r'10\.\d{4,9}/[^\s")]+', text, re.I)
            if match:
                doc.frontmatter.doi = match.group(0).rstrip(".,;")
                break
            if "doi/" in text.lower():
                doi_tail = text.lower().split("doi/", 1)[1].strip()
                if doi_tail.startswith("10."):
                    doc.frontmatter.doi = doi_tail.rstrip(".,;")
                    break

        for line in top_lines:
            text = normalize_unicode(line["text"])
            if text.startswith("Published:"):
                doc.frontmatter.published_date = normalize_whitespace(
                    text.split(":", 1)[1]
                )
                break

    # ------------------------------------------------------
    # YAML
    # ------------------------------------------------------

    def generate_yaml(self, doc):
        fm = doc.frontmatter
        yaml_lines = ["---"]
        if fm.title:
            yaml_lines.append(f"title: {yaml_quote(fm.title)}")
        if fm.subtitle:
            yaml_lines.append(f"subtitle: {yaml_quote(fm.subtitle)}")
        if fm.authors:
            yaml_lines.append("authors:")
            for x in fm.authors:
                yaml_lines.append(f"  - {yaml_quote(x)}")
        if fm.affiliations:
            yaml_lines.append("affiliations:")
            for y in fm.affiliations:
                yaml_lines.append(f"  - {yaml_quote(y)}")
        if fm.doi:
            yaml_lines.append(f"doi: {yaml_quote(fm.doi)}")
        if fm.published_date:
            yaml_lines.append(f"date-published: {yaml_quote(dateform(fm.published_date))}")
        # selected metadata projected into frontmatter
        if "date-extracted" in doc.metadata:
            yaml_lines.append(f'date-extracted: {yaml_quote(doc.metadata["date-extracted"])}')
        yaml_lines.append("---\n")
        return "\n".join(yaml_lines) + "\n\n"



    # ------------------------------------------------------
    # FULL CONVERSION
    # ------------------------------------------------------

    def convert(self):
        """Alpha Version 2 pipeline execution."""
        doc = Document()

        # 1. Frontmatter Layer
        self.extract_frontmatter(doc)

        # 2. Extraction Layer
        raw_lines = self.extract_raw_lines()

        # 3. Document Model Layer
        doc = self.build_document(raw_lines, doc=doc)

        # 4. Metadata Layer
        self.extract_metadata(doc)

        # 5. Refinement Layer
        for block in doc.blocks:
            block.text = self._clean_block_text(block.text)

        # 6. Rendering Layer
        markdown = self.generate_yaml(doc)
        markdown += self.render_markdown(doc)
        
        return markdown


# ==========================================================
# Batch Processing
# ==========================================================

def batch_convert(directory):
    pdf_files = list(Path(directory).glob("*.pdf"))
    for pdf in pdf_files:
        converter = PdfConverter(str(pdf))
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
    converter = PdfConverter(args.input)
    markdown = converter.convert()
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown)
    print(f"Conversion complete: {output_path}")


if __name__ == "__main__":
    main()
