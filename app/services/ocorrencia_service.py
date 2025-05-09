from sqlalchemy.orm import Session
from . import models, schemas

def create_ocorrencia(db: Session, ocorrencia: schemas.OcorrenciaCreate):
    db_item = models.Ocorrencia(**ocorrencia.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_ocorrencia(db: Session, ocorrencia_id: int):
    return db.query(models.Ocorrencia).filter(models.Ocorrencia.id == ocorrencia_id).first()

def get_ocorrencias(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Ocorrencia).offset(skip).limit(limit).all()

def update_ocorrencia(db: Session, ocorrencia_id: int, ocorrencia_data: schemas.OcorrenciaCreate):
    ocorrencia = get_ocorrencia(db, ocorrencia_id)
    if ocorrencia:
        for key, value in ocorrencia_data.dict().items():
            setattr(ocorrencia, key, value)
        db.commit()
        db.refresh(ocorrencia)
    return ocorrencia

def delete_ocorrencia(db: Session, ocorrencia_id: int):
    ocorrencia = get_ocorrencia(db, ocorrencia_id)
    if ocorrencia:
        db.delete(ocorrencia)
        db.commit()
    return ocorrencia
