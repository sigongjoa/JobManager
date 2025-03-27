import unittest
import os
import sys
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, JobPosting, Resume, Schedule
import shutil

# 프로젝트 루트 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from crawlers.saramin_crawler import SaraminCrawler
from crawlers.jobplanet_crawler import JobPlanetCrawler
from crawlers.incruit_crawler import IncruitCrawler
from crawlers.integrated_crawler import IntegratedCrawler

class TestCrawlers(unittest.TestCase):
    def setUp(self):
        """테스트 전에 실행될 설정"""
        self.test_urls = {
            'saramin': 'https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=47878954',  # 실제 채용공고 URL
            'jobplanet': 'https://www.jobplanet.co.kr/job/search/job/11111',  # 실제 채용공고 URL
            'incruit': 'https://www.incruit.com/jobdb/view.asp?test=11111'  # 실제 채용공고 URL
        }
        self.max_jobs = 1  # 각 크롤러당 1개의 공고만 크롤링

    def tearDown(self):
        """테스트 후에 실행될 정리 작업"""
        # 통합 크롤러의 cleanup 메서드 호출
        crawler = IntegratedCrawler()
        crawler.cleanup()
        
        # 추가로 남아있을 수 있는 파일들 정리
        for site in ['Saramin', 'JobPlanet', 'Incruit']:
            filename = f"{site}_jobs.csv"
            max_retries = 3
            retry_delay = 2  # 초
            
            for attempt in range(max_retries):
                try:
                    if os.path.exists(filename):
                        # 파일이 사용 중인지 확인
                        try:
                            with open(filename, 'a'):
                                pass
                            os.remove(filename)
                            print(f"추가 파일 삭제됨: {filename}")
                            break
                        except IOError:
                            print(f"파일이 사용 중입니다. 재시도 중... ({attempt + 1}/{max_retries})")
                            import time
                            time.sleep(retry_delay)
                    else:
                        print(f"파일이 존재하지 않음: {filename}")
                        break
                except Exception as e:
                    print(f"추가 파일 삭제 중 오류 발생: {filename}, 오류: {e}")
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(retry_delay)
                    else:
                        print(f"최대 재시도 횟수 초과: {filename}")

    def test_saramin_crawler(self):
        """사람인 크롤러 테스트"""
        print("\n=== 사람인 크롤러 테스트 ===")
        crawler = SaraminCrawler()
        result = crawler.crawl(self.test_urls['saramin'], self.max_jobs)
        
        # 결과 검증
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        self.assertLessEqual(len(result), self.max_jobs)
        
        if result:
            print("\n크롤링 성공!")
            print("\n첫 번째 채용 공고 정보:")
            first_job = result[0]
            for key, value in first_job.items():
                if key == 'description':
                    print(f"{key}: {value[:100]}...")  # 설명은 처음 100자만 출력
                else:
                    print(f"{key}: {value}")
        else:
            print("\n크롤링 실패: 결과가 없습니다.")

    def test_jobplanet_crawler(self):
        """잡플래닛 크롤러 테스트"""
        print("\n=== 잡플래닛 크롤러 테스트 ===")
        crawler = JobPlanetCrawler()
        result = crawler.crawl(self.test_urls['jobplanet'], self.max_jobs)
        
        # 결과 검증
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        self.assertLessEqual(len(result), self.max_jobs)
        
        if result:
            print("\n크롤링 성공!")
            print("\n첫 번째 채용 공고 정보:")
            first_job = result[0]
            for key, value in first_job.items():
                if key == 'description':
                    print(f"{key}: {value[:100]}...")  # 설명은 처음 100자만 출력
                else:
                    print(f"{key}: {value}")
        else:
            print("\n크롤링 실패: 결과가 없습니다.")

    def test_incruit_crawler(self):
        """인크루트 크롤러 테스트"""
        print("\n=== 인크루트 크롤러 테스트 ===")
        crawler = IncruitCrawler()
        result = crawler.crawl(self.test_urls['incruit'], self.max_jobs)
        
        # 결과 검증
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        self.assertLessEqual(len(result), self.max_jobs)
        
        if result:
            print("\n크롤링 성공!")
            print("\n첫 번째 채용 공고 정보:")
            first_job = result[0]
            for key, value in first_job.items():
                if key == 'description':
                    print(f"{key}: {value[:100]}...")  # 설명은 처음 100자만 출력
                else:
                    print(f"{key}: {value}")
        else:
            print("\n크롤링 실패: 결과가 없습니다.")

    def test_integrated_crawler(self):
        """통합 크롤러 테스트"""
        print("\n=== 통합 크롤러 테스트 ===")
        crawler = IntegratedCrawler()
        results = crawler.crawl_multiple(list(self.test_urls.values()), self.max_jobs)
        
        # 결과 검증
        self.assertIsNotNone(results)
        self.assertIsInstance(results, dict)
        
        # 각 사이트별 결과 출력
        for site, result in results.items():
            print(f"\n{site} 크롤링 결과:")
            if result:
                print("크롤링 성공!")
                print("\n첫 번째 채용 공고 정보:")
                first_job = result[0]
                for key, value in first_job.items():
                    if key == 'description':
                        print(f"{key}: {value[:100]}...")  # 설명은 처음 100자만 출력
                    else:
                        print(f"{key}: {value}")
            else:
                print("크롤링 실패: 결과가 없습니다.")

class TestJobDeletion(unittest.TestCase):
    def setUp(self):
        # 테스트용 데이터베이스 설정
        self.engine = create_engine('sqlite:///test.db')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()
        
        # 테스트용 업로드 디렉토리 생성
        self.test_upload_dir = "test_uploads"
        os.makedirs(self.test_upload_dir, exist_ok=True)
        
        # 테스트 데이터 생성
        self.job = JobPosting(
            company_name="테스트 회사",
            job_title="테스트 직무",
            description="테스트 설명",
            deadline="2024-12-31",
            link="http://test.com"
        )
        self.db.add(self.job)
        self.db.commit()
        
        # 테스트 이력서 생성
        self.resume = Resume(
            title="테스트 이력서",
            file_path=os.path.join(self.test_upload_dir, "test_resume.txt"),
            status="검토중",
            job_posting_id=self.job.id
        )
        self.db.add(self.resume)
        self.db.commit()
        
        # 테스트 파일 생성
        with open(self.resume.file_path, "w") as f:
            f.write("테스트 이력서 내용")
        
        # 테스트 일정 생성
        self.schedule = Schedule(
            job_posting_id=self.job.id,
            title="테스트 일정",
            event_type="면접",
            start_date="2024-03-27",
            end_date="2024-03-28",
            location="테스트 장소",
            description="테스트 설명"
        )
        self.db.add(self.schedule)
        self.db.commit()

    def tearDown(self):
        # 테스트 데이터베이스 정리
        self.db.close()
        if os.path.exists("test.db"):
            os.remove("test.db")
        
        # 테스트 업로드 디렉토리 정리
        if os.path.exists(self.test_upload_dir):
            shutil.rmtree(self.test_upload_dir)

    def test_job_deletion(self):
        """채용공고 삭제 테스트"""
        # 채용공고 삭제
        self.db.delete(self.job)
        self.db.commit()
        
        # 채용공고가 삭제되었는지 확인
        deleted_job = self.db.query(JobPosting).filter_by(id=self.job.id).first()
        self.assertIsNone(deleted_job)
        
        # 관련 이력서가 삭제되었는지 확인
        deleted_resume = self.db.query(Resume).filter_by(id=self.resume.id).first()
        self.assertIsNone(deleted_resume)
        
        # 이력서 파일이 삭제되었는지 확인
        self.assertFalse(os.path.exists(self.resume.file_path))
        
        # 관련 일정이 삭제되었는지 확인
        deleted_schedule = self.db.query(Schedule).filter_by(id=self.schedule.id).first()
        self.assertIsNone(deleted_schedule)

if __name__ == '__main__':
    unittest.main(verbosity=2) 