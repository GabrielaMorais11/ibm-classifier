from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from openpyxl import load_workbook, Workbook
from io import BytesIO
from datetime import datetime
import os

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

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
    
    if normalized in MASTER_DATA:
        return MASTER_DATA[normalized], 'Base Mestre', '100%'
    
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
        'timestamp': datetime.now().isoformat()
    })

@app.route('/classify', methods=['POST'])
def classify():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'Nome vazio'}), 400
        
        # Ler Excel
        wb = load_workbook(filename=BytesIO(file.read()))
        ws = wb.active
        
        # Adicionar colunas de classificação
        max_col = ws.max_column
        ws.cell(1, max_col + 1, 'Classificacao')
        ws.cell(1, max_col + 2, 'Metodo')
        ws.cell(1, max_col + 3, 'Confianca')
        
        # Classificar cada linha
        for row in range(2, ws.max_row + 1):
            account_name = ws.cell(row, 1).value
            classification, method, confidence = find_classification(account_name)
            
            ws.cell(row, max_col + 1, classification)
            ws.cell(row, max_col + 2, method)
            ws.cell(row, max_col + 3, confidence)
        
        # Salvar em BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'contas_classificadas_{timestamp}.xlsx'
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"Erro: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
