import type { Viewport, Category, Hashtag, Coordinates2D } from '../common';

export interface CategoryToHashtagRequest {
  category: Category;
  viewport: Viewport;
}
export interface CategoryToHashtagResponse {
  tags: Hashtag[];
}

export interface PlaceRecommendation {
  name: string;
  category: Category;
  coord: Coordinates2D;
  similarity: number; // 0~1
}

export interface HashtagToPlaceRequest {
  category: Category;
  tag: Hashtag[];
  viewport: Viewport;
}

export interface HashtagToPlaceResponse {
  recommendations: PlaceRecommendation[];
}
