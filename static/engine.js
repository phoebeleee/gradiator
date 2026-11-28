(function(root){
'use strict';
const PASS = new Set(['A+','A0','A-','B+','B0','B-','C+','C0','C-','D+','D0','D-','S','P']);
const FAILED = new Set(['F','U','W']);
const GRADES = {'A+':4.3,'A0':4.0,'A-':3.7,'B+':3.3,'B0':3.0,'B-':2.7,'C+':2.3,'C0':2.0,'C-':1.7,'D+':1.3,'D0':1,'D-':0.7,'F':0};
const CBA = [
  ['경영학과 나의 미래',1,['M2171.002000']],
  ['경영을 위한 경제학',3,['M2171.001900']],
  ['회계 영역',3,['251.205','251.306']],
  ['운영 영역',3,['M1338.003000','251.207A']],
  ['조직 영역',3,['251.209','251.303','M1338.004000']],
  ['경영정보론',3,['251.326']],['재무관리',3,['251.301']],
  ['마케팅관리',3,['251.321']],['경영전략',3,['251.424']],
  ['졸업 세미나',2,['M1338.002600']]
];
const MOT25 = [
 ['경제경영원론',1,'200.105 200.106 212.201 212.202 251.332 M2171.001900 400.015'],
 ['재무/회계',1,'251.204A 251.205 251.301 251.323 406.314 406.433'],
 ['제품·서비스전략',1,'251.321 251.327 251.411A 406.304 406.326 M1505.001500'],
 ['조직과 리더십',1,'212.317 212.472 M1338.004000 M1338.004100 251.303 251.424 406.211'],
 ['의사결정방법론',1,'212.301 251.207A 326.311 406.311 406.315 406.317 406.426B 406.429 406.432'],
 ['기술경영',2,'4251.002A M1338.003000 251.744 400.310 406.310 406.319 406.322 406.324A M1522.002700 463.509 M1338.000400 M1540.000100']
];
const MOT26 = [
 ['경제경영원론',1,'200.105 200.106 212.201 212.202 251.332 M2171.001900'],
 ['재무/회계',1,'251.204A 251.205 251.301 251.323 406.314 406.433 251.306 251.422'],
 ['제품서비스개발',1,'251.321 251.327 251.411A 406.304 406.326 M1505.001500 406.322 400.015 406.310 M1338.003000'],
 MOT25[3],
 ['의사결정방법론',1,'212.301 251.207A 326.311 406.311 406.315 406.317 406.426B 406.429 406.432 M2177.005800'],
 ['기술경영',2,'4251.002A 400.310 406.319 406.324A M1522.002700 463.509 M1338.000400 M1540.000100 M1540.000200 M1540.000300 M1540.000400 M1540.000500']
];
const MOT18 = [
 ['경제경영원론',1,'200.105 200.106 212.201 212.202 251.101 251.103 400.015'],
 MOT25[1],
 ['제품·서비스전략',1,'251.321 251.327 406.304 406.320 406.326 406.430'],
 ['조직과 리더십',1,'212.317 212.472 251.209 251.215 251.303 251.424 406.211 M2177.000700'],
 ['의사결정방법론',1,'212.301 251.207A 326.311 406.311 406.315 406.317 406.429 406.432'],
 ['기술경영',2,'4251.002A 251.320 251.744 400.310 406.310 406.319 406.322 406.324A 4190.315 463.509 M1338.000400 M1338.000200']
];
const MOT21 = [MOT18[0],MOT18[1],['제품·서비스전략',1,'251.321 251.327 406.304 406.320 406.326 M1505.001500'],['조직과 리더십',1,'212.317 212.472 251.209 251.215 251.303 251.424 406.211 M2177.000500'],MOT18[4],['기술경영',2,'4251.002A 251.320 251.744 400.310 406.310 406.319 406.322 406.324A M1522.002700 463.509 M1338.000400 M1540.000100']];
const MOT22 = [MOT18[0],MOT18[1],['제품·서비스전략',1,'251.321 251.327 251.411A 406.304 406.320 406.326 M1505.001500'],MOT21[3],MOT25[4],MOT25[5]];
const MOT23 = [['경제경영원론',1,'200.105 200.106 212.201 212.202 251.101 M2171.001900 400.015'],MOT18[1],MOT25[2],['조직과 리더십',1,'212.317 212.472 251.209 251.215 251.303 251.424 406.211'],MOT25[4],MOT25[5]];
const MOT24 = [MOT23[0],MOT18[1],MOT25[2],['조직과 리더십',1,'212.317 212.472 251.209 M1338.004100 251.303 251.424 406.211'],MOT25[4],MOT25[5]];
const ALIASES={'경영학과나의미래':'M2171.002000','경영을위한경제학':'M2171.001900','경영철학과윤리':'M2171.002100','회계원리':'251.205','관리회계':'251.306','생산서비스운영':'M1338.003000','경영과학':'251.207A','조직행위론':'251.209','조직행동론':'M1338.004000','인사관리':'251.303','경영정보론':'251.326','재무관리':'251.301','마케팅관리':'251.321','경영전략':'251.424','졸업세미나':'M1338.002600','지식경영전략':'4251.002A'};
function normalizedName(s){return String(s||'').replace(/\(영어(?:강의)?\)?$/i,'').replace(/[\s·\-()\[\]]/g,'').toLowerCase();}
function exactCodes(name,catalog){const n=normalizedName(name),codes=new Set();for(const [label,arr] of Object.entries(catalog||{}))if(normalizedName(label)===n)for(const c of arr)codes.add(c);return [...codes];}
function resolveName(name,catalog,termCatalog){const n=normalizedName(name);const byTerm=exactCodes(name,termCatalog);if(byTerm.length===1)return byTerm[0];if(byTerm.length>1)return '';if(ALIASES[n])return ALIASES[n];const codes=exactCodes(name,catalog);return codes.length===1?codes[0]:'';}
function candidateCourses(name,catalog){const n=normalizedName(name);if(n.length<2)return [];let matches=[];for(const [label,codes] of Object.entries(catalog||{})){const full=normalizedName(label);if(full===n||(n.length>=5&&full.startsWith(n))){for(const code of codes)matches.push({name:label,code,exact:full===n});}}matches.sort((a,b)=>Number(b.exact)-Number(a.exact)||a.name.localeCompare(b.name,'ko')||a.code.localeCompare(b.code));return matches.slice(0,20);}
function cbaRules(y){
 if(y<2018||y>2026)return null;
 const rules=CBA.map(x=>({name:x[0],credits:x[1],codes:[...x[2]]}));
 if(y<2024)rules.splice(1,0,{name:'경영철학과 윤리',credits:3,codes:['M2171.002100']});
 if(y<=2020)rules.find(x=>x.name==='운영 영역').codes.push('251.320');
 if(y<=2022)rules.find(x=>x.name==='조직 영역').codes=['251.209','M1338.004000','251.303'];
 return rules;
}
function motRules(v){const selected={'2018':MOT18,'2021':MOT21,'2022':MOT22,'2023':MOT23,'2024':MOT24,'2025':MOT25,'2026후':MOT26}[v];if(!selected)return [];return selected.map(([name,count,codes])=>({name,count,codes:codes.split(' ')}));}
function newCourse(code='',name='',credits='',grade='',original='',group='검토 필요'){return {id:Math.random().toString(36).slice(2),code,name,credits,grade,original,group,include:true};}
function reconstructPage(items){
 const cats=/^(?:교양|전필|전선|일선|연전|부전|복전|복필|복선|연계|교직|설계)$/;
 const anchors=[];for(const it of items){if(!cats.test(String(it.str||'').trim()))continue;const x=it.transform[4];let a=anchors.find(v=>Math.abs(v.x-x)<4);if(a)a.count++;else anchors.push({x,count:1});}
 const cols=anchors.filter(a=>a.count>=3).sort((a,b)=>a.x-b.x);
 const toLines=its=>{let gs=[];for(const it of its){if(!it.str||!it.str.trim())continue;let x=it.transform[4],y=it.transform[5],g=gs.find(v=>Math.abs(v.y-y)<3);if(!g){g={y,items:[]};gs.push(g);}g.items.push({x,text:it.str});}return gs.sort((a,b)=>b.y-a.y).map(g=>({y:g.y,items:g.items.sort((a,b)=>a.x-b.x),text:g.items.sort((a,b)=>a.x-b.x).map(z=>z.text).join(' ').replace(/\s+/g,' ').trim()}));};
 if(cols.length<2||cols.some((c,i)=>i&&c.x-cols[i-1].x<65))return toLines(items).map(l=>l.text).join('\n');
 const firstCourseY=Math.max(...items.filter(i=>cats.test(String(i.str||'').trim())).map(i=>i.transform[5]));
 const head=toLines(items.filter(i=>i.transform[5]>firstCourseY+15)).map(l=>l.text);
 const body=items.filter(i=>i.transform[5]<=firstCourseY+15);let lines=[];
 for(let j=0;j<cols.length;j++){
  const left=j?cols[j].x-5:-Infinity,right=j+1<cols.length?cols[j+1].x-5:Infinity;
  const rows=toLines(body.filter(i=>i.transform[4]>=left&&i.transform[4]<right));let out=[];
  for(const row of rows){const previous=out[out.length-1];const continuation=previous&&previous.course&&previous.y-row.y>2&&previous.y-row.y<15&&row.items.length&&row.items.every(x=>x.x>=cols[j].x+18&&x.x<cols[j].x+112)&&!/\d|학년도|학기|학\s*점|평\s*점|[：:]/.test(row.text);
   if(continuation){previous.text=previous.text.replace(/(\s+\d(?:\.0)?\s+(?:[ABCD](?:[+0-])?|[FSPU]))$/i,(suffix,_,offset,whole)=>{const before=whole.slice(0,offset);return (/[A-Za-z]$/.test(before)&&/^[A-Za-z]/.test(row.text)?' ':'')+row.text+suffix;});previous.y=row.y;}
   else out.push({text:row.text,y:row.y,course:/^(?:교양|전필|전선|일선|연전|부전|복전|복필|복선|연계|교직|설계)\s+.+\s+\d(?:\.0)?\s+(?:[ABCD](?:[+0-])?|[FSPU])$/i.test(row.text)});
  }lines.push(...out.map(x=>x.text));
 }return [...head,...lines].join('\n');
}
function parseText(text,catalog={},history={}){
 const lines=text.split(/\r?\n/);let rows=[], unresolved=[],term='';
 const codeRe=/(?<![A-Za-z0-9])(?:[A-Z]\d{2,5}\.\d{3,6}[A-Z]?|\d{3,4}\.\d{3,4}[A-Z]?)(?![A-Za-z0-9])/gi;
 const gradeRe=/(?:^|\s)([ABCD](?:[+0-])?|F|S|P|U|W)(?=\s|$)/gi;
 for(let n=0;n<lines.length;n++){
  const line=lines[n].replace(/\s+/g,' ').trim();const semester=line.match(/(20\d{2})\s*학년도\s*제?\s*([12SW])\s*학기/i);if(semester)term=semester[1]+'-'+semester[2].toUpperCase();const codes=[...line.matchAll(codeRe)];
  if(!codes.length){
   const categoryLine=/(?:^|\s)(교양|전필|전선|일선|연전|부전|복전|복필|복선|연계|교직|설계)\s+((?:(?!\s(?:교양|전필|전선|일선|연전|부전|복전|복필|복선|연계|교직|설계)\s).)+?)\s+(\d(?:\.0)?)\s+([ABCD](?:[+0-])?|[FSPU])(?=\s|$)/gi;
   for(const m of line.matchAll(categoryLine)){let original=m[1],name=m[2].trim(),grade=m[4].toUpperCase();if(['A','B','C','D'].includes(grade))grade+='0';let group=original==='교양'?'교양':['전필','전선'].includes(original)?'경영학':original==='일선'?'일반선택':original==='연전'&&text.includes('기술경영')?'기술경영':'검토 필요';let row=newCourse(resolveName(name,catalog,history[term]),name,Number(m[3]),grade,original,group);row.term=term;row.codeInferred=!!row.code;rows.push(row);}
   continue;
  }
  if(codes.length!==1){unresolved.push(n+1);continue;}
  const code=codes[0];let rest=line.slice(code.index+code[0].length).trim();const grades=[...rest.matchAll(gradeRe)];
  const grade=grades.length===1?grades[0][1].toUpperCase():'';
  let before=grades.length===1?rest.slice(0,grades[0].index).trim():rest;
  let cat=line.match(/주전공|본전공|복수전공|부전공|연합전공|연계전공|전공필수|전공선택|전필|전선|연전|일반선택|일선|교양/);
  let nums=[...before.matchAll(/(?<![\w.])(?:[0-9]|1[0-2])(?:\.0)?(?![\w.])/g)];
  let credits=nums.length===1?Number(nums[0][0]):'';
  let name=before.replace(/(?<![\w.])(?:[0-9]|1[0-2])(?:\.0)?(?![\w.])/g,' ').replace(/주전공|본전공|복수전공|부전공|연합전공|연계전공|전공필수|전공선택|전필|전선|연전|일반선택|일선|교양/g,' ').replace(/\s+/g,' ').trim();
  let original=cat?cat[0]:'';let group=original==='교양'?'교양':['주전공','본전공','전필','전선','전공필수','전공선택'].includes(original)?'경영학':original==='일선'||original==='일반선택'?'일반선택':original==='연전'&&text.includes('기술경영')?'기술경영':'검토 필요';
  let row=newCourse(code[0].toUpperCase(),name,credits,grade,original,group);row.term=term;rows.push(row);
  if(!grade||credits==='')unresolved.push(n+1);
 }
 const year=text.match(/(?:학번|입학년도|입학연도|입학\s*연도)\s*[:：]?\s*((?:19|20)\d{2})/);
 return {rows,year:year?Number(year[1]):null,unresolved};
}
function norm(r){let grade=String(r.grade||'').trim().toUpperCase();if(['A','B','C','D'].includes(grade))grade+='0';return {...r,code:String(r.code||'').trim().toUpperCase(),grade,credits:Number(r.credits)};}
function audit(rows,year,single,mot,motVersion,catalog={}){
 const cba=cbaRules(year); if(!cba)return {error:'2018~2026학번 경영대학 기준만 지원합니다.'};
 let eligible=[], valid=[], unresolved=[], dup={};
 for(const raw of rows){const r=norm(raw);if(!r.include)continue;const identity=r.code||normalizedName(r.name);if(!identity||!Number.isFinite(r.credits)||r.credits<=0||r.credits>12||(!PASS.has(r.grade)&&!FAILED.has(r.grade))){unresolved.push(r);continue;}r.identity=identity;dup[identity]=(dup[identity]||0)+1;eligible.push(r);}
 const duplicateCodes=Object.keys(dup).filter(k=>dup[k]>1); eligible=eligible.filter(r=>{if(dup[r.identity]>1){unresolved.push(r);return false;}return true;});valid=eligible.filter(r=>PASS.has(r.grade));
 const total=valid.reduce((a,r)=>a+r.credits,0), liberal=valid.filter(r=>r.group==='교양').reduce((a,r)=>a+r.credits,0), primary=valid.filter(r=>r.group==='경영학'||r.group==='양쪽 인정').reduce((a,r)=>a+r.credits,0), tech=valid.filter(r=>r.group==='기술경영'||r.group==='양쪽 인정').reduce((a,r)=>a+r.credits,0);
 const pCourses=valid.filter(r=>r.group==='경영학'||r.group==='양쪽 인정'); const mCourses=valid.filter(r=>r.group==='기술경영'||r.group==='양쪽 인정');
 const names=new Map();function match(r,codes){if(codes.includes(r.code))return {...r,matchKind:r.codeInferred?'inferred_code':'code'};if(!names.has(r.name))names.set(r.name,exactCodes(r.name,catalog));const alternatives=names.get(r.name).filter(c=>codes.includes(c));return alternatives.length?{...r,matchKind:'same_name',requiredCodes:alternatives}:null;}
 let areas=cba.map(g=>{let matches=pCourses.map(r=>match(r,g.codes)).filter(Boolean);if(g.name==='경영을 위한 경제학'&&valid.some(r=>r.code==='200.105')&&valid.some(r=>r.code==='200.106'))matches=[{code:'200.105 + 200.106',credits:0}];return {...g,matches,missing:matches.length===0};});
 const required=year>=2024?27:30; const primaryGoal=single?60:39; const rules=motRules(motVersion);
 // A course fills at most one required area; use an augmenting-path matching
 // so shared course lists cannot make one course satisfy several requirements.
 const slots=[];if(mot)rules.forEach((g,area)=>{for(let i=0;i<g.count;i++)slots.push({area,edges:mCourses.map((r,index)=>({index,match:match(r,g.codes)})).filter(x=>x.match).sort((a,b)=>(a.match.matchKind==='code'?0:1)-(b.match.matchKind==='code'?0:1))});});
 const occupied=new Map(),slotMatch=new Map();function assign(si,seen){for(const edge of slots[si].edges){if(seen.has(edge.index))continue;seen.add(edge.index);const previous=occupied.get(edge.index);if(previous===undefined||assign(previous,seen)){occupied.set(edge.index,si);slotMatch.set(si,edge.match);return true;}}return false;}
 slots.forEach((_,i)=>assign(i,new Set()));
 const motAreas=mot?rules.map((g,area)=>{const matches=slots.flatMap((s,i)=>s.area===area&&slotMatch.has(i)?[slotMatch.get(i)]:[]);return {...g,matches,missing:Math.max(0,g.count-matches.length)};}):[];
 const primaryRequired=areas.reduce((sum,area)=>sum+(area.matches.length?Math.min(area.credits,Math.max(...area.matches.map(m=>m.credits))):0),0);
 const motRequired=motAreas.reduce((sum,area)=>sum+area.matches.slice().sort((a,b)=>b.credits-a.credits).slice(0,area.count).reduce((x,r)=>x+Math.min(3,r.credits),0),0);
 const primaryElective=Math.max(0,primary-primaryRequired), techElective=Math.max(0,tech-motRequired);
 const restrictions=[['200.105','200.106','M2171.001900'],['M1338.003000','406.310'],['251.207A','406.315']].filter(g=>g.every(c=>mCourses.some(r=>r.code===c)));
 const graded=eligible.filter(r=>Object.prototype.hasOwnProperty.call(GRADES,r.grade));const gpaCredits=graded.reduce((s,r)=>s+r.credits,0); const gpa=gpaCredits?graded.reduce((s,r)=>s+r.credits*GRADES[r.grade],0)/gpaCredits:null;
 const sameNameMatches=[...areas,...motAreas].flatMap(area=>area.matches.filter(r=>r.matchKind==='same_name').map(r=>({...r,area:area.name})));
 const overlapCount=valid.filter(r=>r.group==='양쪽 인정').length;
 return {total,liberal,primary,tech,primaryRequired,primaryElective,motRequired,techElective,primaryRequiredRemaining:Math.max(0,required-primaryRequired),primaryElectiveRemaining:Math.max(0,primaryGoal-required-primaryElective),motRequiredRemaining:mot?Math.max(0,21-motRequired):0,motElectiveRemaining:mot?Math.max(0,18-techElective):0,totalRemaining:Math.max(0,130-total),liberalRemaining:Math.max(0,36-liberal),primaryRemaining:Math.max(0,primaryGoal-primary),techRemaining:mot?Math.max(0,39-tech):0,primaryGoal,required,areas,motAreas,unresolved,duplicateCodes,restrictions,gpa,gpaCredits,valid,sameNameMatches,overlapCount};
}
function semesters(today,n){let d=new Date(today),y=d.getFullYear(),m=d.getMonth()+1,s=(m>=3&&m<=8)?1:2;if(m<3)y--;let a=[];for(let i=0;i<n;i++){if(s===1)s=2;else{y++;s=1;}a.push(`${y}년 ${s}학기`);}return a;}
function plan(audit,terms,cap,majorCap){
 if(audit.error)return {terms:[],pending:[]};
 let tasks=[],prim=0,tech=0,lib=0;
 for(const area of audit.areas.filter(x=>x.missing)){tasks.push({name:area.name+' (택1)',credits:area.credits,group:'경영학',options:area.codes.join(' / '),type:'필수영역'});prim+=area.credits;}
 for(const area of audit.motAreas)for(let i=0;i<area.missing;i++){tasks.push({name:'기술경영 · '+area.name+' (택1)',credits:3,group:'기술경영',options:area.codes.join(' / '),type:'필수영역'});tech+=3;}
 function fill(name,group,need){while(need>0){const cr=Math.min(3,need);tasks.push({name,credits:cr,group,options:'',type:'학점 채우기'});need-=cr;}}
 const addPrimaryRequired=Math.max(0,audit.primaryRequiredRemaining-prim);fill('경영학 전공필수 추가 확인','경영학',addPrimaryRequired);prim+=addPrimaryRequired;
 const addMotRequired=Math.max(0,audit.motRequiredRemaining-tech);fill('기술경영 전공필수 추가 확인','기술경영',addMotRequired);tech+=addMotRequired;
 fill('경영학 전공 선택 또는 추가', '경영학',Math.max(0,audit.primaryRemaining-prim,audit.primaryElectiveRemaining));
 fill('기술경영 전공 선택 또는 추가', '기술경영',Math.max(0,audit.techRemaining-tech,audit.motElectiveRemaining));
 fill('교양 영역 확인', '교양',audit.liberalRemaining);lib=audit.liberalRemaining;
 const anticipated=tasks.reduce((s,t)=>s+t.credits,0);fill('졸업 총학점 보충', '일반선택',Math.max(0,audit.totalRemaining-anticipated));
 let result=terms.map(term=>({term,credits:0,major:0,tasks:[]})),pending=[];
 for(const task of tasks){const isMajor=['경영학','기술경영'].includes(task.group);let slot=result.find(t=>t.credits+task.credits<=cap&&t.major+(isMajor?task.credits:0)<=majorCap);if(!slot)pending.push(task);else{slot.tasks.push(task);slot.credits+=task.credits;if(isMajor)slot.major+=task.credits;}}
 return {terms:result,pending,generated:tasks};
}
root.GradEngine={PASS,GRADES,cbaRules,motRules,newCourse,parseText,reconstructPage,audit,semesters,plan,candidateCourses};
if(typeof module!=='undefined'&&module.exports)module.exports=root.GradEngine;
})(typeof window!=='undefined'?window:globalThis);
