# Kröhnkite — Build System

## Build System Type and Configuration Files

Kröhnkite uses **two parallel build systems**:

1. **`taskfile.yaml`** (primary, recommended): Uses [go-task](https://taskfile.dev/) as the task runner. This is the modern, preferred build system.
2. **`Makefile`** (legacy, still functional): Traditional GNU Make build, kept for compatibility.

Both produce identical output: a `.kwinscript` package file (a zip archive with a specific directory structure) installable via KDE's `kpackagetool6`.

### Key Build Files

| File | Purpose |
|------|---------|
| `taskfile.yaml` | go-task task definitions (primary build system) |
| `Makefile` | GNU Make rules (legacy build system) |
| `package.json` | npm package config; declares `typescript` dev dependency and `tsc` script |
| `package-lock.json` | npm lockfile for reproducible dependency install |
| `tsconfig.json` | TypeScript compiler configuration |
| `tslint.json` | TypeScript linter configuration |
| `res/metadata.json` | KWin package metadata template (has `$VER`/`$REV` placeholders) |
| `res/config.xml` | KConfigXT config schema (defines all config keys, types, defaults) |
| `res/config.ui` | Qt Designer UI file for KDE settings dialog |
| `res/main.qml` | Main QML file (KWin script entry point) |
| `res/main.js` | JavaScript bootstrap that loads `script.js` |

## External Dependencies

### Runtime Dependencies (no installation needed beyond KDE Plasma 6)
- **KWin 6**: The window manager that hosts the script. Requires `X-Plasma-API-Minimum-Version: 6.0`.
- **Qt / QML**: Used for the runtime script environment and UI.
- **D-Bus**: Used for mouse-pointer-follows-focus feature.

### Build-Time Dependencies (must be installed by developer)

| Dependency | Purpose | Install method |
|------------|---------|----------------|
| **go-task** | Task runner for `taskfile.yaml` | Package manager or [taskfile.dev](https://taskfile.dev/installation/) |
| **npm** | Node.js package manager | OS package manager |
| **TypeScript** (`^5.9.2`) | TypeScript compiler (`tsc`) | `npm install --save-dev` (handled automatically) |
| **7-zip (p7zip)** | Creates `.kwinscript` zip package | OS package manager (`7z` command) |
| **kpackagetool6** | Installs/upgrades/removes KWin scripts | Part of KDE Plasma 6 SDK |
| **git** | Required for version tagging (`git describe --tags`) | OS package manager |

## Build Targets and Commands

### Using go-task (Recommended)

```bash
# Install npm dependencies (TypeScript compiler)
go-task install-deps

# Compile TypeScript to krohnkite.js
go-task build-ts

# Build the complete KWin package directory (pkg/)
go-task kwin-pkg

# Create the .kwinscript zip archive in builds/
go-task package
# or alias:
go-task kwin-pkg-file

# Build AND install the package into KDE
go-task install

# Uninstall the package from KDE
go-task uninstall

# Clean all build artifacts
go-task clean

# Update metadata.json with version/revision
go-task meta-version

# Update version in package.json
go-task package-json
```

### Using make (Legacy)

```bash
# Build the package directory
make

# Create .kwinscript zip file
make package

# Build and install
make install

# Uninstall
make uninstall

# Run tests
make test

# Clean build artifacts
make clean
```

## How the Build Pipeline Works

### Step 1: Install npm Dependencies
```
npm install --save-dev
```
Installs TypeScript compiler into `node_modules/`. Only runs once (go-task tracks this with `run: once`).

### Step 2: TypeScript Compilation
```
npm run tsc --
```
Compiles all `.ts` files under `src/` into a single concatenated `krohnkite.js` output file. The TypeScript compiler is configured via `tsconfig.json` to use `outFile` mode, producing one big JavaScript file with all classes in global scope.

**Source tracking**: go-task monitors `src/**/*.ts` as sources and `krohnkite.js` as output, skipping recompilation if sources haven't changed.

### Step 3: Build KWin Package Directory (`pkg/`)
The `kwin-pkg` task assembles the `pkg/` directory with the required KWin package structure:
```
pkg/
├── metadata.json               ← from res/metadata.json (with $VER/$REV replaced)
└── contents/
    ├── ui/
    │   ├── main.qml            ← from res/main.qml
    │   ├── config.ui           ← from res/config.ui
    │   ├── shortcuts.qml       ← from res/shortcuts.qml
    │   ├── dbus.qml            ← from res/dbus.qml
    │   └── popup.qml           ← from res/popup.qml
    ├── code/
    │   ├── script.js           ← compiled krohnkite.js
    │   └── main.js             ← from res/main.js
    ├── config/
    │   └── main.xml            ← from res/config.xml
    └── locale/                 ← compiled translation .mo files
        ├── ru/LC_MESSAGES/krohnkite.mo
        └── zh/LC_MESSAGES/krohnkite.mo
```

**Version substitution**: `metadata.json` has `$VER` and `$REV` placeholders replaced by `git describe --tags --abbrev=0` and `git rev-parse --short HEAD` respectively.

### Step 4: Create .kwinscript Archive
```
7z a -tzip builds/krohnkite-<VERSION>_<REV>.kwinscript ./pkg/*
```
Zips the `pkg/` directory contents into a `.kwinscript` file in `builds/`. The filename format is: `krohnkite-<VERSION>[<BRANCH>]_<REV>.kwinscript`. Non-master/main branches append `-<branch>` to the filename.

### Step 5: Install via kpackagetool6
```bash
# Upgrade if already installed, otherwise install fresh:
kpackagetool6 -t KWin/Script -s krohnkite && \
  kpackagetool6 -t KWin/Script -u builds/krohnkite-*.kwinscript || \
  kpackagetool6 -t KWin/Script -i builds/krohnkite-*.kwinscript
```

## How to Build, Test, and Deploy

### Full Development Build and Install
```bash
# Prerequisites: go-task, npm, 7z, kpackagetool6 installed
git clone https://codeberg.org/anametologin/Krohnkite
cd Krohnkite
go-task install
```

### Incremental Development Workflow
```bash
# After modifying TypeScript source files:
go-task install      # recompiles only changed files, reinstalls
```

### Manual kpackagetool6 operations
```bash
# Check if installed:
kpackagetool6 -t KWin/Script -s krohnkite

# Install from file:
kpackagetool6 -t KWin/Script -i krohnkite-x.x.x.x.kwinscript

# Upgrade from file:
kpackagetool6 -t KWin/Script -u krohnkite-x.x.x.x.kwinscript

# Uninstall:
kpackagetool6 -t KWin/Script -r krohnkite
```

### Post-Install Steps
After installation or configuration changes, a **system reboot is required**. Do not toggle the script on/off via KWin Scripts UI — this creates multiple instances. Instead: configure → apply → reboot.

### Autoinstall Tool
The `tools/autoinstall/` directory contains a Python daemon (`autoinstalld.py`) that can watch for built package files and automatically install them on change, useful for rapid development iteration.

## TypeScript Configuration (`tsconfig.json`)

The TypeScript compiler is configured to:
- Output a single concatenated file (`outFile: krohnkite.js`)
- Target ECMAScript 5 or newer (compatible with KWin's JavaScript engine)
- Not use modules (KWin doesn't support ES modules)
- Include all `src/**/*.ts` files in the correct dependency order

## Configuration Schema (`res/config.xml`)

The `config.xml` file is a KConfigXT schema that defines all configuration parameters. Each `<entry>` specifies:
- Name (maps to `KWIN.readConfig("name", default)` call in `KWinConfig`)
- Type (Bool, Int, String, StringList)
- Default value
- Label and description shown in the settings dialog

The settings dialog UI is defined in `res/config.ui` (Qt Designer XML format).
