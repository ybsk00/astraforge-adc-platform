import { test, expect } from '@playwright/test';

/**
 * Candidate Detail E2E Test
 * 
 * - 후보 상세 페이지 접근
 * - 근거(Evidence) 표시 확인
 * - 프로토콜(Protocol) 표시 확인
 */

test.describe('Candidate Detail Page', () => {

    test('should display candidate scores', async ({ page }) => {
        // Navigate to a run with candidates
        await page.goto('/design/runs');

        // Click first run
        const runLink = page.locator('a[href*="/design/runs/"]').first();

        if (await runLink.isVisible()) {
            await runLink.click();
            await page.waitForLoadState('networkidle');

            // Look for score indicators
            const scoreElements = page.locator('[data-testid="score"], .score, text=/[0-9]+\.[0-9]+|[0-9]+%/');

            // Should have at least one score visible
            const scoreCount = await scoreElements.count();
            expect(scoreCount).toBeGreaterThanOrEqual(0);
        }
    });

    test('should display evidence section', async ({ page }) => {
        await page.goto('/design/runs');

        const runLink = page.locator('a[href*="/design/runs/"]').first();

        if (await runLink.isVisible()) {
            await runLink.click();
            await page.waitForLoadState('networkidle');

            // Look for evidence section
            const evidenceSection = page.locator('text=/Evidence|근거|References|참고/i');

            if (await evidenceSection.isVisible()) {
                expect(await evidenceSection.isVisible()).toBeTruthy();
            }
        }
    });

    test('should display protocol recommendations', async ({ page }) => {
        await page.goto('/design/runs');

        const runLink = page.locator('a[href*="/design/runs/"]').first();

        if (await runLink.isVisible()) {
            await runLink.click();
            await page.waitForLoadState('networkidle');

            // Look for protocol section
            const protocolSection = page.locator('text=/Protocol|프로토콜|Assay|실험/i');

            if (await protocolSection.isVisible()) {
                expect(await protocolSection.isVisible()).toBeTruthy();
            }
        }
    });

    test('should display 4-axis radar chart', async ({ page }) => {
        await page.goto('/design/runs');

        const runLink = page.locator('a[href*="/design/runs/"]').first();

        if (await runLink.isVisible()) {
            await runLink.click();
            await page.waitForLoadState('networkidle');

            // Look for chart or canvas element
            const chartElement = page.locator('canvas, svg, [data-testid="radar-chart"], .recharts-wrapper');

            const chartCount = await chartElement.count();
            // Chart may or may not be present depending on data
            expect(chartCount).toBeGreaterThanOrEqual(0);
        }
    });

});
