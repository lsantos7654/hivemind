# Metaflow Repository Summary

## Purpose and Goals

Metaflow is a human-centric framework designed to help scientists and engineers build and manage real-life AI and ML systems. Originally developed at Netflix and now supported by Outerbounds, Metaflow streamlines the entire development lifecycle—from rapid prototyping in notebooks to reliable, maintainable production deployments. The framework enables teams of all sizes to iterate quickly and deliver robust systems efficiently by unifying code, data, and compute at every stage.

The core philosophy of Metaflow is to boost productivity for research and engineering teams working on diverse projects, from classical statistics to state-of-the-art deep learning and foundation models. It bridges the gap between experimental data science work and production-grade ML systems, providing a seamless path from prototype to production and back.

## Key Features and Capabilities

**Workflow Definition and Execution**: Metaflow provides a Pythonic API based on the `FlowSpec` class where users define workflows as directed acyclic graphs (DAGs) of steps. Each step is a Python function decorated with `@step`, and transitions between steps are defined using `self.next()`. The framework automatically handles execution, versioning, and artifact management.

**Scalable Compute**: Metaflow supports effortless horizontal and vertical scaling in cloud environments. Steps can be executed on local machines or seamlessly offloaded to cloud compute services including AWS Batch, Kubernetes, and other orchestrators. The framework supports both CPU and GPU workloads with configurable resource requirements.

**Data Management**: Built-in datastore capabilities automatically version and persist all data artifacts between steps. The framework provides fast data access patterns and supports massive embarrassingly parallel workloads through `foreach` constructs. Integration with cloud storage (S3, Azure, GCP) ensures efficient data handling at scale.

**Production Orchestration**: One-click deployment to production-grade orchestrators including AWS Step Functions, Argo Workflows, and Airflow. Support for scheduled execution, event-driven triggering, and reactive orchestration patterns. Built-in failure handling, retry logic, and checkpointing ensure reliable production deployments.

**Dependency Management**: Comprehensive support for Python dependencies through conda, pip, and pypi decorators. Environment isolation ensures reproducibility across different execution environments. The framework handles containerization and environment setup automatically.

**Observability and Debugging**: Rich client API for accessing and inspecting past runs, including the Metaflow, Flow, Run, Step, and Task objects. Built-in experiment tracking and versioning capabilities. Cards system for visualization and result sharing. Integration with tracing and monitoring systems.

## Primary Use Cases and Target Audience

Metaflow serves data scientists, ML engineers, and AI researchers who need to:

- **Prototype rapidly**: Develop and test ML models locally with notebook support and interactive development
- **Scale seamlessly**: Move from laptop to cloud compute without code changes
- **Deploy reliably**: Push workflows to production with built-in orchestration and monitoring
- **Collaborate effectively**: Share results and reproduce experiments across teams
- **Manage complexity**: Handle diverse ML workloads from simple analytics to distributed training

The framework is used by thousands of practitioners across 70+ organizations including Netflix, Amazon, Goldman Sachs, Doordash, Dyson, and many others. At Netflix alone, Metaflow powers over 3000 AI and ML projects, executing hundreds of millions of compute jobs and managing petabytes of data and models.

## High-Level Architecture

**Core Framework**: The foundation consists of the `FlowSpec` base class and decorator system that defines the flow DSL. The graph module parses flow definitions into DAGs, while the parameters system handles runtime configuration and inputs.

**Execution Layer**: The runtime system executes flows locally or delegates to remote compute. The datastore layer manages artifact persistence and retrieval. The metadata provider tracks run information and lineage.

**Plugin System**: Extensive plugin architecture supporting compute backends (batch, kubernetes), orchestrators (step_functions, argo, airflow), cloud providers (aws, azure, gcp), and additional capabilities (cards, secrets, environment management).

**Client API**: Rich Python API for programmatic access to flows, runs, steps, tasks, and artifacts. The Runner and Deployer APIs enable embedding Metaflow in other applications and notebooks.

**CLI and Tools**: Command-line interface for flow execution, deployment, and management. Tutorial system and development tools integrated into the framework.

## Related Projects and Dependencies

**Core Dependencies**:
- `requests`: HTTP client for API communication
- `boto3`: AWS SDK for cloud integration
- Click: CLI framework (vendored)
- PyYAML: Configuration parsing (vendored)
- typing-extensions, importlib-metadata: Python compatibility (vendored)

**Optional Cloud Integrations**:
- AWS: boto3 for S3, Batch, Step Functions, DynamoDB, EventBridge
- Kubernetes: Native client for pod management and execution
- Azure: Cloud storage and compute integration
- GCP: Cloud storage and compute integration

**Development Tools**:
- Conda/pip for dependency management
- Docker for containerization
- pytest for testing
- R integration for R language support

**Extension Ecosystem**: Metaflow supports extensions through the `metaflow_extensions` package system, allowing organizations to customize and extend framework capabilities while maintaining compatibility with the core.

The project is open source under the Apache 2.0 license and actively maintained with contributions from both Netflix/Outerbounds and the broader community. Documentation is available at docs.metaflow.org, and the community communicates through a public Slack workspace.
