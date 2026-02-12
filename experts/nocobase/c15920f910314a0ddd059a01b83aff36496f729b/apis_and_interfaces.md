# NocoBase APIs and Interfaces

## Public APIs and Entry Points

NocoBase provides APIs at multiple levels: server-side application APIs, database APIs, client-side APIs, and plugin development APIs.

## Server-Side APIs

### Application Class

The `Application` class is the main entry point for NocoBase server applications.

**Location:** `packages/core/server/src/application.ts:222`

**Basic Usage:**
```typescript
import { Application } from '@nocobase/server';

const app = new Application({
  database: {
    dialect: 'postgres',
    host: 'localhost',
    port: 5432,
    username: 'nocobase',
    password: 'password',
    database: 'nocobase',
  },
  resourcer: {
    prefix: '/api',
  },
  plugins: [],
});

// Start the application
app.runAsCLI();
```

**Key Methods:**
```typescript
class Application extends Koa {
  // Lifecycle
  async load(): Promise<void>
  async start(): Promise<void>
  async stop(): Promise<void>
  async destroy(): Promise<void>
  async reload(): Promise<void>

  // Database
  collection(options: CollectionOptions): Collection
  async db.sync(): Promise<void>

  // Plugin Management
  plugin(plugin: PluginType, options?: any): void
  pm: PluginManager

  // Resource Management
  resource(options: ResourceOptions): Resource
  resourcer: Resourcer

  // Middleware
  use(middleware: Middleware): void
  acl: ACL

  // CLI
  runAsCLI(argv?: string[], options?: ParseOptions): Promise<void>
  command(name: string): Command

  // Cache and Services
  cache: CacheManager
  locales: Locale
  logger: Logger
  telemetry: Telemetry
}
```

**Application Options:**
```typescript
interface ApplicationOptions {
  database?: IDatabaseOptions | Database
  resourcer?: ResourceManagerOptions
  plugins?: PluginConfiguration[]
  acl?: boolean
  logger?: LoggerOptions
  cors?: CorsOptions
  dataWrapping?: boolean
  registerActions?: boolean
  i18n?: i18n | InitOptions
  pmSock?: string
  telemetry?: TelemetryOptions
  cache?: CacheManagerOptions
  pubSubManager?: PubSubManagerOptions
}
```

### Database API

**Location:** `packages/core/database/src/database.ts`

**Creating Collections:**
```typescript
import { Database } from '@nocobase/database';

const db = new Database({
  dialect: 'postgres',
  host: 'localhost',
  database: 'mydb',
});

// Define a collection (table)
const users = db.collection({
  name: 'users',
  fields: [
    { type: 'string', name: 'username', unique: true },
    { type: 'string', name: 'email' },
    { type: 'password', name: 'password', hidden: true },
    { type: 'integer', name: 'age' },
    { type: 'belongsTo', name: 'profile', target: 'profiles' },
    { type: 'hasMany', name: 'posts', target: 'posts', foreignKey: 'userId' },
  ],
});

// Sync to database
await db.sync();
```

**Repository Pattern:**
```typescript
// Get repository for a collection
const userRepo = db.getRepository('users');

// CRUD operations
const user = await userRepo.create({
  values: {
    username: 'john',
    email: 'john@example.com',
    password: 'secret123',
  },
});

const users = await userRepo.find({
  filter: {
    age: { $gte: 18 },
  },
  sort: ['-createdAt'],
  limit: 10,
  offset: 0,
});

await userRepo.update({
  filterByTk: user.id,
  values: {
    age: 25,
  },
});

await userRepo.destroy({
  filter: {
    id: user.id,
  },
});
```

**Field Types:**
NocoBase supports extensive field types:
- Basic: `string`, `text`, `integer`, `bigInt`, `float`, `double`, `decimal`, `boolean`, `date`, `dateonly`, `time`
- Special: `password`, `uuid`, `json`, `jsonb`, `array`, `virtual`
- Relations: `belongsTo`, `hasMany`, `hasOne`, `belongsToMany`
- Advanced: `formula`, `sequence`, `sort`, `markdown`, `richText`

**Query Operators:**
```typescript
// Comparison operators
{ age: { $gt: 18 } }          // Greater than
{ age: { $gte: 18 } }         // Greater than or equal
{ age: { $lt: 65 } }          // Less than
{ age: { $lte: 65 } }         // Less than or equal
{ age: { $ne: null } }        // Not equal
{ status: { $in: ['active', 'pending'] } }
{ status: { $notIn: ['banned'] } }

// String operators
{ name: { $like: '%john%' } }
{ name: { $iLike: '%john%' } }  // Case insensitive
{ name: { $startsWith: 'john' } }
{ name: { $endsWith: 'doe' } }

// Logical operators
{ $and: [{ age: { $gte: 18 } }, { status: 'active' }] }
{ $or: [{ role: 'admin' }, { role: 'moderator' }] }
{ $not: { status: 'banned' } }

// Array operators
{ tags: { $anyOf: ['javascript', 'typescript'] } }
{ tags: { $allOf: ['javascript', 'nodejs'] } }

// Association filters
{ 'posts.title': { $like: '%NocoBase%' } }
```

### Resource and Action API

**Location:** `packages/core/resourcer/src/`

**Defining Resources:**
```typescript
import { Resourcer } from '@nocobase/resourcer';

const resourcer = new Resourcer();

// Define a resource
resourcer.define({
  name: 'users',
  actions: {
    list: async (ctx, next) => {
      const { page = 1, pageSize = 20 } = ctx.action.params;
      const users = await ctx.db.getRepository('users').find({
        offset: (page - 1) * pageSize,
        limit: pageSize,
      });
      ctx.body = users;
      await next();
    },
    get: async (ctx, next) => {
      const { filterByTk } = ctx.action.params;
      const user = await ctx.db.getRepository('users').findOne({
        filterByTk,
      });
      ctx.body = user;
      await next();
    },
    create: async (ctx, next) => {
      const { values } = ctx.action.params;
      const user = await ctx.db.getRepository('users').create({
        values,
      });
      ctx.body = user;
      await next();
    },
  },
});

// Association resources
resourcer.define({
  name: 'users.posts',
  actions: {
    list: async (ctx, next) => {
      // List posts for a specific user
    },
  },
});
```

**RESTful API Patterns:**
```
GET    /api/users              # List users
GET    /api/users:list         # Explicit list action
GET    /api/users/1            # Get user by ID
GET    /api/users:get/1        # Explicit get action
POST   /api/users              # Create user
POST   /api/users:create       # Explicit create action
PUT    /api/users/1            # Update user
POST   /api/users:update/1     # Explicit update action
DELETE /api/users/1            # Delete user
POST   /api/users:destroy/1    # Explicit destroy action

# Association resources
GET    /api/users/1/posts      # List user's posts
POST   /api/users/1/posts      # Create post for user
GET    /api/users/1/posts/2    # Get specific post
```

### Plugin Development API

**Location:** `packages/core/server/src/plugin.ts`

**Creating a Plugin:**
```typescript
import { Plugin } from '@nocobase/server';

export class MyPlugin extends Plugin {
  // Called after plugin is added to app
  afterAdd() {
    // Register event listeners, etc.
  }

  // Called before plugin loads
  beforeLoad() {
    // Prepare resources, check dependencies
  }

  // Main plugin loading
  async load() {
    // Define collections
    this.db.collection({
      name: 'my_table',
      fields: [
        { type: 'string', name: 'name' },
      ],
    });

    // Define resources
    this.app.resource({
      name: 'my_resource',
      actions: {
        custom: async (ctx, next) => {
          ctx.body = { message: 'Hello from my plugin!' };
          await next();
        },
      },
    });

    // Add middleware
    this.app.use(async (ctx, next) => {
      console.log('My plugin middleware');
      await next();
    });

    // Register ACL actions
    this.app.acl.allow('my_resource', 'custom', 'loggedIn');
  }

  // Called during installation
  async install(options) {
    // Initial data seeding, configuration
  }

  // Called during upgrade
  async upgrade() {
    // Migration logic
  }

  // Plugin enable/disable hooks
  async beforeEnable() {}
  async afterEnable() {}
  async beforeDisable() {}
  async afterDisable() {}

  // Plugin removal hooks
  async beforeRemove() {}
  async afterRemove() {}
}

export default MyPlugin;
```

**Plugin Helpers:**
```typescript
class Plugin {
  // Properties
  name: string              // Plugin name
  app: Application          // Application instance
  db: Database              // Database instance
  pm: PluginManager         // Plugin manager
  log: Logger               // Plugin logger
  enabled: boolean          // Enable state
  installed: boolean        // Install state

  // Methods
  createLogger(options: LoggerOptions): Logger
  t(key: string, options?: any): string  // i18n translation
  async sendSyncMessage(message: any): Promise<void>
  async handleSyncMessage(message: any): Promise<void>
}
```

## Client-Side APIs

### Application API

**Location:** `packages/core/client/src/application/Application.tsx`

**Creating a Client Application:**
```typescript
import { Application } from '@nocobase/client';

const app = new Application({
  apiClient: {
    baseURL: 'http://localhost:13000/api',
  },
  plugins: [],
});

// Add plugins
app.addPlugin(MyClientPlugin);

// Mount to DOM
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<app.Root />);
```

**Client Plugin Development:**
```typescript
import { Plugin } from '@nocobase/client';

export class MyClientPlugin extends Plugin {
  async load() {
    // Register schema components
    this.app.addComponents({
      MyComponent,
    });

    // Add schema initializers
    this.app.schemaInitializerManager.add(myInitializer);

    // Add schema settings
    this.app.schemaSettingsManager.add(mySettings);

    // Add routes
    this.app.router.add('my-route', {
      path: '/my-page',
      Component: MyPageComponent,
    });

    // Register providers
    this.app.addProvider(MyProvider);
  }
}
```

### API Client

**Making API Requests:**
```typescript
import { useAPIClient, useRequest } from '@nocobase/client';

// In a component
function MyComponent() {
  const api = useAPIClient();

  // Using useRequest hook
  const { data, loading, error, run } = useRequest({
    resource: 'users',
    action: 'list',
    params: {
      filter: { status: 'active' },
      pageSize: 20,
    },
  });

  // Manual API call
  const handleCreate = async () => {
    const user = await api.resource('users').create({
      values: {
        username: 'john',
        email: 'john@example.com',
      },
    });
  };

  return <div>{/* ... */}</div>;
}
```

**API Client Methods:**
```typescript
const api = useAPIClient();

// Resource operations
await api.resource('users').list(params);
await api.resource('users').get({ filterByTk: 1 });
await api.resource('users').create({ values: data });
await api.resource('users').update({ filterByTk: 1, values: data });
await api.resource('users').destroy({ filterByTk: 1 });

// Association operations
await api.resource('users.posts').list({ associatedIndex: userId });
await api.resource('users.posts').create({
  associatedIndex: userId,
  values: postData
});

// Custom actions
await api.resource('users').customAction({
  filterByTk: 1,
  values: data
});

// Direct HTTP
await api.request({ url: '/custom-endpoint', method: 'POST', data });
```

### Schema System

**Schema Components:**
```typescript
import { SchemaComponent, useSchemaComponentContext } from '@nocobase/client';

const schema = {
  type: 'void',
  'x-component': 'Page',
  properties: {
    table: {
      type: 'void',
      'x-component': 'Table',
      'x-component-props': {
        dataSource: 'users',
        columns: [
          { title: 'Username', dataIndex: 'username' },
          { title: 'Email', dataIndex: 'email' },
        ],
      },
    },
  },
};

function MyPage() {
  return <SchemaComponent schema={schema} />;
}
```

**Schema Initializers:**
```typescript
import { SchemaInitializer } from '@nocobase/client';

const myInitializer = new SchemaInitializer({
  name: 'MyInitializer',
  title: 'Add Block',
  items: [
    {
      name: 'table',
      title: 'Table',
      Component: TableBlockInitializer,
    },
    {
      name: 'form',
      title: 'Form',
      Component: FormBlockInitializer,
    },
  ],
});
```

## Integration Patterns and Workflows

### Collection to Resource Auto-Mapping

Collections automatically become REST resources:
```typescript
// Define collection
app.collection({
  name: 'products',
  fields: [
    { type: 'string', name: 'name' },
    { type: 'decimal', name: 'price' },
  ],
});

// Automatically available at /api/products with standard CRUD
```

### Action Middleware Pattern

```typescript
app.resource({
  name: 'users',
  actions: {
    list: [
      // Middleware chain
      async (ctx, next) => {
        // Pre-processing
        console.log('Before list');
        await next();
        // Post-processing
        console.log('After list');
      },
      async (ctx, next) => {
        // Main action
        const users = await ctx.db.getRepository('users').find(ctx.action.params);
        ctx.body = users;
        await next();
      },
    ],
  },
});
```

### Event-Driven Workflows

```typescript
// Database hooks
db.on('users.afterCreate', async (model, options) => {
  console.log('User created:', model.id);
  // Send welcome email, etc.
});

db.on('users.beforeDestroy', async (model, options) => {
  // Cleanup related data
});

// Application events
app.on('beforeStart', async () => {
  console.log('Application starting...');
});

app.on('afterStart', async () => {
  console.log('Application started');
});
```

### ACL Integration Pattern

```typescript
// Define ACL rules
app.acl.define({
  role: 'member',
  actions: {
    'posts:create': {},
    'posts:update': {
      filter: { 'createdById.$eq': '{{ ctx.state.currentUser.id }}' },
    },
    'posts:destroy': {
      filter: { 'createdById.$eq': '{{ ctx.state.currentUser.id }}' },
    },
  },
});

// Check permissions in action
app.resource({
  name: 'posts',
  actions: {
    publish: async (ctx, next) => {
      const canPublish = await ctx.can('publish', 'posts');
      if (!canPublish) {
        throw new Error('Permission denied');
      }
      // Publish logic
    },
  },
});
```

## Configuration Options and Extension Points

### Application Configuration

```typescript
const app = new Application({
  // Database configuration
  database: {
    dialect: 'postgres',
    host: 'localhost',
    port: 5432,
    username: 'nocobase',
    password: 'password',
    database: 'nocobase',
    logging: console.log,
    timezone: '+08:00',
    tablePrefix: 'nc_',
  },

  // Resource configuration
  resourcer: {
    prefix: '/api',
  },

  // Logging
  logger: {
    level: 'info',
    transports: ['console', 'dailyRotateFile'],
  },

  // Caching
  cache: {
    defaultStore: 'memory',
    stores: {
      memory: {
        max: 2000,
      },
      redis: {
        host: 'localhost',
        port: 6379,
      },
    },
  },

  // Telemetry
  telemetry: {
    enabled: true,
    serviceName: 'nocobase',
  },

  // Plugin configuration
  plugins: [
    ['@nocobase/plugin-acl', { enabled: true }],
    ['@nocobase/plugin-workflow', { /* config */ }],
  ],
});
```

### Plugin Extension Points

Plugins can extend nearly every aspect of NocoBase:

1. **Database Schema**: Add collections, fields, indexes
2. **REST API**: Define resources, actions, middleware
3. **UI Components**: Register schema components, blocks, fields
4. **Workflow Nodes**: Add custom workflow triggers and actions
5. **Authentication**: Add auth providers (OAuth, SAML, etc.)
6. **Data Sources**: Connect external databases and APIs
7. **File Storage**: Add storage providers (S3, OSS, etc.)
8. **AI Integration**: Register AI models and capabilities

### Custom Field Types

```typescript
import { Field } from '@nocobase/database';

class CustomField extends Field {
  get dataType() {
    return DataTypes.STRING;
  }

  bind() {
    super.bind();
    // Custom binding logic
  }

  unbind() {
    // Cleanup logic
    super.unbind();
  }
}

// Register field type
db.registerFieldTypes({
  custom: CustomField,
});

// Use in collection
db.collection({
  name: 'items',
  fields: [
    { type: 'custom', name: 'customField' },
  ],
});
```

### CLI Extension

```typescript
// In plugin
async load() {
  this.app.command('my-command')
    .option('-f, --force')
    .action(async (options) => {
      console.log('Running custom command');
    });
}
```

This API surface provides comprehensive access to NocoBase's capabilities, supporting everything from simple CRUD applications to complex enterprise systems with custom workflows, multi-tenancy, and AI integration.
