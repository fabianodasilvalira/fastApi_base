from sqlalchemy.orm import Session

from app.models.ocorrencia import Ocorrencia
from app.schemas.ocorrencia_schemas import OcorrenciaCreate


def create_ocorrencia(db: Session, ocorrencia: OcorrenciaCreate):
    db_ocorrencia = Ocorrencia(**ocorrencia.dict())
    db.add(db_ocorrencia)
    db.commit()
    db.refresh(db_ocorrencia)
    return db_ocorrencia

def get_ocorrencias(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Ocorrencia).offset(skip).limit(limit).all()

def get_ocorrencia_by_id(db: Session, ocorrencia_id: int):
    return db.query(Ocorrencia).filter(Ocorrencia.id == ocorrencia_id).first()
