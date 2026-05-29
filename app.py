from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import os
from io import BytesIO
from datetime import datetime
from difflib import get_close_matches

app = Flask(__name__)
CORS(app)

# Configurações
MASTER_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'contas_ibm_exemplo.csv')

# Carregar base de dados mestre
def load_master_data():
    """Carrega a base de dados mestre com as classificações"""
    try:
        df = pd.read_csv(MASTER_DATA_PATH)
        return df
    except Exception as e:
        print(f"Erro ao carregar base mestre: {e}")
        return pd.DataFrame(columns=['Nome da Conta', 'Classificacao'])

# Função de matching fuzzy
def find_best_match(account_name, master_accounts, threshold=0.6):
    """
    Encontra a melhor correspondência para um nome de conta
    usando matching fuzzy
    """
    if not account_name or pd.isna(account_name):
        return None, 0
    
    account_name_clean = str(account_name).strip().lower()
    master_accounts_clean = [str(acc).strip().lower() for acc in master_accounts]
    
    # Busca exata primeiro
    if account_name_clean in master_accounts_clean:
        idx = master_accounts_clean.index(account_name_clean)
        return master_accounts[idx], 1.0
    
    # Busca fuzzy
    matches = get_close_matches(account_name_clean, master_accounts_clean, n=1, cutoff=threshold)
    
    if matches:
        idx = master_accounts_clean.index(matches[0])
        # Calcular score de similaridade simples
        score = len(set(account_name_clean.split()) & set(matches[0].split())) / max(len(account_name_clean.split()), len(matches[0].split()))
        return master_accounts[idx], score
    
    return None, 0


# Função principal de classificação
def classify_accounts(input_df, master_df):
    """
    Classifica as contas do arquivo de entrada usando a base mestre
    """
    # Identificar coluna com nomes de contas
    possible_columns = ['nome', 'conta', 'cliente', 'empresa', 'account', 'name', 'company']
    account_column = None
    
    for col in input_df.columns:
        if any(keyword in col.lower() for keyword in possible_columns):
            account_column = col
            break
    
    if account_column is None:
        # Usar primeira coluna como padrão
        account_column = input_df.columns[0]
    
    # Criar cópia do dataframe
    result_df = input_df.copy()
    
    # Adicionar colunas de classificação
    result_df['Classificacao'] = ''
    result_df['Metodo'] = ''
    result_df['Confianca'] = ''
    
    master_accounts = master_df['Nome da Conta'].tolist()
    
    # Classificar cada conta
    for idx, row in result_df.iterrows():
        account_name = row[account_column]
        
        # Tentar matching fuzzy primeiro
        matched_account, score = find_best_match(account_name, master_accounts)
        
        if matched_account and score >= 0.6:
            # Encontrou match na base mestre
            classification = master_df[master_df['Nome da Conta'] == matched_account]['Classificacao'].iloc[0]
            result_df.at[idx, 'Classificacao'] = classification
            result_df.at[idx, 'Metodo'] = 'Base Mestre'
            result_df.at[idx, 'Confianca'] = f'{score:.0%}'
        else:
            # Não encontrou - marcar como não classificado
            result_df.at[idx, 'Classificacao'] = 'Não Classificado'
            result_df.at[idx, 'Metodo'] = 'Não encontrado na base'
            result_df.at[idx, 'Confianca'] = '0%'
    
    return result_df

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint para verificar se a API está funcionando"""
    return jsonify({
        'status': 'ok',
        'message': 'API está funcionando',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/classify', methods=['POST'])
def classify():
    """Endpoint principal para classificar contas"""
    try:
        # Verificar se arquivo foi enviado
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'Nome de arquivo vazio'}), 400
        
        # Verificar extensão
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Formato de arquivo inválido. Use .xlsx ou .xls'}), 400
        
        # Ler arquivo Excel
        try:
            input_df = pd.read_excel(file)
        except Exception as e:
            return jsonify({'error': f'Erro ao ler arquivo Excel: {str(e)}'}), 400
        
        if input_df.empty:
            return jsonify({'error': 'Arquivo Excel está vazio'}), 400
        
        # Carregar base mestre
        master_df = load_master_data()
        
        if master_df.empty:
            return jsonify({'error': 'Base de dados mestre não encontrada'}), 500
        
        # Classificar contas
        result_df = classify_accounts(input_df, master_df)
        
        # Gerar arquivo Excel de saída
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            result_df.to_excel(writer, index=False, sheet_name='Contas Classificadas')
        
        output.seek(0)
        
        # Gerar nome do arquivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'contas_classificadas_{timestamp}.xlsx'
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"Erro no processamento: {e}")
        return jsonify({'error': f'Erro ao processar arquivo: {str(e)}'}), 500

@app.route('/update-master', methods=['POST'])
def update_master():
    """Endpoint para atualizar a base de dados mestre"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        
        # Ler novo arquivo mestre
        new_master_df = pd.read_csv(file) if file.filename.endswith('.csv') else pd.read_excel(file)
        
        # Validar colunas
        required_columns = ['Nome da Conta', 'Classificacao']
        if not all(col in new_master_df.columns for col in required_columns):
            return jsonify({'error': f'Arquivo deve conter as colunas: {required_columns}'}), 400
        
        # Salvar novo arquivo mestre
        new_master_df.to_csv(MASTER_DATA_PATH, index=False)
        
        return jsonify({
            'message': 'Base de dados mestre atualizada com sucesso',
            'total_accounts': len(new_master_df)
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao atualizar base mestre: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

# Made with Bob
