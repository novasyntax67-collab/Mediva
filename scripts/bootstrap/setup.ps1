Write-Host "Setting up Carex Project Workspace..." -ForegroundColor Green
Copy-Item .env.web.example -Destination apps/web/.env
Copy-Item .env.api.example -Destination apps/api/.env
Copy-Item .env.worker.example -Destination apps/worker/.env
Copy-Item .env.ai.example -Destination apps/ai-service/.env
pnpm install --ignore-scripts
Write-Host "Workspace Setup Complete!" -ForegroundColor Green
