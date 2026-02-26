# Formily APIs and Interfaces

## Public APIs and Entry Points

Formily exposes a layered API surface organized by package. Each package provides focused functionality with clear boundaries, allowing developers to consume only what they need.

### Core Package API (@formily/core)

**Primary Entry Point**: `packages/core/src/shared/externals.ts`

**Main Factory Function**:
```typescript
import { createForm } from '@formily/core'

// Create a form instance with optional configuration
const form = createForm({
  initialValues: { username: '', email: '' },
  effects: () => {
    onFormInit(() => {
      console.log('Form initialized')
    })
  },
  validateFirst: true,
  readPretty: false
})
```

**Form Instance Properties and Methods**:
```typescript
// State properties (reactive)
form.values          // Current form values
form.initialValues   // Initial values for reset
form.modified        // Whether form has been modified
form.valid           // Whether form passes validation
form.invalid         // Inverse of valid
form.errors          // Array of validation errors
form.warnings        // Array of validation warnings
form.validating      // Whether validation is in progress
form.submitting      // Whether form is submitting
form.loading         // Whether form is in loading state

// Form patterns
form.pattern         // 'editable' | 'disabled' | 'readOnly' | 'readPretty'
form.display         // 'visible' | 'hidden' | 'none'

// Field management
form.fields          // Record of all registered fields
form.createField()   // Create a new field
form.createArrayField()   // Create array field
form.createObjectField()  // Create object field
form.createVoidField()    // Create void (layout) field

// State operations
form.setValues()     // Set form values
form.setInitialValues()   // Set initial values
form.setValuesIn()   // Set value at path
form.getValuesIn()   // Get value at path
form.reset()         // Reset to initial values
form.submit()        // Submit form with validation
form.validate()      // Validate all fields
form.clearErrors()   // Clear validation errors

// Field queries
form.query()         // Query fields by path pattern
form.query('username').get()  // Get field by exact path
form.query('*.email').take()  // Get first matching field
form.query('items.*.name').map() // Map over matching fields

// Lifecycle
form.addEffects()    // Add effect functions dynamically
form.removeEffects() // Remove effect functions
form.onMount()       // Called when form mounts
form.onUnmount()     // Called when form unmounts
```

**Field Creation APIs**:
```typescript
// Create a standard input field
const field = form.createField({
  name: 'username',
  title: 'Username',
  required: true,
  validator: [
    { required: true, message: 'Required' },
    { min: 3, message: 'Min 3 characters' }
  ],
  reactions: (field) => {
    // React to other field changes
    field.visible = form.values.showUsername
  }
})

// Create an array field for lists
const arrayField = form.createArrayField({
  name: 'items',
  initialValue: [],
})

// Array field operations
arrayField.push({ name: '', value: '' })
arrayField.pop()
arrayField.insert(1, { name: 'new' })
arrayField.remove(0)
arrayField.move(0, 2)
arrayField.moveUp(1)
arrayField.moveDown(1)
```

**Effect System API**:
```typescript
import {
  createEffectHook,
  onFormInit,
  onFormMount,
  onFormValuesChange,
  onFieldChange,
  onFieldValueChange,
  onFieldInputValueChange
} from '@formily/core'

// Form-level effects
const form = createForm({
  effects: () => {
    // Runs once when form initializes
    onFormInit(() => {
      console.log('Form ready')
    })

    // Runs when form mounts to DOM
    onFormMount(() => {
      form.setFieldState('username', state => {
        state.loading = false
      })
    })

    // Observe value changes
    onFormValuesChange((form) => {
      console.log('Values changed:', form.values)
    })

    // Field-specific effects
    onFieldValueChange('country', (field) => {
      // Reset city when country changes
      form.setFieldState('city', state => {
        state.value = undefined
        state.dataSource = getCitiesForCountry(field.value)
      })
    })
  }
})

// Create custom effect hooks
const onCustomEvent = createEffectHook('onCustomEvent')

// Use in effects
onCustomEvent(() => {
  // Handle custom event
})

// Trigger from code
form.notify('onCustomEvent', payload)
```

**Type Checking Utilities**:
```typescript
import {
  isForm,
  isField,
  isArrayField,
  isObjectField,
  isVoidField
} from '@formily/core'

if (isArrayField(field)) {
  // TypeScript knows field has push, pop, etc.
  field.push(newItem)
}
```

### Reactive Package API (@formily/reactive)

**Observable Creation**:
```typescript
import { observable, autorun, reaction, batch } from '@formily/reactive'

// Create observable object
const state = observable({
  count: 0,
  user: { name: 'John' }
})

// Deep observable by default
state.count = 1        // Triggers reactions
state.user.name = 'Jane'  // Also triggers reactions

// Observable with annotations
const model = observable({
  count: 0,           // Deep observable
  ref: observable.ref({}),      // Reference (not proxied)
  shallow: observable.shallow([]),  // Shallow observable
  computed: observable.computed(() => state.count * 2)
})

// Access computed value
console.log(model.computed.value)  // Auto-updates when dependencies change
```

**Reaction APIs**:
```typescript
import { autorun, reaction, observe } from '@formily/reactive'

// Autorun: runs immediately and on any dependency change
const dispose = autorun(() => {
  console.log('Count:', state.count)
})

// Later: stop tracking
dispose()

// Reaction: runs only when tracked value changes
reaction(
  () => state.user.name,  // Tracker function
  (name, oldName) => {    // Effect function
    console.log(`Name changed from ${oldName} to ${name}`)
  }
)

// Observe: low-level change observation
observe(state, (change) => {
  console.log('Change:', change.type, change.key, change.value)
})
```

**Batch Updates**:
```typescript
import { batch } from '@formily/reactive'

// Multiple updates trigger reactions only once
batch(() => {
  state.count = 1
  state.count = 2
  state.count = 3
})
// Reactions run once with count = 3
```

**Model Decorator**:
```typescript
import { observable, action } from '@formily/reactive'

class Store {
  count = 0

  constructor() {
    observable(this)  // Make instance observable
  }

  // Action wrapper for batched mutations
  increment = action(() => {
    this.count++
    this.otherValue++
  })
}
```

### React Package API (@formily/react)

**Core Components**:
```typescript
import {
  FormProvider,
  Field,
  ArrayField,
  ObjectField,
  VoidField,
  createSchemaField
} from '@formily/react'

// Provide form context
<FormProvider form={form}>
  <Field
    name="username"
    title="Username"
    required
    decorator={[FormItem]}
    component={[Input, { placeholder: 'Enter username' }]}
  />

  <ArrayField name="items">
    {(field) => (
      field.value?.map((item, index) => (
        <Field key={index} name={index} />
      ))
    )}
  </ArrayField>
</FormProvider>
```

**Schema Field API**:
```typescript
import { createSchemaField } from '@formily/react'
import { Input, Select, FormItem } from '@formily/antd'

// Create SchemaField with component mapping
const SchemaField = createSchemaField({
  components: {
    Input,
    Select,
    FormItem
  },
  scope: {
    // Global expression scope
    customFunction: () => {}
  }
})

// Use with JSON Schema
<SchemaField>
  <SchemaField.String
    name="username"
    title="Username"
    required
    x-decorator="FormItem"
    x-component="Input"
  />

  <SchemaField.Array name="tags">
    <SchemaField.String x-component="Input" />
  </SchemaField.Array>
</SchemaField>

// Or with schema object
<SchemaField schema={{
  type: 'object',
  properties: {
    username: {
      type: 'string',
      title: 'Username',
      required: true,
      'x-decorator': 'FormItem',
      'x-component': 'Input'
    }
  }
}} />
```

**React Hooks**:
```typescript
import {
  useForm,
  useField,
  useFieldSchema,
  useFormEffects
} from '@formily/react'

function MyComponent() {
  // Access form instance
  const form = useForm()

  // Access current field
  const field = useField()

  // Access field schema
  const schema = useFieldSchema()

  // Register effects
  useFormEffects(() => {
    onFieldValueChange('country', () => {
      // React to changes
    })
  })

  return <div>{field.title}</div>
}
```

**Connection API** (for custom components):
```typescript
import { connect, mapProps, mapReadPretty } from '@formily/react'

// Connect component to field
const Input = connect(
  AntdInput,  // Base component
  mapProps({  // Map field props to component props
    value: 'value',
    readOnly: 'disabled'
  }),
  mapReadPretty(PreviewText)  // Component for read-pretty mode
)

// Custom connector
const MyInput = connect(
  BaseInput,
  (props, field) => {
    return {
      ...props,
      disabled: field.disabled || field.readOnly,
      value: field.value ?? '',
      onChange: (e) => field.setValue(e.target.value)
    }
  }
)
```

### JSON Schema Package API (@formily/json-schema)

**Schema Class**:
```typescript
import { Schema } from '@formily/json-schema'

// Create schema instance
const schema = new Schema({
  type: 'object',
  properties: {
    username: {
      type: 'string',
      title: 'Username',
      required: true,
      'x-component': 'Input'
    },
    age: {
      type: 'number',
      'x-component': 'NumberPicker',
      minimum: 0,
      maximum: 120
    }
  }
})

// Schema navigation
schema.properties.username  // Access nested schema
schema.items               // For array schemas
schema.parent              // Parent schema
schema.root                // Root schema

// Schema transformation
const fieldProps = schema.toFieldProps()

// Expression compilation
schema['x-visible'] = '{{$form.values.showAdvanced}}'
// Expression evaluates to boolean at runtime
```

**Schema Markup Components** (JSX alternative):
```typescript
import { SchemaField } from '@formily/react'

const SchemaField = createSchemaField({
  components: { Input, Select }
})

// JSX schema definition
<SchemaField>
  <SchemaField.String
    name="username"
    title="Username"
    x-component="Input"
  />
  <SchemaField.Number
    name="age"
    title="Age"
    x-component="NumberPicker"
  />
  <SchemaField.Object name="address">
    <SchemaField.String name="street" />
    <SchemaField.String name="city" />
  </SchemaField.Object>
</SchemaField>
```

**Schema Expressions**:
Expressions in schema properties are evaluated with context:
```typescript
{
  type: 'string',
  'x-visible': '{{$form.values.country === "US"}}',  // Visibility condition
  'x-disabled': '{{$form.readOnly}}',                 // Disabled state
  'x-validator': '{{(value) => value.length > 3}}',   // Custom validator
  'x-reactions': [{                                    // Field reactions
    dependencies: ['country'],
    fulfill: {
      state: {
        dataSource: '{{fetchCities($deps[0])}}'
      }
    }
  }]
}
```

### Validator Package API (@formily/validator)

**Validation Function**:
```typescript
import {
  validate,
  registerValidateRules,
  registerValidateFormats,
  setValidateLanguage
} from '@formily/validator'

// Validate a value
const results = await validate('test@email', {
  required: true,
  format: 'email',
  max: 50
})

// results = { error: [], success: ['email'], warning: [] }

// Built-in validators
const validators = {
  required: true,
  max: 100,
  min: 10,
  maxLength: 255,
  minLength: 3,
  pattern: /^[A-Z]/,
  format: 'email',  // 'url', 'date', 'datetime', etc.
  validator: (value) => {
    return value !== 'forbidden'
  }
}

// Custom validator function
const customValidator = (value, rule, context) => {
  if (value === context.parent.username) {
    return {
      type: 'error',
      message: 'Cannot be same as username'
    }
  }
}
```

**Register Custom Rules**:
```typescript
import { registerValidateRules } from '@formily/validator'

registerValidateRules({
  phoneNumber: (value) => {
    const regex = /^\d{3}-\d{3}-\d{4}$/
    return regex.test(value) || 'Invalid phone number'
  }
})

// Use in field
form.createField({
  name: 'phone',
  validator: [{ phoneNumber: true }]
})
```

**Internationalization**:
```typescript
import {
  setValidateLanguage,
  registerValidateLocale
} from '@formily/validator'

// Set language
setValidateLanguage('zh-CN')

// Register custom messages
registerValidateLocale({
  'en-US': {
    required: 'This field is required',
    min: 'Value must be at least {{min}}'
  },
  'zh-CN': {
    required: '该字段是必填项',
    min: '值必须至少为 {{min}}'
  }
})
```

### Path Package API (@formily/path)

**FormPath Class**:
```typescript
import { FormPath } from '@formily/shared'

// Create path from string
const path = FormPath.parse('user.address.street')

// Path operations
path.toString()        // 'user.address.street'
path.toArray()         // ['user', 'address', 'street']
path.parent()          // Path to 'user.address'
path.concat('number')  // 'user.address.street.number'

// Path matching
FormPath.parse('items.*.name').match('items.0.name')  // true
FormPath.parse('*.email').match('user.email')         // true

// Value operations on objects
const data = { user: { name: 'John', age: 30 } }

FormPath.getIn(data, 'user.name')           // 'John'
FormPath.setIn(data, 'user.age', 31)        // Mutates data
FormPath.deleteIn(data, 'user.age')         // Remove property
FormPath.existIn(data, 'user.name')         // true

// Destructuring paths
FormPath.parse('user.{name,email}')  // Extracts multiple properties
```

## Key Classes, Functions, and Macros

### Form Class (packages/core/src/models/Form.ts)

The central class managing form state and lifecycle:

```typescript
class Form<ValueType extends object = any> {
  // State properties
  id: string
  values: ValueType
  initialValues: ValueType
  modified: boolean
  valid: boolean
  validating: boolean
  submitting: boolean
  pattern: FormPatternTypes      // editable | disabled | readOnly | readPretty
  display: FormDisplayTypes      // visible | hidden | none

  // Field registry
  fields: Record<string, GeneralField>

  // Core methods
  setValues(values: Partial<ValueType>): void
  setInitialValues(values: Partial<ValueType>): void
  reset(pattern?: '*' | FormPathPattern): Promise<void>
  submit(onSubmit?: (values: ValueType) => any): Promise<any>
  validate(pattern?: FormPathPattern): Promise<void>

  // Field factory methods
  createField<Decorator, Component>(props: IFieldFactoryProps<Decorator, Component>): Field
  createArrayField<Decorator, Component>(props: IFieldFactoryProps<Decorator, Component>): ArrayField
  createObjectField<Decorator, Component>(props: IFieldFactoryProps<Decorator, Component>): ObjectField
  createVoidField<Decorator, Component>(props: IVoidFieldFactoryProps<Decorator, Component>): VoidField

  // Query API
  query(pattern: FormPathPattern): Query

  // Effect system
  addEffects(id: string, effects: () => void): void
  removeEffects(id: string): void

  // Lifecycle callbacks
  onInit(callback: () => void): () => void
  onMount(callback: () => void): () => void
  onUnmount(callback: () => void): () => void
}
```

### Field Classes

**Field** (standard input field):
```typescript
class Field {
  name: string
  title: string
  description: string
  value: any
  initialValue: any
  inputValue: any      // Raw input before transformation
  modified: boolean
  active: boolean      // Has focus
  visited: boolean     // Has been focused
  touched: boolean     // Has been blurred after focus

  valid: boolean
  invalid: boolean
  errors: string[]
  warnings: string[]
  validating: boolean

  pattern: FieldPatternTypes
  display: FieldDisplayTypes
  disabled: boolean
  readOnly: boolean
  readPretty: boolean
  visible: boolean
  hidden: boolean

  required: boolean
  validator: Validator[]
  dataSource: any[]    // For select/cascader components

  // State setters
  setValue(value: any): void
  setInitialValue(value: any): void
  onInput(callback: (field: Field) => void): void
  onFocus(callback: (field: Field) => void): void
  onBlur(callback: (field: Field) => void): void
}
```

**ArrayField** (list/array field):
```typescript
class ArrayField extends Field {
  value: any[]

  push(...items: any[]): number
  pop(): any
  insert(index: number, ...items: any[]): void
  remove(index: number): any
  shift(): any
  unshift(...items: any[]): number
  move(from: number, to: number): void
  moveUp(index: number): void
  moveDown(index: number): void
}
```

## Usage Examples with Code Snippets

### Example 1: Basic Form Setup

```typescript
import { createForm } from '@formily/core'
import { FormProvider, Field } from '@formily/react'
import { Form, FormItem, Input, Submit } from '@formily/antd'

// Create form instance
const form = createForm({
  initialValues: {
    username: '',
    email: ''
  },
  effects: () => {
    onFormValuesChange((form) => {
      console.log('Form values:', form.values)
    })
  }
})

// Render form
function MyForm() {
  return (
    <FormProvider form={form}>
      <Form layout="vertical">
        <Field
          name="username"
          title="Username"
          required
          decorator={[FormItem]}
          component={[Input]}
        />
        <Field
          name="email"
          title="Email"
          required
          validator="email"
          decorator={[FormItem]}
          component={[Input]}
        />
        <Submit onSubmit={console.log}>Submit</Submit>
      </Form>
    </FormProvider>
  )
}
```

### Example 2: Field Linkage

```typescript
const form = createForm({
  effects: () => {
    // When country changes, update cities dropdown
    onFieldValueChange('country', async (field) => {
      const cities = await fetchCities(field.value)

      form.setFieldState('city', state => {
        state.value = undefined
        state.dataSource = cities
        state.loading = false
      })
    })

    // Show/hide fields based on conditions
    onFieldValueChange('userType', (field) => {
      form.setFieldState('companyName', state => {
        state.visible = field.value === 'business'
      })
    })
  }
})
```

### Example 3: Array Field Management

```typescript
function UserList() {
  return (
    <FormProvider form={form}>
      <ArrayField name="users">
        {(field) => (
          <div>
            {field.value?.map((item, index) => (
              <div key={index}>
                <Field
                  name={`users.${index}.name`}
                  component={[Input]}
                />
                <Field
                  name={`users.${index}.email`}
                  component={[Input]}
                />
                <button onClick={() => field.remove(index)}>
                  Remove
                </button>
              </div>
            ))}
            <button onClick={() => field.push({ name: '', email: '' })}>
              Add User
            </button>
          </div>
        )}
      </ArrayField>
    </FormProvider>
  )
}
```

### Example 4: JSON Schema Form

```typescript
import { createSchemaField } from '@formily/react'

const SchemaField = createSchemaField({
  components: {
    Input,
    Select,
    DatePicker,
    FormItem
  }
})

const schema = {
  type: 'object',
  properties: {
    username: {
      type: 'string',
      title: 'Username',
      required: true,
      'x-decorator': 'FormItem',
      'x-component': 'Input',
      'x-component-props': {
        placeholder: 'Enter username'
      }
    },
    birthday: {
      type: 'string',
      title: 'Birthday',
      'x-decorator': 'FormItem',
      'x-component': 'DatePicker'
    },
    role: {
      type: 'string',
      title: 'Role',
      enum: ['admin', 'user', 'guest'],
      'x-decorator': 'FormItem',
      'x-component': 'Select'
    }
  }
}

function SchemaForm() {
  return (
    <FormProvider form={form}>
      <SchemaField schema={schema} />
    </FormProvider>
  )
}
```

### Example 5: Custom Validation

```typescript
// Register custom rule
registerValidateRules({
  uniqueUsername: async (value) => {
    const exists = await checkUsernameExists(value)
    if (exists) {
      return {
        type: 'error',
        message: 'Username already taken'
      }
    }
  }
})

// Use in form
const form = createForm({
  effects: () => {
    onFieldInit('username', (field) => {
      field.validator = [
        { required: true },
        { min: 3, message: 'At least 3 characters' },
        { uniqueUsername: true }
      ]
    })
  }
})
```

## Integration Patterns and Workflows

### Pattern 1: Controlled vs Uncontrolled

Formily supports both controlled and uncontrolled patterns:

```typescript
// Uncontrolled (recommended for performance)
const form = createForm()
<FormProvider form={form}>
  <Field name="input" component={[Input]} />
</FormProvider>

// Controlled (for external state management)
const [formState, setFormState] = useState({})
useEffect(() => {
  form.setValues(formState)
}, [formState])
```

### Pattern 2: Multi-Step Forms

```typescript
import { FormStep } from '@formily/antd'

const form = createForm()

<FormProvider form={form}>
  <FormStep
    current={currentStep}
    onChange={setCurrentStep}
  >
    <FormStep.StepPane title="Basic Info">
      <Field name="username" />
    </FormStep.StepPane>
    <FormStep.StepPane title="Contact">
      <Field name="email" />
    </FormStep.StepPane>
  </FormStep>
</FormProvider>
```

### Pattern 3: Dialog Forms

```typescript
import { FormDialog } from '@formily/antd'

const dialog = FormDialog('Edit User', () => {
  return (
    <FormLayout>
      <Field name="username" component={[Input]} />
      <Field name="email" component={[Input]} />
    </FormLayout>
  )
})

// Open dialog
dialog.open({
  initialValues: { username: 'john' }
}).then((values) => {
  console.log('Submitted:', values)
})
```

## Configuration Options and Extension Points

### Form Configuration Options

```typescript
interface IFormProps {
  initialValues?: any
  values?: any
  pattern?: 'editable' | 'disabled' | 'readOnly' | 'readPretty'
  display?: 'visible' | 'hidden' | 'none'
  hidden?: boolean
  visible?: boolean
  readOnly?: boolean
  disabled?: boolean
  readPretty?: boolean
  editable?: boolean

  validateFirst?: boolean       // Stop validation on first error
  effects?: (form: Form) => void  // Effect registration

  // Lifecycle callbacks
  onInit?: (form: Form) => void
  onMount?: (form: Form) => void
  onUnmount?: (form: Form) => void
}
```

### Field Configuration Options

```typescript
interface IFieldProps {
  name: string | number
  title?: string
  description?: string
  value?: any
  initialValue?: any
  required?: boolean
  hidden?: boolean
  visible?: boolean
  display?: 'visible' | 'hidden' | 'none'
  pattern?: 'editable' | 'disabled' | 'readOnly' | 'readPretty'

  validator?: Validator | Validator[]
  dataSource?: any[]

  decorator?: [Component, Props?]
  component?: [Component, Props?]

  reactions?: FieldReaction | FieldReaction[]
}
```

### Extension: Custom Components

```typescript
import { connect, mapProps } from '@formily/react'

// Create custom form component
const MyCustomInput = connect(
  CustomInputComponent,
  mapProps((props, field) => {
    return {
      ...props,
      value: field.value,
      onChange: field.onInput,
      disabled: field.pattern === 'disabled',
      readOnly: field.pattern === 'readOnly'
    }
  })
)

// Register in SchemaField
const SchemaField = createSchemaField({
  components: {
    MyCustomInput
  }
})
```

### Extension: Custom Validators

```typescript
// Register global validator
registerValidateRules({
  strongPassword: (value) => {
    const hasUpper = /[A-Z]/.test(value)
    const hasLower = /[a-z]/.test(value)
    const hasNumber = /\d/.test(value)
    const hasSpecial = /[!@#$%^&*]/.test(value)

    if (!(hasUpper && hasLower && hasNumber && hasSpecial)) {
      return 'Password must contain uppercase, lowercase, number, and special character'
    }
  }
})
```

### Extension: Custom Effects

```typescript
// Create custom effect hook
const onCustomEvent = createEffectHook<PayloadType>('onCustomEvent')

// Use in form
const form = createForm({
  effects: () => {
    onCustomEvent((payload) => {
      console.log('Custom event:', payload)
    })
  }
})

// Trigger from anywhere
form.notify('onCustomEvent', { data: 'value' })
```
