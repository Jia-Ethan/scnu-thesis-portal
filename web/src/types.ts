export type JobStatus = "queued" | "processing" | "completed" | "failed";

export interface SectionNode {
  kind: string;
  title: string;
  content: string;
}

export interface HealthResponse {
  ok: boolean;
  tex: {
    xelatex: boolean;
    kpsewhich: boolean;
    missing_styles: string[];
  };
}

export interface JobCreateResponse {
  job_id: string;
  status: JobStatus;
}

export interface JobStatusResponse {
  job_id: string;
  status: JobStatus;
  source_type: string;
  template: string;
  error_code?: string | null;
  error_message?: string | null;
  warnings: string[];
  sections: SectionNode[];
  output_dir?: string | null;
  compile_command: string[];
  artifacts?: {
    job_id: string;
    pdf_path?: string | null;
    texzip_path?: string | null;
    compile_log_path?: string | null;
  } | null;
}
