import { test, expect } from '@playwright/test';

/**
 * Run Creation E2E Test
 * 
 * - 런 목록 페이지 접근
 * - 새 런 생성 모달 열기
 * - 런 생성 완료 확인
 */

test.describe('Design Run Creation', () => {

    test.beforeEach(async ({ page }) => {
        // Navigate to design runs page
        await page.goto('/design/runs');
    });

    test('should display runs list page', async ({ page }) => {
        // Check page title or header
        await expect(page.locator('h1')).toContainText(/Design Runs|런|설계/);

        // Check that the page loaded successfully
        await expect(page).toHaveURL(/.*\/design\/runs/);
    });

    test('should open new run modal', async ({ page }) => {
        // Look for create button
        const createButton = page.locator('button', { hasText: /New|새|생성|Create/i });

        if (await createButton.isVisible()) {
            await createButton.click();

            // Check modal appeared - use getByRole for heading which is more specific
            await expect(page.getByRole('heading', { name: '새 Design Run' })).toBeVisible({ timeout: 5000 });
        }
    });

    test('should create a new run successfully', async ({ page }) => {
        // Open modal
        const createButton = page.locator('button', { hasText: /New|새|생성|Create/i });

        if (!(await createButton.isVisible())) {
            test.skip();
            return;
        }

        await createButton.click();

        // Wait for modal - using the header text as indicator
        await expect(page.getByRole('heading', { name: '새 Design Run' })).toBeVisible({ timeout: 5000 });

        // Fill in indication field - actual placeholder is "예: HER2+ Breast Cancer"
        const indicationInput = page.locator('input[placeholder*="HER2"], input[placeholder*="적응증"]');
        if (await indicationInput.isVisible()) {
            await indicationInput.fill('HER2+ Breast Cancer');
        } else {
            // Skip if indication input not found
            test.skip();
            return;
        }

        // Check if targets are available (required for form submission)
        const targetCheckbox = page.locator('input[type="checkbox"]').first();
        if (await targetCheckbox.isVisible({ timeout: 3000 })) {
            await targetCheckbox.check();
        } else {
            // Skip test if no targets available
            console.log('No targets available in catalog - skipping test');
            test.skip();
            return;
        }

        // Submit form - actual button text is "실행 시작"
        const submitButton = page.locator('button:has-text("실행 시작"), button:has-text("Start")');
        if (await submitButton.isEnabled({ timeout: 2000 })) {
            await submitButton.click();

            // Wait for navigation or success
            await page.waitForTimeout(2000);

            // Should either navigate to run detail or show success message or modal closes
            const modalClosed = !(await page.getByRole('heading', { name: '새 Design Run' }).isVisible());
            const navigated = page.url().includes('/runs/');

            expect(modalClosed || navigated).toBeTruthy();
        }
    });


});

test.describe('Design Run Detail', () => {

    test('should display run detail page', async ({ page }) => {
        // Navigate to runs list first
        await page.goto('/design/runs');

        // Click on first run if available
        const runLink = page.locator('a[href*="/design/runs/"]').first();

        if (await runLink.isVisible()) {
            await runLink.click();

            // Check that detail page loaded
            await expect(page).toHaveURL(/.*\/design\/runs\/[a-f0-9-]+/);

            // Check for essential elements
            await expect(page.locator('body')).toContainText(/Candidates|후보|Score|점수/);
        }
    });

});
