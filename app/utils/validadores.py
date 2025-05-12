import re


# Validação de CPF
def validar_cpf(cpf: str) -> bool:
    # Remover caracteres não numéricos
    cpf = re.sub(r'\D', '', cpf)

    # Verificar se o CPF tem 11 dígitos
    if len(cpf) != 11:
        return False

    # CPF's repetidos como 111.111.111.11, 222.222.222.22, etc. são inválidos
    if cpf == cpf[0] * 11:
        return False

    # Validação do CPF utilizando os dígitos verificadores
    def calcular_digito(cpf: str, peso: list) -> int:
        soma = sum(int(cpf[i]) * peso[i] for i in range(len(peso)))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    peso1 = [10, 9, 8, 7, 6, 5, 4, 3, 2]
    peso2 = [11, 10, 9, 8, 7, 6, 5, 4, 3, 2]

    digito1 = calcular_digito(cpf, peso1)
    digito2 = calcular_digito(cpf, peso2)

    return cpf[-2:] == f"{digito1}{digito2}"


# Validação de e-mail
def validar_email(email: str) -> bool:
    # Expressão regular para validar o formato de e-mail
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(regex, email))
