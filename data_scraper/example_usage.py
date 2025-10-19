"""
데이터 수집 파이프라인 사용 예제
"""
from pipeline import DataPipeline
from utils.config import Config


def example_brand_scraping():
    """브랜드별 데이터 수집 예제"""
    print("=" * 60)
    print("예제 1: 브랜드별 데이터 수집")
    print("=" * 60)

    # 파이프라인 초기화
    pipeline = DataPipeline()

    # 수집할 브랜드 목록
    brands = ["무신사 스탠다드", "커버낫", "디스이즈네버댓"]

    # 파이프라인 실행
    pipeline.run_brand_pipeline(
        brand_names=brands,
        max_products_per_brand=10,  # 브랜드당 최대 10개 상품
        download_images=True,
        headless=True  # 브라우저 창 숨기기
    )

    # 결과 저장
    csv_path = pipeline.save_to_csv()
    json_path = pipeline.save_to_json()

    # 요약 출력
    summary = pipeline.get_summary()
    print("\n수집 결과 요약:")
    print(f"  - 총 상품 수: {summary['total_products']}")
    print(f"  - 이미지 포함 상품: {summary['products_with_images']}")
    print(f"  - 총 이미지 수: {summary['total_images']}")

    print(f"\n저장 완료:")
    print(f"  - CSV: {csv_path}")
    print(f"  - JSON: {json_path}")


def example_recommend_scraping():
    """추천 페이지 데이터 수집 예제"""
    print("=" * 60)
    print("예제 2: 추천 페이지 데이터 수집")
    print("=" * 60)

    # 파이프라인 초기화
    pipeline = DataPipeline()

    # 파이프라인 실행
    pipeline.run_recommend_pipeline(
        gender_filter='A',  # A: 전체, M: 남성, W: 여성
        max_products=20,
        download_images=True,
        headless=True
    )

    # 결과 저장
    csv_path = pipeline.save_to_csv("recommend_products.csv")

    # 요약 출력
    summary = pipeline.get_summary()
    print("\n수집 결과 요약:")
    print(f"  - 총 상품 수: {summary['total_products']}")
    print(f"  - 이미지 포함 상품: {summary['products_with_images']}")
    print(f"  - 총 이미지 수: {summary['total_images']}")


def example_single_product():
    """단일 상품 수집 예제"""
    print("=" * 60)
    print("예제 3: 단일 상품 상세 정보 수집")
    print("=" * 60)

    from scrapers.product_scraper import ProductScraper

    # 상품 ID (URL에서 추출: https://www.musinsa.com/products/3782941)
    product_id = "3782941"

    with ProductScraper(headless=False) as scraper:  # headless=False로 브라우저 확인 가능
        product_data = scraper.scrape_product(product_id, download_images=True)

        if product_data:
            print("\n상품 정보:")
            print(f"  - 상품명: {product_data.get('product_name', 'N/A')}")
            print(f"  - 브랜드: {product_data.get('brand', 'N/A')}")
            print(f"  - 가격: {product_data.get('price', 'N/A')}")
            print(f"  - 이미지 수: {product_data.get('image_count', 0)}")
            print(f"  - 다운로드된 이미지: {len(product_data.get('downloaded_images', []))}")


def example_with_env_config():
    """환경 변수 설정 사용 예제"""
    print("=" * 60)
    print("예제 4: .env 파일 설정 사용")
    print("=" * 60)

    # .env 파일에서 브랜드 목록 로드
    brands = Config.TARGET_BRANDS

    if not brands:
        print("경고: .env 파일에 TARGET_BRANDS가 설정되지 않았습니다.")
        brands = ["무신사 스탠다드"]  # 기본값

    # 파이프라인 실행
    pipeline = MusinsaDataPipeline()
    pipeline.run_brand_pipeline(
        brand_names=brands,
        max_products_per_brand=Config.MAX_PRODUCTS_PER_BRAND,
        download_images=True,
        headless=Config.HEADLESS
    )

    # 결과 저장
    pipeline.save_to_csv()
    pipeline.save_to_json()


if __name__ == "__main__":
    # 실행할 예제 선택 (1, 2, 3, 4)
    example_choice = 3

    if example_choice == 1:
        example_brand_scraping()
    elif example_choice == 2:
        example_recommend_scraping()
    elif example_choice == 3:
        example_single_product()
    elif example_choice == 4:
        example_with_env_config()
    else:
        print("올바른 예제 번호를 선택하세요 (1-4)")
