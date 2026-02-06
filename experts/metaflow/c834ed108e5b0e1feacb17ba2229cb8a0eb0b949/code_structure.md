# Metaflow Code Structure

## Complete Annotated Directory Tree

```
metaflow/
├── __init__.py              # Main entry point, exports public API
├── version.py               # Version information
├── flowspec.py              # FlowSpec base class for defining flows
├── decorators.py            # Decorator framework and registration
├── graph.py                 # DAG parsing and flow graph construction
├── parameters.py            # Parameter system for flow inputs
├── exception.py             # Exception hierarchy
├── debug.py                 # Debug utilities
├── util.py                  # Common utility functions
├── metaflow_config.py       # Configuration management
├── metaflow_current.py      # Current runtime context object
├── metaflow_profile.py      # Profiling utilities
├── multicore_utils.py       # Parallel execution utilities
├── includefile.py           # File inclusion in flows
├── tuple_util.py            # Data class utilities
├── unbounded_foreach.py     # Unbounded foreach implementation
├── R.py                     # R language integration
│
├── client/                  # Client API for accessing flows and runs
│   ├── __init__.py          # Exports Metaflow, Flow, Run, Step, Task, DataArtifact
│   └── core.py              # Core client implementation
│
├── datastore/               # Data persistence layer
│   ├── __init__.py
│   ├── flow_datastore.py    # Flow-level datastore operations
│   ├── task_datastore.py    # Task-level artifact storage
│   ├── datastore_set.py     # Collections of datastores
│   ├── spin_datastore.py    # Spin mode datastore
│   └── inputs.py            # Input handling for steps
│
├── metadata_provider/       # Metadata tracking and lineage
│   ├── __init__.py
│   └── util.py
│
├── runner/                  # Programmatic execution API
│   ├── __init__.py
│   ├── metaflow_runner.py   # Runner class for executing flows
│   ├── nbrun.py             # Notebook-specific runner
│   ├── deployer.py          # Deployment API
│   ├── nbdeploy.py          # Notebook deployment
│   ├── subprocess_manager.py # Process management
│   └── utils.py             # Runner utilities
│
├── plugins/                 # Extensible plugin system
│   ├── __init__.py
│   │
│   ├── aws/                 # AWS cloud integration
│   │   ├── batch/           # AWS Batch execution
│   │   │   ├── batch.py     # Batch client
│   │   │   └── batch_decorator.py
│   │   ├── step_functions/  # AWS Step Functions orchestrator
│   │   │   ├── step_functions.py
│   │   │   ├── step_functions_decorator.py
│   │   │   ├── step_functions_deployer.py
│   │   │   ├── schedule_decorator.py
│   │   │   ├── event_bridge_client.py
│   │   │   └── dynamo_db_client.py
│   │   └── aws_utils.py     # Common AWS utilities
│   │
│   ├── kubernetes/          # Kubernetes execution
│   │   ├── kubernetes.py
│   │   ├── kubernetes_decorator.py
│   │   └── kube_utils.py
│   │
│   ├── argo/                # Argo Workflows orchestrator
│   │   ├── argo_workflows.py
│   │   ├── argo_workflows_decorator.py
│   │   ├── argo_workflows_deployer.py
│   │   └── argo_events.py
│   │
│   ├── airflow/             # Apache Airflow integration
│   │   ├── airflow_decorator.py
│   │   └── sensors/         # Airflow sensor implementations
│   │
│   ├── azure/               # Azure cloud integration
│   ├── gcp/                 # Google Cloud Platform integration
│   │
│   ├── pypi/                # Python dependency management
│   │   ├── pypi_decorator.py    # pip packages
│   │   └── conda_decorator.py   # Conda environments
│   │
│   ├── uv/                  # UV package manager integration
│   │
│   ├── cards/               # Visualization and reporting
│   │   ├── card_decorator.py
│   │   ├── card_client/
│   │   └── ui/              # Card UI components (React/TypeScript)
│   │
│   ├── secrets/             # Secrets management
│   │   └── secrets_decorator.py
│   │
│   ├── frameworks/          # ML framework integrations
│   │   └── pytorch.py       # PyTorch distributed training
│   │
│   ├── datastores/          # Storage backend implementations
│   │   └── local_storage.py
│   │
│   ├── datatools/           # Data manipulation tools
│   │
│   ├── env_escape/          # Environment isolation
│   ├── exit_hook/           # Exit hook system
│   │
│   ├── resources_decorator.py   # Resource specification (@resources)
│   ├── retry_decorator.py       # Retry logic (@retry)
│   ├── timeout_decorator.py     # Timeout handling (@timeout)
│   ├── catch_decorator.py       # Exception handling (@catch)
│   ├── parallel_decorator.py    # Parallel execution (@parallel)
│   ├── environment_decorator.py # Environment variables (@environment)
│   ├── project_decorator.py     # Project organization (@project)
│   └── events_decorator.py      # Event triggering
│
├── user_configs/            # User configuration system
│   └── config_parameters.py # Config and ConfigValue classes
│
├── user_decorators/         # User-defined decorator framework
│   ├── user_step_decorator.py   # Step decorator base classes
│   ├── user_flow_decorator.py   # Flow decorator base classes
│   ├── mutable_step.py          # Step mutation API
│   └── mutable_flow.py          # Flow mutation API
│
├── cmd/                     # Command-line interface
│   ├── main_cli.py          # Main CLI entry point
│   ├── code.py              # Code package commands
│   ├── configure_cmd.py     # Configuration commands
│   ├── develop.py           # Development commands
│   └── tutorials_cmd.py     # Tutorial commands
│
├── cli_components/          # CLI component system
│
├── tracing/                 # Distributed tracing support
│
├── mflog/                   # Logging infrastructure
│
├── sidecar/                 # Sidecar process management
│
├── system/                  # System-level utilities
│
├── packaging_sys/           # Code packaging system
│
├── package/                 # Package management
│
├── extension_support/       # Extension loading mechanism
│
├── tutorials/               # Built-in tutorials
│   ├── 00-helloworld/       # Basic introduction
│   ├── 03-playlist-redux/   # Branching and merging
│   ├── 04-playlist-plus/    # Parameters and artifacts
│   ├── 05-hello-cloud/      # Cloud execution
│   └── 08-autopilot/        # Production deployment
│
└── _vendor/                 # Vendored dependencies
    ├── click/               # CLI framework
    ├── yaml/                # YAML parser
    ├── packaging/           # Package version handling
    ├── importlib_metadata/  # Metadata utilities
    ├── typeguard/           # Runtime type checking
    └── typing_extensions.py # Type hints backport

R/                           # R language bindings
docs/                        # Documentation diagrams and notes
test/                        # Test suite
├── core/                    # Core framework tests
├── data/                    # Data handling tests
├── env_escape/              # Environment tests
├── extensions/              # Extension system tests
├── parallel/                # Parallel execution tests
└── unit/                    # Unit tests

devtools/                    # Development utilities
stubs/                       # Type stubs for IDE support
```

## Module and Package Organization

**Core Flow Definition Layer** (`flowspec.py`, `graph.py`, `decorators.py`): These modules implement the fundamental DSL for defining workflows. `FlowSpec` provides the base class, `graph.py` parses step functions into a DAG structure, and `decorators.py` implements the decorator registration and application system.

**Execution and Runtime** (`datastore/`, `metadata_provider/`, `runner/`): The datastore package handles all artifact persistence and versioning. The metadata provider tracks run information and lineage. The runner package provides programmatic APIs for executing flows both interactively and in production.

**Plugin Architecture** (`plugins/`): Metaflow's extensibility is implemented through a comprehensive plugin system. Plugins are organized by category: cloud providers (aws, azure, gcp), compute backends (batch, kubernetes), orchestrators (step_functions, argo, airflow), and capabilities (cards, secrets, dependencies).

**Client API** (`client/`): Provides the programmatic interface for querying and accessing historical flow runs. The hierarchy (Metaflow → Flow → Run → Step → Task → DataArtifact) mirrors the conceptual model of workflow execution.

**CLI System** (`cmd/`, `cli_components/`): Implements the `metaflow` command-line tool using Click. Commands are organized into subcommands for flow execution, configuration, tutorials, and development.

**Extension Support** (`extension_support/`, `user_decorators/`, `user_configs/`): Framework for third-party extensions and user-defined decorators. Provides APIs for mutating flows and steps programmatically.

## Main Source Directories and Purposes

**`metaflow/plugins/`**: Contains all optional functionality through a plugin architecture. Each subdirectory implements integration with a specific technology or capability. Plugins can add decorators, CLI commands, and runtime behaviors.

**`metaflow/client/`**: Read-only API for accessing historical data. Enables data scientists to query past experiments, retrieve artifacts, and build on previous work programmatically.

**`metaflow/runner/`**: Programmatic execution API that allows embedding Metaflow in notebooks, applications, and automated pipelines. Supports both synchronous and asynchronous execution patterns.

**`metaflow/datastore/`**: Abstraction layer for artifact storage. Supports multiple backend implementations (local filesystem, S3, Azure Blob, GCS) with consistent versioning and access patterns.

**`metaflow/cmd/`**: Command-line interface implementation. Each subcommand is implemented as a Click command group, providing user-facing tools for flow management.

**`metaflow/tutorials/`**: Self-contained example flows that teach Metaflow concepts progressively. Each tutorial includes a Python flow file and README with explanations.

## Key Files and Their Roles

**`metaflow/__init__.py`** (209 lines): The main entry point that exports the public API. Handles extension loading, imports core classes (FlowSpec, Flow, Run, etc.), and sets up the module namespace. Uses lazy loading for performance.

**`metaflow/flowspec.py`** (2000+ lines): Implements the `FlowSpec` base class that all flows inherit from. Contains the state machine for flow execution, step transition logic, foreach handling, and integration with decorators.

**`metaflow/graph.py`** (1000+ lines): Parses flow definitions using AST analysis to construct the DAG. Validates flow structure, identifies join points, and provides graph traversal utilities.

**`metaflow/decorators.py`** (800+ lines): Core decorator framework. Implements `Decorator` base class, decorator registration system, and decorator application logic. Handles both step and flow decorators.

**`metaflow/parameters.py`** (500+ lines): Parameter system for flow inputs. Implements `Parameter` class, type conversion, default values, and CLI argument generation. Supports JSON parameters and deploy-time functions.

**`metaflow/client/core.py`** (2000+ lines): Complete implementation of the client API. Defines Flow, Run, Step, Task, and DataArtifact classes with methods for querying and accessing historical data.

**`metaflow/runner/metaflow_runner.py`** (1000+ lines): Runner API for programmatic execution. Supports running flows from Python code, notebooks, or other applications with full control over execution and monitoring.

**`metaflow/plugins/aws/batch/batch_decorator.py`**: AWS Batch integration decorator. Configures container resources, IAM roles, and Batch job queue parameters for cloud execution.

**`metaflow/plugins/kubernetes/kubernetes_decorator.py`**: Kubernetes execution decorator. Handles pod configuration, resource requests, persistent volumes, and node selection for K8s environments.

**`metaflow/cmd/main_cli.py`**: Main CLI entry point. Implements top-level commands and loads subcommands from plugins using Click's command collection pattern.

## Code Organization Patterns

**Decorator Pattern**: Extensively used for extending step and flow behavior. Decorators are classes that wrap step execution, modify flow behavior, or inject capabilities. The `Decorator` base class provides lifecycle hooks (init, task_pre_step, task_post_step, etc.).

**Plugin System**: Extensions are loaded dynamically at import time from the `metaflow_extensions` package. Plugins register decorators, CLI commands, and runtime behaviors through well-defined extension points.

**Lazy Loading**: The main `__init__.py` uses lazy loading with `lazy_load_aliases()` to defer imports until needed. This improves startup time and allows selective loading of heavy dependencies.

**Context Objects**: The `current` singleton provides runtime context (step_name, task_id, run_id, etc.) accessible from within flow code. The `ParameterContext` provides deploy-time context for parameter evaluation.

**State Management**: `FlowSpec` uses the `_FlowState` dictionary-like class to manage flow-level state, parameters, configs, and decorator collections while properly handling inheritance.

**AST Parsing**: Flow definitions are analyzed using Python's `ast` module to extract step functions, decorators, and transition logic before execution. This enables validation and graph construction.

**Metadata Tracking**: The metadata provider pattern abstracts different metadata backends (local, service-based). All runs, steps, and tasks record metadata for lineage tracking and reproducibility.

**Subprocess Management**: The runner uses subprocess managers with async/await patterns to execute flows in isolated processes while monitoring progress and capturing output.

**Type System**: Modern Python type hints throughout with runtime validation using vendored typeguard. Type stubs provided separately for IDE support.
