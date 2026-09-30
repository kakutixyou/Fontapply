export interface ProjectRecord {
  id: number;
  name: string;
  image_path?: string | null;
  created_at: string;
  updated_at?: string;
}

export interface CreateProjectInput {
  name: string;
  image_path?: string;
}

export interface UpdateProjectInput {
  name?: string;
  image_path?: string;
}
