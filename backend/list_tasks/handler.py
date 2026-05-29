"""
Lambda: list_tasks
GET /tasks
Retorna todas las tareas de DynamoDB.
"""

import json
import os
import boto3
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ.get("TABLE_NAME", "taskflow-tasks")


def lambda_handler(event, context):
    table = dynamodb.Table(TABLE_NAME)

    try:
        response = table.scan()
        tasks = response.get("Items", [])

        # Soporte para paginación (si hay muchos registros)
        while "LastEvaluatedKey" in response:
            response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            tasks.extend(response.get("Items", []))

        return {
            "statusCode": 200,
            "headers": cors_headers(),
            "body": json.dumps({
                "tasks": tasks,
                "count": len(tasks)
            }, default=str)
        }

    except Exception as e:
        print(f"ERROR list_tasks: {e}")
        return {
            "statusCode": 500,
            "headers": cors_headers(),
            "body": json.dumps({"error": "Error interno al listar tareas", "detail": str(e)})
        }


def cors_headers():
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
    }
