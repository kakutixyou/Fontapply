export interface ProjectRecord {
  id: string;
  name: string;
  image_path: string;
  created_at: string;
}

export interface CreateProjectInput {
  name: string;
  image_path?: string;
}

export interface UpdateProjectInput {
  name?: string;
  image_path?: string;
}
