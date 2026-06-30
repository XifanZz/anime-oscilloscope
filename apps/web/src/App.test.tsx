import { render, screen } from "@testing-library/react";
import App from "./App";

describe("App", () => {
  it("introduces the product and current implementation phase", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: /听见评分的噪声/ })).toBeInTheDocument();
    expect(screen.getAllByText("番剧示波器").length).toBeGreaterThan(0);
    expect(screen.getByText("骨架与设计系统")).toBeInTheDocument();
  });

  it("labels preview rankings as non-live data", () => {
    render(<App />);

    expect(screen.getByText(/第一阶段的界面设计数据/)).toBeInTheDocument();
    expect(screen.getByText("演示动画 α")).toBeInTheDocument();
  });
});
