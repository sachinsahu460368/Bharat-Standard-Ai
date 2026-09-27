import { useState } from 'react';
import { analyzeFile, generateReport } from './apiService';
import type { AnalysisResponse } from './types/analysis';
import type { ReportResponse } from './types/reports';
import { FileUploader } from './components/FileUploader';
import { Header } from './components/Header';
import { DashboardSummary } from './components/DashboardSummary';
import { RequirementsPanel } from './components/RequirementsPanel';
import { RecommendationsPanel } from './components/RecommendationsPanel';
import { CompliancePanel } from './components/CompliancePanel';
import { VersionAlertsPanel } from './components/VersionAlertsPanel';
import { ReportPanel } from './components/ReportPanel';
import './App.css';

function App() {
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async (file: File) => {
    setLoading(true);
    setError(null);
    try {
      const data = await analyzeFile(file);
      setAnalysis(data);
    } catch (e: any) {
      setError(e.response?.data?.detail || "Analyze failed");
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    if (!analysis) return;
    setLoading(true);
    setError(null);
    try {
      const data = await generateReport(analysis.analysis_id);
      setReport(data);
    } catch (e: any) {
      setError(e.response?.data?.detail || "Report generation failed");
    } finally {
      setLoading(false);
    }
  };

  const resetWorkflow = () => {
    setAnalysis(null);
    setReport(null);
    setLoading(false);
    setError(null);
  };

  return (
    <div className="App">
      <Header />

      {!analysis && !loading && (
        <main className="hero">
          <h1>Find the Right Indian Standards for Your Procurement</h1>
          <FileUploader onAnalyze={handleAnalyze} disabled={loading} />
        </main>
      )}

      {loading && <div className="card loading" style={{marginTop: '40px'}}>Processing Document...</div>}
      {error && <div className="error">{error}</div>}

      {analysis && !loading && !report && (
        <main className="results">
          <DashboardSummary analysis={analysis} />
          <RequirementsPanel requirements={analysis.requirements} />
          <RecommendationsPanel recommendations={analysis.recommendations} />
          <CompliancePanel compliance={analysis.compliance} />
          <VersionAlertsPanel alerts={analysis.version_alerts} />

          <div style={{marginTop: '20px'}}>
            <button className="btn-primary" onClick={handleGenerateReport}>Generate Official Report</button>
            <button className="btn-secondary" style={{marginLeft: '10px'}} onClick={resetWorkflow}>New Analysis</button>
          </div>
        </main>
      )}

      {report && !loading && (
        <ReportPanel report={report} onReset={resetWorkflow} />
      )}
    </div>
  );
}

export default App;
