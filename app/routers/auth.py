from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_db
from app.schemas.token import Token
from app.core.security import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, create_refresh_token, \
    REFRESH_TOKEN_EXPIRE_DAYS, decode_token
from app.schemas.user import LoginInput, UserResponse, LoginResponse
from app.services.user_service import get_user_by_email

router = APIRouter()


@router.post("/login", response_model=LoginResponse, summary="Login de usuário",
             description="Autentica um usuário com email e senha, retornando tokens de acesso e refresh.")
async def login(credentials: LoginInput, db: AsyncSession = Depends(get_async_db)):
    """
    Realiza o login do usuário com email e senha.

    Args:
        credentials: Credenciais de login (email e senha)
        db: Sessão do banco de dados

    Returns:
        Token de acesso, refresh token e dados do usuário
    """
    user = await get_user_by_email(db, credentials.email)
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-mail ou senha incorretos"
        )

    # Cria os tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "perfil": user.perfil},
        expires_delta=access_token_expires
    )

    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        data={"sub": user.email},
        expires_delta=refresh_token_expires
    )

    # Prepara a resposta com os dados do usuário
    user_data = UserResponse(
        id=user.id,
        username=user.username,
        name=user.name,
        email=user.email,
        perfil=user.perfil,
        status=user.status
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user_data.dict()
    }


@router.post("/refresh", response_model=Token, summary="Renovar token de acesso",
             description="Renova o token de acesso usando um refresh token válido.")
async def refresh(refresh_token: str, db: AsyncSession = Depends(get_async_db)):
    """
    Renova o token de acesso usando um refresh token válido.
    
    Args:
        refresh_token: Token de refresh
        db: Sessão do banco de dados
        
    Returns:
        Novo token de acesso e refresh token
    """
    payload = decode_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Token de refresh inválido"
        )

    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Payload do token inválido"
        )
    
    # Verifica se o usuário ainda existe
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )

    # Cria novos tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "perfil": user.perfil},
        expires_delta=access_token_expires
    )

    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    new_refresh_token = create_refresh_token(
        data={"sub": user.email},
        expires_delta=refresh_token_expires
    )

    # Prepara a resposta com os dados do usuário
    user_data = UserResponse(
        id=user.id,
        username=user.username,
        name=user.name,
        email=user.email,
        perfil=user.perfil,
        status=user.status
    )

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user": user_data
    }


@router.post("/gov-br/callback", response_model=Token, summary="Callback de autenticação gov.br",
             description="Recebe o redirecionamento após autenticação bem-sucedida no gov.br.")
async def gov_br_callback(code: str, db: AsyncSession = Depends(get_async_db)):
    """
    Recebe o código de autorização do gov.br após autenticação bem-sucedida.
    Verifica se o usuário existe no sistema e cria um novo usuário se necessário.
    
    Args:
        code: Código de autorização retornado pelo gov.br
        db: Sessão do banco de dados
        
    Returns:
        Token de acesso, refresh token e dados do usuário
    """
    # TODO: Implementar a troca do código por tokens do gov.br
    # Esta é uma implementação inicial que será ajustada conforme a documentação específica do gov.br
    
    try:
        # Aqui seria feita a chamada para a API do gov.br para obter os dados do usuário
        # usando o código de autorização recebido
        
        # Simulação de dados recebidos do gov.br
        gov_br_user_data = {
            "cpf": "12345678900",  # Este valor seria obtido da resposta do gov.br
            "nome": "Nome do Usuário",  # Este valor seria obtido da resposta do gov.br
            "email": "usuario@exemplo.com",  # Este valor seria obtido da resposta do gov.br
        }
        
        # Verifica se o usuário já existe no sistema
        user = await get_user_by_email(db, gov_br_user_data["email"])
        
        if not user:
            # Se o usuário não existir, cria um novo usuário
            from app.schemas.user import UserCreate
            from app.services.user_service import user_service
            import secrets
            
            # Gera uma senha aleatória para o usuário (ele pode alterar depois)
            random_password = secrets.token_urlsafe(12)
            
            # Cria o objeto de criação de usuário
            user_create = UserCreate(
                username=gov_br_user_data["email"].split("@")[0],  # Usa parte do email como username
                name=gov_br_user_data["nome"],
                cpf=gov_br_user_data["cpf"],
                email=gov_br_user_data["email"],
                password=random_password,
                perfil="Usuário",  # Perfil padrão
                status=10  # Status ativo
            )
            
            # Cria o usuário no banco de dados
            user = await user_service.create_user(db=db, user_in=user_create)
        
        # Gera tokens para o usuário
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id, "perfil": user.perfil},
            expires_delta=access_token_expires
        )

        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token = create_refresh_token(
            data={"sub": user.email},
            expires_delta=refresh_token_expires
        )

        # Prepara a resposta com os dados do usuário
        user_data = UserResponse(
            id=user.id,
            username=user.username,
            name=user.name,
            email=user.email,
            perfil=user.perfil,
            status=user.status
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar autenticação do gov.br: {str(e)}"
        )
