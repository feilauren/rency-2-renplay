from crewai import Task
from agents import cypress_reviewer, playwright_refactorer


def build_tasks(cypress_code: str, output_path: str, filename: str) -> tuple[Task, Task]:
    """
    Build the review and refactor tasks for a single Cypress file.

    Args:
        cypress_code: Raw content of the Cypress test file.
        output_path: Directory to write output files into.
        filename: Base filename (no extension) for output files.

    Returns:
        (task_review, task_refactor) — in execution order.
    """
    task_review = Task(
        description=(
            "Review the following Cypress test file and produce structured feedback.\n\n"
            "```javascript\n"
            "{cypress_code}\n"
            "```\n\n"
            "Evaluate against these criteria:\n"
            "1. Selector quality — data-cy/data-testid vs fragile CSS or XPath\n"
            "2. Assertion completeness — are all important states asserted?\n"
            "3. Edge case coverage — negative paths, network errors, validation errors\n"
            "4. Test isolation — no shared mutable state or order dependencies\n"
            "5. Hardcoded values — credentials, magic strings, absolute URLs\n"
            "6. Use of cy.wait() with hardcoded ms delays\n"
            "7. Missing test scenarios based on what the file appears to be testing\n\n"
            "Output a structured markdown review with these exact sections:\n"
            "## Overall Assessment\n"
            "## Issues Found\n"
            "(numbered list, each prefixed with severity: HIGH / MEDIUM / LOW)\n"
            "## Missing Coverage\n"
            "(bullet list)\n"
            "## Recommendations for Playwright Refactor\n"
            "(bullet list of specific changes to make during migration)"
        ),
        expected_output=(
            "Structured markdown review with Overall Assessment, Issues Found "
            "(numbered with HIGH/MEDIUM/LOW severity), Missing Coverage, and "
            "Recommendations for Playwright Refactor sections."
        ),
        agent=cypress_reviewer,
        output_file=f"{output_path}/review_{filename}.md",
    )

    task_refactor = Task(
        description=(
            "Using the Cypress test code and the review notes from the previous task, "
            "produce a complete, idiomatic Playwright TypeScript test file.\n\n"
            "Original Cypress code:\n"
            "```javascript\n"
            "{cypress_code}\n"
            "```\n\n"
            "Translation rules to follow:\n"
            "- cy.visit(url) → await page.goto(url)\n"
            "- cy.get('[data-cy=x]') or cy.get('[data-testid=x]') → page.getByTestId('x')\n"
            "- cy.get('.css-selector') → page.locator('.css-selector')\n"
            "- cy.intercept(method, url, response) → await page.route(url, route => route.fulfill(...))\n"
            "- .should('be.visible') → await expect(locator).toBeVisible()\n"
            "- .should('have.text', x) → await expect(locator).toHaveText(x)\n"
            "- .should('have.value', x) → await expect(locator).toHaveValue(x)\n"
            "- .should('not.exist') → await expect(locator).not.toBeVisible()\n"
            "- .type(text) → await locator.fill(text)\n"
            "- .click() → await locator.click()\n"
            "- .clear() → await locator.clear()\n"
            "- beforeEach(() => {}) → test.beforeEach(async ({ page }) => {})\n"
            "- describe('...', () => {}) → test.describe('...', () => {})\n"
            "- it('...', () => {}) → test('...', async ({ page }) => {})\n\n"
            "Additional requirements:\n"
            "- Use `import {{ test, expect }} from '@playwright/test'` at the top\n"
            "- All test functions must be async\n"
            "- Address all HIGH and MEDIUM severity issues from the review notes\n"
            "- Replace any hardcoded waits with proper Playwright auto-waiting\n"
            "- Use page.getByTestId() wherever data-cy or data-testid selectors were used\n"
            "- Output only the TypeScript file content — no explanation, no markdown fences"
        ),
        expected_output=(
            "A complete, runnable Playwright TypeScript test file with @playwright/test "
            "imports, async/await throughout, and review issues addressed."
        ),
        agent=playwright_refactorer,
        context=[task_review],
        output_file=f"{output_path}/{filename}.spec.ts",
    )

    return task_review, task_refactor
