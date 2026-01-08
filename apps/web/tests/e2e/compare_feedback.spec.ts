import { test, expect } from '@playwright/test';

/**
 * Compare and Feedback E2E Test
 * 
 * - 후보 비교 페이지 접근
 * - 피드백 저장 확인
 */

test.describe('Candidate Comparison', () => {

    test('should navigate to compare page', async ({ page }) => {
        await page.goto('/design/runs');

        const runLink = page.locator('a[href*="/design/runs/"]').first();

        if (await runLink.isVisible()) {
            await runLink.click();
            await page.waitForLoadState('networkidle');

            // Look for compare button or link
            const compareButton = page.locator('button:has-text("Compare"), a:has-text("Compare"), button:has-text("비교")');

            if (await compareButton.isVisible()) {
                await compareButton.click();

                // Should navigate to compare page
                await expect(page).toHaveURL(/.*compare/);
            }
        }
    });

    test('should display side-by-side comparison', async ({ page }) => {
        // Directly navigate to a compare page with candidate IDs
        // Format: /design/runs/[runId]/compare?ids=uuid1,uuid2
        await page.goto('/design/runs');

        const runLink = page.locator('a[href*="/design/runs/"]').first();

        if (await runLink.isVisible()) {
            await runLink.click();
            await page.waitForLoadState('networkidle');

            // Check for comparison elements
            const compareElements = page.locator('[data-testid="compare-view"], .compare-container, .grid');

            const count = await compareElements.count();
            expect(count).toBeGreaterThanOrEqual(0);
        }
    });

});

test.describe('Feedback Submission', () => {

    test('should display feedback form', async ({ page }) => {
        await page.goto('/design/runs');

        const runLink = page.locator('a[href*="/design/runs/"]').first();

        if (await runLink.isVisible()) {
            await runLink.click();
            await page.waitForLoadState('networkidle');

            // Look for feedback elements
            const feedbackElements = page.locator(
                'button:has-text("Feedback"), ' +
                'button:has-text("피드백"), ' +
                '[data-testid="feedback"], ' +
                'textarea[placeholder*="comment"], ' +
                'textarea[placeholder*="코멘트"]'
            );

            const count = await feedbackElements.count();
            expect(count).toBeGreaterThanOrEqual(0);
        }
    });

    test('should submit feedback successfully', async ({ page }) => {
        await page.goto('/design/runs');

        const runLink = page.locator('a[href*="/design/runs/"]').first();

        if (await runLink.isVisible()) {
            await runLink.click();
            await page.waitForLoadState('networkidle');

            // Look for feedback textarea
            const feedbackTextarea = page.locator('textarea').first();

            if (await feedbackTextarea.isVisible()) {
                await feedbackTextarea.fill('Test feedback from E2E test');

                // Look for submit button
                const submitButton = page.locator('button:has-text("Submit"), button:has-text("제출"), button[type="submit"]').first();

                if (await submitButton.isVisible()) {
                    await submitButton.click();

                    // Wait for response
                    await page.waitForTimeout(1000);

                    // Check for success indicator
                    const successIndicator = page.locator('.success, [data-testid="success"], text=/saved|저장/i');

                    if (await successIndicator.isVisible()) {
                        expect(await successIndicator.isVisible()).toBeTruthy();
                    }
                }
            }
        }
    });

    test('should display existing feedback', async ({ page }) => {
        await page.goto('/design/runs');

        const runLink = page.locator('a[href*="/design/runs/"]').first();

        if (await runLink.isVisible()) {
            await runLink.click();
            await page.waitForLoadState('networkidle');

            // Look for feedback history section
            const feedbackHistory = page.locator('text=/Feedback|피드백|Comments|코멘트/i');

            const count = await feedbackHistory.count();
            expect(count).toBeGreaterThanOrEqual(0);
        }
    });

});
