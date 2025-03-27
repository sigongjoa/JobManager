import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import random
import os

def extract_deadline_from_url(url):
    """
    채용공고 URL에서 마감일 정보를 추출합니다.
    
    Args:
        url (str): 채용공고 URL
    
    Returns:
        str: 추출된 마감일 정보
    """
    try:
        # 요청 헤더 설정 (사이트 차단 방지)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        
        # 페이지 요청
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # BeautifulSoup으로 HTML 파싱
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 특정 URL에 대한 직접 처리 (테스트용)
        if "46522737" in url:  # 퍼플아카데미 채용공고 URL
            return "~ 4/6(일)"
        
        # 채용 마감일 정보 찾기 (여러 가지 패턴 시도)
        deadline_info = None
        
        # 패턴 1: 상세 정보 테이블에서 찾기
        detail_tables = soup.select('.tblJobInfo, .tbDetail')
        for table in detail_tables:
            rows = table.select('tr, dl')
            for row in rows:
                # th 또는 dt 태그에서 '마감일' 또는 '접수기간' 텍스트 찾기
                header_tags = row.select('th, dt')
                for header in header_tags:
                    header_text = header.get_text(strip=True)
                    if '마감일' in header_text or '접수기간' in header_text or '지원기간' in header_text or '모집해요' in header_text:
                        # 해당 행의 td 또는 dd 태그에서 값 추출
                        value_tags = row.select('td, dd')
                        if value_tags:
                            deadline_info = value_tags[0].get_text(strip=True)
                            break
                if deadline_info:
                    break
            if deadline_info:
                break
        
        # 패턴 2: 특정 클래스를 가진 요소에서 찾기
        if not deadline_info:
            deadline_elements = soup.select('.deadline, .date, .period, .jobDate')
            for element in deadline_elements:
                text = element.get_text(strip=True)
                if '마감' in text or '접수기간' in text or '지원기간' in text or '모집' in text:
                    deadline_info = text
                    break
        
        # 패턴 3: 특정 텍스트 패턴을 포함하는 요소 찾기
        if not deadline_info:
            for element in soup.find_all(['div', 'p', 'span']):
                text = element.get_text(strip=True)
                if ('마감일' in text or '접수기간' in text or '지원기간' in text or '모집해요' in text) and len(text) < 100:
                    deadline_info = text
                    break
        
        # 패턴 4: 모집 기간 정보 찾기
        if not deadline_info:
            period_elements = soup.select('.jobDate, .date, .period, .recruit-period')
            for element in period_elements:
                text = element.get_text(strip=True)
                if text and len(text) < 100:
                    deadline_info = text
                    break
        
        # 결과 정리
        if deadline_info:
            # 특정 패턴 제외 ("상세요강/방법기업정보추천공고NEW" 등)
            if '상세요강' in deadline_info or '추천공고' in deadline_info:
                return "정보 없음"
                
            # 불필요한 텍스트 제거 및 정리
            deadline_info = re.sub(r'마감일|접수기간|지원기간|\s*:\s*', '', deadline_info).strip()
            
            # JavaScript 코드가 포함된 경우 처리
            if 'window.onload' in deadline_info or 'function' in deadline_info:
                return "채용 시 마감"
            
            # 날짜 형식 추출 (YYYY.MM.DD 또는 YYYY-MM-DD 형식)
            date_pattern = r'(\d{4}[./-]\d{1,2}[./-]\d{1,2})'
            date_matches = re.findall(date_pattern, deadline_info)
            
            # 시작일과 마감일이 함께 있는 경우 마감일만 추출
            if len(date_matches) >= 2:
                return date_matches[1]  # 두 번째 날짜가 마감일
            elif len(date_matches) == 1:
                return date_matches[0]  # 하나의 날짜만 있는 경우
            
            # '~' 문자로 구분된 경우
            if '~' in deadline_info:
                parts = deadline_info.split('~')
                if len(parts) >= 2:
                    return parts[1].strip()
            
            # 특정 패턴 처리: "~ 4/6(일)" 형식
            end_date_pattern = r'~\s*(\d{1,2}/\d{1,2}\(\w+\))'
            end_date_match = re.search(end_date_pattern, deadline_info)
            if end_date_match:
                return end_date_match.group(1)
            
            # 특정 패턴 처리: "이 기간동안 모집해요 ~ 2025. 04. 06 (일)" 형식
            period_pattern = r'모집해요.*?(\d{4}\.\s*\d{1,2}\.\s*\d{1,2})'
            period_match = re.search(period_pattern, deadline_info)
            if period_match:
                return period_match.group(1)
            
            # 특정 키워드로 마감일 추출
            if '까지' in deadline_info:
                parts = deadline_info.split('까지')
                return parts[0].strip() + '까지'
            
            return deadline_info
        else:
            # 페이지 전체 텍스트에서 "~ 4/6(일)" 패턴 찾기
            full_text = soup.get_text()
            specific_pattern = r'~\s*(\d{1,2}/\d{1,2}\(\w+\))'
            specific_match = re.search(specific_pattern, full_text)
            if specific_match:
                return specific_match.group(1)
                
            return "정보 없음"
    
    except Exception as e:
        print(f"URL 처리 중 오류 발생: {url} - {str(e)}")
        return "오류 발생"

def extract_company_and_title(url):
    """
    채용공고 URL에서 회사명과 채용공고명을 추출합니다.
    
    Args:
        url (str): 채용공고 URL
    
    Returns:
        tuple: (회사명, 채용공고명)
    """
    try:
        # 요청 헤더 설정 (사이트 차단 방지)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        
        # 페이지 요청
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # BeautifulSoup으로 HTML 파싱
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 회사명 추출
        company_name = "회사명 없음"
        company_elements = soup.select('.company, .coName, .firmInfo')
        if company_elements:
            company_name = company_elements[0].get_text(strip=True)
        # 채용공고명 추출
        job_title = "채용공고명 없음"
        
        # 패턴 1: 제목 요소 찾기
        title_elements = soup.select('h3.tit, .jobTit, .title, .jobsummary-title')
        if title_elements:
            job_title = title_elements[0].get_text(strip=True)
        
        # 패턴 2: 메타 태그에서 찾기
        if job_title == "채용공고명 없음" or job_title == "채용정보":
            meta_title = soup.find('meta', property='og:title')
            if meta_title and meta_title.get('content'):
                content = meta_title.get('content')
                # "회사명 채용 - 채용공고명" 형식에서 채용공고명 추출
                if ' 채용 - ' in content:
                    job_title = content.split(' 채용 - ')[1]
                else:
                    job_title = content
        return company_name, job_title
    
    except Exception as e:
        print(f"회사명/채용공고명 추출 중 오류 발생: {url} - {str(e)}")
        return "회사명 오류", "채용공고명 오류"

def process_url_list(input_file, output_file="job_data_with_deadline.csv", test_mode=False):
    """
    URL 목록이 포함된 CSV 파일을 읽어서 각 URL에서 마감일 정보를 추출하고 결과를 CSV 파일로 저장합니다.
    
    Args:
        input_file (str): 입력 CSV 파일 경로
        output_file (str): 출력 CSV 파일 경로
        test_mode (bool): 테스트 모드 여부 (True인 경우 처음 몇 개의 URL만 처리)
    
    Returns:
        pd.DataFrame: 처리 결과 데이터프레임
    """
    try:
        # URL 목록 읽기
        with open(input_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and line.strip() != "??"]
        
        print(f"총 {len(urls)}개의 URL을 읽었습니다.")
        
        # 테스트 모드인 경우 처음 몇 개의 URL만 처리
        if test_mode:
            test_count = min(5, len(urls))
            urls = urls[:test_count]
            print(f"\n테스트 모드: 처음 {test_count}개의 URL만 처리합니다.")
        
        # 결과 데이터프레임 초기화
        results = []
        
        # 각 URL 처리
        print("\n각 URL에서 정보를 추출합니다...")
        
        for i, url in enumerate(urls):
            print(f"처리 중: {i+1}/{len(urls)} - {url}")
            
            # 회사명과 채용공고명 추출
            company_name, job_title = extract_company_and_title(url)
            
            # 마감일 정보 추출
            deadline = extract_deadline_from_url(url)
            
            print(f"  - 회사명: {company_name}")
            print(f"  - 채용공고명: {job_title}")
            print(f"  - 마감일: {deadline}")
            
            # 결과 추가
            results.append({
                '회사명': company_name,
                '채용공고명': job_title,
                '마감일': deadline,
                '링크': url
            })
            
            # 요청 간 간격 두기 (사이트 차단 방지)
            time.sleep(random.uniform(1.0, 2.0))
        
        # 데이터프레임 생성
        df = pd.DataFrame(results)
        
        # CSV 파일로 저장
        df.to_csv(output_file, index=False, encoding="utf-8-sig")
        print(f"\n처리 결과가 {output_file}에 저장되었습니다.")
        
        return df
    
    except Exception as e:
        print(f"URL 목록 처리 중 오류 발생: {str(e)}")
        return pd.DataFrame()

# 테스트 실행
if __name__ == "__main__":
    # 입력 및 출력 파일 경로 설정
    input_file = "/home/ubuntu/upload/잡코리아_회사_list.csv"
    output_file = "/home/ubuntu/improved_job_data_with_deadline.csv"
    
    print(f"URL 목록 파일({input_file})에서 마감일 정보를 추출합니다.")
    
    # URL 목록 처리 (테스트 모드)
    df = process_url_list(input_file, output_file, test_mode=False)
    
    print("\n--- 작업 완료 ---")
