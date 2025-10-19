# 데이터 수집 파이프라인 (Data Scraper)

무신사 등 이커머스 웹사이트에서 브랜드별 상품 이미지와 정보를 수집하는 자동화 크롤링 파이프라인입니다.

## 주요 기능

- 브랜드별 상품 검색 및 수집
- 상품 상세 정보 추출 (상품명, 브랜드, 가격, 할인율 등)
- 상품 이미지 자동 다운로드
- CSV/JSON 형식으로 데이터 저장
- 무신사 추천 페이지 크롤링
- 헤드리스 모드 지원 (백그라운드 실행)

## 기술 스택

- **Playwright**: 빠르고 안정적인 브라우저 자동화
- **BeautifulSoup4**: HTML 파싱
- **Requests**: 이미지 다운로드
- **Pillow**: 이미지 처리
- **Pandas**: 데이터 관리 및 저장

## 설치 방법

### 1. 필수 패키지 설치

```bash
cd data_scraper
pip install -r requirements.txt

# Playwright 브라우저 설치 (필수)
playwright install chromium
```

### 2. 환경 변수 설정

`.env.example` 파일을 `.env`로 복사하고 필요한 설정을 수정합니다:

```bash
cp .env.example .env
```

`.env` 파일 예시:
```
TARGET_BRANDS=무신사 스탠다드,커버낫,디스이즈네버댓
MAX_PRODUCTS_PER_BRAND=50
HEADLESS=True
DELAY_BETWEEN_REQUESTS=2
```

## 사용 방법

### 1. 브랜드별 데이터 수집

```python
from pipeline import DataPipeline

# 파이프라인 초기화
pipeline = DataPipeline()

# 브랜드별 데이터 수집
pipeline.run_brand_pipeline(
    brand_names=["무신사 스탠다드", "커버낫"],
    max_products_per_brand=20,
    download_images=True,
    headless=True
)

# 결과 저장
pipeline.save_to_csv()
pipeline.save_to_json()
```

### 2. 단일 상품 수집

```python
from scrapers.product_scraper import ProductScraper

product_id = "3782941"  # 상품 URL에서 추출

with ProductScraper(headless=True) as scraper:
    product_data = scraper.scrape_product(product_id, download_images=True)
    print(product_data)
```

### 3. 추천 페이지 크롤링

```python
from pipeline import DataPipeline

pipeline = DataPipeline()

# 추천 페이지 데이터 수집
pipeline.run_recommend_pipeline(
    gender_filter='A',  # A: 전체, M: 남성, W: 여성
    max_products=30,
    download_images=True
)

pipeline.save_to_csv("recommend_products.csv")
```

### 4. 예제 코드 실행

```bash
python example_usage.py
```

## 프로젝트 구조

```
data_scraper/
├── scrapers/
│   ├── __init__.py
│   ├── product_scraper.py      # 상품 상세 정보 스크래퍼
│   └── brand_crawler.py        # 브랜드 검색 크롤러
├── utils/
│   ├── __init__.py
│   ├── config.py               # 설정 관리
│   ├── logger.py               # 로깅 유틸리티
│   └── image_downloader.py     # 이미지 다운로더
├── data/
│   ├── images/                 # 다운로드된 이미지
│   └── csv/                    # 수집된 데이터 (CSV/JSON)
├── pipeline.py                 # 메인 파이프라인
├── example_usage.py            # 사용 예제
├── requirements.txt            # 필수 패키지
├── .env.example               # 환경 변수 예제
└── README.md                  # 프로젝트 문서
```

## 수집되는 데이터

### 상품 정보
- `product_id`: 상품 ID
- `product_name`: 상품명
- `brand`: 브랜드명
- `price`: 가격
- `discount_rate`: 할인율
- `description`: 상품 설명
- `categories`: 카테고리
- `url`: 상품 URL

### 이미지 정보
- `image_urls`: 이미지 URL 리스트
- `image_count`: 이미지 개수
- `downloaded_images`: 다운로드된 이미지 경로 리스트

## 다음 단계: OCR 처리

이미지에서 텍스트 추출이 필요한 경우 EasyOCR을 사용할 수 있습니다:

```python
import easyocr

# OCR 리더 초기화 (한국어 + 영어)
reader = easyocr.Reader(['ko', 'en'])

# 이미지에서 텍스트 추출
image_path = "data/images/3782941/3782941_0.jpg"
result = reader.readtext(image_path)

for detection in result:
    text = detection[1]
    confidence = detection[2]
    print(f"텍스트: {text}, 신뢰도: {confidence:.2f}")
```

## 주의사항

1. **크롤링 속도 제한**: 서버 부하를 줄이기 위해 요청 간 적절한 지연 시간을 설정하세요 (`DELAY_BETWEEN_REQUESTS`)
2. **헤드리스 모드**: 개발/디버깅 시에는 `headless=False`로 설정하여 브라우저 동작을 확인할 수 있습니다
3. **법적 책임**: 크롤링은 웹사이트 이용약관을 준수하여 사용하세요
4. **로봇 배제 표준**: robots.txt를 확인하고 준수하세요

## 문제 해결

### Playwright 브라우저 오류
```bash
# Playwright 브라우저 재설치
playwright install chromium

# 의존성 설치 (Linux)
playwright install-deps chromium
```

### 메모리 부족
- `max_products_per_brand` 값을 줄이세요
- 이미지 다운로드를 비활성화하세요 (`download_images=False`)

### 성능 최적화
Playwright는 Selenium 대비 20-30% 빠른 성능을 제공합니다:
- 자동 대기 메커니즘으로 안정성 향상
- 네트워크 유휴 상태까지 대기 (`wait_until='networkidle'`)
- 더 적은 메모리 사용량

## 라이센스

이 프로젝트는 교육 및 연구 목적으로만 사용하세요.
