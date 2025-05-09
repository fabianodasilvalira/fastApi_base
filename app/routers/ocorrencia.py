from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import schemas, services, database

router = APIRouter(prefix="/ocorrencias", tags=["Ocorrências"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.OcorrenciaOut)
def create(ocorrencia: schemas.OcorrenciaCreate, db: Session = Depends(get_db)):
    return services.create_ocorrencia(db, ocorrencia)

@router.get("/", response_model=List[schemas.OcorrenciaOut])
def read_all(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return services.get_ocorrencias(db, skip, limit)

@router.get("/{ocorrencia_id}", response_model=schemas.OcorrenciaOut)
def read_one(ocorrencia_id: int, db: Session = Depends(get_db)):
    db_item = services.get_ocorrencia(db, ocorrencia_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada")
    return db_item

@router.put("/{ocorrencia_id}", response_model=schemas.OcorrenciaOut)
def update(ocorrencia_id: int, ocorrencia: schemas.OcorrenciaCreate, db: Session = Depends(get_db)):
    return services.update_ocorrencia(db, ocorrencia_id, ocorrencia)

@router.delete("/{ocorrencia_id}")
def delete(ocorrencia_id: int, db: Session = Depends(get_db)):
    return services.delete_ocorrencia(db, ocorrencia_id)
