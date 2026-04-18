# What about

This Python script converts PDF documents taken from academic journal
databases into Markdown with YAML frontmatter. It uses the ACM Digital Library
(dl.acm.org) for reference documents, such that the script is currently oriented
toward converting normal articles (rather than conference proceedings) from that
database.

## Goals

A goal is to create a core Python script, a single file that can be integrated
into someone's MacOS or Linux system and used as a command line tool, that will
successfully convert and extract metadata from most typical journal articles
from most any database. Then, as an extension on this core, there would be other
scripts in other repositories specialized for the specific patterns found in
PDFs from different journals, i.e., ACM Digital Library, Pubmed, Library
Journal, etc. Unsure whether the extensions for specific journals would be
importing the core scriopt, or whether they would be self-contained forks.

The basic intent of the exercise of developing this script is to learn how to
adapt a traditional algorithmic extraction script, utilizing AI in the
development process when reasonable to do so without leaving the design and
engineering decisions to agentic AI, in order to be able to reliably process
various kinds of formal documents into consistent Markdown and YAML. There are
many purposes for having consistent Markdown-YAML documents; i.e., for building
knowledgebabes using either deterministic techniques or AI code agents, or for
utilizing with LLM conversations in order to increase reliability of responses
and diminish waste of compute on the LLM trying to understand the verbose and
often messy inconsistent internal formatting of PDF files.

In service of these goals, an obvious milestone will be utilizing OCR to convert
PDF documents that are not vectorized but only scanned as raster images.
Integration with [OCRmyPDF](https://github.com/ocrmypdf/ocrmypdf), an existing
Python integration with the core open source OCR engine,
[Tesseract](https://github.com/tesseract-ocr/tesseract), whether by importing it
or wrapping it as a preliminary call.

# Versioning

Alpha 5 is aiming to move all the heuristic detection functionaltiy that
contains values specific to the ACM Digital Library's PDFs to the  constant
variables near the top of the file, where they can be easily configured. Not yet
ready to build a core generalized script without using ACM as a reference.

## History

Previous versionoing was based on fixing observed problems on rendered output,
sometimes making a point leap after collecting the desired improvements for that
version, describing them in an agent instruction file, then having an AI coding
agent make the transformation to the next level.

# AI Use.

Although AI factored heavily into the research, design, and sometimes even
output of this script, as a whole this project is not an agentic one, nor is it
"vibecoded." AI chats in ChatGPT.com and T3.chat have run code reviews that were
the bases for manually implemented improvements. Initially, the project was
started by a use of OpenAI's Codex API connection to GitHub, followed by some
early use of Claude Code to get an early structure in a working prototype. Codex
and Gemini CLI were used to make more dramatic changes at certain points, as
well as smaller changes.

An effort is made to document what AI sourcing has gone in to each commit in the
commit message.
