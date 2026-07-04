from fastapi import Request, HTTPException, status

def verify_patient_access(request: Request, patient_id: str):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    if user.get("role") not in ["clinician", "admin"] and user.get("id") != patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden"
        )
