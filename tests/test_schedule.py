import unittest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Schedule, JobPosting
from datetime import datetime, timedelta

class TestScheduleManagement(unittest.TestCase):
    def setUp(self):
        """테스트 전에 실행될 설정"""
        # 테스트용 데이터베이스 설정
        self.engine = create_engine('sqlite:///test.db')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()
        
        # 테스트 채용공고 생성
        self.job = JobPosting(
            company_name="테스트 회사",
            job_title="테스트 직무",
            description="테스트 설명",
            deadline="2024-12-31",
            link="http://test.com"
        )
        self.db.add(self.job)
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
            pass

    def test_schedule_creation(self):
        """일정 생성 테스트"""
        print("\n=== 일정 생성 테스트 ===")
        
        # 일정 생성
        start_date = datetime.now()
        end_date = start_date + timedelta(hours=1)
        
        schedule = Schedule(
            job_posting_id=self.job.id,
            title="테스트 일정",
            event_type="면접",
            start_date=start_date,
            end_date=end_date,
            location="테스트 장소",
            description="테스트 설명"
        )
        self.db.add(schedule)
        self.db.commit()
        
        # 일정이 생성되었는지 확인
        created_schedule = self.db.query(Schedule).filter_by(id=schedule.id).first()
        self.assertIsNotNone(created_schedule)
        self.assertEqual(created_schedule.title, "테스트 일정")
        self.assertEqual(created_schedule.event_type, "면접")
        print("✓ 일정 생성 확인")

    def test_schedule_update(self):
        """일정 수정 테스트"""
        print("\n=== 일정 수정 테스트 ===")
        
        # 일정 생성
        start_date = datetime.now()
        end_date = start_date + timedelta(hours=1)
        
        schedule = Schedule(
            job_posting_id=self.job.id,
            title="테스트 일정",
            event_type="면접",
            start_date=start_date,
            end_date=end_date,
            location="테스트 장소",
            description="테스트 설명"
        )
        self.db.add(schedule)
        self.db.commit()
        
        # 일정 수정
        new_title = "수정된 일정"
        new_location = "수정된 장소"
        schedule.title = new_title
        schedule.location = new_location
        self.db.commit()
        
        # 수정된 일정 확인
        updated_schedule = self.db.query(Schedule).filter_by(id=schedule.id).first()
        self.assertEqual(updated_schedule.title, new_title)
        self.assertEqual(updated_schedule.location, new_location)
        print("✓ 일정 수정 확인")

    def test_schedule_deletion(self):
        """일정 삭제 테스트"""
        print("\n=== 일정 삭제 테스트 ===")
        
        # 일정 생성
        start_date = datetime.now()
        end_date = start_date + timedelta(hours=1)
        
        schedule = Schedule(
            job_posting_id=self.job.id,
            title="테스트 일정",
            event_type="면접",
            start_date=start_date,
            end_date=end_date,
            location="테스트 장소",
            description="테스트 설명"
        )
        self.db.add(schedule)
        self.db.commit()
        
        # 일정 삭제
        self.db.delete(schedule)
        self.db.commit()
        
        # 일정이 삭제되었는지 확인
        deleted_schedule = self.db.query(Schedule).filter_by(id=schedule.id).first()
        self.assertIsNone(deleted_schedule)
        print("✓ 일정 삭제 확인")

    def test_schedule_cascade_delete(self):
        """채용공고 삭제 시 일정도 함께 삭제되는지 테스트"""
        print("\n=== 채용공고 삭제 시 일정도 함께 삭제되는지 테스트 ===")
        
        # 일정 생성
        start_date = datetime.now()
        end_date = start_date + timedelta(hours=1)
        
        schedule = Schedule(
            job_posting_id=self.job.id,
            title="테스트 일정",
            event_type="면접",
            start_date=start_date,
            end_date=end_date,
            location="테스트 장소",
            description="테스트 설명"
        )
        self.db.add(schedule)
        self.db.commit()
        
        # 채용공고 삭제
        self.db.delete(self.job)
        self.db.commit()
        
        # 일정이 삭제되었는지 확인
        deleted_schedule = self.db.query(Schedule).filter_by(id=schedule.id).first()
        self.assertIsNone(deleted_schedule)
        print("✓ 채용공고 삭제 시 일정도 함께 삭제 확인")

if __name__ == '__main__':
    unittest.main(verbosity=2) 