import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { App } from "./App";
import { healthPayload, jsonResponse, samplePrecheck } from "./test/fixtures";

function mockFetch(handler?: (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>) {
  const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    if (handler) return handler(input, init);
    return jsonResponse(healthPayload);
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("App smoke", () => {
  afterEach(() => {
    window.history.replaceState(null, "", "/");
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("renders the single-page formatter shell", async () => {
    mockFetch();

    const { container } = render(<App />);

    expect(screen.getByRole("heading", { level: 1, name: /论文格式，/ })).toBeInTheDocument();
    expect(screen.getByText("SCNU Thesis Formatter")).toBeInTheDocument();
    expect(screen.getByText("上传 `.docx` 或粘贴正文，完成预检后导出规范化 Word。")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "上传 .docx 文件" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "开始预检" })).toBeInTheDocument();
    expect(screen.getByPlaceholderText("或直接粘贴论文正文")).toBeInTheDocument();
    expect(screen.queryByText("查看 Workbench")).not.toBeInTheDocument();
    expect(screen.queryByText("English")).not.toBeInTheDocument();

    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input.tabIndex).toBe(-1);
    expect(input).toHaveAttribute("aria-hidden", "true");

    await waitFor(() => expect(fetch).toHaveBeenCalledWith("/api/health", undefined));
  });

  it("strips legacy hash routes and renders the formatter", async () => {
    mockFetch();
    window.history.replaceState(null, "", "/#/workbench-demo");

    render(<App />);

    expect(await screen.findByRole("heading", { level: 1, name: /论文格式，/ })).toBeInTheDocument();
    await waitFor(() => expect(window.location.hash).toBe(""));
  });

  it("shows inline guidance when trying to submit empty content", async () => {
    const fetchMock = mockFetch();

    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "开始预检" }));

    expect(await screen.findByText("内容为空，无法开始处理。")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("shows the selected docx filename after upload", async () => {
    mockFetch();
    const { container } = render(<App />);

    const uploadButton = screen.getByRole("button", { name: "上传 .docx 文件" });
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const clickSpy = vi.spyOn(input, "click");
    const file = new File(["docx"], "paper.docx", {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });

    fireEvent.click(uploadButton);
    expect(clickSpy).toHaveBeenCalledTimes(1);
    fireEvent.change(input, { target: { files: [file] } });

    expect(await screen.findByText("paper.docx")).toBeInTheDocument();
  });

  it("shows an inline error after selecting an invalid file", async () => {
    mockFetch();
    const { container } = render(<App />);

    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(["bad"], "paper.pdf", { type: "application/pdf" });

    fireEvent.change(input, { target: { files: [file] } });

    expect(await screen.findByText("当前仅支持上传 `.docx` 文件。")).toBeInTheDocument();
  });

  it("shows source conflict when clicking upload after typing text", async () => {
    mockFetch();
    const { container } = render(<App />);
    fireEvent.change(screen.getByLabelText("论文正文输入框"), {
      target: { value: "已有内容" },
    });

    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const clickSpy = vi.spyOn(input, "click");
    fireEvent.click(screen.getByRole("button", { name: "上传 .docx 文件" }));

    expect(clickSpy).not.toHaveBeenCalled();
    expect(await screen.findByText("请先清空当前输入，再切换输入方式。")).toBeInTheDocument();
  });

  it("opens the apple-style precheck sheet after text precheck succeeds", async () => {
    mockFetch((input) => {
      const url = String(input);
      if (url.includes("/api/public/precheck/text")) return jsonResponse(samplePrecheck());
      return jsonResponse(healthPayload);
    });

    render(<App />);

    fireEvent.change(screen.getByLabelText("论文正文输入框"), {
      target: { value: "结构化映射示例论文\n\n摘要\n本文展示结构化映射后的论文导出流程，并说明新的预检主线。\n\n引言\n这是足够长的正文内容，用于通过预检。".repeat(10) },
    });
    fireEvent.click(screen.getByRole("button", { name: "开始预检" }));

    expect(await screen.findByRole("dialog", { name: "检查完成" })).toBeInTheDocument();
    expect(screen.getByText("可导出")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "导出 Word" })).toBeEnabled();
  });

  it("keeps input after closing the precheck sheet", async () => {
    mockFetch((input) => {
      const url = String(input);
      if (url.includes("/api/public/precheck/text")) return jsonResponse(samplePrecheck());
      return jsonResponse(healthPayload);
    });

    render(<App />);

    const textarea = screen.getByLabelText("论文正文输入框");
    fireEvent.change(textarea, {
      target: { value: "我的论文标题\n\n摘要\n这是摘要。" },
    });
    fireEvent.click(screen.getByRole("button", { name: "开始预检" }));

    await screen.findByRole("dialog", { name: "检查完成" });
    fireEvent.click(screen.getByRole("button", { name: "返回" }));

    await waitFor(() => expect(screen.queryByRole("dialog", { name: "检查完成" })).not.toBeInTheDocument());
    expect(screen.getByLabelText("论文正文输入框")).toHaveValue("我的论文标题\n\n摘要\n这是摘要。");
  });
});
