export default [
  {
    files: ['static/js/**/*.js', 'tests/js/**/*.test.js'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
    },
    rules: {
      'no-unused-vars': 'warn',
      'no-undef': 'off',
      'semi': ['error', 'always'],
    },
  },
];
