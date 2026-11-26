// Live Artifact Session callback. The supplied metrics remain the frozen v1 data.
export default async function authorEnglishSlide({presentation,input}) {
 const FONT='Arial Unicode MS',BLUE='#23589F',INK='#17263B',GRAY='#536278';
 function text(slide,value,x,y,w,h,size=24,bold=false,color=INK){
  const shape=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  shape.text=value;
  shape.text.style={typeface:FONT,fontSize:size,bold,color,alignment:'left',verticalAlignment:'top',autoFit:'none',wrap:'square',insets:0};
  return shape;
 }
 function heading(slide,title,subtitle){
  slide.background.fill='#FFFFFF';
  text(slide,title,60,38,1160,65,48,true);
  text(slide,subtitle,60,108,1160,44,24,false,GRAY);
 }
 const slide=presentation.slides.add({width:1280,height:720});
 if(input.phase===1){
  heading(slide,'Canonical Coverage LoRA','A training objective for hypothesis recovery');
  text(slide,'Motivation and related work',60,176,440,42,29,true,BLUE);
  text(slide,'HypoSpace (2026)',60,231,440,36,25,true);
  text(slide,'Valid outputs can still cover\nonly a few hypotheses.',60,272,440,64,24);
  text(slide,'GAPO (2025)',60,344,440,36,25,true);
  text(slide,'Group-level rewards can\nencourage output diversity.',60,385,440,64,24);
  text(slide,'Our approach',60,466,440,36,25,true,BLUE);
  text(slide,'Use official structure classes\nto optimize a coverage surrogate.',60,509,440,86,25);
  text(slide,'Coverage-aware supervised training',560,176,660,42,29,true,BLUE);
  text(slide,'qₖ = Σ Pθ(h ∣ O),  h ∈ Aₖ',560,237,660,54,32);
  text(slide,'C₁₆ = (1/K) Σₖ [1 − (1 − qₖ)¹⁶]',560,313,660,58,32);
  text(slide,'L = L_SFT − C₁₆',560,391,660,54,32,true,BLUE);
  text(slide,'Aₖ: two verified complete forms, including EOS\nK: valid reference classes. O: observations\nC₁₆: finite-pool coverage lower bound for IID draws',560,467,660,89,23);
  text(slide,'LoRA adapts a small set of parameters.\nContribution: structural classes in the coverage objective.',560,570,660,74,23);
  text(slide,'References: Chen et al., HypoSpace (ICML 2026). Anschel et al., GAPO (EMNLP 2025). Hu et al., LoRA.',60,661,1160,36,16,false,GRAY);
 }else if(input.phase===2){
  heading(slide,'Results and Contribution','4-bit Qwen2.5-1.5B-Instruct, 16 train / 6 validation / 26 test observation sets');
  const table=slide.tables.add({rows:6,columns:4,left:60,top:178,width:700,height:318,columnWidths:[250,150,150,150],values:input.values});
  table.styleOptions={headerRow:false,bandedRows:false};
  table.borders.assign({fill:'#DBE3EC',width:.7,style:'solid'});
  for(let row=0;row<6;row++){
   table.rows[row].height=53;
   for(let col=0;col<4;col++){
    const cell=table.getCell(row,col);cell.fill=row===0?BLUE:row===3?'#EAF1FA':'#FFFFFF';
    cell.text.style={typeface:FONT,fontSize:'17.5pt',bold:row===0||row===3,color:row===0?'#FFFFFF':INK,alignment:col===0?'left':'center',verticalAlignment:'middle',insets:10};
   }
  }
  text(slide,'+24.09 pp',810,182,410,62,40,true,BLUE);
  text(slide,'Recovery gain over Base IID',810,253,410,68,24);
  text(slide,'+0.89 pp',810,336,410,62,40,true,BLUE);
  text(slide,'Compared with balanced SFT\n95% CI [−1.97, +3.72] pp',810,407,410,82,24);
  text(slide,'Recovery advantage is unresolved',810,510,410,60,23,true);
  text(slide,'Exploratory vs. SFT: validity +3.125 pp,\nuniqueness −4.167 pp.',60,540,710,80,23);
  text(slide,'README guides: Validity >90%, Uniqueness >80%, Recovery >80%. Current scores are lower.',60,621,1160,35,22);
  text(slide,'Boolean subset: 2 variables, depth 2. Three inference seeds, one training seed. NR can include invalid hypotheses.',60,669,1160,28,17,false,GRAY);
 }else throw new Error('Expected phase 1 or 2');
 slide.speakerNotes.text=input.notes;
 return {slideCount:presentation.slides.items.length};
}
