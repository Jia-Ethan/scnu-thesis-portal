import { useMemo, useState } from "react";
import type { BodySection, HealthResponse, MetadataFields, NormalizedThesis } from "../generated/contracts";
import { createBlankSection, defaultThesis, hydrateThesis, validateExportReadiness } from "./domain";

export function useThesisEditor(health: HealthResponse | null) {
  const [thesis, setThesis] = useState<NormalizedThesis | null>(null);

  const currentThesis = useMemo(() => thesis ?? defaultThesis(health), [health, thesis]);
  const exportReadiness = useMemo(() => validateExportReadiness(currentThesis), [currentThesis]);

  function setParsedThesis(parsed: NormalizedThesis) {
    setThesis(hydrateThesis(parsed, health));
  }

  function updateMetadata(field: keyof MetadataFields, value: string) {
    setThesis((prev) => {
      const base = prev ?? defaultThesis(health);
      return { ...base, metadata: { ...base.metadata, [field]: value } };
    });
  }

  function updateAbstract(kind: "cn" | "en", patch: Partial<NormalizedThesis["abstract_cn"]>) {
    setThesis((prev) => {
      const base = prev ?? defaultThesis(health);
      const field = kind === "cn" ? "abstract_cn" : "abstract_en";
      return { ...base, [field]: { ...base[field], ...patch } };
    });
  }

  function updateSection(index: number, patch: Partial<BodySection>) {
    setThesis((prev) => {
      const base = prev ?? defaultThesis(health);
      const bodySections = [...base.body_sections];
      bodySections[index] = { ...bodySections[index], ...patch };
      return { ...base, body_sections: bodySections };
    });
  }

  function addSection() {
    setThesis((prev) => {
      const base = prev ?? defaultThesis(health);
      return { ...base, body_sections: [...base.body_sections, createBlankSection(base.body_sections.length)] };
    });
  }

  function removeSection(index: number) {
    setThesis((prev) => {
      const base = prev ?? defaultThesis(health);
      return { ...base, body_sections: base.body_sections.filter((_, currentIndex) => currentIndex !== index) };
    });
  }

  function updateReferences(items: string[]) {
    setThesis((prev) => {
      const base = prev ?? defaultThesis(health);
      return { ...base, references: { items } };
    });
  }

  function updateLongText(field: "acknowledgements" | "appendix", value: string) {
    setThesis((prev) => {
      const base = prev ?? defaultThesis(health);
      return { ...base, [field]: value };
    });
  }

  return {
    thesis,
    currentThesis,
    exportReadiness,
    setParsedThesis,
    updateMetadata,
    updateAbstract,
    updateSection,
    addSection,
    removeSection,
    updateReferences,
    updateLongText,
  };
}
