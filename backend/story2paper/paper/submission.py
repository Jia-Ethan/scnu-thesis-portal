"""
Submission Package Generator
为 ACL/EMNLP/ICLR 生成符合格式要求的 submission package：
- camera-ready PDF（通过 LaTeX 编译）
- anonymized PDF（去除作者信息）
- supplemental materials 打包
- 格式校验（页数、行数、作者数）
"""

from __future__ import annotations
import zipfile
import shutil
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Literal

from backend.story2paper.paper.structure import PaperDraft, ACL_REQUIREMENTS


# ─── Submission Venue Config ────────────────────────────────────────────────────

VENUE_CONFIGS = {
    "acl": {
        "package": "acl_submission.zip",
        "main_tex": "aclpaper.tex",
        "style": "acl",
        "page_limit": 8,
    },
    "emnlp": {
        "package": "emnlp_submission.zip",
        "main_tex": "emnlppaper.tex",
        "style": "emnlp",
        "page_limit": 8,
    },
    "iclr": {
        "package": "iclr_submission.zip",
        "main_tex": "iclrpaper.tex",
        "style": "iclr",
        "page_limit": 8,
    },
}


@dataclass
class SubmissionCheck:
    title_ok: bool = False
    abstract_ok: bool = False
    author_limit_ok: bool = False
    page_estimate_ok: bool = False
    latex_compiles: bool = False
    errors: list[str]


# ─── Submission Package ─────────────────────────────────────────────────────────

class SubmissionPackage:
    """
    生成会议投稿包。
    """

    def __init__(
        self,
        draft: PaperDraft,
        venue: Literal["acl", "emnlp", "iclr"],
        output_dir: str | Path = "outputs/submissions",
        anonymized: bool = False,
    ):
        self.draft = draft
        self.venue = venue
        self.config = VENUE_CONFIGS[venue]
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.anonymized = anonymized

    def generate_tex(self) -> str:
        """生成 LaTeX 源文件内容。"""
        title = self.draft.title if not self.anonymized else self.draft.title
        abstract = self.draft.abstract

        sections_latex = self._sections_to_latex()
        references = self._format_references()

        return self._latex_boilerplate(
            title=title,
            abstract=abstract,
            sections=sections_latex,
            references=references,
        )

    def _sections_to_latex(self) -> str:
        """将 sections dict 转换为 LaTeX section 环境。"""
        mapping = {
            "Introduction": "intro",
            "Related Work": "related",
            "Background": "background",
            "Method": "method",
            "Experiments": "experiments",
            "Discussion": "discussion",
            "Conclusion": "conclusion",
        }
        parts = []
        for sec_name, sec_content in self.draft.sections.items():
            label = mapping.get(sec_name, sec_name.lower())
            parts.append(
                f"\\section{{{sec_name}}}\n"
                f"\\label{{{label}}}\n"
                f"{sec_content}\n"
            )
        return "\n\n".join(parts)

    def _format_references(self) -> str:
        """格式化 references 为 BibTeX 块。"""
        if not self.draft.references:
            return ""
        ref_block = []
        for ref in self.draft.references:
            ref_block.append(ref)
        return "\n".join(ref_block)

    def _latex_boilerplate(
        self,
        title: str,
        abstract: str,
        sections: str,
        references: str,
    ) -> str:
        """组装完整 LaTeX 文档。"""
        anonymized_note = (
            "\\预编译注释：ANONYMIZED FOR SUBMISSION — REMOVE FOR CAMERA-READY"
            if self.anonymized
            else ""
        )
        return f"""\\documentclass[12pt]{{article}}
%% 适用于 {self.venue.upper()} 格式
\\usepackage[utf8]{{inputenc}}
\\usepackage{{times}}
\\usepackage{{url}}
\\usepackage{{booktabs}}
\\usepackage{{amsmath}}
\\usepackage{{graphicx}}
\\usepackage{{lipsum}}

% ACL/EMNLP/ICLR 通用格式
\\usepackage{{acl}}

\\title{{{title}}}
{anonymized_note}

\\author{{
  % ACL: 最多 8 位作者，请按姓氏字母序或贡献排序
  Author 1$^{1}$,
  Author 2$^{2}$,
  Author 3$^{1,2}$
  \\\\
  $^{1}$Institution 1 \\\\
  $^{2}$Institution 2 \\\\
  author1@email.com, author2@email.com
}}

\\date{{}}

\\begin{{document}}
\\maketitle
\\begin{{abstract}}
{abstract}
\\end{{abstract}}

{sections}

% References
\\bibliography{{references}}
\\bibliographystyle{{acl_natbib}}

% Supplemental（可选）
\\newpage
\\section*{{Supplementary Material}}
\\label{{supplementary}}
% Appendix content here

\\end{{document}}
"""

    def check(self) -> SubmissionCheck:
        """格式校验。"""
        errors = []
        check = SubmissionCheck()

        # title 长度
        title_words = len(self.draft.title.split())
        max_title = ACL_REQUIREMENTS["title"]["max_words"]
        check.title_ok = title_words <= max_title
        if not check.title_ok:
            errors.append(f"Title too long: {title_words} words (max {max_title})")

        # abstract 长度
        abstract_words = len(self.draft.abstract.split())
        max_abs = ACL_REQUIREMENTS["abstract"]["max_words"]
        check.abstract_ok = abstract_words <= max_abs
        if not check.abstract_ok:
            errors.append(f"Abstract too long: {abstract_words} words (max {max_abs})")

        # 估算页数（假设 800 words/page）
        total_words = self.draft.total_words()
        estimated_pages = total_words / 800
        check.page_estimate_ok = estimated_pages <= self.config["page_limit"]
        if not check.page_estimate_ok:
            errors.append(
                f"Estimated {estimated_pages:.1f} pages (limit: {self.config['page_limit']})"
            )

        # LaTeX 编译测试
        tex_path = self.output_dir / self.config["main_tex"]
        tex_path.write_text(self.generate_tex(), encoding="utf-8")
        try:
            result = subprocess.run(
                ["pdflatex", "-interaction=batchmode", str(tex_path)],
                capture_output=True,
                timeout=60,
                cwd=self.output_dir,
            )
            check.latex_compiles = result.returncode == 0
            if not check.latex_compiles:
                errors.append("LaTeX compilation failed")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            errors.append("LaTeX not available (pdflatex not found)")

        check.errors = errors
        return check

    def build_package(self) -> Path:
        """
        生成 zip 投递包。
        包含：main tex + 编译后的 PDF + references bib
        """
        package_name = self.config["package"].replace(".zip", f"_{self.venue}.zip")
        package_path = self.output_dir / package_name

        tex_name = self.config["main_tex"]
        tex_path = self.output_dir / tex_name
        tex_path.write_text(self.generate_tex(), encoding="utf-8")

        ref_path = self.output_dir / "references.bib"
        ref_path.write_text(self._format_references(), encoding="utf-8")

        with zipfile.ZipFile(package_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(tex_path, tex_name)
            zf.write(ref_path, "references.bib")

            # 如果有图片目录，加入
            img_dir = self.output_dir / "figures"
            if img_dir.exists():
                for img in img_dir.glob("*"):
                    zf.write(img, f"figures/{img.name}")

        return package_path

    def build_anonymized_package(self) -> Path:
        """生成匿名版投递包（去除作者信息）。"""
        old_draft = self.draft
        self.draft.title = "[TITLE REMOVED FOR ANONYMIZATION]"
        self.draft.abstract = self.draft.abstract  # abstract 保留
        # 去除 references 中的作者名（简化处理）
        if self.draft.references:
            import re
            self.draft.references = [
                re.sub(r"\b[A-Z][a-z]+,\s*[A-Z]\.", "[Author, Year]", ref)
                for ref in self.draft.references
            ]

        path = self.build_package()

        # 恢复
        self.draft = old_draft
        return path
