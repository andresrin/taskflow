#!/bin/bash
# ============================================================
#  deploy.sh — Script de despliegue inicial de TaskFlow
#  Ejecutar UNA VEZ para crear toda la infraestructura en AWS
#
#  Uso:
#    chmod +x scripts/deploy.sh
#    ./scripts/deploy.sh
#
#  Pre-requisitos:
#    - AWS CLI configurado (aws configure)
#    - Permisos de administrador en la cuenta AWS
# ============================================================

set -e   # Salir si algún comando falla
set -o pipefail

# ─── Colores para output ────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; NC='\033[0m'

log()  { echo -e "${BLUE}[INFO]${NC}  $1"; }
ok()   { echo -e "${GREEN}[OK]${NC}    $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ─── Configuración ──────────────────────────────────────────
PROJECT="taskflow"
REGION="us-east-1"                         # Cambia si prefieres otra región
STACK_NAME="${PROJECT}-stack"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ARTIFACTS_BUCKET="${PROJECT}-artifacts-${ACCOUNT_ID}"
FRONTEND_BUCKET="${PROJECT}-frontend-${ACCOUNT_ID}"

echo ""
echo "══════════════════════════════════════════════════"
echo "  TaskFlow — Despliegue inicial en AWS"
echo "══════════════════════════════════════════════════"
log "Región:          $REGION"
log "Cuenta AWS:      $ACCOUNT_ID"
log "Stack:           $STACK_NAME"
log "Bucket artefact: $ARTIFACTS_BUCKET"
log "Bucket frontend: $FRONTEND_BUCKET"
echo ""

# ─── PASO 1: Crear bucket de artefactos ─────────────────────
log "Paso 1/6: Creando bucket de artefactos..."
if aws s3 ls "s3://${ARTIFACTS_BUCKET}" 2>/dev/null; then
  warn "El bucket ${ARTIFACTS_BUCKET} ya existe. Continuando..."
else
  if [ "$REGION" = "us-east-1" ]; then
    aws s3 mb "s3://${ARTIFACTS_BUCKET}" --region "$REGION"
  else
    aws s3 mb "s3://${ARTIFACTS_BUCKET}" --region "$REGION" \
      --create-bucket-configuration LocationConstraint="$REGION"
  fi
  ok "Bucket de artefactos creado."
fi

# ─── PASO 2: Empaquetar funciones Lambda ────────────────────
log "Paso 2/6: Empaquetando funciones Lambda..."
mkdir -p artifacts

for fn in list_tasks create_task update_task delete_task; do
  cd "backend/${fn}"
  zip -r "../../artifacts/${fn}.zip" . -q
  cd ../..
  ok "  → ${fn}.zip"
done

# ─── PASO 3: Subir ZIPs a S3 ────────────────────────────────
log "Paso 3/6: Subiendo artefactos Lambda a S3..."
for fn in list_tasks create_task update_task delete_task; do
  aws s3 cp "artifacts/${fn}.zip" "s3://${ARTIFACTS_BUCKET}/${fn}.zip" --quiet
  ok "  → ${fn}.zip subido."
done

# ─── PASO 4: Desplegar CloudFormation ───────────────────────
log "Paso 4/6: Desplegando infraestructura con CloudFormation..."
aws cloudformation deploy \
  --template-file infrastructure/template.yaml \
  --stack-name "$STACK_NAME" \
  --parameter-overrides \
    ProjectName="$PROJECT" \
    ArtifactsBucket="$ARTIFACTS_BUCKET" \
    Environment="prod" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "$REGION" \
  --no-fail-on-empty-changeset

ok "CloudFormation stack desplegado."

# ─── PASO 5: Obtener outputs ────────────────────────────────
log "Paso 5/6: Obteniendo URLs del stack..."

API_URL=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
  --output text)

FRONTEND_URL=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendUrl'].OutputValue" \
  --output text)

CF_FRONTEND_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
  --output text)

# ─── PASO 6: Actualizar API_URL en app.js y subir frontend ──
log "Paso 6/6: Actualizando API_URL en frontend y desplegando..."
sed -i "s|https://TU_API_GATEWAY_URL/prod|${API_URL}|g" frontend/app.js
aws s3 sync frontend/ "s3://${CF_FRONTEND_BUCKET}/" --delete --quiet
ok "Frontend desplegado con la URL correcta."

# ─── Resumen final ───────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════════════"
echo -e "  ${GREEN}✓ Deploy completado exitosamente${NC}"
echo "══════════════════════════════════════════════════"
echo ""
echo -e "  ${BLUE}API REST:${NC}  $API_URL"
echo -e "  ${BLUE}Frontend:${NC}  $FRONTEND_URL"
echo ""
echo "  Endpoints disponibles:"
echo "    GET    ${API_URL}/tasks"
echo "    POST   ${API_URL}/tasks"
echo "    PUT    ${API_URL}/tasks/{id}"
echo "    DELETE ${API_URL}/tasks/{id}"
echo ""
echo "  Guarda la API_URL — la necesitarás para pruebas manuales."
echo "══════════════════════════════════════════════════"
