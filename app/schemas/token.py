# app/schemas/token.py
from typing import Optional

from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None # Opcional, nem sempre é retornado
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[str] = None # "sub" é o campo padrão para o sujeito (usuário, e.g., email)
    # Adicione outros campos que você espera no payload do token, se necessário
    # user_id: Optional[int] = None
    # role: Optional[str] = None

# Comentários em português:
# - `Token`: Esquema para a resposta do token que é enviada ao cliente após o login.
#   Inclui o `access_token`, opcionalmente um `refresh_token`, e o `token_type` (geralmente "bearer").
# - `TokenPayload`: Esquema para os dados contidos dentro do JWT (o payload).
#   `sub` (subject) é um campo padrão em JWTs para identificar o principal (usuário) a quem o token se refere.
#   Pode ser estendido para incluir outros dados como ID do usuário, papel, etc., conforme definido em `security.py`.

