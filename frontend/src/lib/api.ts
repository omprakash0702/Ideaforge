const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(body.detail ?? `HTTP ${res.status}`)
  }
  return res.json()
}

// ── Types ──────────────────────────────────────────────────────────────────

export type ProjectStatus =
  | 'CREATED' | 'RUNNING' | 'GENERATING' | 'JUDGING'
  | 'EVOLVING' | 'TOURNAMENT' | 'REPORTING' | 'COMPLETED' | 'FAILED'

export interface User {
  id: string
  name: string
  email: string
  created_at: string
}

export interface Project {
  id: string
  user_id: string
  title: string
  problem_statement: string
  status: ProjectStatus
  created_at: string
  updated_at: string
}

export interface UserIdeaCreate {
  title: string
  problem: string
  solution: string
  target_audience: string
  business_model: string
  tech_stack: string
  key_features?: string[]
  competitors?: string[]
}

export interface Idea {
  id: string
  project_id: string
  parent_idea_id: string | null
  version: number
  generator_type: 'CREATIVE' | 'MARKET' | 'BUILDER' | 'ANALYST' | null
  title: string
  problem: string
  solution: string
  target_audience: string
  business_model: string
  tech_stack: string
  key_features: string[] | null
  competitors: string[] | null
  score: number | null
  is_winner: boolean
  created_at: string
}

export interface Evaluation {
  id: string
  idea_id: string
  judge_type: 'INVESTOR' | 'ENGINEER' | 'SKEPTIC'
  score: number
  strengths: string[] | null
  weaknesses: string[] | null
  recommendations: string[] | null
  created_at: string
}

export interface Report {
  id: string
  project_id: string
  winner_idea_id: string | null
  markdown_report: string
  created_at: string
}

export interface IdeaGraphNode {
  id: string
  title: string
  project_id: string
  version: number
  generator_type: string | null
  problem: string
  solution: string
  target_audience: string
  business_model: string
  tech_stack: string
  key_features: string[]
  competitors: string[]
  tournament_rank: number | null
  aggregate_score: number | null
  is_winner: boolean
}

export interface IdeaGraphEdge {
  source: string
  target: string
  type: string                      // 'EVOLVED_INTO' | 'RANKED_ABOVE'
  evolution_rationale: string | null
  score_before: number | null
  score_after: number | null
  score_delta: number | null
  score_diff: number | null
}

export interface JudgeNode {
  id: string
  judge_type: string
  project_id: string
}

export interface EvaluationEdge {
  source: string   // judge node id
  target: string   // idea node id
  score: number
  strengths: string[]
  weaknesses: string[]
  recommendations: string[]
}

export interface IdeaGraphResponse {
  nodes: IdeaGraphNode[]
  edges: IdeaGraphEdge[]
  judge_nodes: JudgeNode[]
  evaluation_edges: EvaluationEdge[]
}

// ── Users ──────────────────────────────────────────────────────────────────

export const api = {
  users: {
    create: (body: { name: string; email: string }) =>
      request<User>('/users', { method: 'POST', body: JSON.stringify(body) }),

    get: (id: string) => request<User>(`/users/${id}`),

    projects: (id: string) => request<Project[]>(`/users/${id}/projects`),
  },

  projects: {
    create: (body: { user_id: string; title: string; problem_statement: string }) =>
      request<Project>('/projects', { method: 'POST', body: JSON.stringify(body) }),

    get: (id: string) => request<Project>(`/projects/${id}`),

    run: (id: string) =>
      request<{ status: string; message: string }>(`/projects/${id}/run`, { method: 'POST' }),

    ideas: (id: string) => request<Idea[]>(`/projects/${id}/ideas`),

    report: (id: string) => request<Report>(`/projects/${id}/report`),

    evaluations: (id: string) => request<Evaluation[]>(`/projects/${id}/evaluations`),

    graph: (id: string) => request<IdeaGraphResponse>(`/projects/${id}/graph`),

    addIdea: (id: string, body: UserIdeaCreate) =>
      request<Idea>(`/projects/${id}/ideas`, { method: 'POST', body: JSON.stringify(body) }),

    evolveIdea: (projectId: string, ideaId: string) =>
      request<Idea[]>(`/projects/${projectId}/ideas/${ideaId}/evolve`, { method: 'POST' }),

    generateWithConstraints: (id: string, constraints: string) =>
      request<Idea[]>(`/projects/${id}/ideas/generate`, {
        method: 'POST',
        body: JSON.stringify({ constraints }),
      }),

    uploadDocument: (id: string, file: File) => {
      const form = new FormData()
      form.append('file', file)
      return request<{
        project_id: string
        filename: string
        source_type: string
        chunk_count: number
        char_count: number
      }>(`/projects/${id}/documents`, {
        method: 'POST',
        headers: {},
        body: form,
      })
    },

    reset: (id: string) => request<Project>(`/projects/${id}/reset`, { method: 'POST' }),

    delete: (id: string) => request<void>(`/projects/${id}`, { method: 'DELETE' }),
  },
}
