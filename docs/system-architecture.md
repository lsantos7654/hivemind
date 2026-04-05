# Hivemind System Architecture

## System-Level Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            ENTRYPOINTS                                          │
│                                                                                 │
│  ┌──────────────────────┐      ┌──────────────────────────────────────────┐     │
│  │      cli.py           │      │               tui/                      │     │
│  │  (Typer + Rich)       │      │  app.py ─── HivemindApp                │     │
│  │                       │      │  screens/                               │     │
│  │  expert subcommands   │      │    ExpertsPane, TeamsPane               │     │
│  │  team subcommands     │      │    TeamDetailScreen                     │     │
│  │  status, redeploy     │      │    VersionDetailScreen                  │     │
│  │  init, switch         │      │  widgets/                               │     │
│  │                       │      │    VimDataTable, SearchBar, Modals      │     │
│  └──────────┬────────────┘      └──────────────────┬─────────────────────┘     │
│             │                                       │                           │
└─────────────┼───────────────────────────────────────┼───────────────────────────┘
              │  calls public functions                │  calls public functions
              ▼                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            SERVICE LAYER                                        │
│                                                                                 │
│  experts.py               teams.py                deployment.py                │
│  ├─ enable_expert()       ├─ create_team()        ├─ redeploy_all_agents()     │
│  ├─ disable_expert()      ├─ delete_team()        ├─ deploy_agent()            │
│  ├─ delete_expert()       ├─ update_team()        ├─ deploy_team_lead()        │
│  ├─ update_expert()       ├─ add_expert_to_team() ├─ update_librarian()        │
│  └─ switch_provider()     └─ remove_expert_from() └─ regenerate_hivemind_md()  │
│                                                                                 │
│  analysis.py              config.py                git.py                      │
│  ├─ start_analysis()      ├─ load_config()         ├─ clone_repo()            │
│  ├─ finish_analysis()     ├─ save_config()         ├─ resolve_latest_commit() │
│  ├─ analyze_repo()        ├─ load_hivemind()       ├─ stage_for_analysis()    │
│  └─ run_async_analysis()  ├─ get_active_provider() └─ commit_analysis_results()│
│                           └─ save_json() [atomic]                               │
│                                                                                 │
└────────┬──────────────────────────┬─────────────────────────┬───────────────────┘
         │                          │                          │
         ▼                          ▼                          ▼
┌──────────────────┐  ┌──────────────────────┐  ┌────────────────────────────────┐
│   models.py      │  │   templates.py       │  │     providers.py               │
│   (Pydantic)     │  │   (Template Engine)  │  │     (Port + Adapters)          │
│                  │  │                      │  │                                │
│  RepoEntry       │  │  Jinja2 Environment  │  │  <<abstract>> Provider         │
│  TeamData        │  │  /templates/*.j2     │  │  ├─ format_agent_md()          │
│  ProviderConfig  │  │                      │  │  ├─ format_lead_md()           │
│  ProviderSettings│  │  hivemind_md_base()  │  │  ├─ deploy_agent()            │
│  HivemindConfig  │  │  team_lead_template()│  │  ├─ deploy_lead()             │
│  AppConfig       │  │  agent_md_template() │  │  ├─ init_dirs()               │
│  OperationResult │  │  update_expert_      │  │  ├─ build_analysis_cmd()       │
│  ProgressInfo    │  │    prompt()          │  │  └─ get_context_append()       │
│  CancellationTkn │  │  create_expert_      │  │                                │
│                  │  │    prompt()          │  │  ┌──────────┐ ┌──────────────┐ │
│                  │  │                      │  │  │ Claude   │ │ OpenCode     │ │
│                  │  │                      │  │  │ Provider │ │ Provider     │ │
│                  │  │                      │  │  └──────────┘ └──────────────┘ │
└──────────────────┘  └──────────────────────┘  └────────────────────────────────┘

         ┌─────────────────────────────────────────────┐
         │            EXTERNAL SYSTEMS                  │
         │                                              │
         │  ┌──────────┐ ┌──────────┐ ┌─────────────┐ │
         │  │ Git      │ │ AI       │ │ Filesystem  │ │
         │  │ (subprocess│ │ Analysis │ │             │ │
         │  │  clone,   │ │ (subprocess│ │ experts/   │ │
         │  │  fetch)   │ │  engine)  │ │ agents/    │ │
         │  └──────────┘ └──────────┘ │ teams/     │ │
         │                             │ providers/ │ │
         │  ┌────────────────────────┐ └─────────────┘ │
         │  │ Web Crawler            │                  │
         │  │ (crawler.py)           │                  │
         │  └────────────────────────┘                  │
         └─────────────────────────────────────────────┘
```

## Data Flow: Expert Lifecycle

```
    User                CLI / TUI            experts/git/analysis    Providers          Filesystem
     │                     │                       │                       │                   │
     │  hivemind add <url> │                       │                       │                   │
     │────────────────────>│                       │                       │                   │
     │                     │  clone_repo(url)      │                       │                   │
     │                     │──────────────────────>│                       │                   │
     │                     │                       │──── git clone ────────────────────────────>│
     │                     │                       │                       │    ~/.cache/repos/ │
     │                     │                       │                       │                   │
     │                     │  start_analysis()     │                       │                   │
     │                     │──────────────────────>│                       │                   │
     │                     │                       │  build_analysis_cmd() │                   │
     │                     │                       │──────────────────────>│                   │
     │                     │                       │<─────── cmd ─────────│                   │
     │                     │                       │                       │                   │
     │                     │                       │──── subprocess(AI engine) ───────────────>│
     │                     │                       │                       │  experts/<name>/  │
     │                     │                       │                       │   <commit>/       │
     │                     │                       │                       │   ├── agent.md    │
     │                     │                       │                       │   └── *.md (docs) │
     │                     │  finish_analysis()    │                       │                   │
     │                     │──────────────────────>│                       │                   │
     │                     │                       │──── HEAD symlink ─────────────────────────>│
     │                     │                       │                       │                   │
     │                     │  enable_expert()      │                       │                   │
     │                     │──────────────────────>│                       │                   │
     │                     │                       │  save_config()        │                   │
     │                     │                       │──────────────────────────────────────────>│
     │                     │                       │                       │   config.json     │
     │                     │                       │                       │                   │
     │                     │  redeploy_all_agents()│                       │                   │
     │                     │──────────────────────>│                       │                   │
     │                     │                       │                       │                   │
     │                     │                       │  (deploy pipeline — see below)            │
     │                     │                       │                       │                   │
```

## Deploy Pipeline (per agent)

```
  ┌────────────────────┐
  │ Read agent.md from │
  │ experts/<name>/HEAD│
  └────────┬───────────┘
           │
           ▼
  ┌────────────────────┐
  │ strip_frontmatter()│  Remove any existing YAML frontmatter
  └────────┬───────────┘
           │
           ▼
  ┌────────────────────┐
  │ get_context_append │  Load provider-specific context from
  │   (agent_type)     │  providers/<name>/context.json +
  │                    │  providers/<name>/overrides.json
  └────────┬───────────┘
           │
           ▼
  ┌────────────────────┐
  │ format_agent_md()  │  Apply provider-specific frontmatter
  │  (Provider method) │  + path transforms:
  │                    │    {EXPERTS_DIR} → actual path
  │                    │    {HIVEMIND_DIR} → actual path
  │                    │    {CACHE_DIR} → actual path
  └────────┬───────────┘         │
           │          ┌──────────┴──────────┐
           │          │                     │
           ▼          ▼                     ▼
  ┌──────────────┐  ┌──────────────┐
  │ Claude       │  │ OpenCode     │  Strategy pattern:
  │ frontmatter: │  │ frontmatter: │  concrete provider
  │ ---          │  │ ---          │  selected at runtime
  │ name: ...    │  │ name: ...    │
  │ model: ...   │  │ model: ...   │
  │ tools: [...]│  │ tools: {...} │
  │ ---          │  │ ---          │
  └──────┬───────┘  └──────┬───────┘
         │                  │
         └────────┬─────────┘
                  │
                  ▼
  ┌────────────────────┐
  │ deploy_agent()     │  Write to agents/expert-<name>.md
  │  (Provider method) │  in provider's home directory
  └────────────────────┘
```

## Filesystem Layout

```
hivemind/                           # HIVEMIND_ROOT
├── hivemind.json                   # Tracked: provider configs, repo registrations
├── config.json                     # Gitignored: enabled/disabled, active_provider, teams
├── HIVEMIND.md                     # Generated: aggregated instructions for provider
├── CLAUDE.md                       # Project instructions for Claude Code
│
├── experts/                        # Expert definitions (versioned)
│   └── <name>/
│       ├── <commit>/               # Version snapshot
│       │   ├── agent.md            # Platform-neutral expert definition
│       │   ├── apis_and_interfaces.md
│       │   ├── architecture_and_patterns.md
│       │   ├── conventions_and_idioms.md
│       │   ├── codebase_structure.md
│       │   └── development_setup.md
│       └── HEAD -> <commit>/       # Symlink to active version
│
├── agents/                         # Deployed agents (generated, provider-specific)
│   ├── expert-<name>.md            # One per enabled expert
│   ├── team-lead-<team>.md         # One per team
│   └── librarian.md                # Auto-generated catalog of all experts + teams
│
├── teams/                          # Team definitions
│   └── <team>/
│       ├── lead.md                 # Team lead agent definition
│       └── expert-<name>/
│           └── notes.md            # Per-expert consultation journal
│
├── providers/                      # Provider-specific configuration
│   └── <provider>/
│       ├── context.json            # Per-agent-type context to append at deploy
│       ├── overrides.json          # User overrides (gitignored)
│       └── instructions.md         # Appended to HIVEMIND.md
│
├── templates/                      # Jinja2 templates
│   ├── agent.md.j2
│   ├── team_lead.md.j2
│   ├── hivemind.md.j2
│   ├── expert_notes.md.j2
│   └── prompts/
│
├── commands/                       # Custom CLI commands
├── private-experts/                # Private expert definitions
│
├── hivemind_cli/                   # Python package
│   ├── cli.py                      # Typer CLI entrypoint
│   ├── config.py                   # Path constants, config I/O, provider cache
│   ├── experts.py                  # Expert lifecycle (enable/disable/update/delete)
│   ├── teams.py                    # Team management (create/delete/add/remove)
│   ├── deployment.py               # Agent deployment, librarian, HIVEMIND.md
│   ├── git.py                      # Git subprocess operations
│   ├── analysis.py                 # AI analysis orchestration
│   ├── models.py                   # Pydantic models (config schemas, results)
│   ├── providers.py                # Provider abstraction (ABC + implementations)
│   ├── templates.py                # Jinja2 template loader
│   ├── crawler.py                  # Web doc crawler
│   └── tui/                        # Textual TUI
│       ├── app.py                  # HivemindApp
│       ├── screens/
│       └── widgets/
│
└── docs/                           # Documentation
    ├── system-architecture.md      # This file
    └── refactor-plan.md            # Architecture refactor plan
```

## Architectural Style

**Layered Architecture with partial Hexagonal (Ports and Adapters) influence.**

| Layer | Module(s) | Role |
|-------|-----------|------|
| **Entrypoints** | `cli.py`, `tui/` | User interaction, delegates to service layer |
| **Service Layer** | `experts.py`, `teams.py`, `deployment.py` | Business logic and orchestration |
| **Infrastructure** | `config.py`, `git.py`, `analysis.py` | Config I/O, git ops, AI subprocess |
| **Entities** | `models.py` | Pydantic models with validation, no business logic |
| **Port** | `providers.py` (Provider ABC) | Abstract interface for platform-specific operations |
| **Adapters** | `ClaudeProvider`, `OpenCodeProvider` | Concrete implementations of Provider port |
| **Template Engine** | `templates.py` | Jinja2 rendering for agent/lead/hivemind content |
| **External Systems** | git (subprocess), AI engine (subprocess), filesystem | Infrastructure not abstracted behind ports |

## Design Patterns Identified

| Pattern | Where | Description |
|---------|-------|-------------|
| **Strategy** | `Provider` selection via `get_active_provider()` | Active provider selected at runtime from config; service layer calls interface without knowing concrete type |
| **Template Method** | `Provider` ABC | Base class defines deploy algorithm skeleton; subclasses override variant steps (frontmatter format, path transforms) |
| **Adapter** | `ClaudeProvider`, `OpenCodeProvider` | Each adapts the generic deploy interface to a specific platform's file format conventions |
| **Abstract Factory** | `Provider` family | Provider defines a cohesive family of related operations (format, deploy, init, build_cmd) |
| **Repository** (informal) | `load_config`/`save_config` in `config.py` | Config persistence via atomic JSON read/write, but no abstract interface |
| **Read Model Projection** | `update_librarian()` | Aggregates all enabled experts into a single librarian agent file (CQRS-like) |

## Key Architectural Observations

### Strengths
1. **Modular service layer** — Business logic split into focused modules (`experts.py`, `teams.py`, `deployment.py`, `git.py`, `analysis.py`, `config.py`) with clear responsibilities
2. **Typed models** — Pydantic `BaseModel` classes with validation replace raw `dict[str, Any]` and manual `from_dict`/`to_dict`
3. **Provider abstraction** — correct port definition enabling multi-platform support
4. **Public API surface** — all functions are properly named (no underscore convention leak across module boundaries)
5. **Explicit dependency injection** — `config: AppConfig` is a required parameter, not resolved internally
6. **Atomic config writes** — `save_json` uses tempfile + rename for crash safety
7. **Versioned experts** — commit-based snapshots with HEAD symlink enable rollback
8. **Config separation** — tracked `hivemind.json` vs gitignored `config.json` aligns with 12-Factor App

### Remaining Debt
1. **No Protocol ports** — git/filesystem/config operations are not behind abstract interfaces (deferred until a second implementation exists)
2. **No event model** — side effects after enable/disable/deploy are imperative calls, not domain events
3. **cli.py `add()` business logic** — the add command still orchestrates the full expert registration workflow inline

---

*Generated 2026-04-05, updated 2026-04-05 after architecture refactor (Pydantic migration, module split, public API surface).*
