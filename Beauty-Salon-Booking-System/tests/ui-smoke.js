const { chromium } = require("playwright");

const APP_URL = "http://127.0.0.1:8501";

async function expectVisible(page, text, label = text) {
  const locator = page.getByText(text, { exact: false }).first();
  await locator.waitFor({ state: "visible", timeout: 15000 });
  console.log(`ok: ${label}`);
}

async function clickNav(page, name) {
  await page.getByText(name, { exact: true }).first().click();
  await expectVisible(page, name, `${name} page`);
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const errors = [];

  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") {
      errors.push(message.text());
    }
  });

  await page.goto(APP_URL, { waitUntil: "networkidle", timeout: 60000 });
  await expectVisible(page, "Sign in or create an account", "auth gate");
  await page.screenshot({ path: "tests/auth-screen.png", fullPage: true });

  if (await page.getByText("Dashboard", { exact: true }).count()) {
    throw new Error("Guest can see Dashboard navigation before signing in.");
  }

  await page.locator('input[aria-label="Email"]').first().fill("mira@example.com");
  await page.locator('input[aria-label="Password"]').first().fill("student123");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expectVisible(page, "Dashboard", "dashboard after login");
  await page.locator('input[aria-label="Admin key"]').fill("salon-admin-key");
  await page.waitForTimeout(500);
  await page.screenshot({ path: "tests/dashboard.png", fullPage: true });

  await clickNav(page, "Services");
  await expectVisible(page, "Signature Facial", "seeded service");
  await page.screenshot({ path: "tests/services.png", fullPage: true });
  const images = await page.locator("img").count();
  if (images < 5) {
    throw new Error(`Expected at least 5 seeded service images, found ${images}.`);
  }

  await clickNav(page, "Appointments");
  await expectVisible(page, "Create appointment", "appointment create form");

  await clickNav(page, "Customers");
  await expectVisible(page, "Create customer", "customer create form");

  await clickNav(page, "Staff");
  await expectVisible(page, "Create staff member", "staff create form");

  await clickNav(page, "Profile");
  await expectVisible(page, "Save profile", "profile form");

  await clickNav(page, "Admin");
  await expectVisible(page, "API key is valid", "admin key validation");

  await page.getByRole("button", { name: "Sign out" }).click();
  await expectVisible(page, "Sign in or create an account", "sign out returns auth gate");

  if (errors.length) {
    throw new Error(`Browser errors detected:\n${errors.join("\n")}`);
  }

  await browser.close();
  console.log("UI smoke test passed.");
})().catch(async (error) => {
  console.error(error);
  process.exit(1);
});
