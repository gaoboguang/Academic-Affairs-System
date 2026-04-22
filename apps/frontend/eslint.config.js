import eslint from "@eslint/js";
import globals from "globals";
import eslintPluginVue from "eslint-plugin-vue";
import tseslint from "typescript-eslint";

const unusedVarsRule = [
  "error",
  {
    argsIgnorePattern: "^_",
    varsIgnorePattern: "^_",
  },
];

export default tseslint.config(
  {
    ignores: ["dist", "coverage", ".vite"],
  },
  {
    extends: [
      eslint.configs.recommended,
      ...tseslint.configs.recommended,
      ...eslintPluginVue.configs["flat/essential"],
    ],
    files: ["src/**/*.{ts,vue}"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: globals.browser,
      parserOptions: {
        parser: tseslint.parser,
      },
    },
    rules: {
      "@typescript-eslint/no-unused-vars": unusedVarsRule,
      "@typescript-eslint/no-explicit-any": "off",
      "vue/no-mutating-props": ["error", { shallowOnly: true }],
      "vue/multi-word-component-names": "off",
    },
  },
  {
    extends: [eslint.configs.recommended, ...tseslint.configs.recommended],
    files: ["tests/**/*.ts"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: {
        ...globals.browser,
        ...globals.node,
        ...globals.vitest,
      },
    },
    rules: {
      "@typescript-eslint/no-unused-vars": unusedVarsRule,
      "@typescript-eslint/no-explicit-any": "off",
    },
  },
);
