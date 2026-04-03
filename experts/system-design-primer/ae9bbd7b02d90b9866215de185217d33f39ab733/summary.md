# System Design Primer — Summary

## Repository Purpose and Goals

The System Design Primer (github.com/donnemartin/system-design-primer) is an organized, open-source educational resource created by Donne Martin. Its dual mission is:

1. **Teach engineers how to design large-scale distributed systems** — providing structured, comprehensive coverage of principles, patterns, and trade-offs involved in building systems at scale.
2. **Prepare candidates for system design interviews** — a required component of the technical interview process at many major technology companies.

The project consolidates resources that were otherwise scattered across the web into a single, curated guide. It is community-maintained and continually updated, with contributions from engineers worldwide.

## Key Features and Capabilities

- **Comprehensive topic index** — Covers the full spectrum of system design: scalability, latency vs. throughput, CAP theorem, consistency patterns, availability patterns, DNS, CDNs, load balancers, reverse proxies, microservices, databases (SQL and NoSQL), caching strategies, asynchronism, communication protocols, and security.
- **System design interview solutions** — Eight fully worked-out system design problems with discussion, back-of-envelope calculations, architecture diagrams, database schema designs, and sample Python code. Problems include: Pastebin/Bit.ly, Twitter timeline/search, web crawler, Mint.com, social graph, key-value store (query cache), Amazon sales ranking, and scaling to millions of users on AWS.
- **Object-oriented design interview solutions** — Six OOD problems with Python implementation files and Jupyter Notebooks covering: hash map, LRU cache, call center, deck of cards, parking lot, and online chat server.
- **Anki flashcard decks** — Three pre-built Anki decks (.apkg files) using spaced repetition for system design concepts, system design exercises, and OO design exercises.
- **Multi-language support** — The main guide is available in English, Japanese (README-ja.md), Simplified Chinese (README-zh-Hans.md), and Traditional Chinese (README-zh-TW.md), with community translation infrastructure for many additional languages.
- **ePub generation** — A shell script (`generate-epub.sh`) uses `pandoc` to compile the README and all system design solution READMEs into a portable ePub book.
- **Real-world architecture references** — Curated links to case studies from Google, Twitter, Facebook, Netflix, Amazon, Uber, and many others, organized by system type (data processing, data store, file system, miscellaneous).
- **Company engineering blog index** — A curated list of engineering blogs from major companies for interview preparation.
- **Study guide by timeline** — Structured guidance for short, medium, and long interview preparation timelines.

## Primary Use Cases and Target Audience

**Target audience:**
- Software engineers preparing for system design interviews at large technology companies
- Developers wanting to deepen their understanding of distributed systems
- Architects or team leads needing a structured reference for system design trade-offs
- Students and self-learners studying computer science systems topics

**Primary use cases:**
- Interview preparation: reviewing design concepts, practicing interview questions, using Anki decks for spaced repetition
- Reference guide: looking up system design patterns, trade-offs, and best practices
- Educational resource: structured learning path from fundamentals to advanced distributed systems topics

## High-Level Architecture Overview

The repository is a **documentation-first project** — there is no deployable application. The architecture is:

- **Core knowledge base**: `README.md` (1,839 lines) is the authoritative English guide covering all system design topics with embedded diagrams, tables, and links.
- **Translated guides**: Parallel README files (`README-ja.md`, `README-zh-Hans.md`, `README-zh-TW.md`) mirror the English content in other languages.
- **Solutions directory** (`solutions/`): Two subdirectories — `system_design/` for full system design problems and `object_oriented_design/` for OOD problems. Each problem has its own directory with a README, Python source files, and architecture diagram images (`.graffle` source + `.png` exports).
- **Resources** (`resources/flash_cards/`): Binary Anki deck files (.apkg).
- **Images** (`images/`): All architecture diagrams and supplementary images referenced in the README.
- **Build tooling**: `generate-epub.sh` uses `pandoc` to concatenate markdown files and produce ePub output.

## Related Projects and Dependencies

- **Interactive Coding Challenges** (github.com/donnemartin/interactive-coding-challenges) — A sister repository by the same author focused on coding interview preparation, including an Anki coding deck.
- **Anki** (apps.ankiweb.net) — Required to use the flashcard decks (.apkg files).
- **pandoc** — Required to run `generate-epub.sh` for ePub generation.
- **mrjob** — Used in `solutions/system_design/pastebin/pastebin.py`, a Python MapReduce framework for the analytics component of the Pastebin solution.
- **Jupyter Notebook** — The OOD solutions include `.ipynb` notebook files alongside `.py` implementations.
