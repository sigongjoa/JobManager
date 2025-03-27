from crawler.final_saramin_crawler import FinalSaraminCrawler
import json
import csv
from datetime import datetime

# 크롤러 생성 및 실행
crawler = FinalSaraminCrawler()
url = "https://www.saramin.co.kr/zf_user/jobs/relay/view?isMypage=no&rec_idx=50253870"
job_data = crawler.crawl_job_detail(url)

if job_data:
    print(f"\n채용 공고 정보:")
    print(f"  회사명: {job_data.get('company_name', '정보 없음')}")
    print(f"  공고 제목: {job_data.get('job_title', '정보 없음')}")
    print(f"  마감일: {job_data.get('application_deadline', '정보 없음')}")
    print(f"  근무지: {job_data.get('location', '정보 없음')}")
    print(f"  경력: {job_data.get('experience', '정보 없음')}")
    print(f"  학력: {job_data.get('education', '정보 없음')}")
    print(f"  고용형태: {job_data.get('employment_type', '정보 없음')}")
    print(f"  급여: {job_data.get('salary', '정보 없음')}")
    print(f"  복리후생: {job_data.get('welfare_benefits', '정보 없음')[:100]}...")
    
    # JSON 파일로 저장
    with open('saramin_jobs.json', 'w', encoding='utf-8') as f:
        json.dump(job_data, f, ensure_ascii=False, indent=2)
    
    # CSV 파일로 저장
    with open('saramin_jobs.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(job_data.keys())  # 헤더
        writer.writerow(job_data.values())  # 데이터
    
    print("\n결과가 saramin_jobs.csv와 saramin_jobs.json 파일에 저장되었습니다.") 