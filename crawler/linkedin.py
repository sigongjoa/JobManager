#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LinkedIn 채용 공고 크롤러 (로그인 기능 포함)

이 스크립트는 LinkedIn의 채용 공고 페이지를 크롤링하여 채용 정보와 회사 정보를 수집합니다.
로그인 기능을 포함하여 더 많은 정보에 접근할 수 있습니다.
"""

import os
import sys
import json
import time
import random
import argparse
import re
import requests
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus, urlparse, parse_qs

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, 
    StaleElementReferenceException, ElementClickInterceptedException
)
from webdriver_manager.chrome import ChromeDriverManager

from bs4 import BeautifulSoup


class LinkedInJobCrawler:
    """LinkedIn 채용 공고 크롤러 클래스 (로그인 기능 포함)"""
    
    def __init__(self, output_dir="linkedin_job_data", headless=False):
        """크롤러 초기화
        
        Args:
            output_dir (str, optional): 출력 디렉토리 경로
            headless (bool, optional): 헤드리스 모드 사용 여부
        """
        self.output_dir = output_dir
        self.headless = headless
        self.driver = None
        self.is_logged_in = False
        
        # 출력 디렉토리 생성
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "jobs"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "companies"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "images"), exist_ok=True)
        
        print(f"출력 디렉토리가 생성되었습니다: {self.output_dir}")
        
        # 웹드라이버 초기화
        self._init_webdriver()
    
    def _init_webdriver(self):
        """웹드라이버 초기화"""
        try:
            chrome_options = Options()
            
            # 헤드리스 모드 설정
            if self.headless:
                chrome_options.add_argument("--headless=new")
            
            # 기타 옵션 설정
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # 봇 감지 회피를 위한 설정
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)
            
            # User-Agent 설정
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
            ]
            chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")
            
            # 웹드라이버 생성
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 웹드라이버 설정
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                """
            })
            
            # 타임아웃 설정
            self.driver.set_page_load_timeout(30)
            
            print("웹드라이버가 초기화되었습니다.")
        
        except Exception as e:
            print(f"웹드라이버 초기화 오류: {e}")
            sys.exit(1)
    
    def __del__(self):
        """소멸자: 웹드라이버 종료"""
        if self.driver:
            self.driver.quit()
            print("웹드라이버가 종료되었습니다.")
    
    def login(self, email, password):
        """LinkedIn 로그인
        
        Args:
            email (str): LinkedIn 계정 이메일
            password (str): LinkedIn 계정 비밀번호
            
        Returns:
            bool: 로그인 성공 여부
        """
        try:
            print("LinkedIn 로그인 시도 중...")
            
            # 로그인 페이지 접속
            self.driver.get("https://www.linkedin.com/login")
            self._wait_for_page_load(timeout=10)
            
            # 이메일 입력
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_input.clear()
            email_input.send_keys(email)
            
            # 비밀번호 입력
            password_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "password"))
            )
            password_input.clear()
            password_input.send_keys(password)
            
            # 로그인 버튼 클릭
            login_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
            )
            login_button.click()
            
            # 로그인 성공 확인
            try:
                WebDriverWait(self.driver, 15).until(
                    lambda d: "feed" in d.current_url or "checkpoint" in d.current_url or "dashboard" in d.current_url
                )
                
                # 보안 확인 페이지 처리
                if "checkpoint" in self.driver.current_url:
                    print("보안 확인 페이지가 감지되었습니다. 수동 확인이 필요합니다.")
                    input("보안 확인을 완료한 후 Enter 키를 눌러주세요...")
                
                self.is_logged_in = True
                print("LinkedIn 로그인 성공!")
                
                # 쿠키 저장
                self._save_cookies()
                
                return True
            
            except TimeoutException:
                print("로그인 실패: 타임아웃 또는 잘못된 자격 증명")
                return False
        
        except Exception as e:
            print(f"로그인 오류: {e}")
            return False
    
    def _save_cookies(self):
        """쿠키 저장"""
        try:
            cookies = self.driver.get_cookies()
            with open(os.path.join(self.output_dir, "linkedin_cookies.json"), "w") as f:
                json.dump(cookies, f)
            print("쿠키가 저장되었습니다.")
        except Exception as e:
            print(f"쿠키 저장 오류: {e}")
    
    def _load_cookies(self):
        """쿠키 로드"""
        try:
            cookie_file = os.path.join(self.output_dir, "linkedin_cookies.json")
            if os.path.exists(cookie_file):
                with open(cookie_file, "r") as f:
                    cookies = json.load(f)
                
                # LinkedIn 도메인 접속
                self.driver.get("https://www.linkedin.com")
                time.sleep(2)
                
                # 쿠키 추가
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except:
                        pass
                
                # 페이지 새로고침
                self.driver.refresh()
                time.sleep(3)
                
                # 로그인 상태 확인
                if self._check_login_status():
                    self.is_logged_in = True
                    print("저장된 쿠키로 로그인 성공!")
                    return True
                else:
                    print("저장된 쿠키로 로그인 실패")
                    return False
            else:
                print("저장된 쿠키 파일이 없습니다.")
                return False
        except Exception as e:
            print(f"쿠키 로드 오류: {e}")
            return False
    
    def _check_login_status(self):
        """로그인 상태 확인
        
        Returns:
            bool: 로그인 상태 여부
        """
        try:
            # 프로필 아이콘 확인
            profile_nav = self.driver.find_elements(By.CSS_SELECTOR, ".global-nav__me-photo, .profile-rail-card__actor-link img")
            if profile_nav and len(profile_nav) > 0:
                return True
            
            # 로그인 버튼 확인 (없어야 함)
            login_buttons = self.driver.find_elements(By.CSS_SELECTOR, "a[data-tracking-control-name='guest_homepage-basic_nav-header-signin'], a.nav__button-secondary")
            if not login_buttons or len(login_buttons) == 0:
                return True
            
            return False
        except:
            return False
    
    def search_jobs(self, keyword, location="대한민국", count=10):
        """LinkedIn에서 채용 공고 검색
        
        Args:
            keyword (str): 검색 키워드
            location (str, optional): 위치
            count (int, optional): 수집할 채용 공고 수
            
        Returns:
            list: 수집된 채용 공고 목록
        """
        print(f"LinkedIn에서 '{keyword}' 키워드로 채용 공고 검색 중...")
        
        # 쿠키로 로그인 시도
        if not self.is_logged_in:
            self._load_cookies()
        
        # 검색 URL 생성
        search_url = f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(keyword)}&location={quote_plus(location)}"
        
        try:
            # 검색 페이지 접속
            self.driver.get(search_url)
            print(f"검색 페이지에 접속했습니다: {search_url}")
            
            # 페이지 로딩 대기
            self._wait_for_page_load(timeout=20)
            
            # 로그인 팝업 처리
            self._handle_login_popup()
            
            # 페이지 스크린샷 저장 (디버깅용)
            screenshot_path = os.path.join(self.output_dir, "linkedin_search_page.png")
            self.driver.save_screenshot(screenshot_path)
            print(f"검색 페이지 스크린샷을 저장했습니다: {screenshot_path}")
            
            # 페이지 스크롤 다운하여 더 많은 결과 로드
            self._scroll_page()
            
            # 채용 공고 목록 수집
            job_listings = []
            collected_count = 0
            page_num = 1
            
            while collected_count < count:
                print(f"채용 공고 목록 페이지 {page_num} 수집 중...")
                
                # 현재 페이지의 채용 공고 목록 가져오기
                job_cards = self._get_job_cards()
                
                if not job_cards or len(job_cards) == 0:
                    print("채용 공고 목록을 찾을 수 없습니다.")
                    break
                
                print(f"{len(job_cards)}개의 채용 공고 카드를 찾았습니다.")
                
                # 각 채용 공고 처리
                for i, job_card in enumerate(job_cards[:min(count - collected_count, len(job_cards))]):
                    try:
                        # 채용 공고 URL 추출
                        job_url = self._extract_job_url(job_card)
                        
                        if not job_url:
                            continue
                        
                        print(f"채용 공고 URL: {job_url}")
                        
                        # 채용 공고 페이지 접속
                        self.driver.get(job_url)
                        self._wait_for_page_load(timeout=15)
                        
                        # 로그인 팝업 처리
                        self._handle_login_popup()
                        
                        # 채용 공고 정보 추출
                        job_info = self._extract_job_info()
                        
                        if job_info:
                            job_listings.append(job_info)
                            collected_count += 1
                            print(f"채용 공고 {collected_count}/{count} 수집 완료: {job_info.get('title', '제목 없음')}")
                            
                            # 이미지 다운로드
                            if job_info.get('company_logo_url'):
                                logo_path = self._download_image(
                                    job_info['company_logo_url'],
                                    f"{self._clean_filename(job_info['company_name'])}_logo"
                                )
                                job_info['company_logo_local_path'] = logo_path
                            
                            # 목표 수량 달성 확인
                            if collected_count >= count:
                                break
                        
                        # 검색 결과 페이지로 돌아가기
                        self.driver.get(search_url)
                        self._wait_for_page_load(timeout=15)
                        
                        # 페이지 스크롤
                        self._scroll_to_position(i + 1)
                        
                        # 랜덤 딜레이
                        time.sleep(random.uniform(2, 4))
                    
                    except Exception as e:
                        print(f"채용 공고 처리 중 오류: {e}")
                        # 검색 결과 페이지로 돌아가기
                        self.driver.get(search_url)
                        self._wait_for_page_load(timeout=15)
                        continue
                
                # 다음 페이지로 이동
                if collected_count < count:
                    if not self._go_to_next_page():
                        print("더 이상 다음 페이지가 없습니다.")
                        break
                    page_num += 1
            
            print(f"총 {len(job_listings)}개 채용 공고 수집 완료")
            
            # 수집 결과 저장
            self._save_job_listings(job_listings, keyword)
            
            return job_listings
        
        except Exception as e:
            print(f"채용 공고 검색 오류: {e}")
            return []
    
    def _get_job_cards(self):
        """채용 공고 카드 요소 가져오기
        
        Returns:
            list: 채용 공고 카드 요소 목록
        """
        # 여러 선택자 시도
        selectors = [
            ".jobs-search-results__list-item",
            ".job-search-card",
            ".jobs-search-two-pane__job-card-container--viewport-tracking-0",
            "li.jobs-search-results__list-item",
            ".base-card.job-search-card"
        ]
        
        for selector in selectors:
            try:
                job_cards = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                )
                if job_cards and len(job_cards) > 0:
                    print(f"채용 공고 카드를 찾았습니다. 선택자: {selector}")
                    return job_cards
            except:
                continue
        
        # 직접 HTML 파싱 시도
        print("선택자로 채용 공고를 찾을 수 없어 HTML 직접 파싱을 시도합니다.")
        html = self.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # 다양한 선택자로 시도
        for selector in [".job-search-card", ".jobs-search-results__list-item", ".base-card.job-search-card"]:
            job_elements = soup.select(selector)
            if job_elements and len(job_elements) > 0:
                print(f"BeautifulSoup으로 {len(job_elements)}개의 채용 공고를 찾았습니다. 선택자: {selector}")
                
                # 각 요소의 링크 추출
                job_urls = []
                for job_elem in job_elements:
                    link_elem = None
                    for link_selector in ["a.job-card-container__link", "a.base-card__full-link", "a[data-control-name='job_card_title']"]:
                        link_elem = job_elem.select_one(link_selector)
                        if link_elem and link_elem.has_attr('href'):
                            job_urls.append(link_elem['href'])
                            break
                
                return job_urls
        
        return []
    
    def _extract_job_url(self, job_card):
        """채용 공고 카드에서 URL 추출
        
        Args:
            job_card: 채용 공고 카드 요소 또는 URL 문자열
            
        Returns:
            str: 채용 공고 URL
        """
        # 이미 URL 문자열인 경우
        if isinstance(job_card, str):
            if not job_card.startswith("http"):
                return f"https://www.linkedin.com{job_card}"
            return job_card
        
        try:
            # Selenium 요소인 경우
            # 여러 선택자 시도
            for selector in ["a.job-card-container__link", "a.base-card__full-link", "a[data-control-name='job_card_title']"]:
                try:
                    link_elem = job_card.find_element(By.CSS_SELECTOR, selector)
                    if link_elem:
                        job_url = link_elem.get_attribute("href")
                        if job_url:
                            return job_url
                except:
                    continue
            
            # 직접 속성 추출 시도
            try:
                job_url = job_card.get_attribute("href")
                if job_url:
                    return job_url
            except:
                pass
            
            # JavaScript로 데이터 추출 시도
            try:
                job_id = job_card.get_attribute("data-entity-urn") or job_card.get_attribute("data-job-id")
                if job_id:
                    if ":" in job_id:
                        job_id = job_id.split(":")[-1]
                    return f"https://www.linkedin.com/jobs/view/{job_id}"
            except:
                pass
            
            # 클릭 후 URL 가져오기 시도
            try:
                # 새 탭에서 열기
                self.driver.execute_script("arguments[0].setAttribute('target', '_blank');", job_card)
                job_card.click()
                
                # 새 탭으로 전환
                self.driver.switch_to.window(self.driver.window_handles[-1])
                
                # URL 가져오기
                job_url = self.driver.current_url
                
                # 원래 탭으로 돌아가기
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                
                return job_url
            except:
                # 원래 탭으로 돌아가기 시도
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                
                pass
        
        except Exception as e:
            print(f"채용 공고 URL 추출 오류: {e}")
        
        return None
    
    def _extract_job_info(self):
        """현재 페이지에서 채용 공고 정보 추출
        
        Returns:
            dict: 추출된 채용 공고 정보
        """
        try:
            # 페이지 소스 가져오기
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # 채용 공고 제목
            title = None
            for title_selector in [".jobs-unified-top-card__job-title", ".topcard__title", "h1.job-title", "h1.top-card-layout__title"]:
                title_elem = soup.select_one(title_selector)
                if title_elem:
                    title = title_elem.text.strip()
                    break
            
            if not title:
                title = "제목 없음"
            
            # 회사 정보
            company_name = None
            for company_selector in [".jobs-unified-top-card__company-name", ".topcard__org-name-link", "a.company-name", "a.topcard__org-name-link", "span.topcard__flavor--bullet"]:
                company_elem = soup.select_one(company_selector)
                if company_elem:
                    company_name = company_elem.text.strip()
                    break
            
            if not company_name:
                company_name = "회사명 없음"
            
            # 회사 로고
            company_logo_url = ""
            for logo_selector in [".jobs-unified-top-card__company-logo", ".company-logo", "img.artdeco-entity-image", "img.lazy-image"]:
                company_logo = soup.select_one(logo_selector)
                if company_logo and company_logo.has_attr('src'):
                    company_logo_url = company_logo['src']
                    break
            
            # 위치 정보
            location = None
            for location_selector in [".jobs-unified-top-card__bullet", ".topcard__flavor--bullet", ".job-location", "span.topcard__flavor--bullet"]:
                location_elems = soup.select(location_selector)
                if location_elems and len(location_elems) > 0:
                    for elem in location_elems:
                        text = elem.text.strip()
                        if "," in text or "시" in text or "도" in text:
                            location = text
                            break
                    if location:
                        break
            
            if not location:
                location = ""
            
            # 근무 형태
            workplace_type = None
            for workplace_selector in [".jobs-unified-top-card__workplace-type", ".topcard__flavor--workplace-type"]:
                workplace_elem = soup.select_one(workplace_selector)
                if workplace_elem:
                    workplace_type = workplace_elem.text.strip()
                    break
            
            if not workplace_type:
                workplace_type = ""
            
            # 지원자 수
            applicants = None
            for applicants_selector in [".jobs-unified-top-card__applicant-count", ".topcard__flavor--metadata"]:
                applicants_elem = soup.select_one(applicants_selector)
                if applicants_elem:
                    applicants = applicants_elem.text.strip()
                    break
            
            if not applicants:
                applicants = ""
            
            # 채용 공고 URL
            job_url = self.driver.current_url
            
            # 채용 공고 상세 내용
            job_description = None
            for description_selector in [".jobs-description__content", ".description__text", ".show-more-less-html__markup", ".jobs-description-content"]:
                job_description_elem = soup.select_one(description_selector)
                if job_description_elem:
                    job_description = job_description_elem.text.strip()
                    break
            
            if not job_description:
                job_description = ""
            
            # 채용 공고 정보 구성
            job_info = {
                "title": title,
                "company_name": company_name,
                "company_logo_url": company_logo_url,
                "location": location,
                "workplace_type": workplace_type,
                "applicants": applicants,
                "job_url": job_url,
                "job_description": job_description,
                "extracted_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 추가 정보 추출
            criteria_container = soup.select(".jobs-unified-top-card__job-insight, .job-criteria-item, .job-details-jobs-unified-top-card__job-insight")
            for criteria in criteria_container:
                criteria_text = criteria.text.strip()
                
                # 경력 요구사항
                if "경력" in criteria_text or "experience" in criteria_text.lower():
                    job_info["experience"] = criteria_text
                
                # 직원 수
                elif "직원" in criteria_text or "employee" in criteria_text.lower():
                    job_info["company_size"] = criteria_text
                
                # 산업 분야
                elif "산업" in criteria_text or "industry" in criteria_text.lower():
                    job_info["industry"] = criteria_text
            
            # 회사 상세 정보 추출
            company_info = self._extract_company_info(company_name)
            if company_info:
                job_info["company_info"] = company_info
            
            # 직무 요구사항 및 자격 요건 추출
            requirements = self._extract_job_requirements(job_description)
            if requirements:
                job_info["requirements"] = requirements
            
            return job_info
        
        except Exception as e:
            print(f"채용 공고 정보 추출 오류: {e}")
            return None
    
    def _extract_company_info(self, company_name):
        """회사 정보 추출
        
        Args:
            company_name (str): 회사명
            
        Returns:
            dict: 추출된 회사 정보
        """
        try:
            # 회사 페이지 버튼 찾기
            company_page_button = None
            try:
                for company_selector in ["a.jobs-unified-top-card__company-url", "a.topcard__org-name-link", "a.company-name"]:
                    try:
                        company_page_button = WebDriverWait(self.driver, 3).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, company_selector))
                        )
                        if company_page_button:
                            break
                    except:
                        continue
            except TimeoutException:
                print(f"'{company_name}' 회사 페이지 버튼을 찾을 수 없습니다.")
                return None
            
            if not company_page_button:
                return None
            
            # 현재 URL 저장
            current_url = self.driver.current_url
            
            # 새 탭에서 회사 페이지 열기
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[1])
            
            # 회사 페이지 URL 가져오기
            company_url = company_page_button.get_attribute('href')
            self.driver.get(company_url)
            
            # 페이지 로딩 대기
            self._wait_for_page_load(timeout=15)
            
            # 로그인 팝업 처리
            self._handle_login_popup()
            
            # 회사 정보 추출
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # 회사 소개
            about = ""
            for about_selector in [".org-about-us-organization-description__text", ".about-us__text", ".company-description"]:
                about_section = soup.select_one(about_selector)
                if about_section:
                    about = about_section.text.strip()
                    break
            
            # 회사 웹사이트
            website = ""
            for website_selector in ["a.org-about-us-company-module__website", "a.website", "a[data-control-name='page_details_module_website_url']"]:
                website_elem = soup.select_one(website_selector)
                if website_elem and website_elem.has_attr('href'):
                    website = website_elem.get('href')
                    break
            
            # 회사 규모
            size = ""
            for size_selector in [".org-about-company-module__company-size-definition-text", ".company-size", ".staffing"]:
                size_elem = soup.select_one(size_selector)
                if size_elem:
                    size = size_elem.text.strip()
                    break
            
            # 회사 유형
            company_type = ""
            for type_selector in [".org-about-company-module__company-type-definition-text", ".company-type"]:
                type_elem = soup.select_one(type_selector)
                if type_elem:
                    company_type = type_elem.text.strip()
                    break
            
            # 산업 분야
            industry = ""
            for industry_selector in [".org-about-company-module__industry", ".industry"]:
                industry_elem = soup.select_one(industry_selector)
                if industry_elem:
                    industry = industry_elem.text.strip()
                    break
            
            # 본사 위치
            headquarters = ""
            for hq_selector in [".org-about-company-module__headquarters", ".headquarters"]:
                hq_elem = soup.select_one(hq_selector)
                if hq_elem:
                    headquarters = hq_elem.text.strip()
                    break
            
            # 설립 연도
            founded = ""
            for founded_selector in [".org-about-company-module__founded", ".founded"]:
                founded_elem = soup.select_one(founded_selector)
                if founded_elem:
                    founded = founded_elem.text.strip()
                    break
            
            # 전문 분야
            specialties = ""
            for specialties_selector in [".org-about-company-module__specialities", ".specialties"]:
                specialties_elem = soup.select_one(specialties_selector)
                if specialties_elem:
                    specialties = specialties_elem.text.strip()
                    break
            
            # 회사 정보 구성
            company_info = {
                "name": company_name,
                "about": about,
                "website": website,
                "size": size,
                "company_type": company_type,
                "industry": industry,
                "headquarters": headquarters,
                "founded": founded,
                "specialties": specialties,
                "linkedin_url": company_url
            }
            
            # 원래 탭으로 돌아가기
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            self.driver.get(current_url)
            
            # 페이지 로딩 대기
            self._wait_for_page_load(timeout=15)
            
            # 회사 정보 저장
            self._save_company_info(company_info)
            
            return company_info
        
        except Exception as e:
            print(f"회사 정보 추출 오류: {e}")
            
            # 오류 발생 시 원래 탭으로 돌아가기
            if len(self.driver.window_handles) > 1:
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
            
            return None
    
    def _extract_job_requirements(self, job_description):
        """채용 공고 설명에서 요구사항 추출
        
        Args:
            job_description (str): 채용 공고 설명
            
        Returns:
            dict: 추출된 요구사항
        """
        if not job_description:
            return None
        
        requirements = {}
        
        # 주요 업무
        main_tasks_match = re.search(r'주요\s*업무|담당\s*업무|What\s*you\'ll\s*do|Responsibilities|Key\s*Responsibilities', job_description, re.IGNORECASE)
        if main_tasks_match:
            start_idx = main_tasks_match.start()
            end_idx = len(job_description)
            
            # 다음 섹션 찾기
            next_section = re.search(r'자격\s*요건|지원\s*자격|Requirements|Qualifications|우대\s*사항|혜택|복지|Benefits', job_description[start_idx:], re.IGNORECASE)
            if next_section:
                end_idx = start_idx + next_section.start()
            
            main_tasks = job_description[start_idx:end_idx].strip()
            requirements["main_tasks"] = main_tasks
        
        # 자격 요건
        qualifications_match = re.search(r'자격\s*요건|지원\s*자격|Requirements|Qualifications', job_description, re.IGNORECASE)
        if qualifications_match:
            start_idx = qualifications_match.start()
            end_idx = len(job_description)
            
            # 다음 섹션 찾기
            next_section = re.search(r'우대\s*사항|혜택|복지|Benefits|Preferred|Nice\s*to\s*have', job_description[start_idx:], re.IGNORECASE)
            if next_section:
                end_idx = start_idx + next_section.start()
            
            qualifications = job_description[start_idx:end_idx].strip()
            requirements["qualifications"] = qualifications
        
        # 우대 사항
        preferred_match = re.search(r'우대\s*사항|Preferred|Nice\s*to\s*have', job_description, re.IGNORECASE)
        if preferred_match:
            start_idx = preferred_match.start()
            end_idx = len(job_description)
            
            # 다음 섹션 찾기
            next_section = re.search(r'혜택|복지|Benefits|회사\s*소개|About\s*us', job_description[start_idx:], re.IGNORECASE)
            if next_section:
                end_idx = start_idx + next_section.start()
            
            preferred = job_description[start_idx:end_idx].strip()
            requirements["preferred"] = preferred
        
        # 혜택 및 복지
        benefits_match = re.search(r'혜택|복지|Benefits|We\s*offer', job_description, re.IGNORECASE)
        if benefits_match:
            start_idx = benefits_match.start()
            end_idx = len(job_description)
            
            # 다음 섹션 찾기
            next_section = re.search(r'회사\s*소개|About\s*us|지원\s*방법|How\s*to\s*apply', job_description[start_idx:], re.IGNORECASE)
            if next_section:
                end_idx = start_idx + next_section.start()
            
            benefits = job_description[start_idx:end_idx].strip()
            requirements["benefits"] = benefits
        
        return requirements if requirements else None
    
    def _handle_login_popup(self):
        """로그인 팝업 처리"""
        try:
            # 로그인 팝업 확인
            login_popups = self.driver.find_elements(By.CSS_SELECTOR, ".authentication-modal, .modal__overlay--visible")
            if login_popups and len(login_popups) > 0:
                print("로그인 팝업이 감지되었습니다.")
                
                # JavaScript로 팝업 닫기 시도
                try:
                    self.driver.execute_script("""
                        var modals = document.querySelectorAll('.modal__overlay--visible, .authentication-modal');
                        for(var i=0; i<modals.length; i++) {
                            modals[i].style.display = 'none';
                        }
                        document.body.classList.remove('overflow-hidden');
                    """)
                    print("JavaScript로 로그인 팝업을 제거했습니다.")
                    time.sleep(1)
                    return True
                except:
                    pass
                
                # 팝업 닫기 버튼 찾기 (여러 선택자 시도)
                for close_selector in ["button.modal__dismiss", "button.artdeco-modal__dismiss", 
                                      "button[aria-label='닫기']", "button[aria-label='Close']",
                                      ".modal__dismiss", ".artdeco-modal__dismiss"]:
                    try:
                        close_buttons = self.driver.find_elements(By.CSS_SELECTOR, close_selector)
                        if close_buttons and len(close_buttons) > 0:
                            # JavaScript로 클릭
                            self.driver.execute_script("arguments[0].click();", close_buttons[0])
                            print(f"로그인 팝업 닫기 버튼을 클릭했습니다. (선택자: {close_selector})")
                            time.sleep(1)
                            return True
                    except:
                        continue
                
                # ESC 키 누르기 시도
                try:
                    webdriver.ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                    print("ESC 키를 눌러 팝업을 닫았습니다.")
                    time.sleep(1)
                    return True
                except:
                    pass
                
                # 로그인 없이 계속하기 버튼 찾기
                for continue_selector in ["button.authwall-join-form__form-toggle--bottom", 
                                         "a.authwall-join-form__form-toggle--bottom",
                                         "button.sign-up-modal__outlet-btn",
                                         "a.sign-up-modal__outlet-btn"]:
                    try:
                        continue_buttons = self.driver.find_elements(By.CSS_SELECTOR, continue_selector)
                        if continue_buttons and len(continue_buttons) > 0:
                            # JavaScript로 클릭
                            self.driver.execute_script("arguments[0].click();", continue_buttons[0])
                            print("로그인 없이 계속하기 버튼을 클릭했습니다.")
                            time.sleep(1)
                            return True
                    except:
                        continue
                
                # 로그인 팝업을 무시하고 계속 진행
                print("로그인 팝업을 처리할 수 없어 무시하고 계속 진행합니다.")
                return True
            
            return True
        
        except Exception as e:
            print(f"로그인 팝업 처리 오류: {e}")
            # 오류가 발생해도 계속 진행
            return True
    
    def _scroll_page(self, count=3):
        """페이지 스크롤
        
        Args:
            count (int, optional): 스크롤 횟수
        """
        try:
            for i in range(count):
                # 스크롤 다운
                self.driver.execute_script("window.scrollBy(0, window.innerHeight);")
                time.sleep(random.uniform(1, 2))
                
                # 로그인 팝업 처리
                self._handle_login_popup()
        except Exception as e:
            print(f"페이지 스크롤 오류: {e}")
    
    def _scroll_to_position(self, position):
        """특정 위치로 스크롤
        
        Args:
            position (int): 스크롤 위치 (카드 인덱스)
        """
        try:
            # 카드 요소 찾기
            job_cards = self._get_job_cards()
            
            if job_cards and len(job_cards) > position:
                # 요소로 스크롤
                self.driver.execute_script("arguments[0].scrollIntoView();", job_cards[position])
                time.sleep(random.uniform(0.5, 1))
            else:
                # 위치 기반 스크롤
                self.driver.execute_script(f"window.scrollTo(0, {position * 300});")
                time.sleep(random.uniform(0.5, 1))
        except Exception as e:
            print(f"스크롤 위치 이동 오류: {e}")
    
    def _go_to_next_page(self):
        """다음 페이지로 이동
        
        Returns:
            bool: 다음 페이지 이동 성공 여부
        """
        try:
            # 다음 페이지 버튼 찾기
            next_button = None
            for next_selector in ["button[aria-label='다음']", "button.artdeco-pagination__button--next", "li.artdeco-pagination__indicator--number.active + li button"]:
                try:
                    next_buttons = self.driver.find_elements(By.CSS_SELECTOR, next_selector)
                    if next_buttons and len(next_buttons) > 0 and next_buttons[0].is_enabled():
                        next_button = next_buttons[0]
                        break
                except:
                    continue
            
            if next_button and next_button.is_enabled():
                # 버튼으로 스크롤
                self.driver.execute_script("arguments[0].scrollIntoView();", next_button)
                time.sleep(random.uniform(1, 2))
                
                # 버튼 클릭
                try:
                    next_button.click()
                except ElementClickInterceptedException:
                    # JavaScript로 클릭
                    self.driver.execute_script("arguments[0].click();", next_button)
                
                time.sleep(random.uniform(3, 5))
                
                # 로그인 팝업 처리
                self._handle_login_popup()
                
                return True
            else:
                # URL에서 페이지 번호 추출 및 수정
                current_url = self.driver.current_url
                parsed_url = urlparse(current_url)
                query_params = parse_qs(parsed_url.query)
                
                # 현재 페이지 번호 확인
                current_page = 1
                if 'start' in query_params:
                    current_page = int(int(query_params['start'][0]) / 25) + 1
                
                # 다음 페이지 URL 생성
                next_page = current_page + 1
                next_start = (next_page - 1) * 25
                
                if 'start' in query_params:
                    query_params['start'] = [str(next_start)]
                else:
                    query_params['start'] = [str(next_start)]
                
                # URL 재구성
                query_string = "&".join([f"{k}={v[0]}" for k, v in query_params.items()])
                next_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{query_string}"
                
                # 다음 페이지로 이동
                self.driver.get(next_url)
                self._wait_for_page_load(timeout=15)
                
                # 로그인 팝업 처리
                self._handle_login_popup()
                
                return True
        
        except Exception as e:
            print(f"다음 페이지 이동 오류: {e}")
        
        return False
    
    def _wait_for_page_load(self, timeout=10):
        """페이지 로딩 대기
        
        Args:
            timeout (int, optional): 타임아웃 시간(초)
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            time.sleep(random.uniform(1, 2))
        except TimeoutException:
            print(f"페이지 로딩 시간 초과 ({timeout}초)")
    
    def _download_image(self, image_url, base_name):
        """이미지 다운로드
        
        Args:
            image_url (str): 이미지 URL
            base_name (str): 저장할 이미지 기본 이름
            
        Returns:
            str: 저장된 이미지 경로 또는 빈 문자열
        """
        if not image_url:
            return ""
        
        try:
            # 이미지 확장자 추출
            ext = image_url.split('.')[-1]
            if '?' in ext:
                ext = ext.split('?')[0]
            
            # 확장자가 없거나 비정상적인 경우 기본값 사용
            if not ext or len(ext) > 5:
                ext = "jpg"
            
            # 파일명 정제
            base_name = self._clean_filename(base_name)
            
            # 저장 경로 생성
            file_name = f"{base_name}.{ext}"
            file_path = os.path.join(self.output_dir, "images", file_name)
            
            # 이미지 다운로드
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Referer": "https://www.linkedin.com/"
            }
            
            response = requests.get(image_url, headers=headers, stream=True, timeout=10)
            if response.status_code == 200:
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                
                print(f"이미지 다운로드 완료: {file_name}")
                return file_path
            else:
                print(f"이미지 다운로드 실패 (상태 코드: {response.status_code}): {image_url}")
                return ""
        except Exception as e:
            print(f"이미지 다운로드 오류: {e}")
            return ""
    
    def _clean_filename(self, filename):
        """파일명에 사용할 수 없는 문자 제거
        
        Args:
            filename (str): 원본 파일명
            
        Returns:
            str: 정제된 파일명
        """
        # 파일명에 사용할 수 없는 문자 제거
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # 공백을 언더스코어로 변경
        filename = filename.replace(' ', '_')
        
        return filename
    
    def _save_job_listings(self, job_listings, keyword):
        """채용 공고 목록을 JSON 파일로 저장
        
        Args:
            job_listings (list): 저장할 채용 공고 목록
            keyword (str): 검색 키워드
        """
        if not job_listings:
            print("저장할 채용 공고가 없습니다.")
            return
        
        # 파일명에 사용할 키워드 정제
        keyword_clean = self._clean_filename(keyword)
        
        # 저장 경로 생성
        file_path = os.path.join(self.output_dir, f"{keyword_clean}_job_listings.json")
        
        # JSON 파일로 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(job_listings, f, ensure_ascii=False, indent=2)
        
        print(f"채용 공고 목록이 저장되었습니다: {file_path}")
        
        # 각 채용 공고 개별 저장
        for job in job_listings:
            job_title = job.get('title', '제목_없음')
            company_name = job.get('company_name', '회사명_없음')
            
            # 파일명 생성
            file_name = f"{self._clean_filename(company_name)}_{self._clean_filename(job_title)}.json"
            job_file_path = os.path.join(self.output_dir, "jobs", file_name)
            
            # JSON 파일로 저장
            with open(job_file_path, 'w', encoding='utf-8') as f:
                json.dump(job, f, ensure_ascii=False, indent=2)
    
    def _save_company_info(self, company_info):
        """회사 정보를 JSON 파일로 저장
        
        Args:
            company_info (dict): 저장할 회사 정보
        """
        if not company_info or not company_info.get('name'):
            print("저장할 회사 정보가 없습니다.")
            return
        
        # 파일명에 사용할 회사명 정제
        company_name = self._clean_filename(company_info['name'])
        
        # 저장 경로 생성
        file_path = os.path.join(self.output_dir, "companies", f"{company_name}.json")
        
        # JSON 파일로 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(company_info, f, ensure_ascii=False, indent=2)
        
        print(f"회사 정보가 저장되었습니다: {file_path}")
    
    def validate_data(self, job_url):
        """수집된 데이터 검증
        
        Args:
            job_url (str): 검증할 채용 공고 URL
            
        Returns:
            dict: 검증 결과
        """
        print(f"채용 공고 데이터 검증 중: {job_url}")
        
        try:
            # 채용 공고 페이지 접속
            self.driver.get(job_url)
            
            # 페이지 로딩 대기
            self._wait_for_page_load(timeout=15)
            
            # 로그인 팝업 처리
            self._handle_login_popup()
            
            # 웹사이트에서 직접 추출한 데이터
            web_data = self._extract_job_info()
            
            if not web_data:
                print("웹사이트에서 데이터를 추출할 수 없습니다.")
                return {'success': False, 'message': '웹사이트에서 데이터를 추출할 수 없습니다.'}
            
            # 파일명 생성
            job_title = web_data.get('title', '제목_없음')
            company_name = web_data.get('company_name', '회사명_없음')
            file_name = f"{self._clean_filename(company_name)}_{self._clean_filename(job_title)}.json"
            
            # 저장된 파일 경로
            file_path = os.path.join(self.output_dir, "jobs", file_name)
            
            # 파일 존재 여부 확인
            if not os.path.exists(file_path):
                # 유사한 파일 찾기
                job_files = os.listdir(os.path.join(self.output_dir, "jobs"))
                similar_files = [f for f in job_files if self._clean_filename(company_name) in f]
                
                if similar_files:
                    file_path = os.path.join(self.output_dir, "jobs", similar_files[0])
                    print(f"유사한 파일을 찾았습니다: {similar_files[0]}")
                else:
                    print(f"저장된 데이터 파일을 찾을 수 없습니다.")
                    return {'success': False, 'message': '저장된 데이터 파일을 찾을 수 없습니다.'}
            
            # 저장된 데이터 로드
            with open(file_path, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
            
            # 필수 필드 비교
            validation_results = {
                "title": {
                    "saved": saved_data.get('title', ''),
                    "web": web_data.get('title', ''),
                    "match": saved_data.get('title', '') == web_data.get('title', '')
                },
                "company_name": {
                    "saved": saved_data.get('company_name', ''),
                    "web": web_data.get('company_name', ''),
                    "match": saved_data.get('company_name', '') == web_data.get('company_name', '')
                },
                "location": {
                    "saved": saved_data.get('location', ''),
                    "web": web_data.get('location', ''),
                    "match": saved_data.get('location', '') == web_data.get('location', '')
                }
            }
            
            # 채용 공고 설명 비교 (길이만)
            saved_desc_len = len(saved_data.get('job_description', ''))
            web_desc_len = len(web_data.get('job_description', ''))
            desc_match = abs(saved_desc_len - web_desc_len) < 100  # 100자 이내 차이는 허용
            
            validation_results["job_description"] = {
                "saved": f"{saved_desc_len} 자",
                "web": f"{web_desc_len} 자",
                "match": desc_match
            }
            
            # 전체 일치 여부 계산
            all_match = all(item['match'] for item in validation_results.values())
            
            validation_summary = {
                'success': True,
                'all_match': all_match,
                'job_url': job_url,
                'validation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'results': validation_results
            }
            
            # 검증 결과 저장
            validation_file = os.path.join(self.output_dir, f"{self._clean_filename(company_name)}_{self._clean_filename(job_title)}_validation.json")
            with open(validation_file, 'w', encoding='utf-8') as f:
                json.dump(validation_summary, f, ensure_ascii=False, indent=2)
            
            print(f"데이터 검증 결과가 저장되었습니다: {validation_file}")
            print(f"검증 결과: {'모든 데이터 일치' if all_match else '일부 데이터 불일치'}")
            
            return validation_summary
        
        except Exception as e:
            print(f"데이터 검증 오류: {e}")
            return {'success': False, 'message': f'데이터 검증 중 오류 발생: {e}'}
