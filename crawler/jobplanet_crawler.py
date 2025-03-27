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

class JobPlanetCrawler(BaseCrawler):
    """
    잡플래닛(JobPlanet) 채용 사이트 크롤러
    """
    
    def __init__(self):
        super().__init__("JobPlanet")
    
    def crawl_job_list(self, url):
        """
        잡플래닛 채용 공고 목록 페이지를 크롤링
        
        Args:
            url (str): 크롤링할 URL
            
        Returns:
            list: 채용 공고 URL 목록
        """
        job_urls = []
        
        try:
            # URL이 직접 채용공고 URL인 경우
            if '/job/search/job/' in url:
                self.logger.info("직접 채용공고 URL이 제공되었습니다.")
                return [url]
            
            # Selenium으로 동적 페이지 로딩
            driver = self.setup_selenium()
            driver.get(url)
            
            # 페이지 로딩 대기
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.recruitment-item'))
                )
            except TimeoutException:
                self.logger.warning("기본 선택자로 요소를 찾을 수 없습니다. 대체 선택자 시도...")
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.job_list, .recruit_list'))
                )
            
            # 페이지가 완전히 로드될 때까지 추가 대기
            time.sleep(5)
            
            # 페이지 소스 파싱
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # 채용 공고 링크 추출
            job_items = soup.select('.recruitment-item, .job_item, .recruit_list_item')
            
            if not job_items:
                # 직접 a 태그 찾기
                self.logger.info("대체 방법으로 채용 공고 링크 찾기 시도...")
                links = soup.select('a[href*="/job/search/job/"]')
                
                for link in links:
                    href = link.get('href', '')
                    if '/job/search/job/' in href and href not in job_urls:
                        job_url = urljoin('https://www.jobplanet.co.kr', href)
                        job_urls.append(job_url)
            else:
                for item in job_items:
                    try:
                        link_tag = item.select_one('a[href*="/job/search/job/"]')
                        if link_tag and 'href' in link_tag.attrs:
                            job_url = link_tag['href']
                            if not job_url.startswith('http'):
                                job_url = urljoin('https://www.jobplanet.co.kr', job_url)
                            job_urls.append(job_url)
                    except Exception as e:
                        self.logger.error(f"채용 공고 URL 추출 중 오류 발생: {e}")
            
            # 중복 URL 제거
            job_urls = list(set(job_urls))
            
            self.logger.info(f"총 {len(job_urls)}개의 채용 공고 URL을 찾았습니다.")
            
            driver.quit()
            return job_urls
            
        except Exception as e:
            self.logger.error(f"채용 공고 목록 크롤링 중 오류 발생: {e}")
            if 'driver' in locals() and driver:
                driver.quit()
            return []
    
    def crawl_job_detail(self, url):
        """
        잡플래닛 채용 공고 상세 페이지를 크롤링
        
        Args:
            url (str): 크롤링할 URL
            
        Returns:
            dict: 채용 공고 상세 정보
        """
        try:
            # Selenium으로 동적 페이지 로딩
            driver = self.setup_selenium()
            driver.get(url)
            
            # 페이지 로딩 대기
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.recruitment-detail'))
                )
            except TimeoutException:
                self.logger.warning("기본 선택자로 요소를 찾을 수 없습니다. 대체 선택자 시도...")
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.job_detail, .view_wrap'))
                )
            
            # 페이지가 완전히 로드될 때까지 추가 대기
            time.sleep(5)
            
            # 페이지 소스 파싱
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # 기업명 추출
            company_name = ""
            company_tag = soup.select_one('.company-name, .company_name, .view_company')
            if company_tag:
                company_name = company_tag.text.strip()
            
            # 공고 제목 추출
            title = ""
            title_tag = soup.select_one('.recruitment-title, .job_title, .view_title')
            if title_tag:
                title = title_tag.text.strip()
            
            # 마감일 추출
            deadline = ""
            deadline_tag = soup.select_one('.recruitment-info .info_period, .job_period, .view_period')
            if deadline_tag:
                deadline = deadline_tag.text.strip()
            
            # 근무지역 추출
            location = ""
            location_tag = soup.select_one('.recruitment-info .info_work_place, .job_location, .view_location')
            if location_tag:
                location = location_tag.text.strip()
            
            # 경력 요구사항 추출
            experience = ""
            experience_tag = soup.select_one('.recruitment-info .info_career, .job_career, .view_career')
            if experience_tag:
                experience = experience_tag.text.strip()
            
            # 학력 요구사항 추출
            education = ""
            education_tag = soup.select_one('.recruitment-info .info_education, .job_education, .view_education')
            if education_tag:
                education = education_tag.text.strip()
            
            # 고용형태 추출
            employment_type = ""
            employment_tag = soup.select_one('.recruitment-info .info_worktype, .job_type, .view_type')
            if employment_tag:
                employment_type = employment_tag.text.strip()
            
            # 상세 내용 추출
            description = ""
            description_tag = soup.select_one('.recruitment-detail-content, .job_detail_content, .view_detail_content')
            if description_tag:
                description = description_tag.text.strip()
            
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
                'employment_type': employment_type,
                'description': description
            }
            
            driver.quit()
            return job_data
            
        except Exception as e:
            self.logger.error(f"채용 공고 상세 크롤링 중 오류 발생: {url}, 오류: {e}")
            if 'driver' in locals() and driver:
                driver.quit()
            return None 