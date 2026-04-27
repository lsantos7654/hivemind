### Component APIs and Props
- Button: `type`, `color`, `variant`, `shape`, `size`, `icon`, `iconPlacement`, `loading`, `block`, `danger`, `ghost`, `htmlType`, `classNames`, `styles`
- ButtonGroup: `size`, `children`
- Input: `value`, `defaultValue`, `placeholder`, `prefix`, `suffix`, `addonBefore`, `addonAfter`, `allowClear`, `maxLength`, `showCount`, `status`, `size`
- Input.TextArea: `autoSize`, `showCount`, `maxLength`
- Input.Search: `onSearch`, `enterButton`, `loading`
- Input.Password: `visibilityToggle`
- Input.OTP: `length`, `formatter`, `mask`
- InputNumber: `min`, `max`, `step`, `precision`, `formatter`, `parser`, `controls`, `keyboard`
- Select: `options`, `mode`, `showSearch`, `filterOption`, `optionFilterProp`, `labelInValue`, `allowClear`, `maxCount`, `popupMatchSelectWidth`, `virtual`
- AutoComplete: `options`, `onSearch`, `onSelect`, `filterOption`
- Cascader: `options`, `multiple`, `showSearch`, `fieldNames`, `changeOnSelect`, `expandTrigger`
- DatePicker / RangePicker: `format`, `disabledDate`, `showTime`, `picker`, `presets`, `locale`, `value`, `defaultValue`, `onChange`
- TimePicker: `format`, `use12Hours`, `hourStep`, `minuteStep`, `secondStep`
- Checkbox: `checked`, `defaultChecked`, `indeterminate`, `onChange`
- Checkbox.Group: `options`, `value`, `onChange`
- Radio / Radio.Group: `value`, `onChange`, `optionType`, `buttonStyle`
- Switch: `checked`, `defaultChecked`, `onChange`, `checkedChildren`, `unCheckedChildren`, `loading`
- Slider: `min`, `max`, `step`, `marks`, `range`, `tooltip`, `onChange`, `onChangeComplete`
- Rate: `count`, `allowHalf`, `allowClear`, `character`, `tooltips`
- ColorPicker: `format`, `presets`, `showText`, `open`, `trigger`, `disabledAlpha`
- Form: `layout`, `form`, `initialValues`, `onFinish`, `onFinishFailed`, `size`, `colon`, `labelAlign`, `labelCol`, `wrapperCol`, `scrollToFirstError`, `validateTrigger`
- Form.Item: `name`, `label`, `rules`, `dependencies`, `tooltip`, `extra`, `hasFeedback`, `validateStatus`, `noStyle`
- Form.List: `name`, dynamic field management (`add`, `remove`, `move`)
- Form.useForm: `getFieldValue`, `setFieldsValue`, `validateFields`, `resetFields`, `submit`, `scrollToField`
- Form.useWatch: reactive field value watching
- Table: `dataSource`, `columns`, `rowKey`, `pagination`, `scroll`, `loading`, `expandable`, `rowSelection`, `size`, `bordered`, `sticky`, `virtual`, `onChange`
- Table column: `title`, `dataIndex`, `key`, `render`, `sorter`, `filters`, `onFilter`, `filterMode`, `fixed`, `width`, `align`, `ellipsis`, `responsive`
- Modal: `open`, `onOk`, `onCancel`, `title`, `footer`, `width`, `centered`, `destroyOnHidden`, `maskClosable`, `keyboard`, `afterOpenChange`
- Modal.confirm / Modal.info / Modal.warning / Modal.error (static methods)
- Drawer: `open`, `onClose`, `title`, `placement`, `width`, `height`, `footer`, `extra`, `destroyOnHidden`
- Dropdown: `menu`, `trigger`, `placement`, `open`, `onOpenChange`, `arrow`, `dropdownRender`
- Menu: `items`, `mode`, `theme`, `selectedKeys`, `openKeys`, `onSelect`, `onOpenChange`, `inlineCollapsed`
- Tabs: `items`, `activeKey`, `type`, `size`, `tabPosition`, `onChange`, `tabBarExtraContent`
- Collapse: `items`, `accordion`, `expandIconPosition`, `ghost`, `bordered`
- Card: `title`, `extra`, `actions`, `cover`, `bordered`, `hoverable`, `loading`, `size`
- List: `dataSource`, `renderItem`, `header`, `footer`, `pagination`, `grid`, `loading`, `size`, `split`, `bordered`
- Tree: `treeData`, `checkable`, `selectable`, `draggable`, `autoExpandParent`, `defaultExpandAll`, `fieldNames`
- TreeSelect: `treeData`, `multiple`, `treeCheckable`, `showCheckedStrategy`, `fieldNames`
- Upload: `action`, `multiple`, `accept`, `maxCount`, `beforeUpload`, `onChange`, `onRemove`, `listType`, `customRequest`, `fileList`, `showUploadList`
- Transfer: `dataSource`, `targetKeys`, `onChange`, `render`, `titles`, `filterOption`, `showSearch`
- Progress: `type`, `percent`, `strokeColor`, `format`, `status`, `strokeWidth`, `size`
- Spin: `spinning`, `size`, `tip`, `indicator`, `delay`
- Skeleton: `active`, `loading`, `avatar`, `paragraph`, `title`, `round`
- Avatar: `src`, `icon`, `shape`, `size`, `alt`
- Avatar.Group: `maxCount`, `maxPopoverPlacement`, `maxStyle`
- Badge: `count`, `dot`, `overflowCount`, `showZero`, `status`, `color`, `text`, `offset`
- Tag: `color`, `icon`, `closable`, `onClose`, `bordered`
- Tooltip: `title`, `placement`, `trigger`, `open`, `arrow`, `color`, `mouseEnterDelay`, `mouseLeaveDelay`
- Popover: `content`, `title`, `trigger`, `placement`, `open`
- Popconfirm: `title`, `description`, `onConfirm`, `onCancel`, `okText`, `cancelText`, `icon`, `disabled`
- Tour: `steps`, `open`, `current`, `onChange`, `onClose`, `onFinish`, `mask`, `type`
- Alert: `type`, `message`, `description`, `showIcon`, `closable`, `onClose`, `action`, `banner`
- Result: `status`, `title`, `subTitle`, `icon`, `extra`
- Empty: `description`, `image`, `imageStyle`
- Notification (imperative): `notification.success/error/warning/info/open({ message, description, placement, duration, ... })`
- Message (imperative): `message.success/error/warning/info/loading(content, duration)`
- Statistic: `value`, `precision`, `prefix`, `suffix`, `title`, `formatter`, `decimalSeparator`
- Statistic.Countdown: `value`, `format`, `onFinish`
- Statistic.Timer: `value`, `format`, `type`
- Steps: `items`, `current`, `status`, `direction`, `labelPlacement`, `progressDot`, `size`, `type`
- Timeline: `items`, `mode`, `pending`, `reverse`
- Descriptions: `items`, `title`, `bordered`, `column`, `size`, `layout`, `colon`, `extra`
- Pagination: `current`, `total`, `pageSize`, `showSizeChanger`, `showQuickJumper`, `onChange`, `itemRender`
- Anchor: `items`, `affix`, `offsetTop`, `targetOffset`, `direction`, `replace`, `onChange`
- Breadcrumb: `items`, `separator`
- Affix: `offsetTop`, `offsetBottom`, `onChange`
- BackTop: `visibilityHeight`, `onClick`, `target`
- FloatButton: `icon`, `tooltip`, `type`, `shape`, `href`, `target`, `badge`
- FloatButton.Group: `trigger`, `icon`, `closeIcon`, `open`, `onOpenChange`, `placement`
- Layout: `Layout`, `Layout.Header`, `Layout.Content`, `Layout.Sider`, `Layout.Footer`
- Layout.Sider: `collapsible`, `collapsed`, `defaultCollapsed`, `onCollapse`, `width`, `collapsedWidth`, `theme`, `breakpoint`, `trigger`
- Grid: `Row` (`gutter`, `align`, `justify`, `wrap`), `Col` (`span`, `offset`, `push`, `pull`, `xs/sm/md/lg/xl/xxl`)
- Space: `size`, `direction`, `wrap`, `align`
- Space.Compact: `size`, `direction`, `block`
- Flex: `align`, `justify`, `gap`, `wrap`, `flex`, `vertical`
- Divider: `type`, `orientation`, `dashed`, `plain`
- Image: `src`, `width`, `height`, `alt`, `fallback`, `preview`, `placeholder`
- Image.PreviewGroup: `items`, `preview`
- Carousel: `autoplay`, `dots`, `effect`, `speed`, `dotPosition`, `slidesToShow`
- Calendar: `mode`, `value`, `fullscreen`, `headerRender`, `cellRender`, `disabledDate`
- Watermark: `content`, `font`, `image`, `zIndex`, `rotate`, `width`, `height`, `gap`
- QRCode: `value`, `type`, `size`, `icon`, `iconSize`, `errorLevel`, `color`, `bgColor`, `status`
- Splitter: `layout`, `onResizeStart`, `onResize`, `onResizeEnd`
- Masonry: `gutter`, `column`
- Segmented: `options`, `value`, `block`, `size`, `disabled`
- Mentions: `options`, `split`, `prefix`, `onSearch`, `filterOption`
- App: `message`, `notification`, `warning` (component-level usage limit overrides)

### Design Token System
- SeedToken interface and all defaults (from `components/theme/themes/seed.ts`)
- MapToken derived colour palettes and scale generation
- AliasToken semantic naming conventions
- Per-component token overrides via `ConfigProvider theme.components`
- `theme.useToken()` hook and return shape: `{ theme, token, hashId, cssVar }`
- `theme.getDesignToken(config)` for static computation
- CSS Variables mode: `cssVar: true` in ThemeConfig
- Dark algorithm: colour inversion and background token derivation
- Compact algorithm: size/spacing scale reduction
- Custom algorithm function signature: `(seedToken: SeedToken, mapToken: MapToken) => Partial<MapToken>`
- Token hierarchy: seed → map → alias → component
- `theme.defaultSeed` — the default seed token values object

### CSS-in-JS Architecture
- `genComponentStyleHook` factory pattern for component styles
- `useStyle(prefixCls)` pattern inside each component
- Hash-based class name generation for style isolation
- Token-driven style calculation (no hardcoded values in component styles)
- CSP nonce support via ConfigProvider
- Style injection and cache invalidation behaviour
- `@ant-design/cssinjs` package: `createTheme`, `StyleContext`, `useStyleRegister`
- Static CSS extraction for SSR via `@ant-design/static-style-extract`

### ConfigProvider Configuration
- All per-component config props (ButtonConfig, InputConfig, TableConfig, etc.)
- `renderEmpty` for custom empty states
- `getPopupContainer` for portal container
- `virtual` for virtualised select-like components
- `warning` configuration and suppression
- `wave` — click ripple effect configuration
- Locale integration: `locale` prop + dayjs locale coordination
- Nested ConfigProvider support (token merging)

### Internationalisation
- All 80+ locale pack names and import paths (`antd/locale/zh_CN`, etc.)
- `Locale` interface structure (component-level string maps)
- `useLocale()` hook
- dayjs locale coordination (must set separately: `dayjs.locale('zh-cn')`)
- Adding/modifying locale files: all language files must be updated in sync

### Build and Development Workflow
- `npm run start` — dev docs server
- `npm run compile` / `npm run build` — ESM/CJS/UMD output
- `npm run style` — static CSS generation
- `npm run test` / `npm run test:update` — Jest test suite
- `npm run tsc` — TypeScript type check
- `npm run lint` — full lint suite
- `npm run token:meta` / `npm run token:statistic` — token tooling
- father build tool configuration (`.fatherrc.ts`)
- antd-tools CLI commands

### Component Contribution Patterns
- Per-component directory structure (impl + style + tests + demos + docs)
- Semantic class names / styles API pattern (`classNames`, `styles` props)
- `useComponentConfig()` for reading ConfigProvider per-component defaults
- `useStyle(prefixCls)` CSS-in-JS style hook pattern
- Compound component pattern (Form.Item, Table.Column, etc.)
- Demo file conventions (absolute imports required in `demo/` and `.dumi/`)
- Test file conventions (relative imports required in `__tests__/`)
- PR title format and changelog entry format
- Branch naming and target branch strategy
- Wave/ripple effect integration

### Testing Patterns
- `@testing-library/react` render helpers
- `jest-axe` for accessibility testing
- Snapshot tests and semantic snapshot tests (`demo-semantic.test.tsx`)
- Image regression tests (puppeteer-based)
- `jest-canvas-mock` for canvas-using components
- `identity-obj-proxy` for CSS module mocking
- `tests/utils.tsx` shared render utilities
- `LIB_DIR` environment variable for testing built outputs

### Accessibility
- ARIA attribute patterns used across components
- Keyboard navigation support
- Screen reader considerations
- jest-axe integration in test suite
