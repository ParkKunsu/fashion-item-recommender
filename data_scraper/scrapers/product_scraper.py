"""
무신사 상품 상세 페이지 스크래퍼
"""
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from pathlib import Path
import json

from ..utils.logger import setup_logger
from ..utils.config import Config
from ..utils.image_downloader import ImageDownloader

logger = setup_logger(__name__)


class ProductScraper:
    """무신사 상품 상세 정보 스크래퍼"""

    def __init__(self, headless: bool = True):
        """
        Args:
            headless: 헤드리스 모드 여부
        """
        self.headless = headless
        self.driver = None
        self.image_downloader = ImageDownloader(Config.IMAGE_DOWNLOAD_PATH)

    def __enter__(self):
        self._init_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _init_driver(self):
        """Chrome 드라이버 초기화"""
        options = uc.ChromeOptions()

        if self.headless:
            options.add_argument('--headless=new')

        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        self.driver = uc.Chrome(options=options)
        self.driver.implicitly_wait(Config.IMPLICIT_WAIT)
        logger.info("Chrome 드라이버 초기화 완료")

    def scrape_product(
        self,
        product_id: str,
        download_images: bool = True
    ) -> Optional[Dict]:
        """
        상품 상세 정보 스크래핑

        Args:
            product_id: 상품 ID
            download_images: 이미지 다운로드 여부

        Returns:
            상품 정보 딕셔너리
        """
        url = f"{Config.BASE_URL}/products/{product_id}"

        try:
            logger.info(f"상품 페이지 접속: {url}")
            self.driver.get(url)

            # 페이지 로딩 대기
            time.sleep(3)

            # 상품 정보 추출
            product_data = self._extract_product_info(product_id)

            # 이미지 추출
            image_urls = self._extract_image_urls()
            product_data['image_urls'] = image_urls
            product_data['image_count'] = len(image_urls)

            # 이미지 다운로드
            if download_images and image_urls:
                downloaded_paths = self.image_downloader.download_images(
                    image_urls,
                    product_id,
                    max_images=Config.MAX_IMAGES_PER_PRODUCT
                )
                product_data['downloaded_images'] = [str(p) for p in downloaded_paths]

            logger.info(f"상품 {product_id} 스크래핑 완료")
            return product_data

        except Exception as e:
            logger.error(f"상품 {product_id} 스크래핑 실패: {e}")
            return None

    def _extract_product_info(self, product_id: str) -> Dict:
        """상품 기본 정보 추출"""
        product_data = {
            'product_id': product_id,
            'url': self.driver.current_url
        }

        try:
            # BeautifulSoup으로 파싱
            soup = BeautifulSoup(self.driver.page_source, 'lxml')

            # 상품명
            try:
                product_name = soup.select_one('span.product_title')
                if product_name:
                    product_data['product_name'] = product_name.get_text(strip=True)
            except:
                pass

            # 브랜드명
            try:
                brand = soup.select_one('p.product_article a')
                if brand:
                    product_data['brand'] = brand.get_text(strip=True)
            except:
                pass

            # 가격
            try:
                price = soup.select_one('span.product_price span')
                if price:
                    product_data['price'] = price.get_text(strip=True)
            except:
                pass

            # 할인율
            try:
                discount = soup.select_one('span.product_article_price span.product_discount')
                if discount:
                    product_data['discount_rate'] = discount.get_text(strip=True)
            except:
                pass

            # 상품 설명
            try:
                description = soup.select_one('p.product_summary')
                if description:
                    product_data['description'] = description.get_text(strip=True)
            except:
                pass

            # 카테고리
            try:
                category_elements = soup.select('p.product_article span')
                categories = [cat.get_text(strip=True) for cat in category_elements]
                if categories:
                    product_data['categories'] = categories
            except:
                pass

        except Exception as e:
            logger.warning(f"상품 정보 추출 중 오류: {e}")

        return product_data

    def _extract_image_urls(self) -> List[str]:
        """상품 이미지 URL 추출"""
        image_urls = []

        try:
            # 메인 상품 이미지
            main_images = self.driver.find_elements(By.CSS_SELECTOR, 'div.product-img img')
            for img in main_images:
                src = img.get_attribute('src')
                if src and src.startswith('http'):
                    image_urls.append(src)

            # 썸네일 이미지에서 원본 URL 추출
            thumbnails = self.driver.find_elements(By.CSS_SELECTOR, 'ul.product_thumb img')
            for thumb in thumbnails:
                src = thumb.get_attribute('src')
                if src and src.startswith('http'):
                    # 썸네일을 원본 이미지로 변환 (무신사의 이미지 URL 패턴)
                    original_url = src.replace('_125.', '_500.')
                    if original_url not in image_urls:
                        image_urls.append(original_url)

            # 상세 이미지 (스크롤 다운하여 로딩)
            try:
                # 페이지 하단으로 스크롤
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

                detail_images = self.driver.find_elements(By.CSS_SELECTOR, 'div.detail_info img')
                for img in detail_images:
                    src = img.get_attribute('src')
                    if src and src.startswith('http') and src not in image_urls:
                        image_urls.append(src)
            except:
                pass

            logger.info(f"추출된 이미지 URL 개수: {len(image_urls)}")

        except Exception as e:
            logger.error(f"이미지 URL 추출 실패: {e}")

        return image_urls

    def scrape_products(
        self,
        product_ids: List[str],
        delay: int = 2
    ) -> List[Dict]:
        """
        여러 상품 스크래핑

        Args:
            product_ids: 상품 ID 리스트
            delay: 요청 간 대기 시간 (초)

        Returns:
            상품 정보 리스트
        """
        products = []

        for idx, product_id in enumerate(product_ids):
            logger.info(f"진행률: {idx + 1}/{len(product_ids)}")

            product_data = self.scrape_product(product_id)
            if product_data:
                products.append(product_data)

            # 마지막 상품이 아니면 대기
            if idx < len(product_ids) - 1:
                time.sleep(delay)

        return products

    def close(self):
        """드라이버 종료"""
        if self.driver:
            self.driver.quit()
            logger.info("Chrome 드라이버 종료")
