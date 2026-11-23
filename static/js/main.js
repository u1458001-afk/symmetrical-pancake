"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const $ = (selector) => document.querySelector(selector);
  const form = $("#planner-form");
  const initialNode = $("#initial-data");
  if (!form || !initialNode) return;
  let initial = {};
  try { initial = JSON.parse(initialNode.textContent); } catch (_error) { initial = {}; }
  const recordStatus = $("#record-status");
  const poolStatus = $("#pool-status");
  const restore = () => {
    try {
      const saved = JSON.parse(localStorage.getItem("nuu-credit-planner") || "null");
      if (saved) {
        $("#requirements").value = saved.requirements || $("#requirements").value;
        $("#courses").value = saved.courses || "";
        $("#course_pool").value = saved.pool || $("#course_pool").value;
        $("#semester_limit").value = saved.limit || "30";
      }
    } catch (_error) { recordStatus.textContent = "瀏覽器暫存資料無法讀取，已保留本頁內容。"; }
  };
  restore();
  form.addEventListener("input", () => {
    try { localStorage.setItem("nuu-credit-planner", JSON.stringify({requirements:$("#requirements").value,courses:$("#courses").value,pool:$("#course_pool").value,limit:$("#semester_limit").value})); }
    catch (_error) { recordStatus.textContent = "瀏覽器儲存空間無法使用；目前仍可計算。"; }
  });
  const loadFile = (inputId, targetId, statusNode) => {
    const input = $(inputId);
    input.addEventListener("change", async () => {
      const file = input.files && input.files[0];
      if (!file) return;
      if (file.size > 1000000) { statusNode.textContent = "檔案需小於 1 MB。"; input.value = ""; return; }
      try { $(targetId).value = await file.text(); statusNode.textContent = `已載入 ${file.name}，請確認欄位後計算。`; $(targetId).dispatchEvent(new Event("input", {bubbles:true})); }
      catch (_error) { statusNode.textContent = "讀取檔案失敗，請確認檔案編碼。"; }
    });
  };
  loadFile("#record-file", "#courses", recordStatus);
  loadFile("#pool-file", "#course_pool", poolStatus);
  $("#export-records").addEventListener("click", () => download("修課紀錄.json", $("#courses").value || "[]", "application/json;charset=utf-8"));
  $("#fetch-courses").addEventListener("click", async () => {
    const button = $("#fetch-courses"); button.disabled = true; poolStatus.textContent = "正在讀取設定的 HTTPS 來源…";
    try {
      const response = await fetch("/api/import", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url:initial.externalUrl})});
      const data = await response.json(); if (!response.ok) throw new Error(data.error || "讀取失敗");
      $("#course_pool").value = JSON.stringify(data.courses, null, 2); poolStatus.textContent = `${data.count} 門課程已載入；請確認來源資料是否最新。`;
      $("#course_pool").dispatchEvent(new Event("input", {bubbles:true}));
    } catch (error) { poolStatus.textContent = error.message || "來源讀取失敗。"; }
    finally { button.disabled = false; }
  });
  const calculateButton = $("#calculate-button");
  form.addEventListener("submit", () => { calculateButton.disabled = true; calculateButton.textContent = "計算中…"; });
  const checks = [...document.querySelectorAll(".course-check")];
  const updateSimulation = () => {
    if (!checks.length) return;
    const chosen = checks.filter((item) => item.checked);
    const credits = chosen.reduce((sum, item) => sum + Number(item.dataset.credits || 0), 0);
    const limit = Number($("#semester_limit").value || initial.result?.semester_limit || 30);
    $("#selected-credits").textContent = credits.toFixed(credits % 1 ? 1 : 0);
    $("#display-limit").textContent = String(limit);
    const message = $("#simulation-message");
    if (credits > limit) { message.textContent = `目前超過上限 ${Number((credits-limit).toFixed(1))} 學分，請調整勾選。`; message.style.color = "#a43f38"; }
    else { message.textContent = chosen.length ? `擬選 ${chosen.length} 門，符合設定的學分上限。` : "勾選課程後查看預估結果。"; message.style.color = ""; }
    const baseline = Number(initial.result?.earned_total || 0);
    $("#projected-total").textContent = `估算取得學分：${(baseline+credits).toFixed((baseline+credits)%1?1:0)} 學分（僅供擬選試算）`;
  };
  checks.forEach((item) => item.addEventListener("change", updateSimulation));
  $("#semester_limit").addEventListener("input", updateSimulation);
  const exportPlan = $("#export-plan");
  if (exportPlan) exportPlan.addEventListener("click", () => {
    const rows = [["課號","課程名稱","學分","類別","推薦原因"], ...checks.filter((item)=>item.checked).map((item)=>{const card=item.closest(".recommendation-card");return [item.value,card.querySelector(".course-main strong").textContent,item.dataset.credits,card.querySelector(".course-main small").textContent,card.querySelector(".course-reason").textContent];})];
    const csv = rows.map((row)=>row.map((cell)=>`"${String(cell).replaceAll('"','""')}"`).join(",")).join("\r\n");
    download("擬選課程清單.csv", "\ufeff"+csv, "text/csv;charset=utf-8");
  });
  if (checks.length) updateSimulation();
});

function download(filename, content, mime) {
  const blob = new Blob([content], {type:mime}); const url = URL.createObjectURL(blob); const link = document.createElement("a");
  link.href = url; link.download = filename; document.body.appendChild(link); link.click(); link.remove(); URL.revokeObjectURL(url);
}
