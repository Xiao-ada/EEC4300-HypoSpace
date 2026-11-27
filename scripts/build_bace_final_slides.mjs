// Live Artifact Session callbacks. All content, tables and notes remain editable.
const FONT='Arial',INK='#17263B',BLUE='#23589F',GRAY='#536278';

function text(slide,value,x,y,w,h,size=26,bold=false,color=INK){
  const shape=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  shape.text=value;
  shape.text.style={typeface:FONT,fontSize:size,bold,color,alignment:'left',verticalAlignment:'top',autoFit:'none',wrap:'square',insets:0};
  return shape;
}
function heading(slide,title,subtitle){
  slide.background.fill='#FFFFFF';
  text(slide,title,60,36,1160,66,47,true);
  if(subtitle)text(slide,subtitle,60,111,1160,58,23,false,GRAY);
}
function notes(content,other){
  return content.sentences.map(v=>v[0]).join(' ')+'\n\n'+other;
}

export async function addPrinciple({presentation,input}){
  const c=input.slides[0];const s=presentation.slides.add({width:1280,height:720});
  heading(s,c.title,c.subtitle);
  const ys=[198,324,450];
  c.left.forEach(([label,value],i)=>{
    text(s,label,60,ys[i],410,36,27,true,BLUE);
    text(s,value,60,ys[i]+45,410,78,i===2?30:25,i===2);
  });
  text(s,'Generation process',530,196,690,42,29,true,BLUE);
  c.steps.forEach((step,i)=>text(s,`${i+1}   ${step}`,530,254+i*81,690,70,27));
  text(s,c.scope,60,636,1160,58,20,false,GRAY);
  s.speakerNotes.text=notes(c,'BACE masks token prefixes only when slack reaches zero. It tracks space-admissible structural classes, which may still violate observations. A finite grammar supplies 300 represented spellings across 33 classes during intervention. The model never receives the test reference set or observation-validator feedback. Coverage LoRA is the learned proposal, and the comparison isolates decoding, not superiority of its loss.\nSources: https://proceedings.mlr.press/v306/chen26bz.html\nhttps://aclanthology.org/2021.emnlp-main.779/\nhttps://arxiv.org/abs/2106.09685\nProject: docs/BACE_METHOD.md; explorer/target_decode.py; explorer/canonical_decode.py');
  return {slide:s.id};
}

export async function addResults({presentation,input}){
  const c=input.slides[1],s=presentation.slides.add({width:1280,height:720});
  heading(s,c.title,c.subtitle);
  const values=[c.columns,...input.resultRows];
  const table=s.tables.add({rows:4,columns:4,left:60,top:185,width:1160,height:216,columnWidths:[500,220,220,220],values});
  table.styleOptions={headerRow:false,bandedRows:false};
  table.borders.assign({fill:'#D8E1ED',width:.8,style:'solid'});
  for(let r=0;r<4;r++){
    table.rows[r].height=54;
    for(let col=0;col<4;col++){
      const cell=table.getCell(r,col);
      cell.fill=r===0?BLUE:r===2?'#EAF1FA':'#FFFFFF';
      cell.text.style={typeface:FONT,fontSize:'21pt',bold:r===0||r===2,color:r===0?'#FFFFFF':INK,alignment:col===0?'left':'center',verticalAlignment:'middle',insets:10};
    }
  }
  text(s,c.gain,60,430,1160,48,34,true,BLUE);
  text(s,c.interval,60,485,1160,36,25);
  text(s,c.cost,60,533,1160,36,25);
  text(s,c.learning,60,581,1160,36,24);
  text(s,c.scope,60,646,1160,55,19,false,GRAY);
  s.speakerNotes.text=notes(c,'Validity is the fraction of attempts satisfying observations and the common space gate. Uniqueness counts distinct space-admissible structural keys, including observation-invalid structures. Recovery uses the full official compatible-reference set. All 16 attempts count. The selected checkpoint is coverage continuation +80. It is identical in both LLM rows. The no-LLM row uses uniform class proposals with the same BACE rule. Three seeds are inference repetitions, not independent training runs. The tasks had already appeared in earlier experiments, so the bootstrap intervals describe an exploratory follow-up. The gain does not prove that the added coverage training loss beats matched SFT.\nSources: https://github.com/Xiao-ada/EEC4300-HypoSpace/blob/main/results/canonical_preference_v5/test/summary.json\nProject: docs/OPTIMIZATION_RESULTS_ZH.md; results/optimization_group_packet.json');
  return {slide:s.id,table:table.id};
}

export async function addSupplement({presentation,input}){
  const c=input.slides[2],s=presentation.slides.add({width:1280,height:720});
  heading(s,c.title,'');
  text(s,c.body[0],80,225,1120,140,35,true,BLUE);
  text(s,c.body[1],80,405,1120,150,32);
  s.speakerNotes.text=notes(c,'Supplementary evidence: the LLM-scored catalog without COVE reaches 37.07% recovery at N=K. COVE plus the LLM and COVE alone both reach 99.27% recovery. The common comparison demonstrates learned-executor benefit over LLM catalog scoring, but no incremental final-metric benefit from the LLM. The paper uses N=K in most experiments. The catalog contains 33 classes and candidates never undergo free autoregressive generation in this pipeline. Do not describe its scores as native LLM capability or replace the BACE table with them.\nSource: https://github.com/Xiao-ada/EEC4300-HypoSpace/blob/main/results/all80/test/summary.json');
  return {slide:s.id};
}
