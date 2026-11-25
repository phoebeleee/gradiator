"""공식 자료에서 확인한 제한된 범위의 계산. 미확인 사항은 승인으로 취급하지 않는다."""
from datetime import date

MOT_2025 = {
    '경제경영원론': ('200.105 200.106 212.201 212.202 251.332 M2171.001900 400.015', 1),
    '재무/회계': ('251.204A 251.205 251.301 251.323 406.314 406.433', 1),
    '제품·서비스전략': ('251.321 251.327 251.411A 406.304 406.326 M1505.001500', 1),
    '조직과 리더십': ('212.317 212.472 M1338.004000 M1338.004100 251.303 251.424 406.211', 1),
    '의사결정방법론': ('212.301 251.207A 326.311 406.311 406.315 406.317 406.426B 406.429 406.432', 1),
    '기술경영': ('4251.002A M1338.003000 251.744 400.310 406.310 406.319 406.322 406.324A M1522.002700 463.509 M1338.000400 M1540.000100', 2),
}

def future_semesters(today, count):
    year, semester = (today.year, 1) if 3 <= today.month <= 8 else ((today.year, 2) if today.month >= 9 else (today.year - 1, 2))
    output = []
    for _ in range(count):
        year, semester = (year, 2) if semester == 1 else (year + 1, 1)
        output.append(f'{year}년 {semester}학기')
    return output

def mot_candidates(code):
    code = str(code).strip().upper()
    return [name for name, (codes, _) in MOT_2025.items() if code in codes.split()]

def mot_summary(rows):
    # 같은 과목은 영역별 중복에 대한 공식 승인 없이 자동 확정하지 않는다.
    result = []
    for name, (codes, minimum) in MOT_2025.items():
        matches = sorted({str(r.get('과목번호', '')).strip().upper() for r in rows if str(r.get('성적', '')).strip().upper() in ('A+', 'A0', 'A-', 'B+', 'B0', 'B-', 'C+', 'C0', 'C-', 'D+', 'D0', 'D-', 'S') and str(r.get('과목번호', '')).strip().upper() in codes.split()})
        result.append({'영역': name, '필요 과목 수': minimum, '일치 과목': ', '.join(matches), '남은 과목 수(잠정)': max(0, minimum - len(matches))})
    return result

def required_future_gpa(credits, current, future, target):
    if future <= 0:
        raise ValueError('향후 학점은 0보다 커야 합니다.')
    return (target * (credits + future) - credits * current) / future

def distribute(items, semesters, cap, major_cap):
    """과목 단위 계획 초안. 자리 부족은 미배정으로 남긴다."""
    loads = {s: [0.0, 0.0] for s in semesters}
    assigned, pending = [], []
    for item in items:
        credits = float(item['학점'])
        if credits <= 0:
            pending.append(item)
            continue
        major = item.get('구분') in ('주전공', '다전공')
        for term in semesters:
            total, maj = loads[term]
            if total + credits <= cap and maj + (credits if major else 0) <= major_cap:
                loads[term] = [total + credits, maj + (credits if major else 0)]
                assigned.append(dict(item, 학기=term, **{'개설 확인': '미확인'}))
                break
        else:
            pending.append(item)
    return assigned, pending

# 2024학번 경영대학 공식 졸업요건의 전공필수 영역.
CBA_2024 = {
    '기초 1 · 경영학과 나의 미래': ['M2171.002000'],
    '기초 2 · 경영을 위한 경제학': ['M2171.001900'],
    '각론 1 · 회계': ['251.205', '251.306'],
    '각론 2 · 운영': ['M1338.003000', '251.207A'],
    '각론 3 · 조직': ['251.209', 'M1338.004000', '251.303'],
    '각론 4 · 정보': ['251.326'],
    '각론 5 · 재무': ['251.301'],
    '각론 6 · 마케팅': ['251.321'],
    '각론 7 · 전략': ['251.424'],
    '졸업세미나': ['M1338.002600'],
}
MOT_2026 = dict(MOT_2025)
MOT_2026.update({
    '경제경영원론': ('200.105 200.106 212.201 212.202 251.332 M2171.001900', 1),
    '재무/회계': ('251.204A 251.205 251.301 251.323 406.314 406.433 251.306 251.422', 1),
    '제품서비스개발': ('251.321 251.327 251.411A 406.304 406.326 M1505.001500 406.322 400.015 406.310 M1338.003000', 1),
    '의사결정방법론': ('212.301 251.207A 326.311 406.311 406.315 406.317 406.426B 406.429 406.432 M2177.005800', 1),
    '기술경영': ('4251.002A 400.310 406.319 406.324A M1522.002700 463.509 M1338.000400 M1540.000100 M1540.000200 M1540.000300 M1540.000400 M1540.000500', 2),
})
MOT_2026.pop('제품·서비스전략')
PASS_GRADES = {'A+', 'A0', 'A-', 'B+', 'B0', 'B-', 'C+', 'C0', 'C-', 'D+', 'D0', 'D-', 'S'}

def candidate_summary(rows, groups, cba=False):
    passed = {str(r.get('과목번호', '')).strip().upper() for r in rows if str(r.get('성적', '')).strip().upper() in PASS_GRADES and r.get('검토 후 배정') != '제외'}
    out = []
    for name, definition in groups.items():
        codes, needed = (definition, 1) if cba else (definition[0].split(), definition[1])
        matches = passed.intersection(codes)
        if cba and name.startswith('기초 2') and {'200.105', '200.106'}.issubset(passed):
            matches.add('200.105 + 200.106')
        out.append({'영역': name, '필요 과목 수': needed, '성적표상 일치 과목': ', '.join(sorted(matches)), '부족 가능 과목 수': max(0, needed - len(matches)), '후보 과목번호': ', '.join(codes)})
    return out

def mot_restrictions(rows):
    codes = {str(r.get('과목번호', '')).strip().upper() for r in rows if str(r.get('성적', '')).strip().upper() in PASS_GRADES and r.get('검토 후 배정') != '제외'}
    warnings = []
    for group in [{'200.105','200.106','M2171.001900'}, {'M1338.003000','406.310'}, {'251.207A','406.315'}]:
        if group.issubset(codes):
            warnings.append(' / '.join(sorted(group)))
    return warnings

def cba_groups(year):
    if year not in range(2018, 2027):
        return None
    groups = {k: list(v) for k, v in CBA_2024.items()}
    if year < 2024:
        groups['기초 · 경영철학과 윤리'] = ['M2171.002100']
    if year <= 2020:
        groups['각론 2 · 운영'].append('251.320')
    if year <= 2022:
        groups['각론 3 · 조직'] = ['251.209', '251.303']
    return groups


def cba_requirements(year, single):
    if year not in range(2018, 2027):
        return None
    required = 27 if year >= 2024 else 30
    return {'총 취득학점': 130, '교양 학점': 36,
            '주전공 학점': 60 if single else 39,
            '주전공 필수': required,
            '주전공 선택': (60 if single else 39) - required,
            '전공 영어강좌 수': 5 if single else 3}


def suggest_classification(classification):
    text = str(classification).strip().replace(' ', '')
    if '교양' in text:
        return '교양'
    if text in ('일선', '일반선택'):
        return '검토 필요'
    if any(x in text for x in ('주전공', '본전공')):
        return '주전공'
    if any(x in text for x in ('복수전공', '부전공', '연합전공', '연계전공')):
        return '다전공'
    return '검토 필요'


def provisional_credit_audit(rows, year, single):
    """확인된 과목만 합산. 중복 과목은 어느 쪽도 자동 반영하지 않는다."""
    groups = cba_groups(year)
    if groups is None:
        return None
    codes = [str(r.get('과목번호', '')).strip().upper() for r in rows]
    counts = {c: codes.count(c) for c in set(codes) if c}
    totals = {'전체': 0.0, '교양': 0.0, '주전공': 0.0}
    excluded = 0
    for row, code in zip(rows, codes):
        grade = str(row.get('성적', '')).strip().upper()
        try:
            credit = float(row.get('학점', 0))
        except (TypeError, ValueError):
            excluded += 1
            continue
        if not code or counts[code] > 1 or grade not in PASS_GRADES or not 0 < credit <= 12 or row.get('검토 후 배정') == '제외':
            excluded += 1
            continue
        totals['전체'] += credit
        if row.get('검토 후 배정') in ('교양', '주전공'):
            totals[row['검토 후 배정']] += credit
    minimum = {'전체': 130, '교양': 36, '주전공': 60 if single else 39}
    return [{'요건': key, '기준 학점': minimum[key], '검토 과목 합계': totals[key], '남은 학점(잠정)': max(0, minimum[key] - totals[key])} for key in minimum], excluded

def cba_checklist(year, single, facts):
    """학생이 확인한 값과 공식 기준을 대조하며, 미입력 값은 미확인으로 남긴다."""
    rules = cba_requirements(year, single)
    if rules is None:
        return []
    checks = []
    def minimum(label, fact, limit, unit):
        value = facts.get(fact)
        status = '미확인' if value is None else ('충족' if value >= limit else '부족')
        remain = '' if value is None else max(0, limit - value)
        checks.append({'요건': label, '기준': f'{limit}{unit} 이상', '입력': '미입력' if value is None else f'{value}{unit}', '상태': status, '부족': remain})
    for name in ('총 취득학점', '교양 학점', '주전공 학점', '주전공 필수', '주전공 선택'):
        minimum(name, name, rules[name], '학점')
    minimum('전공 영어강좌', '전공 영어강좌 수', rules['전공 영어강좌 수'], '과목')
    minimum('전체 평점', '전체 평점', 2.0, '점')
    minimum('전공 평점', '전공 평점', 2.0, '점')
    registrations = facts.get('등록 횟수')
    checks.append({'요건': '등록 횟수', '기준': '6~16회', '입력': '미입력' if registrations is None else str(registrations), '상태': '미확인' if registrations is None else ('충족' if 6 <= registrations <= 16 else '확인 필요'), '부족': ''})
    for item in ('교양 필수·영역 세부', '유효한 영어·말하기·쓰기 성적', '동일·대체 및 재수강', '다전공 요건'):
        checks.append({'요건': item, '기준': '별도 확인', '입력': '', '상태': '미확인', '부족': ''})
    return checks
