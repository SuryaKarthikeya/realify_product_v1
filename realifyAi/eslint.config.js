import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import reactPlugin from 'eslint-plugin-react'
import { defineConfig, globalIgnores } from 'eslint/config'

/**
 * Feature directories under src/features. Each one gets a rule forbidding
 * imports from any *other* feature — the boundary that keeps features
 * independently deletable. Shared code belongs in src/components, src/hooks,
 * src/utils or src/services instead.
 */
const FEATURES = [
  'action-center', 'action-log', 'agents', 'auth', 'comparison',
  'discover', 'history', 'hubs', 'integrations', 'new-analysis',
  'notifications', 'onboarding', 'product-view', 'products', 'profit-ads',
  'screener', 'settings', 'workspace',
]

/**
 * Modules inside the Workspace feature. Each owns its own pages, components,
 * data and logic; none may reach into another's internals.
 */
const WORKSPACE_MODULES = ['dashboard-view', 'simulation']

/**
 * Product domains under src/domains. Each is self-contained: its own data,
 * components and public API. A domain may use `shared`, but never another
 * domain's internals.
 */
const DOMAINS = ['revenue', 'margin', 'cash', 'inventory', 'ads']

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{js,jsx}'],
    extends: [
      js.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    plugins: {
      react: reactPlugin,
    },
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
      parserOptions: {
        ecmaVersion: 'latest',
        ecmaFeatures: { jsx: true },
        sourceType: 'module',
      },
    },
    rules: {
      'no-unused-vars': ['error', { varsIgnorePattern: '^[A-Z_]', argsIgnorePattern: '^_', caughtErrorsIgnorePattern: '^_' }],
      'react/jsx-uses-vars': 'error',
      // Base `no-undef` does not inspect JSX element names, so a component used
      // without being imported fails only at runtime. This closes that gap.
      'react/jsx-no-undef': 'error',
    },
  },

  // ── Feature isolation ────────────────────────────────────────────────────
  ...FEATURES.map((feature) => ({
    files: [`src/features/${feature}/**/*.{js,jsx}`],
    rules: {
      'no-restricted-imports': ['error', {
        patterns: [{
          group: [
            '@/features/*',
            '@/features/*/**',
            `!@/features/${feature}`,
            `!@/features/${feature}/**`,
          ],
          message:
            'Features must not import from other features. Promote the shared code to ' +
            'src/components, src/hooks, src/utils or src/services instead.',
        }],
      }],
    },
  })),

  // Layers below features must never depend on a feature.
  {
    files: [
      'src/components/**/*.{js,jsx}',
      'src/domains/**/*.{js,jsx}',
      'src/hooks/**/*.{js,jsx}',
      'src/utils/**/*.{js,jsx}',
      'src/services/**/*.{js,jsx}',
      'src/store/**/*.{js,jsx}',
      'src/constants/**/*.{js,jsx}',
    ],
    rules: {
      'no-restricted-imports': ['error', {
        patterns: [{
          group: ['@/features/*', '@/features/*/**'],
          message: 'Shared layers must not depend on a feature. Invert the dependency: pass the data in as a prop or argument.',
        }],
      }],
    },
  },

  // ── Domain isolation ─────────────────────────────────────────────────────
  // A domain owns its data and components. Cross-domain access goes through
  // `@/domains/<name>`; `@/domains/shared` is open to all.
  ...DOMAINS.map((domain) => ({
    files: [`src/domains/**/*.{js,jsx}`],
    ignores: [`src/domains/${domain}/**`],
    rules: {
      'no-restricted-imports': ['error', {
        patterns: [{
          group: [`@/domains/${domain}/**`],
          message: `Import the ${domain} domain through its public API (@/domains/${domain}), not its internals.`,
        }],
      }],
    },
  })),

  // Everything outside src/domains reaches a domain through its public API.
  // The exception is `lazy(() => import(...))`, which must name a concrete
  // module to keep its own chunk — same reasoning as the router.
  {
    files: ['src/features/**/*.{js,jsx}', 'src/layouts/**/*.{js,jsx}'],
    rules: {
      'no-restricted-imports': ['error', {
        patterns: [{
          group: ['@/domains/*/components/**', '@/domains/*/data/**', '@/domains/*/utils/**', '!@/domains/shared/**'],
          message: 'Import a product domain through its public API (@/domains/<name>). Deep paths are reserved for lazy() code-split points.',
        }],
      }],
    },
  },

  // The app shell may depend on a feature, but only through its public API
  // (`features/<name>/index.js`) — never on a file inside it.
  {
    files: ['src/layouts/**/*.{js,jsx}'],
    rules: {
      'no-restricted-imports': ['error', {
        patterns: [{
          group: ['@/features/*/**'],
          message:
            'Import a feature through its public API (@/features/<name>) instead of reaching into its internals. ' +
            'If the feature has no index.js yet, add one exporting exactly what the shell needs.',
        }],
      }],
    },
  },

  // ── Workspace module isolation ───────────────────────────────────────────
  // A module owns its pages, components, data and logic. Other modules — and
  // the Workspace root — reach it only through `modules/<name>/index.js`.
  ...WORKSPACE_MODULES.map((module) => ({
    files: [`src/features/workspace/**/*.{js,jsx}`],
    ignores: [`src/features/workspace/modules/${module}/**`],
    rules: {
      'no-restricted-imports': ['error', {
        patterns: [{
          group: [`@/features/workspace/modules/${module}/**`],
          message:
            `Import the ${module} module through its public API ` +
            `(@/features/workspace/modules/${module}), not its internals.`,
        }],
      }],
    },
  })),

  // The router resolves route targets directly so each page keeps its own
  // lazily-loaded chunk; anything else in a feature is off-limits here too.
  {
    files: ['src/routes/**/*.{js,jsx}'],
    rules: {
      'no-restricted-imports': ['error', {
        patterns: [{
          group: [
            '@/features/*/**',
            '!@/features/*/pages/*',
            '!@/features/*/modules/*/pages/*',
          ],
          message: 'The router may only import a feature\'s pages/ (its route targets) or its public API.',
        }],
      }],
    },
  },

  // The route registry is a configuration module, not a component module.
  {
    files: ['src/routes/routeConfig.jsx'],
    rules: { 'react-refresh/only-export-components': 'off' },
  },
])
