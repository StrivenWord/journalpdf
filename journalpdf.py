# Alpha Version 4.5 - 2026-04-14
"""
ACM-Optimized PDF -> Markdown Pipeline
--------------------------------------

Alpha 4 shifts the document model from a flat block list to an explicit
hierarchical tree. Markdown is rendered as a projection of that structure.
"""

import argparse
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from statistics import median

import pymupdf as fitz  # PyMuPDF
from unidecode import unidecode

HEADING_FONTS = {"GillSans-Bold"}
TITLE_FONT_PREFIXES = {"WatersTitling"}
AUTHOR_BIO_FONTS = {"GaramondThree-BoldSC"}
ABSTRACT_FONTS = {"OfficinaSans-BoldItalic"}
FOOTER_HEADER_FONTS = {"Gill-Blk", "Gill-Bk"}
REFERENCE_HEADING_TEXT = {"References", "REFERENCES"}
FRONTMATTER_Y_LIMIT = 600
INCLUDE_FIGURE_OCR_TEXT = False
GRAPHIC_REGION_MARGIN = 2.0
GRAPHIC_REGION_MIN_WIDTH_RATIO = 0.12
GRAPHIC_REGION_MIN_HEIGHT_RATIO = 0.05
GRAPHIC_REGION_MAX_TEXT_SIZE_RATIO = 0.75


class LineType(Enum):
    HEADING = auto()
    BODY = auto()
    ORDERED_LIST_ITEM = auto()
    ABSTRACT = auto()
    FIGURE_CAPTION = auto()
    FOOTNOTE = auto()
    REFERENCE_HEADING = auto()
    AUTHOR_BIO = auto()
    TITLE = auto()
    AUTHOR_BYLINE = auto()
    FOOTER_HEADER = auto()
    NOISE = auto()


class BlockType(Enum):
    PARAGRAPH = auto()
    HEADING = auto()
    ORDERED_LIST_ITEM = auto()
    REFERENCE_HEADING = auto()
    FOOTNOTE = auto()
    AUTHOR_BIO = auto()
    ABSTRACT = auto()


class NodeType(Enum):
    ROOT = auto()
    SECTION = auto()
    PARAGRAPH = auto()
    ORDERED_LIST = auto()
    ORDERED_LIST_ITEM = auto()
    ABSTRACT = auto()
    AUTHOR_BIO = auto()
    REFERENCE_SECTION = auto()


@dataclass
class HeadingCandidate:
    text: str
    score: float
    level_hint: int | None = None


@dataclass
class ReferenceEntry:
    raw: str
    authors: list[str] = field(default_factory=list)
    title: str = ""
    year: str = ""


@dataclass
class Endnote:
    number: str
    text: str


@dataclass
class Block:
    type: BlockType
    text: str
    level: int | None = None
    lines: list[dict] = field(default_factory=list)
    avg_size: float = 0.0
    page_index: int = 0
    column: str | None = None
    heading_candidate: HeadingCandidate | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class Node:
    type: NodeType
    text: str = ""
    level: int | None = None
    children: list["Node"] = field(default_factory=list)
    references: list[ReferenceEntry] = field(default_factory=list)
    ordered_items: list[str] = field(default_factory=list)


@dataclass
class FrontMatter:
    title: str | None = None
    subtitle: str | None = None
    authors: list[str] = field(default_factory=list)
    affiliations: list[str] = field(default_factory=list)
    doi: str | None = None
    published_date: str | None = None
    conference: str | None = None
    body_start_y: float | None = None
    _raw_lines: list[str] = field(default_factory=list)


@dataclass
class Document:
    frontmatter: FrontMatter = field(default_factory=FrontMatter)
    root: Node = field(default_factory=lambda: Node(NodeType.ROOT))
    endnotes: list[Endnote] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


def normalize_unicode(text):
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = unidecode(text)
    text = text.replace("\ufb01", "fi").replace("\ufb02", "fl")
    return text


def fix_hyphenation(text):
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    text = re.sub(r"(\w)-\s+(\w)", r"\1\2", text)
    return text


def clean_common_artifacts(text):
    text = re.sub(
        r"\d+\s*i\s*n\s*t\s*e\s*r\s*a\s*c\s*t\s*i\s*o\s*n\s*s.*?\n",
        "",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"\s*Permission to make digital or hard copies.*?\$[\d.]+\.\s*",
        " ",
        text,
        flags=re.S,
    )
    text = re.sub(r"^ACM\b.*?$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^Copyright\b.*?$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\u00a9\s*\d{4}\s+ACM\b.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def normalize_whitespace(text):
    return re.sub(r"\s+", " ", text).strip()


def yaml_quote(text):
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def dateform(value):
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, "%d %B %Y")
        except ValueError:
            return value
    return value.strftime("%Y-%m-%d")


def _font_matches(font_name, font_set):
    return any(prefix in font_name for prefix in font_set)


def spans_to_text_line(spans):
    if not spans:
        return ""
    parts = []
    for i, span in enumerate(spans):
        text = span["text"]
        if i > 0 and text and parts:
            prev = parts[-1]
            if prev and not prev.endswith((" ", "-")):
                if not text.startswith((" ", ",", ".", ";", ":", ")", "]", "'")):
                    prev_char = prev[-1] if prev else ""
                    first_char = text[0] if text else ""
                    if not (prev_char.isupper() and first_char.islower()):
                        parts.append(" ")
        parts.append(text)
    return "".join(parts).strip()


def get_spans(page):
    data = page.get_text("dict")
    spans = []
    for block in data["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span["text"].strip()
                if not text:
                    continue
                spans.append(
                    {
                        "text": text,
                        "size": span["size"],
                        "font": span.get("font", ""),
                        "y": span["bbox"][1],
                        "x": span["bbox"][0],
                        "bbox": span["bbox"],
                    }
                )
    return spans


class PdfConverter:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.y_start = None
        self._footnote_lines = []

    def _fontsize(self, data):
        counts = {}
        for block in data["blocks"]:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text:
                        continue
                    size = round(span["size"])
                    counts[size] = counts.get(size, 0) + 1
        return max(counts, key=counts.get) if counts else 10

    def get_page_lines(self, page):
        data = page.get_text("dict")
        body_size = self._fontsize(data)
        page_width = page.rect.width
        graphic_regions = self._graphic_text_exclusion_regions(page, page_width, page.rect.height)
        lines = []
        for raw_block in data["blocks"]:
            if "lines" not in raw_block:
                continue
            for raw_line in raw_block["lines"]:
                line_spans = [span for span in raw_line["spans"] if span["text"]]
                if not line_spans:
                    continue
                text = spans_to_text_line(line_spans)
                if not text:
                    continue
                x0, y0, x1, y1 = raw_line["bbox"]
                if self._is_excluded_figure_text(raw_line, line_spans, body_size, graphic_regions):
                    continue
                first_font = line_spans[0].get("font", "")
                first_size = line_spans[0]["size"]
                line_type = self._lineclass(
                    text, line_spans, first_font, first_size, body_size, x0, x1, page_width
                )
                lines.append(
                    {
                        "x0": x0,
                        "y0": y0,
                        "x1": x1,
                        "y1": y1,
                        "text": text,
                        "line_type": line_type,
                        "font": first_font,
                        "size": first_size,
                        "body_size": body_size,
                        "spans": line_spans,
                    }
                )
        return lines

    def _graphic_text_exclusion_regions(self, page, page_width, page_height):
        if INCLUDE_FIGURE_OCR_TEXT:
            return []
        regions = []
        min_width = page_width * GRAPHIC_REGION_MIN_WIDTH_RATIO
        min_height = page_height * GRAPHIC_REGION_MIN_HEIGHT_RATIO

        for image in page.get_image_info(xrefs=True):
            bbox = image.get("bbox")
            if not bbox:
                continue
            rect = fitz.Rect(bbox)
            if rect.width >= min_width and rect.height >= min_height:
                regions.append(rect)

        for drawing in page.get_drawings():
            rect = drawing.get("rect")
            if rect is None:
                continue
            rect = fitz.Rect(rect)
            if rect.width >= min_width and rect.height >= min_height:
                regions.append(rect)

        return self._merge_rects(regions, margin=GRAPHIC_REGION_MARGIN)

    def _merge_rects(self, rects, margin=0.0):
        merged = []
        for rect in sorted(rects, key=lambda item: (item.y0, item.x0, item.y1, item.x1)):
            candidate = fitz.Rect(rect)
            if margin:
                candidate = fitz.Rect(
                    candidate.x0 - margin,
                    candidate.y0 - margin,
                    candidate.x1 + margin,
                    candidate.y1 + margin,
                )
            for index, existing in enumerate(merged):
                if candidate.intersects(existing):
                    merged[index] = existing | candidate
                    break
            else:
                merged.append(candidate)

        changed = True
        while changed:
            changed = False
            compacted = []
            for rect in merged:
                for index, existing in enumerate(compacted):
                    if rect.intersects(existing):
                        compacted[index] = existing | rect
                        changed = True
                        break
                else:
                    compacted.append(rect)
            merged = compacted
        return merged

    def _is_excluded_figure_text(self, raw_line, spans, body_size, graphic_regions):
        if INCLUDE_FIGURE_OCR_TEXT or not graphic_regions or not spans:
            return False

        max_span_size = max(span.get("size", 0) for span in spans)
        if max_span_size > body_size * GRAPHIC_REGION_MAX_TEXT_SIZE_RATIO:
            return False

        span_points = [fitz.Point(*span["origin"]) for span in spans if span.get("origin")]
        if not span_points:
            x0, y0, x1, y1 = raw_line["bbox"]
            span_points = [fitz.Point((x0 + x1) / 2, (y0 + y1) / 2)]

        for region in graphic_regions:
            if all(region.contains(point) for point in span_points):
                return True
        return False

    def _lineclass(self, text, spans, first_font, first_size, body_size, x0, x1, page_width):
        stripped = text.strip()
        text_norm = stripped.lower()
        if re.fullmatch(r"abstract[:.\-–—]?", text_norm):
            return LineType.ABSTRACT
        if stripped.lower().startswith("references"):
            return LineType.REFERENCE_HEADING
        if self._looks_like_ordered_list_item(stripped):
            return LineType.ORDERED_LIST_ITEM
        if re.match(r"^(Figure|Table|Fig\.)\s+\d", stripped):
            return LineType.FIGURE_CAPTION
        if len(stripped) <= 2 and not stripped.isalnum():
            return LineType.NOISE
        if (x1 - x0) < page_width * 0.08:
            return LineType.NOISE
        return LineType.BODY

    # def _assign_columns(self, lines):
    #     """
    #     Assign each line to a column using clustering instead of midpoint.
    #     """
    #     xs = sorted(line["x0"] for line in lines)
    #     if not xs:
    #         return
    #     # Baseline -- median split
    #     mid = xs[len(xs) // 2]
    #     for line in lines:
    #         if line["x0"] < mid:
    #             line["_col"] = "left"
    #         else:
    #             line["_col"] = "right"

    def _order_page_lines(self, lines, page_width, page_height):
        mid_x = page_width / 2
        gutter_margin = 20
        lineparts = []
        for line in lines:
            width = line["x1"] - line["x0"]
            if (
                line["x0"] < mid_x - gutter_margin
                and line["x1"] > mid_x + gutter_margin
                and width > page_width * 0.55
            ):
                line["_col"] = "full"
            else:
                lineparts.append(line)
        xs = sorted(line["x0"] for line in lineparts)
        if xs:
            split = xs[len(xs) // 2]
            for line in lineparts:
                if line["x0"] < split:
                    line["_col"] = "left"
                else:
                    line["_col"] = "right"
        self._mark_page_footnotes(lines, page_width, page_height)
        col_start_y = self._find_column_start(lines)
        pre_column = [line for line in lines if line["y0"] < col_start_y]
        in_column = [line for line in lines if line["y0"] >= col_start_y]
        abstract_lines = [line for line in pre_column if line["line_type"] is LineType.ABSTRACT]
        other_pre = [line for line in pre_column if line["line_type"] is not LineType.ABSTRACT]
        abstract_lines.sort(key=lambda line: (line["y0"], line["x0"]))
        other_pre.sort(key=lambda line: (line["y0"], line["x0"]))
        left_col = [line for line in in_column if line["_col"] in ("left", "full")]
        right_col = [line for line in in_column if line["_col"] == "right"]
        left_col.sort(key=lambda line: line["y0"])
        right_col.sort(key=lambda line: line["y0"])
        return abstract_lines + other_pre + left_col + right_col

    def _mark_page_footnotes(self, lines, page_width, page_height):
        footnote_start_pattern = re.compile(r"^(\d+)\s+")
        mid_x = page_width / 2
        footnote_band_top = page_height * 0.75
        for column in ("left", "right"):
            column_lines = sorted(
                [
                    line
                    for line in lines
                    if ("left" if line["x0"] < mid_x else "right") == column
                ],
                key=lambda line: (line["y0"], line["x0"]),
            )
            starts = []
            for line in column_lines:
                text = line["text"].strip()
                if line["y0"] < footnote_band_top:
                    continue
                if line["size"] > line["body_size"] - 2:
                    continue
                match = footnote_start_pattern.match(text)
                if not match:
                    continue
                starts.append((line, match.group(1)))

            for index, (start_line, number) in enumerate(starts):
                next_start_y = starts[index + 1][0]["y0"] if index + 1 < len(starts) else float("inf")
                for line in column_lines:
                    if line["y0"] < start_line["y0"] or line["y0"] >= next_start_y:
                        continue
                    if line["line_type"] is LineType.NOISE:
                        continue
                    line["line_type"] = LineType.FOOTNOTE
                    line["_footnote_number"] = number

    def _find_column_start(self, lines):
        left_lines = sorted(
            [line for line in lines if line["_col"] == "left"], key=lambda line: line["y0"]
        )
        right_lines = sorted(
            [line for line in lines if line["_col"] == "right"], key=lambda line: line["y0"]
        )
        if not left_lines or not right_lines:
            return float("inf")
        band = 30
        for left in left_lines:
            for right in right_lines:
                overlap = left["y0"] <= right["y1"] + band and right["y0"] <= left["y1"] + band
                if overlap:
                    if left["line_type"] is LineType.ABSTRACT:
                        continue
                    return min(left["y0"], right["y0"])
        return float("inf")

    def extract_raw_lines(self):
        all_ordered_lines = []
        all_footnote_lines = []
        for page_index, page in enumerate(self.doc):
            page_height = page.rect.height
            page_width = page.rect.width
            top_margin = page_height * 0.08
            bottom_margin = page_height * 0.93
            lines = self.get_page_lines(page)
            filtered = []
            for line in lines:
                line["page_index"] = page_index
                line["page_width"] = page_width
                line["page_height"] = page_height
                lt = line["line_type"]
                if lt in (LineType.FOOTER_HEADER, LineType.TITLE, LineType.NOISE, LineType.AUTHOR_BYLINE):
                    continue
                if page_index == 0 and self.y_start is not None and line["y0"] < self.y_start:
                    continue
                if line["y0"] < top_margin and lt != LineType.ABSTRACT:
                    continue
                if line["y1"] > bottom_margin:
                    continue
                filtered.append(line)
            if not filtered:
                continue
            ordered = self._order_page_lines(filtered, page_width, page_height)
            for line in ordered:
                if line["line_type"] is LineType.FOOTNOTE:
                    all_footnote_lines.append(line)
                else:
                    all_ordered_lines.append(line)
        self._footnote_lines = all_footnote_lines
        return all_ordered_lines

    def build_document(self, lines, doc=None):
        doc = doc or Document()
        if not lines:
            return doc
        groups = self._group_lines(lines)
        blocks = []
        for group in groups:
            block = self._lines_to_block(group)
            if block is not None:
                blocks.append(block)
        blocks = self.split_embedded_headings(blocks)
        blocks = self.detect_heading_candidates(blocks)
        blocks = self.resolve_heading_levels(blocks)
        doc.root = self.build_hierarchy(blocks)
        doc.metadata["block-count"] = len(blocks)
        return doc

    def _group_lines(self, lines):
        if not lines:
            return []
        groups = []
        current_group = [lines[0]]
        for index in range(1, len(lines)):
            prev = lines[index - 1]
            curr = lines[index]
            if self._linebreak(prev, curr):
                groups.append(current_group)
                current_group = [curr]
            else:
                current_group.append(curr)
        if current_group:
            groups.append(current_group)
        return groups

    def _has_terminal_punctuation(self, text):
        return text.rstrip().endswith((".", "!", "?", ":", ";"))

    def _linebreak(self, prev, curr):
        if prev["page_index"] != curr["page_index"]:
            return True
        if prev["line_type"] != curr["line_type"]:
            return True
        if curr["line_type"] in (LineType.REFERENCE_HEADING, LineType.HEADING):
            return True
        if prev.get("_col") != curr.get("_col"):
            return True

        vertical_gap = curr["y0"] - prev["y1"]
        indent_diff = abs(curr["x0"] - prev["x0"])

        if curr["line_type"] is LineType.ORDERED_LIST_ITEM:
            if self._starts_new_ordered_list_item(curr["text"]):
                return True
            if vertical_gap > prev["body_size"] * 1.35:
                return True
            return False

        if curr["line_type"] in (LineType.BODY, LineType.ABSTRACT, LineType.AUTHOR_BIO):
            same_column_continuation = (
                prev.get("_col") == curr.get("_col")
                and vertical_gap <= prev["body_size"] * 0.9
                and indent_diff <= 12
                and not self._has_terminal_punctuation(prev["text"])
            )
            if same_column_continuation:
                return False
            if vertical_gap > prev["body_size"] * 1.35:
                return True
            if indent_diff > 14 and self._has_terminal_punctuation(prev["text"]):
                return True
            if len(curr["text"].split()) <= 3 and curr["text"][:1].isupper():
                return True
        return False

    def _lines_to_block(self, group):
        if not group:
            return None
        line_type = group[0]["line_type"]
        text = normalize_whitespace(" ".join(line["text"] for line in group))
        if not text:
            return None
        block_type = BlockType.PARAGRAPH
        if line_type is LineType.ABSTRACT:
            block_type = BlockType.ABSTRACT
        elif line_type is LineType.AUTHOR_BIO:
            block_type = BlockType.AUTHOR_BIO
        elif line_type is LineType.ORDERED_LIST_ITEM:
            block_type = BlockType.ORDERED_LIST_ITEM
        elif line_type is LineType.REFERENCE_HEADING:
            block_type = BlockType.REFERENCE_HEADING
        elif line_type is LineType.FOOTNOTE:
            block_type = BlockType.FOOTNOTE
        elif line_type is LineType.HEADING:
            block_type = BlockType.HEADING
        return Block(
            type=block_type,
            text=text,
            lines=group,
            avg_size=sum(line["size"] for line in group) / len(group),
            page_index=group[0]["page_index"],
            column=group[0].get("_col"),
        )

    def _numbered_heading_level(self, text):
        match = re.match(r"^(\d+(?:\.\d+)*)[\s.)-]+", text)
        if not match:
            return None
        return len(match.group(1).split("."))

    def _starts_new_ordered_list_item(self, text):
        return bool(re.match(r"^\d+\.\s+", normalize_whitespace(text)))

    def _looks_like_ordered_list_item(self, text):
        normalized = normalize_whitespace(text)
        if not re.match(r"^\d+\.\s+", normalized):
            return False
        heading_level = self._numbered_heading_level(normalized)
        if heading_level and heading_level > 1:
            return False
        if re.match(r"^\d+\.\s+[A-Z][A-Za-z0-9'\"()/:,&-]*(?:\s+[A-Z][A-Za-z0-9'\"()/:,&-]*){0,6}$", normalized):
            return False
        if re.match(r"^\d+\.\s+[A-Z][^.!?]{1,80}$", normalized) and len(normalized.split()) <= 8:
            return False
        return True

    def _capitalization_headingish(self, text):
        words = text.split()
        if not words:
            return False
        if text.isupper() and len(words) <= 8:
            return True
        acceptable = 0
        for word in words:
            bare = word.strip(",:;()[]")
            if not bare:
                continue
            if bare.lower() in {"and", "of", "the", "in", "for", "to", "on", "a", "an"}:
                acceptable += 1
            elif bare[:1].isupper():
                acceptable += 1
        return acceptable >= max(1, len(words) - 1)

    def split_embedded_headings(self, blocks):
        result = []
        pattern = re.compile(
            r"^(\d+(?:\.\d+)*)[\s.)-]+(.{2,80}?)(?=\s+[A-Z][a-z]+(?:\s+(?:has|have|was|were|is|are|can|may|might|will|would|should)\b|\s+[a-z]))"
        )
        for block in blocks:
            if block.type is not BlockType.PARAGRAPH:
                result.append(block)
                continue
            match = pattern.match(block.text)
            if not match:
                result.append(block)
                continue
            heading_text = f"{match.group(1)} {normalize_whitespace(match.group(2))}".strip()
            remainder = normalize_whitespace(block.text[match.end() :])
            if len(heading_text.split()) > 12 or not remainder:
                result.append(block)
                continue

            heading_block = Block(
                type=BlockType.HEADING,
                text=heading_text,
                lines=block.lines[:1],
                avg_size=block.avg_size,
                page_index=block.page_index,
                column=block.column,
            )
            paragraph_block = Block(
                type=BlockType.PARAGRAPH,
                text=remainder,
                lines=block.lines,
                avg_size=block.avg_size,
                page_index=block.page_index,
                column=block.column,
                metadata=dict(block.metadata),
            )
            result.append(heading_block)
            result.append(paragraph_block)
        return result

    def _looks_like_reference_entry(self, text):
        normalized = normalize_whitespace(text)
        return bool(
            re.match(r"^(?:\[\d+\]|\d+\.)\s+", normalized)
            and (
                normalized.count(",") >= 2
                or re.search(r"\b(19|20)\d{2}\b", normalized)
                or '"' in normalized
            )
        )

    def _looks_like_contact_or_address(self, text):
        lowered = text.lower()
        return bool(
            "@" in text
            or re.search(r"\+\d", text)
            or re.search(r"\b(street|avenue|road|boulevard|suite|inc\.|ma\s+\d{5})\b", lowered)
        )

    def detect_heading_candidates(self, blocks):
        for index, block in enumerate(blocks):
            if block.type not in (BlockType.PARAGRAPH, BlockType.HEADING, BlockType.REFERENCE_HEADING):
                continue
            if block.type is BlockType.REFERENCE_HEADING:
                block.heading_candidate = HeadingCandidate(block.text, 1.0, level_hint=1)
                continue

            text = block.text.strip()
            words = text.split()
            if not text or len(words) > 12:
                continue
            if self._looks_like_reference_entry(text):
                continue
            if self._looks_like_contact_or_address(text):
                continue
            if text.count(",") >= 2 and re.search(r"\b(19|20)\d{2}\b", text):
                continue

            score = 0.0
            level_hint = self._numbered_heading_level(text)
            if level_hint is not None:
                score += 0.55
            if len(words) <= 12:
                score += 0.15
            if self._capitalization_headingish(text):
                score += 0.15
            if not self._has_terminal_punctuation(text):
                score += 0.10

            prev_block = blocks[index - 1] if index > 0 else None
            next_block = blocks[index + 1] if index + 1 < len(blocks) else None
            isolated = False
            if prev_block and prev_block.page_index == block.page_index:
                prev_gap = block.lines[0]["y0"] - prev_block.lines[-1]["y1"]
                if prev_gap > block.lines[0]["body_size"] * 0.8:
                    isolated = True
            if next_block and next_block.page_index == block.page_index:
                next_gap = next_block.lines[0]["y0"] - block.lines[-1]["y1"]
                if next_gap > block.lines[0]["body_size"] * 0.8:
                    isolated = True
            if isolated:
                score += 0.15
            if block.avg_size > block.lines[0]["body_size"] + 0.75:
                score += 0.10

            if not isolated and level_hint is None and block.avg_size <= block.lines[0]["body_size"] + 1.0:
                continue

            if score >= 0.75:
                block.heading_candidate = HeadingCandidate(text=text, score=score, level_hint=level_hint)
                block.type = BlockType.HEADING
        return blocks

    def resolve_heading_levels(self, blocks):
        paragraph_sizes = [
            block.avg_size
            for block in blocks
            if block.type is BlockType.PARAGRAPH and block.heading_candidate is None
        ]
        body_size = median(paragraph_sizes) if paragraph_sizes else 10.0

        candidate_sizes = sorted(
            {
                round(block.avg_size, 1)
                for block in blocks
                if block.type is BlockType.HEADING and block.heading_candidate is not None
            },
            reverse=True,
        )
        size_to_level = {size: min(index + 1, 6) for index, size in enumerate(candidate_sizes)}

        previous_heading_level = 0
        previous_heading_size = None
        for block in blocks:
            if block.type is not BlockType.HEADING:
                continue
            candidate = block.heading_candidate
            if candidate is None:
                block.level = 1
                continue

            if candidate.level_hint is not None:
                level = candidate.level_hint
            elif block.avg_size > body_size + 0.75:
                level = size_to_level.get(round(block.avg_size, 1), 1)
            elif previous_heading_size is not None and abs(block.avg_size - previous_heading_size) <= 0.35:
                level = previous_heading_level or 1
            else:
                level = 1

            if previous_heading_level and level > previous_heading_level + 1:
                level = previous_heading_level + 1
            block.level = max(1, min(level, 6))
            previous_heading_level = block.level
            previous_heading_size = block.avg_size
        return blocks

    def build_hierarchy(self, blocks):
        root = Node(NodeType.ROOT)
        stack = [root]
        index = 0
        while index < len(blocks):
            block = blocks[index]

            if block.type is BlockType.REFERENCE_HEADING or (
                block.type is BlockType.HEADING and block.text.strip().lower() == "references"
            ):
                level = block.level or 1
                while len(stack) > 1 and (stack[-1].level or 0) >= level:
                    stack.pop()
                node = Node(NodeType.REFERENCE_SECTION, text="References", level=level)
                ordered_items, _ = self.parse_ordered_list(blocks, index + 1)
                if ordered_items:
                    node.ordered_items = ordered_items
                entries, index = self.parse_references(blocks, index + 1)
                node.references = entries
                stack[-1].children.append(node)
                continue

            if block.type is BlockType.HEADING:
                level = block.level or 1
                while len(stack) > 1 and (stack[-1].level or 0) >= level:
                    stack.pop()
                node = Node(NodeType.SECTION, text=block.text, level=level)
                stack[-1].children.append(node)
                stack.append(node)
                index += 1
                continue

            if block.type is BlockType.ORDERED_LIST_ITEM:
                items, index = self.parse_ordered_list(blocks, index)
                if items:
                    stack[-1].children.append(Node(NodeType.ORDERED_LIST, ordered_items=items))
                    continue

            node_type = {
                BlockType.PARAGRAPH: NodeType.PARAGRAPH,
                BlockType.ABSTRACT: NodeType.ABSTRACT,
                BlockType.AUTHOR_BIO: NodeType.AUTHOR_BIO,
            }.get(block.type)
            if node_type is not None:
                stack[-1].children.append(Node(node_type, text=block.text))
            index += 1
        return root

    def parse_references(self, blocks, start_index):
        entries = []
        chunks = []
        current = ""
        index = start_index
        while index < len(blocks):
            block = blocks[index]
            if block.type is BlockType.HEADING or block.type is BlockType.REFERENCE_HEADING:
                break
            text = block.text.strip()
            if not text:
                index += 1
                continue
            starts_new = bool(
                re.match(r"^(?:\[\d+\]|\d+\.)\s+", text)
                or re.match(r"^[A-Z][^.!?]{2,80}\(\d{4}[a-z]?\)", text)
                or re.match(r"^[A-Z][A-Za-z' -]+,\s*[A-Z].{0,40}\d{4}", text)
            )
            if starts_new and current:
                chunks.append(current.strip())
                current = text
            else:
                current = f"{current} {text}".strip() if current else text
            index += 1
        if current:
            chunks.append(current.strip())
        for chunk in chunks:
            entries.append(self._parse_reference_entry(chunk))
        return entries, index

    def parse_ordered_list(self, blocks, start_index):
        items = []
        current = ""
        index = start_index
        while index < len(blocks):
            block = blocks[index]
            if block.type in (BlockType.HEADING, BlockType.REFERENCE_HEADING):
                break
            if block.type not in (BlockType.ORDERED_LIST_ITEM, BlockType.PARAGRAPH):
                break
            text = normalize_whitespace(block.text)
            if not text:
                index += 1
                continue
            if block.type is BlockType.ORDERED_LIST_ITEM and self._starts_new_ordered_list_item(text):
                if current:
                    items.append(current.strip())
                current = text
            elif current:
                current = f"{current} {text}".strip()
            else:
                break
            index += 1
        if current:
            items.append(current.strip())
        return items, index

    def _parse_reference_entry(self, raw):
        cleaned = normalize_whitespace(raw)
        cleaned = re.sub(r"^(?:\[\d+\]|\d+\.)\s*", "", cleaned)
        year_match = re.search(r"\b(19|20)\d{2}[a-z]?\b", cleaned)
        year = year_match.group(0) if year_match else ""

        authors_segment = cleaned
        if year_match:
            authors_segment = cleaned[: year_match.start()].strip(" .,;()")
        elif "." in cleaned:
            authors_segment = cleaned.split(".", 1)[0].strip()

        authors = []
        if authors_segment:
            normalized_authors = authors_segment.replace(" and ", ", ")
            authors = [
                normalize_whitespace(author.strip(" .,;"))
                for author in normalized_authors.split(",")
                if normalize_whitespace(author.strip(" .,;"))
            ]

        title = ""
        quoted = re.search(r'"([^"]+)"', cleaned)
        if quoted:
            title = quoted.group(1).strip()
        elif year_match:
            tail = cleaned[year_match.end() :].strip(" .,:;()")
            sentences = [part.strip() for part in re.split(r"\.\s+", tail) if part.strip()]
            if sentences:
                title = sentences[0]
        else:
            parts = [part.strip() for part in re.split(r"\.\s+", cleaned) if part.strip()]
            if len(parts) >= 2:
                title = parts[1]

        return ReferenceEntry(raw=cleaned, authors=authors, title=title, year=year)

    def build_endnotes(self, footnote_lines):
        grouped = {}
        order = []
        for line in sorted(footnote_lines, key=lambda item: (item["page_index"], item["y0"], item["x0"])):
            number = line.get("_footnote_number")
            if not number:
                continue
            if number not in grouped:
                grouped[number] = []
                order.append(number)
            text = normalize_whitespace(line["text"])
            if not grouped[number]:
                text = re.sub(r"^\d+\s+", "", text)
            grouped[number].append(text)

        endnotes = []
        for number in order:
            note_text = normalize_whitespace(" ".join(grouped[number]))
            if note_text:
                endnotes.append(Endnote(number=number, text=note_text))
        return endnotes

    def render_markdown(self, document):
        parts = []

        def render(node):
            if node.type is NodeType.SECTION:
                parts.append(f'{"#" * (node.level or 1)} {node.text}')
            elif node.type is NodeType.ABSTRACT:
                parts.append("# Abstract")
                if node.text.strip().upper() != "ABSTRACT":
                    parts.append(node.text)
            elif node.type is NodeType.PARAGRAPH:
                parts.append(node.text)
            elif node.type is NodeType.ORDERED_LIST:
                for item in node.ordered_items:
                    parts.append(self._format_ordered_list_item(item))
            elif node.type is NodeType.AUTHOR_BIO:
                parts.append(node.text)
            elif node.type is NodeType.REFERENCE_SECTION:
                parts.append(f'{"#" * (node.level or 1)} {node.text}')
                if node.ordered_items:
                    for item in node.ordered_items:
                        parts.append(self._format_ordered_list_item(item))
                else:
                    for position, entry in enumerate(node.references, start=1):
                        formatted = self._format_reference_entry(entry)
                        if formatted:
                            parts.append(f"{position}. {formatted}")
            for child in node.children:
                render(child)

        for child in document.root.children:
            render(child)
        body = "\n\n".join(part for part in parts if part).strip()
        if document.endnotes:
            endnote_parts = ["---", ""]
            for note in document.endnotes:
                endnote_parts.append(f"[^{note.number}]: {note.text}")
            body = f"{body}\n\n" + "\n".join(endnote_parts)
        return body + "\n"

    def _format_reference_entry(self, entry):
        pieces = []
        if entry.authors:
            pieces.append(", ".join(entry.authors))
        if entry.title:
            pieces.append(entry.title)
        if entry.year:
            pieces.append(entry.year)
        if pieces:
            return ". ".join(piece.rstrip(".") for piece in pieces) + "."
        return entry.raw

    def _format_ordered_list_item(self, text):
        normalized = normalize_whitespace(text)
        match = re.match(r"^(\d+)\.\s*(.*)$", normalized)
        if not match:
            return normalized
        number, body = match.groups()
        return f"{number}. {body.strip()}"

    def extract_tables_from_page(self, page):
        return []

    def _iter_text_nodes(self, node):
        if node.text:
            yield node.text
        for child in node.children:
            yield from self._iter_text_nodes(child)

    def extract_metadata(self, doc):
        text = "\n".join(list(self._iter_text_nodes(doc.root))[:15])
        doc.metadata["source"] = "PDF"
        doc.metadata["date-extracted"] = datetime.now().strftime("%Y-%m-%d")
        if text:
            doc.metadata["excerpt"] = text[:240]

    def _clean_block_text(self, text):
        text = normalize_unicode(text)
        text = fix_hyphenation(text)
        text = clean_common_artifacts(text)
        text = re.sub(r"^(Figure|Table|Fig\.)\s+\d.*$", "", text, flags=re.MULTILINE)
        text = re.sub(r"\(TLG,?\s*LOC,?\s*more\)\s*", "", text)
        text = re.sub(r"(www\.\w+)\.\s+(\w+\.\w+)", r"\1.\2", text)
        return text.strip()

    def _clean_tree(self, node):
        if node.text:
            node.text = self._clean_block_text(node.text)
        if node.type is NodeType.REFERENCE_SECTION:
            for entry in node.references:
                entry.raw = self._clean_block_text(entry.raw)
                entry.title = self._clean_block_text(entry.title)
                entry.authors = [self._clean_block_text(author) for author in entry.authors if author]
            node.ordered_items = [self._clean_block_text(item) for item in node.ordered_items if item]
        if node.type is NodeType.ORDERED_LIST:
            node.ordered_items = [self._clean_block_text(item) for item in node.ordered_items if item]
        for child in node.children:
            self._clean_tree(child)

    def detect_title(self, spans):
        top_spans = [span for span in spans if span["y"] < 350]
        if not top_spans:
            return None, None, None
        title_font_spans = [
            span for span in top_spans if _font_matches(span.get("font", ""), TITLE_FONT_PREFIXES)
        ]
        if title_font_spans:
            title_font_spans.sort(key=lambda span: (span["y"], span["x"]))
            title = self._join_title_spans(title_font_spans)
            title_y = min(span["y"] for span in title_font_spans)
            largest = max(span["size"] for span in title_font_spans)
            return title, title_y, largest
        spans_sorted = sorted(top_spans, key=lambda span: -span["size"])
        largest = spans_sorted[0]["size"]
        title_spans = [span for span in top_spans if largest - 2 <= span["size"] <= largest]
        if not title_spans:
            return None, None, None
        title_spans.sort(key=lambda span: (span["y"], span["x"]))
        title = " ".join(span["text"] for span in title_spans)
        title_y = min(span["y"] for span in title_spans)
        return title, title_y, largest

    def _join_title_spans(self, spans):
        if not spans:
            return ""
        parts = []
        for i, span in enumerate(spans):
            text = span["text"]
            if i > 0 and parts:
                prev_text = parts[-1]
                if len(prev_text) == 1 and prev_text.isupper() and text and text[0].islower():
                    parts.append(text)
                    continue
                if prev_text and not prev_text.endswith(" "):
                    parts.append(" ")
            parts.append(text)
        return "".join(parts).strip()

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
            "university",
            "institute",
            "college",
            "school",
            "department",
            "laboratory",
            "centre",
            "center",
            "faculty",
        )
        location_markers = ("united states", "germany", "singapore", "belgium", "usa")
        return any(keyword in text_lower for keyword in affiliation_keywords) or any(
            marker in text_lower for marker in location_markers
        )

    def _looks_like_person_name(self, text):
        candidate = normalize_whitespace(text).strip(" ,")
        if not candidate or len(candidate) < 5:
            return False
        if any(char.isdigit() for char in candidate):
            return False
        if self._looks_like_affiliation(candidate):
            return False
        if any(
            token in candidate.lower()
            for token in ("open access", "citation", "published", "accepted", "received")
        ):
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

    def _detect_y_start(self, lines):
        sorted_lines = sorted(lines, key=lambda line: (line["y0"], line["x0"]))
        for line in sorted_lines:
            text = normalize_whitespace(line["text"]).lower()
            if line["line_type"] is LineType.ABSTRACT or text == "abstract":
                return line["y0"]
        for line in sorted_lines:
            if line["line_type"] in (LineType.HEADING, LineType.REFERENCE_HEADING) and line["y0"] > 250:
                return line["y0"]
        lower_page_body_lines = [
            line for line in sorted_lines if line["line_type"] is LineType.BODY and line["y0"] > 350
        ]
        if len(lower_page_body_lines) >= 5:
            return min(line["y0"] for line in lower_page_body_lines)
        return float("inf")

    def fmget(self, doc):
        first_page = self.doc[0]
        lines = self.get_page_lines(first_page)
        if not lines:
            return
        page_width = first_page.rect.width
        self.y_start = self._detect_y_start(lines)
        doc.frontmatter.body_start_y = self.y_start
        top_lines = [line for line in lines if line["y0"] < self.y_start]
        top_lines.sort(key=lambda line: (line["y0"], line["x0"]))
        doc.frontmatter._raw_lines = [normalize_unicode(line["text"]) for line in top_lines]

        left_lines = [
            line
            for line in top_lines
            if line["x0"] < page_width * 0.62 and not self._is_frontmatter_noise_line(line["text"])
        ]
        if not left_lines:
            return

        title_candidates = [line for line in left_lines if line["y0"] > 120]
        if not title_candidates:
            return
        title_size = max(line["size"] for line in title_candidates)
        title_seed = next(
            (line for line in title_candidates if abs(line["size"] - title_size) <= 0.5),
            None,
        )
        if not title_seed:
            return

        title_lines = []
        for line in title_candidates:
            if line["y0"] < title_seed["y0"] - 2:
                continue
            if abs(line["size"] - title_size) > 0.8:
                continue
            if line["x0"] > page_width * 0.62:
                continue
            if title_lines and line["y0"] - title_lines[-1]["y0"] > 22:
                break
            title_lines.append(line)
        if not title_lines:
            return

        doc.frontmatter.title = self._join_frontmatter_lines([line["text"] for line in title_lines])
        title_end_y = max(line["y1"] for line in title_lines)

        open_access_line = next(
            (
                line
                for line in top_lines
                if "open access support provided by:" in line["text"].lower()
            ),
            None,
        )
        author_band_end_y = (
            open_access_line["y0"] if open_access_line is not None else min(title_end_y + 170, FRONTMATTER_Y_LIMIT)
        )
        author_band = [line for line in left_lines if title_end_y < line["y0"] < author_band_end_y]

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
            (
                line["y0"]
                for line in author_band
                if self._extract_author_name_and_affiliation(normalize_unicode(line["text"]))[0]
            ),
            default=None,
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
            match = re.search(r"10\.\d{4,9}/[^\s\")]+", text, re.I)
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
                doc.frontmatter.published_date = normalize_whitespace(text.split(":", 1)[1])
                break

    def generate_yaml(self, doc):
        fm = doc.frontmatter
        yaml_lines = ["---"]
        if fm.title:
            yaml_lines.append(f"title: {yaml_quote(fm.title)}")
        if fm.subtitle:
            yaml_lines.append(f"subtitle: {yaml_quote(fm.subtitle)}")
        if fm.authors:
            yaml_lines.append("authors:")
            for author in fm.authors:
                yaml_lines.append(f"  - {yaml_quote(author)}")
        if fm.affiliations:
            yaml_lines.append("affiliations:")
            for affiliation in fm.affiliations:
                yaml_lines.append(f"  - {yaml_quote(affiliation)}")
        if fm.doi:
            yaml_lines.append(f"doi: {yaml_quote(fm.doi)}")
        if fm.published_date:
            yaml_lines.append(f"date-published: {yaml_quote(dateform(fm.published_date))}")
        if "date-extracted" in doc.metadata:
            yaml_lines.append(f'date-extracted: {yaml_quote(doc.metadata["date-extracted"])}')
        yaml_lines.append("---\n")
        return "\n".join(yaml_lines) + "\n\n"

    def convert(self):
        doc = Document()
        self.fmget(doc)
        raw_lines = self.extract_raw_lines()
        doc = self.build_document(raw_lines, doc=doc)
        doc.endnotes = self.build_endnotes(self._footnote_lines)
        self.extract_metadata(doc)
        self._clean_tree(doc.root)
        for note in doc.endnotes:
            note.text = self._clean_block_text(note.text)
        markdown = self.generate_yaml(doc)
        markdown += self.render_markdown(doc)
        return markdown


def batch_convert(directory):
    pdf_files = list(Path(directory).glob("*.pdf"))
    for pdf in pdf_files:
        converter = PdfConverter(str(pdf))
        output = converter.convert()
        output_path = pdf.with_suffix(".md")
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write(output)
        print(f"Converted: {pdf.name} -> {output_path.name}")


def main():
    parser = argparse.ArgumentParser(description="ACM PDF -> Markdown Converter")
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
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(markdown)
    print(f"Conversion complete: {output_path}")


if __name__ == "__main__":
    main()
