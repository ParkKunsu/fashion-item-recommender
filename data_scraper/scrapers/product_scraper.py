"""
상품 상세 페이지 스크래퍼 (Playwright 기반)
"""
import time
from playwright.sync_api import sync_playwright, Browser, Page, Playwright
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from pathlib import Path
import json

from ..utils.logger import setup_logger
from ..utils.config import Config
from ..utils.image_downloader import ImageDownloader

logger = setup_logger(__name__)


class ProductScraper:
    """상품 상세 정보 스크래퍼 (Playwright)"""

    def __init__(self, headless: bool = True):
        """
        Args:
            headless: 헤드리스 모드 여부
        """
        self.headless = headless
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.image_downloader = ImageDownloader(Config.IMAGE_DOWNLOAD_PATH)

    def __enter__(self):
        self._init_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _init_browser(self):
        """Playwright 브라우저 초기화"""
        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
            ]
        )

        # 새 컨텍스트 생성 (브라우저 세션)
        context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        self.page = context.new_page()

        # 기본 타임아웃 설정
        self.page.set_default_timeout(Config.PAGE_LOAD_TIMEOUT * 1000)

        logger.info("Playwright 브라우저 초기화 완료")

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

            # 페이지 이동 및 로딩 완료 대기
            self.page.goto(url, wait_until='networkidle')

            # 추가 대기 (동적 콘텐츠 로딩)
            self.page.wait_for_timeout(2000)

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
            'url': self.page.url
        }

        try:
            # 페이지 HTML 가져오기
            html_content = self.page.content()
            soup = BeautifulSoup(html_content, 'lxml')

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
            main_images = self.page.query_selector_all('div.product-img img')
            for img in main_images:
                src = img.get_attribute('src')
                if src and src.startswith('http'):
                    image_urls.append(src)

            # 썸네일 이미지에서 원본 URL 추출
            thumbnails = self.page.query_selector_all('ul.product_thumb img')
            for thumb in thumbnails:
                src = thumb.get_attribute('src')
                if src and src.startswith('http'):
                    # 썸네일을 원본 이미지로 변환
                    original_url = src.replace('_125.', '_500.')
                    if original_url not in image_urls:
                        image_urls.append(original_url)

            # 상세 이미지 (스크롤 다운하여 로딩)
            try:
                # 페이지 하단으로 스크롤
                self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                self.page.wait_for_timeout(2000)

                detail_images = self.page.query_selector_all('div.detail_info img')
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
        """브라우저 종료"""
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("Playwright 브라우저 종료")
