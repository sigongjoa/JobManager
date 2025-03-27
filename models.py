from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Boolean, event, JSON, create_engine
)
from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import os
from sqlalchemy.sql import func

Base = declarative_base()

# ----------------------
# 1) Resume (자소서)
# ----------------------
class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    file_path = Column(String, nullable=False)  # 파일 경로는 필수
    status = Column(String, default="검토중")  # 검토중, 열람중, 합격, 불합격
    created_at = Column(DateTime, default=datetime.now)
    job_posting_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)  # 채용공고는 필수

    # 관계 설정
    job_posting = relationship("JobPosting", back_populates="resumes")

    # 관계
    applications = relationship("Application", back_populates="resume")
    feedbacks = relationship("Feedback", back_populates="resume")
    questions = relationship("ResumeQuestion", back_populates="resume", cascade="all, delete-orphan")

# 이력서 삭제 시 파일도 함께 삭제하는 이벤트 리스너
@event.listens_for(Resume, 'after_delete')
def delete_resume_file(mapper, connection, target):
    if target.file_path and os.path.exists(target.file_path):
        try:
            os.remove(target.file_path)
        except OSError:
            # 파일 삭제 실패 시 무시
            pass

# ----------------------
# 2) JobPosting (채용공고)
# ----------------------
class JobPosting(Base):
    __tablename__ = "job_postings"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, default="saramin")  # 플랫폼 구분
    company_name = Column(String)
    job_title = Column(String)
    description = Column(Text)
    deadline = Column(String)
    link = Column(String, unique=True)
    experience = Column(String)  # 경력
    education = Column(String)   # 학력
    employment_type = Column(String)  # 고용형태
    location = Column(String)    # 근무지역
    salary = Column(String)      # 급여
    welfare_benefits = Column(Text)  # 복리후생
    applied = Column(Boolean, default=False)
    application_status = Column(String, default="미지원")
    application_date = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    
    # 관계 설정
    resumes = relationship("Resume", back_populates="job_posting")
    schedules = relationship("Schedule", back_populates="job_posting")
    applications = relationship("Application", back_populates="job")

# ----------------------
# 3) Application (지원)
# ----------------------
class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_postings.id"))
    resume_id = Column(Integer, ForeignKey("resumes.id"))
    status = Column(String)  # 예: "지원중", "서류합격", "불합격" 등

    # 관계
    job = relationship("JobPosting", back_populates="applications")
    resume = relationship("Resume", back_populates="applications")

# ----------------------
# 4) Feedback (피드백)
# ----------------------
class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"))
    job_id = Column(Integer, ForeignKey("job_postings.id"), nullable=True)
    feedback_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 관계
    resume = relationship("Resume", back_populates="feedbacks")

# ----------------------
# 5) Portfolio (포트폴리오)
# ----------------------
class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

    # 관계 설정
    links = relationship("PortfolioLink", back_populates="portfolio", cascade="all, delete-orphan")

# ----------------------
# 6) PortfolioLink (포트폴리오 링크)
# ----------------------
class PortfolioLink(Base):
    __tablename__ = "portfolio_links"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"))
    title = Column(String, nullable=False)  # 예: "GitHub", "데모", "문서" 등
    url = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    # 관계 설정
    portfolio = relationship("Portfolio", back_populates="links")

# ----------------------
# 7) Schedule (일정)
# ----------------------
class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)  # 일정 제목
    description = Column(Text, nullable=True)  # 일정 설명
    start_date = Column(DateTime, nullable=False)  # 시작일시
    end_date = Column(DateTime, nullable=True)  # 종료일시
    event_type = Column(String, nullable=False)  # 일정 유형 (서류마감, 면접, 입사예정 등)
    location = Column(String, nullable=True)  # 장소 (면접 장소 등)
    created_at = Column(DateTime, default=datetime.now)

    # 관계 설정
    job_posting_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    job_posting = relationship("JobPosting", back_populates="schedules")

# ----------------------
# 8) ResumeQuestion (자소서 질문)
# ----------------------
class ResumeQuestion(Base):
    __tablename__ = "resume_questions"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"))
    question = Column(String)
    answer = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    resume = relationship("Resume", back_populates="questions")

# 데이터베이스 연결 설정
SQLALCHEMY_DATABASE_URL = "sqlite:///./jobs.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
