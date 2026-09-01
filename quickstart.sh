#!/bin/bash
# =============================================================================
# quickstart.sh — 1-Click Reproducibility Runner for Segula AI Requirement Hub
# =============================================================================
set -e

GREEN='[0;32m'
BLUE='[0;34m'
YELLOW='[1;33m'
RED='[0;31m'
NC='[0m' # No Color
BOLD='[1m'

echo -e "${BLUE}${BOLD}===========================================================================${NC}"
echo -e "${BLUE}${BOLD}⚡ SEGULA AI REQUIREMENT HUB — 1-CLICK SOVEREIGN STACK LAUNCHER           ${NC}"
echo -e "${BLUE}${BOLD}===========================================================================${NC}"

# 1. Check Docker & Docker Compose prerequisites
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Error: Docker is not installed. Please install Docker first: https://docs.docker.com/get-docker/${NC}"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Error: Docker daemon is not running. Please start Docker service.${NC}"
    exit 1
fi

# 2. Check and initialize .env file
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚙️ No .env file found. Creating .env from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ Created .env configuration file.${NC}"
    echo -e "${YELLOW}ℹ️  NOTE: Remember to paste your Lightning AI Studio URL in .env (VLLM_BASE_URL & OLLAMA_BASE_URL)${NC}"
fi

# 3. Check and initialize postgres environment file
if [ ! -f docker/env/.env.postgres ]; then
    mkdir -p docker/env
    echo -e "${YELLOW}⚙️ Creating docker/env/.env.postgres default credentials...${NC}"
    cat << 'ENV_PG' > docker/env/.env.postgres
POSTGRES_DB=requirementshub
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
ENV_PG
    echo -e "${GREEN}✅ Created docker/env/.env.postgres${NC}"
fi

# 4. Build and start full stack in detached mode
echo -e "
${BLUE}🚀 Building and starting Segula AI Requirement Hub containers...${NC}"
docker compose -f docker/docker-compose.yml up --build -d

echo -e "
${GREEN}${BOLD}===========================================================================${NC}"
echo -e "${GREEN}${BOLD}🎉 SEGULA AI REQUIREMENT HUB IS UP AND RUNNING!                            ${NC}"
echo -e "${GREEN}${BOLD}===========================================================================${NC}"
echo -e "  🌐 ${BOLD}Web Application (React 19 SPA):${NC}  http://localhost:5173"
echo -e "  📖 ${BOLD}FastAPI Backend & API Docs:${NC}      http://localhost:8000/docs"
echo -e "  🗄️  ${BOLD}PostgreSQL Adminer (DB Viewer):${NC}  http://localhost:8085"
echo -e "${GREEN}───────────────────────────────────────────────────────────────────────────${NC}"
echo -e "  🔍 ${BOLD}View Live Logs:${NC} docker compose -f docker/docker-compose.yml logs -f"
echo -e "  🛑 ${BOLD}Stop All:${NC}       docker compose -f docker/docker-compose.yml down"
echo -e "${GREEN}===========================================================================${NC}
"
