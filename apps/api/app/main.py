from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.routers.patients import router as patients_router
from app.api.v1.routers.appointments import router as appointments_router
from app.api.v1.routers.consultations import router as consultations_router
from app.api.v1.routers.prescriptions import router as prescriptions_router
from app.api.v1.routers.vitals import router as vitals_router
from app.api.v1.routers.ai import router as ai_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(patients_router, prefix=settings.API_V1_STR)
app.include_router(appointments_router, prefix=settings.API_V1_STR)
app.include_router(consultations_router, prefix=settings.API_V1_STR)
app.include_router(prescriptions_router, prefix=settings.API_V1_STR)
app.include_router(vitals_router, prefix=settings.API_V1_STR)
app.include_router(ai_router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Healthcare Platform API"}
