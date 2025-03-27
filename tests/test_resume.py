import unittest
import os
import sys
import shutil
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, JobPosting, Resume, Schedule, ResumeQuestion
from datetime import datetime, timedelta

# 프로젝트 루트 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

class TestResumeManagement(unittest.TestCase):
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
        
        # 테스트 업로드 디렉토리 정리
        try:
            if os.path.exists(self.test_upload_dir):
                shutil.rmtree(self.test_upload_dir)
        except OSError:
            pass

    def test_resume_creation(self):
        """자소서 생성 테스트"""
        print("\n=== 자소서 생성 테스트 ===")
        
        # 자소서 파일 생성
        file_path = os.path.join(self.test_upload_dir, "test_resume.txt")
        with open(file_path, "w") as f:
            f.write("테스트 자소서 내용")
        
        # 자소서 생성
        resume = Resume(
            title="테스트 자소서",
            file_path=file_path,
            status="검토중",
            job_posting_id=self.job.id
        )
        self.db.add(resume)
        self.db.commit()
        
        # 자소서가 생성되었는지 확인
        created_resume = self.db.query(Resume).filter_by(id=resume.id).first()
        self.assertIsNotNone(created_resume)
        self.assertEqual(created_resume.title, "테스트 자소서")
        print("✓ 자소서 생성 확인")
        
        # 자소서 파일이 생성되었는지 확인
        self.assertTrue(os.path.exists(created_resume.file_path))
        print("✓ 자소서 파일 생성 확인")

    def test_resume_questions(self):
        """자소서 질문 관리 테스트"""
        print("\n=== 자소서 질문 관리 테스트 ===")
        
        # 자소서 생성
        resume = Resume(
            title="테스트 자소서",
            file_path=os.path.join(self.test_upload_dir, "test_resume.txt"),
            status="검토중",
            job_posting_id=self.job.id
        )
        self.db.add(resume)
        self.db.commit()
        
        # 자소서 질문 추가
        questions = [
            ResumeQuestion(
                resume_id=resume.id,
                question="자기소개를 해주세요.",
                answer="안녕하세요, 저는..."
            ),
            ResumeQuestion(
                resume_id=resume.id,
                question="지원 동기를 말씀해주세요.",
                answer="해당 직무에 관심이 있어서..."
            )
        ]
        for question in questions:
            self.db.add(question)
        self.db.commit()
        
        # 질문이 추가되었는지 확인
        added_questions = self.db.query(ResumeQuestion).filter_by(resume_id=resume.id).all()
        self.assertEqual(len(added_questions), 2)
        print("✓ 자소서 질문 추가 확인")
        
        # 자소서 삭제 시 질문도 함께 삭제되는지 확인
        self.db.delete(resume)
        self.db.commit()
        
        deleted_questions = self.db.query(ResumeQuestion).filter_by(resume_id=resume.id).all()
        self.assertEqual(len(deleted_questions), 0)
        print("✓ 자소서 삭제 시 질문도 함께 삭제 확인")

    def test_resume_status_update(self):
        """자소서 상태 업데이트 테스트"""
        print("\n=== 자소서 상태 업데이트 테스트 ===")
        
        # 자소서 생성
        resume = Resume(
            title="테스트 자소서",
            file_path=os.path.join(self.test_upload_dir, "test_resume.txt"),
            status="검토중",
            job_posting_id=self.job.id
        )
        self.db.add(resume)
        self.db.commit()
        
        # 상태 업데이트
        resume.status = "합격"
        self.db.commit()
        
        # 상태가 업데이트되었는지 확인
        updated_resume = self.db.query(Resume).filter_by(id=resume.id).first()
        self.assertEqual(updated_resume.status, "합격")
        print("✓ 자소서 상태 업데이트 확인")

if __name__ == '__main__':
    unittest.main(verbosity=2) 