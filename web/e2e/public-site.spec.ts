import { expect, test } from "@playwright/test";

test("public site and demo are reachable", async ({ page }) => {
  await page.route("**/api/health", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        ok: true,
        app_env: "e2e",
        template: "sc-th-word",
        capabilities: { docx_export: true, profile: "undergraduate" },
        limits: { max_docx_size_bytes: 20 * 1024 * 1024, max_text_precheck_chars: 80_000 },
      }),
    });
  });

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Format your thesis with AI." })).toBeVisible();
  await expect(page.getByRole("link", { name: "Forma 首页" })).toBeVisible();
  await expect(page.getByLabel("论文格式要求输入框")).toBeVisible();
  await expect(page.getByRole("button", { name: "上传 .docx 文件" })).toBeVisible();
  await expect(page.getByText("Ready when your thesis is.")).toBeVisible();

  await page.getByRole("link", { name: "Guide", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Use Forma with a clear boundary." })).toBeVisible();
  await expect(page.getByText("Supported files")).toBeVisible();

  await page.goto("/#/workbench-demo");
  await expect(page.getByRole("heading", { name: "Format your thesis with AI." })).toBeVisible();
  await expect(page.getByText("SCNU Thesis Agent Workbench Demo")).toHaveCount(0);
});
