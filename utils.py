import io
import PyPDF2
import openai
import os

def extract_text_from_pdf_bytes(content):
    """PDF 바이트 데이터에서 텍스트 추출"""
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"PDF 텍스트 추출 중 오류 발생: {e}")
        return "텍스트 추출 실패"

def generate_llm_feedback(resume_text, job_description=None):
    """
    LLM을 통해 자소서 피드백 생성
    실제 구현에서는 OpenAI API 등을 사용할 수 있습니다.
    """
    try:
        # OpenAI API 키 설정 (실제 사용 시 환경 변수 등으로 관리)
        # openai.api_key = os.getenv("OPENAI_API_KEY")
        
        # 실제 API 호출 대신 예시 피드백 생성
        feedback = "자소서 피드백:\n\n"
        feedback += "1. 강점: 전반적으로 경험과 역량이 잘 드러나 있습니다.\n"
        feedback += "2. 개선점: 구체적인 성과와 수치를 더 추가하면 좋을 것 같습니다.\n"
        feedback += "3. 문장 구성: 일부 문장이 너무 길어 가독성이 떨어집니다. 간결하게 정리해보세요.\n"
        
        if job_description:
            feedback += "\n채용공고와의 연관성:\n"
            feedback += "1. 채용공고에서 요구하는 핵심 역량과 자소서의 내용이 일부 일치합니다.\n"
            feedback += "2. 채용공고에서 강조하는 '팀워크'와 '문제해결 능력'에 대한 내용을 더 보강하면 좋을 것 같습니다.\n"
            feedback += "3. 지원 직무와 관련된 프로젝트 경험을 더 구체적으로 서술하면 경쟁력이 높아질 것입니다.\n"
        
        # 실제 OpenAI API 호출 예시 (주석 처리)
        """
        prompt = f"다음 자소서를 분석하고 개선점을 제안해주세요:\n\n{resume_text}"
        if job_description:
            prompt += f"\n\n채용공고 내용:\n{job_description}"
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "당신은 자소서 분석 및 피드백 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )
        feedback = response.choices[0].message.content
        """
        
        return feedback
    
    except Exception as e:
        print(f"피드백 생성 중 오류 발생: {e}")
        return "피드백 생성에 실패했습니다. 다시 시도해주세요."
