import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { App } from "./App";
import { healthPayload, jsonResponse, samplePrecheck, sampleThesis } from "./test/fixtures";

function mockFetch(handler: (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>) {
  const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => handler(input, init));
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function deferredResponse() {
  let resolve!: (value: Response) => void;
  const promise = new Promise<Response>((resolver) => {
    resolve = resolver;
  });
  return { promise, resolve };
}

async function prepareInput(container: HTMLElement) {
  fireEvent.click(screen.getByRole("button", { name: "Example" }));
  const input = container.querySelector('input[type="file"]') as HTMLInputElement;
  const file = new File(["docx"], "paper.docx", {
    type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  });
  fireEvent.change(input, { target: { files: [file] } });
  await screen.findByText("paper.docx");
}

describe("App business flow", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("shows a backend precheck error below the portal surface", async () => {
    mockFetch((input) => {
      const url = String(input);
      if (url.includes("/api/public/precheck/docx")) {
        return jsonResponse({ error_code: "PARSE_FAILED", error_message: "解析失败" }, false);
      }
      return jsonResponse(healthPayload);
    });

    const { container } = render(<App />);
    await prepareInput(container);
    fireEvent.click(screen.getByRole("button", { name: "Start preview" }));

    expect(await screen.findByText("无法完成结构识别，请调整输入内容后重试。")).toBeInTheDocument();
  });

  it("keeps export enabled while clearly showing remaining issues", async () => {
    mockFetch((input) => {
      const url = String(input);
      if (url.includes("/api/public/precheck/docx")) {
        return jsonResponse(
          samplePrecheck({
            summary: {
              can_confirm: false,
              blocking_count: 2,
              warning_count: 1,
              info_count: 2,
              blocking_message: "当前仍有 2 项阻塞问题，暂时无法导出。",
              warning_message: "另有 1 项警告，其中缺失章节会按留白位保留，复杂元素需人工复核。",
            },
            issues: [
              {
                id: "body-missing",
                code: "BODY_MISSING",
                severity: "blocking",
                block: "body",
                title: "正文主体不足",
                message: "正文结构仍需人工留意。",
                block_id: null,
                source_span: null,
                rule_source_id: null,
                suggested_action: null,
              },
            ],
          }),
        );
      }
      return jsonResponse(healthPayload);
    });

    const { container } = render(<App />);
    await prepareInput(container);
    fireEvent.click(screen.getByRole("button", { name: "Start preview" }));

    expect(await screen.findByRole("button", { name: "Export Word" })).toBeEnabled();
    expect(screen.getAllByText("正文结构仍需人工留意。")).not.toHaveLength(0);
  });

  it("applies the placeholder repair state before export", async () => {
    mockFetch((input) => {
      const url = String(input);
      if (url.includes("/api/public/precheck/docx")) {
        return jsonResponse(samplePrecheck({ thesis: sampleThesis() }));
      }
      return jsonResponse(healthPayload);
    });

    const { container } = render(<App />);
    await prepareInput(container);
    fireEvent.click(screen.getByRole("button", { name: "Start preview" }));

    await screen.findByText("Review before export.");
    fireEvent.click(screen.getByRole("button", { name: "Fix format" }));

    expect(await screen.findByText("Fix flow reserved.")).toBeInTheDocument();
    expect(screen.getByText("当前为前端流程预览，后续可接入真实格式修复 Agent。")).toBeInTheDocument();
  });

  it("exports docx and resets after success", async () => {
    let jobPollCount = 0;
    const fetchMock = mockFetch((input) => {
      const url = String(input);
      if (url.includes("/api/public/precheck/docx")) {
        return jsonResponse(samplePrecheck({ thesis: sampleThesis() }));
      }
      if (url.endsWith("/api/public/export-jobs/docx")) {
        return jsonResponse({
          job_id: "job_1",
          export_id: "pub_1",
          status: "running",
          progress: 46,
          message: "正在生成 Word 文件。",
          download_url: null,
          report_url: null,
          expires_at: "2099-01-01T00:00:00",
          error_code: null,
        });
      }
      if (url.endsWith("/api/public/export-jobs/job_1")) {
        jobPollCount += 1;
        return jsonResponse({
          job_id: "job_1",
          export_id: "pub_1",
          status: "done",
          progress: 100,
          message: "导出完成。",
          download_url: "/api/public/exports/pub_1/download",
          report_url: "/api/public/exports/pub_1/report",
          expires_at: "2099-01-01T00:00:00",
          error_code: null,
        });
      }
      if (url.includes("/api/public/exports/pub_1/download")) {
        return jsonResponse({});
      }
      return jsonResponse(healthPayload);
    });

    Object.defineProperty(URL, "createObjectURL", { value: vi.fn(() => "blob:docx"), configurable: true });
    Object.defineProperty(URL, "revokeObjectURL", { value: vi.fn(), configurable: true });
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);

    const { container } = render(<App />);
    await prepareInput(container);
    fireEvent.click(screen.getByRole("button", { name: "Start preview" }));
    await screen.findByText("Review before export.");

    fireEvent.click(screen.getByRole("button", { name: "Export Word" }));

    expect(await screen.findByText(/正在生成 Word 文件/)).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("Ready when your thesis is.")).toBeInTheDocument());

    expect(jobPollCount).toBeGreaterThan(0);
    const exportCall = fetchMock.mock.calls.find(([input]) => String(input).includes("/api/public/export-jobs/docx"));
    expect(exportCall).toBeTruthy();
    const [, request] = exportCall as [RequestInfo | URL, RequestInit];
    const payload = JSON.parse(String(request.body));
    expect(payload.thesis.cover.title).toBe("结构化映射示例论文");
    expect(payload.export_token).toBe("v1:9999999999:test:signature");
  });

  it("keeps upload disabled while precheck is in flight", async () => {
    const precheckDeferred = deferredResponse();
    mockFetch((input) => {
      const url = String(input);
      if (url.includes("/api/public/precheck/docx")) {
        return precheckDeferred.promise;
      }
      return jsonResponse(healthPayload);
    });

    const { container } = render(<App />);
    await prepareInput(container);
    fireEvent.click(screen.getByRole("button", { name: "Start preview" }));

    const uploadButton = screen.getByRole("button", { name: /paper\.docx/ });
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const clickSpy = vi.spyOn(input, "click");

    await waitFor(() => expect(uploadButton).toBeDisabled());
    fireEvent.click(uploadButton);
    expect(clickSpy).not.toHaveBeenCalled();

    precheckDeferred.resolve(await jsonResponse(samplePrecheck()));
    expect(await screen.findByText("Review before export.")).toBeInTheDocument();
  });

  it("can cancel and retry an export job", async () => {
    let createCount = 0;
    mockFetch((input) => {
      const url = String(input);
      if (url.includes("/api/public/precheck/docx")) {
        return jsonResponse(samplePrecheck({ thesis: sampleThesis() }));
      }
      if (url.endsWith("/api/public/export-jobs/docx")) {
        createCount += 1;
        return jsonResponse({
          job_id: `job_${createCount}`,
          export_id: `pub_${createCount}`,
          status: "running",
          progress: 32,
          message: "正在生成 Word 文件。",
          download_url: null,
          report_url: null,
          expires_at: "2099-01-01T00:00:00",
          error_code: null,
        });
      }
      if (url.endsWith("/api/public/export-jobs/job_1/cancel")) {
        return jsonResponse({
          job_id: "job_1",
          export_id: "pub_1",
          status: "canceled",
          progress: 32,
          message: "导出已取消，可重新导出。",
          download_url: null,
          report_url: null,
          expires_at: "2099-01-01T00:00:00",
          error_code: "EXPORT_CANCELED",
        });
      }
      if (url.endsWith("/api/public/export-jobs/job_2")) {
        return jsonResponse({
          job_id: "job_2",
          export_id: "pub_2",
          status: "done",
          progress: 100,
          message: "导出完成。",
          download_url: "/api/public/exports/pub_2/download",
          report_url: "/api/public/exports/pub_2/report",
          expires_at: "2099-01-01T00:00:00",
          error_code: null,
        });
      }
      if (url.includes("/api/public/exports/pub_2/download")) {
        return jsonResponse({});
      }
      return jsonResponse(healthPayload);
    });

    Object.defineProperty(URL, "createObjectURL", { value: vi.fn(() => "blob:docx"), configurable: true });
    Object.defineProperty(URL, "revokeObjectURL", { value: vi.fn(), configurable: true });
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);

    const { container } = render(<App />);
    await prepareInput(container);
    fireEvent.click(screen.getByRole("button", { name: "Start preview" }));
    await screen.findByText("Review before export.");
    fireEvent.click(screen.getByRole("button", { name: "Export Word" }));

    expect(await screen.findByText("正在生成 Word 文件。")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "取消导出" }));
    expect(await screen.findByText("导出已取消，可重新导出。")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "重新导出" }));
    await waitFor(() => expect(screen.getByText("Ready when your thesis is.")).toBeInTheDocument());
    expect(createCount).toBe(2);
  });
});
