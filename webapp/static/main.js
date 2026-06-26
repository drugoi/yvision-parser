const $ = (id) => document.getElementById(id);

function resetDownload() {
  const a = $("download");
  a.hidden = true;
  a.classList.add("is-disabled");
  a.setAttribute("aria-disabled", "true");
  a.removeAttribute("href");
}

// Visible but inactive while the export is still running.
function showDownloadPending() {
  const a = $("download");
  a.hidden = false;
  a.classList.add("is-disabled");
  a.setAttribute("aria-disabled", "true");
  a.removeAttribute("href");
}

// Active only once the zip is ready.
function enableDownload(url) {
  const a = $("download");
  a.href = url;
  a.hidden = false;
  a.classList.remove("is-disabled");
  a.setAttribute("aria-disabled", "false");
}

async function start() {
  $("error").hidden = true;
  resetDownload();
  const account = $("account").value.trim();
  if (!account) return;
  $("go").disabled = true;

  let res;
  try {
    res = await fetch("/api/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ account, include_images: $("images").checked }),
    });
  } catch {
    return showError("Сеть недоступна. Попробуйте ещё раз.");
  }
  if (!res.ok) {
    const data = await res.json().catch(() => ({ detail: "Ошибка" }));
    return showError(data.detail || "Ошибка");
  }
  const { job_id } = await res.json();
  $("progress").hidden = false;
  showDownloadPending();
  poll(job_id);
}

async function poll(jobId) {
  let res;
  try {
    res = await fetch(`/api/export/${jobId}`);
  } catch {
    return showError("Сеть недоступна. Попробуйте ещё раз.");
  }
  if (!res.ok) return showError("Задача не найдена");
  const s = await res.json();

  if (s.state === "error") return showError(s.error || "Ошибка экспорта");

  const bar = document.querySelector("#progress progress");
  if (s.total) {
    $("ptext").textContent = `Обработка: ${s.done} / ${s.total} постов`;
    bar.max = s.total;
    bar.value = s.done;
  } else {
    $("ptext").textContent = "Получение списка постов…";
    bar.removeAttribute("value"); // indeterminate
  }

  if (s.state === "done") {
    $("ptext").textContent = `Готово: ${s.done} постов`;
    bar.max = s.total || 1;
    bar.value = s.total || 1;
    enableDownload(`/api/export/${jobId}/download`);
    $("go").disabled = false;
    return;
  }
  setTimeout(() => poll(jobId), 1500);
}

function showError(msg) {
  $("error").textContent = msg;
  $("error").hidden = false;
  $("progress").hidden = true;
  resetDownload();
  $("go").disabled = false;
}

document.addEventListener("DOMContentLoaded", () => {
  $("go").addEventListener("click", start);
});
