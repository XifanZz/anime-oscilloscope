import path from "node:path";
import { expect, test } from "@playwright/test";

test("ranking, history, and source freshness render from the API", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("status").filter({ hasText: "演示数据模式" })).toBeVisible();
  await expect(page.getByRole("table", { name: "综合排行榜" })).toContainText("极光频率");
  await expect(page.getByRole("img", { name: "Bangumi、MAL 与综合评分历史曲线及分集时间轴" })).toBeVisible();
  await expect(page.getByText("使用上次成功快照", { exact: true })).toBeVisible();
});

test("natural-language search discloses its engine and reasons", async ({ page }) => {
  await page.goto("/#ai-search");
  await page.getByRole("button", { name: "分析这句话" }).click();

  await expect(page.getByText("hash-512-demo", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "潮汐档案" })).toBeVisible();
  await expect(page.getByText("制作地区匹配：CN / JP", { exact: true })).toBeVisible();
});

test("tier placement survives a page reload", async ({ page }) => {
  await page.goto("/#tier-list");
  await page.getByLabel("选择 极光频率").check();
  await page.getByRole("button", { name: "加入所选（1）" }).click();
  await page.getByLabel("移动 极光频率").selectOption("s");
  await expect.poll(() => page.evaluate(() => localStorage.getItem("anime-oscilloscope:tier-libraries:v1"))).toContain('"s":[{"id":"demo-aurora"');
  await page.reload();

  await expect(page.getByLabel("移动 极光频率")).toHaveValue("s");
  await expect(page.getByRole("tab", { name: /我的片库 1 部/ })).toBeVisible();
});

test("local Bilibili file import requires explicit confirmation", async ({ page }) => {
  await page.goto("/#tier-list");
  const fileInput = page.getByLabel("选择B站片单文件");
  await expect(fileInput).toBeEnabled();
  await fileInput.setInputFiles(
    path.resolve("examples/bilibili-history.sample.csv"),
  );

  const confirmAurora = page.getByLabel("确认导入 极光频率");
  await expect(confirmAurora).toBeVisible();
  await expect(page.getByRole("button", { name: "将已确认的 0 部加入当前片库" })).toBeDisabled();
  await confirmAurora.check();
  await page.getByRole("button", { name: "将已确认的 1 部加入当前片库" }).click();

  await expect(page.getByLabel("移动 极光频率")).toBeVisible();
});
