"""
Lambda: delete_task
DELETE /tasks/{id}
Elimina una tarea de DynamoDB por su ID.
"""

import json
import os
import boto3

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ.get("TABLE_NAME", "taskflow-tasks")


def lambda_handler(event, context):
    table = dynamodb.Table(TABLE_NAME)

    # Obtener ID del path
    task_id = (event.get("pathParameters") or {}).get("id")
    if not task_id:
        return error_response(400, "Falta el parámetro 'id' en la URL.")

    # Verificar que existe antes de eliminar
    existing = table.get_item(Key={"id": task_id}).get("Item")
    if not existing:
        return error_response(404, f"Tarea '{task_id}' no encontrada.")

    try:
        table.delete_item(Key={"id": task_id})
        print(f"Tarea eliminada: {task_id} — {existing.get('title', '')}")
        return {
            "statusCode": 200,
            "headers": cors_headers(),
            "body": json.dumps({
                "message": "Tarea eliminada correctamente",
                "id": task_id
            })
        }

    except Exception as e:
        print(f"ERROR delete_task: {e}")
        return error_response(500, f"Error al eliminar: {str(e)}")


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
