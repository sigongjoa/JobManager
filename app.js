// 전역 변수
const API_BASE_URL = '/api';
let currentPage = 'dashboard';

// DOM이 로드된 후 실행
document.addEventListener('DOMContentLoaded', function() {
    // Bootstrap 드롭다운 초기화
    const dropdownElementList = document.querySelectorAll('.dropdown-toggle');
    const dropdownList = [...dropdownElementList].map(dropdownToggleEl => new bootstrap.Dropdown(dropdownToggleEl));
    
    // 네비게이션 이벤트 리스너 설정
    setupNavigation();
    
    // 초기 페이지 로드
    loadPage('dashboard');
    
    // 버튼 이벤트 리스너 설정
    setupButtonListeners();
    
    // 모달 이벤트 리스너 설정
    setupModalListeners();
    
    // 크롤링 폼 이벤트 리스너 설정
    setupCrawlerFormListeners();
});

// 네비게이션 설정
function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const page = this.getAttribute('data-page');
            loadPage(page);
        });
    });
}

// 페이지 로드
function loadPage(page) {
    // 현재 페이지 숨기기
    document.querySelectorAll('.page').forEach(p => {
        p.classList.add('d-none');
    });
    
    // 선택한 페이지 표시
    document.getElementById(`${page}-page`).classList.remove('d-none');
    
    // 네비게이션 링크 활성화
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('data-page') === page) {
            link.classList.add('active');
        }
    });
    
    // 현재 페이지 업데이트
    currentPage = page;
    
    // 페이지별 데이터 로드
    switch (page) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'jobs':
            loadJobs();
            break;
        case 'resumes':
            loadResumes();
            break;
        case 'applications':
            loadApplications();
            break;
        case 'feedbacks':
            loadFeedbacks();
            break;
        case 'linkedin-crawler':
            setupLinkedInCrawler();
            break;
        case 'jobkorea-crawler':
            setupJobKoreaCrawler();
            break;
        case 'wanted-crawler':
            setupWantedCrawler();
            break;
    }
}

// 버튼 이벤트 리스너 설정
function setupButtonListeners() {
    // 채용 공고 추가 버튼
    document.getElementById('add-job-btn').addEventListener('click', addJob);
    
    // 자소서 추가 버튼
    document.getElementById('add-resume-btn').addEventListener('click', addResume);
    
    // 지원 결과 추가 버튼
    document.getElementById('add-application-btn').addEventListener('click', addApplication);
    
    // 피드백 요청 버튼
    document.getElementById('request-feedback-btn').addEventListener('click', requestFeedback);
    
    // 크롤링 버튼
    document.getElementById('crawl-jobs-btn').addEventListener('click', crawlJobs);
    
    // 비교 피드백 요청 버튼
    document.getElementById('request-compare-feedback-btn').addEventListener('click', requestCompareFeeback);
}

// 모달 이벤트 리스너 설정
function setupModalListeners() {
    // 지원 결과 추가 모달이 열릴 때 채용 공고와 자소서 목록 로드
    const addApplicationModal = document.getElementById('addApplicationModal');
    addApplicationModal.addEventListener('show.bs.modal', function() {
        loadJobsForSelect('application-job');
        loadResumesForSelect('application-resume');
    });
    
    // 피드백 요청 모달이 열릴 때 자소서와 채용 공고 목록 로드
    const requestFeedbackModal = document.getElementById('requestFeedbackModal');
    requestFeedbackModal.addEventListener('show.bs.modal', function() {
        loadResumesForSelect('feedback-resume');
        loadJobsForSelect('feedback-job');
    });
}

// 크롤링 폼 이벤트 리스너 설정
function setupCrawlerFormListeners() {
    // 모든 크롤러 폼에 이벤트 리스너 추가
    document.querySelectorAll('.crawler-form').forEach(form => {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // 폼 데이터 가져오기
            const platform = this.querySelector('input[name="platform"]').value;
            const url = this.querySelector('input[type="url"]').value;
            
            // 결과 카드 표시
            const resultsCard = document.getElementById(`${platform}-results`);
            const jobsList = document.getElementById(`${platform}-jobs-list`);
            resultsCard.classList.remove('d-none');
            jobsList.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>';
            
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
                
                if (!response.ok) {
                    throw new Error('크롤링 중 오류가 발생했습니다.');
                }
                
                const data = await response.json();
                
                // 결과 표시
                if (data.jobs && data.jobs.length > 0) {
                    let jobsHtml = '<div class="list-group">';
                    data.jobs.forEach(job => {
                        jobsHtml += `
                            <div class="list-group-item">
                                <div class="d-flex w-100 justify-content-between">
                                    <h5 class="mb-1">${job.title}</h5>
                                    <small>${job.company}</small>
                                </div>
                                <p class="mb-1">${job.description || '설명 없음'}</p>
                                <div class="d-flex justify-content-between align-items-center">
                                    <small>마감일: ${job.deadline || '미정'}</small>
                                    <button class="btn btn-sm btn-primary save-job-btn" data-job-id="${job.id}">저장</button>
                                </div>
                            </div>
                        `;
                    });
                    jobsHtml += '</div>';
                    jobsList.innerHTML = jobsHtml;
                    
                    // 저장 버튼에 이벤트 리스너 추가
                    jobsList.querySelectorAll('.save-job-btn').forEach(button => {
                        button.addEventListener('click', async function() {
                            const jobId = this.dataset.jobId;
                            try {
                                const response = await fetch('/api/jobs', {
                                    method: 'POST',
                                    headers: {
                                        'Content-Type': 'application/json',
                                    },
                                    body: JSON.stringify({ job_id: jobId })
                                });
                                
                                if (!response.ok) {
                                    throw new Error('채용 공고 저장 중 오류가 발생했습니다.');
                                }
                                
                                alert('채용 공고가 성공적으로 저장되었습니다.');
                                this.disabled = true;
                                this.textContent = '저장됨';
                            } catch (error) {
                                console.error('저장 오류:', error);
                                alert('채용 공고 저장 중 오류가 발생했습니다.');
                            }
                        });
                    });
                } else {
                    jobsList.innerHTML = '<p class="text-center">크롤링된 채용 공고가 없습니다.</p>';
                }
            } catch (error) {
                console.error('크롤링 오류:', error);
                jobsList.innerHTML = '<div class="alert alert-danger">크롤링 중 오류가 발생했습니다.</div>';
            }
        });
    });
}

// 대시보드 데이터 로드
async function loadDashboard() {
    try {
        // 최근 채용 공고 로드
        const jobsResponse = await fetch(`${API_BASE_URL}/jobs?limit=5`);
        const jobs = await jobsResponse.json();
        
        let jobsHtml = '';
        if (jobs.length > 0) {
            jobsHtml = '<ul class="list-group">';
            jobs.forEach(job => {
                jobsHtml += `
                    <li class="list-group-item d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${job.title}</strong>
                            <div class="text-muted">${job.company}</div>
                        </div>
                        <span class="badge bg-primary rounded-pill">${job.deadline || '마감일 없음'}</span>
                    </li>
                `;
            });
            jobsHtml += '</ul>';
        } else {
            jobsHtml = '<p class="text-center">등록된 채용 공고가 없습니다.</p>';
        }
        document.getElementById('recent-jobs-list').innerHTML = jobsHtml;
        
        // 지원 현황 로드
        const applicationsResponse = await fetch(`${API_BASE_URL}/applications`);
        const applications = await applicationsResponse.json();
        
        const statusCounts = {
            '지원 완료': 0,
            '서류 합격': 0,
            '면접 합격': 0,
            '최종 합격': 0,
            '불합격': 0
        };
        
        applications.forEach(app => {
            if (statusCounts[app.status] !== undefined) {
                statusCounts[app.status]++;
            }
        });
        
        let statsHtml = '<div class="row">';
        for (const [status, count] of Object.entries(statusCounts)) {
            let bgClass = 'bg-secondary';
            switch (status) {
                case '지원 완료': bgClass = 'bg-info'; break;
                case '서류 합격': bgClass = 'bg-primary'; break;
                case '면접 합격': bgClass = 'bg-warning'; break;
                case '최종 합격': bgClass = 'bg-success'; break;
                case '불합격': bgClass = 'bg-danger'; break;
            }
            
            statsHtml += `
                <div class="col-md-4 mb-3">
                    <div class="card text-white ${bgClass}">
                        <div class="card-body text-center">
                            <h5 class="card-title">${count}</h5>
                            <p class="card-text">${status}</p>
                        </div>
                    </div>
                </div>
            `;
        }
        statsHtml += '</div>';
        document.getElementById('application-stats').innerHTML = statsHtml;
        
        // 최근 피드백 로드
        const feedbacksResponse = await fetch(`${API_BASE_URL}/feedbacks?limit=3`);
        const feedbacks = await feedbacksResponse.json();
        
        let feedbacksHtml = '';
        if (feedbacks.length > 0) {
            feedbacksHtml = '<div class="list-group">';
            feedbacks.forEach(feedback => {
                const truncatedText = feedback.feedback_text.length > 150 
                    ? feedback.feedback_text.substring(0, 150) + '...' 
                    : feedback.feedback_text;
                
                feedbacksHtml += `
                    <div class="list-group-item">
                        <div class="d-flex w-100 justify-content-between">
                            <h5 class="mb-1">${feedback.resume_title}</h5>
                            <small>${new Date(feedback.created_at).toLocaleDateString()}</small>
                        </div>
                        <p class="mb-1">${truncatedText}</p>
                        <button class="btn btn-sm btn-outline-primary mt-2" 
                                onclick="showFeedbackDetail(${feedback.id})">
                            자세히 보기
                        </button>
                    </div>
                `;
            });
            feedbacksHtml += '</div>';
        } else {
            feedbacksHtml = '<p class="text-center">등록된 피드백이 없습니다.</p>';
        }
        document.getElementById('recent-feedbacks').innerHTML = feedbacksHtml;
        
    } catch (error) {
        console.error('대시보드 로드 중 오류 발생:', error);
        showToast('대시보드 데이터를 불러오는 중 오류가 발생했습니다.', 'danger');
    }
}

// 채용 공고 목록 로드
async function loadJobs() {
    try {
        const response = await fetch(`${API_BASE_URL}/jobs`);
        const jobs = await response.json();
        
        let html = '';
        if (jobs.length > 0) {
            jobs.forEach(job => {
                html += `
                    <tr>
                        <td>${job.title}</td>
                        <td>${job.company}</td>
                        <td>${job.deadline || '마감일 없음'}</td>
                        <td>${new Date(job.crawled_at).toLocaleDateString()}</td>
                        <td>
                            <button class="btn btn-sm btn-info" onclick="showJobDetail(${job.id})">상세</button>
                            <button class="btn btn-sm btn-danger" onclick="deleteJob(${job.id})">삭제</button>
                        </td>
                    </tr>
                `;
            });
        } else {
            html = '<tr><td colspan="5" class="text-center">등록된 채용 공고가 없습니다.</td></tr>';
        }
        
        document.getElementById('jobs-list').innerHTML = html;
    } catch (error) {
        console.error('채용 공고 로드 중 오류 발생:', error);
        showToast('채용 공고를 불러오는 중 오류가 발생했습니다.', 'danger');
    }
}

// 자소서 목록 로드
async function loadResumes() {
    try {
        const response = await fetch(`${API_BASE_URL}/resumes`);
        const resumes = await response.json();
        
        let html = '';
        if (resumes.length > 0) {
            resumes.forEach(resume => {
                html += `
                    <tr>
                        <td>${resume.title}</td>
                        <td>${new Date(resume.uploaded_at).toLocaleDateString()}</td>
                        <td>
                            <button class="btn btn-sm btn-info" onclick="showResumeDetail(${resume.id})">상세</button>
                            <button class="btn btn-sm btn-danger" onclick="deleteResume(${resume.id})">삭제</button>
                        </td>
                    </tr>
                `;
            });
        } else {
            html = '<tr><td colspan="3" class="text-center">등록된 자소서가 없습니다.</td></tr>';
        }
        
        document.getElementById('resumes-list').innerHTML = html;
    } catch (error) {
        console.error('자소서 로드 중 오류 발생:', error);
        showToast('자소서를 불러오는 중 오류가 발생했습니다.', 'danger');
    }
}

// 지원 결과 목록 로드
async function loadApplications() {
    try {
        const response = await fetch(`${API_BASE_URL}/applications`);
        const applications = await response.json();
        
        let html = '';
        if (applications.length > 0) {
            applications.forEach(app => {
                let statusClass = '';
                switch (app.status) {
                    case '지원 완료': statusClass = 'status-applied'; break;
                    case '서류 합격': statusClass = 'status-document-passed'; break;
                    case '면접 합격': statusClass = 'status-interview-passed'; break;
                    case '최종 합격': statusClass = 'status-final-passed'; break;
                    case '불합격': statusClass = 'status-failed'; break;
                }
                
                html += `
                    <tr>
                        <td>${app.company}</td>
                        <td>${app.job_title}</td>
                        <td>${app.resume_title}</td>
                        <td><span class="status-badge ${statusClass}">${app.status}</span></td>
                        <td>${new Date(app.applied_at).toLocaleDateString()}</td>
                        <td>
                            <button class="btn btn-sm btn-info" onclick="showApplicationDetail(${app.id})">상세</button>
                            <button class="btn btn-sm btn-warning" onclick="showCompare(${app.job_id}, ${app.resume_id})">비교</button>
                            <button class="btn btn-sm btn-danger" onclick="deleteApplication(${app.id})">삭제</button>
                        </td>
                    </tr>
                `;
            });
        } else {
            html = '<tr><td colspan="6" class="text-center">등록된 지원 결과가 없습니다.</td></tr>';
        }
        
        document.getElementById('applications-list').innerHTML = html;
    } catch (error) {
        console.error('지원 결과 로드 중 오류 발생:', error);
        showToast('지원 결과를 불러오는 중 오류가 발생했습니다.', 'danger');
    }
}

// 피드백 목록 로드
async function loadFeedbacks() {
    try {
        const response = await fetch(`${API_BASE_URL}/feedbacks`);
        const feedbacks = await response.json();
        
        let html = '';
        if (feedbacks.length > 0) {
            feedbacks.forEach(feedback => {
                html += `
                    <tr>
                        <td>${feedback.resume_title}</td>
                        <td>${feedback.job_id ? '있음' : '없음'}</td>
                        <td>${new Date(feedback.created_at).toLocaleDateString()}</td>
                        <td>
                            <button class="btn btn-sm btn-info" onclick="showFeedbackDetail(${feedback.id})">상세</button>
                            <button class="btn btn-sm btn-danger" onclick="deleteFeedback(${feedback.id})">삭제</button>
                        </td>
                    </tr>
                `;
            });
        } else {
            html = '<tr><td colspan="4" class="text-center">등록된 피드백이 없습니다.</td></tr>';
        }
        
        document.getElementById('feedbacks-list').innerHTML = html;
    } catch (error) {
        console.error('피드백 로드 중 오류 발생:', error);
        showToast('피드백을 불러오는 중 오류가 발생했습니다.', 'danger');
    }
}

// 채용 공고 상세 정보 표시
async function showJobDetail(jobId) {
    try {
        const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`);
        const job = await response.json();
        
        const html = `
            <h4>${job.title}</h4>
            <p class="text-muted">${job.company}</p>
            <p><strong>마감일:</strong> ${job.deadline || '마감일 없음'}</p>
            <p><strong>링크:</strong> <a href="${job.link}" target="_blank">${job.link}</a></p>
            <hr>
            <div class="job-description">
                <h5>채용 공고 내용</h5>
                ${job.description}
            </div>
        `;
        
        document.getElementById('job-detail-content').innerHTML = html;
        
        // 모달 표시
        const modal = new bootstrap.Modal(document.getElementById('jobDetailModal'));
        modal.show();
    } catch (error) {
        console.error('채용 공고 상세 정보 로드 중 오류 발생:', error);
        showToast('채용 공고 상세 정보를 불러오는 중 오류가 발생했습니다.', 'danger');
    }
}

// 자소서 상세 정보 표시
async function showResumeDetail(resumeId) {
    try {
        const response = await fetch(`${API_BASE_URL}/resumes/${resumeId}`);
        const resume = await response.json();
        
        const html = `
            <h4>${resume.title}</h4>
            <p class="text-muted">업로드: ${new Date(resume.uploaded_at).toLocaleDateString()}</p>
            <hr>
            <div class="resume-content">
                <h5>자소서 내용</h5>
                ${resume.text_content}
            </div>
        `;
        
        document.getElementById('resume-detail-content').innerHTML = html;
        
        // 모달 표시
        const modal = new bootstrap.Modal(document.getElementById('resumeDetailModal'));
        modal.show();
    } catch (error) {
        console.error('자소서 상세 정보 로드 중 오류 발생:', error);
        showToast('자소서 상세 정보를 불러오는 중 오류가 발생했습니다.', 'danger');
    }
}

// 피드백 상세 정보 표시
async function showFeedbackDetail(feedbackId) {
    try {
        const response = await fetch(`${API_BASE_URL}/feedbacks/${feedbackId}`);
        const feedback = await response.json();
        
        const html = `
            <h4>${feedback.resume_title}에 대한 피드백</h4>
            <p class="text-muted">생성: ${new Date(feedback.created_at).toLocaleDateString()}</p>
            <hr>
            <div class="feedback-content">
                ${feedback.feedback_text}
            </div>
        `;
        
        document.getElementById('feedback-detail-content').innerHTML = html;
        
        // 모달 표시
        const modal = new bootstrap.Modal(document.getElementById('feedbackDetailModal'));
        modal.show();
    } catch (error) {
        console.error('피드백 상세 정보 로드 중 오류 발생:', error);
        showToast('피드백 상세 정보를 불러오는 중 오류가 발생했습니다.', 'danger');
    }
}

// 자소서와 채용공고 비교
async function showCompare(jobId, resumeId) {
    try {
        const response = await fetch(`${API_BASE_URL}/compare?job_id=${jobId}&resume_id=${resumeId}`);
        const data = await response.json();
        
        document.getElementById('compare-resume-content').innerHTML = data.resume.text_content;
        document.getElementById('compare-job-content').innerHTML = data.job.description;
    } catch (error) {
        console.error('자소서와 채용공고 비교 중 오류 발생:', error);
        showToast('자소서와 채용공고를 비교하는 중 오류가 발생했습니다.', 'danger');
    }
}

// 크롤링 관련 함수들
function setupLinkedInCrawler() {
    const form = document.getElementById('linkedin-crawler-form');
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        const url = document.getElementById('linkedin-url').value;
        await startCrawling('linkedin', url);
    });
}

function setupJobKoreaCrawler() {
    const form = document.getElementById('jobkorea-crawler-form');
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        const url = document.getElementById('jobkorea-url').value;
        await startCrawling('jobkorea', url);
    });
}

function setupWantedCrawler() {
    const form = document.getElementById('wanted-crawler-form');
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        const url = document.getElementById('wanted-url').value;
        await startCrawling('wanted', url);
    });
}

async function startCrawling(platform, url) {
    try {
        // 로딩 표시
        const resultsCard = document.getElementById(`${platform}-results`);
        const jobsList = document.getElementById(`${platform}-jobs-list`);
        resultsCard.classList.remove('d-none');
        jobsList.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>';

        // 크롤링 API 호출
        const response = await fetch(`${API_BASE_URL}/crawl`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                platform: platform,
                url: url
            })
        });

        if (!response.ok) {
            throw new Error('크롤링 중 오류가 발생했습니다.');
        }

        const data = await response.json();
        
        // 결과 표시
        let jobsHtml = '';
        if (data.jobs && data.jobs.length > 0) {
            jobsHtml = '<div class="list-group">';
            data.jobs.forEach(job => {
                jobsHtml += `
                    <div class="list-group-item">
                        <div class="d-flex w-100 justify-content-between">
                            <h5 class="mb-1">${job.title}</h5>
                            <small>${job.company}</small>
                        </div>
                        <p class="mb-1">${job.description || '설명 없음'}</p>
                        <div class="d-flex justify-content-between align-items-center">
                            <small>마감일: ${job.deadline || '미정'}</small>
                            <button class="btn btn-sm btn-primary" onclick="saveJob('${job.id}')">저장</button>
                        </div>
                    </div>
                `;
            });
            jobsHtml += '</div>';
        } else {
            jobsHtml = '<p class="text-center">크롤링된 채용 공고가 없습니다.</p>';
        }
        jobsList.innerHTML = jobsHtml;
    } catch (error) {
        console.error('크롤링 오류:', error);
        document.getElementById(`${platform}-jobs-list`).innerHTML = 
            '<div class="alert alert-danger">크롤링 중 오류가 발생했습니다.</div>';
    }
}

async function saveJob(jobId) {
    try {
        const response = await fetch(`${API_BASE_URL}/jobs`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                job_id: jobId
            })
        });

        if (!response.ok) {
            throw new Error('채용 공고 저장 중 오류가 발생했습니다.');
        }

        alert('채용 공고가 성공적으로 저장되었습니다.');
    } catch (error) {
        console.error('저장 오류:', error);
        alert('채용 공고 저장 중 오류가 발생했습니다.');
    }
}

// 크롤링 버튼 클릭 이벤트
document.getElementById('crawlButton').addEventListener('click', async function() {
    const urlInput = document.getElementById('urlInput');
    const url = urlInput.value.trim();
    
    if (!url) {
        alert('URL을 입력해주세요.');
        return;
    }

    try {
        // 로딩 표시
        this.disabled = true;
        this.textContent = '크롤링 중...';

        // API 호출
        const response = await fetch('/api/crawl', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                url: url,
                platform: 'saramin'
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || '크롤링 중 오류가 발생했습니다.');
        }

        // 결과를 테이블에 추가
        const jobs = data.jobs;
        const tbody = document.querySelector('#jobTable tbody');
        
        // 기존 행 제거
        tbody.innerHTML = '';
        
        jobs.forEach(job => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${job.company || ''}</td>
                <td>${job.title || ''}</td>
                <td>${job.deadline || ''}</td>
                <td>${job.experience || ''}</td>
                <td>${job.education || ''}</td>
                <td>${job.employment_type || ''}</td>
                <td>${job.location || ''}</td>
                <td>${job.salary || ''}</td>
                <td><a href="${job.link}" target="_blank">링크</a></td>
            `;
            tbody.appendChild(row);
        });

        // 입력 필드 초기화
        urlInput.value = '';
        
        // 성공 메시지 표시
        alert(data.message);

    } catch (error) {
        console.error('크롤링 오류:', error);
        alert(error.message || '크롤링 중 오류가 발생했습니다.');
    } finally {
        // 버튼 상태 복구
        this.disabled = false;
        this.textContent = '크롤링';
    }
});