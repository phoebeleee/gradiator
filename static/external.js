(function(root){
'use strict';
const thresholds={general:{teps:[374,600],toeic:[900,990],toefl_old:[105,120],toefl_new:[5,6]},speaking:{teps_s:[67,100],toeic_s:[160,200],toefl_old:[20,30],toefl_new:[4,6],opic:[3,5]},writing:{teps_w:[67,100],toeic_w:[160,200],toefl_old:[20,30],toefl_new:[4,6]}};
function examResult(section,type,score,expiry,year,term){
 const limit=thresholds[section]&&thresholds[section][type];
 if(!type||score===''||!expiry||!year||!term)return {state:'unknown',text:'시험, 점수, 유효기간, 졸업 신청 학기를 입력해 주세요.'};
 if(!limit||!Number.isFinite(Number(score))||Number(score)<0||Number(score)>limit[1]||!/^\d{4}-\d{2}-\d{2}$/.test(expiry)||Number(year)<2018||Number(year)>2100||!['1','2'].includes(String(term)))return {state:'unknown',text:'입력값을 확인해 주세요.'};
 const start=`${year}-${String(term)==='1'?'03-01':'09-01'}`;
 if(expiry<=start)return {state:'fail',text:`유효기간이 신청 학기 시작일 ${start} 이후가 아닙니다.`};
 if(Number(score)<limit[0])return {state:'fail',text:`기준 미달: ${type==='opic'?'IM3 이상':limit[0]+'점 이상'}이 필요합니다.`};
 return {state:'pass',text:'입력한 점수와 유효기간 기준 충족 · 증빙 제출 및 학교 확인 필요'};
}
root.GradExternal={examResult};
if(typeof module!=='undefined'&&module.exports){module.exports=root.GradExternal;return;}
const $=id=>document.getElementById(id);
const sections=[['general','영어시험',[['','시험 선택'],['teps','NEW TEPS'],['toeic','TOEIC'],['toefl_old','TOEFL iBT 종전 총점 /120'],['toefl_new','TOEFL iBT 새 총점 /6']]],['speaking','말하기',[['','시험 선택'],['teps_s','TEPS Speaking'],['toeic_s','TOEIC Speaking'],['toefl_old','TOEFL iBT 종전 Speaking /30'],['toefl_new','TOEFL iBT 새 Speaking /6'],['opic','OPIc']]],['writing','쓰기',[['','시험 선택'],['teps_w','TEPS Writing'],['toeic_w','TOEIC Writing'],['toefl_old','TOEFL iBT 종전 Writing /30'],['toefl_new','TOEFL iBT 새 Writing /6']]]];
const manual=[['liberalEnglish','입학 시 영어 교양 이수 기준'],['liberalAreas','교양 세부 영역 및 필수과목'],['majorGpa','전공 평점 및 전체 평점'],['statistics','통계학·통계학실험 이수 및 예외'],['overlapApproval','전공 간 중복인정 승인'],['thesis','기술경영 졸업논문 등 별도 요건']];
$('examInputs').innerHTML=sections.map(([id,label,opts])=>`<div class="area"><div><strong>${label}</strong><div class="controls"><div class="field"><label for="${id}Type">시험 종류</label><select id="${id}Type">${opts.map(([v,t])=>`<option value="${v}">${t}</option>`).join('')}</select></div><div class="field" id="${id}ScoreField"><label for="${id}Score">점수</label><input id="${id}Score" type="number" min="0" step="any" placeholder="미입력"></div><div class="field hidden" id="${id}OpicField"><label for="${id}Opic">OPIc 등급</label><select id="${id}Opic"><option value="">선택</option><option value="0">IL 이하</option><option value="1">IM1</option><option value="2">IM2</option><option value="3">IM3</option><option value="4">IH</option><option value="5">AL 이상</option></select></div><div class="field"><label for="${id}Expiry">유효기간 종료일</label><input id="${id}Expiry" type="date"></div></div><div id="${id}Result" class="muted"></div></div></div>`).join('');
$('manualInputs').innerHTML=manual.map(([id,label])=>`<div class="field" id="${id}Field"><label for="${id}">${label}</label><select id="${id}"><option value="">미확인</option><option value="yes">학교 기준 확인·충족</option><option value="no">미충족 또는 추가 확인 필요</option><option value="na">해당 없음 확인</option></select></div>`).join('');
const ids=['gradYear','gradTerm','registered','englishClasses',...sections.flatMap(([id])=>[id+'Type',id+'Score',id+'Opic',id+'Expiry']),...manual.map(([id])=>id)];
function getValues(){return Object.fromEntries(ids.map(id=>[id,$(id).value]));}
function setValues(values={}){for(const id of ids)$(id).value=typeof values[id]==='string'||typeof values[id]==='number'?String(values[id]):'';render();}
function render(){const single=$('track').value==='single',mot=$('mot').value==='yes';const n=$('registered').value,eng=$('englishClasses').value;let messages=[];if(n==='')messages.push('등록 학기: 미입력');else if(!Number.isInteger(Number(n))||Number(n)<0||Number(n)>30)messages.push('등록 학기 입력값을 확인하세요.');else messages.push(`등록 학기: ${n}학기 · ${Number(n)>=6&&Number(n)<=16?'6~16학기 범위':'6~16학기 요건 확인 필요'} (예외 및 휴학 확인)`);const goal=single?5:3;if(eng==='')messages.push(`전공 영어강좌: 미입력 · 기준 ${goal}과목`);else if(!Number.isInteger(Number(eng))||Number(eng)<0||Number(eng)>100)messages.push('영어강좌 수를 확인하세요.');else messages.push(`전공 영어강좌: ${eng}/${goal}과목 · ${Number(eng)>=goal?'입력 기준 충족':'추가 이수 필요'}`);$('basicChecks').textContent=messages.join(' / ');
 for(const [id] of sections){let type=$(id+'Type').value;$(id+'ScoreField').classList.toggle('hidden',type==='opic');$(id+'OpicField').classList.toggle('hidden',type!=='opic');const score=$(id+(type==='opic'?'Opic':'Score')).value;const result=examResult(id,type,score,$(id+'Expiry').value,$('gradYear').value,$('gradTerm').value);$(id+'Result').textContent=({pass:'입력 기준 충족',fail:'추가 확인 필요',unknown:'미확인'})[result.state]+' — '+result.text;}
 $('thesisField').classList.toggle('hidden',!mot);$('overlapApprovalField').classList.toggle('hidden',!mot);const relevant=manual.filter(([id])=>mot||!['thesis','overlapApproval'].includes(id));const unknown=relevant.filter(([id])=>!$(id).value).length,nonpass=relevant.filter(([id])=>$(id).value==='no').length;$('manualResults').textContent=`미확인 ${unknown}개 · 추가 확인 필요 ${nonpass}개. 직접 입력한 확인 내용이며 학교의 최종 판정이 아닙니다.`;}
for(const id of ids){$(id).addEventListener('input',render);$(id).addEventListener('change',render);}
$('track').addEventListener('change',render);$('mot').addEventListener('change',render);
root.GradExternal={examResult,getValues,setValues,render};render();
})(typeof window!=='undefined'?window:globalThis);
