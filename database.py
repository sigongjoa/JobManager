# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from models import Base
from typing import List, Optional, Dict
from datetime import datetime
import json
import os
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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
        """데이터베이스 초기화"""
        self.data_dir = "data"
        self.jobs_file = os.path.join(self.data_dir, "jobs.json")
        self.resumes_file = os.path.join(self.data_dir, "resumes.json")
        self.applications_file = os.path.join(self.data_dir, "applications.json")
        self._ensure_data_files()
        logger.info("데이터베이스 초기화 완료")

    def _ensure_data_files(self):
        """데이터 디렉토리와 파일들이 존재하는지 확인하고 없으면 생성"""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            for file_path in [self.jobs_file, self.resumes_file, self.applications_file]:
                if not os.path.exists(file_path):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump([], f, ensure_ascii=False, indent=2)
            logger.info("데이터 파일 확인/생성 완료")
        except Exception as e:
            logger.error(f"데이터 파일 생성 중 오류: {e}")
            raise

    def _load_data(self, file_path: str) -> List[Dict]:
        """JSON 파일에서 데이터 로드"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"JSON 파일 디코딩 오류: {file_path}")
            return []
        except Exception as e:
            logger.error(f"데이터 로드 중 오류: {e}")
            return []

    def _save_data(self, file_path: str, data: List[Dict]):
        """데이터를 JSON 파일로 저장"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"데이터 저장 완료: {file_path}")
        except Exception as e:
            logger.error(f"데이터 저장 중 오류: {e}")
            raise

    def save_job_posting(self, job_data: Dict) -> Dict:
        """채용 공고 저장"""
        try:
            jobs = self._load_data(self.jobs_file)
            
            # ID 생성
            job_data['id'] = str(len(jobs) + 1)
            
            # 타임스탬프 추가
            job_data['created_at'] = datetime.now().isoformat()
            
            # 필수 필드 확인
            required_fields = ['title', 'company_name', 'url']
            for field in required_fields:
                if not job_data.get(field):
                    logger.warning(f"필수 필드 누락: {field}")
            
            jobs.append(job_data)
            self._save_data(self.jobs_file, jobs)
            logger.info(f"채용 공고 저장 완료: {job_data['id']}")
            return job_data
        except Exception as e:
            logger.error(f"채용 공고 저장 중 오류: {e}")
            raise

    def get_job_postings(self, skip: int = 0, limit: int = 10) -> List[Dict]:
        """채용 공고 목록 조회"""
        try:
            jobs = self._load_data(self.jobs_file)
            return jobs[skip:skip + limit]
        except Exception as e:
            logger.error(f"채용 공고 목록 조회 중 오류: {e}")
            return []

    def get_job_posting(self, job_id: str) -> Optional[Dict]:
        """특정 채용 공고 조회"""
        try:
            jobs = self._load_data(self.jobs_file)
            for job in jobs:
                if job.get('id') == job_id:
                    return job
            logger.warning(f"채용 공고를 찾을 수 없음: {job_id}")
            return None
        except Exception as e:
            logger.error(f"채용 공고 조회 중 오류: {e}")
            return None

    def update_job_posting(self, job_id: str, job_data: Dict) -> Optional[Dict]:
        """채용 공고 수정"""
        try:
            jobs = self._load_data(self.jobs_file)
            for i, job in enumerate(jobs):
                if job.get('id') == job_id:
                    job_data['id'] = job_id
                    job_data['updated_at'] = datetime.now().isoformat()
                    jobs[i] = job_data
                    self._save_data(self.jobs_file, jobs)
                    logger.info(f"채용 공고 업데이트 완료: {job_id}")
                    return job_data
            logger.warning(f"채용 공고를 찾을 수 없음: {job_id}")
            return None
        except Exception as e:
            logger.error(f"채용 공고 업데이트 중 오류: {e}")
            return None

    def delete_job_posting(self, job_id: str) -> bool:
        """채용 공고 삭제"""
        try:
            jobs = self._load_data(self.jobs_file)
            filtered_jobs = [job for job in jobs if job.get('id') != job_id]
            if len(filtered_jobs) < len(jobs):
                self._save_data(self.jobs_file, filtered_jobs)
                logger.info(f"채용 공고 삭제 완료: {job_id}")
                return True
            logger.warning(f"채용 공고를 찾을 수 없음: {job_id}")
            return False
        except Exception as e:
            logger.error(f"채용 공고 삭제 중 오류: {e}")
            return False

    def save_resume(self, resume_data: Dict) -> Dict:
        """이력서 저장"""
        try:
            resumes = self._load_data(self.resumes_file)
            
            # ID 생성
            resume_data['id'] = str(len(resumes) + 1)
            
            # 타임스탬프 추가
            resume_data['created_at'] = datetime.now().isoformat()
            
            # 필수 필드 확인
            required_fields = ['name', 'email', 'phone', 'education', 'experience', 'skills']
            for field in required_fields:
                if not resume_data.get(field):
                    logger.warning(f"필수 필드 누락: {field}")
            
            resumes.append(resume_data)
            self._save_data(self.resumes_file, resumes)
            logger.info(f"이력서 저장 완료: {resume_data['id']}")
            return resume_data
        except Exception as e:
            logger.error(f"이력서 저장 중 오류: {e}")
            raise

    def get_resumes(self, skip: int = 0, limit: int = 10) -> List[Dict]:
        """이력서 목록 조회"""
        try:
            resumes = self._load_data(self.resumes_file)
            return resumes[skip:skip + limit]
        except Exception as e:
            logger.error(f"이력서 목록 조회 중 오류: {e}")
            return []

    def get_resume(self, resume_id: str) -> Optional[Dict]:
        """특정 이력서 조회"""
        try:
            resumes = self._load_data(self.resumes_file)
            for resume in resumes:
                if resume.get('id') == resume_id:
                    return resume
            logger.warning(f"이력서를 찾을 수 없음: {resume_id}")
            return None
        except Exception as e:
            logger.error(f"이력서 조회 중 오류: {e}")
            return None

    def update_resume(self, resume_id: str, resume_data: Dict) -> Optional[Dict]:
        """이력서 수정"""
        try:
            resumes = self._load_data(self.resumes_file)
            for i, resume in enumerate(resumes):
                if resume.get('id') == resume_id:
                    resume_data['id'] = resume_id
                    resume_data['updated_at'] = datetime.now().isoformat()
                    resumes[i] = resume_data
                    self._save_data(self.resumes_file, resumes)
                    logger.info(f"이력서 업데이트 완료: {resume_id}")
                    return resume_data
            logger.warning(f"이력서를 찾을 수 없음: {resume_id}")
            return None
        except Exception as e:
            logger.error(f"이력서 업데이트 중 오류: {e}")
            return None

    def delete_resume(self, resume_id: str) -> bool:
        """이력서 삭제"""
        try:
            resumes = self._load_data(self.resumes_file)
            filtered_resumes = [resume for resume in resumes if resume.get('id') != resume_id]
            if len(filtered_resumes) < len(resumes):
                self._save_data(self.resumes_file, filtered_resumes)
                logger.info(f"이력서 삭제 완료: {resume_id}")
                return True
            logger.warning(f"이력서를 찾을 수 없음: {resume_id}")
            return False
        except Exception as e:
            logger.error(f"이력서 삭제 중 오류: {e}")
            return False

    def save_application(self, application_data: Dict) -> Dict:
        """지원 현황 저장"""
        try:
            applications = self._load_data(self.applications_file)
            
            # ID 생성
            application_data['id'] = str(len(applications) + 1)
            
            # 타임스탬프 추가
            if 'applied_at' not in application_data:
                application_data['applied_at'] = datetime.now().isoformat()
            
            # 채용 공고 정보 가져오기
            if 'job_id' in application_data:
                job = self.get_job_posting(application_data['job_id'])
                if job:
                    application_data['job_title'] = job.get('title', '')
                    application_data['company'] = job.get('company_name', '')
            
            applications.append(application_data)
            self._save_data(self.applications_file, applications)
            logger.info(f"지원 현황 저장 완료: {application_data['id']}")
            return application_data
        except Exception as e:
            logger.error(f"지원 현황 저장 중 오류: {e}")
            raise

    def get_applications(self, skip: int = 0, limit: int = 10) -> List[Dict]:
        """지원 현황 목록 조회"""
        try:
            applications = self._load_data(self.applications_file)
            return applications[skip:skip + limit]
        except Exception as e:
            logger.error(f"지원 현황 목록 조회 중 오류: {e}")
            return []

    def get_application(self, application_id: str) -> Optional[Dict]:
        """특정 지원 현황 조회"""
        try:
            applications = self._load_data(self.applications_file)
            for application in applications:
                if application.get('id') == application_id:
                    return application
            logger.warning(f"지원 현황을 찾을 수 없음: {application_id}")
            return None
        except Exception as e:
            logger.error(f"지원 현황 조회 중 오류: {e}")
            return None

    def update_application(self, application_id: str, update_data: Dict) -> Optional[Dict]:
        """지원 현황 수정"""
        try:
            applications = self._load_data(self.applications_file)
            for i, application in enumerate(applications):
                if application.get('id') == application_id:
                    applications[i].update(update_data)
                    applications[i]['updated_at'] = datetime.now().isoformat()
                    self._save_data(self.applications_file, applications)
                    logger.info(f"지원 현황 업데이트 완료: {application_id}")
                    return applications[i]
            logger.warning(f"지원 현황을 찾을 수 없음: {application_id}")
            return None
        except Exception as e:
            logger.error(f"지원 현황 업데이트 중 오류: {e}")
            return None

    def delete_application(self, application_id: str) -> bool:
        """지원 현황 삭제"""
        try:
            applications = self._load_data(self.applications_file)
            filtered_applications = [app for app in applications if app.get('id') != application_id]
            if len(filtered_applications) < len(applications):
                self._save_data(self.applications_file, filtered_applications)
                logger.info(f"지원 현황 삭제 완료: {application_id}")
                return True
            logger.warning(f"지원 현황을 찾을 수 없음: {application_id}")
            return False
        except Exception as e:
            logger.error(f"지원 현황 삭제 중 오류: {e}")
            return False

    def get_dashboard_stats(self) -> Dict:
        """대시보드 통계 정보 조회"""
        try:
            jobs = self._load_data(self.jobs_file)
            resumes = self._load_data(self.resumes_file)
            applications = self._load_data(self.applications_file)

            today = datetime.now().date()
            today_applications = [
                app for app in applications 
                if datetime.fromisoformat(app.get('applied_at', '')).date() == today
            ]

            stats = {
                'total_jobs': len(jobs),
                'total_resumes': len(resumes),
                'total_applications': len(applications),
                'today_applications': len(today_applications)
            }
            
            logger.info("대시보드 통계 조회 완료")
            return stats
        except Exception as e:
            logger.error(f"대시보드 통계 조회 중 오류: {e}")
            return {
                'total_jobs': 0,
                'total_resumes': 0,
                'total_applications': 0,
                'today_applications': 0
            }
