// src/api/uploadApi.ts
import { apiClient } from "./apiClient";

export interface UploadResponse {
  id: number;
  filename: string;
  status: string;
  file_path: string;
}

export const uploadFile = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append("file", file);

  // Minor comment: Axios automatically sets the boundary for multipart/form-data
  const response = await apiClient.post<UploadResponse>("/upload", formData);

  return response.data;
};
