import streamlit as st
import requests
import zipfile
import io
import os

st.set_page_config(page_title="PatchGuard-Local", layout="wide")

# 사이드바: 설정 영역
with st.sidebar:
    st.header("⚙️ 환경 설정 (Settings)")
    selected_lang = st.radio("출력 언어 선택 (Output Language)", ["한국어 (Korean)", "English"])
    
    st.markdown("---")
    st.header("📂 프로젝트 업로드")
    upload_type = st.radio("업로드 방식 선택", ["단일 파일 업로드", "프로젝트 ZIP 업로드"])
    
    uploaded_files = {}

    if upload_type == "단일 파일 업로드":
        single_file = st.file_uploader("코드 파일 선택", type=['py', 'js', 'java', 'html', 'sql', 'env'])
        if single_file:
            try:
                content = single_file.read().decode('utf-8', errors='ignore')
                uploaded_files[single_file.name] = content
            except Exception as e:
                st.error(f"파일 읽기 오류: {e}")

    else:
        zip_file = st.file_uploader("프로젝트 ZIP 파일 선택", type=['zip'])
        if zip_file:
            with zipfile.ZipFile(io.BytesIO(zip_file.read())) as z:
                ALLOWED_EXTENSIONS = ('.py', '.js', '.ts', '.html', '.java', '.cpp', '.c', '.sql', '.env', '.json')
                for file_info in z.infolist():
                    if file_info.is_dir() or any(p.startswith('.') for p in file_info.filename.split('/')):
                        continue
                    if 'node_modules' in file_info.filename or 'venv' in file_info.filename:
                        continue
                    
                    if file_info.filename.endswith(ALLOWED_EXTENSIONS):
                        try:
                            with z.open(file_info) as f:
                                content = f.read().decode('utf-8', errors='ignore')
                                uploaded_files[file_info.filename] = content
                        except Exception:
                            pass
            st.success(f"총 {len(uploaded_files)}개의 코드 파일 감지 완료!")

# 언어별 프롬프트 및 설정
if selected_lang == "한국어 (Korean)":
    SYSTEM_PROMPT = """[ROLE]
당신은 대한민국 최고의 소스코드 보안 분석가입니다.
사용자가 제공한 소스코드를 정적 분석하여 OWASP Top 10 기준 취약점(SQL 인젝션, XSS, 하드코딩된 API Key/Secret, 안전하지 않은 함수 등)을 탐지하고 시큐어 코딩 패치 코드를 제시해야 합니다.

[STRICT INSTRUCTION]
1. 모든 진단 결과, 취약점 설명, 패치 이유, 공격 시나리오를 반드시 '100% 한국어'로만 작성하십시오.
2. 영문 설명이나 영어 문장은 절대로 사용하지 마십시오 (코드 문법 자체를 제외한 모든 본문 텍스트는 한국어 필수).

[출력 양식]
### 1. 🛡️ 취약점 진단
- 발견된 취약점 명칭 및 위험도(High/Medium/Low)
- 취약 코드 라인 및 원인 설명 (한국어)

### 2. 💻 시큐어 코딩 패치 코드
- 보안 표준이 적용된 안전한 수정 코드 전체

### 3. ⚠️ 공격 시나리오 및 조치 팁
- 공격자가 이 취약점을 악용할 수 있는 시나리오와 예방 조치 (한국어)
"""
    title_text = "🛡️ PatchGuard-Local: 프로젝트 단위 취약점 진단"
    caption_text = "외부 통신 없는 로컬 환경에서 소스코드 및 ZIP 프로젝트를 일괄 분석하고 시큐어 패치를 제공합니다."
    btn_text = "🛡️ 이 파일 로컬 보안 진단 실행"
    spinner_text = "로컬 sLLM이 오프라인 분석 중..."
    success_text = "✅ 로컬 온디바이스 진단 완료 (외부 데이터 유출 0건)"
else:
    SYSTEM_PROMPT = """[ROLE]
You are an expert source code security analyst.
Analyze the provided code based on OWASP Top 10 vulnerabilities and propose secure patch code.

[STRICT INSTRUCTION]
Provide all explanations, causes, and scenarios entirely in English.

[Format]
### 1. 🛡️ Vulnerability Diagnosis
- Identified vulnerability name and severity (High/Medium/Low)
- Vulnerable line number and root cause

### 2. 💻 Secure Patch Code
- Fully refactored safe code block

### 3. ⚠️ Attack Scenario & Tips
"""
    title_text = "🛡️ PatchGuard-Local: Project-Level Vulnerability Scanner"
    caption_text = "Analyze source codes and ZIP projects entirely offline without external data leakage."
    btn_text = "🛡️ Run Local Security Diagnosis"
    spinner_text = "Local sLLM is analyzing offline..."
    success_text = "✅ Local On-Device Diagnosis Complete (Zero Data Leak)"

st.title(title_text)
st.caption(caption_text)

def analyze_with_local_llm(filename, code_content, prompt, lang):
    if lang == "한국어 (Korean)":
        user_message = f"반드시 한국어로만 답변해 주세요.\n\n[파일명: {filename}]\n[소스코드]:\n{code_content}\n\n위 코드를 분석하고 반드시 한국어로 진단 리포트를 작성하세요."
    else:
        user_message = f"[Filename: {filename}]\n[Source Code]:\n{code_content}"

    payload = {
        "model": "qwen2.5-coder:7b",
        "system": prompt,
        "prompt": user_message,
        "stream": False,
        "options": {
            "temperature": 0.2
        }
    }
    response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=90)
    if response.status_code == 200:
        return response.json().get("response", "")
    else:
        return f"분석 오류 (HTTP {response.status_code})"

if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = {}

# 메인 뷰
if not uploaded_files:
    st.info("👈 좌측 사이드바에서 개별 코드 파일 또는 프로젝트 ZIP 파일을 업로드해 주세요.")
else:
    # 1. 상단 컨트롤 바 (파일 선택 + 실행 버튼)
    top_col1, top_col2 = st.columns([3, 1])
    with top_col1:
        selected_filename = st.selectbox("분석할 파일 선택:", list(uploaded_files.keys()), label_visibility="collapsed")
    with top_col2:
        run_btn = st.button(btn_text, type="primary", use_container_width=True)

    file_code = uploaded_files[selected_filename]

    if run_btn:
        with st.spinner(f"`{selected_filename}` {spinner_text}"):
            try:
                result = analyze_with_local_llm(selected_filename, file_code, SYSTEM_PROMPT, selected_lang)
                st.session_state.analysis_results[selected_filename] = result
            except requests.exceptions.ConnectionError:
                st.error("❌ Ollama가 실행되어 있지 않습니다. 터미널에서 `ollama serve`를 켜주세요.")
            except Exception as e:
                st.error(f"오류 발생: {e}")

    st.markdown("---")

    # 2. 결과 뷰 (원문 코드 깨짐 방지: st.code 직접 출력)
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"📄 원본 코드 (`{selected_filename}`)")
        # 깨짐 없이 안전한 순수 코드 뷰어 (우측 상단 복사 및 마우스 스크롤 지원)
        st.code(file_code, language='python', line_numbers=True)

    with col2:
        st.subheader("🔍 진단 및 패치 결과")
        if selected_filename in st.session_state.analysis_results:
            st.markdown(st.session_state.analysis_results[selected_filename])
            st.success(success_text)
        else:
            st.info("상단의 진단 실행 버튼을 누르면 오프라인 보안 분석이 시작됩니다.")