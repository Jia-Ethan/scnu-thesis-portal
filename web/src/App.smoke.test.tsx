import { render, screen, waitFor } from "@testing-library/react";
import { App } from "./App";

describe("App smoke", () => {
  it("renders launch boundary and both inputs", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          ok: true,
          app_env: "development",
          template: "latex-scnu-web",
          capabilities: {
            tex_zip: true,
            pdf: false,
            pdf_reason: "PDF 仅在本地开发模式中可用。",
          },
          limits: {
            max_docx_size_bytes: 4194304,
          },
          tex: {
            xelatex: false,
            kpsewhich: false,
            missing_styles: ["ctex.sty"],
          },
        }),
      }),
    );

    render(<App />);

    expect(screen.getByText("把原始论文内容整理成可进入模板的规范化产物")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "上传 `.docx`" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "粘贴正文" })).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("模板：latex-scnu-web")).toBeInTheDocument();
    });
  });
});
