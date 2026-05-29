from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import csv
from io import StringIO, BytesIO
from datetime import datetime
import os

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Base de dados mestre
MASTER_DATA = {
    'banco do brasil': 'Enterprise',
    'petrobras': 'Enterprise',
    'vale': 'Enterprise',
    'itau unibanco': 'Strategic',
    'itaú unibanco': 'Strategic',
    'bradesco': 'Strategic',
    'ambev': 'Strategic',
    'natura': 'Select Horizon',
    'magazine luiza': 'Select Horizon',
    'localiza': 'Select Horizon',
    'totvs': 'Select T',
    'linx': 'Select T',
    'senior sistemas': 'Select T',
}

def normalize(text):
    if not text:
        return ''
    return str(text).strip().lower()

def find_classification(account_name):
    normalized = normalize(account_name)
    
    # Busca exata
    if normalized in MASTER_DATA:
        return MASTER_DATA[normalized], 'Base Mestre', '100%'
    
    # Busca parcial
    for key in MASTER_DATA:
        if key in normalized or normalized in key:
            return MASTER_DATA[key], 'Base Mestre', '80%'
    
    return 'Não Classificado', 'Não encontrado', '0%'

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'message': 'API funcionando',
        'timestamp': datetime.now().isoformat(),
        'total_contas': len(MASTER_DATA)
    })

@app.route('/classify', methods=['POST'])
def classify():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'Nome vazio'}), 400
        
        # Ler arquivo como texto
        content = file.read().decode('utf-8', errors='ignore')
        
        # Processar CSV
        lines = content.strip().split('\n')
        if not lines:
            return jsonify({'error': 'Arquivo vazio'}), 400
        
        # Criar resultado
        result_lines = []
        header = lines[0] + ',Classificacao,Metodo,Confianca'
        result_lines.append(header)
        
        for line in lines[1:]:
            if not line.strip():
                continue
            
            parts = line.split(',')
            if not parts:
                continue
            
            account_name = parts[0]
            classification, method, confidence = find_classification(account_name)
            
            result_line = line + f',{classification},{method},{confidence}'
            result_lines.append(result_line)
        
        # Gerar CSV de saída
        output = '\n'.join(result_lines)
        
        # Retornar arquivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'contas_classificadas_{timestamp}.csv'
        
        return send_file(
            BytesIO(output.encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"Erro: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
