# Job Manager

취업 준비를 위한 채용 공고 관리 시스템입니다.

## 주요 기능

- 사람인 채용 공고 크롤링
- 채용 공고 관리
- 이력서 관리
- 지원 현황 관리
- 대시보드를 통한 통계 확인

## 기술 스택

- Backend: FastAPI
- Frontend: HTML, JavaScript, Bootstrap 5
- Database: JSON 파일 기반 저장소
- Crawler: Selenium

## 설치 방법

1. 저장소 클론
```bash
git clone https://github.com/[username]/JobManager.git
cd JobManager
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

3. 의존성 설치
```bash
pip install -r requirements.txt
```

4. 서버 실행
```bash
uvicorn main:app --reload
```

## 사용 방법

1. 웹 브라우저에서 `http://localhost:8000` 접속
2. 사람인 채용 공고 URL을 입력하여 크롤링
3. 크롤링된 채용 공고 확인 및 관리
4. 이력서 등록 및 관리
5. 지원 현황 관리 및 상태 업데이트

## 주의사항

- 크롤링은 사람인 채용 공고 페이지만 지원합니다.
- 데이터는 로컬의 JSON 파일에 저장됩니다.
- 실제 지원은 사람인 페이지에서 진행해야 합니다. 