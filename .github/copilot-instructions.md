# Copilot Instructions for bobada

## Project Overview

**bobada** is a Playwright end-to-end testing project focused on automated browser testing. The project tests SAML2 authentication flows against institutional SSO systems (USAL IdP integration).

## Key Architecture

- **Testing Framework**: Playwright 1.58.0 with TypeScript
- **Test Organization**: All tests reside in `./tests/` directory with `.spec.ts` suffix
- **Test Execution**: Runs against Chromium, Firefox, and WebKit by default
- **CI/CD**: GitHub Actions workflow triggers on push/PR to main/master branches

## Critical Developer Workflows

### Running Tests Locally
```bash
npm ci                                    # Install dependencies
npx playwright install --with-deps        # Install browser binaries
npx playwright test                       # Run all tests
npx playwright test --ui                  # Interactive UI mode
npx playwright test --debug               # Debug with inspector
```

### CI/CD Pipeline
Tests auto-run on GitHub Actions with:
- 2 retries on CI failures
- Serial execution (workers: 1)
- HTML report uploaded as artifact
- 30-day retention

## Project-Specific Patterns

### Test Structure
Each test file imports from `@playwright/test` and uses:
```typescript
import { test, expect } from '@playwright/test';

test('test name', async ({ page }) => {
  // page fixture provides browser automation
  await page.goto('https://...');
  await expect(page).toHaveTitle(/expected/);
});
```

### SAML2 Authentication Testing
Current test in [tests/example.spec.ts](tests/example.spec.ts) tests SAML2 SSO login with:
- Long encoded SAML requests as URL parameters
- RelayState redirects (federated identity)
- Signature validation via RSA-SHA256

When adding new SAML2 tests, preserve the full encoded request/response cycle.

## Configuration Files

- **playwright.config.ts**: Defines test directory, parallel execution, retry logic, and HTML reporting
- **package.json**: Contains Playwright and TypeScript dev dependencies
- **.github/workflows/playwright.yml**: CI/CD automation

## Common Commands

| Task | Command |
|------|---------|
| Install deps | `npm ci` |
| Run tests | `npx playwright test` |
| Debug tests | `npx playwright test --debug` |
| Open last report | `npx playwright show-report` |
| Update snapshots | `npx playwright test --update-snapshots` |

## Notes for Agents

- Trace collection is enabled on first-retry to diagnose failures
- BaseURL is commented out; tests use full URLs
- Mobile and alternative browser profiles are available but disabled by default
- Always use `await` with Playwright async operations
