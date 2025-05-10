#!/usr/bin/env python3
import json
import requests
import os
from datetime import datetime

# Caminho para o arquivo de dados de teste JSON
TEST_DATA_FILE = "api_test_data.json"
# Caminho para o relatório de teste
TEST_REPORT_FILE = "api_test_report.txt"

# Variáveis globais para armazenar tokens e IDs entre os testes
variables = {}

def replace_variables(data_string, current_variables):
    """Substitui placeholders como {{variable_name}} por seus valores."""
    original_data_string = data_string 
    for key, value in current_variables.items():
        placeholder = f"{{{{{key}}}}}" 
        if value is not None: 
            if placeholder in data_string:
                data_string = data_string.replace(placeholder, str(value))
    return data_string

def run_tests(test_data):
    global variables
    initial_json_vars = test_data.get("variables", {}).copy()
    variables = initial_json_vars
    
    test_suite_name = test_data.get("test_suite_name", "Unnamed Test Suite")
    global_headers = test_data.get("global_headers", {})
    test_cases = test_data.get("test_cases", [])
    
    results = []
    passed_count = 0
    failed_count = 0

    print(f"Iniciando suíte de testes: {test_suite_name}")
    print(f"Total de casos de teste: {len(test_cases)}\n")
    print(f"DEBUG: Variáveis INICIAIS da suíte (após reset e JSON): {variables}")

    for i, case in enumerate(test_cases):
        case_name = case.get("name", f"Caso de Teste Sem Nome {i+1}")
        method = case.get("method", "GET").upper()
        url_template = case.get("url", "")
        payload_template = case.get("payload")
        form_data_template = case.get("form_data")
        headers_template = case.get("headers", {})
        expected_status = case.get("expected_status")
        save_response_map = case.get("save_response", {})

        print(f"Executando teste {i+1}/{len(test_cases)}: {case_name}")

        url = replace_variables(url_template, variables)
        
        current_case_headers = {**global_headers, **headers_template}
        processed_headers = {}
        for h_key, h_value_template in current_case_headers.items():
            processed_headers[h_key] = replace_variables(str(h_value_template), variables)
        
        payload = None
        if payload_template:
            payload_str = json.dumps(payload_template)
            payload_str = replace_variables(payload_str, variables)
            try:
                payload = json.loads(payload_str)
            except json.JSONDecodeError as e:
                print(f"  ERRO ao decodificar payload JSON após substituição: {e}, string era: {payload_str}")
                results.append({"case_name": case_name, "status": "ERRO_INTERNO", "error_message": f"Falha ao decodificar payload: {e}"})
                failed_count += 1
                continue 

        form_data = None
        if form_data_template:
            form_data = {}
            for fd_key, fd_value_template in form_data_template.items():
                form_data[fd_key] = replace_variables(str(fd_value_template), variables)
        
        response = None
        error_message = None
        actual_status = None
        response_json = None
        response_text_preview = None

        try:
            print(f"  {method} {url}")
            if payload:
                print(f"  Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            if form_data:
                 print(f"  Form Data: {form_data}")
            
            safe_headers_log = {k: (v[:25] + "..." if isinstance(v, str) and ("token" in k.lower() or "authorization" in k.lower()) and len(v) > 25 else v) for k,v in processed_headers.items()}
            print(f"  Headers (para request): {safe_headers_log}")

            if method == "POST":
                if payload:
                    response = requests.post(url, json=payload, headers=processed_headers)
                elif form_data:
                    response = requests.post(url, data=form_data, headers=processed_headers)
                else:
                    response = requests.post(url, headers=processed_headers)
            elif method == "GET":
                response = requests.get(url, headers=processed_headers)
            elif method == "PUT":
                response = requests.put(url, json=payload, headers=processed_headers)
            elif method == "DELETE":
                response = requests.delete(url, headers=processed_headers)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")

            actual_status = response.status_code
            response_text_preview = response.text[:500] + ("..." if len(response.text) > 500 else "")
            print(f"  Status Recebido: {actual_status}")
            if response.content:
                try:
                    response_json = response.json()
                except json.JSONDecodeError:
                    print(f"  Resposta não é JSON: {response_text_preview}")
            else:
                print("  Resposta vazia.")

        except requests.exceptions.RequestException as e:
            error_message = f"Erro na requisição: {e}"
            print(f"  {error_message}")
        except Exception as e:
            error_message = f"Erro inesperado durante o teste: {e}"
            print(f"  {error_message}")

        status_match = (expected_status == actual_status)
        result_status = "PASSOU" if status_match else "FALHOU"

        if status_match:
            passed_count += 1
            if response_json and save_response_map:
                for var_name, json_path in save_response_map.items():
                    current_value_from_response = response_json
                    path_keys = json_path.split(".") 
                    valid_path = True
                    for p_key in path_keys:
                        if isinstance(current_value_from_response, dict) and p_key in current_value_from_response:
                            current_value_from_response = current_value_from_response[p_key]
                        elif isinstance(current_value_from_response, list) and p_key.isdigit() and int(p_key) < len(current_value_from_response):
                            current_value_from_response = current_value_from_response[int(p_key)] 
                        else:
                            print(f"  AVISO: Chave/Índice aninhado \'{p_key}\' não encontrado em \'{json_path}\' na resposta para salvar em \'{var_name}\'. Resposta: {str(response_json)[:200]}...")
                            valid_path = False
                            break
                    if valid_path:
                        variables[var_name] = current_value_from_response
                        print(f"  Variável salva: {var_name} = {str(variables[var_name])[:100] + '...' if isinstance(variables[var_name], str) and len(variables[var_name]) > 100 else variables[var_name]}")
        else:
            failed_count += 1
            print(f"  Status esperado: {expected_status}, Recebido: {actual_status}")

        results.append({
            "case_name": case_name,
            "method": method,
            "url": url,
            "status": result_status,
            "expected_status": expected_status,
            "actual_status": actual_status,
            "error_message": error_message,
            "response_preview": response_text_preview
        })
        print(f"  Resultado: {result_status}\n")

    report_content = f"Relatório da Suíte de Testes: {test_suite_name}\n"
    report_content += f"Data da Execução: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" # CORRIGIDO: Aspas internas trocadas para simples
    report_content += f"Total de Casos: {len(test_cases)}\n"
    report_content += f"Passaram: {passed_count}\n"
    report_content += f"Falharam: {failed_count}\n\n"
    report_content += "Detalhes dos Casos:\n"
    report_content += "=====================\n"

    for res in results:
        report_content += f"Caso: {res['case_name']}\n"
        report_content += f"  URL: {res['method']} {res['url']}\n"
        report_content += f"  Resultado: {res['status']}\n"
        report_content += f"  Status Esperado: {res['expected_status']}, Status Recebido: {res['actual_status']}\n"
        if res['error_message']:
            report_content += f"  Erro: {res['error_message']}\n"
        if res['status'] == "FALHOU" and res['response_preview']:
             report_content += f"  Preview da Resposta: {res['response_preview']}\n"
        report_content += "---------------------\n"
    
    with open(TEST_REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print(f"\nRelatório de teste salvo em: {TEST_REPORT_FILE}")
    print(f"Resumo: {passed_count} passaram, {failed_count} falharam.")

if __name__ == "__main__":
    if not os.path.exists(TEST_DATA_FILE):
        print(f"Erro: Arquivo de dados de teste '{TEST_DATA_FILE}' não encontrado na raiz do projeto.")
    else:
        with open(TEST_DATA_FILE, "r", encoding="utf-8") as f:
            test_data_json = json.load(f)
        run_tests(test_data_json)

