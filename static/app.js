// DOM이 로드된 후 실행
document.addEventListener('DOMContentLoaded', function() {
    // 모든 크롤러 폼에 이벤트 리스너 추가
    document.querySelectorAll('.crawler-form').forEach(form => {
        form.addEventListener('submit', handleCrawlerFormSubmit);
    });

    // 테스트 버튼에 이벤트 리스너 추가
    document.querySelectorAll('.test-existing-data').forEach(button => {
        button.addEventListener('click', handleTestExistingData);
    });

    // 탭 변경 시 URL 업데이트
    const tabs = document.querySelectorAll('[data-bs-toggle="tab"]');
    tabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(event) {
            const platform = event.target.textContent.toLowerCase();
            history.pushState(null, '', `/crawling?platform=${platform}`);
        });
    });
});

// 테스트 데이터 처리
async function handleTestExistingData(e) {
    const platform = this.dataset.platform;
    const resultDiv = document.getElementById(`${platform}-results`);
    
    // 로딩 표시
    resultDiv.innerHTML = '<div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div>';
    
    try {
        // 테스트용 URL (테스트 데이터용)
        const testUrl = 'http://test.com/job/1';
        
        // API 호출
        const response = await fetch('/api/crawl', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                platform: platform,
                url: testUrl
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || '테스트 중 오류가 발생했습니다.');
        }
        
        // 결과 표시 (기존 displayResults 함수 재사용)
        displayResults(data, resultDiv);
    } catch (error) {
        console.error('테스트 오류:', error);
        resultDiv.innerHTML = '<div class="alert alert-danger">테스트 중 오류가 발생했습니다: ' + error.message + '</div>';
    }
}

// 크롤러 폼 제출 처리
async function handleCrawlerFormSubmit(e) {
    e.preventDefault();
    
    // 폼 데이터 가져오기
    const platform = this.querySelector('input[name="platform"]').value;
    const url = this.querySelector('input[type="url"]').value;
    const resultDiv = document.getElementById(`${platform}-results`);
    
    // 로딩 표시
    resultDiv.innerHTML = '<div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div>';
    
    try {
        // API 호출
        const response = await fetch('/api/crawl', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                platform: platform,
                url: url
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || '크롤링 중 오류가 발생했습니다.');
        }
        
        // 결과 표시
        displayResults(data, resultDiv);
    } catch (error) {
        console.error('크롤링 오류:', error);
        resultDiv.innerHTML = '<div class="alert alert-danger">크롤링 중 오류가 발생했습니다: ' + error.message + '</div>';
    }
}

// 결과 표시 함수
function displayResults(data, resultDiv) {
    if (data.success && data.jobs && data.jobs.length > 0) {
        let html = '';
        data.jobs.forEach(job => {
            html += `
                <div class="card mb-4">
                    <div class="card-header">
                        <h5 class="card-title mb-0">${job.title}</h5>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <strong>회사:</strong> ${job.company}
                        </div>
                        <div class="mb-3">
                            <strong>마감일:</strong> ${job.deadline || '미정'}
                        </div>
                        <div class="mb-3">
                            <strong>경력:</strong> ${job.experience || '미정'}
                        </div>
                        <div class="mb-3">
                            <strong>학력:</strong> ${job.education || '미정'}
                        </div>
                        <div class="mb-3">
                            <strong>고용형태:</strong> ${job.employment_type || '미정'}
                        </div>
                        <div class="mb-3">
                            <strong>근무지:</strong> ${job.location || '미정'}
                        </div>
                        <div class="mb-3">
                            <strong>급여:</strong> ${job.salary || '미정'}
                        </div>
                        <div class="mb-3">
                            <strong>채용 공고 링크:</strong> 
                            <a href="${job.link}" target="_blank">${job.link}</a>
                        </div>
                        <div class="mb-3">
                            <strong>상세 설명:</strong>
                            <pre class="mt-2" style="white-space: pre-wrap; font-family: inherit;">${job.description || '상세 설명 없음'}</pre>
                        </div>
                        <button class="btn btn-primary save-job-btn" data-job='${JSON.stringify(job)}'>저장</button>
                    </div>
                </div>
            `;
        });
        resultDiv.innerHTML = html;
        
        // 저장 버튼에 이벤트 리스너 추가
        resultDiv.querySelectorAll('.save-job-btn').forEach(button => {
            button.addEventListener('click', async function() {
                const jobData = JSON.parse(this.dataset.job);
                const jobId = await saveJob(jobData);
                if (jobId) {
                    this.disabled = true;
                    this.textContent = '저장됨';
                }
            });
        });
    } else {
        resultDiv.innerHTML = `<div class="alert alert-danger">${data.message || '크롤링된 채용 공고가 없습니다.'}</div>`;
    }
}

// 채용공고 저장 함수
async function saveJob(jobData) {
    try {
        const response = await fetch('/api/jobs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(jobData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert('채용공고가 저장되었습니다.');
            return result.job_id;
        } else {
            throw new Error(result.detail || '채용공고 저장에 실패했습니다.');
        }
    } catch (error) {
        console.error('채용공고 저장 에러:', error);
        alert('채용공고 저장에 실패했습니다: ' + error.message);
        return null;
    }
} 