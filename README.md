# Fashion Item Recommender

브랜드 기반 패션 아이템 추천 시스템입니다. 사용자가 선호하는 브랜드를 입력하면 유사한 스타일의 의상을 추천합니다.

## 프로젝트 개요

패션 이커머스 플랫폼에서 데이터를 수집하고, 이미지와 메타데이터를 분석하여 개인화된 패션 아이템을 추천하는 AI 시스템입니다.

## 주요 기능

- 🔍 **브랜드 기반 데이터 수집**: 특정 브랜드의 상품 정보 및 이미지 자동 수집
- 🖼️ **이미지 분석**: OCR 및 이미지 특징 추출
- 🤖 **추천 시스템**: 사용자 선호 브랜드 기반 유사 아이템 추천
- 📊 **데이터 관리**: CSV/JSON 형식의 구조화된 데이터 저장

## 프로젝트 구조

```
fashion-item-recommender/
├── data_scraper/          # 데이터 수집 파이프라인
│   ├── scrapers/          # 크롤링 모듈
│   ├── utils/             # 유틸리티 (설정, 로깅, 이미지 다운로드)
│   ├── pipeline.py        # 데이터 수집 파이프라인
│   └── README.md          # 데이터 수집 모듈 상세 문서
│
├── feature_extraction/    # (예정) 이미지 특징 추출 모듈
├── recommender/           # (예정) 추천 엔진
├── api/                   # (예정) REST API 서버
└── README.md              # 프로젝트 전체 문서
```

## 기술 스택

### 데이터 수집
- Selenium + undetected-chromedriver
- BeautifulSoup4, Requests
- Pandas

### 이미지 처리 (예정)
- EasyOCR (텍스트 추출)
- PyTorch / TensorFlow (이미지 특징 추출)

### 추천 시스템 (예정)
- scikit-learn
- 협업 필터링 / 콘텐츠 기반 필터링

## 시작하기

### 1. 데이터 수집

```bash
cd data_scraper
pip install -r requirements.txt
cp .env.example .env
# .env 파일에서 TARGET_BRANDS 설정

python example_usage.py
```

자세한 사용법은 [data_scraper/README.md](data_scraper/README.md)를 참고하세요.

### 2. 추천 시스템 (개발 예정)

추후 업데이트 예정

## 개발 로드맵

- [x] 데이터 수집 파이프라인 구축
- [ ] OCR 기반 이미지 텍스트 추출
- [ ] 이미지 특징 벡터 추출 (CNN)
- [ ] 추천 알고리즘 개발
- [ ] 웹 인터페이스 / API 개발
- [ ] 모델 학습 및 평가

## 주의사항

이 프로젝트는 교육 및 연구 목적으로만 사용하세요.
