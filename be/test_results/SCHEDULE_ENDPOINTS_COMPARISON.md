# Schedule 엔드포인트 비교 분석

**비교 대상**:
- `/api/users/schedules/schedule` (Schedules Router)
- `/api/trip-planner/schedule` (Trip Planner Router)

---

## 1. 엔드포인트 기본 정보

| 항목 | Schedules Schedule | Trip Planner Schedule |
|------|-------------------|---------------------|
| **경로** | `/api/users/schedules/schedule` | `/api/trip-planner/schedule` |
| **HTTP 메서드** | `GET` (Body 사용) | `POST` |
| **주요 목적** | DB 조회 및 정보 확장 | 일정 최적화 (TripScheduler) |
| **처리 범위** | 여러 날 (Multi-day) | 단일 날 (Single day) |

---

## 2. 입력 스키마 비교

### Schedules Schedule 입력

**파일**: `app/schemas/schedules.py:66-68`

```python
class SchedulRequest(BaseModel):
    user_id: str
    places_by_day: Dict[int, List[PlaceWithServiceIn]]

class PlaceWithServiceIn(BaseModel):
    name: str              # 장소 이름
    service_time: int      # 체류 시간
```

**특징**:
- 여러 날짜 지원 (`places_by_day`)
- 장소 이름 + service_time만 필요
- 좌표, 카테고리 등은 DB에서 조회

**예시**:
```json
{
  "user_id": "user123",
  "places_by_day": {
    "0": [
      {"name": "제주국제공항", "service_time": 30},
      {"name": "용두암", "service_time": 60}
    ],
    "1": [
      {"name": "성산일출봉", "service_time": 120}
    ]
  }
}
```

### Trip Planner Schedule 입력

**파일**: `app/routers/trip_planner.py:19-52`

```python
class TripScheduleRequest(BaseModel):
    places: List[PlaceInput]
    user: UserInput
    day_info: DayInfoInput
    use_mock: Optional[bool] = False

class PlaceInput(BaseModel):
    id: int
    name: str
    x_cord: float          # 좌표 필수
    y_cord: float          # 좌표 필수
    category: Optional[str] = None
    service_time: Optional[int] = 0
    open_time: Optional[str] = None
    close_time: Optional[str] = None
    tags: Optional[List[str]] = []
    is_mandatory: Optional[bool] = False
    closed_days: Optional[List] = []
    break_time: Optional[List] = []

class UserInput(BaseModel):
    start_time: str
    end_time: str
    travel_style: Optional[str] = "normal"
    meal_time_preferences: Optional[Dict[str, List[str]]] = None

class DayInfoInput(BaseModel):
    type: Optional[str] = "normal"
    is_first_day: Optional[bool] = False
    is_last_day: Optional[bool] = False
    date: Optional[str] = None
    weekday: Optional[str] = None
```

**특징**:
- 단일 날짜만 처리 (`places` 리스트)
- 모든 장소 정보가 입력에 포함되어야 함
- 사용자 선호도, 날짜 정보 포함
- TripScheduler 실행을 위한 상세 정보 필요

**예시**:
```json
{
  "places": [
    {
      "id": 1,
      "name": "제주국제공항",
      "x_cord": 126.4959513,
      "y_cord": 33.5059365,
      "category": "transport",
      "service_time": 30,
      "open_time": "00:00",
      "close_time": "23:59",
      "is_mandatory": true
    }
  ],
  "user": {
    "start_time": "09:00",
    "end_time": "18:00",
    "travel_style": "relaxed",
    "meal_time_preferences": {
      "lunch": ["12:00", "13:30"]
    }
  },
  "day_info": {
    "is_first_day": false,
    "is_last_day": false,
    "date": "2025-10-01",
    "weekday": "수요일"
  },
  "use_mock": false
}
```

---

## 3. 출력 스키마 비교

### Schedules Schedule 출력

**파일**: `app/schemas/schedules.py:71-83`

```python
class PlaceWithTimingOut(BaseModel):
    name: str
    category: str
    address: str
    arrival_str: str        # 빈 문자열
    departure_str: str      # 빈 문자열
    service_time: int
    x_cord: float
    y_cord: float

class SchedulResponse(BaseModel):
    places_by_day: Dict[int, List[PlaceWithTimingOut]]
    path: List[List[List[float]]]  # 항상 빈 배열
```

**특징**:
- `arrival_str`, `departure_str`이 빈 문자열 (시간 계산 안함)
- `path`는 항상 빈 배열
- 여러 날짜의 장소 정보 반환

**예시**:
```json
{
  "places_by_day": {
    "0": [
      {
        "name": "제주국제공항",
        "category": "transport",
        "address": "제주 제주시 공항로 2",
        "arrival_str": "",
        "departure_str": "",
        "service_time": 30,
        "x_cord": 126.4959513,
        "y_cord": 33.5059365
      }
    ]
  },
  "path": []
}
```

### Trip Planner Schedule 출력

**파일**: `app/routers/trip_planner.py:54-56`

```python
class TripScheduleResponse(BaseModel):
    visits: List[Dict[str, Any]]
    path: List[List[List[float]]]
```

**Visits 구조** (TripScheduler 성공 시):
```python
{
  "order": int,
  "place": str,
  "arrival_str": str,      # "HH:MM" 형식
  "departure_str": str,    # "HH:MM" 형식
  "stay_duration": str,    # "HH:MM" 형식
  "x_cord": float,
  "y_cord": float,
  "travel_time": str       # "HH:MM" (선택적)
}
```

**특징**:
- 최적화된 방문 순서 (`order`)
- 정확한 도착/출발 시간
- 이동 시간 계산
- 실제 도로 경로 좌표 (Real API mode)

**예시** (Real API mode):
```json
{
  "visits": [
    {
      "order": 1,
      "place": "착한갈치",
      "arrival_str": "11:20",
      "departure_str": "12:20",
      "stay_duration": "01:00",
      "x_cord": 126.6061121,
      "y_cord": 33.2398767
    },
    {
      "order": 2,
      "place": "이중섭거리",
      "arrival_str": "12:29",
      "departure_str": "13:59",
      "stay_duration": "01:30",
      "x_cord": 126.5648532,
      "y_cord": 33.2413549,
      "travel_time": "00:09"
    }
  ],
  "path": [
    [
      [126.6061121, 33.2398767],
      [126.6060, 33.2397],
      [126.6058, 33.2395],
      ... (184개 좌표)
    ],
    [...]
  ]
}
```

---

## 4. 처리 로직 비교

### Schedules Schedule 처리 흐름

**파일**: `app/routers/schedules.py:232-259`

```
1. 입력: places_by_day (장소 이름 + service_time)
2. 각 날짜별로 반복:
   a. 각 장소 이름으로 DB 조회 (_find_place_by_name)
   b. 찾은 경우: 상세 정보 추가 (category, address, 좌표)
   c. 못 찾은 경우: 건너뜀 (skip)
3. arrival_str, departure_str은 빈 문자열로 설정
4. path는 빈 배열로 설정
5. 반환
```

**특징**:
- ✅ 간단한 DB 조회
- ✅ 빠른 처리
- ❌ 시간 최적화 없음
- ❌ 경로 생성 없음
- ❌ 이동 시간 계산 없음

### Trip Planner Schedule 처리 흐름

**파일**: `app/routers/trip_planner.py:58-151`

```
1. 입력: places + user + day_info (모든 정보 포함)
2. TripScheduler 실행 시도:
   a. prepare_matrices() - 시간/거리/경로 매트릭스 생성
   b. calculate_time_windows() - 시간 윈도우 계산
   c. split_restaurant_nodes() - 식당 노드 분리
   d. generate_valid_combinations() - 유효한 조합 생성
   e. run_scheduler() - OR-Tools로 최적 경로 계산
3. 성공 시:
   - 최적화된 방문 순서
   - 정확한 도착/출발 시간
   - 이동 시간 계산
   - 실제 도로 경로 (Real API mode)
4. 실패 시 (Fallback):
   - 입력 순서대로 배치
   - 간단한 시간 할당
   - 직선 경로 생성
5. 반환
```

**특징**:
- ✅ 시간 최적화
- ✅ 경로 최적화 (TSP)
- ✅ 제약 조건 고려 (영업시간, 식사시간)
- ✅ 실제 도로 경로 (Real API)
- ⚠️ 복잡한 처리 (느림)
- ⚠️ 실패 시 fallback

---

## 5. 사용 목적 비교

### Schedules Schedule 사용 시나리오

**언제 사용**:
1. 프론트엔드가 이미 장소를 선택한 상태
2. 장소 이름만 있고 상세 정보가 필요할 때
3. 여러 날의 장소 정보를 한 번에 확장할 때
4. 시간 최적화가 필요 없을 때

**사용 흐름**:
```
Frontend → 장소 이름 선택 → /schedules/schedule → DB 조회 → 상세 정보 반환 → Frontend
```

**장점**:
- 간단한 요청
- 빠른 응답
- 여러 날 처리 가능

**단점**:
- 시간 정보 없음
- 경로 없음
- 최적화 없음

### Trip Planner Schedule 사용 시나리오

**언제 사용**:
1. 장소 순서를 최적화하고 싶을 때
2. 정확한 도착/출발 시간이 필요할 때
3. 실제 도로 경로를 표시하고 싶을 때
4. 영업시간, 식사시간 제약을 고려해야 할 때
5. **단일 날짜 일정**을 계획할 때

**사용 흐름**:
```
Frontend → 장소 선택 + 선호도 입력 → /trip-planner/schedule → TripScheduler 실행 → 최적 일정 반환 → Frontend
```

**장점**:
- 시간 최적화
- 경로 최적화
- 제약 조건 고려
- 실제 도로 경로

**단점**:
- 복잡한 요청 (모든 정보 필요)
- 느린 응답 (특히 Real API)
- 단일 날짜만 처리
- 실패 가능성

---

## 6. 통합 사용 패턴

### 패턴 A: 2단계 프로세스 (권장)

```
1단계: /schedules/schedule
   - 장소 이름 → 상세 정보 조회
   - 빠른 응답

2단계: /trip-planner/schedule (날짜별로 반복)
   - 1단계 결과 사용
   - 날짜별로 최적화
   - 실제 경로 생성
```

**예시 흐름**:
```javascript
// 1단계: 장소 확장
const expandedPlaces = await fetch('/api/users/schedules/schedule', {
  body: { places_by_day: { "0": [...], "1": [...] } }
});

// 2단계: 각 날짜 최적화
const schedules = [];
for (let day = 0; day < totalDays; day++) {
  const dayPlaces = expandedPlaces.places_by_day[day];
  const optimized = await fetch('/api/trip-planner/schedule', {
    body: {
      places: dayPlaces,
      user: userPreferences,
      day_info: { is_first_day: day === 0, is_last_day: day === totalDays - 1 },
      use_mock: false
    }
  });
  schedules.push(optimized);
}
```

### 패턴 B: 직접 사용

```
직접 /trip-planner/schedule 호출
   - 모든 정보를 프론트엔드에서 준비
   - DB 조회 없이 바로 최적화
```

---

## 7. 주요 차이점 요약

| 특징 | Schedules Schedule | Trip Planner Schedule |
|------|-------------------|---------------------|
| **입력 복잡도** | 낮음 (이름 + time) | 높음 (모든 정보) |
| **처리 속도** | 빠름 (DB 조회만) | 느림 (최적화) |
| **날짜 범위** | Multi-day | Single day |
| **시간 계산** | ❌ 없음 | ✅ 정확한 계산 |
| **경로 생성** | ❌ 없음 | ✅ 실제 도로 경로 |
| **최적화** | ❌ 없음 | ✅ TSP 최적화 |
| **제약 조건** | ❌ 미고려 | ✅ 영업시간 등 고려 |
| **DB 의존성** | ✅ 필수 | ❌ 선택 |
| **실패 처리** | Skip | Fallback |

---

## 8. 권장 사항

### 프론트엔드 구현 가이드

1. **초기 장소 선택 단계**:
   - `/api/places/search` 또는 `/api/users/maps/select_hashtag`
   - 사용자가 장소 이름 선택

2. **장소 정보 확장**:
   - `/api/users/schedules/schedule`
   - 선택한 장소들의 상세 정보 조회

3. **일정 최적화** (날짜별):
   - `/api/trip-planner/schedule`
   - 각 날짜마다 별도로 호출
   - `use_mock: false` 사용 (프로덕션)

4. **최종 결과 저장/표시**:
   - 최적화된 일정과 경로 표시
   - 지도에 path 그리기

### 주의사항

1. **당일치기 처리**:
   - `is_first_day: true`, `is_last_day: true`일 때
   - Transport 노드 2개 필요 (출발, 도착)

2. **중간날 처리**:
   - `is_first_day: false`, `is_last_day: false`
   - Transport 0개 가능

3. **Real API 사용**:
   - 항상 `use_mock: false`
   - Naver API 키 필요
   - 비용 발생

---

## 9. 결론

두 엔드포인트는 **서로 다른 목적**을 가지고 있습니다:

- **Schedules Schedule**: 정보 확장 (DB 조회)
- **Trip Planner Schedule**: 일정 최적화 (TripScheduler)

**Best Practice**: 두 API를 순차적으로 사용
1. Schedules Schedule로 장소 정보 확장
2. Trip Planner Schedule로 날짜별 최적화

**핵심**: Trip Planner Schedule이 **실제 여행 일정 생성의 핵심**입니다.

---

**작성자**: Claude Code
**문서 버전**: 1.0