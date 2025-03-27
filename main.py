from fastapi import FastAPI, HTTPException, Depends, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from crawler.final_saramin_crawler import FinalSaraminCrawler
from database import Database, get_db
from sqlalchemy.orm import Session
import logging
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()

# 정적 파일과 템플릿 설정
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Pydantic 모델
class CrawlRequest(BaseModel):
    url: str

class JobResponse(BaseModel):
    success: bool
    job: Optional[dict] = None
    message: Optional[str] = None

class ResumeRequest(BaseModel):
    name: str
    email: str
    phone: str
    education: str
    experience: str
    skills: str

class ApplicationRequest(BaseModel):
    job_id: str
    status: str
    applied_at: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/crawl", response_model=JobResponse)
async def crawl_job(request: CrawlRequest):
    try:
        logger.info(f"크롤링 시작: {request.url}")
        
        # URL 유효성 검사
        if not request.url or not request.url.startswith("https://www.saramin.co.kr"):
            logger.warning("유효하지 않은 URL")
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "유효하지 않은 사람인 URL입니다."}
            )

        # 크롤러 실행
        crawler = FinalSaraminCrawler()
        logger.info("크롤러 인스턴스 생성됨")
        
        job_data = crawler.crawl_job_detail(request.url)
        logger.info(f"크롤링 결과: {job_data}")
        
        if not job_data:
            logger.warning("채용 공고를 찾을 수 없음")
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "채용 공고를 찾을 수 없습니다."}
            )

        # 데이터베이스에 저장
        db = Database()
        saved_job = db.save_job_posting(job_data)
        logger.info(f"저장된 채용 공고: {saved_job}")

        return JSONResponse(
            content={"success": True, "job": saved_job}
        )

    except Exception as e:
        logger.error(f"크롤링 중 오류 발생: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"크롤링 중 오류가 발생했습니다: {str(e)}"}
        )

@app.get("/api/dashboard")
async def get_dashboard_stats():
    try:
        db = Database()
        stats = db.get_dashboard_stats()
        return JSONResponse(content=stats)
    except Exception as e:
        logger.error(f"대시보드 통계 조회 중 오류: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"message": f"대시보드 통계 조회 중 오류가 발생했습니다: {str(e)}"}
        )

@app.get("/api/jobs")
async def get_jobs(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100)):
    try:
        db = Database()
        jobs = db.get_job_postings(skip=skip, limit=limit)
        total = len(db._load_data(db.jobs_file))  # 전체 채용 공고 수
        return JSONResponse(content={
            "success": True,
            "jobs": jobs,
            "total": total,
            "skip": skip,
            "limit": limit
        })
    except Exception as e:
        logger.error(f"채용 공고 목록 조회 중 오류: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"채용 공고 목록 조회 중 오류가 발생했습니다: {str(e)}"}
        )

@app.post("/api/resumes")
async def create_resume(resume_data: ResumeRequest):
    try:
        db = Database()
        saved_resume = db.save_resume(resume_data.dict())
        return JSONResponse(
            content={"success": True, "resume": saved_resume}
        )
    except Exception as e:
        logger.error(f"이력서 저장 중 오류: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"이력서 저장 중 오류가 발생했습니다: {str(e)}"}
        )

@app.get("/api/resumes")
async def get_resumes():
    try:
        db = Database()
        resumes = db.get_resumes()
        return JSONResponse(content={"success": True, "resumes": resumes})
    except Exception as e:
        logger.error(f"이력서 목록 조회 중 오류: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"이력서 목록 조회 중 오류가 발생했습니다: {str(e)}"}
        )

@app.put("/api/resumes/{resume_id}")
async def update_resume(resume_id: str, resume_data: ResumeRequest):
    try:
        db = Database()
        updated_resume = db.update_resume(resume_id, resume_data.dict())
        if not updated_resume:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "이력서를 찾을 수 없습니다."}
            )
        return JSONResponse(content={"success": True, "resume": updated_resume})
    except Exception as e:
        logger.error(f"이력서 수정 중 오류: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"이력서 수정 중 오류가 발생했습니다: {str(e)}"}
        )

@app.delete("/api/resumes/{resume_id}")
async def delete_resume(resume_id: str):
    try:
        db = Database()
        if db.delete_resume(resume_id):
            return JSONResponse(content={"success": True})
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "이력서를 찾을 수 없습니다."}
        )
    except Exception as e:
        logger.error(f"이력서 삭제 중 오류: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"이력서 삭제 중 오류가 발생했습니다: {str(e)}"}
        )

@app.post("/api/applications")
async def create_application(application_data: ApplicationRequest):
    try:
        db = Database()
        saved_application = db.save_application(application_data.dict())
        return JSONResponse(
            content={"success": True, "application": saved_application}
        )
    except Exception as e:
        logger.error(f"지원 현황 저장 중 오류: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"지원 현황 저장 중 오류가 발생했습니다: {str(e)}"}
        )

@app.get("/api/applications")
async def get_applications():
    try:
        db = Database()
        applications = db.get_applications()
        return JSONResponse(content={"success": True, "applications": applications})
    except Exception as e:
        logger.error(f"지원 현황 목록 조회 중 오류: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"지원 현황 목록 조회 중 오류가 발생했습니다: {str(e)}"}
        )

@app.put("/api/applications/{application_id}")
async def update_application_status(application_id: str, status_data: dict):
    try:
        db = Database()
        updated_application = db.update_application(application_id, status_data)
        if not updated_application:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "지원 현황을 찾을 수 없습니다."}
            )
        return JSONResponse(content={"success": True, "application": updated_application})
    except Exception as e:
        logger.error(f"지원 현황 상태 업데이트 중 오류: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"지원 현황 상태 업데이트 중 오류가 발생했습니다: {str(e)}"}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
