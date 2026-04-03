# System Design Primer — Code Structure

## Annotated Directory Tree

```
system-design-primer/
├── README.md                          # Main English guide (1,839 lines) — the core knowledge base
├── README-ja.md                       # Japanese translation of the full guide
├── README-zh-Hans.md                  # Simplified Chinese translation
├── README-zh-TW.md                    # Traditional Chinese translation
├── CONTRIBUTING.md                    # Contribution guidelines, PR process, translation workflow
├── TRANSLATIONS.md                    # Translation status and maintainer contact list
├── LICENSE.txt                        # License file
├── epub-metadata.yaml                 # Pandoc metadata for ePub generation (title, author, etc.)
├── generate-epub.sh                   # Shell script to build ePub books from markdown using pandoc
│
├── images/                            # All diagram and illustration images
│   ├── jj3A5N8.png                    # AWS scaling diagram
│   ├── jrUBAF7.png                    # System design topic map / index diagram
│   ├── bgLMI2u.png                    # CAP theorem Venn diagram
│   ├── C9ioGtn.png                    # Master-slave replication diagram
│   ├── krAHLGg.png                    # Master-master replication diagram
│   ├── U3qV33e.png                    # Federation / functional partitioning diagram
│   ├── h81n9iK.png                    # Load balancer diagram
│   ├── n41Azff.png                    # Reverse proxy diagram
│   ├── IOyLj4i.jpg                    # DNS hierarchy diagram
│   ├── h9TAuGI.jpg                    # CDN diagram
│   ├── 4edXG0T.png                    # Pastebin architecture diagram
│   ├── bWxPtQA.png                    # Web crawler architecture diagram
│   ├── V5q57vU.png                    # Mint.com architecture diagram
│   ├── cdCv5g7.png                    # Social graph architecture diagram
│   ├── 4j99mhe.png                    # Query cache architecture diagram
│   ├── MzExP06.png                    # Sales rank architecture diagram
│   ├── TcUo2fw.png                    # Twitter timelines diagram
│   ├── OfVllex.png                    # Study guide / interview timeline matrix
│   ├── study_guide.png                # Study guide overview image
│   └── ...                            # Additional architecture and concept diagrams
│
├── resources/
│   └── flash_cards/                   # Anki flashcard decks for spaced repetition study
│       ├── System Design.apkg         # Core system design concepts deck
│       ├── System Design Exercises.apkg  # System design practice problem deck
│       └── OO Design.apkg             # Object-oriented design exercises deck
│
└── solutions/
    ├── system_design/                 # Fully worked system design interview problems
    │   ├── pastebin/                  # Design Pastebin.com (or Bit.ly)
    │   │   ├── README.md              # Full solution walkthrough (use cases → scale)
    │   │   ├── README-zh-Hans.md      # Chinese translation of solution
    │   │   ├── pastebin.py            # MapReduce analytics implementation (mrjob)
    │   │   ├── __init__.py
    │   │   ├── pastebin.graffle       # OmniGraffle source for architecture diagram
    │   │   ├── pastebin.png           # Full architecture diagram
    │   │   ├── pastebin_basic.graffle # OmniGraffle source for simplified diagram
    │   │   └── pastebin_basic.png     # Simplified architecture diagram
    │   ├── twitter/                   # Design Twitter timeline and search
    │   │   ├── README.md
    │   │   ├── README-zh-Hans.md
    │   │   ├── twitter.graffle
    │   │   ├── twitter.png
    │   │   ├── twitter_basic.graffle
    │   │   └── twitter_basic.png
    │   ├── web_crawler/               # Design a web crawler
    │   │   └── README.md
    │   ├── mint/                      # Design Mint.com (personal finance aggregator)
    │   │   └── README.md
    │   ├── social_graph/              # Design data structures for a social network
    │   │   └── README.md
    │   ├── query_cache/               # Design a key-value store for a search engine
    │   │   └── README.md
    │   ├── sales_rank/                # Design Amazon's sales ranking by category
    │   │   └── README.md
    │   ├── scaling_aws/               # Design a system scaling to millions of users on AWS
    │   │   └── README.md
    │   └── template/                  # Template directory for new solution contributions
    │
    └── object_oriented_design/        # Object-oriented design interview problems
        ├── call_center/               # Design a call center dispatch system
        │   ├── call_center.py         # Full Python OOP implementation
        │   ├── call_center.ipynb      # Jupyter Notebook with solution walkthrough
        │   └── __init__.py
        ├── lru_cache/                 # Design a least recently used cache
        │   ├── lru_cache.py           # Python implementation (Node + LinkedList + Cache)
        │   ├── lru_cache.ipynb        # Jupyter Notebook
        │   └── __init__.py
        ├── hash_table/                # Design a hash map
        │   ├── hash_map.ipynb         # Jupyter Notebook (primary artifact)
        │   └── __init__.py
        ├── deck_of_cards/             # Design a deck of cards
        │   ├── deck_of_cards.ipynb
        │   └── __init__.py
        ├── parking_lot/               # Design a parking lot system
        │   ├── parking_lot.ipynb
        │   └── __init__.py
        └── online_chat/               # Design a chat server
            ├── online_chat.ipynb
            └── __init__.py
```

## Module and Package Organization

The repository is organized as a **documentation and educational resource** rather than a software package. There are no `setup.py`, `pyproject.toml`, `package.json`, or equivalent build manifests. The Python files are illustrative implementations embedded within the educational content.

### Primary Organization Principle

Content is organized by **problem type and format**:

1. **Conceptual reference** — The `README.md` and its translations form the definitive reference guide, covering all system design topics from first principles.
2. **Interview exercises with solutions** — The `solutions/` directory groups problems by interview type (system design vs. object-oriented design), with each problem isolated in its own directory containing explanation, code, and diagrams.
3. **Study aids** — The `resources/flash_cards/` directory contains pre-built Anki decks for offline study.

### Main Source Directories

**`solutions/system_design/`** — Eight complete system design problem walkthroughs. Each directory follows a consistent four-step structure in its README:
- Step 1: Outline use cases, constraints, and assumptions
- Step 2: Create a high-level design
- Step 3: Design core components
- Step 4: Scale the design (address bottlenecks)

Some problems include companion Python files demonstrating key algorithmic components (e.g., MapReduce jobs for analytics).

**`solutions/object_oriented_design/`** — Six OOD problem directories. Each contains:
- A `.py` file with the full Python class hierarchy
- A `.ipynb` Jupyter Notebook that serves as the interactive solution presentation
- An `__init__.py` making the directory a Python package

**`images/`** — Flat directory of all images referenced in the markdown files. Images are named with imgur-style random identifiers (e.g., `bgLMI2u.png`) corresponding to the image URLs embedded in the README.

## Key Files and Their Roles

| File | Role |
|------|------|
| `README.md` | The 1,839-line core knowledge base — the primary learning resource and interview guide |
| `solutions/system_design/pastebin/README.md` | Most detailed system design solution; demonstrates the full four-step methodology |
| `solutions/system_design/pastebin/pastebin.py` | MapReduce job skeleton using `mrjob` for URL hit-count analytics |
| `solutions/object_oriented_design/call_center/call_center.py` | Complete OOD implementation: `Employee` (abstract), `Operator`, `Supervisor`, `Director`, `Call`, `CallCenter` classes with escalation logic |
| `solutions/object_oriented_design/lru_cache/lru_cache.py` | LRU Cache: `Node`, `LinkedList`, `Cache` classes implementing O(1) get/set with eviction |
| `generate-epub.sh` | Pandoc-based build script that concatenates all markdown and generates ePub files |
| `epub-metadata.yaml` | Pandoc metadata (title, author, language) for ePub output |
| `CONTRIBUTING.md` | PR workflow, translation process, and maintainer guidance |
| `TRANSLATIONS.md` | List of in-progress translations, language codes, and maintainer contacts |

## Code Organization Patterns

### System Design Solutions Pattern

Every system design solution in `solutions/system_design/` follows this consistent structure:

```
problem_name/
├── README.md          # The solution document
├── *.py               # Optional algorithmic implementation
├── *.graffle          # OmniGraffle source (architecture diagrams)
└── *.png              # Rendered diagram images
```

The README solution documents follow a rigid four-step interview methodology template, ensuring learners internalize the process as well as the content.

### OOD Solutions Pattern

OOD solutions provide two views of the same solution:
- **`.py` file** — Pure Python, importable, executable standalone implementation
- **`.ipynb` file** — Jupyter Notebook combining explanation, code cells, and output in an interactive format

The Python implementations use idiomatic OOP patterns: abstract base classes (`ABCMeta`, `@abstractmethod`), enumerations (`Enum`), and standard library data structures (`deque`, `dict`).

### Documentation Linking Pattern

The README makes extensive use of anchor-based internal links (e.g., `[CAP theorem](#cap-theorem)`) for cross-referencing topics, creating a navigable hyperlinked reference. External links cite primary sources (research papers, engineering blogs, video lectures) to support each concept.
