# Goal

The objetive of this project is to create a Python script in a single .py file that will accept command line arguments to take as input academic journal articles in PDF format sourced from ACM Digital Library and to create as output well formatted and technically correct Markdown files.

## Secondary Goals

1. The development of the script should proceed in such a way that the specific characteristics of the PDF files from the specific source will be addressed.
2. The development of the script should be generalizable beyond the specific characteristics of the PDFs retrived from the specific source. The script should be designed with possiblities for future generalization to support more kinds of PDFs from different sources with different characteristics.
3. The script should be easily usable from the command line and accept reasonable parameters for accomplishing transformations, including the selection of different kinds of Markdown conventions.
4. The script will output YAML frontmatter at the beginning of each output Markdown file. This YAML section will contain any obvious metadata about the PDF document as a data object, i.e., author, date of publication, etc.

# Project Roadmap

1. Production of the basic script, which must correctly extract Markdown files from PDFs in the same manner as human conversions provided as reference.
2. Improvement of the script to allow for more contingencies regarding technical problems in PDF files and emergent patterns in Markdown syntax, generalizable accross any PDFs likely to be encountered in the ACM Digital Library.
3. Refinement of the YAML frontmatter output, following a structure designed to document information pertaining to the user's research and source discovery process as well as all useful metadata concerning the article, the PDF document, and the publication.
4. Generalization of the Python extraction script and YAML frontmatter conventions to work with other PDFs from other academic sources.
5. Further generalization of the script to also work with PDFs that are not from academic sources.
6. Integration with functionality OCR (through `ocrmypdf` and `tesseract` and possibly image manipulation and extraction tools, scripts, and/or libraries) to correctly convert even PDFs that are scanned images not having vector text data.
7. Reassesment and further development of user interface.
8. Connection with an associated Chromium browser app, which will be developed separately, such that this script would serve as the engine to perform the extraction for the browser app.

# Development Guidelines

This section contains critical information about working with this codebase. Follow these guidelines precisely.

## Core Development Rules

1. Package Management
   - ONLY use uv, NEVER pip
   - Installation: `uv add package`
   - Running tools: `uv run tool`
   - Upgrading: `uv add --dev package --upgrade-package package`
   - FORBIDDEN: `uv pip install`, `@latest` syntax

2. Code Quality
   - Public APIs must have docstrings
   - Functions must be focused and small
   - Line length: 88 chars maximum

3. Testing Requirements
   - Coverage: test edge cases and errors
   - New features require tests
   - Bug fixes require regression tests

4. Code Style
    - PEP 8 naming (snake_case for functions/variables)
    - Class names in PascalCase
    - Constants in UPPER_SNAKE_CASE
    - Document with docstrings
    - Use f-strings for formatting

## Development Philosophy

- **Simplicity**: Write simple, straightforward code
- **Readability**: Make code easy to understand
- **Performance**: Consider performance without sacrificing readability
- **Maintainability**: Write code that's easy to update
- **Testability**: Ensure code is testable
- **Reusability**: Create reusable components and functions
- **Less Code = Less Debt**: Minimize code footprint

## Coding Best Practices

- **Early Returns**: Use to avoid nested conditions
- **Descriptive Names**: Use clear variable/function names (prefix handlers with "handle")
- **Constants Over Functions**: Use constants where possible
- **DRY Code**: Don't repeat yourself
- **Object Oriented Style**: Prefer semantic, intuitive OOP when not verbose
- **Procedural Style**: When OOP would be inappropriately verbose or complicated, utilize clear, traditional, procedural programming style
- **Minimal Changes**: Only modify code related to the task at hand
- **Function Ordering**: Define composing functions before their components
- **TODO Comments**: Mark issues in existing code with "TODO:" prefix
- **Simplicity**: Prioritize simplicity and readability over clever solutions
- **Build Iteratively** Start with minimal functionality and verify it works before adding complexity
- **Run Tests**: Test your code frequently with realistic inputs and validate outputs
- **Build Test Environments**: Create testing environments for components that are difficult to validate directly
- **Functional Code**: Use functional and stateless approaches where they improve clarity
- **Clean logic**: Keep core logic clean and push implementation details to the edges
- **Reduce Blank Lines**: Don't add many unnecessary lines for the sake of visual clarity. Add reasonable spaces between objects and other top-level items, and between major sections of the script file, but don't regularly use blank lines in the middle of functions.

## Error Resolution

1. CI Failures
   - Fix order:
     1. Formatting
     2. Type errors
     3. Linting
   - Type errors:
     - Get full line context
     - Check Optional types
     - Add type narrowing
     - Verify function signatures

2. Common Issues
   - Line length:
     - Break strings with parentheses
     - Multi-line function calls
     - Split imports
   - Types:
     - Add None checks
     - Narrow string types
     - Match existing patterns

3. Best Practices
   - Keep changes minimal
   - Follow existing patterns
   - Document public APIs
   - Test thoroughly
