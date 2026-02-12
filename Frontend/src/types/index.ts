/**
 * TypeScript interfaces matching the Backend Pydantic schemas.
 *
 * Author: brandyxie
 * Email:  brandyxie100@qq.com
 */

export interface ExtractedSkill {
  name: string;
  level: "beginner" | "intermediate" | "advanced" | "expert";
  years: number | null;
}

export interface WorkExperience {
  title: string;
  company: string;
  duration: string;
  domain: string;
  highlights: string[];
}

export interface Education {
  degree: string;
  institution: string;
  year: string;
}

export interface JobMatch {
  role: string;
  similarity_score: number;
  reason: string;
}

export interface Recommendation {
  category: string;
  suggestion: string;
  priority: "low" | "medium" | "high";
}

export interface CVUploadResponse {
  file_id: string;
  filename: string;
  file_type: "pdf" | "docx" | "txt";
  char_count: number;
  message: string;
}

export interface CVAnalysisResult {
  file_id: string;
  candidate_name: string;
  email: string;
  summary: string;
  skills: ExtractedSkill[];
  experience: WorkExperience[];
  education: Education[];
  job_matches: JobMatch[];
  recommendations: Recommendation[];
  overall_score: number;
  analyzed_at: string;
}

export interface AgentQueryRequest {
  file_id: string;
  question: string;
}

export interface AgentQueryResponse {
  answer: string;
  sources: string[];
  tool_calls: string[];
}

export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
}

/** UI state for the analysis workflow */
export type AppStep = "upload" | "analyzing" | "results";
