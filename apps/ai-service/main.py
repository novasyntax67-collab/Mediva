from fastapi import FastAPI
from gateway.router import router as gateway_router

app = FastAPI(title="Mediva Consolidated AI Service", version="1.0.0")

app.include_router(gateway_router)

@app.get("/")
def read_root():
    return {"message": "Mediva Consolidated AI Service is running"}
