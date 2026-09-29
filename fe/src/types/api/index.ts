// src/types/api/index.ts
export interface ApiResult<T> {
  success: boolean;
  data: T | null;
  error: unknown | null;
}
