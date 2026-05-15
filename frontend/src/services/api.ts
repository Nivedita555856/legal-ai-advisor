import axios from 'axios';
import { QueryResult, Document, Lawyer, SearchResult } from '../types';

const BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor for logging
api.interceptors.request.use((config) => {
  console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const message = err.response?.data?.detail || err.message || 'API Error';
    console.error('[API Error]', message);
    return Promise.reject(new Error(message));
  }
);

export const legalApi = {
  health: () => api.get('/health'),

  query: (query: string, jurisdiction = 'India'): Promise<{ data: QueryResult }> =>
    api.post('/query', { query, jurisdiction }),

  uploadDocument: (file: File, docName?: string): Promise<{ data: any }> => {
    const formData = new FormData();
    formData.append('file', file);
    if (docName) formData.append('doc_name', docName);
    return api.post('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  listDocuments: (): Promise<{ data: { documents: Document[]; count: number } }> =>
    api.get('/documents'),

  getDocumentStats: () => api.get('/documents/stats'),

  searchDocuments: (query: string, topK = 10): Promise<{ data: { results: SearchResult[] } }> =>
    api.post('/search', { query, top_k: topK }),

  findLawyers: (city: string, practiceArea?: string): Promise<{ data: { lawyers: Lawyer[] } }> =>
    api.post('/lawyers', { city, practice_area: practiceArea }),

  generateDraft: (
    scenario: string,
    docType = 'notice',
    parties = 'Party A and Party B',
    jurisdiction = 'India'
  ): Promise<{ data: { draft: string } }> =>
    api.post('/draft', { scenario, doc_type: docType, parties, jurisdiction }),

  summarize: (text: string): Promise<{ data: { summary: string } }> =>
    api.post('/summarize', { query: text }),

  listAnalyses: () => api.get('/analyses'),
};

export default legalApi;
