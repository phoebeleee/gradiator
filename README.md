# 졸업 에이전트

서울대학교 경영학과 2018~2026학번의 졸업요건 및 수강계획을 검토하는 Streamlit 웹앱입니다. 공식 졸업사정 결과가 아닙니다.

## 무료 웹 배포

Streamlit Community Cloud에서 GitHub 저장소를 연결하고 앱 파일을 `app.py`, Python 버전을 3.12로 지정합니다. 저장소에 `app.py`, `engine.py`, `local_extract.py`, `requirements.txt`, `packages.txt`, `data/2026-2.xls`가 모두 있어야 합니다. `packages.txt`가 서버에 Tesseract와 한국어·영어 OCR 데이터를 설치합니다. 개인 API 키나 유료 AI 연결은 필요하지 않습니다. 무료 서비스의 처리 속도, 자원 한도 및 휴면 정책은 서비스 제공자에 따릅니다.

웹앱은 사용자의 브라우저가 아니라 배포 서버에서 PDF 및 OCR을 처리합니다. 성적표를 외부 AI API로 보내지 않습니다. 자료는 세션에 보관되며 다운로드한 JSON 외 별도 데이터베이스에 저장하지 않습니다. 공용 서비스로 공개한다면 운영자는 접근 제어와 개인정보 처리방침을 마련해야 합니다.

## 무료 사용법

1. 성적표가 텍스트 PDF라면 `무료 · 텍스트 PDF`를, 이미지로 스캔된 PDF라면 `무료 · 스캔 PDF OCR`을 선택합니다.
2. 읽은 과목과 원문을 대조하고 학번·전공, 교과구분, 불명확하거나 누락된 내용을 수정합니다.
3. 졸업요건과 계획을 확인하고 JSON으로 저장합니다. 무료 계획 도우미와 평점 계산기는 `학점 목표 상담` 메뉴에 있습니다.

무료 추출은 정해진 형식의 행을 찾는 방식입니다. 한 줄에 과목번호와 성적이 없는 항목, 표가 복잡한 PDF, 흐린 스캔은 빠지거나 잘못 읽힐 수 있습니다. 원문 검토가 필수입니다. 무료 상담은 정해진 질문을 다루며 GPT 자유 대화가 아닙니다.

경영학 2018~2026학번의 총학점·전공필수 영역을 잠정 비교합니다. 교양 세부 영역, 재수강, 일선 전공 인정, 중복인정, 다전공 전체 요건과 실제 졸업사정은 확정하지 않습니다. 2026년 2학기 수업 목록은 2026년 7월 3일 기준의 자료이며 최신 개설 상황은 수강신청 시스템에서 확인해야 합니다. 근거는 `학교_기준_정리.md`에 정리되어 있습니다.

## 로컬 실행

Python 3.12와 Tesseract OCR, 한국어·영어 언어 데이터가 필요합니다. [Tesseract 설치 안내](https://tesseract-ocr.github.io/tessdoc/Installation.html)를 참고하세요.

```bash
pip install -r requirements.txt
streamlit run app.py
```

Docker를 쓰는 경우 `docker build -t graduation-agent .` 후 `docker run --rm -p 8501:8501 graduation-agent`를 실행합니다.

```bash
python -m unittest test_engine test_local_extract test_app_integration -v
```
