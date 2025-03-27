#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Wanted 채용 공고 크롤러
"""

import os
import re
import time
import json
import random
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import warnings

# BeautifulSoup의 :contains 경고 무시
warnings.filterwarnings("ignore", category=FutureWarning)

class WantedCrawler:
    """Wanted 채용 공고 크롤링을 위한 클래스"""
    
    def __init__(self):
        """초기화 함수"""
        # 사용자 에이전트 목록
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0'
        ]
        
        # Selenium 웹드라이버 설정
        chrome_options = Options()
        
        # 랜덤 사용자 에이전트 설정
        self.user_agent = random.choice(user_agents)
        chrome_options.add_argument(f'user-agent={self.user_agent}')
        
        # 봇 감지 회피를 위한 설정
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # 추가적인 봇 감지 회피 설정
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--lang=ko_KR')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        
        # 세션 충돌 방지를 위한 설정
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--no-service-autorun')
        chrome_options.add_argument('--password-store=basic')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--disable-popup-blocking')
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        # 봇 감지 회피를 위한 추가 설정
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": self.user_agent})
    
    def crawl(self, url):
        """
        주어진 URL의 채용 공고를 크롤링합니다.
        
        Args:
            url (str): 크롤링할 Wanted 채용 공고 URL
            
        Returns:
            dict: 크롤링된 채용 정보
        """
        print(f"크롤링 시작: {url}")
        
        # URL 유효성 검사
        if not url.startswith('https://www.wanted.co.kr/wd/'):
            raise ValueError("유효한 Wanted 채용 공고 URL이 아닙니다.")
        
        # 페이지 로드
        self.driver.get(url)
        time.sleep(5)  # 초기 로딩 대기 시간 증가
        
        try:
            # 실제 콘텐츠가 로드될 때까지 대기
            wait = WebDriverWait(self.driver, 20)  # 타임아웃 시간 증가
            
            # 회사명이 로드될 때까지 대기
            wait.until(lambda driver: driver.find_element(By.CSS_SELECTOR, 
                "div.JobHeader_className__nhyKU"))
            
            # 채용 상세 내용이 로드될 때까지 대기
            wait.until(lambda driver: driver.find_element(By.CSS_SELECTOR, 
                "div.JobDescription_className__U5Q_x"))
            
            # 스크롤 전에 추가 대기
            time.sleep(2)
            
            # 전체 페이지 내용을 보기 위해 스크롤 다운
            self._scroll_to_bottom()
            
            # 스크롤 후 추가 대기
            time.sleep(2)
            
        except Exception as e:
            print(f"페이지 로드 대기 중 오류: {e}")
            import traceback
            print(traceback.format_exc())
            time.sleep(5)  # 오류 발생 시 추가 대기
        
        # 페이지 소스 가져오기
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # 채용 정보 추출
        job_data = self._extract_job_data(soup)
        job_data['url'] = url
        
        print(f"크롤링 완료: {url}")
        return job_data
    
    def _bypass_protection(self):
        """봇 감지 우회를 위한 추가 동작 수행"""
        # 랜덤 마우스 움직임 시뮬레이션
        for _ in range(3):
            x = random.randint(100, 700)
            y = random.randint(100, 500)
            self.driver.execute_script(f"window.scrollTo({x}, {y})")
            time.sleep(random.uniform(0.5, 1.5))
        
        # 쿠키 수락 버튼 클릭 시도
        try:
            cookie_buttons = self.driver.find_elements(By.XPATH, 
                "//button[contains(text(), '수락') or contains(text(), 'Accept') or contains(text(), '동의')]")
            if cookie_buttons:
                cookie_buttons[0].click()
                time.sleep(1)
        except Exception as e:
            print(f"쿠키 버튼 클릭 시도 중 오류: {e}")
    
    def _scroll_to_bottom(self):
        """페이지 전체 내용을 보기 위해 하단까지 스크롤합니다."""
        # 초기 높이
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # 페이지 하단으로 스크롤
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # 랜덤 대기 시간
            time.sleep(random.uniform(1.0, 2.0))
            
            # 새 스크롤 높이 계산
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # 스크롤이 더 이상 내려가지 않으면 종료
            if new_height == last_height:
                break
                
            last_height = new_height
            
            # 봇 감지 회피를 위한 랜덤 중간 스크롤
            if random.random() < 0.3:  # 30% 확률로
                middle_height = last_height * random.uniform(0.3, 0.7)
                self.driver.execute_script(f"window.scrollTo(0, {middle_height});")
                time.sleep(random.uniform(0.5, 1.0))
    
    def _extract_job_data(self, soup):
        """
        BeautifulSoup 객체에서 채용 정보를 추출합니다.
        
        Args:
            soup (BeautifulSoup): 파싱된 HTML
            
        Returns:
            dict: 추출된 채용 정보
        """
        job_data = {}
        
        try:
            # 디버깅을 위한 HTML 저장
            print("\n=== 페이지 HTML ===")
            print(soup.prettify()[:1000])  # 처음 1000자만 출력
            
            # 회사명 추출
            company_name = soup.select_one('div.JobHeader_className__nhyKU h6')
            if company_name:
                job_data['company_name'] = company_name.text.strip()
            else:
                job_data['company_name'] = "회사명 없음"
            
            # 채용 공고 제목 추출
            title = soup.select_one('div.JobHeader_className__nhyKU h2')
            if title:
                job_data['title'] = title.text.strip()
            else:
                job_data['title'] = "채용공고명 없음"
            
            # 포지션 설명 전체 텍스트 가져오기
            position_description = soup.select_one('div.JobDescription_className__U5Q_x')
            
            if position_description:
                # 전체 텍스트를 가져와서 줄바꿈으로 분리
                full_text = position_description.get_text('\n', strip=True)
                
                # 섹션별로 내용 추출
                sections = {
                    'main_tasks': [],
                    'requirements': [],
                    'preferences': [],
                    'benefits': []
                }
                
                current_section = None
                lines = full_text.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 섹션 제목 확인
                    if any(keyword in line for keyword in ['주요업무', '핵심업무', '담당업무']):
                        current_section = 'main_tasks'
                        continue
                    elif any(keyword in line for keyword in ['자격요건', '필수사항', '지원자격']):
                        current_section = 'requirements'
                        continue
                    elif '우대사항' in line:
                        current_section = 'preferences'
                        continue
                    elif any(keyword in line for keyword in ['혜택', '복지', '처우']):
                        current_section = 'benefits'
                        continue
                    
                    # 현재 섹션이 있으면 내용 추가
                    if current_section and line:
                        sections[current_section].append(line)
                
                # 결과 저장
                for section_name, content in sections.items():
                    if content:
                        job_data[section_name] = '\n'.join(content)
                    else:
                        job_data[section_name] = f"{section_name} 정보 없음"
                
                # 통합 description 생성
                description_parts = []
                section_titles = {
                    'main_tasks': '주요업무',
                    'requirements': '자격요건',
                    'preferences': '우대사항',
                    'benefits': '혜택 및 복지'
                }
                
                for section_name, title in section_titles.items():
                    if sections[section_name]:
                        description_parts.append(f"[ {title} ]\n" + job_data[section_name])
                
                job_data['description'] = "\n\n".join(description_parts) if description_parts else "상세 내용 없음"
            else:
                print("포지션 설명을 찾을 수 없습니다.")
                job_data.update({
                    'main_tasks': "주요업무 정보 없음",
                    'requirements': "자격요건 정보 없음",
                    'preferences': "우대사항 정보 없음",
                    'benefits': "혜택 및 복지 정보 없음",
                    'description': "상세 내용 없음"
                })
            
            # 마감일은 상시채용으로 설정
            job_data['deadline'] = "상시채용"
            
            # 디버깅을 위한 출력
            print("\n=== 추출된 데이터 ===")
            for key, value in job_data.items():
                if key != 'description':  # description은 너무 길어서 제외
                    print(f"{key}: {value}")
            
        except Exception as e:
            print(f"\n!!! 데이터 추출 중 오류 발생: {str(e)}")
            import traceback
            print(traceback.format_exc())
            
            # 기본값 설정
            job_data.update({
                'company_name': "회사명 없음",
                'title': "채용공고명 없음",
                'main_tasks': "주요업무 정보 없음",
                'requirements': "자격요건 정보 없음",
                'preferences': "우대사항 정보 없음",
                'benefits': "혜택 및 복지 정보 없음",
                'deadline': "상시채용",
                'description': "상세 내용 없음"
            })
        
        return job_data
    
    def close(self):
        """웹드라이버 종료"""
        if self.driver:
            self.driver.quit()
            print("웹드라이버 종료")

