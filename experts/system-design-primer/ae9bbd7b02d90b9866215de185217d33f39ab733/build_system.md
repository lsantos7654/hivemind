# System Design Primer — Build System

## Overview

The System Design Primer is **not a traditional software project** — it has no compiled artifacts, no package manager manifest, and no test suite. It is a documentation and educational content repository. The only "build" step is optional: generating ePub books from the markdown source files using a shell script.

## Build System Type

**No formal build system.** The repository relies on:
- A bash shell script (`generate-epub.sh`) for ePub generation
- Git for version control and contribution workflow
- GitHub for hosting, issue tracking, and pull requests

## Configuration Files

| File | Purpose |
|------|---------|
| `generate-epub.sh` | Shell script to build ePub files using `pandoc` |
| `epub-metadata.yaml` | Pandoc document metadata (title, author, language) for ePub output |
| `CONTRIBUTING.md` | Contribution and PR process documentation |
| `TRANSLATIONS.md` | Translation workflow and maintainer directory |

There is no `Makefile`, `package.json`, `pyproject.toml`, `setup.py`, `requirements.txt`, `Cargo.toml`, or any other standard build manifest.

## External Dependencies

### For ePub Generation (optional)

**`pandoc`** — The only external tool required for building ePub output. It must be installed and available on `$PATH`.

- Install on macOS: `brew install pandoc`
- Install on Ubuntu/Debian: `apt-get install pandoc`
- Official site: pandoc.org

### For Running Python Solution Code (optional)

The Python files in `solutions/` are illustrative and not meant to be deployed, but they have implicit dependencies:

**`mrjob`** — Used in `solutions/system_design/pastebin/pastebin.py` for the MapReduce analytics example.
- Install: `pip install mrjob`
- GitHub: github.com/Yelp/mrjob

**Jupyter Notebook / JupyterLab** — Required to open the `.ipynb` files in `solutions/object_oriented_design/`.
- Install: `pip install jupyter` or `pip install jupyterlab`
- The `.py` companion files can be run with plain Python without Jupyter.

**Python standard library** — The OOD Python files use only stdlib modules:
- `abc` — Abstract base classes (`ABCMeta`, `abstractmethod`)
- `collections` — `deque` for queue data structures
- `enum` — `Enum` for typed constants

No `requirements.txt` or `pyproject.toml` is provided because the Python code is reference material, not a deployable package.

### For Viewing Flashcards (optional)

**Anki** (apps.ankiweb.net) — Required to open the `.apkg` flashcard deck files in `resources/flash_cards/`.

## Build Targets and Commands

### Generate ePub Books

The `generate-epub.sh` script produces four ePub files — one for English (with all system design solutions concatenated) and one each for Japanese, Simplified Chinese, and Traditional Chinese.

```bash
# Ensure pandoc is installed first
which pandoc

# Run the ePub generator from the repo root
bash generate-epub.sh
```

**What the script does:**

1. Checks that `pandoc` is installed (exits with error if missing).
2. **English ePub** (`README.epub`): Creates a temp file, appends `README.md`, then loops over all directories in `solutions/system_design/` (skipping `template` and `__init__.py`), concatenating each solution's `README.md`. Feeds the combined content to `pandoc` with `epub-metadata.yaml` and `--metadata=lang:en`.
3. **Japanese ePub** (`README-ja.epub`): Pipes `README-ja.md` to pandoc with `lang:ja`.
4. **Simplified Chinese ePub** (`README-zh-Hans.epub`): Pipes `README-zh-Hans.md` to pandoc with `lang:zh-Hans`.
5. **Traditional Chinese ePub** (`README-zh-TW.epub`): Pipes `README-zh-TW.md` to pandoc with `lang:zh-TW`.

**Script internals:**

```bash
# Core ePub generation function
generate_from_stdin() {
  outfile=$1
  language=$2
  pandoc --metadata-file=epub-metadata.yaml --metadata=lang:$2 --from=markdown -o $1 <&0
}

# English ePub concatenates README + all system_design solution READMEs
generate_with_solutions() {
  tmpfile=$(mktemp /tmp/sytem-design-primer-epub-generator.XXX)
  cat ./README.md >> $tmpfile
  for dir in ./solutions/system_design/*; do
    case $dir in *template*) continue;; esac
    case $dir in *__init__.py*) continue;; esac
    : [[ -d "$dir" ]] && ( cd "$dir" && cat ./README.md >> $tmpfile && echo "" >> $tmpfile )
  done
  cat $tmpfile | generate_from_stdin 'README.epub' 'en'
  rm "$tmpfile"
}
```

### Running Python OOD Solutions

```bash
# Run the LRU cache implementation directly
python solutions/object_oriented_design/lru_cache/lru_cache.py

# Run the call center implementation
python solutions/object_oriented_design/call_center/call_center.py

# Open a Jupyter Notebook (requires Jupyter installed)
jupyter notebook solutions/object_oriented_design/lru_cache/lru_cache.ipynb
```

### Running the MapReduce Analytics Example

```bash
# Install mrjob first
pip install mrjob

# Run locally (reads from stdin, writes to stdout)
python solutions/system_design/pastebin/pastebin.py < input_log_file.txt
```

## How to Contribute

Contributions follow a standard GitHub fork-and-PR workflow:

```bash
# 1. Fork the repo on GitHub, then clone your fork
git clone git@github.com:YourLogin/system-design-primer.git
cd system-design-primer

# 2. Create a feature branch
git checkout -b my-feature

# 3. Make changes and commit
git add modified_files
git commit -m "Description of changes"

# 4. Push to your fork
git push -u origin my-feature

# 5. Open a Pull Request on GitHub
```

### Translation Contributions

- Changes to content: English first, then translate to each language.
- Changes to translations only: modify the `README-XX.md` file directly.
- New language: create `README-XX.md` where XX is the IETF language tag; include links to the translation at the top of each README-XX.md file in alphabetical order by ISO code.

## Deployment

There is no deployment process. The repository is the product — users access it directly on GitHub or download it. The ePub files, if generated, are for offline reading only and are not checked in to the repository.

## Testing

There is no automated test suite. The "tests" are:
- Human review of PR content for accuracy and clarity
- Community feedback via GitHub issues
- Native speaker review for translation PRs before merge
