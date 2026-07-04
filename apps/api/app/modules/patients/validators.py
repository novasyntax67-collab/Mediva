from datetime import date
from fastapi import HTTPException, status

def validate_birth_date(birth_date: date):
    if birth_date > date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Birth date cannot be in the future"
        )
