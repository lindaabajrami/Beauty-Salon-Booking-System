const { chromium } = require("playwright");

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  await page.goto("http://127.0.0.1:8501", { waitUntil: "networkidle", timeout: 60000 });
  await page.locator('input[aria-label="Email"]').first().fill("mira@example.com");
  await page.locator('input[aria-label="Password"]').first().fill("student123");
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.getByText("Dashboard", { exact: false }).first().waitFor({ state: "visible", timeout: 15000 });
  await page.locator('input[aria-label="Admin key"]').fill("salon-admin-key");
  await page.waitForTimeout(10000);
  const plotlyCount = await page.locator(".js-plotly-plot").count();
  const svgCount = await page.locator("svg").count();
  await page.screenshot({ path: "tests/dashboard-after-wait.png", fullPage: true });
  console.log(`plotly=${plotlyCount} svg=${svgCount}`);
  await browser.close();
})();
