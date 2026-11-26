// Editable two-slide evidence deck. Requires the bundled @oai/artifact-tool runtime.
import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath, pathToFileURL} from 'node:url';

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const modules=process.env.ARTIFACT_NODE_MODULES;
const skill=process.env.PRESENTATION_SKILL_DIR;
const python=process.env.PRESENTATION_PYTHON;
if(!modules||!skill||!python)throw new Error('Set ARTIFACT_NODE_MODULES, PRESENTATION_SKILL_DIR and PRESENTATION_PYTHON from workspace dependencies');
process.env.RUNTIME_NODE_MODULES ??= modules;
const req=createRequire(path.join(modules,'@oai/artifact-tool/package.json'));
const {Presentation,PresentationFile}=await import(pathToFileURL(req.resolve('@oai/artifact-tool')).href);
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const build=path.join(ROOT,'runs/personal_slides_build');
const output=path.join(ROOT,'presentations');
await fs.mkdir(build,{recursive:true});await fs.mkdir(output,{recursive:true});
const prs=Presentation.create({slideSize:{width:1280,height:720}});
const FONT='Arial Unicode MS';
const BLUE='#23589F',INK='#17263B',GRAY='#536278';

function text(slide,value,x,y,w,h,size=24,bold=false,color=INK,font=FONT){
 const shape=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 shape.text=value;
 shape.text.style={typeface:font,fontSize:size,bold,color,alignment:'left',verticalAlignment:'top',autoFit:'none',wrap:'square',insets:0};
 return shape;
}
function heading(slide,title,subtitle){
 slide.background.fill='#FFFFFF';
 text(slide,title,60,38,1160,65,48,true);
 text(slide,subtitle,60,108,1160,44,24,false,GRAY);
}

const s1=prs.slides.add();
heading(s1,'结构类别覆盖 LoRA','研究思路与训练原理');
text(s1,'问题来源与文献启发',60,176,440,42,29,true,BLUE);
text(s1,'HypoSpace（2026）',60,231,440,36,25,true);
text(s1,'合法生成仍可能集中在少数假设',60,272,440,64,24);
text(s1,'GAPO（2025）',60,344,440,36,25,true);
text(s1,'组级训练可以关注多样性与覆盖',60,385,440,64,24);
text(s1,'本项目的切入点',60,466,440,36,25,true,BLUE);
text(s1,'利用可枚举的官方结构类别，\n将覆盖代理加入监督训练',60,509,440,86,25);

text(s1,'按结构类别聚合完整回答概率',560,176,660,42,29,true,BLUE);
text(s1,'qₖ = Σ Pθ(h ∣ O)，h ∈ Aₖ',560,237,660,54,32);
text(s1,'C₁₆ = (1/K) Σₖ [1 − (1 − qₖ)¹⁶]',560,313,660,58,32);
text(s1,'训练损失 = 均衡 SFT 损失 − C₁₆',560,391,660,54,31,true,BLUE);
text(s1,'Aₖ：同类两种合法写法，概率包含结束符\nK：合法结构类总数，O：给定观测\nC₁₆：固定提示独立采样下的有限池覆盖下界',560,467,660,89,23);
text(s1,'LoRA 更新少量参数，测试仅输入原始观测\n创新定位：官方结构类与有限预算目标的结合',560,570,660,74,23);
text(s1,'参考：Chen et al., HypoSpace（ICML 2026）；Anschel et al., GAPO（EMNLP 2025）；Hu et al., LoRA',60,661,1160,36,16,false,GRAY);
s1.speakerNotes.text=`我的方向是通过训练目标，提高模型在 HypoSpace 上的结构覆盖率。HypoSpace 指出，合法答案仍可能集中在少数假设。我参考 GAPO 的组级多样性训练思路，探索基于官方结构类别的监督式覆盖代理。将同类两种合法写法的完整序列概率求和，用十六次采样的至少一次命中函数构造代理，并与均衡 SFT 联合训练。LoRA 是已有实现工具。\n\n有限池代理在固定提示独立采样等条件下提供覆盖下界，不保证真实 RR 随有限训练增加。官方结构类不等于完整真值表等价类。\n\n来源：https://proceedings.mlr.press/v306/chen26bz.html\nhttps://aclanthology.org/2025.emnlp-main.1649/\nhttps://arxiv.org/abs/2106.09685\n项目实现：explorer/coverage_lora.py；docs/METHOD.md`;

const summary=JSON.parse(await fs.readFile(path.join(ROOT,'results/final/test/summary.json'),'utf8'));
const methods=[['原始模型','base_iid'],['均衡 SFT','balanced_sft_iid'],['结构类别覆盖','canonical_coverage_iid'],['字符串覆盖','string_coverage_iid'],['原始模型＋历史','base_memory']];
const values=[['方法','VR 合法率','NR 唯一率','RR 恢复率'],...methods.map(([label,key])=>[label,...['VR','NR','RR'].map(m=>(100*summary.metrics[key][m]).toFixed(2)+'%')])];
const s2=prs.slides.add();
heading(s2,'实验结果与贡献边界','Qwen2.5-1.5B-Instruct（4-bit），16 / 6 / 26 个训练、验证和测试观测实例');
const table=s2.tables.add({rows:6,columns:4,left:60,top:178,width:700,height:318,columnWidths:[250,150,150,150],values});
table.styleOptions={headerRow:false,bandedRows:false};
table.borders.assign({fill:'#DBE3EC',width:.7,style:'solid'});
for(let row=0;row<6;row++){
 table.rows[row].height=53;
 for(let col=0;col<4;col++){
  const c=table.getCell(row,col);
  c.fill=row===0?BLUE:row===3?'#EAF1FA':'#FFFFFF';
  c.text.style={typeface:FONT,fontSize:'17.5pt',bold:row===0||row===3,color:row===0?'#FFFFFF':INK,alignment:col===0?'left':'center',verticalAlignment:'middle',insets:10};
 }
}
text(s2,'+24.09 个百分点',810,182,410,62,40,true,BLUE);
text(s2,'整体方法相对原始模型的 RR 提升',810,253,410,68,24);
text(s2,'+0.89 个百分点',810,336,410,62,40,true,BLUE);
text(s2,'相对均衡 SFT 的 RR 差\n95% 区间 [−1.97, +3.72]',810,407,410,82,24);
text(s2,'恢复率额外收益尚不确定',810,510,410,44,25,true);
text(s2,'探索性分析：相对 SFT，VR 提高 3.125 个百分点，NR 降低 4.167 个百分点',60,540,710,80,23);
text(s2,'已完成五组对照与消融、6720 次正式生成、原始记录和独立复核',60,621,1160,35,23);
text(s2,'范围：两变量、深度二布尔子集；三个推理种子、一个训练种子。NR 可包含违反观测的结构',60,669,1160,28,17,false,GRAY);
s2.speakerNotes.text=`实验在 Mac 上使用十五亿参数模型完成。三种微调使用匹配的数据与训练预算；测试为26题、三个推理种子、每题16次、五种方法，共6240次，加480次验证合计6720次。\n\n恢复率从原始模型13.67%提高至结构覆盖37.76%。匹配SFT已达到36.86%，新增覆盖项只提高0.89个百分点，原按题bootstrap区间跨零，尚不能确认恢复率额外优势。探索性次要分析观察到VR提高3.125个百分点、NR降低4.167个百分点。次要推断不是预注册确认性结论。\n\n只有一个训练种子，不能外推到所有HypoSpace任务或重新训练后的稳定收益。贡献包括任务相关目标设计、匹配消融和可复现实现。\n\n原始来源：results/final/test/summary.json；results/contribution_audit/secondary_metrics.json。公开仓库：https://github.com/Xiao-ada/EEC4300-HypoSpace\nhttps://github.com/Xiao-ada/EEC4300-HypoSpace/blob/main/results/final/test/summary.json`;

for(let i=0;i<2;i++){
 const image=await prs.export({slide:prs.slides.getItem(i),format:'png',scale:1.5});
 await fs.writeFile(path.join(build,`slide-${i+1}.png`),new Uint8Array(await image.arrayBuffer()));
}
const candidate=path.join(build,'candidate.pptx');
await(await PresentationFile.exportPptx(prs)).save(candidate);
const finalPath=path.join(output,'personal_method_results.pptx');
await finalizePresentation({workspaceDir:ROOT,candidatePath:candidate,finalPath,
 explicitTotalSlideCount:2,requiredNativeTableOwnerSlides:[2],requiredNativeChartOwnerSlides:[],
 pythonExecutable:python,integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit','--require-native-table-slide','2'],
 fontPolicy:{basis:'design',families:[FONT]},verifyArtifactToolImport:true,
 receiptPath:path.join(build,'validation.json')});
console.log(JSON.stringify({finalPath,previews:[path.join(build,'slide-1.png'),path.join(build,'slide-2.png')]}));
