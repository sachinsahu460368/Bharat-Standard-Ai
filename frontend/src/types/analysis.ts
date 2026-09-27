export interface DocumentInfo {
  filename: string;
  pages: number;
  content_length: number;
  extraction_method: string;
}

export interface ExtractedRequirements {
  product?: string;
  category?: string;
  quantity?: string;
  application?: string;
  environment?: string;
  technical_requirements: string[];
  materials: string[];
  performance_requirements: string[];
  safety_requirements: string[];
  testing_requirements: string[];
  certification_mentions: string[];
  referenced_standards: string[];
}

export interface EvidenceRecord {
  text: string;
  source_type: string;
  source_name: string;
  source_url?: string;
  page?: number;
}

export interface RecommendedStandard {
  standard_id: string;
  standard_number: string;
  title: string;
  relevance: 'High' | 'Medium' | 'Low';
  score: number;
  matched_requirements: string[];
  reason: string;
  evidence: EvidenceRecord[];
  status: string;
  source: { name: string; type: string };
}

export interface VersionAlert {
  standard_id: string;
  detected_version?: string;
  latest_known_version?: string;
  status: string;
  message: string;
}

export interface ComplianceResult {
  standard_id: string;
  status: string; // APPLICABLE, NOT_APPLICABLE, NOT_FOUND, REQUIRES_VERIFICATION
  requirement: string;
  authority: string;
  verification_message?: string;
}

export interface StandardExplanation {
  standard_id: string;
  explanation: string;
  confidence: string;
}

export interface AnalysisResponse {
  analysis_id: string;
  status: string;
  document: DocumentInfo;
  requirements: ExtractedRequirements;
  recommendations: RecommendedStandard[];
  related_standards: Record<string, any>;
  version_alerts: VersionAlert[];
  compliance: ComplianceResult[];
  explanation?: StandardExplanation;
  warnings: string[];
}
