# 🛡️ PatchGuard-Local

온디바이스(로컬) AI 기반 소스코드 보안 취약점 진단 및 시큐어 코딩 패치 도구 (WIP / 프로토타입 단계)

## 📌 주요 특징
- **Zero Data Leak**: 외부 API 전송 없이 로컬 경량 모델(Ollama)을 활용한 오프라인 분석
- **프로젝트 단위 진단**: 단일 파일 및 ZIP 프로젝트 압축 파일 지원
- **다국어 지원**: 한국어 / 영어 리포트 지원

## 🚀 실행 방법
1. Ollama 실행 및 모델 다운로드:
   ```bash
   ollama run qwen2.5-coder:7b

필요 패키지 설치:
   pip install streamlit requests
   
앱 실행:
   python -m streamlit run app.py
