import axios from 'axios';
import type { AnalysisResponse } from './types/analysis';
import type { ReportResponse } from './types/reports';

const API_BASE = "http://localhost:8000";

export const analyzeFile = async (file: File): Promise<AnalysisResponse> => {
  const formData = new FormData();
  formData.append("file", file);
  const response = await axios.post(`${API_BASE}/api/v1/analyze`, formData);
  return response.data;
};

export const generateReport = async (analysis_id: string): Promise<ReportResponse> => {
  const response = await axios.post(`${API_BASE}/api/v1/reports`, { analysis_id });
  return response.data;
};
