"""
데이터 수집 파이프라인 오케스트레이터
"""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import json

from .scrapers.brand_crawler import BrandCrawler
from .scrapers.product_scraper import ProductScraper
from .utils.config import Config
from .utils.logger import setup_logger

logger = setup_logger(__name__)


class DataPipeline:
    """데이터 수집 파이프라인"""

    def __init__(self):
        """파이프라인 초기화"""
        Config.create_directories()
        self.results = []

    def run_brand_pipeline(
        self,
        brand_names: List[str],
        max_products_per_brand: Optional[int] = None,
        download_images: bool = True,
        headless: bool = True
    ):
        """
        브랜드별 데이터 수집 파이프라인 실행

        Args:
            brand_names: 브랜드명 리스트
            max_products_per_brand: 브랜드당 최대 상품 수
            download_images: 이미지 다운로드 여부
            headless: 헤드리스 모드 여부
        """
        logger.info("=" * 60)
        logger.info("무신사 데이터 수집 파이프라인 시작")
        logger.info(f"타겟 브랜드: {', '.join(brand_names)}")
        logger.info("=" * 60)

        # 1단계: 브랜드별 상품 ID 수집
        logger.info("\n[1단계] 브랜드별 상품 목록 수집")
        with BrandCrawler(headless=headless) as crawler:
            brand_products = crawler.get_brand_products_multi(
                brand_names,
                max_products_per_brand or Config.MAX_PRODUCTS_PER_BRAND
            )

        # 수집된 상품 ID 요약
        total_products = sum(len(ids) for ids in brand_products.values())
        logger.info(f"총 {total_products}개 상품 발견")
        for brand, ids in brand_products.items():
            logger.info(f"  - {brand}: {len(ids)}개")

        # 2단계: 상품 상세 정보 및 이미지 수집
        logger.info("\n[2단계] 상품 상세 정보 및 이미지 수집")
        with ProductScraper(headless=headless) as scraper:
            for brand, product_ids in brand_products.items():
                logger.info(f"\n브랜드: {brand}")

                for idx, product_id in enumerate(product_ids, 1):
                    logger.info(f"  [{idx}/{len(product_ids)}] 상품 ID: {product_id}")

                    product_data = scraper.scrape_product(
                        product_id,
                        download_images=download_images
                    )

                    if product_data:
                        product_data['target_brand'] = brand
                        self.results.append(product_data)

        logger.info(f"\n총 {len(self.results)}개 상품 정보 수집 완료")

    def run_recommend_pipeline(
        self,
        gender_filter: str = 'A',
        max_products: Optional[int] = None,
        download_images: bool = True,
        headless: bool = True
    ):
        """
        추천 페이지 데이터 수집 파이프라인 실행

        Args:
            gender_filter: 성별 필터 (A: 전체, M: 남성, W: 여성)
            max_products: 최대 상품 수
            download_images: 이미지 다운로드 여부
            headless: 헤드리스 모드 여부
        """
        logger.info("=" * 60)
        logger.info("무신사 추천 페이지 데이터 수집 파이프라인 시작")
        logger.info("=" * 60)

        # 1단계: 추천 상품 ID 수집
        logger.info("\n[1단계] 추천 상품 목록 수집")
        with BrandCrawler(headless=headless) as crawler:
            product_ids = crawler.get_recommend_products(
                gender_filter,
                max_products or Config.MAX_PRODUCTS_PER_BRAND
            )

        logger.info(f"총 {len(product_ids)}개 추천 상품 발견")

        # 2단계: 상품 상세 정보 및 이미지 수집
        logger.info("\n[2단계] 상품 상세 정보 및 이미지 수집")
        with ProductScraper(headless=headless) as scraper:
            products = scraper.scrape_products(
                product_ids,
                delay=Config.DELAY_BETWEEN_REQUESTS
            )
            self.results.extend(products)

        logger.info(f"\n총 {len(self.results)}개 상품 정보 수집 완료")

    def save_to_csv(self, filename: Optional[str] = None) -> Path:
        """
        수집된 데이터를 CSV로 저장

        Args:
            filename: 파일명 (기본: musinsa_products_YYYYMMDD_HHMMSS.csv)

        Returns:
            저장된 파일 경로
        """
        if not self.results:
            logger.warning("저장할 데이터가 없습니다.")
            return None

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"musinsa_products_{timestamp}.csv"

        output_path = Config.CSV_OUTPUT_PATH / filename

        # DataFrame 생성
        df = pd.DataFrame(self.results)

        # CSV 저장
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        logger.info(f"CSV 저장 완료: {output_path}")

        return output_path

    def save_to_json(self, filename: Optional[str] = None) -> Path:
        """
        수집된 데이터를 JSON으로 저장

        Args:
            filename: 파일명 (기본: musinsa_products_YYYYMMDD_HHMMSS.json)

        Returns:
            저장된 파일 경로
        """
        if not self.results:
            logger.warning("저장할 데이터가 없습니다.")
            return None

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"musinsa_products_{timestamp}.json"

        output_path = Config.CSV_OUTPUT_PATH / filename

        # JSON 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        logger.info(f"JSON 저장 완료: {output_path}")

        return output_path

    def get_summary(self) -> Dict:
        """수집 결과 요약"""
        if not self.results:
            return {"message": "수집된 데이터가 없습니다."}

        df = pd.DataFrame(self.results)

        summary = {
            "total_products": len(self.results),
            "products_with_images": len([r for r in self.results if r.get('downloaded_images')]),
            "total_images": sum(r.get('image_count', 0) for r in self.results),
        }

        if 'brand' in df.columns:
            summary['brands'] = df['brand'].value_counts().to_dict()

        if 'target_brand' in df.columns:
            summary['target_brands'] = df['target_brand'].value_counts().to_dict()

        return summary
