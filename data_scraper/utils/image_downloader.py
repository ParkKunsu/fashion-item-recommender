"""
이미지 다운로드 모듈
"""
import requests
from pathlib import Path
from typing import List, Optional
from PIL import Image
from io import BytesIO
import hashlib
from .logger import setup_logger

logger = setup_logger(__name__)


class ImageDownloader:
    """이미지 다운로드 및 저장"""

    def __init__(self, download_path: Path):
        """
        Args:
            download_path: 이미지 저장 경로
        """
        self.download_path = Path(download_path)
        self.download_path.mkdir(parents=True, exist_ok=True)

    def download_image(
        self,
        url: str,
        product_id: str,
        image_index: int = 0,
        validate: bool = True
    ) -> Optional[Path]:
        """
        이미지 다운로드

        Args:
            url: 이미지 URL
            product_id: 상품 ID
            image_index: 이미지 인덱스
            validate: 이미지 검증 여부

        Returns:
            저장된 이미지 경로 또는 None
        """
        try:
            # 이미지 다운로드
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            # 이미지 검증
            if validate:
                img = Image.open(BytesIO(response.content))
                img.verify()

            # 파일명 생성
            file_ext = self._get_image_extension(url, response.headers.get('Content-Type', ''))
            filename = f"{product_id}_{image_index}{file_ext}"
            file_path = self.download_path / product_id / filename

            # 디렉토리 생성
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # 이미지 저장
            with open(file_path, 'wb') as f:
                f.write(response.content)

            logger.info(f"이미지 다운로드 완료: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"이미지 다운로드 실패 ({url}): {e}")
            return None

    def download_images(
        self,
        urls: List[str],
        product_id: str,
        max_images: Optional[int] = None
    ) -> List[Path]:
        """
        여러 이미지 다운로드

        Args:
            urls: 이미지 URL 리스트
            product_id: 상품 ID
            max_images: 최대 다운로드 이미지 수

        Returns:
            저장된 이미지 경로 리스트
        """
        downloaded_images = []
        urls_to_download = urls[:max_images] if max_images else urls

        for idx, url in enumerate(urls_to_download):
            image_path = self.download_image(url, product_id, idx)
            if image_path:
                downloaded_images.append(image_path)

        logger.info(f"상품 {product_id}: {len(downloaded_images)}/{len(urls_to_download)} 이미지 다운로드 완료")
        return downloaded_images

    @staticmethod
    def _get_image_extension(url: str, content_type: str) -> str:
        """이미지 확장자 추출"""
        # URL에서 확장자 추출 시도
        if '.' in url.split('/')[-1]:
            ext = '.' + url.split('.')[-1].split('?')[0]
            if ext.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                return ext

        # Content-Type에서 추출
        content_type_map = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp'
        }
        return content_type_map.get(content_type, '.jpg')

    @staticmethod
    def generate_image_hash(image_path: Path) -> str:
        """이미지 해시 생성 (중복 체크용)"""
        with open(image_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
