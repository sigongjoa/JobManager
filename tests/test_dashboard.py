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

class TestDashboard(unittest.TestCase):
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

    def tearDown(self):
        """테스트 후에 실행될 정리 작업"""
        # 테스트 데이터베이스 정리
        self.db.close()
        self.engine.dispose()
        
        try:
            if os.path.exists("test.db"):
                os.remove("test.db")
        except OSError:
            pass
        
        # 테스트 업로드 디렉토리 정리
        try:
            if os.path.exists(self.test_upload_dir):
                shutil.rmtree(self.test_upload_dir)
        except OSError:
            pass

    def test_job_statistics(self):
        """채용공고 통계 테스트"""
        print("\n=== 채용공고 통계 테스트 ===")
        
        # 채용공고 생성
        jobs = [
            JobPosting(
                company_name="회사1",
                job_title="직무1",
                description="설명1",
                deadline="2024-12-31",
                link="http://test1.com",
                application_status="서류검토중"
            ),
            JobPosting(
                company_name="회사2",
                job_title="직무2",
                description="설명2",
                deadline="2024-12-31",
                link="http://test2.com",
                application_status="서류합격"
            ),
            JobPosting(
                company_name="회사3",
                job_title="직무3",
                description="설명3",
                deadline="2024-12-31",
                link="http://test3.com",
                application_status="최종합격"
            )
        ]
        for job in jobs:
            self.db.add(job)
        self.db.commit()
        
        # 채용공고 수 확인
        total_jobs = self.db.query(JobPosting).count()
        self.assertEqual(total_jobs, 3)
        print("✓ 총 채용공고 수 확인")
        
        # 상태별 채용공고 수 확인
        reviewing = self.db.query(JobPosting).filter_by(application_status="서류검토중").count()
        passed = self.db.query(JobPosting).filter_by(application_status="서류합격").count()
        final = self.db.query(JobPosting).filter_by(application_status="최종합격").count()
        
        self.assertEqual(reviewing, 1)
        self.assertEqual(passed, 1)
        self.assertEqual(final, 1)
        print("✓ 상태별 채용공고 수 확인")

    def test_upcoming_schedules(self):
        """예정된 일정 테스트"""
        print("\n=== 예정된 일정 테스트 ===")
        
        # 채용공고 생성
        job = JobPosting(
            company_name="테스트 회사",
            job_title="테스트 직무",
            description="테스트 설명",
            deadline="2024-12-31",
            link="http://test.com"
        )
        self.db.add(job)
        self.db.commit()
        
        # 일정 생성
        now = datetime.now()
        schedules = [
            Schedule(
                job_posting_id=job.id,
                title="지난 일정",
                event_type="면접",
                start_date=now - timedelta(days=1),
                end_date=now - timedelta(days=1) + timedelta(hours=1)
            ),
            Schedule(
                job_posting_id=job.id,
                title="오늘 일정",
                event_type="면접",
                start_date=now,
                end_date=now + timedelta(hours=1)
            ),
            Schedule(
                job_posting_id=job.id,
                title="다가오는 일정",
                event_type="면접",
                start_date=now + timedelta(days=1),
                end_date=now + timedelta(days=1) + timedelta(hours=1)
            )
        ]
        for schedule in schedules:
            self.db.add(schedule)
        self.db.commit()
        
        # 예정된 일정 확인
        upcoming = self.db.query(Schedule).filter(Schedule.start_date >= now).all()
        self.assertEqual(len(upcoming), 2)
        print("✓ 예정된 일정 수 확인")

    def test_resume_statistics(self):
        """자소서 통계 테스트"""
        print("\n=== 자소서 통계 테스트 ===")
        
        # 채용공고 생성
        job = JobPosting(
            company_name="테스트 회사",
            job_title="테스트 직무",
            description="테스트 설명",
            deadline="2024-12-31",
            link="http://test.com"
        )
        self.db.add(job)
        self.db.commit()
        
        # 자소서 생성
        resumes = [
            Resume(
                title="자소서1",
                file_path=os.path.join(self.test_upload_dir, "resume1.txt"),
                status="검토중",
                job_posting_id=job.id
            ),
            Resume(
                title="자소서2",
                file_path=os.path.join(self.test_upload_dir, "resume2.txt"),
                status="합격",
                job_posting_id=job.id
            ),
            Resume(
                title="자소서3",
                file_path=os.path.join(self.test_upload_dir, "resume3.txt"),
                status="불합격",
                job_posting_id=job.id
            )
        ]
        for resume in resumes:
            self.db.add(resume)
        self.db.commit()
        
        # 상태별 자소서 수 확인
        reviewing = self.db.query(Resume).filter_by(status="검토중").count()
        passed = self.db.query(Resume).filter_by(status="합격").count()
        failed = self.db.query(Resume).filter_by(status="불합격").count()
        
        self.assertEqual(reviewing, 1)
        self.assertEqual(passed, 1)
        self.assertEqual(failed, 1)
        print("✓ 상태별 자소서 수 확인")

if __name__ == '__main__':
    unittest.main(verbosity=2) 