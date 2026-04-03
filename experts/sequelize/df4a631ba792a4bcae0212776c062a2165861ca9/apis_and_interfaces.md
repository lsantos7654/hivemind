# Sequelize APIs and Interfaces

## Public APIs and Entry Points

### Primary Entry Points

**Main Sequelize Class**: The `Sequelize` class serves as the primary entry point and connection manager for the ORM. It coordinates database connections, model registration, and global configuration.

```javascript
import { Sequelize } from '@sequelize/core';

// Database connection with configuration
const sequelize = new Sequelize('database', 'username', 'password', {
  host: 'localhost',
  dialect: 'postgres',
  pool: {
    max: 5,
    min: 0,
    acquire: 30000,
    idle: 10000
  },
  logging: console.log
});
```

**Model Class**: The `Model` class provides the foundation for all database entities, offering both static methods for query operations and instance methods for record manipulation.

```javascript
import { Model, DataTypes } from '@sequelize/core';

class User extends Model {
  static associate() {
    // Define associations here
  }
}

User.init({
  firstName: DataTypes.STRING,
  lastName: DataTypes.STRING,
  email: DataTypes.STRING
}, {
  sequelize,
  modelName: 'User'
});
```

**DataTypes Namespace**: Comprehensive data type definitions for all supported SQL data types with database-specific optimizations.

```javascript
import { DataTypes } from '@sequelize/core';

// Available data types
DataTypes.STRING(255)      // VARCHAR with length
DataTypes.TEXT             // TEXT/LONGTEXT
DataTypes.INTEGER          // 32-bit integer
DataTypes.BIGINT          // 64-bit integer
DataTypes.FLOAT           // Floating point
DataTypes.DECIMAL(10, 2)  // Decimal with precision
DataTypes.DATE            // Date and time
DataTypes.BOOLEAN         // Boolean
DataTypes.JSON            // JSON data type
DataTypes.UUID            // UUID data type
DataTypes.ENUM('value1', 'value2') // Enumeration
```

## Key Classes, Functions, and Macros

### Core Classes

**Sequelize Class Methods**:

```javascript
// Connection and lifecycle management
await sequelize.authenticate();        // Test database connection
await sequelize.sync();                // Synchronize models with database
await sequelize.sync({ force: true }); // Drop and recreate tables
await sequelize.close();               // Close all connections

// Transaction management
const transaction = await sequelize.transaction();
await sequelize.transaction(async (t) => {
  // Transactional operations
});

// Query execution
const [results, metadata] = await sequelize.query(
  'SELECT * FROM users WHERE active = ?',
  { replacements: [true], type: QueryTypes.SELECT }
);

// Model definition and registration
const User = sequelize.define('User', {
  name: DataTypes.STRING
});
```

**Model Class Static Methods**:

```javascript
// CRUD Operations
const user = await User.create({ name: 'John Doe' });
const users = await User.findAll();
const user = await User.findByPk(1);
const user = await User.findOne({ where: { email: 'john@example.com' } });
await User.update({ active: false }, { where: { id: 1 } });
await User.destroy({ where: { active: false } });

// Complex queries
const users = await User.findAll({
  where: {
    age: { [Op.gte]: 18 },
    status: 'active'
  },
  include: ['Profile', 'Orders'],
  order: [['createdAt', 'DESC']],
  limit: 10,
  offset: 20
});

// Aggregation functions
const count = await User.count({ where: { active: true } });
const sum = await Order.sum('total', { where: { status: 'completed' } });
const max = await Product.max('price');
const min = await Product.min('price');
```

**Model Instance Methods**:

```javascript
// Instance operations
const user = await User.findByPk(1);
user.name = 'Jane Doe';
await user.save();                    // Save changes to database
await user.reload();                  // Refresh from database
await user.destroy();                 // Delete record
const userData = user.toJSON();       // Serialize to plain object

// Association methods (dynamically generated)
const posts = await user.getPosts();  // Get associated records
await user.addPost(post);             // Add association
await user.removePost(post);          // Remove association
await user.setPosts([post1, post2]);  // Replace associations
```

### Association Classes

**Association Types**:

```javascript
// One-to-One relationships
User.hasOne(Profile);
Profile.belongsTo(User);

// One-to-Many relationships
User.hasMany(Post);
Post.belongsTo(User);

// Many-to-Many relationships
User.belongsToMany(Role, { through: 'UserRoles' });
Role.belongsToMany(User, { through: 'UserRoles' });

// Self-referencing associations
Category.hasMany(Category, { as: 'SubCategories', foreignKey: 'parentId' });
Category.belongsTo(Category, { as: 'Parent', foreignKey: 'parentId' });
```

### Query Builder and Expression APIs

**Operators (Op)**:

```javascript
import { Op } from '@sequelize/core';

const users = await User.findAll({
  where: {
    age: { [Op.gte]: 18 },                    // age >= 18
    name: { [Op.like]: '%john%' },            // name LIKE '%john%'
    status: { [Op.in]: ['active', 'pending'] }, // status IN (...)
    [Op.or]: [
      { email: { [Op.endsWith]: '@gmail.com' } },
      { verified: true }
    ],
    [Op.and]: [
      { active: true },
      { createdAt: { [Op.gte]: new Date('2024-01-01') } }
    ]
  }
});
```

**SQL Expression Builders**:

```javascript
import { fn, col, literal, where } from '@sequelize/core';

// Function calls
const users = await User.findAll({
  attributes: [
    'id',
    [fn('UPPER', col('name')), 'upperName'],
    [fn('COUNT', col('posts.id')), 'postCount']
  ],
  include: ['Posts'],
  group: ['User.id']
});

// Raw SQL expressions
const users = await User.findAll({
  where: literal('age > 18 AND status = "active"')
});

// Column references
const users = await User.findAll({
  where: where(fn('LOWER', col('email')), 'john@example.com')
});
```

## Usage Examples with Code Snippets

### Basic Model Definition and Usage

```javascript
import { Sequelize, DataTypes, Model } from '@sequelize/core';

// Database connection
const sequelize = new Sequelize('postgres://user:pass@localhost:5432/mydb');

// Model definition
class User extends Model {
  static associate() {
    // Define associations after all models are loaded
    User.hasMany(Post);
    User.belongsTo(Department);
  }

  // Instance methods
  getFullName() {
    return `${this.firstName} ${this.lastName}`;
  }

  async getPosts() {
    return await this.getPosts({
      where: { published: true },
      order: [['createdAt', 'DESC']]
    });
  }
}

User.init({
  id: {
    type: DataTypes.UUID,
    defaultValue: DataTypes.UUIDV4,
    primaryKey: true
  },
  firstName: {
    type: DataTypes.STRING,
    allowNull: false,
    validate: {
      notEmpty: true,
      len: [2, 50]
    }
  },
  lastName: {
    type: DataTypes.STRING,
    allowNull: false
  },
  email: {
    type: DataTypes.STRING,
    allowNull: false,
    unique: true,
    validate: {
      isEmail: true
    }
  },
  age: {
    type: DataTypes.INTEGER,
    validate: {
      min: 0,
      max: 120
    }
  },
  status: {
    type: DataTypes.ENUM('active', 'inactive', 'pending'),
    defaultValue: 'pending'
  }
}, {
  sequelize,
  modelName: 'User',
  tableName: 'users',
  indexes: [
    { fields: ['email'] },
    { fields: ['lastName', 'firstName'] }
  ],
  hooks: {
    beforeCreate: (user) => {
      user.email = user.email.toLowerCase();
    }
  }
});
```

### Advanced Querying Patterns

```javascript
// Complex joins with eager loading
const users = await User.findAll({
  include: [
    {
      model: Post,
      as: 'Posts',
      include: [
        {
          model: Comment,
          include: [User]
        }
      ],
      where: { published: true }
    },
    {
      model: Department,
      attributes: ['name', 'code']
    }
  ],
  where: {
    active: true,
    createdAt: {
      [Op.gte]: new Date('2024-01-01')
    }
  },
  order: [
    ['createdAt', 'DESC'],
    ['Posts', 'publishedAt', 'DESC'],
    ['Posts', 'Comments', 'createdAt', 'ASC']
  ]
});

// Aggregation with grouping
const departmentStats = await User.findAll({
  attributes: [
    'departmentId',
    [fn('COUNT', col('id')), 'userCount'],
    [fn('AVG', col('age')), 'averageAge'],
    [fn('MAX', col('createdAt')), 'latestUser']
  ],
  include: [{
    model: Department,
    attributes: ['name']
  }],
  where: { active: true },
  group: ['departmentId', 'Department.id'],
  having: literal('COUNT(id) > 5'),
  order: [[fn('COUNT', col('id')), 'DESC']]
});

// Subqueries and raw SQL
const activeUsersWithRecentPosts = await User.findAll({
  where: {
    id: {
      [Op.in]: literal(`
        (SELECT DISTINCT user_id FROM posts
         WHERE created_at > NOW() - INTERVAL '30 days')
      `)
    },
    active: true
  }
});
```

### Transaction Management

```javascript
// Managed transactions (recommended)
try {
  await sequelize.transaction(async (t) => {
    // All operations within this callback are transactional
    const user = await User.create({
      firstName: 'John',
      lastName: 'Doe',
      email: 'john@example.com'
    }, { transaction: t });

    const profile = await Profile.create({
      userId: user.id,
      bio: 'Software developer'
    }, { transaction: t });

    // If any operation fails, the entire transaction is rolled back
    return { user, profile };
  });
} catch (error) {
  console.log('Transaction failed:', error);
}

// Unmanaged transactions (manual control)
const t = await sequelize.transaction();
try {
  const user = await User.create({
    firstName: 'Jane',
    lastName: 'Doe'
  }, { transaction: t });

  await Profile.create({
    userId: user.id,
    bio: 'Designer'
  }, { transaction: t });

  await t.commit();
} catch (error) {
  await t.rollback();
  throw error;
}

// Transaction with specific isolation level
await sequelize.transaction({
  isolationLevel: Transaction.ISOLATION_LEVELS.SERIALIZABLE
}, async (t) => {
  // Critical operations requiring highest isolation
});
```

## Integration Patterns and Workflows

### Application Integration Patterns

**Express.js Integration**:

```javascript
import express from 'express';
import { Sequelize } from '@sequelize/core';

const app = express();
const sequelize = new Sequelize(process.env.DATABASE_URL);

// Middleware for database connection
app.use(async (req, res, next) => {
  req.db = sequelize;
  next();
});

// Route with transaction
app.post('/users', async (req, res) => {
  try {
    const user = await sequelize.transaction(async (t) => {
      return await User.create(req.body, { transaction: t });
    });
    res.json(user);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  await sequelize.close();
  process.exit(0);
});
```

**Repository Pattern Implementation**:

```javascript
class UserRepository {
  constructor(sequelize) {
    this.User = sequelize.models.User;
    this.sequelize = sequelize;
  }

  async findById(id) {
    return await this.User.findByPk(id, {
      include: ['Profile', 'Department']
    });
  }

  async findByEmail(email) {
    return await this.User.findOne({
      where: { email: email.toLowerCase() }
    });
  }

  async createWithProfile(userData, profileData) {
    return await this.sequelize.transaction(async (t) => {
      const user = await this.User.create(userData, { transaction: t });
      const profile = await Profile.create({
        ...profileData,
        userId: user.id
      }, { transaction: t });

      return { user, profile };
    });
  }

  async updateStatus(id, status) {
    const [affectedCount] = await this.User.update(
      { status },
      { where: { id }, returning: true }
    );
    return affectedCount > 0;
  }
}
```

### Testing Patterns

```javascript
import { Sequelize } from '@sequelize/core';
import { describe, it, beforeEach, afterEach } from 'mocha';
import { expect } from 'chai';

describe('User Model', () => {
  let sequelize;

  beforeEach(async () => {
    sequelize = new Sequelize('sqlite::memory:');
    // Define models
    User.init(/* ... */, { sequelize });
    await sequelize.sync({ force: true });
  });

  afterEach(async () => {
    await sequelize.close();
  });

  it('should create a user successfully', async () => {
    const user = await User.create({
      firstName: 'John',
      lastName: 'Doe',
      email: 'john@example.com'
    });

    expect(user.id).to.exist;
    expect(user.firstName).to.equal('John');
    expect(user.getFullName()).to.equal('John Doe');
  });

  it('should validate email format', async () => {
    try {
      await User.create({
        firstName: 'John',
        lastName: 'Doe',
        email: 'invalid-email'
      });
      expect.fail('Should have thrown validation error');
    } catch (error) {
      expect(error.name).to.equal('SequelizeValidationError');
    }
  });
});
```

## Configuration Options and Extension Points

### Database Configuration

```javascript
const sequelize = new Sequelize('database', 'username', 'password', {
  host: 'localhost',
  port: 5432,
  dialect: 'postgres',

  // Connection pool configuration
  pool: {
    max: 20,              // Maximum connections
    min: 5,               // Minimum connections
    acquire: 30000,       // Maximum time to get connection
    idle: 10000,          // Maximum idle time
    evict: 1000,          // Check for idle connections interval
    handleDisconnects: true
  },

  // Logging configuration
  logging: (sql, timing) => {
    console.log(`[${timing}ms] ${sql}`);
  },
  benchmark: true,        // Include execution time in logs

  // Query configuration
  query: {
    nest: true,          // Nested object results
    raw: false           // Return model instances
  },

  // Timezone and locale
  timezone: '+00:00',
  dialectOptions: {
    dateStrings: true,
    typeCast: true,
    timezone: 'local'
  },

  // SSL configuration
  ssl: {
    require: true,
    rejectUnauthorized: false
  },

  // Read/write splitting
  replication: {
    read: [
      { host: 'read-replica-1.example.com' },
      { host: 'read-replica-2.example.com' }
    ],
    write: { host: 'master.example.com' }
  }
});
```

### Model Configuration and Hooks

```javascript
class User extends Model {
  static init(attributes, options) {
    return super.init(attributes, {
      ...options,

      // Table configuration
      tableName: 'users',
      underscored: true,    // Use snake_case for columns
      paranoid: true,       // Soft deletes
      timestamps: true,     // createdAt, updatedAt

      // Validation
      validate: {
        bothNamesOrNone() {
          if ((this.firstName || this.lastName) &&
              !(this.firstName && this.lastName)) {
            throw new Error('Either both names or none!');
          }
        }
      },

      // Hooks (lifecycle events)
      hooks: {
        beforeValidate: (user) => {
          if (user.email) {
            user.email = user.email.toLowerCase().trim();
          }
        },

        afterCreate: async (user) => {
          await EmailService.sendWelcomeEmail(user.email);
        },

        beforeDestroy: async (user) => {
          await user.cleanupRelatedData();
        }
      },

      // Indexes
      indexes: [
        { fields: ['email'], unique: true },
        { fields: ['firstName', 'lastName'] },
        { fields: ['createdAt'] },
        {
          fields: ['deletedAt'],
          where: { deletedAt: { [Op.not]: null } }
        }
      ],

      // Scopes (predefined queries)
      scopes: {
        active: { where: { status: 'active' } },
        recent: { where: { createdAt: { [Op.gte]: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) } } },
        withProfile: { include: ['Profile'] }
      }
    });
  }
}

// Usage of scopes
const activeUsers = await User.scope('active').findAll();
const recentActiveUsers = await User.scope(['active', 'recent']).findAll();
```

The Sequelize API is designed to be both powerful and intuitive, providing multiple levels of abstraction from simple CRUD operations to complex database interactions while maintaining consistency across different database systems and offering extensive customization options for enterprise requirements.
