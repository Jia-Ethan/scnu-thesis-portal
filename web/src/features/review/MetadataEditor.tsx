import type { MetadataFields } from "../../generated/contracts";
import { FieldGroup, SectionCard } from "../../components/ui";

const fields = [
  ["title", "论文题目"],
  ["author_name", "学生姓名"],
  ["student_id", "学号"],
  ["department", "学院 / 系别"],
  ["major", "专业"],
  ["class_name", "班级"],
  ["advisor_name", "指导老师"],
  ["submission_date", "提交日期"],
] as [keyof MetadataFields, string][];

type MetadataEditorProps = {
  metadata: MetadataFields;
  onChange: (field: keyof MetadataFields, value: string) => void;
};

export function MetadataEditor({ metadata, onChange }: MetadataEditorProps) {
  return (
    <SectionCard title="封面字段" eyebrow="Metadata" description="这些字段会进入模板工程，请先补齐基础信息。">
      <div className="form-grid">
        {fields.map(([field, label]) => {
          const id = `metadata-${field}`;
          return (
            <FieldGroup key={field} label={label} htmlFor={id}>
              <input id={id} value={metadata[field] ?? ""} onChange={(event) => onChange(field, event.target.value)} />
            </FieldGroup>
          );
        })}
      </div>
    </SectionCard>
  );
}
