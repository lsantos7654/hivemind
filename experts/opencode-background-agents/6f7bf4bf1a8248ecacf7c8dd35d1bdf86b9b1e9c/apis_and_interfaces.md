# OpenCode Background Agents - APIs and Interfaces

## Public APIs and Entry Points

### Plugin Entry Point
The plugin exports a default function that serves as the main entry point for OpenCode's plugin system:

```typescript
export const BackgroundAgentsPlugin: Plugin = async (ctx) => {
  const { client, directory } = ctx
  // Plugin initialization and return configuration object
}
export default BackgroundAgentsPlugin
```

**Plugin Context (`ctx`):**
- `client`: OpenCode client instance for API interactions
- `directory`: Current working directory for project identification

### Tool Interface APIs

The plugin exposes three primary tools through OpenCode's tool system:

#### **`delegate(prompt, agent)` - Background Task Creation**
**Purpose**: Launch asynchronous background tasks with immediate ID return
**Parameters**:
- `prompt` (string): Detailed task description for the agent
- `agent` (string): Target agent name ("explore", "researcher", "scribe", "general")

**Return**: Immediate acknowledgment with readable delegation ID

**Usage Example**:
```typescript
// Tool call from OpenCode interface
delegate("Research OAuth2 PKCE best practices", "researcher")
// Returns: "Delegation started: swift-amber-falcon\nAgent: researcher"
```

#### **`delegation_read(id)` - Result Retrieval**  
**Purpose**: Retrieve completed delegation results by ID
**Parameters**:
- `id` (string): Delegation ID (e.g., "swift-amber-falcon")

**Return**: Full markdown-formatted delegation result with metadata

**Usage Example**:
```typescript
delegation_read("swift-amber-falcon")
// Returns: Full delegation markdown with title, description, and result content
```

#### **`delegation_list()` - Delegation Discovery**
**Purpose**: List all delegations with status and metadata
**Parameters**: None

**Return**: Formatted list of delegations with titles, descriptions, and status

**Usage Example**:
```typescript
delegation_list()
// Returns: Markdown-formatted list of all delegations with metadata
```

## Key Classes, Functions, and Macros

### Core Classes

#### **DelegationManager Class**
**Purpose**: Central orchestrator for delegation lifecycle management
**Key methods**:

```typescript
class DelegationManager {
  // Core delegation operations
  async delegate(input: DelegateInput): Promise<Delegation>
  async readOutput(sessionID: string, id: string): Promise<string>
  async listDelegations(sessionID: string): Promise<DelegationListItem[]>
  
  // Event handling
  async handleSessionIdle(sessionID: string): Promise<void>
  handleMessageEvent(sessionID: string, messageText?: string): void
  
  // Internal management
  private async persistOutput(delegation: Delegation, content: string): Promise<void>
  private async notifyParent(delegation: Delegation): Promise<void>
  private async getResult(delegation: Delegation): Promise<string>
}
```

**Constructor Parameters**:
```typescript
constructor(client: OpencodeClient, baseDir: string, log: Logger)
```

### Key Functions

#### **Agent Capability Detection**
```typescript
async function parseAgentWriteCapability(
  client: OpencodeClient,
  agentName: string, 
  log: Logger
): Promise<{ isReadOnly: boolean }>
```
**Purpose**: Determines if an agent has write capabilities by parsing OpenCode configuration
**Logic**: Checks if edit, write, and bash permissions are all denied

#### **Metadata Generation**
```typescript
async function generateMetadata(
  client: OpencodeClient,
  resultContent: string,
  parentID: string,
  debugLog: (msg: string) => Promise<void>
): Promise<GeneratedMetadata>
```
**Purpose**: Uses small language model to generate titles and descriptions for delegation results
**Fallback**: Truncation-based metadata when small_model unavailable

#### **Project Identification**
```typescript
async function getProjectId(projectRoot: string, client?: OpencodeClient): Promise<string>
```
**Purpose**: Generate stable project identifier for cross-worktree storage consistency
**Strategy**: Git root commit SHA with path-based fallback

### Data Structures and Interfaces

#### **Delegation Interface**
```typescript
interface Delegation {
  id: string                    // Human-readable ID (e.g., "swift-amber-falcon")
  sessionID: string            // OpenCode session ID for the delegation
  parentSessionID: string      // Parent session for notifications
  parentMessageID: string      // Parent message context
  parentAgent: string          // Agent that created the delegation
  prompt: string               // Original delegation prompt
  agent: string                // Target agent name
  status: "running" | "complete" | "error" | "cancelled" | "timeout"
  startedAt: Date             // Delegation creation timestamp
  completedAt?: Date          // Completion timestamp
  progress: DelegationProgress // Progress tracking information
  error?: string              // Error message if failed
  title?: string              // Generated title (from small_model)
  description?: string        // Generated description (from small_model)
  result?: string             // Final delegation result
}
```

#### **Tool Context Interface**
```typescript
interface ToolContext {
  sessionID: string    // Current OpenCode session
  messageID: string    // Current message context
  agent: string        // Current agent name
}
```

## Usage Examples with Code Snippets

### Basic Delegation Workflow

#### **1. Creating a Background Delegation**
```typescript
// User initiates delegation through OpenCode interface
const result = await delegate(
  "Research the latest OAuth2 security best practices and PKCE implementation patterns", 
  "researcher"
)
console.log(result)
// Output: "Delegation started: elegant-blue-tiger\nAgent: researcher\nYou WILL be notified when complete. Do NOT poll."
```

#### **2. Retrieving Results**
```typescript
// After receiving completion notification
const delegationResult = await delegation_read("elegant-blue-tiger")
console.log(delegationResult)
/* Output: 
# OAuth2 Security Best Practices

Research on OAuth2 PKCE implementation patterns and security considerations...

**ID:** elegant-blue-tiger
**Agent:** researcher  
**Status:** complete
**Started:** 2026-03-18T10:30:00.000Z
**Completed:** 2026-03-18T10:32:45.000Z

---

[Full research results...]
*/
```

#### **3. Listing All Delegations**
```typescript
const allDelegations = await delegation_list()
console.log(allDelegations)
/* Output:
## Delegations

- **elegant-blue-tiger** | OAuth2 Security Best Practices [complete]
  → Research on OAuth2 PKCE implementation patterns and security considerations
- **swift-red-falcon** | Database Migration Analysis [running]
  → Analyzing database schema changes for version 2.0
*/
```

### Advanced Integration Patterns

#### **Error Handling Pattern**
```typescript
try {
  const delegation = await delegate("Invalid task", "nonexistent-agent")
} catch (error) {
  console.log(error.message)
  // Output: Agent "nonexistent-agent" not found.\n\nAvailable agents:\n• researcher - External research and analysis\n• explore - Codebase exploration and analysis
}
```

#### **Agent Routing Validation**
```typescript
// Attempting to use write-capable agent with delegate tool
try {
  const result = await delegate("Write a new feature", "coder")
} catch (error) {
  console.log(error.message)
  // Output: Agent "coder" is write-capable and requires the native `task` tool for proper undo/branching support.
}
```

## Integration Patterns and Workflows

### Hook-Based Integration

#### **System Prompt Injection**
```typescript
"experimental.chat.system.transform": async (_input, output) => {
  output.system.push(DELEGATION_RULES)
}
```
**Purpose**: Injects delegation usage rules into every chat session
**Content**: Guidelines for agent routing, completion notification expectations, and tool usage patterns

#### **Context Compaction Preservation**  
```typescript
"experimental.session.compacting": async (input, output) => {
  const running = manager.getRunningDelegations()
  const completed = await manager.listDelegations(input.sessionID) 
  output.context.push(formatDelegationContext(running, completed))
}
```
**Purpose**: Preserves delegation context during OpenCode's context compaction
**Strategy**: Injects delegation status and recent results into compaction context

#### **Tool Execution Interception**
```typescript  
"tool.execute.before": async (input, output) => {
  if (input.tool !== "task") return
  const { isReadOnly } = await parseAgentWriteCapability(client, agentName, log)
  if (isReadOnly) {
    throw new Error("Read-only agent should use delegate tool")
  }
}
```
**Purpose**: Prevents incorrect tool usage by enforcing agent routing rules
**Logic**: Read-only agents must use `delegate`, write-capable agents must use `task`

### Event-Driven Workflows

#### **Session Lifecycle Management**
```typescript
event: async ({ event }) => {
  if (event.type === "session.idle") {
    const delegation = manager.findBySession(event.properties.sessionID)
    if (delegation) {
      await manager.handleSessionIdle(event.properties.sessionID)
    }
  }
}
```
**Purpose**: Handles delegation completion when background sessions become idle
**Process**: Extracts results, generates metadata, persists to storage, notifies parent

#### **Progress Tracking Integration**
```typescript
if (event.type === "message.updated") {
  const sessionID = event.properties.info.sessionID
  manager.handleMessageEvent(sessionID)
}
```
**Purpose**: Updates delegation progress tracking based on message activity
**Usage**: Provides last activity timestamps for monitoring and debugging

## Configuration Options and Extension Points

### Agent Configuration Integration

#### **Permission-Based Routing**
The plugin reads OpenCode's agent configuration to determine routing:
```typescript
// Agent configuration structure
{
  agent: {
    "researcher": {
      permission: {
        edit: "deny",
        write: "deny", 
        bash: { "*": "deny" }
      }
    }
  }
}
```
**Read-only determination**: All write tools (edit, write, bash) must be denied
**Routing decision**: Read-only agents use `delegate`, others use `task`

#### **Small Model Integration**
```typescript
// Configuration check for metadata generation
const config = await client.config.get()
const configData = config.data as { small_model?: string }
if (configData?.small_model) {
  // Use small model for title/description generation
}
```
**Purpose**: Leverages configured small model for delegation metadata generation
**Fallback**: Text truncation when small model unavailable

### Storage Configuration

#### **Project-Scoped Storage**
```typescript
// Storage location determination
const projectId = await getProjectId(directory)
const baseDir = path.join(os.homedir(), ".local", "share", "opencode", "delegations", projectId)
```
**Strategy**: Git repository-based project identification for stable storage
**Structure**: `~/.local/share/opencode/delegations/<project-id>/<root-session-id>/`

#### **Cross-Worktree Consistency**
The storage system handles git worktrees automatically:
- Resolves `.git` file references to shared repository
- Uses common git directory for project identification
- Ensures all worktrees share delegation storage

### Extension Points for Customization

#### **Custom Metadata Generators**
Replace the `generateMetadata` function to customize title/description generation:
```typescript
async function customGenerateMetadata(
  client: OpencodeClient,
  resultContent: string,
  parentID: string,
  debugLog: (msg: string) => Promise<void>
): Promise<GeneratedMetadata> {
  // Custom metadata generation logic
}
```

#### **Storage Backend Customization**
Modify storage location and format by extending `DelegationManager`:
```typescript
class CustomDelegationManager extends DelegationManager {
  private async persistOutput(delegation: Delegation, content: string): Promise<void> {
    // Custom storage implementation
  }
}
```

#### **Agent Capability Detection Extension**
Extend agent routing logic for custom agent types:
```typescript
async function customParseAgentCapability(
  client: OpencodeClient,
  agentName: string,
  log: Logger
): Promise<{ customCapability: boolean }> {
  // Custom agent capability detection
}
```

The API design prioritizes simplicity for common use cases while providing comprehensive extension points for advanced customization. The tool interface maintains consistency with OpenCode's native tools while adding powerful background delegation capabilities.