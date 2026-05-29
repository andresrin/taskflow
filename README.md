# ⚡ TaskFlow — Gestor de Tareas Serverless en AWS

Aplicación web serverless para gestión de tareas, desplegada completamente sobre AWS.
Arquitectura: **Lambda + API Gateway + DynamoDB + S3 + CloudWatch + IAM + CodePipeline/CodeBuild**.

---

## 🏗️ Arquitectura

```
Navegador → S3 (frontend) → API Gateway → Lambda → DynamoDB
                                              ↓
                                         CloudWatch (logs)
                                              ↑
                                      IAM (roles y permisos)
```

## 📁 Estructura del repositorio

```
taskflow/
├── frontend/
│   ├── index.html          ← Interfaz de usuario
│   ├── style.css           ← Estilos dark mode
│   └── app.js              ← Llamadas a la API REST
├── backend/
│   ├── list_tasks/
│   │   └── handler.py      ← GET /tasks
│   ├── create_task/
│   │   └── handler.py      ← POST /tasks
│   ├── update_task/
│   │   └── handler.py      ← PUT /tasks/{id}
│   └── delete_task/
│       └── handler.py      ← DELETE /tasks/{id}
├── infrastructure/
│   └── template.yaml       ← CloudFormation (toda la infraestructura)
├── tests/
│   └── test_tasks.py       ← Pruebas unitarias (pytest)
├── scripts/
│   ├── deploy.sh           ← Deploy inicial completo
│   ├── teardown.sh         ← Eliminar toda la infraestructura
│   └── test_api.sh         ← Probar endpoints manualmente
├── buildspec.yml           ← Instrucciones para CodeBuild (CI/CD)
├── .gitignore
└── README.md
```

## 🚀 Despliegue rápido

### Pre-requisitos
- Cuenta AWS activa
- AWS CLI instalado y configurado (`aws configure`)
- Git instalado

### 1. Clonar el repositorio
```bash
git clone https://github.com/TU_USUARIO/taskflow.git
cd taskflow
```

### 2. Desplegar en AWS (un solo comando)
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

El script crea automáticamente:
- Bucket S3 para artefactos Lambda
- Infraestructura completa via CloudFormation
- Sube el frontend al bucket S3
- Configura la URL de la API en el frontend

### 3. Probar los endpoints
```bash
chmod +x scripts/test_api.sh
./scripts/test_api.sh https://TU_URL.execute-api.us-east-1.amazonaws.com/prod
```

## 📡 API Endpoints

| Método | Endpoint       | Descripción             |
|--------|----------------|-------------------------|
| GET    | /tasks         | Listar todas las tareas |
| POST   | /tasks         | Crear nueva tarea        |
| PUT    | /tasks/{id}    | Actualizar tarea         |
| DELETE | /tasks/{id}    | Eliminar tarea           |

### Ejemplo de uso con curl

```bash
# Crear tarea
curl -X POST https://TU_URL/prod/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Mi tarea","priority":"high"}'

# Listar tareas
curl https://TU_URL/prod/tasks
```

## 🧪 Pruebas unitarias

```bash
# Instalar pytest
pip install pytest

# Ejecutar pruebas
python -m pytest tests/ -v
```

## 💸 Costos estimados

Operando dentro del **AWS Free Tier**: **~$0.00/mes** en uso académico.

## 🗑️ Eliminar infraestructura

```bash
chmod +x scripts/teardown.sh
./scripts/teardown.sh
```

---

**Proyecto universitario** · Arquitectura Cloud AWS · DevOps & CI/CD
