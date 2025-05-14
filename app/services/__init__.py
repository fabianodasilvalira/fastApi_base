from .user_service import user_service
from .ocorrencia_service import create_ocorrencia, get_ocorrencias, get_ocorrencia_by_id # Manter existentes
from .parecer_service import ( # Adicionado Parecer Service
    create_parecer,
    get_pareceres,
    get_parecer_by_id,
    update_parecer,
    delete_parecer
)
from .sistemas_autorizados_service import ( # Adicionado Sistemas Autorizados Service
    criar_sistema_autorizado,
    get_sistemas_autorizados,
    get_sistema_autorizado_by_id,
    get_sistema_autorizado_by_token,
    validar_token_sistema,
    atualizar_ultima_atividade_sistema,
    update_sistema_autorizado,
)

__all__ = [
    "user_service",
    "create_ocorrencia",
    "get_ocorrencias",
    "get_ocorrencia_by_id",
    "create_parecer",
    "get_pareceres",
    "get_parecer_by_id",
    "update_parecer",
    "delete_parecer",
    "criar_sistema_autorizado",
    "get_sistemas_autorizados",
    "get_sistema_autorizado_by_id",
    "get_sistema_autorizado_by_token",
    "validar_token_sistema",
    "atualizar_ultima_atividade_sistema",
    "update_sistema_autorizado",
]
