"""
Lambda: create_task
POST /tasks
Crea una nueva tarea en DynamoDB.
Body esperado (JSON):
  {
    "title": "string (requerido, max 100 chars)",
    "description": "string (opcional)",
    "priority": "low | medium | high (default: medium)"
  }
"""

import json
import os
import uuid
import boto3
from datetime import datetime, timezone

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ.get("TABLE_NAME", "taskflow-tasks")

VALID_PRIORITIES = {"low", "medium", "high"}


def lambda_handler(event, context):
    table = dynamodb.Table(TABLE_NAME)

    # Parsear body
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return error_response(400, "El body debe ser JSON válido.")

    # Validar campo obligatorio
    title = (body.get("title") or "").strip()
    if not title:
        return error_response(400, "El campo 'title' es obligatorio.")
    if len(title) > 100:
        return error_response(400, "El título no puede superar 100 caracteres.")

    priority = body.get("priority", "medium")
    if priority not in VALID_PRIORITIES:
        return error_response(400, f"'priority' debe ser uno de: {', '.join(VALID_PRIORITIES)}.")

    # Construir ítem
    task = {
        "id": str(uuid.uuid4()),
        "title": title,
        "description": (body.get("description") or "").strip(),
        "priority": priority,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        table.put_item(Item=task)
        print(f"Tarea creada: {task['id']} — {task['title']}")
        return {
            "statusCode": 201,
            "headers": cors_headers(),
            "body": json.dumps({"message": "Tarea creada", "task": task})
        }

    except Exception as e:
        print(f"ERROR create_task: {e}")
        return error_response(500, f"Error al guardar la tarea: {str(e)}")


def error_response(status, message):
    return {
        "statusCode": status,
        "headers": cors_headers(),
        "body": json.dumps({"error": message})
    }


def cors_headers():
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
    }
