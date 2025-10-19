"""
브랜드별 상품 목록 크롤러 (Playwright 기반)
"""
import time
from playwright.sync_api import sync_playwright, Browser, Page, Playwright
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re

from ..utils.logger import setup_logger
from ..utils.config import Config

logger = setup_logger(__name__)


class BrandCrawler:
    """브랜드별 상품 목록 크롤러 (Playwright)"""

    def __init__(self, headless: bool = True):
        """
        Args:
            headless: 헤드리스 모드 여부
        """
        self.headless = headless
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

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

        # 새 컨텍스트 생성
        context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

        self.page = context.new_page()

        # 기본 타임아웃 설정
        self.page.set_default_timeout(Config.PAGE_LOAD_TIMEOUT * 1000)

        logger.info("Playwright 브라우저 초기화 완료")

    def search_brand_products(
        self,
        brand_name: str,
        max_products: Optional[int] = None
    ) -> List[str]:
        """
        브랜드 검색 후 상품 ID 목록 추출

        Args:
            brand_name: 브랜드명
            max_products: 최대 상품 수

        Returns:
            상품 ID 리스트
        """
        try:
            logger.info(f"브랜드 '{brand_name}' 검색 시작")

            # 무신사 메인 페이지 이동
            self.page.goto(Config.BASE_URL, wait_until='networkidle')
            self.page.wait_for_timeout(2000)

            # 검색창 찾기 및 검색
            search_input = self.page.query_selector('input[type="search"], input.search-input')
            if search_input:
                search_input.fill(brand_name)
                search_input.press('Enter')

                # 검색 결과 로딩 대기
                self.page.wait_for_timeout(3000)

                # 브랜드 필터 적용 시도
                try:
                    brand_filter = self.page.query_selector(f'xpath=//a[contains(text(), "{brand_name}")]')
                    if brand_filter:
                        brand_filter.click()
                        self.page.wait_for_timeout(2000)
                except:
                    logger.warning("브랜드 필터를 찾을 수 없습니다. 검색 결과를 그대로 사용합니다.")

                # 상품 ID 추출
                product_ids = self._extract_product_ids(max_products)

                logger.info(f"브랜드 '{brand_name}': {len(product_ids)}개 상품 발견")
                return product_ids

        except Exception as e:
            logger.error(f"브랜드 '{brand_name}' 검색 실패: {e}")
            return []

    def get_recommend_products(
        self,
        gender_filter: str = 'A',
        max_products: Optional[int] = None
    ) -> List[str]:
        """
        추천 페이지에서 상품 ID 추출

        Args:
            gender_filter: 성별 필터 (A: 전체, M: 남성, W: 여성)
            max_products: 최대 상품 수

        Returns:
            상품 ID 리스트
        """
        try:
            url = f"{Config.RECOMMEND_URL}?gf={gender_filter}"
            logger.info(f"추천 페이지 접속: {url}")

            # 페이지 이동 및 네트워크 대기
            self.page.goto(url, wait_until='networkidle')
            self.page.wait_for_timeout(3000)

            # 스크롤하여 더 많은 상품 로딩
            self._scroll_to_load_products()

            # 상품 ID 추출
            product_ids = self._extract_product_ids(max_products)

            logger.info(f"추천 페이지에서 {len(product_ids)}개 상품 발견")
            return product_ids

        except Exception as e:
            logger.error(f"추천 페이지 크롤링 실패: {e}")
            return []

    def _extract_product_ids(self, max_products: Optional[int] = None) -> List[str]:
        """현재 페이지에서 상품 ID 추출"""
        product_ids = []

        try:
            # 페이지 HTML 가져오기
            html_content = self.page.content()
            soup = BeautifulSoup(html_content, 'lxml')

            # 상품 링크에서 ID 추출
            product_links = soup.select('a[href*="/products/"]')

            for link in product_links:
                href = link.get('href', '')
                match = re.search(r'/products/(\d+)', href)
                if match:
                    product_id = match.group(1)
                    if product_id not in product_ids:
                        product_ids.append(product_id)

                        if max_products and len(product_ids) >= max_products:
                            break

        except Exception as e:
            logger.error(f"상품 ID 추출 실패: {e}")

        return product_ids

    def _scroll_to_load_products(self, scroll_count: int = 5):
        """페이지 스크롤하여 상품 로딩"""
        try:
            for i in range(scroll_count):
                # 페이지 하단으로 스크롤
                self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                self.page.wait_for_timeout(2000)

                logger.info(f"스크롤 {i + 1}/{scroll_count}")

        except Exception as e:
            logger.warning(f"스크롤 중 오류: {e}")

    def get_brand_products_multi(
        self,
        brand_names: List[str],
        max_products_per_brand: Optional[int] = None
    ) -> Dict[str, List[str]]:
        """
        여러 브랜드의 상품 목록 추출

        Args:
            brand_names: 브랜드명 리스트
            max_products_per_brand: 브랜드당 최대 상품 수

        Returns:
            {브랜드명: [상품ID 리스트]} 딕셔너리
        """
        results = {}

        for brand_name in brand_names:
            product_ids = self.search_brand_products(brand_name, max_products_per_brand)
            results[brand_name] = product_ids

            # 다음 브랜드 검색 전 대기
            time.sleep(Config.DELAY_BETWEEN_REQUESTS)

        return results

    def close(self):
        """브라우저 종료"""
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("Playwright 브라우저 종료")
