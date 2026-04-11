import type { NormalizedThesis } from "../../generated/contracts";
import { referencesToString, splitReferences } from "../../app/domain";
import { FieldGroup, SectionCard } from "../../components/ui";

type ReferencesEditorProps = {
  thesis: NormalizedThesis;
  onChange: (items: string[]) => void;
};

export function ReferencesEditor({ thesis, onChange }: ReferencesEditorProps) {
  return (
    <SectionCard title="参考文献" eyebrow="References" description="每行保留一条参考文献，导出时会写入模板工程。">
      <FieldGroup label="每行一条" htmlFor="references-items">
        <textarea
          id="references-items"
          rows={10}
          value={referencesToString(thesis)}
          onChange={(event) => onChange(splitReferences(event.target.value))}
        />
      </FieldGroup>
    </SectionCard>
  );
}
