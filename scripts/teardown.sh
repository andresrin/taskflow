#!/bin/bash
# ============================================================
#  teardown.sh — Eliminar TODA la infraestructura de TaskFlow
#  Útil para evitar costos después de la presentación.
#
#  Uso:
#    chmod +x scripts/teardown.sh
#    ./scripts/teardown.sh
# ============================================================

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; NC='\033[0m'

PROJECT="taskflow"
REGION="us-east-1"
STACK_NAME="${PROJECT}-stack"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ARTIFACTS_BUCKET="${PROJECT}-artifacts-${ACCOUNT_ID}"

echo ""
echo -e "${RED}══════════════════════════════════════════════════${NC}"
echo -e "${RED}  ⚠  TEARDOWN — Eliminar infraestructura TaskFlow${NC}"
echo -e "${RED}══════════════════════════════════════════════════${NC}"
echo ""
read -p "¿Estás seguro? Esto eliminará DynamoDB, Lambda, API Gateway y S3. (escribe 'si'): " CONFIRM

if [ "$CONFIRM" != "si" ]; then
  echo "Operación cancelada."
  exit 0
fi

echo ""
echo -e "${BLUE}[1/3]${NC} Vaciando bucket de artefactos..."
aws s3 rm "s3://${ARTIFACTS_BUCKET}" --recursive --quiet 2>/dev/null || true
aws s3 rb "s3://${ARTIFACTS_BUCKET}" --force 2>/dev/null || true
echo -e "${GREEN}✓${NC} Bucket de artefactos eliminado."

echo -e "${BLUE}[2/3]${NC} Vaciando bucket frontend (CloudFormation lo eliminará)..."
CF_FRONTEND_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
  --output text 2>/dev/null || echo "")

if [ -n "$CF_FRONTEND_BUCKET" ]; then
  aws s3 rm "s3://${CF_FRONTEND_BUCKET}" --recursive --quiet 2>/dev/null || true
fi

echo -e "${BLUE}[3/3]${NC} Eliminando stack CloudFormation..."
aws cloudformation delete-stack --stack-name "$STACK_NAME" --region "$REGION"
aws cloudformation wait stack-delete-complete --stack-name "$STACK_NAME" --region "$REGION"
echo -e "${GREEN}✓${NC} Stack eliminado."

echo ""
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✓ Teardown completado. Costo: $0.00${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
