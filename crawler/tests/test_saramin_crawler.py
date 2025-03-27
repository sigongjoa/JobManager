import unittest
import os
import sys
import logging
from pathlib import Path

# 크롤러 모듈 import를 위한 경로 설정
sys.path.append(str(Path(__file__).parent.parent.parent))
from crawler.final_saramin_crawler import FinalSaraminCrawler

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestSaraminCrawler(unittest.TestCase):
    def setUp(self):
        """테스트 전 실행되는 설정"""
        self.crawler = FinalSaraminCrawler()
        self.test_url = "https://www.saramin.co.kr/zf_user/jobs/relay/view?isMypage=no&rec_idx=50313449&recommend_ids=eJxVjbkRw0AMA6txToB%2FrELUfxe%2BkT13VMYdEFgXeNB4F%2FDJy4XqFn638IcpAd%2Bp0gK1EY4UO13pVu4uBNQ4XQ2E%2FFPrai7xmSoDhwjhA8mYIpXFPZ65ziFK8YF07YNEv6Y0vfKkRfZYFm170i%2Ff%2FT98&view_type=list&gz=1&t_ref_content=major_company&t_ref=main&t_category=relay_view&relayNonce=4f88cd57bdd7a1009eb8&immediately_apply_layer_open=n#seq=0"

    def test_crawl_job_detail(self):
        """채용공고 상세 정보 크롤링 테스트"""
        logger.info("채용공고 상세 정보 크롤링 테스트 시작")
        
        # 크롤링 실행
        job_data = self.crawler.crawl_job_detail(self.test_url)
        
        # 결과 검증
        self.assertIsNotNone(job_data, "크롤링 결과가 None입니다.")
        self.assertIsInstance(job_data, dict, "크롤링 결과가 딕셔너리 형태가 아닙니다.")
        
        # 필수 필드 존재 여부 확인
        required_fields = ['company_name', 'job_title', 'application_deadline', 'url']
        for field in required_fields:
            self.assertIn(field, job_data, f"필수 필드 {field}가 없습니다.")
        
        # 데이터 출력
        logger.info("\n크롤링 결과:")
        logger.info(f"회사명: {job_data.get('company_name', '정보 없음')}")
        logger.info(f"공고 제목: {job_data.get('job_title', '정보 없음')}")
        logger.info(f"마감일: {job_data.get('application_deadline', '정보 없음')}")
        logger.info(f"URL: {job_data.get('url', '정보 없음')}")
        logger.info(f"근무지: {job_data.get('location', '정보 없음')}")
        logger.info(f"경력: {job_data.get('experience', '정보 없음')}")
        logger.info(f"학력: {job_data.get('education', '정보 없음')}")
        logger.info(f"고용형태: {job_data.get('employment_type', '정보 없음')}")
        logger.info(f"급여: {job_data.get('salary', '정보 없음')}")
        logger.info(f"복리후생: {job_data.get('welfare_benefits', '정보 없음')[:100]}...")

    def test_save_to_csv(self):
        """CSV 저장 테스트"""
        logger.info("CSV 저장 테스트 시작")
        
        # 크롤링 실행
        job_data = self.crawler.crawl_job_detail(self.test_url)
        
        # CSV 저장
        test_filename = "test_saramin_jobs.csv"
        self.crawler.save_to_csv(test_filename)
        
        # 파일 존재 여부 확인
        file_path = os.path.join(self.crawler.DATA_DIR, test_filename)
        self.assertTrue(os.path.exists(file_path), "CSV 파일이 생성되지 않았습니다.")

    def test_save_to_json(self):
        """JSON 저장 테스트"""
        logger.info("JSON 저장 테스트 시작")
        
        # 크롤링 실행
        job_data = self.crawler.crawl_job_detail(self.test_url)
        
        # JSON 저장
        test_filename = "test_saramin_jobs.json"
        self.crawler.save_to_json(test_filename)
        
        # 파일 존재 여부 확인
        file_path = os.path.join(self.crawler.DATA_DIR, test_filename)
        self.assertTrue(os.path.exists(file_path), "JSON 파일이 생성되지 않았습니다.")

if __name__ == '__main__':
    unittest.main() 