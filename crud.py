from sqlalchemy.orm import Session
from models import JobPosting, Resume, Application, Feedback, Portfolio, PortfolioLink, Schedule, ResumeQuestion
import datetime

# 채용 공고 관련 CRUD 함수
def get_jobs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(JobPosting).offset(skip).limit(limit).all()

def get_job(db: Session, job_id: int):
    return db.query(JobPosting).filter(JobPosting.id == job_id).first()

def get_job_by_link(db: Session, link: str):
    return db.query(JobPosting).filter(JobPosting.link == link).first()

def create_job_posting(
    db: Session,
    company_name: str,
    job_title: str,
    description: str = None,
    deadline: str = None,
    link: str = None,
    source: str = None,
    experience: str = None,
    education: str = None,
    employment_type: str = None,
    location: str = None,
    salary: str = None
):
    db_job = JobPosting(
        company_name=company_name,
        job_title=job_title,
        description=description,
        deadline=deadline,
        link=link,
        source=source,
        experience=experience,
        education=education,
        employment_type=employment_type,
        location=location,
        salary=salary
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

def update_job(
    db: Session,
    job_id: int,
    company_name: str = None,
    job_title: str = None,
    description: str = None,
    deadline: str = None,
    link: str = None,
    source: str = None,
    experience: str = None,
    education: str = None,
    employment_type: str = None,
    location: str = None,
    salary: str = None
):
    db_job = get_job(db, job_id)
    if db_job:
        if company_name:
            db_job.company_name = company_name
        if job_title:
            db_job.job_title = job_title
        if description:
            db_job.description = description
        if deadline:
            db_job.deadline = deadline
        if link:
            db_job.link = link
        if source:
            db_job.source = source
        if experience:
            db_job.experience = experience
        if education:
            db_job.education = education
        if employment_type:
            db_job.employment_type = employment_type
        if location:
            db_job.location = location
        if salary:
            db_job.salary = salary
        
        db.commit()
        db.refresh(db_job)
    return db_job

def delete_job(db: Session, job_id: int):
    db_job = get_job(db, job_id)
    if db_job:
        db.delete(db_job)
        db.commit()
    return db_job

# 자소서 관련 CRUD 함수
def get_resumes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Resume).offset(skip).limit(limit).all()

def get_resume(db: Session, resume_id: int):
    return db.query(Resume).filter(Resume.id == resume_id).first()

def create_resume(db: Session, title: str, file_path: str, text_content: str):
    db_resume = Resume(
        title=title,
        file_path=file_path,
        text_content=text_content,
        uploaded_at=datetime.datetime.utcnow()
    )
    db.add(db_resume)
    db.commit()
    db.refresh(db_resume)
    return db_resume

def update_resume(db: Session, resume_id: int, data: dict):
    db_resume = get_resume(db, resume_id)
    if db_resume:
        for key, value in data.items():
            setattr(db_resume, key, value)
        db.commit()
        db.refresh(db_resume)
    return db_resume

def delete_resume(db: Session, resume_id: int):
    db_resume = get_resume(db, resume_id)
    if db_resume:
        db.delete(db_resume)
        db.commit()
        return True
    return False

# 지원 결과 관련 CRUD 함수
def get_applications(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Application).offset(skip).limit(limit).all()

def get_application(db: Session, application_id: int):
    return db.query(Application).filter(Application.id == application_id).first()

def get_applications_by_resume(db: Session, resume_id: int):
    return db.query(Application).filter(Application.resume_id == resume_id).all()

def create_application(db: Session, job_id: int, resume_id: int, status: str, notes: str = None):
    db_app = Application(
        job_id=job_id,
        resume_id=resume_id,
        status=status,
        notes=notes,
        applied_at=datetime.datetime.utcnow()
    )
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    return db_app

def update_application(db: Session, application_id: int, data: dict):
    db_app = get_application(db, application_id)
    if db_app:
        for key, value in data.items():
            setattr(db_app, key, value)
        db.commit()
        db.refresh(db_app)
    return db_app

def delete_application(db: Session, application_id: int):
    db_app = get_application(db, application_id)
    if db_app:
        db.delete(db_app)
        db.commit()
        return True
    return False

# 피드백 관련 CRUD 함수
def get_feedbacks(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Feedback).offset(skip).limit(limit).all()

def get_feedback(db: Session, feedback_id: int):
    return db.query(Feedback).filter(Feedback.id == feedback_id).first()

def get_feedbacks_by_resume(db: Session, resume_id: int):
    return db.query(Feedback).filter(Feedback.resume_id == resume_id).all()

def create_feedback(db: Session, resume_id: int, feedback_text: str, job_id: int = None):
    db_feedback = Feedback(
        resume_id=resume_id,
        job_id=job_id,
        feedback_text=feedback_text,
        created_at=datetime.datetime.utcnow()
    )
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback

def update_feedback(db: Session, feedback_id: int, data: dict):
    db_feedback = get_feedback(db, feedback_id)
    if db_feedback:
        for key, value in data.items():
            setattr(db_feedback, key, value)
        db.commit()
        db.refresh(db_feedback)
    return db_feedback

def delete_feedback(db: Session, feedback_id: int):
    db_feedback = get_feedback(db, feedback_id)
    if db_feedback:
        db.delete(db_feedback)
        db.commit()
        return True
    return False
