from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
from models import JobPosting
from .final_saramin_crawler import FinalSaraminCrawler
from pydantic import BaseModel
import crud
import logging
import json

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

router = APIRouter()

class CrawlRequest(BaseModel):
    url: str
    platform: str

def format_job_response(job):
    """일관된 형식의 job 응답을 반환"""
    try:
        response = {
            "id": job.id,
            "company_name": job.company_name,
            "job_title": job.job_title,
            "deadline": job.deadline,
            "link": job.link,
            "experience": job.experience,
            "education": job.education,
            "employment_type": job.employment_type,
            "location": job.location,
            "salary": job.salary
        }
        logger.debug(f"포맷된 job 응답: {json.dumps(response, ensure_ascii=False, indent=2)}")
        return response
    except Exception as e:
        logger.error(f"Job 응답 포맷 중 오류 발생: {str(e)}")
        logger.error(f"Job 객체 정보: {vars(job)}")
        raise

@router.post("/crawl")
async def crawl_job(req: CrawlRequest, db: Session = Depends(get_db)):
    """채용 공고 URL을 크롤링하여 데이터베이스에 저장"""
    logger.info(f"[API] 크롤링 요청 시작 - URL: {req.url}, Platform: {req.platform}")
    
    try:
        # URL 유효성 검사
        if not req.url:
            logger.warning("[API] URL이 제공되지 않음")
            raise HTTPException(
                status_code=400,
                detail="URL이 제공되지 않았습니다."
            )

        # 테스트 데이터 반환
        if 'test.com' in req.url:
            logger.info("[API] 테스트 데이터 반환")
            test_data = {
                "message": "테스트 데이터가 성공적으로 반환되었습니다.",
                "jobs": [{
                    "id": 1,
                    "title": "테스트 직무",
                    "company": "테스트 회사",
                    "deadline": "2024-12-31",
                    "link": req.url,
                    "experience": "신입/경력",
                    "education": "학력무관",
                    "employment_type": "정규직",
                    "location": "서울",
                    "salary": "회사내규에 따름",
                    "description": "테스트 직무 상세 설명입니다."
                }]
            }
            logger.info(f"[API] 테스트 데이터: {json.dumps(test_data, ensure_ascii=False)}")
            return JSONResponse(content=test_data)

        # 이미 존재하는 URL인지 확인
        logger.info("[API] 기존 URL 확인 중...")
        existing_job = crud.get_job_by_link(db, req.url)
        if existing_job:
            logger.info(f"[API] 기존 채용공고 발견 - ID: {existing_job.id}")
            return {
                "message": "이미 등록된 채용 공고입니다.",
                "jobs": [{
                    "id": existing_job.id,
                    "title": existing_job.job_title,
                    "company": existing_job.company_name,
                    "deadline": existing_job.deadline,
                    "link": existing_job.link,
                    "experience": existing_job.experience,
                    "education": existing_job.education,
                    "employment_type": existing_job.employment_type,
                    "location": existing_job.location,
                    "salary": existing_job.salary,
                    "description": existing_job.description
                }]
            }

        # 실제 크롤러 실행
        logger.info("[API] 크롤러 초기화 중...")
        crawler = FinalSaraminCrawler()
        logger.info("[API] 크롤링 시작...")
        job_data = crawler.crawl_job_detail(req.url)
        
        if job_data:
            logger.info("[API] 크롤링 성공")
            logger.debug(f"[API] 크롤링된 데이터: {json.dumps(job_data, ensure_ascii=False, indent=2)}")
        else:
            logger.warning("[API] 크롤링 결과 없음")
            raise HTTPException(
                status_code=400,
                detail="채용공고 정보를 가져올 수 없습니다."
            )

        # 데이터베이스에 저장
        logger.info("[API] 데이터베이스 저장 시작")
        try:
            job = crud.create_job_posting(
                db,
                company_name=job_data.get('company_name', ''),
                job_title=job_data.get('title', ''),
                description=job_data.get('description', ''),
                deadline=job_data.get('deadline', ''),
                link=req.url,
                experience=job_data.get('experience', ''),
                education=job_data.get('education', ''),
                employment_type=job_data.get('employment_type', ''),
                location=job_data.get('location', ''),
                salary=job_data.get('salary', ''),
                source=req.platform
            )
            logger.info("[API] 데이터베이스 저장 성공")
            logger.debug(f"[API] 생성된 job 객체: {vars(job)}")
        except Exception as db_error:
            logger.error(f"[API] 데이터베이스 저장 실패: {str(db_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"데이터베이스 저장 중 오류가 발생했습니다: {str(db_error)}"
            )

        return {
            "message": "채용 공고가 성공적으로 등록되었습니다.",
            "jobs": [{
                "id": job.id,
                "title": job.job_title,
                "company": job.company_name,
                "deadline": job.deadline,
                "link": job.link,
                "experience": job.experience,
                "education": job.education,
                "employment_type": job.employment_type,
                "location": job.location,
                "salary": job.salary,
                "description": job.description
            }]
        }

    except HTTPException as he:
        logger.error(f"[API] HTTP 오류: {str(he)}")
        raise he
    except Exception as e:
        logger.error(f"[API] 예상치 못한 오류 발생: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"크롤링 중 오류가 발생했습니다: {str(e)}"
        ) 