import { mkdir, rename, rm } from "node:fs/promises";
import path from "node:path";
import { chromium } from "@playwright/test";

const outputDir = path.resolve("docs/assets/demo-recording");
const finalVideo = path.resolve("docs/assets/anime-oscilloscope-demo.webm");
await rm(outputDir, { recursive: true, force: true });
await mkdir(outputDir, { recursive: true });

const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width: 1280, height: 720 },
  recordVideo: { dir: outputDir, size: { width: 1280, height: 720 } },
});
const page = await context.newPage();
const video = page.video();

await page.goto("http://127.0.0.1:5173");
await page.waitForTimeout(1800);
await page.getByRole("link", { name: "综合榜单", exact: true }).click();
await page.waitForTimeout(1400);
await page.getByLabel("门槛").selectOption("threshold");
await page.waitForTimeout(1200);
await page.getByRole("link", { name: "评分走势", exact: true }).click();
await page.waitForTimeout(1700);
await page.getByRole("link", { name: "AI 找番", exact: true }).click();
await page.waitForTimeout(900);
await page.getByRole("button", { name: "分析这句话", exact: true }).click();
await page.getByText("hash-512-demo", { exact: true }).waitFor();
await page.waitForTimeout(1800);
await page.getByRole("link", { name: "从夯到拉", exact: true }).click();
await page.waitForTimeout(1000);
await page.getByLabel("选择 极光频率").check();
await page.getByRole("button", { name: "加入所选（1）", exact: true }).click();
await page.getByLabel("移动 极光频率").selectOption("s");
await page.getByLabel("移动 极光频率").scrollIntoViewIfNeeded();
await page.waitForTimeout(1800);

await page.close();
await context.close();
await browser.close();

if (!video) throw new Error("Playwright video recording is unavailable");
const recordedPath = await video.path();
await rm(finalVideo, { force: true });
await rename(recordedPath, finalVideo);
await rm(outputDir, { recursive: true, force: true });
console.log(finalVideo);
