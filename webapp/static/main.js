const $ = (id) => document.getElementById(id);

async function start() {
  $("error").hidden = true;
  $("download").hidden = true;
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
    const a = $("download");
    a.href = `/api/export/${jobId}/download`;
    a.hidden = false;
    $("go").disabled = false;
    return;
  }
  setTimeout(() => poll(jobId), 1500);
}

function showError(msg) {
  $("error").textContent = msg;
  $("error").hidden = false;
  $("progress").hidden = true;
  $("go").disabled = false;
}

document.addEventListener("DOMContentLoaded", () => {
  $("go").addEventListener("click", start);
});
