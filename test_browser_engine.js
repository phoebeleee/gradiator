'use strict';
const assert=require('node:assert/strict');
const E=require('./static/engine.js');
function row(code,credits,grade,group){return E.newCourse(code,code,credits,grade,'',group);}
const rows=[row('251.205',3,'A0','경영학'),row('4251.002A',3,'B+','기술경영'),row('000.001',3,'S','교양'),row('251.301',3,'F','경영학'),row('251.321',3,'A0','양쪽 인정')];
const a=E.audit(rows,2024,false,true,'2025');
assert.equal(a.total,12);assert.equal(a.primary,6);assert.equal(a.tech,6);assert.equal(a.liberal,3);
assert.equal(a.primaryRequired,6);assert.equal(a.totalRemaining,118);assert.equal(a.primaryRemaining,33);assert.equal(a.techRemaining,33);
assert.equal(a.gpaCredits,12);assert.ok(Math.abs(a.gpa-2.825)<1e-8);
const double=E.audit([...rows,row('251.205',3,'A0','경영학')],2024,false,true,'2025');assert.ok(double.duplicateCodes.includes('251.205'));assert.equal(double.total,9);
const justOne=E.audit([row('000.100',3,'A0','일반선택')],2024,true,false,'unknown');assert.equal(justOne.total,3);assert.equal(justOne.primary,0);assert.equal(justOne.primaryRemaining,60);
const terms=E.semesters('2026-08-31T12:00:00',2);assert.deepEqual(terms,['2026년 2학기','2027년 1학기']);
const result=E.plan(a,['one','two'],18,12);assert.ok(result.pending.length>0);result.terms.forEach(t=>{assert.ok(t.credits<=18);assert.ok(t.major<=12)});
const parsed=E.parseText('학번: 2024-12345\n전필 M2171.002000 경영학과 나의 미래 1 A0\n일선 251.205 회계원리 3 B+\n교양 000.001 교양 예시 3 S');assert.equal(parsed.year,2024);assert.equal(parsed.rows.length,3);assert.equal(parsed.rows[1].group,'일반선택');assert.equal(parsed.rows[1].credits,3);
const multi=E.parseText('학번: 2022-00000 기술경영\n전필 회계원리 3 A+ 교양 공개교양 3 A 연전 지식경영전략 3 B+\n일선 번호없는과목 2 S',{});assert.equal(multi.rows.length,4);assert.equal(multi.rows[0].code,'251.205');assert.equal(multi.rows[0].group,'경영학');assert.equal(multi.rows[1].grade,'A0');assert.equal(multi.rows[2].group,'기술경영');assert.equal(E.audit(multi.rows,2022,false,true,'2021').total,11);
const numbered=E.parseText('기술경영\n연전 4251.002A 지식경영전략 3 B');assert.equal(numbered.rows[0].group,'기술경영');assert.equal(E.audit(numbered.rows,2022,false,true,'2024').total,3);
const teaching=E.parseText('교양 F37.204 컴퓨팅 3 A');assert.equal(teaching.rows[0].code,'F37.204');
const catalog={'임의 테스트 과목':['F37.204','L0444.000500'],'회계원리':['251.205']};assert.equal(E.parseText('전필 회계원리(영어강의) 3 A',catalog).rows[0].code,'251.205');assert.deepEqual(E.candidateCourses('임의 테스트',catalog).map(x=>x.code),['F37.204','L0444.000500']);assert.equal(E.parseText('교양 임의 테스트 과목 3 A',catalog).rows[0].code,'');
assert.deepEqual(E.candidateCourses('통계학',{'통계학':['A01.001','B01.001'],'통계학교육':['C01.001']}).map(x=>x.code),['A01.001','B01.001']);
const item=(str,x,y)=>({str,transform:[1,0,0,1,x,y]});
const multiColumn=[item('학번: 2022-12345 기술경영',0,180),item('2022학년도 제1학기',26,105),
 item('교양',0,90),item('첫 번째 과목',26,90),item('3',114,90),item('A+',128,90),
 item('교양',0,70),item('두 번째 과목',26,70),item('3',114,70),item('A',128,70),
 item('교양',0,50),item('세 번째로 긴',26,50),item('3',114,50),item('B+',128,50),item('과목 이름',26,40),
 item('2022학년도 제2학기',176,105),item('연전',150,90),item('네 번째 과목',176,90),item('3',264,90),item('A+',278,90),
 item('교양',150,70),item('다섯 번째 과목',176,70),item('3',264,70),item('A',278,70),
 item('교양',150,50),item('여섯 번째 과목',176,50),item('3',264,50),item('S',278,50)];
const columnText=E.reconstructPage(multiColumn), columnParsed=E.parseText(columnText,{'첫 번째 과목':['111.111','222.222']},{'2022-1':{'첫 번째 과목':['111.111']}});
assert.equal(columnParsed.rows.length,6);assert.equal(columnParsed.rows[0].code,'111.111');assert.equal(columnParsed.rows[0].term,'2022-1');assert.equal(columnParsed.rows[2].name,'세 번째로 긴과목 이름');assert.equal(columnParsed.rows[3].term,'2022-2');assert.equal(columnParsed.rows[3].group,'기술경영');assert.equal(E.audit(columnParsed.rows,2022,false,true,'2024').total,18);
assert.ok(E.cbaRules(2022).find(x=>x.name==='조직 영역').codes.includes('M1338.004000'));
assert.equal(E.cbaRules(2026).length,10);assert.equal(E.cbaRules(2018).length,11);assert.equal(E.cbaRules(2027),null);
assert.ok(E.motRules('2026후').find(x=>x.name==='제품서비스개발').codes.includes('M1338.003000'));
console.log('credit audit, cohort rules, privacy-sensitive parsing, repeated courses, GPA and scheduling: passed');
