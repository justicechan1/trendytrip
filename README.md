# Trendy Trip

해시태그 기반 감성 검색으로 맞춤 여행 일정을 추천하는 제주 여행 서비스입니다. 이 중 장소 검색 API를 담당했습니다.

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
| 담당 | 장소 검색 API — 음식점·카페·관광지·숙소 통합 검색, 장소 상세 조회 |
| 배경 | 여행지를 조건으로 검색하는 것을 넘어, 원하는 '분위기'로 장소를 찾고 하루 일정까지 자동으로 짜주는 제주 여행 플래너 |

## 아키텍처

```
fe/  Vue 3 + TypeScript + Vite    — 지도(Naver Maps) 기반 일정 플래너 UI, PDF/HTML 내보내기
be/  FastAPI                      — 장소 검색·일정 생성 API
  app/routers/places.py           — 장소 검색 API (담당)
  app/core/search.py, vector.py   — 해시태그 유사도 계산 (팀원)
  app/cache.py                    — 사용자별 임시 일정/장소 인메모리 캐시 (팀원)
  TripScheduler/                  — OR-Tools 기반 경로/일정 최적화 엔진 (팀원)
  TripRecommendationSystem/       — 해시태그 임베딩 유사도 기반 장소 추천 (팀원)
```

## 주요 기능

- **장소 검색 (담당)**: 음식점·카페·관광지·숙소를 이름·카테고리·주소 키워드로 통합 검색하고, 장소 상세(주소·좌표·영업시간·편의시설·사진) 조회
- **해시태그 기반 감성 추천**: 장소 해시태그 임베딩 유사도로 분위기에 맞는 장소 추천
- **자동 일정 생성**: OR-Tools로 방문 시간대·영업시간·필수 방문지·이동 동선을 고려한 하루 일정 자동 배치
- **지도 시각화**: Naver Maps 연동, 일정을 경로선(Path)으로 시각화
- **일정 내보내기**: 완성된 일정을 PDF/HTML로 내보내기

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
