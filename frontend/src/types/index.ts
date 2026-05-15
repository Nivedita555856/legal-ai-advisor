export interface Document {
  id: string;
  name: string;
  file_type: string;
  content?: string;
  chunk_count: number;
  uploaded_at: string;
}

export interface RiskScore {
  score: number;
  level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  factors?: string[];
  recommendation?: string;
}

export interface Contradiction {
  clause_a: number;
  clause_b: number;
  has_contradiction: boolean;
  severity: 'LOW' | 'MEDIUM' | 'HIGH';
  explanation: string;
}

export interface Lawyer {
  name: string;
  practice_areas: string[];
  experience: number;
  firm: string;
  contact: string;
  rating: number;
  city?: string;
}

export interface MCTSStep {
  action: string;
  value: number;
  visits: number;
}

export interface QueryResult {
  success: boolean;
  query: string;
  jurisdiction: string;
  answer: string;
  risk_score: RiskScore;
  contradictions: Contradiction[];
  similar_cases: string[];
  lawyers: Lawyer[];
  rag_strategy: string;
  mcts_path: MCTSStep[];
  draft: string;
  needs_human_review: boolean;
}

export interface SearchResult {
  id: string;
  score: number;
  text: string;
  document: string;
  chunk_index: number;
}

export interface Analysis {
  id: string;
  document_id?: string;
  query: string;
  answer: string;
  risk_level?: string;
  risk_score?: number;
  rag_strategy?: string;
  created_at: string;
}
