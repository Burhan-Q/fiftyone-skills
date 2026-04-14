---
name: fiftyone-develop-modal-panel
description: Develops custom FiftyOne modal panel plugins with JavaScript UI. Use when building interactive panels that appear in the sample modal — image overlays, per-sample visualizations, annotation tools, or any custom UI that needs to render alongside a sample.
---

# Develop FiftyOne Modal Panel Plugins

## Overview

This skill builds **modal panels** — interactive JS panels that appear inside the
FiftyOne sample modal. Modal panels are JS-first: the UI is a React component
registered from JavaScript, while Python operators provide backend data access.

**Do NOT use Python Panel classes with `composite_view=True`** for modal panels.
This pattern is unreliable and produces "Unsupported View" errors. Instead, use
the proven architecture described below.

---

## Architecture (JS Panel + Python Operators)

```
┌─────────────────────────────────────────────────┐
│              FiftyOne Sample Modal               │
├────────────────────┬────────────────────────────┤
│  JS Panel (React)  │  Python Operators (backend) │
├────────────────────┼────────────────────────────┤
│ • registerComponent│ • foo.Operator classes       │
│   with panelOptions│ • ctx.current_sample (ID)    │
│   surfaces: "modal"│ • ctx.dataset[id] (sample)   │
│ • useOperatorExec  │ • Return dicts from execute() │
│ • React state/hooks│ • unlisted=True for internal │
└────────────────────┴────────────────────────────┘
```

### Why this architecture?

| Approach | Works? | Notes |
|----------|--------|-------|
| Python Panel + `composite_view=True` | **NO** | "Unsupported View" error — component not found |
| Python Panel only (no JS) | Limited | No image display (`panel.image()` doesn't exist) |
| **JS Panel + Python Operators** | **YES** | Proven, reliable pattern |

---

## Critical Rules (Read Before Coding)

### 1. Panel registration — `panelOptions`, not `surfaces`

```typescript
// CORRECT — panel appears in modal picker
registerComponent({
  name: "MyModalPanel",
  label: "My Modal Panel",
  component: MyComponent,
  type: PluginComponentType.Panel,
  panelOptions: { surfaces: "modal" },  // <-- MUST use panelOptions
});

// WRONG — panel will NOT appear in modal
registerComponent({
  name: "MyModalPanel",
  component: MyComponent,
  type: PluginComponentType.Panel,
  surfaces: "modal",  // <-- This does NOT work for modal panels
});
```

### 2. Panel name in fiftyone.yml must match JS registration

```yaml
# fiftyone.yml
panels:
  - MyModalPanel  # Must exactly match registerComponent name
```

### 3. JS bundle path goes in package.json, not fiftyone.yml

```json
// package.json
{
  "fiftyone": {
    "script": "dist/index.umd.js"
  }
}
```

Do NOT use `js_bundle:` in fiftyone.yml — it is unreliable.

### 4. `ctx.current_sample` returns an ID, not a Sample

```python
# CORRECT
sample_id = ctx.current_sample
sample = ctx.dataset[sample_id]
filepath = sample.filepath

# WRONG — ctx.current_sample is a string ID, not a Sample object
filepath = ctx.current_sample.filepath  # AttributeError!
```

### 5. `useOperatorExecutor` — watch `.result`, don't chain `.then()`

```typescript
// CORRECT — watch the result state
const myOp = useOperatorExecutor("@plugin/my_operator");

useEffect(() => { myOp.execute({}); }, []);  // Fire once

useEffect(() => {
  if (myOp.result?.data) {
    setData(myOp.result.data);  // React to result
  }
}, [myOp.result]);

// WRONG — execute() returns void, not the result
myOp.execute({}).then((result) => { ... });  // result is undefined!
```

### 6. `@fiftyone/*` packages are externalized as window globals

These are provided by the FiftyOne App at runtime — do NOT install them via npm/yarn:

| Package | Global | Purpose |
|---------|--------|---------|
| `@fiftyone/plugins` | `__fop__` | registerComponent, PluginComponentType |
| `@fiftyone/operators` | `__foo__` | useOperatorExecutor, usePanelEvent |
| `@fiftyone/state` | `__fos__` | Dataset/view/modal state atoms |
| `@fiftyone/components` | `__foc__` | UI components |
| `@fiftyone/utilities` | `__fou__` | Utility functions |
| `@fiftyone/spaces` | `__fosp__` | Panel/space management |
| `@mui/material` | `__mui__` | MUI components (Box, Typography, etc.) |
| `react` | `React` | React |
| `react-dom` | `ReactDOM` | ReactDOM |
| `recoil` | `recoil` | Recoil state (useRecoilValue, etc.) |

### 7. Use Yarn 4.x (not npm) for FiftyOne plugin development

---

## File Structure

```
my-modal-plugin/
├── fiftyone.yml          # Plugin manifest (panels + operators)
├── __init__.py           # Python operators for backend data
├── package.json          # JS metadata + fiftyone.script path
├── tsconfig.json         # TypeScript config
├── vite.config.ts        # Build config with externals
├── src/
│   ├── index.ts          # registerComponent entry point
│   └── MyPanel.tsx       # React panel component
└── dist/
    └── index.umd.js      # Built bundle (auto-generated)
```

---

## Complete Working Example

### fiftyone.yml

```yaml
name: "@myorg/my-modal-plugin"
type: plugin
version: "1.0.0"
description: "My custom modal panel"
fiftyone:
  version: "*"
panels:
  - MyModalPanel
operators:
  - get_data
  - get_current_sample
```

### __init__.py

```python
import fiftyone.operators as foo
import fiftyone.operators.types as types


class GetData(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="get_data",
            label="Get Data",
            unlisted=True,
        )

    def execute(self, ctx):
        # Access dataset, return data for the JS panel
        values = ctx.dataset.values("filepath")
        return {"values": values}


class GetCurrentSample(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="get_current_sample",
            label="Get Current Sample",
            unlisted=True,
        )

    def execute(self, ctx):
        try:
            sample_id = ctx.current_sample  # Returns ID string
            if sample_id:
                sample = ctx.dataset[sample_id]  # Fetch actual sample
                return {"filepath": sample.filepath, "id": sample_id}
        except Exception:
            pass
        return {"filepath": None, "id": None}


def register(p):
    p.register(GetData)
    p.register(GetCurrentSample)
```

### package.json

```json
{
  "name": "@myorg/my-modal-plugin",
  "version": "1.0.0",
  "main": "src/index.ts",
  "fiftyone": {
    "script": "dist/index.umd.js"
  },
  "scripts": {
    "build": "vite build",
    "dev": "IS_DEV=true vite build --watch"
  },
  "dependencies": {
    "@rollup/plugin-node-resolve": "^15.0.2",
    "@vitejs/plugin-react": "^4.0.0",
    "react": "^18.2.0",
    "vite-plugin-externals": "^0.6.2"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "vite": "^5.0.0"
  },
  "packageManager": "yarn@4.10.3"
}
```

### vite.config.ts

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { nodeResolve } from "@rollup/plugin-node-resolve";
import { viteExternalsPlugin } from "vite-plugin-externals";
import path from "path";
import pkg from "./package.json";

const { FIFTYONE_DIR } = process.env;
const IS_DEV = process.env.IS_DEV === "true";

function fiftyonePlugin() {
  return {
    name: "fiftyone-rollup",
    resolveId: {
      order: "pre" as const,
      async handler(source: string) {
        if (source.startsWith("@fiftyone") && FIFTYONE_DIR) {
          const pkgName = source.split("/")[1];
          const modulePath = `${FIFTYONE_DIR}/app/packages/${pkgName}`;
          return this.resolve(modulePath, source, { skipSelf: true });
        }
        return null;
      },
    },
  };
}

export default defineConfig({
  mode: IS_DEV ? "development" : "production",
  plugins: [
    fiftyonePlugin(),
    nodeResolve(),
    react(),
    viteExternalsPlugin({
      react: "React",
      "react-dom": "ReactDOM",
      "@fiftyone/state": "__fos__",
      "@fiftyone/operators": "__foo__",
      "@fiftyone/components": "__foc__",
      "@fiftyone/utilities": "__fou__",
      "@fiftyone/plugins": "__fop__",
      "@fiftyone/spaces": "__fosp__",
    }),
  ],
  build: {
    minify: !IS_DEV,
    lib: {
      entry: path.join(__dirname, pkg.main),
      name: pkg.name,
      fileName: (format) => `index.${format}.js`,
      formats: ["umd"],
    },
  },
  define: {
    "process.env.NODE_ENV": JSON.stringify(
      IS_DEV ? "development" : "production"
    ),
  },
  optimizeDeps: {
    exclude: ["react", "react-dom"],
  },
});
```

### tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "jsx": "react-jsx",
    "moduleResolution": "Node",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["src"]
}
```

### src/index.ts

```typescript
import { PluginComponentType, registerComponent } from "@fiftyone/plugins";
import MyModalPanel from "./MyPanel";

console.log("[MyPlugin] Registering MyModalPanel");

registerComponent({
  name: "MyModalPanel",       // Must match fiftyone.yml panels entry
  label: "My Modal Panel",
  component: MyModalPanel,
  type: PluginComponentType.Panel,
  panelOptions: { surfaces: "modal" },  // CRITICAL for modal panels
});
```

### src/MyPanel.tsx

```typescript
import React, { useState, useEffect, useRef, useCallback } from "react";
import { useOperatorExecutor } from "@fiftyone/operators";

const PLUGIN = "@myorg/my-modal-plugin";

export default function MyModalPanel() {
  const dataOp = useOperatorExecutor(`${PLUGIN}/get_data`);
  const sampleOp = useOperatorExecutor(`${PLUGIN}/get_current_sample`);

  const [data, setData] = useState<string[]>([]);
  const [currentSample, setCurrentSample] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const hasTriggered = useRef(false);

  // Fire operators once on mount
  useEffect(() => {
    if (hasTriggered.current) return;
    hasTriggered.current = true;
    dataOp.execute({});
    sampleOp.execute({});
  }, []);

  // Watch for data result
  useEffect(() => {
    if (dataOp.result?.values) {
      setData(dataOp.result.values);
      setLoading(false);
    }
  }, [dataOp.result]);

  // Watch for current sample result
  useEffect(() => {
    if (sampleOp.result?.filepath) {
      setCurrentSample(sampleOp.result);
    }
  }, [sampleOp.result]);

  // Watch for errors
  useEffect(() => {
    if (dataOp.error) {
      console.error("[MyPlugin] data error:", dataOp.error);
      setLoading(false);
    }
  }, [dataOp.error]);

  // Refresh current sample (e.g. after navigating)
  const refresh = useCallback(() => {
    sampleOp.execute({});
  }, [sampleOp]);

  if (loading) return <div style={{ padding: 16, color: "#888" }}>Loading…</div>;

  return (
    <div style={{ padding: 16, color: "#e0e0e0" }}>
      <h3>My Modal Panel</h3>
      <p>Current: {currentSample?.filepath ?? "none"}</p>
      <button onClick={refresh}>Refresh Sample</button>
      <p>{data.length} items loaded</p>
    </div>
  );
}
```

---

## Build & Install

```bash
cd my-modal-plugin

# Install dependencies (use yarn, not npm)
yarn install

# Build the JS bundle
yarn build

# Verify dist/index.umd.js was created
ls dist/index.umd.js
```

After building, restart the FiftyOne App. Open any sample in the modal — the
panel should appear in the modal panel picker.

### Development workflow

```bash
# Terminal 1: Watch for TS changes (auto-rebuilds)
yarn dev

# Terminal 2: Run FiftyOne with debug logging
fiftyone app debug <dataset-name>

# After each rebuild, hard-refresh the browser (Ctrl+Shift+R)
```

---

## Accessing Modal Context from JS

### Current sample via Python operator

The most reliable way to get the current modal sample is through a Python
operator using `ctx.current_sample`:

```python
class GetCurrentSample(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(name="get_current_sample", unlisted=True)

    def execute(self, ctx):
        sample_id = ctx.current_sample           # String ID
        sample = ctx.dataset[sample_id]           # Fetch Sample object
        return {"filepath": sample.filepath, "id": sample_id}
```

### Media URLs

FiftyOne serves media through its `/media` endpoint:

```typescript
function getMediaUrl(filepath: string): string {
  return `/media?filepath=${encodeURIComponent(filepath)}`;
}

// Usage in JSX
<img src={getMediaUrl(filepath)} alt="sample" />
```

This works for both local paths and cloud storage (S3, GCS) — the FiftyOne
server handles the proxy/redirect.

---

## Patterns

### Dropdown populated from dataset

```python
# Python operator
class GetFieldValues(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(name="get_field_values", unlisted=True)

    def execute(self, ctx):
        return {"values": ctx.dataset.distinct("label")}
```

```typescript
// JS component
const fieldOp = useOperatorExecutor("@myorg/plugin/get_field_values");

useEffect(() => { fieldOp.execute({}); }, []);
useEffect(() => {
  if (fieldOp.result?.values) setOptions(fieldOp.result.values);
}, [fieldOp.result]);

return (
  <select onChange={(e) => setSelected(e.target.value)}>
    {options.map(v => <option key={v} value={v}>{v}</option>)}
  </select>
);
```

### Passing parameters to operators

```python
class GetSampleField(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(name="get_sample_field", unlisted=True)

    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.str("sample_id", required=True)
        inputs.str("field", required=True)
        return types.Property(inputs)

    def execute(self, ctx):
        sample_id = ctx.params["sample_id"]
        field = ctx.params["field"]
        sample = ctx.dataset[sample_id]
        return {"value": sample[field]}
```

```typescript
// Pass params to execute()
fieldOp.execute({ sample_id: "abc123", field: "predictions" });
```

### CSS image overlay (client-side compositing)

```typescript
// Two stacked images with CSS opacity — no server round-trip for slider changes
<div style={{ position: "relative", width: "100%", height: "100%" }}>
  <img src={baseSrc} style={{
    position: "absolute", top: "50%", left: "50%",
    transform: "translate(-50%, -50%)",
    maxWidth: "100%", maxHeight: "100%", objectFit: "contain",
  }} />
  <img src={overlaySrc} style={{
    position: "absolute", top: "50%", left: "50%",
    transform: "translate(-50%, -50%)",
    maxWidth: "100%", maxHeight: "100%", objectFit: "contain",
    opacity: sliderValue / 100,
    mixBlendMode: diffMode ? "difference" : "normal",
    pointerEvents: "none",
  }} />
</div>
```

---

## Debugging

### Where logs go

| Log Type | Location |
|----------|----------|
| Python operators | Server terminal (print/logging) |
| JS component | Browser DevTools Console (F12) |
| Network requests | Browser DevTools Network tab |
| Bundle loading | Browser Console — look for registration log |

### Verify bundle loads

Add a `console.log` at the top of `src/index.ts`:
```typescript
console.log("[MyPlugin] Registering...");
```

If you don't see this in the browser console, the bundle isn't loading. Check:
1. `fiftyone.script` path in `package.json` is correct
2. `dist/index.umd.js` exists after build
3. FiftyOne server was restarted

### "Unsupported View" error

This means the App can't find a JS component. If you see this:
- You are likely using `composite_view=True` in a Python Panel — **don't do this**
- Switch to the JS Panel + Python Operators architecture described above

### Panel not in modal picker

Check these in order:
1. `panels:` entry in `fiftyone.yml` matches `registerComponent` name exactly
2. `panelOptions: { surfaces: "modal" }` is set (not `surfaces: "modal"`)
3. `fiftyone.script` in `package.json` points to built bundle
4. Bundle was rebuilt after changes (`yarn build`)
5. FiftyOne server was restarted

### Operator result is empty/undefined

`useOperatorExecutor.execute()` returns void. Do NOT chain `.then()` on it.
Instead, watch the `.result` property via `useEffect`:

```typescript
useEffect(() => {
  if (myOp.result) console.log("Got result:", myOp.result);
}, [myOp.result]);
```

---

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| `surfaces: "modal"` at top level of registerComponent | Use `panelOptions: { surfaces: "modal" }` |
| `composite_view=True` in Python Panel | Don't use — switch to JS panel |
| `js_bundle:` in fiftyone.yml | Use `fiftyone.script` in package.json |
| `ctx.current_sample.filepath` | `ctx.dataset[ctx.current_sample].filepath` |
| `execute().then(r => ...)` | Watch `executor.result` via useEffect |
| `npm install` for FiftyOne plugins | Use `yarn install` (Yarn 4.x) |
| `@fiftyone/*` in npm dependencies | Externalize them — they're window globals |
| Missing `type: plugin` in fiftyone.yml | Add it — some versions require it |
| Panel name mismatch between yml and JS | Must be identical strings |
