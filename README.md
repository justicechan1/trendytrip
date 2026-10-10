# Trendy Trip

해시태그 기반 감성 검색으로 맞춤 여행 일정을 추천하는 제주 여행 서비스입니다. 알고리즘 팀원과 입출력 JSON 규격을 맞춰, 추천·일정 최적화 알고리즘을 서비스로 연결하는 FastAPI 백엔드 API 전체를 설계·구현했습니다. 장소 데이터 수집(TourAPI 연동·크롤링)과 소개문 생성(Gemini API)은 단독으로 맡았습니다.

<img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white">
<img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white">
<img src="https://img.shields.io/badge/MySQL-4479A1?style=flat-square&logo=mysql&logoColor=white">
<img src="https://img.shields.io/badge/Gemini%20API-8E75B2?style=flat-square&logo=googlegemini&logoColor=white">
<img src="https://img.shields.io/badge/OR--Tools-4285F4?style=flat-square&logo=google&logoColor=white">
<img src="https://img.shields.io/badge/Vue%203-4FC08D?style=flat-square&logo=vuedotjs&logoColor=white">
<img src="https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white">
<img src="https://img.shields.io/badge/Naver%20Maps-03C75A?style=flat-square&logo=naver&logoColor=white">

## 프로젝트 개요

| 항목 | 내용 |
|---|---|
| 개발 기간 | 2025.01 ~ 2025.11 |
| 담당 | Back-end API (`be/app`) — 알고리즘 팀원이 요구한 데이터를 기준으로 API 설계, DB 장소·해시태그 데이터를 알고리즘 입력 JSON으로 구성하고 출력 JSON을 받아 화면용 응답으로 변환 (장소 검색, 해시태그 지도 탐색, 일정 생성·재계산)<br>장소 데이터 수집 (단독) — TourAPI 연동, 카페·음식점·숙소·관광지 크롤링, 읍면동 단위 분할 수집과 중복 제거<br>장소 소개문 생성 (단독) — Gemini API로 카페·음식점·관광지 10,902곳 소개문 일괄 생성 |
| 수상 | 교내 공학작품 전시회 최우수상 |
| 배경 | 여행지를 조건으로 검색하는 것을 넘어, 원하는 '분위기'로 장소를 찾고 하루 일정까지 자동으로 짜주는 제주 여행 플래너 |

## 아키텍처

```
fe/  Vue 3 + TypeScript + Vite    — 지도(Naver Maps) 기반 일정 플래너 UI, PDF/HTML 내보내기
be/
  app/                            — FastAPI 서버 (담당)
    routers/places.py             — 장소 통합 검색, 상세 조회
    routers/maps.py               — 지도 영역 내 해시태그 집계, 해시태그 유사 장소 검색
    routers/schedules.py          — 여행 일정 초기 생성, 일자별 동선 조회
    routers/trip_planner.py       — 알고리즘 입력 JSON 구성 → 일정 최적화 엔진 호출 → 출력 JSON 변환, 일정 재계산
    core/vector.py                — 임베딩 벡터 정규화
    cache.py                      — 사용자별 일정 인메모리 캐시
  TripScheduler/                  — OR-Tools 기반 경로/일정 최적화 알고리즘 (팀원)
  TripRecommendationSystem/       — 해시태그 임베딩 기반 장소 추천 알고리즘 (팀원)
```

## 주요 기능

- **장소 데이터 수집**: TourAPI 연동과 크롤링으로 제주 카페·음식점·숙소·관광지 데이터를 수집해 DB 구축
- **장소 소개문**: Gemini API로 카페 5,031 · 음식점 4,684 · 관광지 1,187곳의 소개문을 생성해 장소 상세에 제공
- **장소 검색**: 음식점·카페·관광지·숙소를 이름·카테고리·주소 키워드로 통합 검색하고, 장소 상세(주소·좌표·영업시간·편의시설·사진) 조회
- **해시태그 지도 탐색**: 현재 지도 화면(viewport) 안의 장소 해시태그를 빈도순으로 집계하고, 선택한 해시태그와 임베딩 유사도가 높은 장소를 반환
- **자동 일정 생성**: OR-Tools로 방문 시간대·영업시간·필수 방문지·이동 동선을 고려한 하루 일정 자동 배치
- **지도 시각화**: Naver Maps 연동, 일정을 경로선(Path)으로 시각화
- **일정 내보내기**: 완성된 일정을 PDF/HTML로 내보내기

## 트러블슈팅

1. **임베딩 벡터 타입 혼재·0벡터 예외 방어**
   - 문제: DB에서 읽은 해시태그 임베딩이 list/ndarray로 혼재되어 들어오고, 일부 항목은 0벡터라 코사인 유사도 계산 시 0으로 나누는 문제가 발생할 수 있었음
   - 해결: 임베딩을 `np.ndarray`로 강제 변환하고, L2 정규화 시 `+1e-8` epsilon을 더해 0벡터로 인한 `ZeroDivisionError`를 방지 (`vector.py`, `maps.py`)

2. **일정 재계산 응답속도 개선**
   - 문제: 사용자가 일정을 수정할 때마다 추천 로직 전체가 재실행되어 응답이 느려짐
   - 해결: 일정 재계산 API(`trip_planner.py`)를 조회 API와 분리하고, 세션 단위 인메모리 캐시(`cache.py`)로 직전 조회 결과를 재사용해 응답속도 개선

3. **장소 크롤링 누락 — 읍면동 단위 분할 수집**
   - 문제: 제주 전체를 한 번에 크롤링하면 검색 결과 상한에 걸려 누락되는 장소가 많았음
   - 해결: 수집 단위를 제주 읍면동으로 줄여 지역별로 나눠 수집하고, 지역 경계에서 겹쳐 수집된 장소는 최종 데이터에서 중복 제거

4. **장소 소개문 1만 건 일괄 생성 — 사용량 제한 대응**
   - 문제: 10,902곳을 한 건씩 Gemini에 요청하면 호출 수가 많아 API 사용량 제한에 걸릴 수 있었음
   - 해결: 장소를 20곳씩 묶어 546회 요청으로 줄이고, 무작위 20곳으로 프롬프트를 다듬은 뒤 다른 무작위 20곳으로 재검증하고 전체에 적용

## 로컬 실행

### Backend

```bash
cd be
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # DATABASE_URL, NAVER_API_CLIENT_ID/SECRET 채우기
uvicorn app.main:app --reload
```

### Frontend

```bash
cd fe
npm install
npm run dev
```

## DB

`DB_1107/DB_1107/Dump20251107(스키마만)/`에 테이블별 스키마(DDL)만 포함되어 있습니다. 실제 데이터가 포함된 전체 덤프는 용량 문제로 리포지토리에서 제외했습니다.
