const { chromium } = require("playwright");

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 390, height: 844 }, isMobile: true });
  await page.goto("http://127.0.0.1:8501", { waitUntil: "networkidle", timeout: 60000 });
  await page.getByText("Sign in or create an account").waitFor({ state: "visible", timeout: 15000 });
  await page.locator('input[aria-label="Email"]').first().fill("mira@example.com");
  await page.locator('input[aria-label="Password"]').first().fill("student123");
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.getByText("Dashboard", { exact: false }).first().waitFor({ state: "visible", timeout: 15000 });
  await page.waitForTimeout(8000);
  await page.screenshot({ path: "tests/mobile-dashboard.png", fullPage: true });
  await browser.close();
  console.log("Mobile smoke test passed.");
})();
