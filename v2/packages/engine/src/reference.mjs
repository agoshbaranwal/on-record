// AUTO-EXTRACTED from instrument.html — the shipped algorithm, unmodified except that every
// wall-clock read is routed through NOW(). This is the reference the TypeScript port must match.
export function makeReference(NOW, LF) {
 const MONS=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
 function qtile(sorted,p){if(!sorted.length)return null;
  return sorted[Math.min(sorted.length-1,Math.floor(p/100*(sorted.length-1)))];}
 function dLabel(iso){var p=iso.split("-");
  return (+p[2])+" "+["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][+p[1]-1];}
 function compute(aj,fc,name){
  var d=aj.daily,N=d.time.length,date=d.time,tx=d.temperature_2m_max,tn=d.temperature_2m_min;
  var md={},annual={},oldTx=[],oldTn=[],i,y;
  for(i=0;i<N;i++){if(tx[i]==null)continue;y=+date[i].slice(0,4);
   var k=date[i].slice(5);(md[k]=md[k]||[]).push([y,tx[i]]);
   (annual[y]=annual[y]||[]).push(tx[i]);
   if(y>=1951&&y<=1980){oldTx.push(tx[i]);if(tn[i]!=null)oldTn.push(tn[i]);}}
  if(oldTx.length<3650)throw new Error("record too thin");
  oldTx.sort(function(a,b){return a-b;});oldTn.sort(function(a,b){return a-b;});
  var thrHot=Math.round(qtile(oldTx,95)*10)/10,thrNight=Math.round(qtile(oldTn,95)*10)/10;
  var cH={},cN={};
  for(i=0;i<N;i++){y=+date[i].slice(0,4);
   if(tx[i]!=null&&tx[i]>=thrHot)cH[y]=(cH[y]||0)+1;
   if(tn[i]!=null&&tn[i]>=thrNight)cN[y]=(cN[y]||0)+1;}
  function series(c){var out=[];for(var y2=1940;y2<=LF;y2++)out.push({year:y2,n:c[y2]||0});return out;}
  /* the window: 25 days back to 25 days ahead of today */
  var WN=51,anchorMs=NOW()-25*864e5,anchorISO=new Date(anchorMs).toISOString().slice(0,10);
  var labels=[],keys=[];
  for(i=0;i<WN;i++){var dd=new Date(anchorMs+i*864e5);
   labels.push(MONS[dd.getUTCMonth()]+" "+dd.getUTCDate());keys.push(dd.toISOString().slice(5,10));}
  var spag={},oldB=[],newB=[],env=[],lo=99,hi=-99;
  for(i=0;i<WN;i++){var rows=md[keys[i]]||[],olds=[],news=[],all=[];
   for(var r=0;r<rows.length;r++){var yy=rows[r][0],v=rows[r][1];
    var s=spag[yy];if(!s){s=spag[yy]=[];for(var z=0;z<WN;z++)s.push(null);}
    s[i]=Math.round(v*10)/10;all.push(v);
    if(yy>=1951&&yy<=1980)olds.push(v);
    if(yy>=LF-29&&yy<=LF)news.push(v);
    if(v<lo)lo=v;if(v>hi)hi=v;}
   function m2(a){if(!a.length)return null;var t2=0;for(var j=0;j<a.length;j++)t2+=a[j];
    return Math.round(t2/a.length*10)/10;}
   oldB.push(m2(olds));newB.push(m2(news));
   env.push(all.length?Math.round(Math.max.apply(null,all)*10)/10:null);}
  var ydom=[Math.floor((lo-2)/5)*5,Math.ceil((hi+2)/5)*5],ticks=[];
  for(i=ydom[0];i<=ydom[1];i+=5)ticks.push(i);
  /* annual anomaly vs the 1951-80 mean of annual means */
  var base=[],anom=[];
  for(y=1951;y<=1980;y++)if(annual[y]){var t3=0;
   for(i=0;i<annual[y].length;i++)t3+=annual[y][i];base.push(t3/annual[y].length);}
  var bmean=base.length?base.reduce(function(a,b){return a+b;},0)/base.length:0;
  for(y=1940;y<=LF;y++){if(annual[y]&&annual[y].length>300){var t4=0;
    for(i=0;i<annual[y].length;i++)t4+=annual[y][i];
    anom.push(Math.round((t4/annual[y].length-bmean)*100)/100);}else anom.push(0);}
  /* today against its own date */
  var todayISO=new Date(NOW()).toISOString().slice(0,10),tk=todayISO.slice(5);
  var exact=md[tk]||[],rec=null,recy=null;
  for(i=0;i<exact.length;i++)if(rec==null||exact[i][1]>rec){rec=exact[i][1];recy=exact[i][0];}
  var wvals=[];
  for(i=-7;i<=7;i++){var wd=new Date(NOW()+i*864e5).toISOString().slice(5,10);
   (md[wd]||[]).forEach(function(rv){wvals.push(rv[1]);});}
  wvals.sort(function(a,b){return a-b;});
  var pct=null;if(fc!=null&&wvals.length){var le=0;
   for(i=0;i<wvals.length;i++)if(wvals[i]<=fc)le++;
   pct=Math.min(100,Math.round(100*le/wvals.length));}
  return {V:{custom:true,place:name,anchorISO:anchorISO,ydom:ydom,ticks:ticks,
    RW:{labels:labels,spaghetti:spag,old_normal_1951_1980:oldB,new_normal_last30:newB,
        record_envelope:env,new_normal_label:(LF-29)+"–"+LF},
    S:{year0:1940,anom:anom},
    G:{days_ge35_per_year:series(cH),warm_nights_ge25_per_year:series(cN)},
    thr:{hot:thrHot,night:thrNight,
     hotLabel:"hotter than 95% of days here in 1951\u201380 (above "+thrHot.toFixed(1)+" °C)",
     nightLabel:"below "+thrNight.toFixed(1)+" °C \u2014 warmer than 95% of nights here in 1951\u201380"}},
   t:{mode:"live",tmax:fc,comparable:fc,dateISO:todayISO,dateLabel:dLabel(todayISO),
      fetched:todayISO,rec:rec,recy:recy,n:exact.length,pct:pct,   // null when this place has no same-date record — never synthesize a "0.0 °C" mark
      bias:0,h40a:0,h40b:0}};}
 return compute;
}
