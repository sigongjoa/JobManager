#!/usr/bin/env python3
"""
최종 사람인 크롤러 - 근무조건 추출 개선
"""

import os
import time
import logging
import json
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import unittest

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 데이터 저장 경로 설정
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

class FinalSaraminCrawler:
    """최종 사람인 크롤러 클래스"""
    
    def __init__(self):
        self.site_name = "Saramin"
        self.data = []
        self.max_retries = 3
        self.wait_time = 30
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.jobs = []
        
    def setup_driver(self):
        """Selenium 웹드라이버 설정"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        return driver

    def extract_text_safely(self, driver, selector, multiple=False):
        """안전하게 텍스트 추출"""
        try:
            if multiple:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                return [element.text.strip() for element in elements if element.text.strip()]
            else:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                return element.text.strip()
        except Exception as e:
            return [] if multiple else ""
    
    def extract_with_multiple_selectors(self, driver, selectors, multiple=False):
        """여러 선택자를 시도하여 텍스트 추출"""
        for selector in selectors:
            try:
                result = self.extract_text_safely(driver, selector, multiple)
                if result:
                    logger.info(f"선택자 '{selector}'로 데이터 추출 성공")
                    return result
            except Exception as e:
                continue
        return [] if multiple else ""
    
    def extract_table_data(self, driver, table_selector):
        """테이블 데이터 추출"""
        try:
            tables = driver.find_elements(By.CSS_SELECTOR, table_selector)
            if not tables:
                return {}
            
            table_data = {}
            for table in tables:
                rows = table.find_elements(By.TAG_NAME, 'tr')
                for row in rows:
                    try:
                        th_elements = row.find_elements(By.TAG_NAME, 'th')
                        td_elements = row.find_elements(By.TAG_NAME, 'td')
                        
                        if th_elements and td_elements:
                            key = th_elements[0].text.strip()
                            value = td_elements[0].text.strip()
                            if key and value:
                                table_data[key] = value
                    except Exception as e:
                        continue
            
            return table_data
        except Exception as e:
            logger.warning(f"테이블 데이터 추출 중 오류 발생: {e}")
            return {}
    
    def extract_job_conditions(self, driver):
        """근무조건 추출 - 개선된 버전"""
        conditions = {}
        
        # 1. 근무조건 섹션 찾기 (가장 정확한 방법)
        try:
            condition_sections = driver.find_elements(By.CSS_SELECTOR, '.jv_cont')
            for section in condition_sections:
                try:
                    title_element = section.find_element(By.CSS_SELECTOR, '.tit_job_condition')
                    title = title_element.text.strip()
                    if '근무조건' in title:
                        logger.info(f"근무조건 섹션 찾음: {title}")
                        items = section.find_elements(By.CSS_SELECTOR, '.cont .item')
                        for item in items:
                            try:
                                dt = item.find_element(By.CSS_SELECTOR, 'dt').text.strip()
                                dd = item.find_element(By.CSS_SELECTOR, 'dd').text.strip()
                                if dt and dd:
                                    conditions[dt] = dd
                                    logger.info(f"근무조건 항목: {dt} - {dd}")
                            except Exception as e:
                                continue
                except Exception as e:
                    continue
        except Exception as e:
            logger.warning(f"근무조건 섹션 찾기 중 오류 발생: {e}")
        
        # 2. 상세 정보 테이블 찾기
        try:
            info_tables = driver.find_elements(By.CSS_SELECTOR, '.jv_summary .jv_summary_info')
            for table in info_tables:
                try:
                    rows = table.find_elements(By.CSS_SELECTOR, 'div.row')
                    for row in rows:
                        try:
                            dt = row.find_element(By.CSS_SELECTOR, 'div.col.head').text.strip()
                            dd = row.find_element(By.CSS_SELECTOR, 'div.col.body').text.strip()
                            if dt and dd:
                                conditions[dt] = dd
                                logger.info(f"상세 정보 항목: {dt} - {dd}")
                        except Exception as e:
                            continue
                except Exception as e:
                    continue
        except Exception as e:
            logger.warning(f"상세 정보 테이블 찾기 중 오류 발생: {e}")
        
        # 3. 특정 필드 직접 찾기
        field_selectors = {
            '경력': ['.experience', '.career', '.info_exp', '#job-position-job-experience-text'],
            '학력': ['.education', '.info_edu', '#job-position-job-education-text'],
            '근무형태': ['.employment_type', '.info_emp_type', '#job-position-job-type-text'],
            '근무지역': ['.location', '.info_loc', '#job-position-job-location-text', '.work_place'],
            '근무시간': ['.work_time', '.info_work_time', '#job-position-job-worktime-text'],
            '급여': ['.salary', '.info_salary', '#job-position-job-salary-text']
        }
        
        for field, selectors in field_selectors.items():
            if field not in conditions:  # 이미 찾은 필드는 건너뛰기
                value = self.extract_with_multiple_selectors(driver, selectors)
                if value:
                    conditions[field] = value
                    logger.info(f"직접 찾은 {field}: {value}")
        
        # 4. 페이지 소스에서 정규식으로 찾기
        if not conditions:
            try:
                page_source = driver.page_source
                
                # 경력 패턴
                career_patterns = [
                    r'경력\s*[:：]\s*([^<\n]+)',
                    r'경력</dt>\s*<dd[^>]*>([^<]+)',
                    r'경력\s*</th>\s*<td[^>]*>([^<]+)'
                ]
                
                for pattern in career_patterns:
                    match = re.search(pattern, page_source)
                    if match:
                        conditions['경력'] = match.group(1).strip()
                        logger.info(f"정규식으로 찾은 경력: {conditions['경력']}")
                        break
                
                # 학력 패턴
                education_patterns = [
                    r'학력\s*[:：]\s*([^<\n]+)',
                    r'학력</dt>\s*<dd[^>]*>([^<]+)',
                    r'학력\s*</th>\s*<td[^>]*>([^<]+)'
                ]
                
                for pattern in education_patterns:
                    match = re.search(pattern, page_source)
                    if match:
                        conditions['학력'] = match.group(1).strip()
                        logger.info(f"정규식으로 찾은 학력: {conditions['학력']}")
                        break
                
                # 근무지역 패턴
                location_patterns = [
                    r'근무지역\s*[:：]\s*([^<\n]+)',
                    r'근무지</dt>\s*<dd[^>]*>([^<]+)',
                    r'근무지\s*</th>\s*<td[^>]*>([^<]+)',
                    r'지역\s*[:：]\s*([^<\n]+)'
                ]
                
                for pattern in location_patterns:
                    match = re.search(pattern, page_source)
                    if match:
                        conditions['근무지역'] = match.group(1).strip()
                        logger.info(f"정규식으로 찾은 근무지역: {conditions['근무지역']}")
                        break
                
                # 고용형태 패턴
                employment_patterns = [
                    r'고용형태\s*[:：]\s*([^<\n]+)',
                    r'고용형태</dt>\s*<dd[^>]*>([^<]+)',
                    r'고용형태\s*</th>\s*<td[^>]*>([^<]+)',
                    r'근무형태\s*[:：]\s*([^<\n]+)'
                ]
                
                for pattern in employment_patterns:
                    match = re.search(pattern, page_source)
                    if match:
                        conditions['고용형태'] = match.group(1).strip()
                        logger.info(f"정규식으로 찾은 고용형태: {conditions['고용형태']}")
                        break
                
                # 급여 패턴
                salary_patterns = [
                    r'급여\s*[:：]\s*([^<\n]+)',
                    r'급여</dt>\s*<dd[^>]*>([^<]+)',
                    r'급여\s*</th>\s*<td[^>]*>([^<]+)',
                    r'연봉\s*[:：]\s*([^<\n]+)'
                ]
                
                for pattern in salary_patterns:
                    match = re.search(pattern, page_source)
                    if match:
                        conditions['급여'] = match.group(1).strip()
                        logger.info(f"정규식으로 찾은 급여: {conditions['급여']}")
                        break
            except Exception as e:
                logger.warning(f"정규식 검색 중 오류 발생: {e}")
        
        # 5. 이미지 분석 (사용자가 제공한 이미지 참고)
        # 이미지에서 본 구조를 기반으로 직접 추출
        try:
            # 경력
            career_elements = driver.find_elements(By.CSS_SELECTOR, '.jv_summary .jv_summary_info .row')
            for element in career_elements:
                try:
                    head = element.find_element(By.CSS_SELECTOR, '.col.head').text.strip()
                    if '경력' in head:
                        body = element.find_element(By.CSS_SELECTOR, '.col.body').text.strip()
                        conditions['경력'] = body
                        logger.info(f"이미지 구조 기반으로 찾은 경력: {body}")
                except Exception as e:
                    continue
            
            # 학력
            education_elements = driver.find_elements(By.CSS_SELECTOR, '.jv_summary .jv_summary_info .row')
            for element in education_elements:
                try:
                    head = element.find_element(By.CSS_SELECTOR, '.col.head').text.strip()
                    if '학력' in head:
                        body = element.find_element(By.CSS_SELECTOR, '.col.body').text.strip()
                        conditions['학력'] = body
                        logger.info(f"이미지 구조 기반으로 찾은 학력: {body}")
                except Exception as e:
                    continue
            
            # 근무형태
            employment_elements = driver.find_elements(By.CSS_SELECTOR, '.jv_summary .jv_summary_info .row')
            for element in employment_elements:
                try:
                    head = element.find_element(By.CSS_SELECTOR, '.col.head').text.strip()
                    if '근무형태' in head:
                        body = element.find_element(By.CSS_SELECTOR, '.col.body').text.strip()
                        conditions['근무형태'] = body
                        logger.info(f"이미지 구조 기반으로 찾은 근무형태: {body}")
                except Exception as e:
                    continue
            
            # 근무지역
            location_elements = driver.find_elements(By.CSS_SELECTOR, '.jv_summary .jv_summary_info .row')
            for element in location_elements:
                try:
                    head = element.find_element(By.CSS_SELECTOR, '.col.head').text.strip()
                    if '근무지역' in head:
                        body = element.find_element(By.CSS_SELECTOR, '.col.body').text.strip()
                        conditions['근무지역'] = body
                        logger.info(f"이미지 구조 기반으로 찾은 근무지역: {body}")
                except Exception as e:
                    continue
        except Exception as e:
            logger.warning(f"이미지 구조 기반 추출 중 오류 발생: {e}")
        
        return conditions
    
    def extract_welfare_benefits(self, driver):
        """복리후생 추출"""
        try:
            welfare_sections = driver.find_elements(By.CSS_SELECTOR, '.jv_cont')
            for section in welfare_sections:
                try:
                    title = section.find_element(By.CSS_SELECTOR, '.tit_job_condition').text.strip()
                    if '복리후생' in title:
                        content = section.find_element(By.CSS_SELECTOR, '.cont').text.strip()
                        return content
                except Exception as e:
                    continue
            
            # 다른 선택자 시도
            welfare_selectors = [
                '.welfare',
                '.benefits',
                '#job-welfare-text',
                '.jv_benefit'
            ]
            
            welfare = self.extract_with_multiple_selectors(driver, welfare_selectors)
            return welfare
        except Exception as e:
            logger.warning(f"복리후생 추출 중 오류 발생: {e}")
            return ""
    
    def extract_application_period(self, driver):
        """접수기간 및 방법 추출"""
        application_info = {}
        
        try:
            # 접수기간 및 방법 섹션 찾기
            application_sections = driver.find_elements(By.CSS_SELECTOR, '.jv_cont')
            for section in application_sections:
                try:
                    title = section.find_element(By.CSS_SELECTOR, '.tit_job_condition').text.strip()
                    if '접수기간' in title or '지원방법' in title:
                        items = section.find_elements(By.CSS_SELECTOR, '.cont .item')
                        for item in items:
                            try:
                                dt = item.find_element(By.CSS_SELECTOR, 'dt').text.strip()
                                dd = item.find_element(By.CSS_SELECTOR, 'dd').text.strip()
                                if dt and dd:
                                    application_info[dt] = dd
                            except Exception as e:
                                continue
                except Exception as e:
                    continue
            
            # 직접 선택자 시도
            deadline_selectors = [
                '.deadline',
                '.apply_deadline',
                '#job-application-deadline-text',
                '.info_period'
            ]
            
            deadline = self.extract_with_multiple_selectors(driver, deadline_selectors)
            if deadline:
                application_info['접수기간'] = deadline
            
            method_selectors = [
                '.apply_method',
                '.application_method',
                '#job-application-method-text',
                '.info_apply'
            ]
            
            method = self.extract_with_multiple_selectors(driver, method_selectors)
            if method:
                application_info['지원방법'] = method
        except Exception as e:
            logger.warning(f"접수기간 및 방법 추출 중 오류 발생: {e}")
        
        return application_info
    
    def extract_company_info(self, driver):
        """기업정보 추출"""
        company_info = {}
        
        try:
            # 기업정보 섹션 찾기
            company_sections = driver.find_elements(By.CSS_SELECTOR, '.jv_cont')
            for section in company_sections:
                try:
                    title = section.find_element(By.CSS_SELECTOR, '.tit_job_condition').text.strip()
                    if '기업정보' in title:
                        items = section.find_elements(By.CSS_SELECTOR, '.cont .item')
                        for item in items:
                            try:
                                dt = item.find_element(By.CSS_SELECTOR, 'dt').text.strip()
                                dd = item.find_element(By.CSS_SELECTOR, 'dd').text.strip()
                                if dt and dd:
                                    company_info[dt] = dd
                            except Exception as e:
                                continue
                except Exception as e:
                    continue
            
            # 직접 선택자 시도
            company_name_selectors = [
                '.company_name',
                '.corp_name',
                '#company-name-text',
                '.info_company'
            ]
            
            company_name = self.extract_with_multiple_selectors(driver, company_name_selectors)
            if company_name:
                company_info['회사명'] = company_name
            
            company_type_selectors = [
                '.company_type',
                '.corp_type',
                '#company-type-text',
                '.info_company_type'
            ]
            
            company_type = self.extract_with_multiple_selectors(driver, company_type_selectors)
            if company_type:
                company_info['기업형태'] = company_type
            
            company_size_selectors = [
                '.company_size',
                '.corp_size',
                '#company-size-text',
                '.info_company_size'
            ]
            
            company_size = self.extract_with_multiple_selectors(driver, company_size_selectors)
            if company_size:
                company_info['기업규모'] = company_size
            
            company_industry_selectors = [
                '.company_industry',
                '.corp_industry',
                '#company-industry-text',
                '.info_company_industry'
            ]
            
            company_industry = self.extract_with_multiple_selectors(driver, company_industry_selectors)
            if company_industry:
                company_info['산업'] = company_industry
        except Exception as e:
            logger.warning(f"기업정보 추출 중 오류 발생: {e}")
        
        return company_info
    
    def crawl_job_detail(self, url):
        """채용 공고 상세 페이지에서 정보 추출"""
        logger.info(f"채용 공고 크롤링 중: {url}")
        
        for retry in range(self.max_retries):
            try:
                driver = self.setup_driver()
                driver.get(url)
                
                # 페이지 로딩 대기
                logger.info(f"페이지 로딩 대기 중... ({self.wait_time}초)")
                time.sleep(self.wait_time)
                
                # 기본 정보 초기화
                job_data = {
                    'site': self.site_name,
                    'url': url,
                    'company_name': '',
                    'title': '',
                    'deadline': '',
                    'location': '',
                    'experience': '',
                    'education': '',
                    'employment_type': '',
                    'salary': '',
                    'description': '',
                    'welfare_benefits': '',
                    'application_period': {},
                    'company_info': {}
                }
                
                # 회사명 추출
                company_name_selectors = [
                    '.company_name',
                    '.corp_name',
                    '.name',
                    'a[href*="company"]',
                    'a[href*="corp"]',
                    '.company',
                    '.corp',
                    '#company_name',
                    '#corp_name',
                    '.jv_header .company_name',
                    '.jv_company .name'
                ]
                
                company_name = self.extract_with_multiple_selectors(driver, company_name_selectors)
                if company_name:
                    job_data['company_name'] = company_name
                    logger.info(f"회사명: {company_name}")
                
                # 공고 제목 추출
                title_selectors = [
                    '.tit_job',
                    '.recruit_title',
                    '.job_tit',
                    'h1',
                    'h2',
                    '.title',
                    '.job_title',
                    '#job_title',
                    '.header_top_title',
                    '.jv_header .tit_job',
                    '.jv_title'
                ]
                
                title = self.extract_with_multiple_selectors(driver, title_selectors)
                if title:
                    job_data['title'] = title
                    logger.info(f"공고 제목: {title}")
                
                # 근무조건 추출 (개선된 버전)
                job_conditions = self.extract_job_conditions(driver)
                logger.info(f"근무조건: {job_conditions}")
                
                if '경력' in job_conditions:
                    job_data['experience'] = job_conditions['경력']
                
                if '학력' in job_conditions:
                    job_data['education'] = job_conditions['학력']
                
                if '근무형태' in job_conditions:
                    job_data['employment_type'] = job_conditions['근무형태']
                elif '고용형태' in job_conditions:
                    job_data['employment_type'] = job_conditions['고용형태']
                
                if '근무지역' in job_conditions:
                    job_data['location'] = job_conditions['근무지역']
                elif '근무지' in job_conditions:
                    job_data['location'] = job_conditions['근무지']
                
                if '급여' in job_conditions:
                    job_data['salary'] = job_conditions['급여']
                elif '연봉' in job_conditions:
                    job_data['salary'] = job_conditions['연봉']
                
                # 복리후생 추출
                welfare_benefits = self.extract_welfare_benefits(driver)
                if welfare_benefits:
                    job_data['welfare_benefits'] = welfare_benefits
                    logger.info(f"복리후생: {welfare_benefits[:100]}...")
                
                # 접수기간 및 방법 추출
                application_period = self.extract_application_period(driver)
                if application_period:
                    job_data['application_period'] = application_period
                    logger.info(f"접수기간 및 방법: {application_period}")
                    
                    if '접수기간' in application_period:
                        job_data['deadline'] = application_period['접수기간']
                
                # 기업정보 추출
                company_info = self.extract_company_info(driver)
                if company_info:
                    job_data['company_info'] = company_info
                    logger.info(f"기업정보: {company_info}")
                
                # 상세 내용 추출
                description_selectors = [
                    '#job_content',
                    '.job_detail_content',
                    '.recruit_detail',
                    '.job_detail',
                    '.detail_content',
                    '#jobDescriptionContent',
                    '.job_description',
                    '.description',
                    '.detail',
                    '.content',
                    '.jv_detail',
                    '.jv_cont .desc',
                    '.jv_cont .cont'
                ]
                
                description = self.extract_with_multiple_selectors(driver, description_selectors)
                if description:
                    job_data['description'] = description
                    logger.info(f"상세 내용 길이: {len(description)} 자")
                
                # 데이터 검증
                for key, value in job_data.items():
                    if key not in ['site', 'url', 'welfare_benefits', 'application_period', 'company_info', 'description'] and not value:
                        logger.warning(f"{key} 정보를 찾을 수 없습니다.")
                
                logger.info("채용 공고 크롤링 완료")
                driver.quit()
                return job_data
                
            except Exception as e:
                logger.error(f"채용 공고 상세 페이지 크롤링 중 오류 발생 (시도 {retry+1}/{self.max_retries}): {e}")
                if driver:
                    driver.quit()
                
                if retry < self.max_retries - 1:
                    logger.info(f"{5 * (retry + 1)}초 후 재시도합니다...")
                    time.sleep(5 * (retry + 1))
                else:
                    logger.error("최대 재시도 횟수를 초과했습니다.")
                    return None

if __name__ == "__main__":
    # 테스트 코드
    crawler = FinalSaraminCrawler()
    test_url = "https://www.saramin.co.kr/zf_user/jobs/relay/view?view_type=search&rec_idx=50312877&location=ts&searchword=python&searchType=search&paid_fl=n&search_uuid=2b35898e-9a07-4331-bc57-7fa286717407"
    result = crawler.crawl_job_detail(test_url)
    print(json.dumps(result, ensure_ascii=False, indent=2))
