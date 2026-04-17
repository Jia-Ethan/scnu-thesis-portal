"""
Method Formalizer
将 Story2Paper pipeline 的 method 描述 formalize 为标准学术格式：
- 数学符号定义
- 算法步骤描述（Algorithm 风格）
- 定理/引理/证明结构
- 复杂度分析
"""

from __future__ import annotations
from dataclasses import dataclass

from backend.story2paper.shared.llm_router import LLMRouter


# ─── Formalization Prompts ─────────────────────────────────────────────────────

MATH_DEFINITION_PROMPT = """You are a technical writing assistant specializing in formalizing ML/NLP methods.
Given a method description, produce a rigorous mathematical formalization.

Input Method Description:
{method_text}

Task:
1. Define all key mathematical objects (sets, functions, variables) with types
2. State the optimization objective (if applicable) in LaTeX
3. Define any novel constructs introduced by the method
4. State key assumptions

Output format:
## Mathematical Definitions
[Your formalization in LaTeX]

## Key Equations
[Numbered LaTeX equations]

## Assumptions
[Numbered list of assumptions]

If no mathematical content is needed, say "No formalization needed for this method."
"""


ALGORITHM_DESCRIPTION_PROMPT = """You are a technical writing assistant.
Given a method description, produce a clear algorithm description in LaTeX algorithmicx style.

Input Method Description:
{method_text}

Task:
Produce a LaTeX algorithmicx block describing the algorithm steps.

Output format:
## Algorithm (algorithm2e or algorithmicx LaTeX)
```latex
\\begin{{algorithm}}
\\caption{{MethodName}}
\\begin{{algorithmic}}[1]
\\STATE ...
\\IF{{...}} \\STATE ... \\ENDIF
\\FOR{{...}} \\STATE ... \\ENDFOR
\\WHILE{{...}} \\STATE ... \\ENDWHILE
\\RETURN ...
\\end{{algorithmic}}
\\end{{algorithm}}
```

Focus on:
- Precise input/output specifications
- Loop invariants where appropriate
- Return values and termination conditions
"""


COMPLEXITY_ANALYSIS_PROMPT = """You are a computational complexity analyst.
Given a method description, analyze the time and space complexity.

Input Method Description:
{method_text}

Task:
1. Identify the main computational loops
2. State time complexity per component (Architect, Writer, Evaluator, Refiner)
3. State space complexity (memory usage)
4. Identify the bottleneck

Output format:
## Complexity Analysis
| Component | Time Complexity | Space Complexity |
|---|---|---|
| Architect | O(...) | O(...) |
| Writer (per section) | O(...) | O(...) |
| Evaluator | O(...) | O(...) |
| Refiner (per round) | O(...) | O(...) |

**Overall Pipeline**: O(...) time, O(...) space

**Bottleneck**: [identification]
"""


CONVERGENCE_PROMPT = """You are a theoretical ML analyst.
Given a method description and its contract mechanism, analyze convergence properties.

Input:
{method_text}

Contract Mechanism:
{contract_description}

Task:
1. State conditions under which the pipeline converges
2. Identify any fixed-point properties
3. Discuss termination guarantees

Output format:
## Theoretical Analysis
**Theorem / Proposition**: [state it]
**Proof Sketch**: [outline]
**Conditions**: [necessary conditions]
**Counterexamples**: [known failure modes]
"""


# ─── Method Formalizer ─────────────────────────────────────────────────────────

@dataclass
class FormalizedMethod:
    definitions: str = ""
    equations: str = ""
    assumptions: str = ""
    algorithm: str = ""
    complexity_table: str = ""
    convergence_analysis: str = ""
    raw_text: str = ""


class MethodFormalizer:
    """
    将 Story2Paper pipeline 输出的 method 内容 formalize 为学术标准。
    """

    def __init__(self, model: str | None = None):
        self.router = LLMRouter()
        self.model = model or "gpt-4o"

    def _call_llm(self, prompt: str) -> str:
        messages = [{"role": "user", "content": prompt}]
        resp = self.router.route(messages, model=self.model)
        return resp["content"]

    def formalize(
        self,
        method_text: str,
        contract_description: str = "",
        include_theory: bool = True,
    ) -> FormalizedMethod:
        """
        完整 formalize：
        数学定义 → 算法描述 → 复杂度分析 → 收敛性分析
        """
        result = FormalizedMethod(raw_text=method_text)

        # 1. 数学定义
        math_out = self._call_llm(
            MATH_DEFINITION_PROMPT.format(method_text=method_text)
        )
        result.definitions, result.equations, result.assumptions = _parse_math_output(math_out)

        # 2. 算法描述
        algo_out = self._call_llm(
            ALGORITHM_DESCRIPTION_PROMPT.format(method_text=method_text)
        )
        result.algorithm = _extract_latex_block(algo_out)

        # 3. 复杂度分析
        complexity_out = self._call_llm(
            COMPLEXITY_ANALYSIS_PROMPT.format(method_text=method_text)
        )
        result.complexity_table = complexity_out

        # 4. 收敛性分析（可选）
        if include_theory and contract_description:
            theory_out = self._call_llm(
                CONVERGENCE_PROMPT.format(
                    method_text=method_text,
                    contract_description=contract_description,
                )
            )
            result.convergence_analysis = theory_out

        return result

    def build_method_section(
        self,
        informal_method: str,
        contract_description: str = "",
    ) -> str:
        """
        生成完整的 formal method section。
        """
        fm = self.formalize(informal_method, contract_description)

        sections = ["## Method\n", informal_method]

        if fm.definitions or fm.equations:
            sections.append("\n### Mathematical Formalization\n")
            if fm.definitions:
                sections.append(fm.definitions)
            if fm.equations:
                sections.append(fm.equations)
            if fm.assumptions:
                sections.append(fm.assumptions)

        if fm.algorithm:
            sections.append("\n### Algorithm\n")
            sections.append(fm.algorithm)

        if fm.complexity_table:
            sections.append("\n### Complexity Analysis\n")
            sections.append(fm.complexity_table)

        if fm.convergence_analysis:
            sections.append("\n### Theoretical Analysis\n")
            sections.append(fm.convergence_analysis)

        return "\n".join(sections)


# ─── Parsing Helpers ────────────────────────────────────────────────────────────

def _parse_math_output(raw: str) -> tuple[str, str, str]:
    """从 LLM 输出中解析出定义/方程/假设三个部分。"""
    definitions, equations, assumptions = "", "", ""
    current = None

    for line in raw.split("\n"):
        ll = line.strip().lower()
        if ll.startswith("## mathematical definitions") or ll.startswith("## definitions"):
            current = "defs"
        elif ll.startswith("## key equations") or ll.startswith("## equations"):
            current = "eqs"
        elif ll.startswith("## assumptions"):
            current = "assump"
        elif ll.startswith("##"):
            current = None

        if current == "defs":
            definitions += line + "\n"
        elif current == "eqs":
            equations += line + "\n"
        elif current == "assump":
            assumptions += line + "\n"

    return definitions.strip(), equations.strip(), assumptions.strip()


def _extract_latex_block(text: str) -> str:
    """从 LLM 输出中提取 LaTeX 代码块。"""
    if "```latex" in text:
        parts = text.split("```latex")
        for part in parts[1:]:
            if "```" in part:
                return "```latex" + part.split("```")[0] + "```"
    elif "\\begin{algorithm}" in text:
        # 没有 markdown 代码块，直接提取 algorithm 环境
        start = text.find("\\begin{algorithm}")
        end = text.find("\\end{algorithm}") + len("\\end{algorithm}")
        return text[start:end]
    return text  # fallback：返回原文
