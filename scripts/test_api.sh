#!/bin/bash
# ============================================================
#  test_api.sh — Prueba manual de todos los endpoints
#
#  Uso:
#    chmod +x scripts/test_api.sh
#    ./scripts/test_api.sh https://TU_URL.execute-api.us-east-1.amazonaws.com/prod
# ============================================================

API_URL="${1:-}"

if [ -z "$API_URL" ]; then
  echo "Uso: ./scripts/test_api.sh <API_URL>"
  echo "Ejemplo: ./scripts/test_api.sh https://abc123.execute-api.us-east-1.amazonaws.com/prod"
  exit 1
fi

GREEN='\033[0;32m'; BLUE='\033[0;34m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo ""
echo "══════════════════════════════════════════════════"
echo "  TaskFlow — Prueba de endpoints"
echo "  URL: $API_URL"
echo "══════════════════════════════════════════════════"

# ─── GET /tasks (lista vacía inicial) ───────────────────────
echo ""
echo -e "${BLUE}[TEST 1]${NC} GET /tasks — Listar tareas"
curl -s -w "\nHTTP Status: %{http_code}\n" "${API_URL}/tasks" | python3 -m json.tool 2>/dev/null || true

# ─── POST /tasks — Crear tarea 1 ────────────────────────────
echo ""
echo -e "${BLUE}[TEST 2]${NC} POST /tasks — Crear tarea de alta prioridad"
RESPONSE=$(curl -s -X POST "${API_URL}/tasks" \
  -H "Content-Type: application/json" \
  -d '{"title":"Preparar presentación","description":"Slides de la exposición universitaria","priority":"high"}')
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
TASK_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['task']['id'])" 2>/dev/null || echo "")

# ─── POST /tasks — Crear tarea 2 ────────────────────────────
echo ""
echo -e "${BLUE}[TEST 3]${NC} POST /tasks — Crear segunda tarea"
curl -s -X POST "${API_URL}/tasks" \
  -H "Content-Type: application/json" \
  -d '{"title":"Revisar código","priority":"medium"}' | python3 -m json.tool 2>/dev/null || true

# ─── GET /tasks — Ver las 2 tareas ──────────────────────────
echo ""
echo -e "${BLUE}[TEST 4]${NC} GET /tasks — Listar todas las tareas (deberían aparecer 2)"
curl -s "${API_URL}/tasks" | python3 -m json.tool 2>/dev/null || true

# ─── PUT /tasks/{id} — Marcar como done ─────────────────────
if [ -n "$TASK_ID" ]; then
  echo ""
  echo -e "${BLUE}[TEST 5]${NC} PUT /tasks/${TASK_ID} — Marcar como completada"
  curl -s -X PUT "${API_URL}/tasks/${TASK_ID}" \
    -H "Content-Type: application/json" \
    -d '{"status":"done"}' | python3 -m json.tool 2>/dev/null || true

  # ─── DELETE /tasks/{id} ─────────────────────────────────────
  echo ""
  echo -e "${BLUE}[TEST 6]${NC} DELETE /tasks/${TASK_ID} — Eliminar la tarea"
  curl -s -X DELETE "${API_URL}/tasks/${TASK_ID}" | python3 -m json.tool 2>/dev/null || true
fi

# ─── POST inválido (sin título) ──────────────────────────────
echo ""
echo -e "${BLUE}[TEST 7]${NC} POST /tasks — Body inválido (sin título, debe retornar 400)"
curl -s -X POST "${API_URL}/tasks" \
  -H "Content-Type: application/json" \
  -d '{"description":"Sin titulo"}' | python3 -m json.tool 2>/dev/null || true

echo ""
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✓ Pruebas completadas${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo ""
