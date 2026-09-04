const GROUP_COLORS = {
  "P": "#E2352F", "W": "#FFC53D", "R": "#2F6FED", "I": "#35C46B", "S": "#9AA0A6", "DP": "#9AA0A6"
};
const GROUP_LABELS = {
  "P": "Cấm", "W": "Nguy hiểm", "R": "Hiệu lệnh", "I": "Chỉ dẫn", "S": "Phụ", "DP": "Phụ"
};

let selectedFile = null;

// ---------- Tabs ----------
document.querySelectorAll(".tab").forEach(tabBtn => {
  tabBtn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
    tabBtn.classList.add("active");
    document.getElementById(`tab-${tabBtn.dataset.tab}`).classList.add("active");
  });
});

// ---------- Kiểm tra model đã sẵn sàng chưa ----------
async function checkStatus() {
  const dot = document.getElementById("statusDot");
  const text = document.getElementById("statusText");
  const modelStatus = document.getElementById("modelStatus");
  const classCount = document.getElementById("classCount");
  try {
    const res = await fetch("/api/classes");
    const data = await res.json();
    if (data.classes) {
      dot.classList.add("ok");
      text.textContent = "Model & dữ liệu lớp đã sẵn sàng";
      modelStatus.textContent = "● Sẵn sàng";
      classCount.textContent = `${data.count} lớp biển báo (data/data.yaml)`;
      document.getElementById("runBtn").disabled = false;
    }
  } catch (e) {
    dot.classList.add("err");
    text.textContent = "Không kết nối được backend";
    modelStatus.textContent = "● Lỗi kết nối";
  }
}
checkStatus();

// ---------- Chọn ảnh ----------
const fileInput = document.getElementById("fileInput");
const fileNameField = document.getElementById("fileNameField");
const runBtn = document.getElementById("runBtn");
const placeholder = document.getElementById("placeholder");
const resultImg = document.getElementById("resultImg");

fileInput.addEventListener("change", () => {
  if (!fileInput.files.length) return;
  selectedFile = fileInput.files[0];
  fileNameField.textContent = selectedFile.name;
  runBtn.disabled = false;

  const reader = new FileReader();
  reader.onload = e => {
    placeholder.style.display = "none";
    resultImg.src = e.target.result;
    resultImg.style.display = "block";
  };
  reader.readAsDataURL(selectedFile);
});

// ---------- Ngưỡng tin cậy ----------
const confRange = document.getElementById("confRange");
const confVal = document.getElementById("confVal");
confRange.addEventListener("input", () => {
  confVal.textContent = parseFloat(confRange.value).toFixed(2);
});

// ---------- Chạy nhận diện ----------
runBtn.addEventListener("click", async () => {
  if (!selectedFile) return;
  runBtn.disabled = true;
  runBtn.textContent = "⏳ Đang xử lý…";

  const form = new FormData();
  form.append("image", selectedFile);
  form.append("conf", confRange.value);

  try {
    const res = await fetch("/api/predict", { method: "POST", body: form });
    const data = await res.json();
    if (data.error) throw new Error(data.error);

    resultImg.src = data.result_image_url + "?t=" + Date.now();
    document.getElementById("imgMeta").textContent = data.filename;
    document.getElementById("inferTime").textContent = `Thời gian suy luận: ${data.inference_ms} ms`;
    document.getElementById("detCount").textContent =
      `${data.count} biển · tin cậy TB ${data.avg_confidence ? (data.avg_confidence * 100).toFixed(1) + "%" : "—"}`;

    renderDetections(data.detections);
    renderGroupBars(data.detections);
  } catch (e) {
    alert("Lỗi khi nhận diện: " + e.message);
  } finally {
    runBtn.disabled = false;
    runBtn.textContent = "▶ Chạy nhận diện";
  }
});

function renderDetections(detections) {
  const list = document.getElementById("detList");
  if (!detections.length) {
    list.innerHTML = `<div class="empty-note">Không phát hiện biển báo nào trong ảnh này.</div>`;
    return;
  }
  list.innerHTML = detections.map(d => `
    <div class="det-card" style="border-left-color:${d.color}">
      <div class="top">
        <span class="code" style="color:${d.color}">${d.code}</span>
        <span class="pct">${(d.confidence * 100).toFixed(1)}%</span>
      </div>
      <div class="name">${d.group} — ${d.meaning}</div>
      <div class="conf-track"><div class="conf-fill" style="width:${(d.confidence*100).toFixed(0)}%; background:${d.color}"></div></div>
      <div class="xy">x: ${d.bbox[0]}–${d.bbox[2]} · y: ${d.bbox[1]}–${d.bbox[3]}</div>
    </div>
  `).join("");
}

function renderGroupBars(detections) {
  const counts = {};
  detections.forEach(d => { counts[d.group_prefix] = (counts[d.group_prefix] || 0) + 1; });
  const total = detections.length || 1;
  const groups = ["P", "W", "R", "I", "S"];
  document.getElementById("groupBars").innerHTML = groups.map(g => {
    const n = counts[g] || 0;
    const pct = Math.round((n / total) * 100);
    return `
      <div class="g-row">
        <div class="g-name">${GROUP_LABELS[g]}</div>
        <div class="g-track"><div class="g-fill" style="width:${pct}%; background:${GROUP_COLORS[g]}"></div></div>
        <div class="num">${n}</div>
      </div>`;
  }).join("");
}

// ---------- Đánh giá mô hình ----------
const evalBtn = document.getElementById("evalBtn");
evalBtn.addEventListener("click", async () => {
  evalBtn.disabled = true;
  evalBtn.textContent = "⏳ Đang đánh giá trên tập test… (có thể mất vài phút)";
  document.getElementById("evalEmpty").textContent = "Đang chạy model.val() trên tập test, vui lòng chờ…";

  try {
    const res = await fetch("/api/evaluate?force=true", { method: "POST" });
    const data = await res.json();
    if (data.error) throw new Error(data.error);

    document.getElementById("evalEmpty").style.display = "none";
    document.getElementById("evalResults").style.display = "block";

    document.getElementById("kpiP").textContent = (data.precision * 100).toFixed(1) + "%";
    document.getElementById("kpiR").textContent = (data.recall * 100).toFixed(1) + "%";
    document.getElementById("kpiMap50").textContent = (data.map50 * 100).toFixed(1) + "%";
    document.getElementById("kpiMap5095").textContent = (data.map50_95 * 100).toFixed(1) + "%";
    document.getElementById("evalMeta").textContent = `tập ${data.split} · lúc ${data.evaluated_at}`;

    if (data.confusion_matrix_url) {
      document.getElementById("cmImg").src = data.confusion_matrix_url + "?t=" + Date.now();
    }

    document.getElementById("worstTable").innerHTML = data.worst_classes.map(c => `
      <tr>
        <td style="color:${c.color}; font-family:'JetBrains Mono'">${c.code}</td>
        <td>${c.group}</td>
        <td>${(c.ap50 * 100).toFixed(1)}%</td>
      </tr>`).join("");
  } catch (e) {
    document.getElementById("evalEmpty").style.display = "block";
    document.getElementById("evalEmpty").textContent = "Lỗi khi đánh giá: " + e.message;
  } finally {
    evalBtn.disabled = false;
    evalBtn.textContent = "▶ Chạy đánh giá trên tập test";
  }
});