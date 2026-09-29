// src/types/domain/user.ts
import type {
  Category,
  Hashtag,
  Viewport,
  ISODate,
  ISOTime,
  Id
} from '../common';

export interface MealPreferences {
  breakfast: string[];
  lunch: string[];
  dinner: string[];
}

export interface UserPreferences {
  startTime: ISOTime;
  endTime: ISOTime;
  travelStyle: string;
  meals: MealPreferences;
  tags: Hashtag[];
}

export interface UserState {
  id: Id;
  area: string;
  startDate: ISODate;
  endDate: ISODate;
  tripDays: number;
  startPlace: string;
  startTime: ISOTime;
  endPlace: string;
  endTime: ISOTime;
  selectedDates: ISODate[];
  accommodationName: string;
  accommodationDay: number | null;
  tags: Hashtag[];
  category: Category | '';
  tripStyle: string;  // 여행 스타일 
  jeju_area: string[];  // 선택한 제주 읍면 지역
  viewport: Viewport | null;
  preferences: UserPreferences | null;
}
