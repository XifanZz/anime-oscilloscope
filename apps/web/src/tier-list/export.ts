import { tierDefinitions, type TierLibrary } from "./model";

export type ExportLayout = { width: number; height: number; rowHeights: number[] };

export function buildExportLayout(library: TierLibrary): ExportLayout {
  const width = 1200;
  const cardsPerRow = 6;
  const rowHeights = tierDefinitions.map((tier) => Math.max(170, Math.ceil(library.entries[tier.id].length / cardsPerRow) * 150 + 36));
  return { width, height: 150 + rowHeights.reduce((sum, height) => sum + height, 0) + 70, rowHeights };
}

export async function exportTierList(library: TierLibrary): Promise<void> {
  const layout = buildExportLayout(library);
  const canvas = document.createElement("canvas");
  canvas.width = layout.width;
  canvas.height = layout.height;
  const context = canvas.getContext("2d");
  if (!context) throw new Error("浏览器不支持画布导出");

  context.fillStyle = "#07131f";
  context.fillRect(0, 0, canvas.width, canvas.height);
  context.fillStyle = "#e9f4f3";
  context.font = "700 42px sans-serif";
  context.fillText(library.name, 48, 68);
  context.fillStyle = "#7ef7c7";
  context.font = "16px monospace";
  context.fillText("ANIME OSCILLOSCOPE · 从夯到拉", 48, 102);

  let rowY = 130;
  tierDefinitions.forEach((tier, tierIndex) => {
    const rowHeight = layout.rowHeights[tierIndex];
    context.fillStyle = tier.color;
    context.fillRect(32, rowY, 120, rowHeight - 8);
    context.fillStyle = "#07131f";
    context.font = "900 46px sans-serif";
    context.textAlign = "center";
    context.fillText(tier.label, 92, rowY + 72);
    context.font = "13px sans-serif";
    context.fillText(tier.description, 92, rowY + 100);
    context.textAlign = "left";

    library.entries[tier.id].forEach((anime, index) => {
      const column = index % 6;
      const line = Math.floor(index / 6);
      const x = 174 + column * 164;
      const y = rowY + 18 + line * 150;
      context.fillStyle = "#112b39";
      context.fillRect(x, y, 146, 118);
      context.fillStyle = tier.color;
      context.fillRect(x, y, 146, 5);
      context.fillStyle = "#e9f4f3";
      context.font = "700 17px sans-serif";
      const title = anime.name_cn ?? anime.canonical_name;
      context.fillText(title.length > 9 ? `${title.slice(0, 9)}…` : title, x + 12, y + 50);
      context.fillStyle = "#88a3aa";
      context.font = "12px sans-serif";
      context.fillText(`${anime.media_type.toUpperCase()} · ${anime.air_date.slice(0, 4)}`, x + 12, y + 82);
    });
    rowY += rowHeight;
  });

  context.fillStyle = "#607b82";
  context.font = "12px monospace";
  context.fillText("仅保存在本地浏览器 · anime-oscilloscope", 48, canvas.height - 28);
  const link = document.createElement("a");
  link.href = canvas.toDataURL("image/png");
  link.download = `${library.name.replace(/[\\/:*?"<>|]/g, "-")}-tier-list.png`;
  document.body.appendChild(link);
  link.click();
  link.remove();
}
