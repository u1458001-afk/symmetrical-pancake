"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const form = $("#planner-form");
  const dataNode = $("#initial-data");
  if (!form || !dataNode) return;

  let initial = {};
  try { initial = JSON.parse(dataNode.textContent); } catch (_error) { initial = {}; }
  const search = $("#global-search");
  const records = $$("#record-list .record-row");
  const recommendations = $$("#recommendation-list .recommendation-row");
  const recordFilter = {value:"all"};
  const recommendationFilter = {value:"all"};
  const storageKey = "nuu-credit-planner";

  const dispatchInput = (element) => element.dispatchEvent(new Event("input", {bubbles:true}));
  const saveDraft = () => {
    try {
      localStorage.setItem(storageKey, JSON.stringify({
        scenarioId:$("#scenario_id").value,
        requirements:$("#requirements").value,
        courses:$("#courses").value,
        pool:$("#course_pool").value,
        limit:$("#semester-limit-edit").value,
        selected:recommendations.filter((row)=>$("input",row).checked).map((row)=>row.dataset.code),
      }));
    } catch (_error) {
      const status = $("#record-status");
      if (status) status.textContent = "瀏覽器暫存空間無法使用；資料仍可在本頁計算。";
    }
  };
  const emitDraftEvents = () => ["#requirements", "#courses", "#course_pool", "#semester-limit-edit"].forEach((selector)=>dispatchInput($(selector)));

  const saved = (() => {
    try { return JSON.parse(localStorage.getItem(storageKey) || "null"); }
    catch (_error) { return null; }
  })();
  if (saved && !initial.hasError) {
    $("#requirements").value = saved.requirements ?? $("#requirements").value;
    $("#courses").value = saved.courses ?? $("#courses").value;
    $("#course_pool").value = saved.pool ?? $("#course_pool").value;
    $("#semester-limit-edit").value = saved.limit ?? initial.semesterLimit ?? 30;
    $("#semester_limit").value = $("#semester-limit-edit").value;
    $("#scenario_id").value = saved.scenarioId || initial.scenarioId || "custom";
    if (Array.isArray(saved.selected)) {
      recommendations.forEach((row)=>{ if (saved.selected.includes(row.dataset.code)) $("input",row).checked = true; });
    }
    const differs = saved.requirements !== undefined && (
      saved.requirements !== JSON.stringify(initial.requirements, null, 2) ||
      saved.courses !== JSON.stringify(initial.courses, null, 2) ||
      saved.pool !== JSON.stringify(initial.pool, null, 2) ||
      Number(saved.limit) !== Number(initial.semesterLimit)
    );
    if (differs) window.setTimeout(()=>form.requestSubmit(), 0);
  }
  ["#requirements", "#courses", "#course_pool", "#semester-limit-edit"].forEach((selector)=>$(selector).addEventListener("input", saveDraft));
  recommendations.forEach((row)=>$("input",row).addEventListener("change",()=>{saveDraft();updateSimulation();applyRecommendationFilters();}));

  const submitCalculation = () => {
    $("#semester_limit").value = $("#semester-limit-edit").value || initial.semesterLimit || 30;
    saveDraft();
    form.requestSubmit();
  };

  $$('[data-load-scenario]').forEach((button)=>button.addEventListener("click",()=>{
    const selected = initial.scenarios?.[button.dataset.loadScenario];
    if (!selected) return;
    $("#scenario_id").value = button.dataset.loadScenario;
    $("#requirements").value = JSON.stringify(selected.requirements, null, 2);
    $("#courses").value = JSON.stringify(selected.courses, null, 2);
    $("#course_pool").value = JSON.stringify(selected.course_pool, null, 2);
    emitDraftEvents();
    submitCalculation();
  }));

  $("#clear-data").addEventListener("click",()=>{
    const baseline = initial.scenarios?.a;
    $("#scenario_id").value = "custom";
    $("#requirements").value = JSON.stringify(baseline?.requirements || initial.requirements, null, 2);
    $("#courses").value = "[]";
    $("#course_pool").value = JSON.stringify(baseline?.course_pool || initial.pool, null, 2);
    $("#global-search").value = "";
    recommendations.forEach((row)=>{ $("input",row).checked = false; });
    emitDraftEvents();
    submitCalculation();
  });

  $("#open-data").addEventListener("click",()=>{
    const editor = $("#data-editor"); editor.open = true; editor.scrollIntoView({behavior:"smooth",block:"center"});
    $("#courses").focus({preventScroll:true});
  });
  $("#save-settings").addEventListener("click",submitCalculation);
  $("#semester-limit-edit").addEventListener("input",()=>{ $("#semester_limit").value = $("#semester-limit-edit").value; updateSimulation(); });

  const filterRecords = () => {
    const query = search.value.trim().toLocaleLowerCase();
    let visible = 0;
    records.forEach((row)=>{
      const textMatch = !query || row.dataset.search.toLocaleLowerCase().includes(query);
      let filterMatch = true;
      if (recordFilter.value === "failed") filterMatch = row.dataset.outcome === "未通過" && row.dataset.resolved !== "true";
      if (recordFilter.value === "retake") filterMatch = row.dataset.retake === "true";
      if (recordFilter.value === "passed") filterMatch = row.dataset.outcome === "通過";
      row.hidden = !(textMatch && filterMatch);
      if (!row.hidden) visible += 1;
    });
    $("#records-empty").hidden = !records.length || visible > 0;
  };
  const applyRecommendationFilters = () => {
    const query = search.value.trim().toLocaleLowerCase();
    let visible = 0;
    recommendations.forEach((row)=>{
      const textMatch = !query || row.dataset.search.toLocaleLowerCase().includes(query);
      const selected = $("input",row).checked;
      let filterMatch = true;
      if (recommendationFilter.value === "needed") filterMatch = row.dataset.required === "true" || row.dataset.failed === "true";
      if (recommendationFilter.value === "largest") filterMatch = row.dataset.largest === "true";
      if (recommendationFilter.value === "selected") filterMatch = selected;
      row.hidden = !(textMatch && filterMatch);
      if (!row.hidden) visible += 1;
    });
    $("#recommendations-empty").hidden = !recommendations.length || visible > 0;
  };

  $$("[data-filter-set]").forEach((button)=>button.addEventListener("click",()=>{
    const target = button.dataset.filterSet === "records" ? recordFilter : recommendationFilter;
    target.value = button.dataset.filter;
    $$(`[data-filter-set="${button.dataset.filterSet}"]`).forEach((chip)=>chip.classList.toggle("active", chip === button));
    if (button.dataset.filterSet === "records") filterRecords(); else applyRecommendationFilters();
  }));
  search.addEventListener("input",()=>{filterRecords();applyRecommendationFilters();});
  document.addEventListener("keydown",(event)=>{
    if (event.key !== "/" || event.ctrlKey || event.metaKey || event.altKey) return;
    const tag = document.activeElement?.tagName?.toLowerCase();
    if (["input","textarea","select"].includes(tag) || document.activeElement?.isContentEditable) return;
    event.preventDefault(); search.focus();
  });

  const updateSimulation = () => {
    const chosen = recommendations.filter((row)=>$("input",row).checked);
    const credits = chosen.reduce((sum,row)=>sum+Number(row.dataset.credits || 0),0);
    const limit = Number($("#semester-limit-edit").value || initial.semesterLimit || 30);
    $("#selected-credits").textContent = credits.toFixed(credits%1?1:0);
    $("#limit-warning").hidden = credits <= limit;
    const selectedByCategory = {};
    chosen.forEach((row)=>{selectedByCategory[row.dataset.category]=(selectedByCategory[row.dataset.category]||0)+Number(row.dataset.credits||0);});
    const remainingNode = $("#remaining-gaps");
    const gapParts = Object.entries(initial.result?.categories || {})
      .filter(([category,item])=>category !== "總學分" && item.gap > 0)
      .map(([category,item])=>({category,remaining:Math.max(0,item.gap-(selectedByCategory[category]||0))}))
      .filter((item)=>item.remaining > 0);
    const totalGap = initial.result?.categories?.["總學分"]?.gap || 0;
    const remainingTotal = Math.max(0,totalGap-credits);
    remainingNode.replaceChildren();
    const items = [{category:"總學分",remaining:remainingTotal},...gapParts];
    items.forEach((item)=>{
      const chip = document.createElement("span");
      chip.textContent = `${item.category} `;
      const value = document.createElement("b"); value.textContent = String(Number(item.remaining.toFixed(1)));
      chip.append(value); remainingNode.append(chip);
    });
    if (!items.length) remainingNode.textContent = "已達門檻";
  };

  const parseCourseEditor = async (textarea) => {
    const value = textarea.value.trim();
    if (!value) return [];
    try { const data=JSON.parse(value); return Array.isArray(data)?data:(data.courses||data["課程"]||[]); }
    catch (_error) {
      const response=await fetch("/api/import",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({content:value,format:"auto"})});
      const data=await response.json(); if(!response.ok) throw new Error(data.error||"課程格式錯誤。"); return data.courses;
    }
  };

  const addRecord = async () => {
    const status = $("#quick-add-status");
    const name = $("#quick-name").value.trim();
    if (!name) {status.textContent="請先輸入課程名稱。";$("#quick-name").focus();return;}
    const credits = Number($("#quick-credits").value);
    if (!Number.isFinite(credits)||credits<0||credits>30) {status.textContent="學分請填 0 到 30 的數字。";return;}
    try {
      const courses=await parseCourseEditor($("#courses"));
      const course={name,credits,category:$("#quick-category").value,status:$("#quick-status").value,semester:"自行新增",required:$("#quick-required").checked};
      if($("#quick-score").value!=="") course.score=Number($("#quick-score").value);
      courses.push(course); $("#courses").value=JSON.stringify(courses,null,2); $("#scenario_id").value="custom"; dispatchInput($("#courses"));
      submitCalculation();
    } catch(error) {status.textContent=error.message||"無法新增課程，請先確認修課資料格式。";}
  };
  $("#add-record").addEventListener("click",addRecord);
  ["#quick-name","#quick-credits","#quick-score"].forEach((selector)=>$(selector).addEventListener("keydown",(event)=>{if(event.key==="Enter"){event.preventDefault();addRecord();}}));

  const loadFile = (inputId,targetId,statusId) => {
    const input=$(inputId); input.addEventListener("change",async()=>{
      const file=input.files?.[0]; if(!file)return;
      const status=$(statusId); if(file.size>1000000){status.textContent="檔案需小於 1 MB。";input.value="";return;}
      try {$(targetId).value=await file.text();dispatchInput($(targetId));status.textContent=`已載入 ${file.name}，套用資料後即可計算。`;$("#scenario_id").value="custom";}
      catch(_error){status.textContent="讀取檔案失敗，請確認檔案編碼。";}
    });
  };
  loadFile("#record-file","#courses","#record-status");
  loadFile("#pool-file","#course_pool","#pool-status");

  const download = (filename,content,type) => {
    const blob=new Blob([content],{type});const url=URL.createObjectURL(blob);const link=document.createElement("a");
    link.href=url;link.download=filename;document.body.appendChild(link);link.click();link.remove();URL.revokeObjectURL(url);
  };
  $("#export-records").addEventListener("click",async()=>{
    try {const courses=await parseCourseEditor($("#courses"));download("修課紀錄.json",JSON.stringify(courses,null,2),"application/json;charset=utf-8");}
    catch(error){$("#record-status").textContent=error.message||"無法匯出，請檢查資料格式。";}
  });
  $("#export-plan").addEventListener("click",()=>{
    const rows=[["課號","課程名稱","學分","類別","推薦原因"],...recommendations.filter((row)=>$("input",row).checked).map((row)=>[row.dataset.code,$(".recommendation-main strong",row).textContent,row.dataset.credits,row.dataset.category,$(".recommendation-reason",row).textContent])];
    const csv=rows.map((row)=>row.map((cell)=>`"${String(cell).replaceAll('"','""')}"`).join(",")).join("\r\n");
    download("擬選課程清單.csv","\ufeff"+csv,"text/csv;charset=utf-8");
  });

  $("#fetch-courses").addEventListener("click",async()=>{
    const status=$("#pool-status");const button=$("#fetch-courses");const url=$("#source-url").value.trim();
    if(!url){status.textContent="請輸入 HTTPS JSON 或 CSV 網址。";$("#source-url").focus();return;}
    button.disabled=true;status.textContent="正在讀取課程來源…";
    try {const response=await fetch("/api/import",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url})});const data=await response.json();if(!response.ok)throw new Error(data.error||"匯入失敗。");
      $("#course_pool").value=JSON.stringify(data.courses,null,2);$("#scenario_id").value="custom";dispatchInput($("#course_pool"));status.textContent=`已載入 ${data.count} 門課程；請核對資料更新時間。`;
    }catch(error){status.textContent=error.message||"無法讀取課程來源。";}finally{button.disabled=false;}
  });

  if(saved?.selected){updateSimulation();}
  filterRecords();applyRecommendationFilters();updateSimulation();
});
