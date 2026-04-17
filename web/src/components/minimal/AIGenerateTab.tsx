import { useEffect, useRef, useState } from "react";
import type { CoverFields } from "../../generated/contracts";
import type { Story2PaperWSEvent } from "../../app/api";
import { story2paperWS } from "../../app/api";

export type AIGenPhase = "idle" | "generating" | "done" | "error";

export type AIGenState = {
  phase: AIGenPhase;
  researchPrompt: string;
  paperId: string | null;
  currentAgent: string | null;
  sectionIndex: number;
  revisionRound: number;
  error: string | null;
};

type AIGenerateTabProps = {
  state: AIGenState;
  coverFields: CoverFields;
  onPromptChange: (v: string) => void;
  onCoverChange: (fields: CoverFields) => void;
  onGenerate: () => void;
  onClear: () => void;
};

const AGENT_LABELS: Record<string, string> = {
  architect: "架构师 · 构建大纲",
  writer: "写作 Agent · 撰写章节",
  evaluator: "评估 Agent · 审核质量",
  refiner: "精修 Agent · 优化内容",
  done: "生成完成",
};

export function AIGenerateTab({
  state,
  coverFields,
  onPromptChange,
  onCoverChange,
  onGenerate,
  onClear,
}: AIGenerateTabProps) {
  const wsRef = useRef<WebSocket | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "0px";
    ta.style.height = `${ta.scrollHeight}px`;
    ta.style.overflowY = ta.scrollHeight > 320 ? "auto" : "hidden";
  }, [state.researchPrompt]);

  // WebSocket lifecycle
  useEffect(() => {
    if (!state.paperId || state.phase !== "generating") return;

    const ws = story2paperWS(state.paperId);
    wsRef.current = ws;

    ws.onmessage = (event: MessageEvent<string>) => {
      try {
        const data = JSON.parse(event.data) as Story2PaperWSEvent;
        if (data.event === "done" && data.final_output) {
          ws.close();
        }
      } catch {
        // ignore parse errors
      }
    };

    ws.onerror = () => {
      ws.close();
    };

    ws.onclose = () => {
      wsRef.current = null;
    };

    return () => {
      ws.close();
    };
  }, [state.paperId, state.phase]);

  const isBusy = state.phase === "generating";

  function updateCover(field: keyof CoverFields, value: string) {
    onCoverChange({ ...coverFields, [field]: value });
  }

  return (
    <div className="ai-gen-tab">
      {/* Research prompt */}
      <div className="ai-gen-section">
        <label className="field-label" htmlFor="research-prompt">
          研究方向与想法
        </label>
        <textarea
          id="research-prompt"
          ref={textareaRef}
          className="composer-textarea ai-prompt-textarea"
          placeholder="描述你的研究问题、方向或初步想法…"
          value={state.researchPrompt}
          onChange={(e) => onPromptChange(e.target.value)}
          disabled={isBusy}
          rows={3}
        />
      </div>

      {/* Cover fields */}
      <div className="ai-gen-section">
        <p className="field-label">论文封面信息</p>
        <div className="cover-fields-grid">
          <label className="cover-field">
            <span>论文题目</span>
            <input
              type="text"
              placeholder="（自动从 AI 生成结果填充）"
              value={coverFields.title}
              onChange={(e) => updateCover("title", e.target.value)}
              disabled={isBusy}
            />
          </label>
          <label className="cover-field">
            <span>学生姓名</span>
            <input
              type="text"
              placeholder="必填"
              value={coverFields.student_name}
              onChange={(e) => updateCover("student_name", e.target.value)}
              disabled={isBusy}
            />
          </label>
          <label className="cover-field">
            <span>学号</span>
            <input
              type="text"
              placeholder="必填"
              value={coverFields.student_id}
              onChange={(e) => updateCover("student_id", e.target.value)}
              disabled={isBusy}
            />
          </label>
          <label className="cover-field">
            <span>专业</span>
            <input
              type="text"
              placeholder="必填"
              value={coverFields.major}
              onChange={(e) => updateCover("major", e.target.value)}
              disabled={isBusy}
            />
          </label>
          <label className="cover-field">
            <span>班级</span>
            <input
              type="text"
              placeholder="如：2022 级 1 班"
              value={coverFields.class_name}
              onChange={(e) => updateCover("class_name", e.target.value)}
              disabled={isBusy}
            />
          </label>
          <label className="cover-field">
            <span>指导老师</span>
            <input
              type="text"
              placeholder="必填"
              value={coverFields.advisor}
              onChange={(e) => updateCover("advisor", e.target.value)}
              disabled={isBusy}
            />
          </label>
          <label className="cover-field">
            <span>毕业时间</span>
            <input
              type="text"
              placeholder="如：2026 年 6 月"
              value={coverFields.graduation_time}
              onChange={(e) => updateCover("graduation_time", e.target.value)}
              disabled={isBusy}
            />
          </label>
        </div>
      </div>

      {/* Generation status */}
      {state.phase === "generating" && (
        <div className="ai-gen-status">
          <div className="agent-progress">
            {Object.entries(AGENT_LABELS).map(([key, label]) => {
              const isActive =
                (key === "architect" && (!state.currentAgent || state.currentAgent === "architect")) ||
                (key === "writer" && state.currentAgent === "writer") ||
                (key === "evaluator" && state.currentAgent === "evaluator") ||
                (key === "refiner" && state.currentAgent === "refiner");
              const isDone =
                key === "architect"
                  ? state.currentAgent !== "architect" && state.currentAgent !== null
                  : key === "done";
              return (
                <span
                  key={key}
                  className={`agent-step ${isActive ? "active" : ""} ${isDone ? "done" : ""}`}
                >
                  {label}
                </span>
              );
            })}
          </div>
          {state.currentAgent && (
            <p className="agent-hint">
              {AGENT_LABELS[state.currentAgent] ?? state.currentAgent}进行中…
              {state.sectionIndex > 0 ? ` 第 ${state.sectionIndex} 节` : ""}
              {state.revisionRound > 0 ? ` 第 ${state.revisionRound} 轮修订` : ""}
            </p>
          )}
        </div>
      )}

      {/* Error */}
      {state.phase === "error" && state.error && (
        <div className="ai-gen-error">
          <p>{state.error}</p>
        </div>
      )}

      {/* Actions */}
      <div className="ai-gen-actions">
        {state.phase !== "generating" && (
          <button
            type="button"
            className="btn-primary"
            disabled={!state.researchPrompt.trim() || isBusy}
            onClick={onGenerate}
          >
            生成论文
          </button>
        )}
        {state.phase === "generating" && (
          <button type="button" className="btn-secondary" disabled>
            生成中…
          </button>
        )}
        {(state.phase === "done" || state.phase === "error") && (
          <button type="button" className="btn-ghost" onClick={onClear}>
            重新开始
          </button>
        )}
      </div>
    </div>
  );
}
