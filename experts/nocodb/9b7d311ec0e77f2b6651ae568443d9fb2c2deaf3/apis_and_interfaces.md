# NocoDB APIs and Interfaces

## Public APIs and Entry Points

NocoDB provides comprehensive REST APIs organized into multiple versions and categories. The primary API entry points are:

**API Versions:**
- `/api/v1/*` - Original stable API (most endpoints)
- `/api/v2/*` - Enhanced API with improved performance
- `/api/v3/*` - Next-generation API (in development)

**Main API Categories:**

1. **Metadata APIs** (`/api/v1/db/meta/*`)
   - Database schema management
   - Table and column operations
   - View management
   - Relationship configuration

2. **Data APIs** (`/api/v2/tables/{tableId}/*`)
   - CRUD operations on table data
   - Bulk operations
   - Data filtering and sorting
   - Aggregations and grouping

3. **Public/Shared APIs** (`/api/v1/db/public/*`, `/api/v2/public/*`)
   - Shared view access
   - Form submissions
   - Public calendar views
   - Password-protected shares

4. **Internal APIs** (`/api/v1/db/internal/*`)
   - Link column operations
   - Internal metadata management

5. **Authentication APIs** (`/api/v1/auth/*`)
   - User authentication
   - Token management
   - OAuth flows

6. **Base Management APIs** (`/api/v1/db/meta/bases/*`, `/api/v2/meta/bases/*`)
   - Base (project) creation and management
   - User permissions
   - Base settings

## Key Classes, Functions, and Macros

### Backend Core Classes

**1. Noco Class (src/Noco.ts)**
The main application singleton that initializes and manages the NocoDB instance.

```typescript
class Noco {
  static _this: Noco;
  static _httpServer: http.Server;
  static _nestApp: INestApplication;

  static async init(
    params: any,
    httpServer: http.Server,
    app: Express
  ): Promise<Router>;

  static get dashboardUrl(): string;
  static get ncMeta(): MetaService;
}
```

Key methods:
- `init()`: Initialize NocoDB with configuration
- `dashboardUrl`: Get the dashboard URL
- `ncMeta`: Access metadata service

**2. BaseModelSqlv2 (src/db/BaseModelSqlv2.ts)**
The core data access layer for SQL operations on tables.

```typescript
class BaseModelSqlv2 {
  constructor(args: {
    dbDriver: XKnex;
    model: Model;
    view?: View;
  });

  // CRUD Operations
  async insert(data: any, trx?: any, cookie?: any): Promise<any>;
  async delByPk(id: any, trx?: any, cookie?: any): Promise<any>;
  async updateByPk(id: any, data: any, trx?: any, cookie?: any): Promise<any>;
  async readByPk(id: any, validateFormula = false, query?: any): Promise<any>;

  // List Operations
  async list(args?: {
    fieldsSet?: Set<string>;
    viewId?: string;
    where?: string;
    limit?: number;
    offset?: number;
    sort?: string;
  }): Promise<any>;

  // Aggregations
  async groupBy(args: {
    groupByColumnIds?: string[];
    where?: string;
  }): Promise<any>;

  // Nested Operations
  async nestedRead(args: {
    columnId: string;
    id: any;
  }): Promise<any>;
}
```

**3. Model Classes (src/models/)**

Essential model classes that map to database tables:

```typescript
// Base (Project) Model
class Base {
  static async get(baseId: string, ncMeta = Noco.ncMeta): Promise<Base>;
  static async list(args?: any, ncMeta = Noco.ncMeta): Promise<Base[]>;
  static async createBase(base: Partial<Base>, ncMeta = Noco.ncMeta): Promise<Base>;
  async getTables(ncMeta = Noco.ncMeta): Promise<Model[]>;
  async delete(ncMeta = Noco.ncMeta): Promise<void>;
}

// Table (Model) Model
class Model {
  static async get(modelId: string, ncMeta = Noco.ncMeta): Promise<Model>;
  static async list(args: any, ncMeta = Noco.ncMeta): Promise<Model[]>;
  async getColumns(ncMeta = Noco.ncMeta): Promise<Column[]>;
  async getViews(force?: boolean, ncMeta = Noco.ncMeta): Promise<View[]>;
}

// Column Model
class Column {
  static async get(args: { colId: string }, ncMeta = Noco.ncMeta): Promise<Column>;
  static async insert(column: Partial<Column>, ncMeta = Noco.ncMeta): Promise<Column>;
  async delete(ncMeta = Noco.ncMeta): Promise<void>;
}

// View Model
class View {
  static async get(viewId: string, ncMeta = Noco.ncMeta): Promise<View>;
  static async list(tableId: string, ncMeta = Noco.ncMeta): Promise<View[]>;
  async getColumns(ncMeta = Noco.ncMeta): Promise<Column[]>;
  async getFilters(ncMeta = Noco.ncMeta): Promise<Filter[]>;
}
```

**4. Service Layer (src/services/)**

Services implement business logic:

```typescript
// Data Table Service
@Injectable()
class DataTableService {
  async dataList(params: {
    baseId: string;
    modelId: string;
    query: any;
  }): Promise<any>;

  async dataRead(params: {
    baseId: string;
    modelId: string;
    rowId: any;
    query?: any;
  }): Promise<any>;

  async dataInsert(params: {
    baseId: string;
    modelId: string;
    body: any;
  }): Promise<any>;

  async dataUpdate(params: {
    baseId: string;
    modelId: string;
    rowId: any;
    body: any;
  }): Promise<any>;

  async dataDelete(params: {
    baseId: string;
    modelId: string;
    rowId: any;
  }): Promise<number>;
}

// Bases Service
@Injectable()
class BasesService {
  async baseList(params: {
    workspaceId?: string;
    user: any;
  }): Promise<Base[]>;

  async baseCreate(params: {
    base: Partial<Base>;
    user: any;
  }): Promise<Base>;

  async baseUpdate(params: {
    baseId: string;
    base: Partial<Base>;
    user: any;
  }): Promise<Base>;
}

// Columns Service
@Injectable()
class ColumnsService {
  async columnAdd(params: {
    tableId: string;
    column: Partial<Column>;
    user: any;
  }): Promise<Column>;

  async columnUpdate(params: {
    columnId: string;
    column: Partial<Column>;
    user: any;
  }): Promise<Column>;

  async columnDelete(params: {
    columnId: string;
    user: any;
  }): Promise<boolean>;
}
```

### Frontend Core Composables

**1. useApi (composables/useApi/index.ts)**
Primary API client composable:

```typescript
function useApi() {
  const api: Api = createEventHook<Api>();
  const isLoading = ref(false);
  const error = ref(null);

  return {
    api,
    isLoading,
    error,
  };
}
```

**2. useGlobal (composables/useGlobal/)**
Global state management:

```typescript
interface GlobalState {
  user: User | null;
  token: string | null;
  workspace: Workspace | null;
  base: Base | null;
}

function useGlobal() {
  const state = useState<GlobalState>();
  const signIn = async (credentials: any) => Promise<void>;
  const signOut = async () => Promise<void>;
  const loadBase = async (baseId: string) => Promise<void>;

  return {
    state,
    signIn,
    signOut,
    loadBase,
  };
}
```

**3. useViewData (composables/useViewData.ts)**
View data management:

```typescript
function useViewData(
  meta: Ref<TableType>,
  viewMeta: Ref<ViewType>,
) {
  const data = ref<any[]>([]);
  const paginationData = ref<PaginationData>();

  const loadData = async (params?: any) => Promise<void>;
  const insertRow = async (row: any) => Promise<any>;
  const updateRow = async (rowId: any, row: any) => Promise<any>;
  const deleteRow = async (rowId: any) => Promise<void>;

  return {
    data,
    paginationData,
    loadData,
    insertRow,
    updateRow,
    deleteRow,
  };
}
```

### SDK Classes

**1. Api Class (nocodb-sdk)**
Auto-generated from OpenAPI specification:

```typescript
class Api<SecurityDataType = unknown> {
  public constructor(config?: ApiConfig<SecurityDataType>);

  // Base operations
  public base = {
    list: (query?: any) => Promise<BaseListType>,
    read: (baseId: string) => Promise<BaseType>,
    update: (baseId: string, data: BaseReq) => Promise<BaseType>,
    delete: (baseId: string) => Promise<void>,
  };

  // Table operations
  public dbTable = {
    list: (baseId: string) => Promise<TableListType>,
    read: (tableId: string) => Promise<TableType>,
    create: (baseId: string, data: TableReq) => Promise<TableType>,
    update: (tableId: string, data: TableReq) => Promise<TableType>,
    delete: (tableId: string) => Promise<void>,
  };

  // Data operations
  public dbTableRow = {
    list: (tableId: string, query?: any) => Promise<any>,
    read: (tableId: string, rowId: string) => Promise<any>,
    create: (tableId: string, data: any) => Promise<any>,
    update: (tableId: string, rowId: string, data: any) => Promise<any>,
    delete: (tableId: string, rowId: string) => Promise<number>,

    // Nested operations
    nestedList: (tableId: string, rowId: string, columnId: string) => Promise<any>,
    nestedAdd: (tableId: string, rowId: string, columnId: string, refRowId: string) => Promise<void>,
    nestedRemove: (tableId: string, rowId: string, columnId: string, refRowId: string) => Promise<void>,
  };

  // View operations
  public dbView = {
    list: (tableId: string) => Promise<ViewListType>,
    read: (viewId: string) => Promise<ViewType>,
    create: (tableId: string, data: ViewReq) => Promise<ViewType>,
    update: (viewId: string, data: ViewReq) => Promise<ViewType>,
    delete: (viewId: string) => Promise<void>,
  };

  // Column operations
  public dbTableColumn = {
    list: (tableId: string) => Promise<ColumnListType>,
    read: (columnId: string) => Promise<ColumnType>,
    create: (tableId: string, data: ColumnReq) => Promise<ColumnType>,
    update: (columnId: string, data: ColumnReq) => Promise<ColumnType>,
    delete: (columnId: string) => Promise<void>,
  };
}
```

## Usage Examples with Code Snippets

### Example 1: Creating a Base (Project)

**Using REST API:**
```bash
curl -X POST http://localhost:8080/api/v1/db/meta/bases \
  -H "xc-auth: YOUR_AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Project",
    "type": "mysql",
    "config": {
      "client": "mysql2",
      "connection": {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "password",
        "database": "my_db"
      }
    }
  }'
```

**Using SDK:**
```typescript
import { Api } from 'nocodb-sdk';

const api = new Api({
  baseURL: 'http://localhost:8080',
  headers: {
    'xc-auth': 'YOUR_AUTH_TOKEN'
  }
});

const base = await api.base.create({
  title: 'My Project',
  type: 'mysql',
  config: {
    client: 'mysql2',
    connection: {
      host: 'localhost',
      port: 3306,
      user: 'root',
      password: 'password',
      database: 'my_db'
    }
  }
});
```

### Example 2: Creating a Table

**Using REST API:**
```bash
curl -X POST http://localhost:8080/api/v1/db/meta/bases/{baseId}/tables \
  -H "xc-auth: YOUR_AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Users",
    "table_name": "users",
    "columns": [
      {
        "column_name": "id",
        "title": "ID",
        "uidt": "ID",
        "pk": true,
        "ai": true
      },
      {
        "column_name": "name",
        "title": "Name",
        "uidt": "SingleLineText"
      },
      {
        "column_name": "email",
        "title": "Email",
        "uidt": "Email"
      }
    ]
  }'
```

**Using SDK:**
```typescript
const table = await api.base.tableCreate(baseId, {
  title: 'Users',
  table_name: 'users',
  columns: [
    {
      column_name: 'id',
      title: 'ID',
      uidt: UITypes.ID,
      pk: true,
      ai: true
    },
    {
      column_name: 'name',
      title: 'Name',
      uidt: UITypes.SingleLineText
    },
    {
      column_name: 'email',
      title: 'Email',
      uidt: UITypes.Email
    }
  ]
});
```

### Example 3: CRUD Operations on Data

**Create (Insert) Row:**
```typescript
// Using SDK
const newRow = await api.dbTableRow.create(tableId, {
  name: 'John Doe',
  email: 'john@example.com',
  age: 30
});

// Using REST API
// POST /api/v2/tables/{tableId}/records
```

**Read (List) Rows with Filtering:**
```typescript
// Using SDK
const rows = await api.dbTableRow.list(tableId, {
  where: '(name,like,%John%)',
  limit: 25,
  offset: 0,
  sort: '-created_at'
});

// Using REST API
// GET /api/v2/tables/{tableId}/records?where=(name,like,%25John%25)&limit=25&offset=0&sort=-created_at
```

**Update Row:**
```typescript
// Using SDK
const updated = await api.dbTableRow.update(tableId, rowId, {
  name: 'Jane Doe',
  email: 'jane@example.com'
});

// Using REST API
// PATCH /api/v2/tables/{tableId}/records/{rowId}
```

**Delete Row:**
```typescript
// Using SDK
await api.dbTableRow.delete(tableId, rowId);

// Using REST API
// DELETE /api/v2/tables/{tableId}/records/{rowId}
```

### Example 4: Working with Views

**Create a Grid View:**
```typescript
const gridView = await api.dbView.gridCreate(tableId, {
  title: 'Active Users',
  type: ViewTypes.GRID
});
```

**Create a Gallery View:**
```typescript
const galleryView = await api.dbView.galleryCreate(tableId, {
  title: 'User Gallery',
  type: ViewTypes.GALLERY,
  fk_cover_image_col_id: coverImageColumnId
});
```

**Create a Kanban View:**
```typescript
const kanbanView = await api.dbView.kanbanCreate(tableId, {
  title: 'Task Board',
  type: ViewTypes.KANBAN,
  fk_grp_col_id: statusColumnId
});
```

**Add Filters to View:**
```typescript
const filter = await api.dbTableFilter.create(viewId, {
  fk_column_id: columnId,
  comparison_op: 'eq',
  value: 'Active',
  logical_op: 'and'
});
```

**Add Sorts to View:**
```typescript
const sort = await api.dbTableSort.create(viewId, {
  fk_column_id: columnId,
  direction: 'desc'
});
```

### Example 5: Working with Linked Records

**List Linked Records:**
```typescript
const linkedRecords = await api.dbTableRow.nestedList(
  tableId,
  rowId,
  linkColumnId,
  {
    limit: 25,
    offset: 0
  }
);
```

**Link Records:**
```typescript
await api.dbTableRow.nestedAdd(
  tableId,
  rowId,
  linkColumnId,
  refRowId
);
```

**Unlink Records:**
```typescript
await api.dbTableRow.nestedRemove(
  tableId,
  rowId,
  linkColumnId,
  refRowId
);
```

### Example 6: Bulk Operations

**Bulk Insert:**
```typescript
// Using REST API
// POST /api/v2/tables/{tableId}/records/bulk
const result = await fetch(`/api/v2/tables/${tableId}/records/bulk`, {
  method: 'POST',
  headers: {
    'xc-auth': token,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify([
    { name: 'User 1', email: 'user1@example.com' },
    { name: 'User 2', email: 'user2@example.com' },
    { name: 'User 3', email: 'user3@example.com' }
  ])
});
```

**Bulk Update:**
```typescript
// POST /api/v2/tables/{tableId}/records/bulk/update
const result = await api.dbTableRow.bulkUpdate(tableId, [
  { id: 1, name: 'Updated Name 1' },
  { id: 2, name: 'Updated Name 2' }
]);
```

**Bulk Delete:**
```typescript
// POST /api/v2/tables/{tableId}/records/bulk/delete
await api.dbTableRow.bulkDelete(tableId, [
  { id: 1 },
  { id: 2 },
  { id: 3 }
]);
```

### Example 7: Aggregations and Grouping

**Get Aggregations:**
```typescript
// GET /api/v2/tables/{tableId}/aggregate
const aggregations = await fetch(
  `/api/v2/tables/${tableId}/aggregate?fields=count(*),sum(amount),avg(price)`,
  {
    headers: { 'xc-auth': token }
  }
);
```

**Group By Column:**
```typescript
// GET /api/v2/tables/{tableId}/bulk/group
const grouped = await api.dbTableRow.groupBy(tableId, {
  column_name: 'status',
  where: '(active,eq,true)'
});
```

### Example 8: Working with Forms

**Get Form View:**
```typescript
const formView = await api.dbView.formRead(formViewId);
```

**Submit Form (Public):**
```typescript
// POST /api/v1/db/public/shared-view/{sharedViewUuid}/rows
const submission = await fetch(
  `/api/v1/db/public/shared-view/${sharedViewUuid}/rows`,
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: 'John Doe',
      email: 'john@example.com',
      message: 'Hello from the form!'
    })
  }
);
```

## Integration Patterns and Workflows

### Pattern 1: Authentication Flow

**Token-Based Authentication:**
```typescript
// 1. Sign in to get token
const { token } = await fetch('/api/v1/auth/signin', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password'
  })
}).then(r => r.json());

// 2. Use token in subsequent requests
const api = new Api({
  baseURL: 'http://localhost:8080',
  headers: { 'xc-auth': token }
});
```

**OAuth Flow:**
```typescript
// 1. Redirect to OAuth provider
window.location.href = '/api/v1/auth/google';

// 2. Handle callback
// GET /api/v1/auth/google/callback?code=...
// NocoDB handles this automatically and redirects with token
```

### Pattern 2: Real-Time Collaboration

**WebSocket Connection:**
```typescript
import { io } from 'socket.io-client';

const socket = io('http://localhost:8080', {
  auth: { token: 'YOUR_AUTH_TOKEN' }
});

// Join a base/table room
socket.emit('join', { baseId, tableId });

// Listen for data changes
socket.on('dataChanged', (data) => {
  console.log('Data updated:', data);
  // Refresh your view
});

// Listen for schema changes
socket.on('schemaChanged', (data) => {
  console.log('Schema updated:', data);
  // Reload metadata
});
```

### Pattern 3: Plugin Integration

**Storage Plugin Example:**
```typescript
// In backend plugin (src/plugins/custom-storage/)
import { IStorageAdapterV2 } from '~/types/nc-plugin';

export default class CustomStoragePlugin implements IStorageAdapterV2 {
  async fileCreate(key: string, file: any): Promise<any> {
    // Upload file to your storage
    return uploadedFileUrl;
  }

  async fileRead(key: string): Promise<any> {
    // Read file from storage
    return fileStream;
  }

  async fileDelete(key: string): Promise<any> {
    // Delete file from storage
  }

  async test(): Promise<boolean> {
    // Test connection
    return true;
  }
}
```

### Pattern 4: Webhook Integration

**Configure Webhook:**
```typescript
const hook = await api.dbTableWebhook.create(tableId, {
  title: 'New User Webhook',
  event: 'after',
  operation: 'insert',
  notification: {
    type: 'URL',
    payload: {
      method: 'POST',
      url: 'https://api.example.com/webhook',
      headers: [{
        name: 'Content-Type',
        value: 'application/json'
      }],
      body: '{{ json data }}'
    }
  }
});
```

## Configuration Options and Extension Points

### Backend Configuration

**Environment Variables:**
```bash
# Database
NC_DB='pg://host:5432?u=user&p=pass&d=dbname'

# Authentication
NC_AUTH_JWT_SECRET='your-secret-key'

# Public URL
NC_PUBLIC_URL='https://your-domain.com'

# Redis (for caching and jobs)
NC_REDIS_URL='redis://localhost:6379'

# Storage
NC_S3_BUCKET_NAME='your-bucket'
NC_S3_REGION='us-east-1'
NC_S3_ACCESS_KEY='your-access-key'
NC_S3_ACCESS_SECRET='your-secret'

# Email
NC_SMTP_HOST='smtp.gmail.com'
NC_SMTP_PORT='587'
NC_SMTP_USERNAME='your-email@gmail.com'
NC_SMTP_PASSWORD='your-password'

# Features
NC_DISABLE_TELE='true'
NC_ADMIN_EMAIL='admin@example.com'
NC_ADMIN_PASSWORD='admin-password'
```

### Frontend Configuration

**nuxt.config.ts Options:**
```typescript
export default defineNuxtConfig({
  runtimeConfig: {
    public: {
      ncBackendUrl: process.env.NUXT_PUBLIC_NC_BACKEND_URL,
      ncCdnUrl: process.env.NC_CDN_URL,
    }
  }
});
```

### Extension Points

1. **Custom Cell Types**: Extend column types in `packages/nocodb-sdk/src/lib/UITypes.ts`
2. **Custom Plugins**: Add plugins to `packages/nocodb/src/plugins/`
3. **Custom Integrations**: Add to `packages/noco-integrations/packages/`
4. **Custom Views**: Extend view types in models
5. **Custom Webhooks**: Add notification channels to plugins
6. **Custom Authentication**: Add strategies to `src/strategies/`
7. **Custom API Endpoints**: Add controllers to `src/controllers/`
