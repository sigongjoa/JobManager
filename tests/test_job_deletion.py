import unittest
import os
import sys
import shutil
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, JobPosting, Resume, Schedule
from datetime import datetime, timedelta

# 프로젝트 루트 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

class TestJobDeletion(unittest.TestCase):
    def setUp(self):
        """테스트 전에 실행될 설정"""
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
            start_date=datetime(2024, 3, 27),
            end_date=datetime(2024, 3, 28),
            location="테스트 장소",
            description="테스트 설명"
        )
        self.db.add(self.schedule)
        self.db.commit()

    def tearDown(self):
        """테스트 후에 실행될 정리 작업"""
        # 테스트 데이터베이스 정리
        self.db.close()
        self.engine.dispose()
        
        try:
            if os.path.exists("test.db"):
                os.remove("test.db")
        except OSError:
            pass  # 파일 삭제 실패 시 무시
        
        # 테스트 업로드 디렉토리 정리
        try:
            if os.path.exists(self.test_upload_dir):
                shutil.rmtree(self.test_upload_dir)
        except OSError:
            pass  # 디렉토리 삭제 실패 시 무시

    def test_job_deletion(self):
        """채용공고 삭제 테스트"""
        print("\n=== 채용공고 삭제 테스트 ===")
        
        # 채용공고 삭제
        self.db.delete(self.job)
        self.db.commit()
        
        # 채용공고가 삭제되었는지 확인
        deleted_job = self.db.query(JobPosting).filter_by(id=self.job.id).first()
        self.assertIsNone(deleted_job)
        print("✓ 채용공고 삭제 확인")
        
        # 관련 이력서가 삭제되었는지 확인
        deleted_resume = self.db.query(Resume).filter_by(id=self.resume.id).first()
        self.assertIsNone(deleted_resume)
        print("✓ 관련 이력서 삭제 확인")
        
        # 이력서 파일이 삭제되었는지 확인
        self.assertFalse(os.path.exists(self.resume.file_path))
        print("✓ 이력서 파일 삭제 확인")
        
        # 관련 일정이 삭제되었는지 확인
        deleted_schedule = self.db.query(Schedule).filter_by(id=self.schedule.id).first()
        self.assertIsNone(deleted_schedule)
        print("✓ 관련 일정 삭제 확인")

if __name__ == '__main__':
    unittest.main(verbosity=2) 