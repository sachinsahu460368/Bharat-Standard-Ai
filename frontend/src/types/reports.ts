export interface ReportSection {
  title: string;
  content: string;
}

export interface ReportResponse {
  report_id: string;
  analysis_id: string;
  generated_at: string;
  sections: ReportSection[];
  summary: string;
  disclaimer: string;
}
