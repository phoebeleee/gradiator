"""성적표의 로컬 추출과 OCR. 추출 결과는 반드시 원본과 비교한다."""
import io
import re
import shutil
import subprocess
from collections import Counter

from engine import suggest_classification

CODE = re.compile(r'(?<![A-Za-z0-9])(?:[A-Z]\d{2,5}\.\d{4,6}[A-Z]?|\d{3,4}\.\d{3,4}[A-Z]?)(?![A-Za-z0-9])', re.I)
GRADE = re.compile(r'(?<![A-Z0-9])(?:[ABCD][+0-]|[FSU])(?![A-Z0-9])', re.I)
CATEGORY = re.compile(r'주전공\s*(?:전공)?\s*(?:필수|선택)?|복수전공|부전공|연합전공|연계전공|전공필수|전공선택|전필|전선|일반선택|일선|교양')
YEAR = re.compile(r'(?:학번|입학년도|입학연도|입학\s*연도)\s*[:：]?\s*((?:19|20)\d{2})(?:\s*[-–]\s*\d+)?')


def parse_transcript_text(text):
    """한 줄에 과목번호·성적이 있는 행만 추출한다. 누락 학점은 빈 값."""
    lines = text.splitlines()
    courses = []
    unmatched = []
    for line_no, raw in enumerate(lines, 1):
        line = ' '.join(raw.strip().split())
        if not line:
            continue
        codes = list(CODE.finditer(line))
        if not codes:
            continue
        if len(codes) != 1:
            unmatched.append(line_no)
            continue
        code = codes[0]
        # 성적표 맨 끝의 최종 성적만 사용한다. 두 성적이 있으면 추측하지 않는다.
        grades = list(GRADE.finditer(line[code.end():]))
        if len(grades) != 1:
            unmatched.append(line_no)
            continue
        grade = grades[0]
        before_grade = line[code.end():code.end() + grade.start()].strip()
        cat = CATEGORY.search(line)
        numbers = list(re.finditer(r'(?<![A-Za-z0-9.])(?:[0-9]|1[0-2])(?:\.0)?(?![A-Za-z0-9.])', before_grade))
        # 학점/이론/실습 등 여러 숫자는 확정하지 않는다.
        credit = float(numbers[-1].group()) if len(numbers) == 1 else None
        name = before_grade
        if cat:
            name = name.replace(cat.group(), ' ')
        if numbers:
            name = re.sub(r'(?<![A-Za-z0-9.])(?:[0-9]|1[0-2])(?:\.0)?(?![A-Za-z0-9.])', ' ', name)
        name = ' '.join(name.split()).strip(' -|:')
        classification = cat.group().strip() if cat else ''
        courses.append({'과목번호': code.group().upper(), '과목명': name, '학점': credit,
                        '성적': grade.group().upper(), '성적표상 구분': classification,
                        '검토 후 배정': suggest_classification(classification), '원본 줄': line_no})
    match = YEAR.search(text)
    return {'admission_year': int(match.group(1)) if match else None, 'courses': courses, 'unmatched_lines': unmatched}


def local_ocr_pdf(data, max_pages=20):
    """PDF를 메모리에서 렌더링하고 OCR에 표준입력으로 전달한다."""
    binary = shutil.which('tesseract')
    if not binary:
        raise RuntimeError('무료 OCR 실행 프로그램 Tesseract와 한국어 언어 데이터를 설치해 주세요. README를 참고하세요.')
    if len(data) > 15_000_000:
        raise ValueError('PDF가 15MB를 초과합니다.')
    langs = subprocess.run([binary, '--list-langs'], capture_output=True, text=True, timeout=15, check=True)
    if 'kor' not in langs.stdout.split() or 'eng' not in langs.stdout.split():
        raise RuntimeError('Tesseract 한국어(kor) 및 영어(eng) 언어 데이터가 필요합니다.')
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument(data)
    try:
        if len(pdf) > max_pages:
            raise ValueError(f'PDF가 {max_pages}페이지를 초과합니다.')
        pages = []
        for index in range(len(pdf)):
            page = pdf[index]
            bitmap = page.render(scale=2.5)
            try:
                buffer = io.BytesIO()
                bitmap.to_pil().save(buffer, format='PNG')
                completed = subprocess.run([binary, 'stdin', 'stdout', '-l', 'kor+eng', '--psm', '6'], input=buffer.getvalue(), capture_output=True, timeout=120)
                if completed.returncode:
                    raise RuntimeError('OCR이 페이지를 처리하지 못했습니다. 언어 설치와 PDF 상태를 확인하세요.')
                pages.append(completed.stdout.decode('utf-8', errors='replace'))
            finally:
                bitmap.close()
                page.close()
        return '\n'.join(pages)
    finally:
        pdf.close()
