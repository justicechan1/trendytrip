# Trendy Trip

Gemini 임베딩 기반 시맨틱 검색으로 감성 맞춤 여행 일정을 추천하는 제주 여행 서비스입니다. Back-end를 전담했습니다.

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
| 개발 기간 | 2025.01 ~ 2025.07 |
| 담당 | Back-end 전담 |
| 배경 | 여행지를 조건으로 검색하는 것을 넘어, 원하는 '분위기'로 장소를 찾고 하루 일정까지 자동으로 짜주는 제주 여행 플래너 |

## 아키텍처

```
fe/  Vue 3 + TypeScript + Vite    — 지도(Naver Maps) 기반 일정 플래너 UI, PDF/HTML 내보내기
be/  FastAPI                      — 장소 검색·일정 생성 API
  app/core/search.py, vector.py   — 임베딩 유사도 계산, 벡터 정규화
  app/cache.py                    — 사용자별 임시 일정/장소 인메모리 캐시
  TripScheduler/                  — OR-Tools 기반 경로/일정 최적화 엔진
  TripRecommendationSystem/       — 해시태그 임베딩 유사도 기반 장소 추천
```

## 주요 기능

- **해시태그 기반 감성 검색**: 카페·숙소·음식점·관광지·교통 데이터를 해시태그 임베딩으로 벡터화해 유사도 기반으로 추천
- **자동 일정 생성**: OR-Tools로 방문 시간대·영업시간·필수 방문지·이동 동선을 고려한 하루 일정 자동 배치
- **지도 시각화**: Naver Maps 연동, 일정을 경로선(Path)으로 시각화
- **일정 내보내기**: 완성된 일정을 PDF/HTML로 내보내기

## 트러블슈팅

1. **임베딩 벡터 타입 혼재·0벡터 예외 방어**
   - 문제: 장소별 해시태그 임베딩이 list/ndarray로 혼재되어 들어오고, 일부 항목은 0벡터라 코사인 유사도 계산 시 0으로 나누는 문제가 발생할 수 있었음
   - 해결: 임베딩을 `np.ndarray`로 강제 변환하고, L2 정규화 시 `+1e-8` epsilon을 더해 0벡터로 인한 `ZeroDivisionError`를 방지 (`vector.py`, `embedding_similarity.py`)

2. **일정 재계산 응답속도 개선**
   - 문제: 사용자가 일정을 수정할 때마다 추천 로직 전체가 재실행되어 응답이 느려짐
   - 해결: 일정 재계산 API(`trip_planner.py`)를 조회 API와 분리하고, 세션 단위 인메모리 캐시(`cache.py`)로 직전 조회 결과를 재사용해 응답속도 개선

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
