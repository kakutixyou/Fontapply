/** Export-related shared types. */

export interface ExportZipRequest {
  projectId: string;
  includeFonts?: boolean;
  embedFonts?: boolean;
}

export interface ExportZipResponse {
  downloadUrl: string;
  fileSize: number;
}
