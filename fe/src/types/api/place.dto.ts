import type { PlaceDetail } from '../domain/place';
import type { PlaceName } from '../common';

export interface PlaceDetailRequest { name: PlaceName; }
export interface PlaceDetailResponse { place: PlaceDetail; }

export interface PlaceSearchRequest { keyword: PlaceName; }
export interface PlaceSearchHit { name: PlaceName; }
export interface PlaceSearchResponse { results: PlaceSearchHit[]; }
