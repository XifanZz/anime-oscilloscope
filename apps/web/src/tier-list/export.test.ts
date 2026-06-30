import { vi } from "vitest";
import { exportTierList } from "./export";
import { createLibrary } from "./model";

describe("tier list PNG export", () => {
  it("renders a canvas and triggers a synchronous PNG download", async () => {
    const context = {
      fillStyle: "",
      font: "",
      textAlign: "left",
      fillRect: vi.fn(),
      fillText: vi.fn(),
    };
    const getContext = vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue(context as unknown as CanvasRenderingContext2D);
    const toDataURL = vi.spyOn(HTMLCanvasElement.prototype, "toDataURL").mockReturnValue("data:image/png;base64,dGVzdA==");
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);

    await exportTierList(createLibrary("测试/片库", "export"));

    expect(context.fillRect).toHaveBeenCalled();
    expect(toDataURL).toHaveBeenCalledWith("image/png");
    expect(click).toHaveBeenCalledOnce();
    getContext.mockRestore();
    toDataURL.mockRestore();
    click.mockRestore();
  });
});
