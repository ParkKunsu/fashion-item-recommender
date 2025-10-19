"""
설정 관리 모듈
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    """크롤링 설정"""

    # 기본 경로
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    IMAGE_DIR = DATA_DIR / "images"
    CSV_DIR = DATA_DIR / "csv"

    # 무신사 URL
    BASE_URL = os.getenv("BASE_URL", "https://www.musinsa.com")
    RECOMMEND_URL = f"{BASE_URL}/main/musinsa/recommend"

    # 크롤링 설정
    HEADLESS = os.getenv("HEADLESS", "True").lower() == "true"
    PAGE_LOAD_TIMEOUT = int(os.getenv("PAGE_LOAD_TIMEOUT", "30"))
    IMPLICIT_WAIT = int(os.getenv("IMPLICIT_WAIT", "10"))

    # 이미지 다운로드 설정
    IMAGE_DOWNLOAD_PATH = Path(os.getenv("IMAGE_DOWNLOAD_PATH", str(IMAGE_DIR)))
    MAX_IMAGES_PER_PRODUCT = int(os.getenv("MAX_IMAGES_PER_PRODUCT", "10"))

    # 데이터 저장 설정
    CSV_OUTPUT_PATH = Path(os.getenv("CSV_OUTPUT_PATH", str(CSV_DIR)))

    # 타겟 브랜드
    TARGET_BRANDS = [
        brand.strip()
        for brand in os.getenv("TARGET_BRANDS", "").split(",")
        if brand.strip()
    ]

    # 크롤링 제한
    MAX_PRODUCTS_PER_BRAND = int(os.getenv("MAX_PRODUCTS_PER_BRAND", "100"))
    DELAY_BETWEEN_REQUESTS = int(os.getenv("DELAY_BETWEEN_REQUESTS", "2"))

    @classmethod
    def create_directories(cls):
        """필요한 디렉토리 생성"""
        cls.IMAGE_DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)
        cls.CSV_OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
