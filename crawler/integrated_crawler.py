import re
import logging
from urllib.parse import urlparse
from crawlers.saramin_crawler import SaraminCrawler
from crawlers.jobplanet_crawler import JobPlanetCrawler
from crawlers.incruit_crawler import IncruitCrawler
import pandas as pd
import os
from typing import List, Dict, Any

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("integrated_crawler.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("IntegratedCrawler")

class IntegratedCrawler:
    """
    여러 채용 사이트의 크롤러를 통합하여 관리하는 클래스
    """
    
    def __init__(self):
        """통합 크롤러 초기화"""
        self.logger = logging.getLogger(__name__)
        self.crawlers = {
            'Saramin': SaraminCrawler(),
            'JobPlanet': JobPlanetCrawler(),
            'Incruit': IncruitCrawler()
        }
    
    def detect_site(self, url):
        """
        URL을 분석하여 어떤 사이트인지 감지
        
        Args:
            url (str): 분석할 URL
            
        Returns:
            str: 감지된 사이트 이름 (saramin, jobplanet, incruit 중 하나)
                 감지 실패 시 None 반환
        """
        try:
            domain = urlparse(url).netloc.lower()
            
            if 'saramin.co.kr' in domain:
                return 'Saramin'
            elif 'jobplanet.co.kr' in domain:
                return 'JobPlanet'
            elif 'incruit.com' in domain:
                return 'Incruit'
            else:
                logger.warning(f"지원하지 않는 사이트입니다: {domain}")
                return None
                
        except Exception as e:
            logger.error(f"사이트 감지 중 오류 발생: {e}")
            return None
    
    def crawl(self, url, max_jobs=None):
        """
        URL을 분석하여 적절한 크롤러를 선택하고 크롤링 실행
        
        Args:
            url (str): 크롤링할 URL
            max_jobs (int): 최대 크롤링할 채용 공고 수 (기본값: None, 모든 공고 크롤링)
            
        Returns:
            tuple: (사이트 이름, 크롤링 결과)
        """
        site = self.detect_site(url)
        
        if not site:
            logger.error(f"지원하지 않는 사이트입니다: {url}")
            return None, []
        
        logger.info(f"감지된 사이트: {site}, URL: {url}")
        
        try:
            crawler = self.crawlers[site]
            result = crawler.crawl(url, max_jobs)
            
            if result:
                logger.info(f"크롤링 성공: {site}, 총 {len(result)}개의 채용 공고를 수집했습니다.")
            else:
                logger.warning(f"크롤링 결과가 없습니다: {site}, URL: {url}")
            
            return site, result
            
        except Exception as e:
            logger.error(f"크롤링 중 오류 발생: {site}, URL: {url}, 오류: {e}")
            return site, []
    
    def crawl_multiple(self, urls: List[str], max_jobs: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """
        여러 URL에서 채용 정보를 크롤링
        
        Args:
            urls (List[str]): 크롤링할 URL 목록
            max_jobs (int): 각 크롤러당 최대 크롤링할 채용 공고 수
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: 사이트별 크롤링 결과
        """
        results = {}
        
        try:
            for url in urls:
                # URL에서 사이트 식별
                site = None
                if 'saramin.co.kr' in url:
                    site = 'Saramin'
                elif 'jobplanet.co.kr' in url:
                    site = 'JobPlanet'
                elif 'incruit.com' in url:
                    site = 'Incruit'
                
                if site and site in self.crawlers:
                    self.logger.info(f"{site} 크롤러로 크롤링 시작: {url}")
                    result = self.crawlers[site].crawl(url, max_jobs)
                    results[site] = result
                else:
                    self.logger.warning(f"지원하지 않는 URL입니다: {url}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"통합 크롤링 중 오류 발생: {e}")
            return {}
    
    def cleanup(self):
        """생성된 CSV 파일들을 정리"""
        for site in self.crawlers.keys():
            filename = f"{site}_jobs.csv"
            max_retries = 3
            retry_delay = 2  # 초
            
            for attempt in range(max_retries):
                try:
                    if os.path.exists(filename):
                        # 파일이 사용 중인지 확인
                        try:
                            with open(filename, 'a'):
                                pass
                            os.remove(filename)
                            self.logger.info(f"파일 삭제됨: {filename}")
                            break
                        except IOError:
                            self.logger.warning(f"파일이 사용 중입니다. 재시도 중... ({attempt + 1}/{max_retries})")
                            import time
                            time.sleep(retry_delay)
                    else:
                        self.logger.info(f"파일이 존재하지 않음: {filename}")
                        break
                except Exception as e:
                    self.logger.error(f"파일 삭제 중 오류 발생: {filename}, 오류: {e}")
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(retry_delay)
                    else:
                        self.logger.error(f"최대 재시도 횟수 초과: {filename}")


def main():
    """
    메인 함수
    """
    # 통합 크롤러 생성
    crawler = IntegratedCrawler()
    
    # 테스트할 URL 목록
    test_urls = [
        "https://www.saramin.co.kr/zf_user/search/recruit?searchType=search&searchword=개발자",
        "https://www.jobplanet.co.kr/job/search?q=개발자",
        "https://www.incruit.com/list/search.asp?col=all&kw=개발자"
    ]
    
    # 각 URL 크롤링 테스트
    for url in test_urls:
        print(f"\n{'='*50}")
        print(f"URL 테스트: {url}")
        print(f"{'='*50}")
        
        site, result = crawler.crawl(url, max_jobs=3)  # 테스트를 위해 각 사이트당 최대 3개의 공고만 크롤링
        
        if result:
            print(f"크롤링 성공: {site}, 총 {len(result)}개의 채용 공고를 수집했습니다.")
            
            # 결과 출력 (첫 번째 항목만)
            if len(result) > 0:
                print("\n첫 번째 채용 공고 정보:")
                for key, value in result[0].items():
                    if key == 'description':
                        print(f"{key}: {value[:100]}...")  # 설명은 처음 100자만 출력
                    else:
                        print(f"{key}: {value}")
        else:
            print(f"크롤링 실패: {site}, URL: {url}")
    
    print("\n모든 테스트가 완료되었습니다.")


if __name__ == "__main__":
    main() 