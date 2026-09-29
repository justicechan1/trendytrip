# Real API Mode Path 생성 문제 분석

**분석 일시**: 2025-09-30
**이슈**: Real API mode에서도 path가 제대로 생성되지 않음

---

## 문제 요약

`use_mock=False` (Real API mode)로 테스트 시:
- ✅ API 호출 성공 (200 OK)
- ✅ `visits` 배열 생성됨
- ❌ `path` 배열이 단순함 (시작점-끝점만, 2개 좌표)
- ❌ TripScheduler가 실제로 실행되지 않음

**예상**: 실제 도로를 따라 수십 개의 좌표
**실제**: 직선 경로 (2개 좌표만)

---

## 근본 원인 발견

### 백엔드 로그 분석

```
[SCHEDULER_API] Valid combinations: 1
[SCHEDULER_API] Testing combination: ()
[SCHEDULER_API] Scheduler failed: 당일치기 여행에서 transport 노드가 정확히 2개 있어야 합니다.
[SCHEDULER_API] Traceback: ...
ValueError: 시작/종료 노드 결정 실패: 당일치기 여행에서 transport 노드가 정확히 2개 있어야 합니다.

[DEBUG] 스케줄러 결과가 비어있음: {'visits': [], 'path': []}
[DEBUG] 기본 응답 사용
```

**핵심 문제**:
- TripScheduler가 예외를 발생시킴
- 당일치기 여행(`is_first_day: true`, `is_last_day: true`)에서 **transport 노드 2개 필요**
- 테스트 데이터는 transport가 1개만 제공됨 (제주국제공항)
- → 검증 실패 → fallback 로직 실행 → 간단한 path 생성

### 코드 위치

**에러 발생 위치**: `TripScheduler/tripscheduler/core/indexing/handlers.py:78`

```python
def handle_one_day_trip(...):
    if len(transport_indices) != 2:
        raise ValueError("당일치기 여행에서 transport 노드가 정확히 2개 있어야 합니다.")
```

**검증 로직**: `TripScheduler/tripscheduler/core/indexing/handlers.py:116`

```python
def determine_start_end_indices(places, day_info):
    if day_info["is_first_day"] and day_info["is_last_day"]:
        return handler(places, acc_indices, transport_indices, start_index, end_index)
```

---

## TripScheduler의 Transport 요구사항

### 여행 타입별 Transport 필요 개수

| 여행 타입 | is_first_day | is_last_day | Transport 개수 |
|---------|-------------|------------|--------------|
| 당일치기 | true | true | **2개** (출발, 도착) |
| 첫째날 | true | false | 1개 (출발) |
| 중간날 | false | false | 0개 |
| 마지막날 | false | true | 1개 (도착) |

### Transport의 역할

1. **출발 Transport**: 여행 시작점 (예: 제주국제공항 도착)
2. **도착 Transport**: 여행 종료점 (예: 제주국제공항 출발)

당일치기 여행은 같은 날 도착하고 출발하므로 2개 필요.

---

## 테스트 데이터 문제

### 현재 테스트 데이터

```json
{
  "places": [
    {
      "id": 1,
      "name": "제주국제공항",
      "category": "transport",
      "is_mandatory": true  // Transport 1개만
    },
    {
      "id": 2,
      "name": "용두암",
      "category": "landmark"
    },
    {
      "id": 3,
      "name": "동문재래시장",
      "category": "landmark"
    }
  ],
  "day_info": {
    "is_first_day": true,   // 당일치기
    "is_last_day": true     // 당일치기
  }
}
```

**문제**: Transport가 1개뿐 → TripScheduler 검증 실패

---

## 해결 방법

### 방법 1: Transport 노드 2개 제공 (권장)

당일치기 여행 시 출발과 도착 transport를 명시:

```json
{
  "places": [
    {
      "id": 1,
      "name": "제주국제공항 (도착)",
      "category": "transport",
      "service_time": 30,
      "is_mandatory": true
    },
    {
      "id": 2,
      "name": "용두암",
      "category": "landmark",
      "service_time": 60
    },
    {
      "id": 3,
      "name": "동문재래시장",
      "category": "landmark",
      "service_time": 90
    },
    {
      "id": 4,
      "name": "제주국제공항 (출발)",
      "category": "transport",
      "service_time": 30,
      "is_mandatory": true
    }
  ],
  "day_info": {
    "is_first_day": true,
    "is_last_day": true
  }
}
```

**장점**:
- TripScheduler가 정상 실행됨
- 실제 도로 경로 생성
- 공항 도착/출발 시간 고려

### 방법 2: 여행 타입 변경

당일치기가 아닌 다른 타입으로 변경:

```json
{
  "day_info": {
    "is_first_day": true,
    "is_last_day": false  // 중간에 계속됨
  }
}
```

**장점**: Transport 1개로 가능
**단점**: 의미론적으로 부정확 (실제로는 당일치기인데...)

### 방법 3: TripScheduler 검증 로직 완화

`handlers.py`의 검증을 완화하여 transport 1개도 허용:

```python
def handle_one_day_trip(...):
    if len(transport_indices) == 1:
        # 같은 transport를 출발과 도착으로 사용
        start_idx = end_idx = transport_indices[0]
        return start_idx, end_idx
    elif len(transport_indices) == 2:
        # 기존 로직
        ...
```

**장점**: 기존 테스트 데이터 그대로 사용
**단점**: TripScheduler 로직 변경 필요, 의도 변경

---

## 테스트 케이스 수정

### 올바른 당일치기 테스트

```python
test_data = {
    "places": [
        {
            "id": 1,
            "name": "제주국제공항 (도착)",
            "x_cord": 126.4959513,
            "y_cord": 33.5059365,
            "category": "transport",
            "service_time": 30,
            "open_time": "00:00",
            "close_time": "23:59",
            "is_mandatory": True
        },
        {
            "id": 2,
            "name": "용두암",
            "x_cord": 126.5114,
            "y_cord": 33.514892,
            "category": "landmark",
            "service_time": 60,
            "open_time": "00:00",
            "close_time": "23:59"
        },
        {
            "id": 3,
            "name": "동문재래시장",
            "x_cord": 126.5345,
            "y_cord": 33.5125,
            "category": "landmark",
            "service_time": 90,
            "open_time": "08:00",
            "close_time": "20:00"
        },
        {
            "id": 4,
            "name": "제주국제공항 (출발)",
            "x_cord": 126.4959513,
            "y_cord": 33.5059365,
            "category": "transport",
            "service_time": 30,
            "open_time": "00:00",
            "close_time": "23:59",
            "is_mandatory": True
        }
    ],
    "user": {
        "start_time": "09:00",
        "end_time": "18:00",
        "travel_style": "normal",
        "meal_time_preferences": {
            "lunch": ["12:00", "13:30"],
            "dinner": ["18:00", "19:30"]
        }
    },
    "day_info": {
        "type": "normal",
        "is_first_day": True,
        "is_last_day": True,
        "date": "2025-10-01",
        "weekday": "수요일"
    },
    "use_mock": False
}
```

### 올바른 중간날 테스트

```python
test_data = {
    "places": [
        {
            "id": 2,
            "name": "용두암",
            "x_cord": 126.5114,
            "y_cord": 33.514892,
            "category": "landmark",
            "service_time": 60
        },
        {
            "id": 3,
            "name": "동문재래시장",
            "x_cord": 126.5345,
            "y_cord": 33.5125,
            "category": "landmark",
            "service_time": 90
        }
    ],
    "day_info": {
        "is_first_day": False,  // 중간날
        "is_last_day": False
    },
    "use_mock": False
}
```

---

## 프론트엔드 대응 방안

### 당일치기 여행 처리

```typescript
function preparePlacesForSchedule(places, tripType) {
  if (tripType.isFirstDay && tripType.isLastDay) {
    // 당일치기: transport가 있다면 복제하여 시작/끝에 추가
    const transportPlace = places.find(p => p.category === 'transport');

    if (transportPlace) {
      return [
        { ...transportPlace, name: `${transportPlace.name} (도착)` },
        ...places.filter(p => p.category !== 'transport'),
        { ...transportPlace, name: `${transportPlace.name} (출발)`, id: transportPlace.id + 1000 }
      ];
    }
  }

  return places;
}
```

### 여행 타입 자동 결정

```typescript
interface TripDay {
  date: string;
  places: Place[];
}

function determineDayType(dayIndex: number, totalDays: number) {
  const isFirstDay = dayIndex === 0;
  const isLastDay = dayIndex === totalDays - 1;

  return {
    is_first_day: isFirstDay,
    is_last_day: isLastDay,
    // 당일치기: transport 2개 필요
    // 첫째날: transport 1개 (출발)
    // 마지막날: transport 1개 (도착)
    // 중간날: transport 0개
  };
}
```

---

## 권장 사항

### 즉시 조치

1. **당일치기 테스트 수정**
   - Transport 노드 2개로 변경
   - 출발/도착 명확히 구분

2. **프론트엔드 로직 추가**
   - 당일치기 자동 감지
   - Transport 자동 복제

3. **TripScheduler 에러 처리**
   - 명확한 에러 메시지
   - 사용자 친화적 피드백

### 장기 개선

1. **TripScheduler 유연성 향상**
   - Transport 1개도 허용
   - 같은 장소를 시작/끝으로 사용

2. **테스트 커버리지 확대**
   - 모든 여행 타입 테스트
   - Transport 조합 테스트

3. **문서화**
   - TripScheduler 요구사항 명시
   - API 문서에 예제 추가

---

## 결론

**현재 상태**: Real API mode에서도 TripScheduler가 실행되지 않음

**원인**: 당일치기 여행에서 transport 노드 1개만 제공 (2개 필요)

**해결**: Transport 노드를 2개로 변경하거나, 중간날 타입으로 변경

**영향**: 프론트엔드에서 당일치기 처리 로직 필요

---

**작성자**: Claude Code
**문서 버전**: 1.0