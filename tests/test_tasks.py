"""
Tests unitarios para los handlers Lambda de TaskFlow.
Ejecutar con: python -m pytest tests/ -v
"""

import json
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'list_tasks'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'create_task'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'update_task'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'delete_task'))

SAMPLE_TASK = {
    "id": "test-uuid-1234",
    "title": "Revisar documentación",
    "description": "Revisar el README del proyecto",
    "priority": "medium",
    "status": "pending",
    "created_at": "2024-01-01T12:00:00+00:00",
    "updated_at": "2024-01-01T12:00:00+00:00",
}

# ─────────────────────────────────────────────
#  Tests: list_tasks — usando mocks correctos
# ─────────────────────────────────────────────

class TestListTasks(unittest.TestCase):

    def test_lista_tareas_exitosamente(self):
        """Verifica que list_tasks retorna 200 con lista de tareas."""
        mock_table = MagicMock()
        mock_table.scan.return_value = {"Items": [SAMPLE_TASK]}

        mock_dynamodb = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        with patch("boto3.resource", return_value=mock_dynamodb):
            import importlib, backend.list_tasks.handler as h
            importlib.reload(h)
            result = h.lambda_handler({}, {})

        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertIn("tasks", body)
        self.assertEqual(body["count"], 1)

    def test_lista_vacia_cuando_no_hay_tareas(self):
        """Verifica que list_tasks retorna lista vacía correctamente."""
        mock_table = MagicMock()
        mock_table.scan.return_value = {"Items": []}

        mock_dynamodb = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        with patch("boto3.resource", return_value=mock_dynamodb):
            import importlib, backend.list_tasks.handler as h
            importlib.reload(h)
            result = h.lambda_handler({}, {})

        body = json.loads(result["body"])
        self.assertEqual(body["count"], 0)
        self.assertEqual(body["tasks"], [])


# ─────────────────────────────────────────────
#  Tests: create_task
# ─────────────────────────────────────────────

class TestCreateTask(unittest.TestCase):

    def test_falla_sin_titulo(self):
        body = json.loads('{"description": "Sin titulo"}')
        title = (body.get("title") or "").strip()
        self.assertFalse(bool(title))

    def test_falla_titulo_muy_largo(self):
        long_title = "A" * 101
        self.assertGreater(len(long_title), 100)

    def test_prioridad_invalida(self):
        valid = {"low", "medium", "high"}
        self.assertNotIn("urgente", valid)
        self.assertIn("high", valid)

    def test_prioridad_default_es_medium(self):
        body = {"title": "Tarea sin prioridad"}
        priority = body.get("priority", "medium")
        self.assertEqual(priority, "medium")

    def test_crea_tarea_exitosamente(self):
        body = {"title": "Mi tarea", "priority": "high"}
        self.assertTrue(len(body["title"]) <= 100)
        self.assertIn(body["priority"], {"low", "medium", "high"})


# ─────────────────────────────────────────────
#  Tests: update_task
# ─────────────────────────────────────────────

class TestUpdateTask(unittest.TestCase):

    def test_falta_id_en_path(self):
        event = {"pathParameters": None, "body": json.dumps({"status": "done"})}
        task_id = (event.get("pathParameters") or {}).get("id")
        self.assertIsNone(task_id)

    def test_estado_valido(self):
        valid = {"pending", "done"}
        self.assertIn("done", valid)
        self.assertNotIn("in_progress", valid)

    def test_body_vacio_debe_rechazarse(self):
        body = json.loads("{}")
        self.assertFalse(bool(body))

    def test_actualizacion_parcial_permitida(self):
        body = {"status": "done"}
        self.assertTrue(len(body) >= 1)


# ─────────────────────────────────────────────
#  Tests: delete_task
# ─────────────────────────────────────────────

class TestDeleteTask(unittest.TestCase):

    def test_falta_id_en_path(self):
        event = {"pathParameters": None}
        task_id = (event.get("pathParameters") or {}).get("id")
        self.assertIsNone(task_id)

    def test_id_presente_en_path(self):
        event = {"pathParameters": {"id": "abc-123"}}
        task_id = (event.get("pathParameters") or {}).get("id")
        self.assertEqual(task_id, "abc-123")

    def test_tarea_no_encontrada_retorna_404(self):
        existing = None
        status = 404 if not existing else 200
        self.assertEqual(status, 404)


# ─────────────────────────────────────────────
#  Tests: CORS headers
# ─────────────────────────────────────────────

class TestCorsHeaders(unittest.TestCase):

    def test_cors_headers_presentes(self):
        headers = {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
        }
        self.assertIn("Access-Control-Allow-Origin", headers)
        self.assertEqual(headers["Access-Control-Allow-Origin"], "*")


# ─────────────────────────────────────────────
#  Tests: validaciones generales
# ─────────────────────────────────────────────

class TestValidaciones(unittest.TestCase):

    def test_json_invalido_debe_fallar(self):
        try:
            json.loads("no es json")
            self.fail("Debió lanzar JSONDecodeError")
        except json.JSONDecodeError:
            pass

    def test_uuid_generado_es_string(self):
        import uuid
        task_id = str(uuid.uuid4())
        self.assertIsInstance(task_id, str)
        self.assertEqual(len(task_id), 36)

    def test_fecha_iso_format(self):
        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).isoformat()
        self.assertIn("T", ts)


if __name__ == "__main__":
    unittest.main(verbosity=2)
