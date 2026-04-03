# Ant Design — APIs and Interfaces

## Public Entry Points

Ant Design is imported from the `antd` package. All 84+ components, their TypeScript prop types, and shared utilities are re-exported from `components/index.ts`.

```tsx
// Named component imports (tree-shakeable via ESM)
import { Button, Form, Table, ConfigProvider, theme } from 'antd';

// Type imports
import type { ButtonProps, FormInstance, TableProps, ThemeConfig } from 'antd';

// Locale import
import enUS from 'antd/locale/en_US';

// ESM deep import (bypasses index barrel for smaller bundles)
import Button from 'antd/es/button';
```

---

## ConfigProvider — Global Configuration

`ConfigProvider` is the root configuration component. It must wrap the application to enable theming, localisation, and component-level defaults.

**File:** `components/config-provider/index.tsx`

```tsx
import { ConfigProvider } from 'antd';
import enUS from 'antd/locale/en_US';
import { theme } from 'antd';

<ConfigProvider
  locale={enUS}
  direction="ltr"          // 'ltr' | 'rtl'
  componentSize="middle"   // 'small' | 'middle' | 'large'
  prefixCls="ant"          // CSS class prefix (default: 'ant')
  theme={{
    algorithm: theme.defaultAlgorithm,
    token: {
      colorPrimary: '#1677ff',
      borderRadius: 6,
      fontFamily: 'Inter, sans-serif',
    },
    components: {
      Button: { colorPrimary: '#00b96b' },  // Per-component token overrides
    },
    cssVar: true,           // Enable CSS custom properties mode
  }}
  wave={{ disabled: false }}
>
  <App />
</ConfigProvider>
```

Key `ConfigProviderProps` (defined in `components/config-provider/context.ts`):
- `locale` — Locale pack object
- `direction` — `'ltr' | 'rtl'`
- `componentSize` — Default size for all form controls
- `theme` — `ThemeConfig` (see Design Token section below)
- `prefixCls` — CSS class name prefix
- `csp` — Content Security Policy nonce
- `renderEmpty` — Custom empty state renderer
- `getPopupContainer` — Default popup container function
- `virtual` — Enable virtual scrolling for select-like components
- Per-component config props: `button`, `input`, `select`, `table`, `form`, `modal`, etc.

---

## Design Token System

**Files:** `components/theme/index.tsx`, `components/theme/themes/seed.ts`

The design token system has three tiers:

### 1. Seed Tokens (primitives, `SeedToken`)
Raw design values. Key defaults from `components/theme/themes/seed.ts`:

```ts
colorPrimary: '#1677ff'
colorSuccess: '#52c41a'
colorWarning: '#faad14'
colorError: '#ff4d4f'
colorInfo: '#1677ff'
fontSize: 14
borderRadius: 6
controlHeight: 32      // Default control height in px
sizeUnit: 4            // 4px spacing unit
```

### 2. Map Tokens
Derived from seed tokens by the algorithm. Examples:
- `colorPrimaryBg`, `colorPrimaryHover`, `colorPrimaryActive` (from `colorPrimary`)
- `colorBgContainer`, `colorBgLayout`, `colorBorderSecondary`

### 3. Alias Tokens (`AliasToken`)
Semantic names used by component styles.

### Theme Algorithms

```tsx
import { theme } from 'antd';

// Light (default)
theme.defaultAlgorithm

// Dark mode
theme.darkAlgorithm

// Compact (reduced spacing)
theme.compactAlgorithm

// Multiple algorithms can be combined:
algorithm: [theme.darkAlgorithm, theme.compactAlgorithm]
```

### `theme.useToken()` Hook

Access the current design token values inside any component:

```tsx
import { theme } from 'antd';

function MyComponent() {
  const { token, hashId, cssVar } = theme.useToken();
  // token.colorPrimary, token.fontSize, token.borderRadius, etc.
  return <div style={{ color: token.colorPrimary }}>Hello</div>;
}
```

### `theme.getDesignToken(config)` — Static Token Computation

Compute token values without React:

```tsx
import { theme } from 'antd';

const globalToken = theme.getDesignToken({
  token: { colorPrimary: '#1677ff' },
  algorithm: theme.darkAlgorithm,
});
// globalToken.colorPrimary, globalToken.colorBgContainer, etc.
```

---

## Button Component

**File:** `components/button/Button.tsx`

```tsx
import { Button } from 'antd';

// Variants (new in v5+, preferred over `type`)
<Button color="primary" variant="solid">Primary</Button>
<Button color="default" variant="outlined">Default</Button>
<Button color="danger" variant="filled">Danger</Button>

// Legacy type prop (still supported)
<Button type="primary">Primary</Button>
<Button type="default">Default</Button>
<Button type="dashed">Dashed</Button>
<Button type="text">Text</Button>
<Button type="link">Link</Button>

// Props
<Button
  size="large"                    // 'small' | 'middle' | 'large'
  shape="round"                   // 'default' | 'circle' | 'round'
  icon={<SearchOutlined />}
  iconPlacement="start"           // 'start' | 'end'
  loading={true}                  // or { delay: 300 }
  disabled={false}
  block={false}                   // Full width
  danger={false}
  ghost={false}
  htmlType="button"               // 'button' | 'submit' | 'reset'
  classNames={{ root: '', icon: '', content: '' }}  // Semantic class names
  styles={{ root: {}, icon: {}, content: {} }}      // Semantic styles
/>

// Button.Group
<Button.Group size="large">
  <Button>Left</Button>
  <Button>Right</Button>
</Button.Group>
```

Key types (`components/button/buttonHelpers.tsx`):
- `ButtonType`: `'primary' | 'dashed' | 'link' | 'text' | 'default'`
- `ButtonVariantType`: `'outlined' | 'dashed' | 'solid' | 'filled' | 'text' | 'link'`
- `ButtonColorType`: `'default' | 'primary' | 'danger'`
- `ButtonShape`: `'default' | 'circle' | 'round'`

---

## Form Component

**File:** `components/form/index.tsx`

```tsx
import { Form, Input, Button } from 'antd';
import type { FormInstance } from 'antd';

const [form] = Form.useForm();

<Form
  form={form}
  layout="horizontal"   // 'horizontal' | 'vertical' | 'inline'
  onFinish={(values) => console.log(values)}
  onFinishFailed={({ values, errorFields }) => {}}
  initialValues={{ username: '' }}
  size="middle"
  colon={true}
  labelAlign="right"
  scrollToFirstError
>
  <Form.Item
    name="username"
    label="Username"
    rules={[
      { required: true, message: 'Required!' },
      { min: 3, message: 'Min 3 chars' },
      { validator: async (_, value) => { /* custom */ } },
    ]}
  >
    <Input />
  </Form.Item>

  <Form.List name="items">
    {(fields, { add, remove }) =>
      fields.map(field => (
        <Form.Item key={field.key} {...field}>
          <Input />
        </Form.Item>
      ))
    }
  </Form.List>
</Form>

// Imperative API
form.getFieldValue('username');
form.setFieldsValue({ username: 'alice' });
form.validateFields(['username']);
form.resetFields();
form.submit();

// Watch a field value reactively
const username = Form.useWatch('username', form);
```

---

## Table Component

**File:** `components/table/index.tsx`

```tsx
import { Table } from 'antd';
import type { TableProps, TableColumnsType } from 'antd';

const columns: TableColumnsType<DataType> = [
  {
    title: 'Name',
    dataIndex: 'name',
    key: 'name',
    sorter: (a, b) => a.name.localeCompare(b.name),
    filters: [{ text: 'Alice', value: 'Alice' }],
    onFilter: (value, record) => record.name === value,
    render: (text) => <a>{text}</a>,
    fixed: 'left',
    width: 150,
  },
];

<Table<DataType>
  columns={columns}
  dataSource={data}
  rowKey="id"
  pagination={{ pageSize: 20, showSizeChanger: true }}
  scroll={{ x: 1200, y: 400 }}
  loading={false}
  expandable={{ expandedRowRender: (record) => <p>{record.description}</p> }}
  rowSelection={{
    type: 'checkbox',
    onChange: (selectedRowKeys, selectedRows) => {},
  }}
  size="middle"
  bordered={false}
  sticky
  virtual                          // Virtualised rows for large datasets
/>
```

---

## Notification and Message (Imperative APIs)

These are static APIs that do not require a parent component:

```tsx
import { notification, message, App } from 'antd';

// Global notification (requires App.useApp() in antd v6 for proper theming)
notification.success({ message: 'Done', description: 'Operation succeeded' });
notification.error({ message: 'Error', description: 'Something failed' });

// Brief message
message.success('Saved!');
message.loading('Uploading...', 3);

// Recommended: use App.useApp() hook inside App wrapper for themed instances
function MyComponent() {
  const { notification, message, modal } = App.useApp();
  notification.success({ message: 'Themed notification' });
}
```

---

## Typography Component

```tsx
import { Typography } from 'antd';
const { Title, Text, Paragraph, Link } = Typography;

<Title level={1}>H1</Title>          // level: 1-5
<Text type="secondary" copyable>Text</Text>
// type: 'secondary' | 'success' | 'warning' | 'danger'
<Paragraph ellipsis={{ rows: 2, expandable: true }}>Long text...</Paragraph>
<Link href="https://ant.design" target="_blank">Link</Link>
```

---

## Locale / Internationalisation

```tsx
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import jaJP from 'antd/locale/ja_JP';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';

dayjs.locale('zh-cn');

<ConfigProvider locale={zhCN}>
  <DatePicker />   {/* Will display in Chinese */}
</ConfigProvider>
```

80+ locale files available in `components/locale/`, named as `<lang>_<country>.ts`.

---

## Utility Type Helpers

Exported from `components/_util/type.ts`:

```tsx
import type { GetProp, GetProps, GetRef } from 'antd';

// Extract a specific prop type from a component
type CheckboxValue = GetProp<typeof Checkbox, 'value'>;

// Extract all props of a component
type ButtonAllProps = GetProps<typeof Button>;

// Extract the ref type of a component
type InputRefType = GetRef<typeof Input>;
```

---

## Integration Patterns

### Next.js / SSR with Static CSS Extraction

```tsx
// Use @ant-design/static-style-extract for SSR:
import { extractStyle } from '@ant-design/static-style-extract';
const cssText = extractStyle();
```

### Custom Theme with CSS Variables

```tsx
<ConfigProvider theme={{ cssVar: true, hashed: false, token: { colorPrimary: '#f00' } }}>
  {/* All ant design tokens are now also available as CSS custom properties */}
  {/* e.g. --ant-color-primary: #f00 */}
</ConfigProvider>
```

### RTL Support

```tsx
<ConfigProvider direction="rtl">
  <App />
</ConfigProvider>
```

### App Component (antd v5+ preferred pattern for imperative APIs)

```tsx
import { App } from 'antd';

// Wrap at app root
<App><MyApp /></App>

// Inside any child:
function MyChild() {
  const { message, notification, modal } = App.useApp();
  // These respect ConfigProvider theme/locale
}
```

---

## Extension Points

- **Custom empty state:** `ConfigProvider renderEmpty={fn}` — override the empty state renderer globally.
- **Custom prefix:** `ConfigProvider prefixCls="my"` — all CSS classes become `my-btn`, etc.
- **Component-level token overrides:** `ConfigProvider theme={{ components: { Button: { ... } } }}`.
- **Custom algorithms:** Pass a function `(seedToken, mapToken) => Partial<MapToken>` as the `algorithm` to derive custom token mappings.
- **`getPopupContainer`:** Override the DOM container for all overlay components (tooltips, dropdowns, modals) globally.
