import requests
from abc import ABC, abstractmethod
import time
import random
from bs4 import BeautifulSoup
import pandas as pd
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("crawler.log"),
        logging.StreamHandler()
    ]
)

class BaseCrawler(ABC):
    """
    취업 사이트 크롤러의 기본 클래스
    모든 사이트별 크롤러는 이 클래스를 상속받아 구현
    """
    
    def __init__(self, site_name):
        self.site_name = site_name
        self.logger = logging.getLogger(site_name)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.data = []
        
    def get_page(self, url, delay=1):
        """
        웹 페이지 내용을 가져오는 메서드
        
        Args:
            url (str): 크롤링할 URL
            delay (int): 요청 간 딜레이 (초)
            
        Returns:
            BeautifulSoup: 파싱된 HTML 내용
        """
        try:
            time.sleep(delay + random.random())  # 서버 부하 방지를 위한 랜덤 딜레이
            response = self.session.get(url)
            response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
            return BeautifulSoup(response.text, 'html.parser')
        except requests.exceptions.RequestException as e:
            self.logger.error(f"URL 요청 중 오류 발생: {url}, 오류: {e}")
            return None
    
    def setup_selenium(self, headless=True):
        """
        Selenium 웹드라이버 설정
        
        Args:
            headless (bool): 헤드리스 모드 사용 여부
            
        Returns:
            WebDriver: 설정된 웹드라이버 객체
        """
        options = Options()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    
    def get_page_with_selenium(self, url, delay=2):
        """
        Selenium을 사용하여 동적 웹 페이지 내용을 가져오는 메서드
        
        Args:
            url (str): 크롤링할 URL
            delay (int): 페이지 로딩 대기 시간 (초)
            
        Returns:
            tuple: (WebDriver, BeautifulSoup) 웹드라이버와 파싱된 HTML 내용
        """
        try:
            driver = self.setup_selenium()
            driver.get(url)
            time.sleep(delay)  # 페이지 로딩 대기
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            return driver, soup
        except Exception as e:
            self.logger.error(f"Selenium으로 URL 요청 중 오류 발생: {url}, 오류: {e}")
            if 'driver' in locals():
                driver.quit()
            return None, None
    
    def save_to_csv(self, filename=None):
        """
        수집된 데이터를 CSV 파일로 저장
        
        Args:
            filename (str): 저장할 파일명 (기본값: {site_name}_jobs.csv)
            
        Returns:
            str: 저장된 파일 경로
        """
        if not filename:
            filename = f"{self.site_name}_jobs.csv"
        
        if not self.data:
            self.logger.warning(f"저장할 데이터가 없습니다: {filename}")
            return None
        
        try:
            df = pd.DataFrame(self.data)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            self.logger.info(f"데이터가 성공적으로 저장되었습니다: {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"데이터 저장 중 오류 발생: {filename}, 오류: {e}")
            return None
    
    @abstractmethod
    def crawl_job_list(self, url):
        """
        채용 공고 목록 페이지를 크롤링하는 메서드
        
        Args:
            url (str): 크롤링할 URL
            
        Returns:
            list: 채용 공고 URL 목록
        """
        pass
    
    @abstractmethod
    def crawl_job_detail(self, url):
        """
        채용 공고 상세 페이지를 크롤링하는 메서드
        
        Args:
            url (str): 크롤링할 URL
            
        Returns:
            dict: 채용 공고 상세 정보
        """
        pass
    
    def crawl(self, url, max_jobs=None):
        """
        채용 공고를 크롤링하는 메인 메서드
        
        Args:
            url (str): 크롤링할 URL
            max_jobs (int): 최대 크롤링할 채용 공고 수 (기본값: None, 모든 공고 크롤링)
            
        Returns:
            list: 수집된 채용 공고 정보 목록
        """
        self.logger.info(f"크롤링 시작: {url}")
        
        try:
            # 채용 공고 목록 페이지 크롤링
            job_urls = self.crawl_job_list(url)
            
            if not job_urls:
                self.logger.warning("채용 공고 URL을 찾을 수 없습니다.")
                return []
            
            self.logger.info(f"총 {len(job_urls)}개의 채용 공고 URL을 찾았습니다.")
            
            # 최대 크롤링할 채용 공고 수 제한
            if max_jobs and max_jobs < len(job_urls):
                job_urls = job_urls[:max_jobs]
                self.logger.info(f"최대 {max_jobs}개의 채용 공고만 크롤링합니다.")
            
            # 채용 공고 상세 페이지 크롤링
            for i, job_url in enumerate(job_urls):
                self.logger.info(f"채용 공고 크롤링 중 ({i+1}/{len(job_urls)}): {job_url}")
                
                try:
                    job_data = self.crawl_job_detail(job_url)
                    if job_data:
                        self.data.append(job_data)
                except Exception as e:
                    self.logger.error(f"채용 공고 상세 크롤링 중 오류 발생: {job_url}, 오류: {e}")
            
            self.logger.info(f"크롤링 완료: 총 {len(self.data)}개의 채용 공고를 수집했습니다.")
            return self.data
            
        except Exception as e:
            self.logger.error(f"크롤링 중 오류 발생: {e}")
            return [] 