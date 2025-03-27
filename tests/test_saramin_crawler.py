from final_saramin_crawler import FinalSaraminCrawler

# 크롤러 인스턴스 생성
crawler = FinalSaraminCrawler()

# 특정 URL에서 채용 공고 크롤링
url = 'https://www.saramin.co.kr/zf_user/search/recruit?searchType=search&searchword=개발자'
results = crawler.crawl(url, max_jobs=5)   # 최대 5개 채용 공고만 크롤링

# 결과 저장
crawler.save_to_csv("saramin_jobs.csv")
crawler.save_to_json("saramin_jobs.json") 