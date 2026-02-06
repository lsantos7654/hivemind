# Metaflow APIs and Interfaces

## Public APIs and Entry Points

Metaflow provides three primary API surfaces for different use cases:

**1. Flow Definition API**: For authoring workflows using the FlowSpec DSL
**2. Client API**: For querying and accessing historical flow runs programmatically
**3. Runner API**: For executing flows programmatically from Python code

### Flow Definition API Entry Points

The primary entry point for defining workflows is importing from the top-level `metaflow` module:

```python
from metaflow import FlowSpec, step, Parameter, Config
from metaflow import conda, batch, kubernetes, retry, catch
from metaflow import current, S3, IncludeFile
```

**Key Imports**:
- `FlowSpec`: Base class for all flows
- `step`: Decorator marking functions as workflow steps
- `Parameter`: Input parameters for flows
- `Config`: Configuration parameters loaded from external sources
- Decorators: `conda`, `batch`, `kubernetes`, `retry`, `timeout`, `catch`, `resources`, `card`, etc.
- `current`: Runtime context object (current.step_name, current.task_id, etc.)
- Data tools: `S3`, `IncludeFile`, datatools utilities

### Client API Entry Points

For accessing and querying completed runs:

```python
from metaflow import Metaflow, Flow, Run, Step, Task, DataArtifact
from metaflow import namespace, get_namespace, metadata, get_metadata
```

**Hierarchy**:
```
Metaflow()           # Entry point to all flows
  └─ Flow('MyFlow')   # Specific flow by name
      └─ Run('MyFlow/123')  # Specific run
          └─ Step('end')     # Specific step
              └─ Task('456')  # Specific task
                  └─ DataArtifact('result')  # Specific artifact
```

### Runner API Entry Points (Python 3.7+)

For programmatic execution:

```python
from metaflow import Runner, NBRunner, Deployer, NBDeployer, DeployedFlow
```

## Key Classes, Functions, and Interfaces

### FlowSpec Class

The foundation of flow definition. All workflows inherit from `FlowSpec`:

```python
from metaflow import FlowSpec, step, Parameter

class MyFlow(FlowSpec):
    """
    A simple workflow demonstrating Metaflow basics.
    """

    # Define parameters
    alpha = Parameter('alpha', default=0.5, help='Learning rate')

    @step
    def start(self):
        """Entry point step - required in all flows"""
        print(f"Starting with alpha={self.alpha}")
        self.data = [1, 2, 3, 4, 5]
        self.next(self.process)

    @step
    def process(self):
        """Processing step"""
        self.results = [x * 2 for x in self.data]
        self.next(self.end)

    @step
    def end(self):
        """Exit step - required in all flows"""
        print(f"Results: {self.results}")

if __name__ == '__main__':
    MyFlow()
```

**Key Methods**:
- `self.next(self.step_name)`: Transition to next step(s)
- `self.merge_artifacts()`: Merge artifacts in join steps
- Access to `current` context through instance

**Key Attributes**:
- Parameters defined as class attributes
- Artifacts created by assigning to self (e.g., `self.data = ...`)
- All artifacts automatically versioned and persisted

### Step Decorator and Transitions

The `@step` decorator marks methods as workflow steps:

```python
from metaflow import FlowSpec, step

class BranchingFlow(FlowSpec):

    @step
    def start(self):
        self.branches = ['a', 'b', 'c']
        # Fan-out: parallel execution
        self.next(self.process, foreach='branches')

    @step
    def process(self):
        # Access current branch value
        self.branch_result = f"processed {self.input}"
        self.next(self.join)

    @step
    def join(self, inputs):
        # Fan-in: merge results from parallel branches
        self.all_results = [inp.branch_result for inp in inputs]
        self.merge_artifacts(inputs, exclude=['branch_result'])
        self.next(self.end)

    @step
    def end(self):
        print(f"Completed {len(self.all_results)} branches")
```

**Transition Patterns**:
- **Linear**: `self.next(self.step_name)`
- **Fan-out** (foreach): `self.next(self.step_name, foreach='iterable')`
- **Branch**: `self.next(self.step_a, self.step_b)`
- **Conditional**: Custom logic determining which next() to call

**Join Step Pattern**: When multiple branches converge, the join step receives an `inputs` parameter containing all upstream task objects.

### Decorators for Compute and Dependencies

**Resource Specification**:
```python
from metaflow import FlowSpec, step, resources, batch

class ComputeFlow(FlowSpec):

    @batch(cpu=4, memory=16000, gpu=1, image='my-ml-image:latest')
    @step
    def train(self):
        # Runs on AWS Batch with specified resources
        import tensorflow as tf
        # ... training code
        self.next(self.end)
```

**Dependency Management**:
```python
from metaflow import FlowSpec, step, conda, pypi

class DependencyFlow(FlowSpec):

    @conda(libraries={'pandas': '2.0.0', 'scikit-learn': '1.3.0'})
    @step
    def analyze(self):
        import pandas as pd
        import sklearn
        # Isolated conda environment with specified versions
        self.next(self.end)

    @pypi(packages={'transformers': '4.30.0', 'torch': '2.0.0'})
    @step
    def inference(self):
        from transformers import pipeline
        # Isolated pip environment
        self.next(self.end)
```

**Kubernetes Execution**:
```python
from metaflow import FlowSpec, step, kubernetes

class K8sFlow(FlowSpec):

    @kubernetes(
        cpu=8,
        memory=32000,
        image='my-image:v1',
        namespace='ml-workflows',
        service_account='metaflow-sa',
        secrets=['db-creds']
    )
    @step
    def train_distributed(self):
        # Runs as Kubernetes pod
        self.next(self.end)
```

**Retry and Error Handling**:
```python
from metaflow import FlowSpec, step, retry, catch, timeout

class RobustFlow(FlowSpec):

    @retry(times=3, minutes_between_retries=5)
    @timeout(hours=2)
    @step
    def flaky_api_call(self):
        # Retries up to 3 times on failure
        # Terminates if exceeds 2 hours
        response = make_api_call()
        self.next(self.end)

    @catch(var='error')
    @step
    def might_fail(self):
        # Exception captured in self.error if raised
        risky_operation()
        self.next(self.end)
```

### Parameters and Configuration

**Parameter Types**:
```python
from metaflow import FlowSpec, Parameter, JSONType, IncludeFile

class ParameterizedFlow(FlowSpec):

    # String parameter with default
    model_name = Parameter('model-name',
                           default='bert-base',
                           help='Model to use')

    # Numeric parameter
    learning_rate = Parameter('lr',
                             type=float,
                             default=0.001)

    # Boolean parameter
    debug = Parameter('debug',
                      type=bool,
                      default=False,
                      is_flag=True)

    # JSON parameter for complex types
    config = Parameter('config',
                       type=JSONType,
                       default='{}')

    # Include external file
    data_file = IncludeFile('data',
                           default='data.csv',
                           help='Input data file',
                           is_text=True)
```

**Config System** (for environment-specific values):
```python
from metaflow import FlowSpec, Config, step

class ConfigFlow(FlowSpec):

    # Load from config file
    db = Config('database', default={'host': 'localhost'})

    @step
    def start(self):
        # Access config values
        print(f"Connecting to {self.db.host}")
        self.next(self.end)
```

### Client API for Querying Runs

**Accessing Flow Runs**:
```python
from metaflow import Flow, Metaflow

# List all flows
for flow in Metaflow():
    print(flow.id)

# Access specific flow
flow = Flow('MyFlow')

# Latest run
latest_run = flow.latest_run

# Latest successful run
successful = flow.latest_successful_run

# Access specific run by ID
run = Run('MyFlow/123')

# Iterate through all runs
for run in flow:
    print(f"{run.id}: {run.finished_at}")
```

**Accessing Artifacts**:
```python
from metaflow import Flow

flow = Flow('MyFlow')
run = flow.latest_successful_run

# Access step
step = run['end']  # or run.data.end

# Access task (steps may have multiple tasks in foreach)
task = step.task

# Access artifacts
result = task.data.result  # or task['result']
model = task.data.model

# Iterate through artifacts
for artifact_name in task:
    value = task[artifact_name].data
    print(f"{artifact_name}: {value}")
```

**Filtering and Querying**:
```python
from metaflow import Flow

flow = Flow('MyFlow')

# Filter by tags
tagged_runs = [r for r in flow if 'production' in r.tags]

# Filter by time
from datetime import datetime, timedelta
recent = [r for r in flow
          if r.finished_at > datetime.now() - timedelta(days=7)]

# Access metadata
for run in flow:
    print(f"User: {run.user}")
    print(f"Parameters: {run.data}")
    print(f"Tags: {run.tags}")
```

### Runner API for Programmatic Execution

**Basic Execution**:
```python
from metaflow import Runner

# Create runner
with Runner('myflow.py').run(alpha=0.8) as running:
    # Execution is non-blocking
    print(f"Run ID: {running.run.id}")

    # Wait for completion
    running.wait()

    # Access results
    print(f"Status: {running.status}")
    print(f"Results: {running.run['end'].task.data.results}")
```

**Async Execution**:
```python
from metaflow import Runner
import asyncio

async def execute_flows():
    with Runner('myflow.py') as runner:
        # Launch multiple runs in parallel
        run1 = runner.async_run(alpha=0.5)
        run2 = runner.async_run(alpha=0.8)

        # Wait for both
        await run1.wait()
        await run2.wait()

        print(f"Run 1: {run1.run.id}")
        print(f"Run 2: {run2.run.id}")

asyncio.run(execute_flows())
```

**Notebook Runner** (for Jupyter notebooks):
```python
from metaflow import NBRunner

# Run flow from notebook
runner = NBRunner(globals())
result = runner.run(alpha=0.5)

# Access results directly
print(result.run.data.results)
```

**Deployment API**:
```python
from metaflow import Deployer, step_functions

# Deploy to AWS Step Functions
with Deployer('myflow.py') as deployer:
    deployment = deployer.deploy(
        workflow='step-functions',
        name='my-production-flow',
        tags=['production', 'v1.0']
    )

    print(f"Deployed: {deployment.name}")
    print(f"Workflow ID: {deployment.workflow_id}")

# Trigger deployed flow
deployment.trigger(alpha=0.8)

# List deployments
from metaflow import DeployedFlow
for flow in DeployedFlow('MyFlow'):
    print(f"{flow.name}: {flow.workflow}")
```

### Current Context Object

The `current` singleton provides runtime information:

```python
from metaflow import FlowSpec, step, current

class ContextFlow(FlowSpec):

    @step
    def start(self):
        print(f"Flow name: {current.flow_name}")
        print(f"Run ID: {current.run_id}")
        print(f"Step name: {current.step_name}")
        print(f"Task ID: {current.task_id}")
        print(f"User: {current.username}")
        print(f"Origin run ID: {current.origin_run_id}")

        # Useful for debugging
        print(f"Is running locally: {current.is_running_locally}")

        # Parallel execution context
        if hasattr(current, 'parallel'):
            print(f"Worker index: {current.parallel.node_index}")

        self.next(self.end)
```

**Available Attributes**:
- `flow_name`, `run_id`, `step_name`, `task_id`
- `username`, `origin_run_id`
- `pathspec`: Full path like "MyFlow/123/step/456"
- `is_running_locally`: Boolean for local vs cloud execution
- `retry_count`: Current retry attempt
- `namespace`: Metadata namespace
- `parallel`: Parallel execution context (if applicable)

### Cards System for Visualization

```python
from metaflow import FlowSpec, step, card
from metaflow.cards import Markdown, Table, Image

class CardFlow(FlowSpec):

    @card
    @step
    def analyze(self):
        # Create visualizations
        from metaflow import current

        current.card.append(Markdown("## Analysis Results"))
        current.card.append(Table([[1, 2], [3, 4]]))

        # Or use decorator options
        self.next(self.end)

    @card(type='blank', id='custom')
    @step
    def custom_viz(self):
        from metaflow import current
        current.card['custom'].append(Markdown("# Custom Card"))
        self.next(self.end)
```

## Integration Patterns and Workflows

### Production Deployment Pattern

```python
# 1. Develop locally
python myflow.py run --alpha 0.5

# 2. Test on cloud compute
python myflow.py run --with batch --alpha 0.5

# 3. Deploy to production
python myflow.py step-functions create --alpha 0.5

# 4. Schedule
python myflow.py step-functions create \
    --schedule '@daily' \
    --alpha 0.5
```

### Event-Driven Workflows

```python
from metaflow import FlowSpec, step, trigger, trigger_on_finish

@trigger(event='my-event')
class ReactiveFlow(FlowSpec):
    """Triggered by external events"""

    @step
    def start(self):
        # Access event payload
        print(self.event_data)
        self.next(self.end)

@trigger_on_finish(flow='UpstreamFlow')
class DownstreamFlow(FlowSpec):
    """Triggered when UpstreamFlow completes"""

    @step
    def start(self):
        # Access upstream run
        from metaflow import Flow
        upstream = Flow('UpstreamFlow').latest_run
        self.upstream_data = upstream['end'].task.data
        self.next(self.end)
```

### Parallel and Distributed Training

```python
from metaflow import FlowSpec, step, parallel, batch, kubernetes

class DistributedTraining(FlowSpec):

    @batch(gpu=8, memory=64000, cpu=32)
    @parallel(num_parallel=4)
    @step
    def train_distributed(self):
        """Gang-scheduled multi-node training"""
        from metaflow import current

        # Each node knows its role
        rank = current.parallel.node_index
        world_size = current.parallel.num_nodes

        # Distributed training code
        train_model(rank, world_size)

        self.next(self.gather)

    @step
    def gather(self, inputs):
        """Aggregate results from all nodes"""
        self.merge_artifacts(inputs)
        self.next(self.end)
```

### Hyperparameter Tuning Pattern

```python
from metaflow import FlowSpec, step, batch

class HPTuning(FlowSpec):

    @step
    def start(self):
        # Define parameter grid
        self.configs = [
            {'lr': 0.001, 'batch': 32},
            {'lr': 0.01, 'batch': 64},
            {'lr': 0.1, 'batch': 128}
        ]
        # Parallel trials
        self.next(self.train, foreach='configs')

    @batch(cpu=4, memory=16000)
    @step
    def train(self):
        # Train with self.input config
        config = self.input
        self.score = train_model(**config)
        self.next(self.join)

    @step
    def join(self, inputs):
        # Find best configuration
        best = max(inputs, key=lambda x: x.score)
        self.best_config = best.input
        self.best_score = best.score
        self.next(self.end)
```

## Configuration Options and Extension Points

### Extension Points

**Custom Decorators**:
```python
from metaflow import StepDecorator

class MyDecorator(StepDecorator):
    name = 'my_decorator'
    defaults = {'option': 'value'}

    def task_pre_step(self, step_name, task_datastore, metadata):
        # Called before step execution
        pass

    def task_post_step(self, step_name, flow, graph, retry_count):
        # Called after step execution
        pass
```

**Extension Packages**: Create `metaflow_extensions` packages to:
- Add custom decorators
- Register CLI commands
- Provide custom datastores
- Integrate new compute backends
- Add metadata providers

### Configuration Files

Metaflow is configured through environment variables and config files:

```bash
# ~/.metaflowconfig/config.json
{
    "METAFLOW_DATASTORE_SYSROOT_S3": "s3://my-bucket/metaflow",
    "METAFLOW_SERVICE_URL": "https://metadata.mycompany.com",
    "METAFLOW_DEFAULT_METADATA": "service"
}
```

Key configuration options:
- `METAFLOW_DATASTORE_SYSROOT_*`: Storage location
- `METAFLOW_SERVICE_*`: Metadata service settings
- `METAFLOW_BATCH_*`: AWS Batch configuration
- `METAFLOW_KUBERNETES_*`: Kubernetes settings
- `METAFLOW_DEFAULT_METADATA`: Metadata provider choice
