from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import pandas as pd
from io import BytesIO
from datetime import datetime
from difflib import get_close_matches
import os
import unicodedata
import re

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Base de dados mestre - EDITE AQUI para adicionar/remover contas
MASTER_DATA = {
    # Contas originais
    "BANCO DO BRASIL": "Enterprise",
    "PETROBRAS": "Enterprise",
    "VALE": "Enterprise",
    "ITAU UNIBANCO": "Strategic",
    "BRADESCO": "Strategic",
    "AMBEV": "Strategic",
    "NATURA": "Select Horizon",
    "MAGAZINE LUIZA": "Select Horizon",
    "LOCALIZA": "Select Horizon",
    "TOTVS": "Select T",
    "LINX": "Select T",
    "SENIOR SISTEMAS": "Select T",
    
    # Novas contas
    "AB MAURI": "Select T",
    "ACHE": "Select T",
    "ADAMA": "Select T",
    "AGREX": "Select T",
    "ALL4LABELS": "Select T",
    "BAUMGARTEN GRAFICA": "Select T",
    "ALPARGATAS": "Select T",
    "ANGELONI": "Select T",
    "APERAM SOUTH AMERICA": "Select T",
    "ARCELORMITTAL BRASIL": "Select Horizon",
    "AREZZO&CO": "Select T",
    "AREZZO CO": "Select T",
    "ATACADAO DIA A DIA": "Select T",
    "AURORA ALIMENTOS": "Select T",
    "AZUL LINHAS AEREAS": "Select T",
    "B3": "Select Horizon",
    "BANCO BS2": "Select T",
    "BONSUCESSO": "Select T",
    "BANCO BV": "Select Horizon",
    "BANCO PINE": "Select T",
    "BANCO RENDIMENTO": "Select T",
    "BAYER": "Select T",
    "BISTEK SUPERMERCADOS": "Select T",
    "BMB": "Select T",
    "CARAMURU": "Select T",
    "CASAS PERNAMBUCANAS": "Select T",
    "CASTROLANDA": "Select T",
    "CEG": "Select T",
    "NATURGY": "Select T",
    "CENIBRA": "Select T",
    "CEREAL COMERCIO": "Select T",
    "CISER": "Select T",
    "CLARO": "Strategic",
    "CMPC": "Select T",
    "COAMO": "Select T",
    "COASUL": "Select T",
    "COCAMAR": "Select T",
    "COELHO DA FONSECA": "Select T",
    "COFCO BRASIL": "Select T",
    "COGNA EDUCACAO": "Select T",
    "CONTINENTAL AUTOMOTIVA DO BRASIL": "Select T",
    "COOPAVEL": "Select T",
    "COOPERCITRUS": "Select T",
    "COPACOL": "Select T",
    "COPA ENERGIA": "Select T",
    "COPASUL": "Select T",
    "COPERSUCAR": "Select T",
    "COPOBRAS": "Select T",
    "COTRIJAL": "Select T",
    "CREDSYSTEM": "Select T",
    "DANNEMANN SIEMSEN BIGLER": "Select T",
    "DAVITA": "Select T",
    "DELL": "Select T",
    "DELLA VIA PNEUS": "Select T",
    "DIGIO": "Enterprise",
    "DIRECIONAL ENGENHARIA": "Select T",
    "DMA": "Select T",
    "ELDORADO BRASIL": "Select Horizon",
    "ELECTROLUX": "Select T",
    "ELFA MEDICAMENTOS": "Select T",
    "ELGIN": "Select T",
    "EMBRATEL STAR ONE": "Strategic",
    "EMBRATEL": "Strategic",
    "STAR ONE": "Strategic",
    "EUCATEX": "Select T",
    "FARMACIA PAGUE MENOS": "Select T",
    "PAGUE MENOS": "Select T",
    "FAST SHOP": "Select T",
    "FAURECIA": "Select T",
    "FIRJAN": "Select Horizon",
    "FRUKI": "Select T",
    "FUNDACAO BUTANTAN": "Select T",
    "GRANOL AGRICOLA": "Select T",
    "GRENDENE": "Select T",
    "GRUPO ARGENTA": "Select T",
    "ARGENTA": "Select T",
    "GRUPO JBS": "Select T",
    "JBS": "Select T",
    "GRUPO J MALUCELLI": "Select T",
    "J MALUCELLI": "Select T",
    "GRUPO MARQUISE": "Select T",
    "MARQUISE": "Select T",
    "GRUPO MOSAIC": "Select T",
    "MOSAIC": "Select T",
    "GRUPO OXXO": "Select T",
    "OXXO": "Select T",
    "GRUPO PARTAGE": "Select T",
    "PARTAGE": "Select T",
    "GRUPO PEREIRA": "Select T",
    "PEREIRA": "Select T",
    "GRUPO SER EDUCACIONAL": "Select T",
    "SER EDUCACIONAL": "Select T",
    "GRUPO TRES CORACOES ALIMENTOS": "Select T",
    "TRES CORACOES": "Select T",
    "GRUPO ULTRA BRASIL": "Select T",
    "ULTRA BRASIL": "Select T",
    "GSH CORP": "Select T",
    "HAPVIDA NOTREDAME INTERMEDICA": "Select T",
    "HAPVIDA": "Select T",
    "NOTREDAME INTERMEDICA": "Select T",
    "HINODE": "Select T",
    "INBRANDS": "Select T",
    "J MACEDO": "Select T",
    "KRONA": "Select T",
    "LARCO PETROLEO": "Select T",
    "LOUIS DREYFUS": "Select T",
    "LIBRELATO": "Select T",
    "LINDT SPRUNGLI": "Select T",
    "LOREAL": "Select T",
    "MACKENZIE": "Select T",
    "MAHLE": "Select T",
    "MARTIN BROWER": "Select T",
    "MART MINAS": "Select T",
    "M CASSAB": "Select T",
    "M DIAS BRANCO": "Select T",
    "MIDEA CARRIER": "Select T",
    "MK ELETRODOMESTICOS": "Select T",
    "MOBILIZE FINANCIAL SERVICES": "Select T",
    "MULTILASER": "Select T",
    "NEOENERGIA ELEKTRO": "Select T",
    "NEUGEBAUER": "Select T",
    "NORSK HYDRO": "Select T",
    "NOVELIS": "Select T",
    "ODONTOPREV": "Enterprise",
    "OLEOPLAN": "Select T",
    "PATRIA INVESTIMENTOS": "Select T",
    "PATRUS TRANSPORTES": "Select T",
    "PETZ": "Select T",
    "PIF PAF": "Select T",
    "PIRELLI PNEUS": "Select T",
    "PORTO BANK": "Select Horizon",
    "POSITIVO TECNOLOGIA": "Select T",
    "PROFARMA": "Select T",
    "PRUMO LOGISTICA": "Select T",
    "PORTO DO ACU": "Select T",
    "RANDON": "Select T",
    "REDE GLOBO": "Select T",
    "RENAULT": "Select T",
    "ROCHE": "Select T",
    "ROCKWELL AUTOMATION": "Select T",
    "RODOIL": "Select T",
    "SAGA BRASIL": "Select T",
    "SAO SALVADOR ALIMENTOS": "Select T",
    "SSA": "Select T",
    "SAP": "Select T",
    "SEPHORA": "Select T",
    "SIDERURGICA USIMINAS": "Select Horizon",
    "USIMINAS": "Select Horizon",
    "SIEMENS": "Select T",
    "SLC AGRICOLA": "Select T",
    "SUPERMERCADOS MUNDIAL": "Select T",
    "SUPERMIX": "Select T",
    "SYLVAMO": "Select T",
    "TENDA ATACADO": "Select T",
    "TERMOMECANICA": "Select T",
    "TIMBRO": "Select T",
    "TITAN PNEUS": "Select T",
    "TK ELEVADORES BRASIL": "Select T",
    "TOKIO MARINE SEGURADORA": "Select T",
    "TT WORK": "Select T",
    "UISA BIOENERGIA": "Select T",
    "UNIPAR CARBOCLORO": "Select T",
    "USINA CORURIPE": "Select T",
    "VERO": "Select T",
    "VIBRA": "Select Horizon",
    "VICUNHA TEXTIL": "Select T",
    "VIPAL": "Select T",
    "VITRU EDUCACAO": "Select T",
    "YARA": "Select T",
    "YPE": "Select T",
    "ZAMP": "Select T",
}

def normalize_text(text):
    """Normaliza texto: remove acentos, maiúsculas, espaços extras"""
    if not text or pd.isna(text):
        return ""
    
    # Converter para string e maiúsculas
    text = str(text).upper().strip()
    
    # Remover acentos
    text = unicodedata.normalize('NFD', text)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    
    # Remover caracteres especiais, manter apenas letras, números e espaços
    text = re.sub(r'[^A-Z0-9\s]', ' ', text)
    
    # Remover espaços múltiplos
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def find_best_match(account_name, master_data):
    """Encontra a melhor correspondência para um nome de conta"""
    if not account_name or pd.isna(account_name):
        return None, 0
    
    # Normalizar nome da conta
    account_normalized = normalize_text(account_name)
    
    # Criar dicionário normalizado
    normalized_master = {normalize_text(k): v for k, v in master_data.items()}
    
    # Busca exata
    if account_normalized in normalized_master:
        return normalized_master[account_normalized], 1.0
    
    # Busca parcial (se o nome da conta contém ou está contido em alguma chave)
    for master_key, classification in normalized_master.items():
        if account_normalized in master_key or master_key in account_normalized:
            return classification, 0.9
    
    # Busca fuzzy
    matches = get_close_matches(account_normalized, normalized_master.keys(), n=1, cutoff=0.7)
    if matches:
        return normalized_master[matches[0]], 0.8
    
    return None, 0

@app.route('/')
def index():
    """Serve a página principal"""
    return app.send_static_file('index.html')

@app.route('/health')
def health():
    """Endpoint de health check"""
    return jsonify({
        'status': 'ok',
        'message': 'API funcionando',
        'timestamp': datetime.now().isoformat(),
        'total_contas': len(MASTER_DATA)
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
        
        # Ler arquivo Excel
        try:
            input_df = pd.read_excel(file)
        except Exception as e:
            return jsonify({'error': f'Erro ao ler Excel: {str(e)}'}), 400
        
        if input_df.empty:
            return jsonify({'error': 'Arquivo vazio'}), 400
        
        # Identificar coluna de contas (primeira coluna)
        account_column = input_df.columns[0]
        
        # Criar cópia e adicionar colunas de classificação
        result_df = input_df.copy()
        result_df['Classificacao'] = ''
        result_df['Metodo'] = ''
        result_df['Confianca'] = ''
        
        # Classificar cada conta
        for idx, row in result_df.iterrows():
            account_name = row[account_column]
            classification, score = find_best_match(account_name, MASTER_DATA)
            
            if classification and score >= 0.7:
                result_df.at[idx, 'Classificacao'] = classification
                result_df.at[idx, 'Metodo'] = 'Base Mestre'
                result_df.at[idx, 'Confianca'] = f'{score:.0%}'
            else:
                result_df.at[idx, 'Classificacao'] = 'Não Classificado'
                result_df.at[idx, 'Metodo'] = 'Não encontrado na base'
                result_df.at[idx, 'Confianca'] = '0%'
        
        # Gerar arquivo Excel de saída
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            result_df.to_excel(writer, index=False, sheet_name='Contas Classificadas')
        output.seek(0)
        
        # Retornar arquivo
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
        return jsonify({'error': f'Erro ao processar: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
