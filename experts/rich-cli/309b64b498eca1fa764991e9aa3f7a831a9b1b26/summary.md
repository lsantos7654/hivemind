# Rich-CLI Summary

## Repository Purpose

Rich-CLI is a command-line interface toolbox that brings beautiful, formatted output to the terminal. Built on top of the Rich library by Textualize, it provides a powerful `rich` command that transforms plain text, code files, and structured data into richly formatted, syntax-highlighted terminal output. The project aims to make terminal output more readable, accessible, and visually appealing without requiring users to write code.

## Key Features and Capabilities

Rich-CLI offers extensive formatting and display capabilities:

**Syntax Highlighting**: Automatically detects and highlights over 500 programming languages and file formats using Pygments lexers. Supports customizable themes (defaulting to "ansi_dark"), line numbers, indentation guides, and configurable wrapping behavior.

**Specialized Renderers**: Provides dedicated rendering modes for:
- Markdown files with hyperlink support
- JSON with pretty-printing and color highlighting
- CSV/TSV files displayed as formatted tables with auto-detected delimiters
- Jupyter notebooks (.ipynb) with full cell rendering
- ReStructuredText (RST) documents

**Rich Text Markup**: Enables inline styling using console markup syntax (similar to BBCode) for creating styled terminal output with bold, colors, and other text effects.

**Layout and Styling**: Comprehensive control over output presentation including alignment (left/center/right), text justification (left/right/center/full), padding, panel borders (multiple box styles), width constraints, and style application.

**Interactive Pager**: Built-in pager with vi-style navigation (j/k, ctrl-d/ctrl-u) for scrolling through large outputs directly in the terminal.

**Network Support**: Can fetch and display files directly from HTTP/HTTPS URLs, automatically detecting content type via MIME headers.

**Export Functionality**: Saves rendered output to HTML or SVG formats for sharing or embedding in documentation.

## Primary Use Cases and Target Audience

The primary audience includes:

- **Developers and DevOps Engineers**: Quick code review, log file inspection with syntax highlighting, and configuration file viewing
- **Technical Writers**: Previewing markdown documentation and generating formatted output for screenshots
- **Data Analysts**: Viewing CSV data tables and JSON API responses in readable formats
- **Terminal Enthusiasts**: Anyone wanting prettier terminal output without writing scripts

Common workflows include piping command output through rich for formatting, using it as a replacement for `cat` with syntax highlighting, and creating formatted terminal presentations or demonstrations.

## High-Level Architecture

Rich-CLI is architected as a thin CLI wrapper around the Rich library. The main entry point (`__main__.py`) uses Click for command-line argument parsing with a custom `RichCommand` class that provides a richly formatted help display. The core workflow:

1. **Input Processing**: Reads content from files, URLs, or stdin
2. **Format Detection**: Auto-detects format based on file extension or uses explicit flags
3. **Rendering**: Delegates to Rich library components (Syntax, Markdown, JSON, Table, etc.) to create renderables
4. **Output**: Renders to console or exports to HTML/SVG

The codebase is organized into focused modules: markdown rendering customization, an interactive pager based on Textual, and Windows terminal compatibility utilities.

## Related Projects and Dependencies

Rich-CLI depends on several key libraries:

- **Rich** (>= 12.4.0): The core rendering engine providing all formatting capabilities
- **Click** (>= 8.0.0): Command-line interface framework
- **Textual** (>= 0.1.18): Terminal UI framework powering the interactive pager
- **rich-rst** (>= 1.1.7): ReStructuredText rendering support
- **requests** (>= 2.0.0): HTTP client for fetching remote resources
- **Pygments**: Syntax highlighting (indirect dependency via Rich)

Rich-CLI is part of the Textualize ecosystem, developed by the same team behind Rich and Textual. It serves as a practical demonstration of Rich's capabilities and provides a no-code solution for users who want Rich's formatting power in shell scripts and command-line workflows. The project supports Python 3.9+ and is distributed via PyPI, Homebrew (macOS), and pipx.

## Project Status

The project is in production/stable status (version 1.8.1 as of 2025-07-04), with active maintenance focusing on bug fixes and dependency updates. Recent changes include modernizing the build system to PEP 621 and Poetry 2.x, dropping Python 3.7/3.8 support, and UTF-8 encoding improvements.
