# Should `make dev` / `make dev-save` / `make dev-reset` be more Bazel-native?

**Verdict:** No. Both `expert-bazel` and `expert-bazel-lib` independently
arrived at the same conclusion: keep the sidecar Python script. There is one
small independent cleanup worth doing.

## Current workflow

`scripts/dev-opencode.py` (~140 lines), invoked via Make targets:

- **`make dev`** — clones `sst/opencode@v<version>` (read out of
  `MODULE.bazel`) into `dev/opencode/` (gitignored), creates branch
  `hivemind`, then `git am`s every `third_party/patches/*.patch` so each
  becomes one commit on that branch.
- **`make dev-save`** — runs `git format-patch v<version>..hivemind`,
  wholesale replaces `third_party/patches/*.patch`, then rewrites the
  `_OPENCODE_PATCHES = [...]` literal in `third_party/extensions.bzl` via
  regex.
- **`make dev-reset`** — `rm -rf dev/opencode && make dev`.

The patch list in `extensions.bzl` is consumed by the `opencode_install`
custom repo rule, which downloads the upstream tarball at fetch time and
applies the patches with system `patch -p1`.

## `expert-bazel` findings

1. **No Bazel-native idiom exists for this loop.** Closest analogues —
   `aspect_rules_lint` formatters and `gazelle update` — write files but do
   not maintain a parallel git worktree. Large Bazel projects (rules_go,
   rules_rust, envoy) all use a sidecar script for equivalent loops. This
   is a deliberate out-of-tree workflow, not a gap waiting to be filled.

2. **None of Bazel's value props apply.** Caching, incrementality,
   hermeticity — all useless for a one-shot, stateful, git-manipulating
   user action.

3. **`bazel run` mechanics work** (not sandboxed, can write to the source
   tree via `BUILD_WORKSPACE_DIRECTORY`), but bring real gotchas:
   - `Path(__file__).resolve().parent.parent` resolves into the runfiles
     tree, not the workspace — would have to be replaced with
     `Path(os.environ["BUILD_WORKSPACE_DIRECTORY"])`.
   - No recursive Bazel calls (output base lock).
   - `BUILD_WORKING_DIRECTORY` ≠ `BUILD_WORKSPACE_DIRECTORY` — easy footgun.

4. **Reading the version from `MODULE.bazel` natively is a wash.** No
   primitive exposes module-extension tag values to a `bazel run` target
   without re-parsing or coupling the tool to a fully-resolved external
   repo (which is exactly what you don't want when debugging a broken
   fetch). Regex on `MODULE.bazel` is simpler and more robust.

5. **Honest recommendation: keep the sidecar.** The script is correct, does
   one thing, runs only when patches are added/edited. "Bazel-native" pays
   off when you get caching, incrementality, or hermeticity — none apply.
   Make targets calling a Python script is the right tool here.

## `expert-bazel-lib` findings

I evaluated `aspect_bazel_lib`'s `write_source_files` specifically for the
"save back to source" half of the workflow:

1. **Dynamic filenames are a hard blocker.**
   `write_source_files(files = {...})` dict keys must be analysis-time
   Starlark literals. Patch filenames come from `git format-patch` output
   at runtime (filenames derive from commit subjects).

2. **TreeArtifact entries don't prune.** Even using one entry to write the
   whole `third_party/patches/` directory, the rule copies in but never
   removes files absent from the generated set. With a patch series where
   commit rewords are routine, stale `.patch` files would accumulate.
   Source: `lib/private/write_source_file.bzl` — the rule copies `in_file`
   to `out_file` with no pruning step.

3. **Partial `.bzl` rewriting is unsupported.** `write_source_files` is
   full-file replacement only. The `_OPENCODE_PATCHES = [...]` literal
   sits inside a mixed-purpose `extensions.bzl` and cannot be replaced
   in-place by this rule.

4. **`run_binary` + `write_source_files` chain doesn't rescue it.** Even
   wired up cleanly, you still need a sidecar to `rm -rf` stale patches
   before Bazel writes the new set — defeating the point.

5. **Honest recommendation: don't use `write_source_files` here.** It earns
   its keep for stable-filename outputs (generated protos, lock files,
   formatted code). For a patch series with volatile filenames it adds
   complexity without solving the hard part.

## One independent cleanup worth doing

Factor `_OPENCODE_PATCHES` out of `third_party/extensions.bzl` into its own
`third_party/patches_list.bzl` that's wholly owned and overwritten by
`scripts/dev-opencode.py`.

**Why:** Replaces the regex `re.sub` against `extensions.bzl` with a plain
`write_text` of a tiny generated file. Localizes the volatile state to one
fully-owned file. Tiny win, ~20 LoC change.

**Files involved:**
- `third_party/patches_list.bzl` — new generated file with header marking
  it auto-managed; contains `OPENCODE_PATCHES = [...]`.
- `third_party/extensions.bzl` — replace inline list (lines 86–93) with
  `load(":patches_list.bzl", "OPENCODE_PATCHES")` and update the reference
  inside `_ext_impl` (line 78).
- `scripts/dev-opencode.py:_rewrite_patches_list` — drop the regex `re.sub`,
  use `Path.write_text` of the new `.bzl` instead. Update the
  `EXTENSIONS_BZL` constant to `PATCHES_LIST_BZL`.

## Latent bug noted (not in scope unless you ever bazel-ify)

`scripts/dev-opencode.py:30`:

```python
REPO_ROOT = Path(__file__).resolve().parent.parent
```

Correct under `python3 scripts/dev-opencode.py` (current invocation). Would
break under `bazel run` (resolves into runfiles tree, not workspace). Fix
at that point: `Path(os.environ["BUILD_WORKSPACE_DIRECTORY"])`. Since the
recommendation is to *stay* with the Make-driven invocation, no action
needed today.
