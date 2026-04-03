# Sequelize APIs and Interfaces

## Public APIs and Entry Points

### Main Sequelize Class
The primary entry point is the `Sequelize` class located in `src/sequelize.js:35-1486`. This class provides database connection management, model definition, and configuration.

**Constructor Signatures:**
```javascript
// Basic database connection
new Sequelize(database, username, password, options)

// URI-based connection
new Sequelize('postgres://user:pass@example.com:5432/dbname', options)

// Options object only
new Sequelize({ database, username, password, dialect: 'postgres' })
```

**Key Methods:**
- `define(modelName, attributes, options)` - Define a new model representing a database table
- `model(modelName)` - Retrieve a previously defined model
- `isDefined(modelName)` - Check if a model exists
- `getDialect()` - Get the configured database dialect
- `getQueryInterface()` - Access the query interface for raw operations
- `authenticate()` - Test database connection
- `sync(options)` - Synchronize models with database schema
- `drop(options)` - Drop all tables
- `transaction(callback)` - Execute operations within a transaction

### Model Class API
The `Model` class (`src/model.js:53-4754`) is the base class for all database table representations.

**Static Methods (Class-level operations):**
```javascript
// Querying
Model.findAll(options)        // Find multiple records
Model.findOne(options)        // Find single record
Model.findByPk(id, options)   // Find by primary key
Model.findAndCountAll(options) // Find with count
Model.count(options)          // Count records
Model.sum(field, options)     // Sum numeric field
Model.min(field, options)     // Minimum value
Model.max(field, options)     // Maximum value

// Modification
Model.create(values, options)     // Create new record
Model.bulkCreate(records, options) // Create multiple records
Model.update(values, options)     // Update existing records
Model.destroy(options)            // Delete records
Model.restore(options)            // Restore soft-deleted records (paranoid)
Model.upsert(values, options)     // Insert or update

// Schema operations
Model.init(attributes, options)   // Initialize model definition
Model.sync(options)              // Synchronize table schema
Model.drop(options)              // Drop table

// Association definition
Model.hasOne(target, options)        // One-to-one relationship
Model.hasMany(target, options)       // One-to-many relationship
Model.belongsTo(target, options)     // Many-to-one relationship
Model.belongsToMany(target, options) // Many-to-many relationship
```

**Instance Methods (Record-level operations):**
```javascript
// Data access
instance.get(key)              // Get attribute value
instance.set(key, value)       // Set attribute value
instance.getDataValue(key)     // Get raw data value
instance.setDataValue(key, val) // Set raw data value
instance.changed(key)          // Check if attribute changed
instance.previous(key)         // Get previous value

// Persistence
instance.save(options)         // Save changes to database
instance.reload(options)       // Refresh from database
instance.destroy(options)      // Delete record
instance.restore(options)      // Restore soft-deleted record

// Validation
instance.validate(options)     // Validate instance data
```

## Key Classes, Functions, and Macros

### Data Types (`src/data-types.js`)
Sequelize provides a comprehensive type system for database columns:

**String Types:**
```javascript
DataTypes.STRING(length)       // VARCHAR with optional length
DataTypes.STRING.BINARY        // Binary string
DataTypes.TEXT                 // Long text field
DataTypes.TEXT('tiny')         // Tiny text (MySQL)
DataTypes.TEXT('medium')       // Medium text (MySQL)
DataTypes.TEXT('long')         // Long text (MySQL)
DataTypes.CHAR(length)         // Fixed-length string
DataTypes.CITEXT               // Case-insensitive text (PostgreSQL)
```

**Numeric Types:**
```javascript
DataTypes.INTEGER              // 32-bit integer
DataTypes.BIGINT               // 64-bit integer
DataTypes.FLOAT                // Single precision floating point
DataTypes.DOUBLE               // Double precision floating point
DataTypes.REAL                 // Real number
DataTypes.DECIMAL(precision, scale) // Fixed-point decimal
DataTypes.SMALLINT             // 16-bit integer
DataTypes.TINYINT              // 8-bit integer (MySQL)
DataTypes.MEDIUMINT            // 24-bit integer (MySQL)
```

**Date/Time Types:**
```javascript
DataTypes.DATE                 // Datetime with timezone
DataTypes.DATE(precision)      // With fractional seconds
DataTypes.DATEONLY            // Date without time
DataTypes.TIME                // Time only
DataTypes.NOW                 // Current timestamp default
```

**Other Types:**
```javascript
DataTypes.BOOLEAN             // Boolean value
DataTypes.UUID                // UUID string
DataTypes.UUIDV1             // UUID version 1
DataTypes.UUIDV4             // UUID version 4
DataTypes.JSON               // JSON data (PostgreSQL, MySQL 5.7+)
DataTypes.JSONB              // Binary JSON (PostgreSQL)
DataTypes.BLOB               // Binary data
DataTypes.ENUM('value1', 'value2') // Enumeration
DataTypes.ARRAY(DataTypes.STRING)  // Array type (PostgreSQL)
DataTypes.RANGE(DataTypes.INTEGER) // Range type (PostgreSQL)
DataTypes.GEOMETRY           // Spatial geometry
DataTypes.GEOGRAPHY          // Geographic coordinate
```

### Query Operators (`src/operators.ts`)
Sequelize provides symbolic operators for complex queries:

```javascript
const { Op } = require('sequelize');

// Logical operators
[Op.and]: [condition1, condition2]    // AND
[Op.or]: [condition1, condition2]     // OR
[Op.not]: condition                   // NOT

// Comparison operators
[Op.eq]: value                        // = value
[Op.ne]: value                        // != value
[Op.gt]: value                        // > value
[Op.gte]: value                       // >= value
[Op.lt]: value                        // < value
[Op.lte]: value                       // <= value
[Op.between]: [min, max]              // BETWEEN min AND max
[Op.notBetween]: [min, max]           // NOT BETWEEN
[Op.in]: [val1, val2]                 // IN (val1, val2)
[Op.notIn]: [val1, val2]              // NOT IN (val1, val2)

// String operators
[Op.like]: 'pattern%'                 // LIKE pattern
[Op.notLike]: 'pattern%'              // NOT LIKE pattern
[Op.iLike]: 'pattern%'                // ILIKE (PostgreSQL)
[Op.notILike]: 'pattern%'             // NOT ILIKE (PostgreSQL)
[Op.regexp]: '^pattern'               // REGEXP (MySQL/PostgreSQL)
[Op.notRegexp]: '^pattern'            // NOT REGEXP
[Op.iRegexp]: '^pattern'              // Case-insensitive REGEXP (PostgreSQL)

// Array operators (PostgreSQL)
[Op.contains]: [1, 2]                 // Array contains values
[Op.contained]: [1, 2]                // Array contained by values
[Op.overlap]: [1, 2]                  // Arrays overlap
[Op.adjacent]: [1, 2]                 // Arrays are adjacent

// JSON operators (PostgreSQL)
[Op.extract]: { path: '$.key' }       // Extract JSON path
```

### Association Classes
Each association type is implemented as a separate class:

**BelongsTo** (`src/associations/belongs-to.js`):
```javascript
// Many-to-one relationship
User.belongsTo(Company, { foreignKey: 'companyId', as: 'employer' });
// Adds: user.getEmployer(), user.setEmployer(), user.createEmployer()
```

**HasOne** (`src/associations/has-one.js`):
```javascript
// One-to-one relationship
User.hasOne(Profile, { foreignKey: 'userId', as: 'profile' });
// Adds: user.getProfile(), user.setProfile(), user.createProfile()
```

**HasMany** (`src/associations/has-many.js`):
```javascript
// One-to-many relationship
User.hasMany(Post, { foreignKey: 'authorId', as: 'posts' });
// Adds: user.getPosts(), user.setPosts(), user.addPost(), user.removePost()
```

**BelongsToMany** (`src/associations/belongs-to-many.js`):
```javascript
// Many-to-many relationship with junction table
User.belongsToMany(Role, { through: 'UserRoles', as: 'roles' });
// Adds: user.getRoles(), user.setRoles(), user.addRole(), user.removeRole()
```

## Usage Examples with Code Snippets

### Basic Model Definition and Operations

```javascript
const { Sequelize, DataTypes } = require('sequelize');

// Initialize Sequelize
const sequelize = new Sequelize('database', 'username', 'password', {
  host: 'localhost',
  dialect: 'postgres',
  logging: console.log,
  pool: {
    max: 5,
    min: 0,
    acquire: 30000,
    idle: 10000
  }
});

// Define a User model
const User = sequelize.define('User', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true
  },
  firstName: {
    type: DataTypes.STRING(50),
    allowNull: false,
    validate: {
      notEmpty: true,
      len: [2, 50]
    }
  },
  lastName: {
    type: DataTypes.STRING(50),
    allowNull: false
  },
  email: {
    type: DataTypes.STRING(100),
    unique: true,
    allowNull: false,
    validate: {
      isEmail: true
    }
  },
  birthDate: {
    type: DataTypes.DATEONLY
  },
  isActive: {
    type: DataTypes.BOOLEAN,
    defaultValue: true
  },
  metadata: {
    type: DataTypes.JSONB  // PostgreSQL JSON
  }
}, {
  timestamps: true,        // Adds createdAt, updatedAt
  paranoid: true,          // Soft deletes with deletedAt
  underscored: true,       // Use snake_case column names
  indexes: [
    {
      unique: true,
      fields: ['email']
    },
    {
      fields: ['lastName', 'firstName']
    }
  ]
});

// Model lifecycle hooks
User.addHook('beforeCreate', async (user, options) => {
  // Hash password, generate UUID, etc.
  user.email = user.email.toLowerCase();
});

User.addHook('afterCreate', async (user, options) => {
  // Send welcome email, log creation, etc.
  console.log(`User ${user.email} created`);
});
```

### Advanced Querying Examples

```javascript
// Basic queries
const users = await User.findAll({
  where: {
    isActive: true,
    [Op.or]: [
      { firstName: 'John' },
      { lastName: { [Op.like]: 'Smith%' } }
    ]
  },
  order: [['createdAt', 'DESC']],
  limit: 10,
  offset: 20
});

// Complex queries with associations
const usersWithPosts = await User.findAll({
  include: [{
    model: Post,
    as: 'posts',
    where: {
      publishedAt: { [Op.not]: null }
    },
    required: false  // LEFT JOIN vs INNER JOIN
  }],
  where: {
    createdAt: {
      [Op.gte]: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) // Last 30 days
    }
  }
});

// Aggregation queries
const stats = await User.findAll({
  attributes: [
    'isActive',
    [sequelize.fn('COUNT', sequelize.col('id')), 'userCount'],
    [sequelize.fn('AVG', sequelize.col('age')), 'averageAge']
  ],
  group: ['isActive'],
  having: {
    [sequelize.fn('COUNT', sequelize.col('id'))]: {
      [Op.gt]: 10
    }
  }
});

// Raw queries when ORM is insufficient
const results = await sequelize.query(
  'SELECT u.*, COUNT(p.id) as post_count FROM users u LEFT JOIN posts p ON u.id = p.author_id WHERE u.created_at > :since GROUP BY u.id',
  {
    replacements: { since: new Date('2023-01-01') },
    type: QueryTypes.SELECT,
    model: User,
    mapToModel: true
  }
);
```

### Transaction Management

```javascript
// Managed transaction (recommended)
await sequelize.transaction(async (t) => {
  const user = await User.create({
    firstName: 'John',
    lastName: 'Doe',
    email: 'john@example.com'
  }, { transaction: t });

  await Profile.create({
    userId: user.id,
    bio: 'Software developer'
  }, { transaction: t });

  // Transaction auto-commits on success, auto-rolls back on error
});

// Unmanaged transaction (manual control)
const t = await sequelize.transaction();
try {
  const user = await User.create(userData, { transaction: t });
  await Profile.create(profileData, { transaction: t });
  await t.commit();
} catch (error) {
  await t.rollback();
  throw error;
}

// Isolation levels
await sequelize.transaction({
  isolationLevel: Transaction.ISOLATION_LEVELS.SERIALIZABLE
}, async (t) => {
  // Critical operations requiring serializable isolation
});
```

## Integration Patterns and Workflows

### Model Relationships and Eager Loading

```javascript
// Define relationships
User.hasMany(Post, { foreignKey: 'authorId', as: 'posts' });
User.hasOne(Profile, { foreignKey: 'userId', as: 'profile' });
Post.belongsTo(User, { foreignKey: 'authorId', as: 'author' });
Post.belongsToMany(Tag, { through: 'PostTags', as: 'tags' });

// Eager loading patterns
const userWithData = await User.findByPk(1, {
  include: [
    {
      model: Post,
      as: 'posts',
      include: [
        { model: Tag, as: 'tags' }
      ]
    },
    { model: Profile, as: 'profile' }
  ]
});

// Lazy loading (N+1 queries - avoid in production)
const users = await User.findAll();
for (const user of users) {
  const posts = await user.getPosts(); // Separate query per user
}

// Optimal: Include with pagination
const usersWithPosts = await User.findAll({
  include: [{
    model: Post,
    as: 'posts',
    separate: true,    // Separate query to avoid JOIN issues
    limit: 5,          // Limit posts per user
    order: [['createdAt', 'DESC']]
  }]
});
```

### Validation and Error Handling

```javascript
// Model-level validation
const User = sequelize.define('User', {
  email: {
    type: DataTypes.STRING,
    validate: {
      isEmail: {
        msg: 'Must be a valid email address'
      },
      async isUnique(value) {
        const existing = await User.findOne({ where: { email: value } });
        if (existing) {
          throw new Error('Email already exists');
        }
      }
    }
  },
  age: {
    type: DataTypes.INTEGER,
    validate: {
      min: {
        args: [18],
        msg: 'Must be at least 18 years old'
      },
      max: 120
    }
  }
});

// Custom validation functions
User.addHook('beforeValidate', (user, options) => {
  if (user.birthDate) {
    const age = new Date().getFullYear() - user.birthDate.getFullYear();
    user.age = age;
  }
});

// Error handling
try {
  const user = await User.create(invalidData);
} catch (error) {
  if (error instanceof ValidationError) {
    console.log('Validation errors:', error.errors);
    error.errors.forEach(err => {
      console.log(`${err.path}: ${err.message}`);
    });
  } else if (error instanceof UniqueConstraintError) {
    console.log('Unique constraint violation:', error.parent.constraint);
  } else if (error instanceof DatabaseError) {
    console.log('Database error:', error.parent.code);
  }
}
```

## Configuration Options and Extension Points

### Sequelize Configuration Options

```javascript
const sequelize = new Sequelize(connectionString, {
  // Connection options
  host: 'localhost',
  port: 5432,
  username: 'user',
  password: 'pass',
  database: 'mydb',
  dialect: 'postgres',

  // Connection pooling
  pool: {
    max: 20,          // Maximum connections
    min: 0,           // Minimum connections
    acquire: 60000,   // Maximum time to get connection (ms)
    idle: 1000,       // Time before releasing idle connection (ms)
    evict: 1000,      // Time between eviction runs (ms)
    handleDisconnects: true
  },

  // Logging
  logging: console.log,              // Function or false
  benchmark: true,                   // Log query execution time

  // Timezone handling
  timezone: '+00:00',                // UTC
  dialectOptions: {
    useUTC: false,
    dateStrings: true,
    typeCast: true,
    timezone: 'local'
  },

  // Query options
  define: {
    timestamps: true,                // Add createdAt, updatedAt
    paranoid: false,                 // Soft deletes with deletedAt
    underscored: false,             // Use camelCase vs snake_case
    freezeTableName: false,         // Use model name as table name
    charset: 'utf8',
    collate: 'utf8_general_ci',
    classMethods: {},               // Deprecated
    instanceMethods: {},            // Deprecated
    tableName: 'my_table',         // Override table name
    getterMethods: {},             // Virtual getters
    setterMethods: {},             // Virtual setters
    defaultScope: {},              // Default query scope
    scopes: {}                     // Named query scopes
  },

  // Synchronization
  sync: { force: false, alter: false },

  // Hooks
  hooks: {
    beforeConnect: (config) => {},
    afterConnect: (connection, config) => {},
    beforeDisconnect: (connection) => {},
    afterDisconnect: (connection) => {}
  },

  // Replication (read/write splitting)
  replication: {
    read: [
      { host: 'read1.example.com', username: 'read-user', password: 'pass' },
      { host: 'read2.example.com', username: 'read-user', password: 'pass' }
    ],
    write: { host: 'write.example.com', username: 'write-user', password: 'pass' }
  },

  // Retry configuration
  retry: {
    match: [/Deadlock/i, /SequelizeConnectionError/],
    max: 3,
    backoffBase: 1000,
    backoffExponent: 1.5
  }
});
```

### Model Extension Points

```javascript
// Scopes for reusable query logic
const User = sequelize.define('User', attributes, {
  defaultScope: {
    where: { isActive: true }
  },
  scopes: {
    active: { where: { isActive: true } },
    recent: { where: { createdAt: { [Op.gte]: new Date(Date.now() - 7*24*60*60*1000) } } },
    withPosts: {
      include: [{ model: Post, as: 'posts' }]
    },
    byRole: (role) => ({
      where: { role: role }
    })
  }
});

// Usage: User.scope('active', 'recent').findAll()
// Usage: User.scope({ method: ['byRole', 'admin'] }).findAll()

// Virtual attributes
const User = sequelize.define('User', {
  firstName: DataTypes.STRING,
  lastName: DataTypes.STRING,
  fullName: {
    type: DataTypes.VIRTUAL,
    get() {
      return `${this.firstName} ${this.lastName}`;
    },
    set(value) {
      const names = value.split(' ');
      this.setDataValue('firstName', names[0]);
      this.setDataValue('lastName', names.slice(1).join(' '));
    }
  }
});

// Instance methods
User.prototype.getFullName = function() {
  return `${this.firstName} ${this.lastName}`;
};

// Class methods
User.findByEmail = function(email) {
  return this.findOne({ where: { email: email.toLowerCase() } });
};

// Hook system for lifecycle events
User.addHook('beforeValidate', 'hashPassword', (user, options) => {
  if (user.changed('password')) {
    user.password = hashPassword(user.password);
  }
});

User.addHook('afterCreate', async (user, options) => {
  await EmailService.sendWelcomeEmail(user.email);
});
```

This comprehensive API documentation covers the core functionality developers need to build robust database-driven applications with Sequelize, from basic CRUD operations to advanced features like transactions, associations, and custom extensions.
