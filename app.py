import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from io import BytesIO

import pandas as pd
import streamlit as st
from pypdf import PdfReader
from local_extract import parse_transcript_text, local_ocr_pdf
from engine import (mot_candidates, distribute, required_future_gpa, candidate_summary,
                    mot_restrictions, MOT_2025, MOT_2026, CBA_2024, PASS_GRADES,
                    cba_groups, cba_requirements, cba_checklist, suggest_classification, provisional_credit_audit)

CBA = 'https://cba.snu.ac.kr/academics/undergraduate/graduation/requirements'
MOT = 'https://mot.snu.ac.kr/course_regulation/'
SUGANG = 'https://sugang.snu.ac.kr/sugang/co/co100.action'
COLUMNS = ['과목번호', '과목명', '학점', '성적', '성적표상 구분', '검토 후 배정']


def future_semesters(today, count):
    # 현재 학기는 제외하고 다음 정규학기부터 배정한다.
    year, semester = (today.year, 1) if 3 <= today.month <= 8 else ((today.year, 2) if today.month >= 9 else (today.year - 1, 2))
    result = []
    for _ in range(count):
        if semester == 1:
            semester = 2
        else:
            year, semester = year + 1, 1
        result.append(f'{year}년 {semester}학기')
    return result


def sample_courses(kind):
    # 실제 학생의 성적표가 아닌 기능 확인용 가상 데이터
    rows = [
        ['251.101', '경영학원론', 3, 'A0', '전선', '주전공'],
        ['251.205', '회계원리', 3, 'B+', '일선', '검토 필요'],
        ['4251.002A', '기술경영 관련 예시', 3, 'A-', '일선', '검토 필요'],
        ['000.001', '교양 예시', 3, 'S', '교양', '교양'],
    ]
    if kind == '가상 학생 B':
        rows[0][3] = 'B0'
        rows.append(['000.002', '일반선택 예시', 3, 'A+', '일선', '일반선택'])
    if kind == '경영학 단일전공 예시':
        rows = [rows[0], rows[1], rows[3]]
    return pd.DataFrame(rows, columns=COLUMNS)


def extract_pdf(upload):
    if upload.size > 15_000_000:
        raise ValueError('PDF가 15MB를 초과합니다.')
    reader = PdfReader(BytesIO(upload.getvalue()))
    if len(reader.pages) > 20:
        raise ValueError('PDF가 20페이지를 초과합니다.')
    return '\n'.join(page.extract_text(extraction_mode='layout') or '' for page in reader.pages)


@st.cache_data(show_spinner=False)
def load_offerings():
    path = os.path.join(os.path.dirname(__file__), 'data', '2026-2.xls')
    frame = pd.read_excel(path, header=2, dtype=str, engine='xlrd').fillna('')
    if '교과목번호' not in frame.columns:
        raise ValueError('공식 강좌 목록의 과목번호 열을 찾지 못했습니다.')
    return frame


def init_state():
    if 'courses' not in st.session_state:
        st.session_state.courses = pd.DataFrame(columns=COLUMNS)
    if 'requirements' not in st.session_state:
        st.session_state.requirements = pd.DataFrame([
            ['주전공', '총 이수학점', 0.0, 0.0, '미확인'],
            ['주전공', '전공 이수학점', 0.0, 0.0, '미확인'],
            ['다전공', '전공 이수학점', 0.0, 0.0, '전공과 기준 확인 필요'],
        ], columns=['전공', '요건', '필요 학점', '인정 학점', '근거 및 확인 상태'])
    if 'plan' not in st.session_state:
        st.session_state.plan = pd.DataFrame(columns=['학기', '과목 또는 요건', '학점', '구분', '개설 확인'])


def graduation_home():
    st.title('졸업 에이전트')
    st.caption('서울대학교 졸업 요건과 이수 계획을 함께 검토합니다. 무료 분석에는 API 키가 필요하지 않습니다.')
    st.warning('공식 졸업사정 결과가 아닙니다. 학번별 요건, 교과구분 변경, 중복 인정 및 실제 개설 여부는 반드시 학과에 확인하세요.')
    with st.expander('시작하기 · 성적표 또는 가상 사례', expanded=True):
        sample = st.selectbox('연습용 사례', ['선택 안 함', '가상 학생 A', '가상 학생 B', '경영학 단일전공 예시'])
        if st.button('가상 사례 불러오기') and sample != '선택 안 함':
            st.session_state.courses = sample_courses(sample)
            st.session_state.pop('courses_editor', None)
            st.rerun()
        upload = st.file_uploader('성적증명서 PDF', type='pdf')
        method = st.selectbox('분석 방식', ['무료 · 텍스트 PDF', '무료 · 스캔 PDF OCR'])
        st.caption('웹앱을 운영하는 서버에서 파일을 처리하며 외부 AI 서비스로 전송하지 않습니다.')
        if upload and st.button('PDF 분석'):
            try:
                extracted = local_ocr_pdf(upload.getvalue()) if method == '무료 · 스캔 PDF OCR' else extract_pdf(upload)
                if len(extracted.strip()) < 30:
                    st.warning('텍스트가 충분히 읽히지 않았습니다. 스캔 파일이면 무료 OCR을 선택해 보세요.')
                else:
                    parsed = parse_transcript_text(extracted)
                    st.session_state.local_text = extracted
                    st.session_state.pop('local_raw_text', None)
                    st.session_state.local_unmatched = parsed['unmatched_lines']
                    st.session_state.profile = {'admission_year': parsed['admission_year'] or '', 'primary_major': '', 'other_majors': ''}
                    if parsed['courses']:
                        st.session_state.courses = pd.DataFrame(parsed['courses'], columns=COLUMNS)
                        st.session_state.pop('courses_editor', None)
                        st.success(f"{len(parsed['courses'])}개 행을 추출했습니다. 표와 원문을 비교해 누락 또는 오류를 수정하세요.")
                    else:
                        st.warning('자동 추출된 과목이 없습니다. 원문을 보고 직접 입력하세요. 기존 과목표는 유지됩니다.')
            except Exception as exc:
                st.error(f'분석하지 못했습니다: {exc}')
    if st.session_state.get('local_text'):
        with st.expander('무료 분석 원문 및 누락 확인'):
            st.caption('표 형식과 글자 인식에 따라 행이 누락될 수 있습니다. 한 줄에 과목번호와 성적이 있는 항목만 자동 추출합니다.')
            st.write('자동 추출에서 제외된 과목번호 포함 줄:', st.session_state.get('local_unmatched', []))
            st.text_area('PDF에서 읽은 원문', st.session_state.local_text, height=240, key='local_raw_text')
    if 'profile' in st.session_state:
        st.write('PDF에서 추출한 학적 정보:', st.session_state.profile)
        if st.button('추출한 학적 정보를 입력란에 적용'):
            profile = st.session_state.profile
            import re
            match = re.search(r'(?:19|20)\d{2}', str(profile.get('admission_year', '')))
            if match and 2018 <= int(match.group()) <= 2100:
                st.session_state.admission = int(match.group())
            if profile.get('primary_major'):
                st.session_state.major = str(profile['primary_major'])
            if profile.get('other_majors'):
                st.session_state.other = str(profile['other_majors'])
    cols = st.columns(3)
    cols[0].number_input('입학연도', 2018, 2100, 2024, key='admission', help='2018학번 이후를 대상으로 합니다. 경영학 자동 비교는 현재 2026학번까지 지원합니다.')
    cols[1].text_input('주전공', '경영학과', key='major')
    cols[2].text_input('다전공 및 선발연도', '연합전공 기술경영 / 선발연도 확인 필요', key='other')
    st.caption('추출된 학적 정보를 적용한 뒤 원본과 비교해 주세요.')
    st.subheader('이수 과목 검토')
    st.caption('일선은 자동 전공 인정하지 않습니다. 성적표상 구분을 유지하면서 검토 후 배정을 별도로 선택하세요. F·재수강·중복 과목은 직접 확인하세요.')
    st.session_state.courses = st.data_editor(st.session_state.courses, num_rows='dynamic', use_container_width=True, key='courses_editor', column_config={'검토 후 배정': st.column_config.SelectboxColumn(options=['검토 필요', '주전공', '다전공', '교양', '일반선택', '제외'])})
    if not st.session_state.courses.empty:
        completed = st.session_state.courses.copy()
        completed['학점'] = pd.to_numeric(completed['학점'], errors='coerce')
        valid = completed['성적'].fillna('').astype(str).str.strip().str.upper().isin(PASS_GRADES) & completed['학점'].gt(0)
        reviewed = completed[valid & completed['검토 후 배정'].isin(['주전공', '다전공', '교양', '일반선택'])]
        totals = reviewed.groupby('검토 후 배정')['학점'].sum()
        st.write('검토 후 배정 기준 학점 합계:', {str(k): float(v) for k, v in totals.items()})
        st.caption('선택한 과목과 통과 성적만 합산한 참고치입니다. 동일·재수강 과목과 교과구분 변경, 전공 간 중복은 자동 조정하지 않습니다.')
        codes = completed['과목번호'].fillna('').astype(str).str.strip().str.upper()
        if codes[codes.ne('')].duplicated().any():
            st.warning('과목번호가 반복됩니다. 재수강·중복 학점이 합계에 들어갔는지 확인하세요.')
        candidates = st.session_state.courses.copy()
        candidates['기술경영 2025 기준 일치 영역'] = candidates['과목번호'].apply(lambda code: ', '.join(mot_candidates(code)))
        st.dataframe(candidates[['과목번호', '과목명', '성적표상 구분', '기술경영 2025 기준 일치 영역']], hide_index=True, use_container_width=True)
        st.caption('과목번호 일치는 인정 후보이며, 이수구분 변경·중복인정·동일 교과목 제한은 확정되지 않았습니다.')
    with st.expander('확인된 공식 기준으로 살펴보기'):
        records = st.session_state.courses.to_dict('records')
        year = st.session_state.admission
        if cba_groups(year) and '경영' in st.session_state.major:
            required = cba_requirements(year, False)['주전공 필수']
            st.markdown(f'**경영학 {year} 입학자:** 총 130학점, 교양 36학점, 전공은 다전공 병행 시 39학점, 단일전공 시 60학점. 전공필수 {required}학점.')
            single = st.radio('전공 방식', ['다전공 병행', '단일전공'], horizontal=True, key='auto_mode') == '단일전공'
            audit, excluded = provisional_credit_audit(records, year, single)
            st.dataframe(pd.DataFrame(audit), hide_index=True, use_container_width=True)
            st.caption(f'전체 학점은 과목번호가 중복되지 않은 통과 과목만, 주전공·교양은 검토 후 배정을 선택한 과목만 계산합니다. 자동 계산에서 제외된 과목 {excluded}개. 재수강·동일과목과 대체 인정, 누락 과목에 따라 달라집니다.')
            st.dataframe(pd.DataFrame(candidate_summary(records, cba_groups(year), cba=True)), hide_index=True, use_container_width=True)
            st.caption('과목번호와 통과 성적의 단순 대조입니다. 동일·대체 과목, 전공 인정, 교양과 영어 및 평점 등은 별도 확인이 필요합니다.')
            st.markdown('**추가 정보로 졸업요건 확인**')
            st.caption('성적표 또는 학과 확인 결과의 숫자를 입력하세요. 입력하지 않은 요건은 미확인으로 남습니다. 전공필수 초과 학점의 전공선택 인정도 반영한 숫자를 입력하세요.')
            if st.button('과목표의 잠정 학점 합계를 확인값 입력란에 넣기', help='재수강, 교과구분과 과목 누락을 먼저 확인하세요.'):
                for row in audit:
                    target = {'전체': '총 취득학점', '교양': '교양 학점', '주전공': '주전공 학점'}[row['요건']]
                    st.session_state['fact_' + target] = float(row['검토 과목 합계'])
            labels = ['총 취득학점', '교양 학점', '주전공 학점', '주전공 필수', '주전공 선택', '전공 영어강좌 수', '전체 평점', '전공 평점', '등록 횟수']
            facts = {}
            cols2 = st.columns(3)
            for i, label in enumerate(labels):
                is_gpa = '평점' in label
                maximum = 4.3 if is_gpa else 250.0
                facts[label] = cols2[i % 3].number_input(label, min_value=0.0, max_value=maximum, value=None, step=0.1 if is_gpa else 1.0, key='fact_' + label)
            checks = cba_checklist(year, single, facts)
            st.dataframe(pd.DataFrame(checks), hide_index=True, use_container_width=True)
            if year >= 2025:
                st.info('교양 세부: 지성의 열쇠 3개 영역 이상 9학점, 베리타스 3학점, 체육실기 및 기초 필수과목 등을 확인해야 합니다.')
            elif year in (2023, 2024):
                st.info('교양 세부: 학문의 세계 4개 영역 이상 12학점(자연·기술 또는 생명·환경 3학점 포함), 체육실기 및 기초 필수과목 등을 확인해야 합니다.')
            else:
                st.info('교양 세부: 학문의 세계 3개 영역 이상 12학점(자연·기술 또는 생명·환경 3학점 포함), 체육실기 및 기초 필수과목 등을 확인해야 합니다.')
            st.caption('표의 충족은 입력값과 해당 숫자 기준만 대조한 결과입니다. 세부 요건과 입력값의 정확성을 포함한 최종 졸업사정은 학과에서 확인해야 합니다.')
        else:
            st.info('현재 자동 비교 가능한 경영학 주전공 기준은 2018~2026학번입니다. 다른 학번과 전공은 공식 기준을 확인해야 합니다.')
        version = st.selectbox('기술경영 적용 후보 기준', ['선택 안 함', '2025 기준 / 2026 영역변경 전', '2026 영역변경 후'])
        if version != '선택 안 함':
            rules = MOT_2026 if version == '2026 영역변경 후' else MOT_2025
            st.markdown('**기술경영:** 총 39학점, 전필 21학점과 전선 18학점, 평점 2.0 이상. 선발연도와 경과조치에 맞는 기준을 선택해야 합니다.')
            st.dataframe(pd.DataFrame(candidate_summary(records, rules)), hide_index=True, use_container_width=True)
            for group in mot_restrictions(records):
                st.warning(f'기술경영 학점 인정 제한 확인: {group}')
            st.caption('성적표상 일치는 인정 확정이 아닙니다. 변경 전·후 규정은 혼용할 수 없으며 동일·대체 과목과 이수구분, 중복인정을 확인해야 합니다.')
    st.subheader('졸업 요건 및 남은 학점')
    if st.session_state.admission == 2024 and '경영' in st.session_state.major:
        mode = st.radio('2024학번 경영학 전공 방식', ['다전공 병행', '단일전공'], horizontal=True)
        if st.button('2024학번 경영학 기준으로 요건 표 교체', help='현재 요건 표가 새 기준으로 교체됩니다.'):
            total = 60.0 if mode == '단일전공' else 39.0
            elective = 33.0 if mode == '단일전공' else 12.0
            st.session_state.requirements = pd.DataFrame([
                ['전체', '총 취득학점', 130.0, 0.0, '2024학번 원문 · 인정 학점 입력'],
                ['교양', '교양 학점', 36.0, 0.0, '2024학번 원문 · 세부 영역 별도 확인'],
                ['주전공', '경영학 전공 총학점', total, 0.0, '2024학번 원문'],
                ['주전공', '전공필수', 27.0, 0.0, '2024학번 원문 · 영역별 확인'],
                ['주전공', '전공선택', elective, 0.0, '전필 초과 인정 확인'],
            ], columns=st.session_state.requirements.columns)
            st.session_state.pop('requirements_editor', None)
            st.rerun()
    st.caption('주전공부터 입력하세요. 인정 학점은 중복 인정과 재수강을 확인한 뒤 직접 입력합니다. 0은 미입력으로 취급합니다.')
    st.session_state.requirements = st.data_editor(st.session_state.requirements, num_rows='dynamic', use_container_width=True, key='requirements_editor')
    req = st.session_state.requirements.copy()
    for col in ['필요 학점', '인정 학점']:
        req[col] = pd.to_numeric(req[col], errors='coerce').fillna(0)
    req['남은 학점'] = (req['필요 학점'] - req['인정 학점']).clip(lower=0).where(req['필요 학점'] > 0)
    st.dataframe(req, use_container_width=True, hide_index=True)
    st.info('요건 간 학점이 겹칠 수 있으므로 남은 학점의 합계를 졸업까지 필요한 총 학점으로 더하지 않습니다. 필수 과목과 비교과 요건은 행을 추가해 기록하세요.')
    st.markdown(f'**공식 자료:** [경영학과 학번별 졸업기준]({CBA}) · [기술경영 이수규정]({MOT}) · [수강신청 및 수강편람]({SUGANG})')


def semester_plan():
    st.title('학기별 계획')
    st.caption('현재 학기는 제외하고 다음 정규학기부터 계획합니다. 3~8월은 1학기, 9~다음 해 2월은 2학기입니다.')
    a, b, c = st.columns(3)
    count = a.number_input('계획할 학기 수', 1, 12, 4)
    cap = b.number_input('학기별 최대학점', 1, 30, 18)
    major_cap = c.number_input('학기별 전공학점 한도', 0, 30, 12)
    semesters = future_semesters(datetime.now(ZoneInfo('Asia/Seoul')).date(), count)
    st.write('계획 대상:', ', '.join(semesters))
    st.markdown('**자동 배분할 과목 또는 요건**')
    if 'plan_items' not in st.session_state:
        st.session_state.plan_items = pd.DataFrame(columns=['과목 또는 요건', '학점', '구분'])
    st.session_state.plan_items = st.data_editor(st.session_state.plan_items, num_rows='dynamic', key='items_editor', use_container_width=True, column_config={'구분': st.column_config.SelectboxColumn(options=['주전공', '다전공', '교양', '일반선택'])})
    if st.button('입력한 항목을 학기에 자동 배분'):
        try:
            assigned, pending = distribute(st.session_state.plan_items.to_dict('records'), semesters, cap, major_cap)
            st.session_state.plan = pd.DataFrame(assigned, columns=['학기', '과목 또는 요건', '학점', '구분', '개설 확인'])
            st.session_state.pop('plan_editor', None)
            st.session_state.pending_plan = pending
        except (ValueError, TypeError):
            st.error('각 항목의 학점에 숫자를 입력하세요.')
    if st.session_state.get('pending_plan'):
        st.warning(f"한도 안에서 배정하지 못한 항목: {len(st.session_state.pending_plan)}개")
        st.dataframe(pd.DataFrame(st.session_state.pending_plan), hide_index=True)
    st.session_state.plan = st.data_editor(st.session_state.plan, num_rows='dynamic', use_container_width=True, key='plan_editor', column_config={
        '학기': st.column_config.SelectboxColumn(options=semesters, required=True),
        '구분': st.column_config.SelectboxColumn(options=['주전공', '다전공', '교양', '일반선택']),
        '개설 확인': st.column_config.SelectboxColumn(options=['미확인', '확인함']),
    })
    plan = st.session_state.plan.copy()
    if not plan.empty:
        plan['학점'] = pd.to_numeric(plan['학점'], errors='coerce').fillna(0)
        plan['전공학점'] = plan['학점'].where(plan['구분'].isin(['주전공', '다전공']), 0)
        summary = plan.groupby('학기')[['학점', '전공학점']].sum().reindex(semesters, fill_value=0)
        st.bar_chart(summary)
        st.dataframe(summary, use_container_width=True)
        for term, row in summary.iterrows():
            if row['학점'] > cap or row['전공학점'] > major_cap:
                st.warning(f'{term}: 설정한 한도를 초과했습니다.')
        if (~plan['개설 확인'].eq('확인함')).any():
            st.info('미확인 과목은 수강편람에서 해당 학기 개설 여부를 확인하세요.')
    st.markdown(f'[서울대학교 수강신청 시스템 및 수강편람]({SUGANG})')
    with st.expander('공식 개설강좌 목록 검색'):
        st.caption('2026년 2학기 전체 강좌 목록 · 2026년 7월 3일 기준. 수업의 이후 변경은 반영되지 않으며 다른 학기 개설을 의미하지 않습니다.')
        st.markdown('[자료 출처와 기준일](https://gsep.snu.ac.kr/boards/notice/41324/detail/news/notice/?page=17&paginate_by=10) · [최신 강좌 확인](' + SUGANG + ')')
        query = st.text_input('과목번호 또는 과목명으로 검색')
        if query.strip():
            try:
                catalog = load_offerings()
                mask = catalog.astype(str).apply(lambda col: col.str.contains(query.strip(), case=False, regex=False)).any(axis=1)
                found = catalog.loc[mask]
                st.write(f'{len(found)}개 분반 검색됨')
                st.dataframe(found.head(100), hide_index=True, use_container_width=True)
                if len(found) > 100:
                    st.caption('처음 100개만 표시합니다. 검색어를 구체적으로 입력하세요.')
            except Exception as exc:
                st.error(f'강좌 목록을 읽지 못했습니다: {exc}')


def chatbot():
    st.title('학점 목표 상담')
    st.caption('평점에 포함되는 학점과 현재 평점을 직접 입력해 목표 달성에 필요한 앞으로의 평균을 계산합니다.')
    x, y, z = st.columns(3)
    credits = x.number_input('현재 평점 반영 학점', min_value=0.0, value=60.0, step=1.0)
    gpa = y.number_input('현재 평점', min_value=0.0, max_value=4.3, value=3.5, step=0.1)
    target = z.number_input('목표 평점', min_value=0.0, max_value=4.3, value=3.8, step=0.1)
    future = st.number_input('앞으로 평점에 반영될 학점', min_value=1.0, value=30.0, step=1.0)
    needed = required_future_gpa(credits, gpa, future, target)
    st.metric('필요한 향후 평균 평점', f'{max(0, needed):.2f} / 4.3')
    if needed > 4.3:
        st.warning('입력한 학점으로는 4.3 만점 기준 목표에 도달하기 어렵습니다.')
    st.caption('S/U, 재수강 및 성적 대체는 계산에 자동 반영되지 않습니다. 공식 성적표의 평점 반영 학점을 사용하세요.')
    st.subheader('무료 계획 도우미')
    topic = st.selectbox('무엇을 확인할까요?', ['목표 평점 달성 가능성', '졸업요건 확인 순서', '학기 계획 세우기', '일선·다전공 인정'])
    if topic == '목표 평점 달성 가능성':
        if needed > 4.3:
            st.write(f'예정된 {future:g}학점으로 목표를 이루려면 평균 {needed:.2f}점이 필요합니다. 4.3 만점 기준으로는 학점이나 목표를 조정해야 합니다.')
        else:
            st.write(f'예정된 {future:g}학점에서 평균 {max(needed, 0):.2f}점 이상이 필요합니다. 실제 성적과 재수강 반영 방식에 따라 달라질 수 있습니다.')
    elif topic == '졸업요건 확인 순서':
        st.write('졸업 현황에서 입학연도와 주전공을 확인한 다음, 총학점·전공필수 영역·교양·영어 및 다전공 요건 순서로 살펴보세요. 미확인 항목은 학과 원문과 비교해야 합니다.')
    elif topic == '학기 계획 세우기':
        st.write('학기별 계획에서 부족한 과목을 입력하고 학점 한도를 설정한 뒤 자동 배분하세요. 실제 개설, 시간표와 선수과목은 수강신청 시스템에서 확인해야 합니다.')
    else:
        st.write('일선으로 표시된 과목은 자동으로 전공학점에 포함되지 않습니다. 과목번호와 해당 전공의 인정 목록을 비교하고 교과구분 변경 및 중복인정을 확인하세요.')


def main():
    st.set_page_config(page_title='졸업 에이전트', page_icon='🎓', layout='wide')
    init_state()
    menu = st.sidebar.radio('메뉴', ['졸업 현황', '학기별 계획', '학점 목표 상담'])
    st.sidebar.caption('초안 · 입력 내용은 현재 브라우저 세션에만 유지됩니다.')
    export = {'courses': st.session_state.courses.to_dict('records'), 'requirements': st.session_state.requirements.to_dict('records'), 'plan': st.session_state.plan.to_dict('records')}
    st.sidebar.download_button('현재 자료 JSON 다운로드', json.dumps(export, ensure_ascii=False, default=str, indent=2), 'graduation-plan.json', 'application/json', help='민감한 성적 정보가 포함됩니다.')
    with st.sidebar.expander('저장 자료 불러오기'):
        saved = st.file_uploader('이 앱에서 저장한 JSON', type=['json'], key='restore_file')
        if saved and st.button('저장 자료로 교체'):
            try:
                if saved.size > 2_000_000:
                    raise ValueError('파일이 너무 큽니다.')
                data = json.loads(saved.getvalue())
                if not isinstance(data, dict):
                    raise ValueError('자료 형식이 올바르지 않습니다.')
                expected = {'courses': COLUMNS, 'requirements': ['전공', '요건', '필요 학점', '인정 학점', '근거 및 확인 상태'], 'plan': ['학기', '과목 또는 요건', '학점', '구분', '개설 확인']}
                restored = {}
                for name, columns in expected.items():
                    rows = data.get(name)
                    if not isinstance(rows, list) or len(rows) > 5000 or any(not isinstance(r, dict) or any(c not in r for c in columns) for r in rows):
                        raise ValueError(f'{name} 자료 형식이 올바르지 않습니다.')
                    restored[name] = pd.DataFrame(rows, columns=columns)
                for name, frame in restored.items():
                    st.session_state[name] = frame
                for key in ['courses_editor', 'requirements_editor', 'plan_editor']:
                    st.session_state.pop(key, None)
                st.rerun()
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                st.sidebar.error(f'불러오지 못했습니다: {exc}')
    if menu == '졸업 현황':
        graduation_home()
    elif menu == '학기별 계획':
        semester_plan()
    else:
        chatbot()


if __name__ == '__main__':
    main()
