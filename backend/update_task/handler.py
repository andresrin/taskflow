"""
Lambda: update_task
PUT /tasks/{id}
Actualiza el estado (y opcionalmente título/descripción/prioridad) de una tarea.
Body esperado (JSON) — todos opcionales:
  {
    "status": "pending | done",
    "title": "string",
    "description": "string",
    "priority": "low | medium | high"
  }
"""

import json
import os
import boto3
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ.get("TABLE_NAME", "taskflow-tasks")

VALID_STATUSES   = {"pending", "done"}
VALID_PRIORITIES = {"low", "medium", "high"}


def lambda_handler(event, context):
    table = dynamodb.Table(TABLE_NAME)

    # Obtener ID del path
    task_id = (event.get("pathParameters") or {}).get("id")
    if not task_id:
        return error_response(400, "Falta el parámetro 'id' en la URL.")

    # Parsear body
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return error_response(400, "El body debe ser JSON válido.")

    if not body:
        return error_response(400, "Debes enviar al menos un campo para actualizar.")

    # Verificar que la tarea existe
    existing = table.get_item(Key={"id": task_id}).get("Item")
    if not existing:
        return error_response(404, f"Tarea '{task_id}' no encontrada.")

    # Construir expresión de actualización dinámica
    update_expr_parts = []
    expr_attr_values  = {}
    expr_attr_names   = {}

    if "status" in body:
        if body["status"] not in VALID_STATUSES:
            return error_response(400, f"'status' debe ser: {', '.join(VALID_STATUSES)}.")
        update_expr_parts.append("#st = :status")
        expr_attr_values[":status"] = body["status"]
        expr_attr_names["#st"] = "status"   # 'status' es palabra reservada en DynamoDB

    if "title" in body:
        title = body["title"].strip()
        if not title or len(title) > 100:
            return error_response(400, "El título debe tener entre 1 y 100 caracteres.")
        update_expr_parts.append("title = :title")
        expr_attr_values[":title"] = title

    if "description" in body:
        update_expr_parts.append("description = :desc")
        expr_attr_values[":desc"] = body["description"].strip()

    if "priority" in body:
        if body["priority"] not in VALID_PRIORITIES:
            return error_response(400, f"'priority' debe ser: {', '.join(VALID_PRIORITIES)}.")
        update_expr_parts.append("priority = :priority")
        expr_attr_values[":priority"] = body["priority"]

    # Siempre actualizar updated_at
    update_expr_parts.append("updated_at = :updated_at")
    expr_attr_values[":updated_at"] = datetime.now(timezone.utc).isoformat()

    try:
        response = table.update_item(
            Key={"id": task_id},
            UpdateExpression="SET " + ", ".join(update_expr_parts),
            ExpressionAttributeValues=expr_attr_values,
            ExpressionAttributeNames=expr_attr_names if expr_attr_names else None,
            ReturnValues="ALL_NEW"
        )

        updated = response.get("Attributes", {})
        print(f"Tarea actualizada: {task_id}")
        return {
            "statusCode": 200,
            "headers": cors_headers(),
            "body": json.dumps({"message": "Tarea actualizada", "task": updated}, default=str)
        }

    except Exception as e:
        print(f"ERROR update_task: {e}")
        return error_response(500, f"Error al actualizar: {str(e)}")


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
