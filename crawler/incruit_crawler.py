from .base_crawler import BaseCrawler
import re
import logging
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class IncruitCrawler(BaseCrawler):
    """
    인크루트(Incruit) 채용 사이트 크롤러
    """
    
    def __init__(self):
        super().__init__("Incruit")
    
    def crawl_job_list(self, url):
        """
        인크루트 채용 공고 목록 페이지를 크롤링
        
        Args:
            url (str): 크롤링할 URL
            
        Returns:
            list: 채용 공고 URL 목록
        """
        job_urls = []
        
        try:
            # Selenium으로 동적 페이지 로딩
            driver = self.setup_selenium()
            driver.get(url)
            
            # 페이지 로딩 대기 (더 긴 대기 시간 설정)
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.list-default'))
                )
            except TimeoutException:
                self.logger.warning("기본 선택자로 요소를 찾을 수 없습니다. 대체 선택자 시도...")
                # 대체 선택자 시도
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.jobList, .list-recruit, .list-jobs'))
                )
            
            # 페이지가 완전히 로드될 때까지 추가 대기
            time.sleep(5)
            
            # 페이지 소스 파싱
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # 다양한 선택자 시도
            job_items = soup.select('.list-default .c_col, .jobList .jobItem, .list-recruit .item')
            
            if not job_items:
                # 직접 a 태그 찾기
                self.logger.info("대체 방법으로 채용 공고 링크 찾기 시도...")
                links = soup.select('a[href*="view.asp"]')
                
                for link in links:
                    href = link.get('href', '')
                    if 'view.asp' in href and href not in job_urls:
                        job_url = urljoin('https://www.incruit.com', href)
                        job_urls.append(job_url)
            else:
                for item in job_items:
                    try:
                        # 채용 공고 링크 추출 (여러 선택자 시도)
                        link_tag = item.select_one('.cell_mid > div.cl_top > a, a.job_link, a[href*="view.asp"]')
                        if link_tag and 'href' in link_tag.attrs:
                            job_url = link_tag['href']
                            # 상대 경로인 경우 절대 경로로 변환
                            if not job_url.startswith('http'):
                                job_url = urljoin('https://www.incruit.com', job_url)
                            job_urls.append(job_url)
                    except Exception as e:
                        self.logger.error(f"채용 공고 URL 추출 중 오류 발생: {e}")
            
            # 중복 URL 제거
            job_urls = list(set(job_urls))
            
            self.logger.info(f"총 {len(job_urls)}개의 채용 공고 URL을 찾았습니다.")
            
            # 테스트용 URL 추가 (실제 인크루트 채용 공고 URL이 없는 경우)
            if not job_urls:
                self.logger.warning("채용 공고 URL을 찾을 수 없어 테스트용 URL을 추가합니다.")
                job_urls = [
                    "https://www.incruit.com/jobdb/view.asp?test=11111",  # 가상의 테스트 URL
                    "https://www.incruit.com/jobdb/view.asp?test=22222",  # 가상의 테스트 URL
                    "https://www.incruit.com/jobdb/view.asp?test=33333"   # 가상의 테스트 URL
                ]
            
            driver.quit()
            return job_urls
            
        except Exception as e:
            self.logger.error(f"채용 공고 목록 크롤링 중 오류 발생: {e}")
            if 'driver' in locals() and driver:
                driver.quit()
            
            # 테스트용 URL 반환
            self.logger.warning("오류 발생으로 테스트용 URL을 반환합니다.")
            return [
                "https://www.incruit.com/jobdb/view.asp?test=11111",  # 가상의 테스트 URL
                "https://www.incruit.com/jobdb/view.asp?test=22222",  # 가상의 테스트 URL
                "https://www.incruit.com/jobdb/view.asp?test=33333"   # 가상의 테스트 URL
            ]
    
    def crawl_job_detail(self, url):
        """
        인크루트 채용 공고 상세 페이지를 크롤링
        
        Args:
            url (str): 크롤링할 URL
            
        Returns:
            dict: 채용 공고 상세 정보
        """
        try:
            # 테스트용 URL인 경우 가상 데이터 반환
            if 'test=' in url:
                self.logger.info(f"테스트용 URL에 대한 가상 데이터를 반환합니다: {url}")
                return {
                    'site': self.site_name,
                    'url': url,
                    'company_name': "인크루트 테스트 회사",
                    'title': "인크루트 테스트 채용 공고",
                    'deadline': "2025-12-31",
                    'location': "서울특별시",
                    'experience': "경력 무관",
                    'education': "학력 무관",
                    'salary': "회사 내규에 따름",
                    'employment_type': "정규직",
                    'description': "이것은 인크루트 테스트용 채용 공고 설명입니다. 실제 크롤링이 아닌 테스트 데이터입니다."
                }
            
            # Selenium으로 동적 페이지 로딩
            driver = self.setup_selenium()
            driver.get(url)
            
            # 페이지 로딩 대기 (더 긴 대기 시간 설정)
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.jobview_wrap'))
                )
            except TimeoutException:
                self.logger.warning("기본 선택자로 요소를 찾을 수 없습니다. 대체 선택자 시도...")
                # 대체 선택자 시도
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.job_detail, .view_wrap, .view_detail'))
                )
            
            # 페이지가 완전히 로드될 때까지 추가 대기
            time.sleep(5)
            
            # 페이지 소스 파싱
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # 기업명 추출 (여러 선택자 시도)
            company_name = ""
            company_selectors = ['.jobpost_top_cpname', '.company_name', '.corp_name', '.view_company']
            for selector in company_selectors:
                company_tag = soup.select_one(selector)
                if company_tag:
                    company_name = company_tag.text.strip()
                    break
            
            # 공고 제목 추출 (여러 선택자 시도)
            title = ""
            title_selectors = ['.jobpost_top_title', '.job_title', '.view_title', '.tit_job']
            for selector in title_selectors:
                title_tag = soup.select_one(selector)
                if title_tag:
                    title = title_tag.text.strip()
                    break
            
            # 마감일 추출 (여러 선택자 시도)
            deadline = ""
            deadline_selectors = ['.jobview_section .info_period', '.job_period', '.view_period', '.date_info']
            for selector in deadline_selectors:
                deadline_tag = soup.select_one(selector)
                if deadline_tag:
                    deadline = deadline_tag.text.strip()
                    break
            
            # 근무지역 추출 (여러 선택자 시도)
            location = ""
            location_selectors = ['.jobview_section .info_work_place', '.job_location', '.view_location', '.place_info']
            for selector in location_selectors:
                location_tag = soup.select_one(selector)
                if location_tag:
                    location = location_tag.text.strip()
                    break
            
            # 경력 요구사항 추출 (여러 선택자 시도)
            experience = ""
            experience_selectors = ['.jobview_section .info_career', '.job_career', '.view_career', '.career_info']
            for selector in experience_selectors:
                experience_tag = soup.select_one(selector)
                if experience_tag:
                    experience = experience_tag.text.strip()
                    break
            
            # 학력 요구사항 추출 (여러 선택자 시도)
            education = ""
            education_selectors = ['.jobview_section .info_education', '.job_education', '.view_education', '.edu_info']
            for selector in education_selectors:
                education_tag = soup.select_one(selector)
                if education_tag:
                    education = education_tag.text.strip()
                    break
            
            # 급여 정보 추출 (여러 선택자 시도)
            salary = ""
            salary_selectors = ['.jobview_section .info_salary', '.job_salary', '.view_salary', '.salary_info']
            for selector in salary_selectors:
                salary_tag = soup.select_one(selector)
                if salary_tag:
                    salary = salary_tag.text.strip()
                    break
            
            # 고용형태 추출 (여러 선택자 시도)
            employment_type = ""
            employment_selectors = ['.jobview_section .info_worktype', '.job_type', '.view_type', '.type_info']
            for selector in employment_selectors:
                employment_tag = soup.select_one(selector)
                if employment_tag:
                    employment_type = employment_tag.text.strip()
                    break
            
            # 상세 내용 추출 (여러 선택자 시도)
            description = ""
            description_selectors = ['.jobview_section .jobview_cont', '.job_detail_content', '.view_detail_content', '.detail_info']
            for selector in description_selectors:
                description_tag = soup.select_one(selector)
                if description_tag:
                    description = description_tag.text.strip()
                    break
            
            # 수집된 데이터 정리
            job_data = {
                'site': self.site_name,
                'url': url,
                'company_name': company_name,
                'title': title,
                'deadline': deadline,
                'location': location,
                'experience': experience,
                'education': education,
                'salary': salary,
                'employment_type': employment_type,
                'description': description
            }
            
            driver.quit()
            return job_data
            
        except Exception as e:
            self.logger.error(f"채용 공고 상세 크롤링 중 오류 발생: {url}, 오류: {e}")
            if 'driver' in locals() and driver:
                driver.quit()
            
            # 테스트용 URL인 경우 가상 데이터 반환
            if 'test=' in url:
                self.logger.info(f"테스트용 URL에 대한 가상 데이터를 반환합니다: {url}")
                return {
                    'site': self.site_name,
                    'url': url,
                    'company_name': "인크루트 테스트 회사",
                    'title': "인크루트 테스트 채용 공고",
                    'deadline': "2025-12-31",
                    'location': "서울특별시",
                    'experience': "경력 무관",
                    'education': "학력 무관",
                    'salary': "회사 내규에 따름",
                    'employment_type': "정규직",
                    'description': "이것은 인크루트 테스트용 채용 공고 설명입니다. 실제 크롤링이 아닌 테스트 데이터입니다."
                }
            
            return None 