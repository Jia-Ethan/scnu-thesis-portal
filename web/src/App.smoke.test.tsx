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

function selectDocx(container: HTMLElement, filename = "paper.docx") {
  const input = container.querySelector('input[type="file"]') as HTMLInputElement;
  const file = new File(["docx"], filename, {
    type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  });
  fireEvent.change(input, { target: { files: [file] } });
  return file;
}

describe("App smoke", () => {
  afterEach(() => {
    window.history.replaceState(null, "", "/");
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("renders the thesis portal entry", async () => {
    mockFetch();

    const { container } = render(<App />);

    expect(screen.getByRole("heading", { level: 1, name: "Format your thesis with AI." })).toBeInTheDocument();
    expect(screen.getAllByText("Forma")).not.toHaveLength(0);
    expect(screen.getByLabelText("论文格式要求输入框")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "上传 .docx 文件" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Start preview" })).toBeInTheDocument();
    expect(screen.getByText("Ready when your thesis is.")).toBeInTheDocument();

    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input.tabIndex).toBe(-1);
    expect(input).toHaveAttribute("aria-hidden", "true");

    await waitFor(() => expect(fetch).toHaveBeenCalledWith("/api/health", undefined));
  });

  it("strips legacy hash routes and renders the portal", async () => {
    mockFetch();
    window.history.replaceState(null, "", "/#/workbench-demo");

    render(<App />);

    expect(await screen.findByRole("heading", { level: 1, name: "Format your thesis with AI." })).toBeInTheDocument();
    await waitFor(() => expect(window.location.hash).toBe(""));
  });

  it("renders the guide route", async () => {
    mockFetch();
    window.history.replaceState(null, "", "/#/guide");

    render(<App />);

    expect(screen.getByRole("heading", { level: 1, name: "Use Forma with a clear boundary." })).toBeInTheDocument();
    expect(screen.getByText("Supported files")).toBeInTheDocument();
    expect(screen.getByText("Privacy")).toBeInTheDocument();
  });

  it("shows inline guidance when trying to submit empty content", async () => {
    const fetchMock = mockFetch();

    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "Start preview" }));

    expect(await screen.findAllByText("请先粘贴格式要求，并上传 .docx 论文文件。")).not.toHaveLength(0);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("fills an example requirement and shows the selected docx filename", async () => {
    mockFetch();
    const { container } = render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "Example" }));
    expect(String((screen.getByLabelText("论文格式要求输入框") as HTMLTextAreaElement).value)).toContain("本科毕业论文");

    selectDocx(container, "paper.docx");
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

  it("shows the result panel after docx precheck succeeds", async () => {
    mockFetch((input) => {
      const url = String(input);
      if (url.includes("/api/public/precheck/docx")) return jsonResponse(samplePrecheck());
      return jsonResponse(healthPayload);
    });

    const { container } = render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "Example" }));
    selectDocx(container);
    fireEvent.click(screen.getByRole("button", { name: "Start preview" }));

    expect(await screen.findByText("Review before export.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Fix format" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Export Word" })).toBeEnabled();
  });
});
