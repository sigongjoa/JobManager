from fastapi import FastAPI, HTTPException, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from crawler.final_saramin_crawler import FinalSaraminCrawler
from database import Database
import logging
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# 정적 파일과 템플릿 설정
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 데이터베이스 초기화
db = Database()

# Pydantic 모델
class JobPosting(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    experience: Optional[str] = None
    education: Optional[str] = None
    employment_type: Optional[str] = None
    salary: Optional[str] = None
    deadline: Optional[str] = None
    description: Optional[str] = None
    link: str
    platform: str
    crawled_at: datetime = datetime.now()

class CrawlRequest(BaseModel):
    url: str
    platform: Optional[str] = "Saramin"

class Resume(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    education: List[str]
    experience: List[str]
    skills: List[str]
    created_at: datetime = datetime.now()

class Application(BaseModel):
    id: str
    job_id: str
    job_title: str
    company: str
    status: str
    applied_at: datetime = datetime.now()
    feedback: Optional[str] = None

class Portfolio(BaseModel):
    title: str
    description: str
    link: Optional[str] = None

# 의존성 함수
def get_db():
    return db

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/crawl/saramin")
async def crawl_saramin(request: CrawlRequest):
    try:
        # URL 유효성 검사
        if not request.url or not request.url.startswith("https://www.saramin.co.kr"):
            raise HTTPException(status_code=400, detail="유효하지 않은 사람인 URL입니다.")

        # 크롤러 인스턴스 생성 및 실행
        crawler = FinalSaraminCrawler()
        job_data = crawler.crawl_job_detail(request.url)
        
        if not job_data:
            raise HTTPException(status_code=404, detail="채용 공고를 찾을 수 없습니다.")

        # 데이터베이스에 저장
        job_posting = JobPosting(**job_data, platform="Saramin")
        db.save_job_posting(job_posting)

        return {"success": True, "job": job_data}

    except Exception as e:
        logger.error(f"크롤링 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs")
async def get_jobs(db: Database = Depends(get_db)):
    try:
        jobs = db.get_job_postings()
        return {"success": True, "jobs": jobs}
    except Exception as e:
        logger.error(f"채용 공고 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str, db: Database = Depends(get_db)):
    try:
        job = db.get_job_posting(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="채용 공고를 찾을 수 없습니다.")
        return {"success": True, "job": job}
    except Exception as e:
        logger.error(f"채용 공고 상세 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/resumes")
async def create_resume(resume: Resume, db: Database = Depends(get_db)):
    try:
        db.save_resume(resume)
        return {"success": True, "message": "이력서가 저장되었습니다."}
    except Exception as e:
        logger.error(f"이력서 저장 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/resumes")
async def get_resumes(db: Database = Depends(get_db)):
    try:
        resumes = db.get_resumes()
        return {"success": True, "resumes": resumes}
    except Exception as e:
        logger.error(f"이력서 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/resumes/{resume_id}")
async def get_resume(resume_id: str, db: Database = Depends(get_db)):
    try:
        resume = db.get_resume(resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail="이력서를 찾을 수 없습니다.")
        return {"success": True, "resume": resume}
    except Exception as e:
        logger.error(f"이력서 상세 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/applications")
async def create_application(application: Application, db: Database = Depends(get_db)):
    try:
        db.save_application(application)
        return {"success": True, "message": "지원 현황이 저장되었습니다."}
    except Exception as e:
        logger.error(f"지원 현황 저장 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/applications")
async def get_applications(db: Database = Depends(get_db)):
    try:
        applications = db.get_applications()
        # 오늘의 크롤링 수 계산
        today = datetime.now().date()
        today_crawls = len([app for app in applications if app.get('applied_at', '').startswith(today.strftime('%Y-%m-%d'))])
        return {
            "success": True,
            "applications": applications,
            "todayCrawls": today_crawls
        }
    except Exception as e:
        logger.error(f"지원 현황 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/applications/{application_id}")
async def get_application(application_id: str, db: Database = Depends(get_db)):
    try:
        application = db.get_application(application_id)
        if not application:
            raise HTTPException(status_code=404, detail="지원 현황을 찾을 수 없습니다.")
        return {"success": True, "application": application}
    except Exception as e:
        logger.error(f"지원 현황 상세 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/portfolio")
async def create_portfolio(portfolio: Portfolio, db: Database = Depends(get_db)):
    try:
        db.save_portfolio(portfolio.dict())
        return {"success": True}
    except Exception as e:
        logger.error(f"포트폴리오 저장 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolio")
async def get_portfolio(db: Database = Depends(get_db)):
    try:
        portfolio = db.get_portfolio()
        return {"success": True, "portfolio": portfolio}
    except Exception as e:
        logger.error(f"포트폴리오 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
