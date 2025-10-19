"""
브랜드별 상품 목록 크롤러
"""
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re

from ..utils.logger import setup_logger
from ..utils.config import Config

logger = setup_logger(__name__)


class BrandCrawler:
    """브랜드별 상품 목록 크롤러"""

    def __init__(self, headless: bool = True):
        """
        Args:
            headless: 헤드리스 모드 여부
        """
        self.headless = headless
        self.driver = None

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
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        self.driver = uc.Chrome(options=options)
        self.driver.implicitly_wait(Config.IMPLICIT_WAIT)
        logger.info("Chrome 드라이버 초기화 완료")

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
            # 무신사 메인 페이지
            logger.info(f"브랜드 '{brand_name}' 검색 시작")
            self.driver.get(Config.BASE_URL)
            time.sleep(2)

            # 검색창 찾기 및 검색
            search_box = self.driver.find_element(By.CSS_SELECTOR, 'input[type="search"], input.search-input')
            search_box.clear()
            search_box.send_keys(brand_name)
            search_box.send_keys(Keys.RETURN)

            time.sleep(3)

            # 브랜드 필터 적용 (가능한 경우)
            try:
                brand_filter = self.driver.find_element(By.XPATH, f"//a[contains(text(), '{brand_name}')]")
                brand_filter.click()
                time.sleep(2)
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

            self.driver.get(url)
            time.sleep(3)

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
            soup = BeautifulSoup(self.driver.page_source, 'lxml')

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
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

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
        """드라이버 종료"""
        if self.driver:
            self.driver.quit()
            logger.info("Chrome 드라이버 종료")
