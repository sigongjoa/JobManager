def crawl_job_detail(self, url):
    """채용 공고 상세 페이지에서 정보 추출"""
    print(f"\n[크롤러 시작] 크롤링 URL: {url}")
    
    for retry in range(self.max_retries):
        try:
            driver = self.setup_driver()
            print(f"[드라이버 설정 완료] Selenium WebDriver 초기화됨")
            
            print(f"[페이지 로딩] URL 접속 시도...")
            driver.get(url)
            
            # 페이지 로딩 대기
            print(f"[페이지 로딩] {self.wait_time}초 대기 중...")
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
            print("\n[회사명 추출] 시작")
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
                print(f"[회사명 추출 성공] {company_name}")
            else:
                print("[회사명 추출 실패] 회사명을 찾을 수 없음")
            
            # 공고 제목 추출
            print("\n[공고 제목 추출] 시작")
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
                print(f"[공고 제목 추출 성공] {title}")
            else:
                print("[공고 제목 추출 실패] 제목을 찾을 수 없음")
            
            # 근무조건 추출 (개선된 버전)
            print("\n[근무조건 추출] 시작")
            job_conditions = self.extract_job_conditions(driver)
            print(f"[근무조건 추출 결과] {job_conditions}")
            
            if '경력' in job_conditions:
                job_data['experience'] = job_conditions['경력']
                print(f"[경력 추출 성공] {job_conditions['경력']}")
            
            if '학력' in job_conditions:
                job_data['education'] = job_conditions['학력']
                print(f"[학력 추출 성공] {job_conditions['학력']}")
            
            if '근무형태' in job_conditions:
                job_data['employment_type'] = job_conditions['근무형태']
                print(f"[근무형태 추출 성공] {job_conditions['근무형태']}")
            elif '고용형태' in job_conditions:
                job_data['employment_type'] = job_conditions['고용형태']
                print(f"[고용형태 추출 성공] {job_conditions['고용형태']}")
            
            if '근무지역' in job_conditions:
                job_data['location'] = job_conditions['근무지역']
                print(f"[근무지역 추출 성공] {job_conditions['근무지역']}")
            elif '근무지' in job_conditions:
                job_data['location'] = job_conditions['근무지']
                print(f"[근무지 추출 성공] {job_conditions['근무지']}")
            
            if '급여' in job_conditions:
                job_data['salary'] = job_conditions['급여']
                print(f"[급여 추출 성공] {job_conditions['급여']}")
            elif '연봉' in job_conditions:
                job_data['salary'] = job_conditions['연봉']
                print(f"[연봉 추출 성공] {job_conditions['연봉']}")
            
            # 복리후생 추출
            print("\n[복리후생 추출] 시작")
            welfare_benefits = self.extract_welfare_benefits(driver)
            if welfare_benefits:
                job_data['welfare_benefits'] = welfare_benefits
                print(f"[복리후생 추출 성공] {welfare_benefits[:100]}...")
            else:
                print("[복리후생 추출 실패] 복리후생 정보를 찾을 수 없음")
            
            # 접수기간 및 방법 추출
            print("\n[접수기간 추출] 시작")
            application_period = self.extract_application_period(driver)
            if application_period:
                job_data['application_period'] = application_period
                print(f"[접수기간 추출 성공] {application_period}")
                
                if '접수기간' in application_period:
                    job_data['deadline'] = application_period['접수기간']
                    print(f"[마감일 추출 성공] {application_period['접수기간']}")
            else:
                print("[접수기간 추출 실패] 접수기간 정보를 찾을 수 없음")
            
            # 기업정보 추출
            print("\n[기업정보 추출] 시작")
            company_info = self.extract_company_info(driver)
            if company_info:
                job_data['company_info'] = company_info
                print(f"[기업정보 추출 성공] {company_info}")
            else:
                print("[기업정보 추출 실패] 기업정보를 찾을 수 없음")
            
            # 상세 내용 추출
            print("\n[상세 내용 추출] 시작")
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
                print(f"[상세 내용 추출 성공] 길이: {len(description)} 자")
            else:
                print("[상세 내용 추출 실패] 상세 내용을 찾을 수 없음")
            
            # 데이터 검증
            print("\n[데이터 검증] 시작")
            for key, value in job_data.items():
                if key not in ['site', 'url', 'welfare_benefits', 'application_period', 'company_info', 'description'] and not value:
                    print(f"[데이터 검증 실패] {key} 정보를 찾을 수 없음")
            
            print("\n[크롤링 완료] 모든 데이터 추출 완료")
            driver.quit()
            return job_data
        
        except Exception as e:
            print(f"\n[오류 발생] 크롤링 중 오류 발생 (시도 {retry+1}/{self.max_retries}): {e}")
            if driver:
                driver.quit()
            
            if retry < self.max_retries - 1:
                print(f"[재시도] {5 * (retry + 1)}초 후 재시도합니다...")
                time.sleep(5 * (retry + 1))
            else:
                print("[최종 실패] 최대 재시도 횟수를 초과했습니다.")
                return None 