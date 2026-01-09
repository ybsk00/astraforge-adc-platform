/**
 * API 클라이언트 설정
 */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export interface Component {
  id: string;
  workspace_id: string | null;
  type: 'target' | 'antibody' | 'linker' | 'payload' | 'conjugation';
  name: string;
  properties: Record<string, unknown>;
  quality_grade: 'gold' | 'silver' | 'bronze';
  status: 'pending_compute' | 'active' | 'failed' | 'deprecated';
  compute_error: string | null;
  computed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ComponentListResponse {
  items: Component[];
  total: number;
  limit: number;
  offset: number;
}

export interface ComponentCreate {
  type: Component['type'];
  name: string;
  properties: Record<string, unknown>;
  quality_grade: Component['quality_grade'];
}

export interface CatalogStats {
  total: number;
  by_type: Record<string, number>;
  by_status: Record<string, number>;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // 카탈로그 API
  async getComponents(params?: {
    type?: string;
    status?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }): Promise<ComponentListResponse> {
    const searchParams = new URLSearchParams();
    if (params?.type) searchParams.set('type', params.type);
    if (params?.status) searchParams.set('status', params.status);
    if (params?.search) searchParams.set('search', params.search);
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.offset) searchParams.set('offset', params.offset.toString());

    const query = searchParams.toString();
    return this.request<ComponentListResponse>(
      `/api/v1/catalog/components${query ? `?${query}` : ''}`
    );
  }

  async getComponent(id: string): Promise<Component> {
    return this.request<Component>(`/api/v1/catalog/components/${id}`);
  }

  async createComponent(data: ComponentCreate): Promise<Component> {
    return this.request<Component>('/api/v1/catalog/components', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateComponent(
    id: string,
    data: Partial<ComponentCreate>
  ): Promise<Component> {
    return this.request<Component>(`/api/v1/catalog/components/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async deleteComponent(id: string): Promise<{ status: string }> {
    return this.request<{ status: string }>(
      `/api/v1/catalog/components/${id}`,
      { method: 'DELETE' }
    );
  }

  async retryComponent(id: string): Promise<{ status: string }> {
    return this.request<{ status: string }>(
      `/api/v1/catalog/components/${id}/retry`,
      { method: 'POST' }
    );
  }

  async getCatalogStats(): Promise<CatalogStats> {
    return this.request<CatalogStats>('/api/v1/catalog/components/stats/summary');
  }
}

export const api = new ApiClient(API_BASE_URL);
