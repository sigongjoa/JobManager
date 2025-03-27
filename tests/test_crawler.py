#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
크롤러 테스트 스크립트
"""

import os
import sys
import logging
import time
import requests
from bs4 import BeautifulSoup
import re
from improved_url_deadline_extractor import extract_company_and_title, extract_deadline_from_job_page

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_crawler():
    # 테스트할 URL 목록
    test_urls = [
        "https://www.wanted.co.kr/wd/253325",  # 뷰런테크놀로지 Deep Learning Engineer 채용공고
    ]
    
    print("\n=== 크롤링 테스트 결과 ===\n")
    
    for url in test_urls:
        print(f"\n=== 테스트 URL: {url} ===")
        
        try:
            # 회사명, 제목, 설명 추출
            print("\n크롤링 시작...")
            company, title, description = extract_company_and_title(url)
            
            print(f"\n[회사 정보]")
            print(f"회사명: {company}")
            
            print(f"\n[채용공고 정보]")
            print(f"제목: {title}")
            
            print(f"\n[상세 정보]")
            print(f"설명 길이: {len(description) if description else 0}")
            if description and description != "정보 없음":
                print("\n=== 설명 내용 ===")
                print(description[:1000] + "..." if len(description) > 1000 else description)
                print("\n=== 설명 끝 ===")
            else:
                print("설명 내용이 없습니다.")
            
            # 마감일 추출
            deadline = extract_deadline_from_job_page(url)
            print(f"\n[마감 정보]")
            print(f"마감일: {deadline}")
            
        except Exception as e:
            print(f"\n[에러 발생]")
            print(f"에러 내용: {str(e)}")
            
        print("\n" + "="*50)

if __name__ == "__main__":
    test_crawler()
