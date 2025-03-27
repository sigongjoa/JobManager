# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from models import Base
from typing import List, Optional, Dict
from datetime import datetime
import json
import os

SQLALCHEMY_DATABASE_URL = "sqlite:///./job_manager.db"

# SQLite를 사용할 경우, connect_args 설정 필요
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 세션 생성용 객체
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 데이터베이스 초기화 함수
def init_db():
    # 여기서 models를 import하여 테이블 생성
    from models import Resume, JobPosting, Application, Feedback, Portfolio
    Base.metadata.create_all(bind=engine)

# 데이터베이스 세션 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Database:
    def __init__(self):
        self.data_dir = "data"
        self.jobs_file = os.path.join(self.data_dir, "jobs.json")
        self.resumes_file = os.path.join(self.data_dir, "resumes.json")
        self.applications_file = os.path.join(self.data_dir, "applications.json")
        self.portfolio_file = os.path.join(self.data_dir, "portfolio.json")
        self._ensure_data_files()

    def _ensure_data_files(self):
        """데이터 디렉토리와 파일들이 존재하는지 확인하고 없으면 생성"""
        os.makedirs(self.data_dir, exist_ok=True)
        for file_path in [self.jobs_file, self.resumes_file, self.applications_file, self.portfolio_file]:
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False)

    def _load_data(self, file_path: str) -> List[Dict]:
        """JSON 파일에서 데이터 로드"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    def _save_data(self, file_path: str, data: List[Dict]):
        """데이터를 JSON 파일로 저장"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # 채용 공고 관련 메서드
    def save_job_posting(self, job_data: Dict):
        jobs = self._load_data(self.jobs_file)
        job_data['id'] = str(len(jobs) + 1)
        job_data['crawled_at'] = datetime.now().isoformat()
        jobs.append(job_data)
        self._save_data(self.jobs_file, jobs)
        return job_data

    def get_job_postings(self) -> List[Dict]:
        return self._load_data(self.jobs_file)

    def get_job_posting(self, job_id: str) -> Optional[Dict]:
        jobs = self._load_data(self.jobs_file)
        for job in jobs:
            if job.get('id') == job_id:
                return job
        return None

    # 이력서 관련 메서드
    def save_resume(self, resume_data: Dict):
        resumes = self._load_data(self.resumes_file)
        resume_data['id'] = str(len(resumes) + 1)
        resume_data['created_at'] = datetime.now().isoformat()
        resumes.append(resume_data)
        self._save_data(self.resumes_file, resumes)
        return resume_data

    def get_resumes(self) -> List[Dict]:
        return self._load_data(self.resumes_file)

    def get_resume(self, resume_id: str) -> Optional[Dict]:
        resumes = self._load_data(self.resumes_file)
        for resume in resumes:
            if resume.get('id') == resume_id:
                return resume
        return None

    # 지원 현황 관련 메서드
    def save_application(self, application_data: Dict):
        applications = self._load_data(self.applications_file)
        application_data['id'] = str(len(applications) + 1)
        if isinstance(application_data['applied_at'], datetime):
            application_data['applied_at'] = application_data['applied_at'].isoformat()
        applications.append(application_data)
        self._save_data(self.applications_file, applications)
        return application_data

    def get_applications(self) -> List[Dict]:
        return self._load_data(self.applications_file)

    def get_application(self, application_id: str) -> Optional[Dict]:
        applications = self._load_data(self.applications_file)
        for application in applications:
            if application.get('id') == application_id:
                return application
        return None

    # 포트폴리오 관련 메서드
    def save_portfolio(self, portfolio_data: Dict):
        portfolio = self._load_data(self.portfolio_file)
        portfolio_data['id'] = str(len(portfolio) + 1)
        portfolio_data['created_at'] = datetime.now().isoformat()
        portfolio.append(portfolio_data)
        self._save_data(self.portfolio_file, portfolio)
        return portfolio_data

    def get_portfolio(self) -> List[Dict]:
        return self._load_data(self.portfolio_file)
