// ============================================================
//  TaskFlow — Frontend App
//  Consume la API REST desplegada en AWS API Gateway
// ============================================================

// ⚠️  REEMPLAZA esta URL con la que te genera AWS API Gateway
//     Ejemplo: https://abc123def.execute-api.us-east-1.amazonaws.com/prod
const API_URL = "https://TU_API_GATEWAY_URL/prod";

// ============================================================
//  UTILIDADES
// ============================================================

function showStatus(msg, type = "success") {
  const el = document.getElementById("status-msg");
  el.textContent = msg;
  el.className = `status-msg ${type}`;
  setTimeout(() => { el.className = "status-msg hidden"; }, 3500);
}

function setLoading(loading) {
  const btn = document.getElementById("btn-create");
  btn.disabled = loading;
  btn.textContent = loading ? "Creando..." : "+ Crear tarea";
}

function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString("es-CO", { day: "2-digit", month: "short", year: "numeric" });
}

// ============================================================
//  LISTAR TAREAS
// ============================================================

async function loadTasks() {
  const container = document.getElementById("tasks-list");
  container.innerHTML = '<div class="loading">Cargando tareas...</div>';

  try {
    const res = await fetch(`${API_URL}/tasks`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const data = await res.json();
    const tasks = data.tasks || [];

    document.getElementById("task-count").textContent = tasks.length;

    if (tasks.length === 0) {
      container.innerHTML = '<div class="empty">No hay tareas aún. ¡Crea la primera!</div>';
      return;
    }

    // Ordenar: pendientes primero, luego por prioridad
    const order = { high: 0, medium: 1, low: 2 };
    tasks.sort((a, b) => {
      if (a.status === b.status) return (order[a.priority] ?? 1) - (order[b.priority] ?? 1);
      return a.status === "done" ? 1 : -1;
    });

    container.innerHTML = tasks.map(renderTask).join("");
  } catch (err) {
    container.innerHTML = `<div class="empty" style="color:#ff6b6b">Error al cargar tareas: ${err.message}</div>`;
    console.error("loadTasks:", err);
  }
}

function renderTask(task) {
  const done = task.status === "done";
  const priorityClass = `priority-${task.priority || "medium"}`;
  const priorityLabel = { high: "Alta", medium: "Media", low: "Baja" }[task.priority] || "Media";

  return `
    <div class="task-card ${done ? "done" : ""}" id="card-${task.id}">
      <div class="task-top">
        <input
          type="checkbox"
          class="task-checkbox"
          ${done ? "checked" : ""}
          onchange="toggleTask('${task.id}', '${done ? "pending" : "done"}')"
          aria-label="Marcar como ${done ? "pendiente" : "completada"}"
        />
        <div class="task-info">
          <div class="task-title">${escapeHtml(task.title)}</div>
          ${task.description ? `<div class="task-desc">${escapeHtml(task.description)}</div>` : ""}
          <div class="task-meta">
            <span class="priority-badge ${priorityClass}">${priorityLabel}</span>
            ${task.created_at ? `<span class="task-date">${formatDate(task.created_at)}</span>` : ""}
            <button class="btn-delete" onclick="deleteTask('${task.id}')">Eliminar</button>
          </div>
        </div>
      </div>
    </div>`;
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ============================================================
//  CREAR TAREA
// ============================================================

async function createTask() {
  const title = document.getElementById("title").value.trim();
  const description = document.getElementById("description").value.trim();
  const priority = document.getElementById("priority").value;

  if (!title) {
    showStatus("El título es obligatorio.", "error");
    document.getElementById("title").focus();
    return;
  }

  setLoading(true);
  try {
    const res = await fetch(`${API_URL}/tasks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, description, priority }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    document.getElementById("title").value = "";
    document.getElementById("description").value = "";
    document.getElementById("priority").value = "medium";
    showStatus("✓ Tarea creada correctamente.");
    await loadTasks();
  } catch (err) {
    showStatus(`Error al crear tarea: ${err.message}`, "error");
    console.error("createTask:", err);
  } finally {
    setLoading(false);
  }
}

// ============================================================
//  ACTUALIZAR ESTADO (toggle)
// ============================================================

async function toggleTask(id, newStatus) {
  try {
    const res = await fetch(`${API_URL}/tasks/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    await loadTasks();
  } catch (err) {
    showStatus(`Error al actualizar tarea: ${err.message}`, "error");
    console.error("toggleTask:", err);
    await loadTasks(); // revert UI
  }
}

// ============================================================
//  ELIMINAR TAREA
// ============================================================

async function deleteTask(id) {
  if (!confirm("¿Eliminar esta tarea?")) return;

  try {
    const res = await fetch(`${API_URL}/tasks/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    showStatus("Tarea eliminada.");
    await loadTasks();
  } catch (err) {
    showStatus(`Error al eliminar: ${err.message}`, "error");
    console.error("deleteTask:", err);
  }
}

// ============================================================
//  INIT
// ============================================================

// Permitir crear con Enter en el campo título
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("title").addEventListener("keydown", (e) => {
    if (e.key === "Enter") createTask();
  });
  loadTasks();
});
