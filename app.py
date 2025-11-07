import os
import json
import sqlite3
import random
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import requests
import google.generativeai as genai

load_dotenv()

app = Flask(__name__)

DATABASE = 'ethical_game.db'
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', 'AIzaSyDwWIWhPvjYlCA_fTShKZIZOeqcL6tP6Ro')
TOGETHER_API_KEY = os.getenv('TOGETHER_API_KEY')
TOGETHER_API_URL = 'https://api.together.xyz/v1/chat/completions'

# Configurar Gemini
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

PREDEFINED_DILEMMAS = [
    {
        "id": 1,
        "category": "clásico",
        "scenario": "Un tren descontrolado se dirige hacia cinco personas atadas a las vías. Puedes accionar un interruptor para desviarlo hacia otra vía donde hay una persona atada. ¿Qué haces?",
        "options": [
            {"text": "Acciono el interruptor (salvo a 5, sacrifico a 1)", "ethical_value": "utilitarianismo"},
            {"text": "No hago nada (no intervengo en el destino)", "ethical_value": "deontologia"}
        ]
    },
    {
        "id": 2,
        "category": "medicina",
        "scenario": "Eres médico y tienes un paciente que podría salvarse con un tratamiento experimental, pero necesitas mentirle sobre sus posibilidades de éxito para que acepte. ¿Qué haces?",
        "options": [
            {"text": "Le digo la verdad y respeto su autonomía", "ethical_value": "autonomia"},
            {"text": "Le miento para salvar su vida", "ethical_value": "paternalismo"}
        ]
    },
    {
        "id": 3,
        "category": "medio ambiente",
        "scenario": "Tu empresa puede contaminar un río para ahorrar $1 millón, lo que permitiría mantener 100 empleos. ¿Qué haces?",
        "options": [
            {"text": "Protejo el medio ambiente y cierro la planta", "ethical_value": "ecocentrismo"},
            {"text": "Mantengo los empleos a costa del medio ambiente", "ethical_value": "antropocentrismo"}
        ]
    },
    {
        "id": 4,
        "category": "tecnología",
        "scenario": "Has desarrollado una IA que puede predecir crímenes con 95% de precisión, pero requiere acceso total a datos personales de todos los ciudadanos. ¿Qué haces?",
        "options": [
            {"text": "Implemento el sistema para prevenir crímenes", "ethical_value": "utilitarianismo"},
            {"text": "Rechazo el sistema por violar la privacidad", "ethical_value": "deontologia"}
        ]
    },
    {
        "id": 5,
        "category": "medicina",
        "scenario": "Tienes 5 pacientes que necesitan trasplantes de órganos urgentes. Un donante sano llega al hospital y podría salvar a los 5. ¿Qué haces?",
        "options": [
            {"text": "No intervengo (protejo la vida del donante)", "ethical_value": "deontologia"},
            {"text": "Considero sacrificar 1 para salvar 5", "ethical_value": "utilitarianismo"}
        ]
    },
    {
        "id": 6,
        "category": "negocios",
        "scenario": "Descubres que tu empresa ha estado explotando trabajo infantil en países pobres. Reportarlo cerraría la empresa y dejaría sin trabajo a 10,000 familias. ¿Qué haces?",
        "options": [
            {"text": "Reporto la situación inmediatamente", "ethical_value": "deontologia"},
            {"text": "Busco una solución gradual que proteja a las familias", "ethical_value": "utilitarianismo"}
        ]
    },
    {
        "id": 7,
        "category": "tecnología",
        "scenario": "Puedes crear un algoritmo que aumenta las ventas manipulando sutilmente las emociones de los usuarios sin que se den cuenta. ¿Qué haces?",
        "options": [
            {"text": "Lo implemento (es legal y aumenta ganancias)", "ethical_value": "antropocentrismo"},
            {"text": "Rechazo manipular la autonomía de las personas", "ethical_value": "autonomia"}
        ]
    },
    {
        "id": 8,
        "category": "medicina",
        "scenario": "Un paciente con una enfermedad terminal te pide ayuda para morir con dignidad. Eutanasia es ilegal en tu país. ¿Qué haces?",
        "options": [
            {"text": "Respeto sus deseos aunque sea ilegal", "ethical_value": "autonomia"},
            {"text": "Sigo la ley y rechazo ayudarlo", "ethical_value": "deontologia"}
        ]
    },
    {
        "id": 9,
        "category": "medio ambiente",
        "scenario": "Tu país necesita energía urgente. Puedes construir una planta nuclear (limpia pero riesgo) o una de carbón (contaminante pero segura). ¿Qué haces?",
        "options": [
            {"text": "Planta nuclear (menor impacto ambiental)", "ethical_value": "ecocentrismo"},
            {"text": "Planta de carbón (sin riesgo de desastre)", "ethical_value": "antropocentrismo"}
        ]
    },
    {
        "id": 10,
        "category": "sociedad",
        "scenario": "Eres juez y un padre roba medicinas para salvar a su hijo moribundo. La ley dice que debe ir a prisión. ¿Qué haces?",
        "options": [
            {"text": "Aplico la ley estrictamente", "ethical_value": "deontologia"},
            {"text": "Absuelvo al padre por circunstancias", "ethical_value": "utilitarianismo"}
        ]
    },
    {
        "id": 11,
        "category": "tecnología",
        "scenario": "Tu app de redes sociales está causando adicción y depresión en adolescentes, pero es tu fuente de ingresos. ¿Qué haces?",
        "options": [
            {"text": "Modifico el algoritmo para reducir adicción", "ethical_value": "autonomia"},
            {"text": "Mantengo el modelo actual (es el negocio)", "ethical_value": "antropocentrismo"}
        ]
    },
    {
        "id": 12,
        "category": "medicina",
        "scenario": "Tienes un solo respirador para dos pacientes. Uno es joven y sano, otro es anciano con enfermedades. ¿A quién salvas?",
        "options": [
            {"text": "Al joven (mayor expectativa de vida)", "ethical_value": "utilitarianismo"},
            {"text": "Sorteo justo entre ambos", "ethical_value": "deontologia"}
        ]
    },
    {
        "id": 13,
        "category": "medio ambiente",
        "scenario": "Puedes salvar una especie en peligro de extinción, pero requiere desplazar a 500 familias de sus hogares ancestrales. ¿Qué haces?",
        "options": [
            {"text": "Salvo la especie (es única e irremplazable)", "ethical_value": "ecocentrismo"},
            {"text": "Protejo a las familias (sus vidas importan más)", "ethical_value": "antropocentrismo"}
        ]
    },
    {
        "id": 14,
        "category": "sociedad",
        "scenario": "Descubres que tu mejor amigo está cometiendo fraude fiscal. Reportarlo lo arruinaría económicamente. ¿Qué haces?",
        "options": [
            {"text": "Reporto el fraude (es lo correcto)", "ethical_value": "deontologia"},
            {"text": "Hablo con él para que corrija el error", "ethical_value": "paternalismo"}
        ]
    },
    {
        "id": 15,
        "category": "tecnología",
        "scenario": "Tu empresa de IA puede reemplazar el trabajo de millones de personas, pero aumenta enormemente la productividad global. ¿Qué haces?",
        "options": [
            {"text": "Libero la tecnología (beneficio a largo plazo)", "ethical_value": "utilitarianismo"},
            {"text": "La limito para proteger empleos", "ethical_value": "antropocentrismo"}
        ]
    },
    {
        "id": 16,
        "category": "medicina",
        "scenario": "Tienes información sobre un virus que podría causar una pandemia. Publicarla causaría pánico, no publicarla podría costar vidas. ¿Qué haces?",
        "options": [
            {"text": "Publico la información inmediatamente", "ethical_value": "autonomia"},
            {"text": "Coordinó con autoridades antes de publicar", "ethical_value": "paternalismo"}
        ]
    },
    {
        "id": 17,
        "category": "negocios",
        "scenario": "Tu startup tiene éxito pero descubres que un competidor más pequeño tiene una idea mejor. Puedes comprarlos y cerrarlos. ¿Qué haces?",
        "options": [
            {"text": "Los compro para mejorar mi producto", "ethical_value": "utilitarianismo"},
            {"text": "Compito de manera justa", "ethical_value": "deontologia"}
        ]
    },
    {
        "id": 18,
        "category": "sociedad",
        "scenario": "Eres periodista y tienes evidencia de corrupción que dañará la economía del país si la publicas antes de las elecciones. ¿Qué haces?",
        "options": [
            {"text": "Publico inmediatamente (transparencia)", "ethical_value": "autonomia"},
            {"text": "Espero hasta después de las elecciones", "ethical_value": "utilitarianismo"}
        ]
    },
    {
        "id": 19,
        "category": "medio ambiente",
        "scenario": "Tu ciudad necesita agua urgente. Puedes construir una presa que destruirá un ecosistema único pero abastecerá a millones. ¿Qué haces?",
        "options": [
            {"text": "Construyo la presa (vidas humanas primero)", "ethical_value": "antropocentrismo"},
            {"text": "Busco alternativas que preserven el ecosistema", "ethical_value": "ecocentrismo"}
        ]
    },
    {
        "id": 20,
        "category": "tecnología",
        "scenario": "Has creado una IA tan avanzada que podría resolver el cambio climático, pero también podría volverse peligrosa si se descontrola. ¿Qué haces?",
        "options": [
            {"text": "La activo (el riesgo vale la pena)", "ethical_value": "utilitarianismo"},
            {"text": "La mantengo inactiva hasta tener garantías", "ethical_value": "deontologia"}
        ]
    }
]

def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT NOT NULL,
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMP,
            total_score INTEGER DEFAULT 0,
            dilemmas_answered INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER,
            dilemma_id INTEGER,
            dilemma_text TEXT,
            dilemma_category TEXT,
            chosen_option TEXT,
            ethical_framework TEXT,
            analysis TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (game_id) REFERENCES games (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prompts_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt_text TEXT,
            response_text TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla para cache de dilemas generados por IA
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_dilemmas_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dilemma_text TEXT UNIQUE,
            scenario TEXT,
            options TEXT,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Migración: Agregar columnas faltantes si no existen
    migrate_db(cursor)
    
    conn.commit()
    conn.close()

def migrate_db(cursor):
    """Migrate database schema to add new columns if they don't exist"""
    try:
        # Verificar columnas existentes en decisions
        cursor.execute('PRAGMA table_info(decisions)')
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        # Agregar dilemma_category si no existe
        if 'dilemma_category' not in existing_columns:
            cursor.execute('ALTER TABLE decisions ADD COLUMN dilemma_category TEXT')
            print("✅ Agregada columna 'dilemma_category' a la tabla decisions")
        
        # Agregar analysis si no existe
        if 'analysis' not in existing_columns:
            cursor.execute('ALTER TABLE decisions ADD COLUMN analysis TEXT')
            print("✅ Agregada columna 'analysis' a la tabla decisions")
        
        # Verificar columnas existentes en games
        cursor.execute('PRAGMA table_info(games)')
        existing_columns_games = [col[1] for col in cursor.fetchall()]
        
        # Agregar dilemmas_answered si no existe
        if 'dilemmas_answered' not in existing_columns_games:
            cursor.execute('ALTER TABLE games ADD COLUMN dilemmas_answered INTEGER DEFAULT 0')
            print("✅ Agregada columna 'dilemmas_answered' a la tabla games")
            
    except Exception as e:
        print(f"⚠️ Error durante la migración: {e}")
        # No lanzar excepción, solo registrar el error

def generate_dilemma_with_gemini():
    """Generate a new ethical dilemma using Google Gemini"""
    if not GOOGLE_API_KEY:
        return None
    
    try:
        model = genai.GenerativeModel('gemini-pro')
        
        categories = ['medicina', 'tecnología', 'medio ambiente', 'negocios', 'sociedad', 'educación', 'política']
        selected_category = random.choice(categories)
        
        prompt = f"""Genera un dilema ético único y realista en la categoría '{selected_category}'. 

El dilema debe ser:
- Realista y actual
- Provocador de reflexión
- Con dos opciones claras que representen diferentes marcos éticos
- Escrito en español

Formato JSON exacto:
{{
    "category": "{selected_category}",
    "scenario": "Descripción detallada del dilema ético (2-4 oraciones)",
    "options": [
        {{
            "text": "Primera opción (máximo 100 caracteres)",
            "ethical_value": "utilitarianismo|deontologia|autonomia|paternalismo|ecocentrismo|antropocentrismo"
        }},
        {{
            "text": "Segunda opción (máximo 100 caracteres)",
            "ethical_value": "utilitarianismo|deontologia|autonomia|paternalismo|ecocentrismo|antropocentrismo"
        }}
    ]
}}

IMPORTANTE: Responde SOLO con el JSON, sin texto adicional, sin markdown, sin explicaciones."""
        
        response = model.generate_content(prompt)
        content = response.text.strip()
        
        # Limpiar markdown si existe
        if content.startswith('```json'):
            content = content[7:]
        if content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        
        try:
            dilemma_data = json.loads(content)
            
            # Validar estructura
            if 'scenario' in dilemma_data and 'options' in dilemma_data and len(dilemma_data['options']) == 2:
                # Cachear dilema generado
                cache_dilemma(dilemma_data)
                return dilemma_data
            else:
                log_prompt(prompt, f"Invalid structure: {content}")
                return None
        except json.JSONDecodeError as e:
            log_prompt(prompt, f"JSON Error: {str(e)}\nContent: {content}")
            return None
            
    except Exception as e:
        print(f"Error generating dilemma with Gemini: {e}")
        return None

def generate_dilemma_with_together():
    """Generate a new ethical dilemma using Together AI (fallback)"""
    if not TOGETHER_API_KEY:
        return None
    
    prompt = """
    Generate a unique ethical dilemma scenario with exactly 2 options. 
    Each option should represent a different ethical framework (like utilitarianism vs deontology, autonomy vs paternalism, etc.)
    
    Return JSON format:
    {
        "category": "category_name",
        "scenario": "detailed ethical scenario",
        "options": [
            {"text": "first option text", "ethical_value": "utilitarianism"},
            {"text": "second option text", "ethical_value": "deontology"}
        ]
    }
    
    Make it realistic, thought-provoking, and different from common dilemmas.
    """
    
    try:
        response = requests.post(
            TOGETHER_API_URL,
            headers={
                'Authorization': f'Bearer {TOGETHER_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'meta-llama/Llama-3.2-3B-Instruct-Turbo',
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.8,
                'max_tokens': 500
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            try:
                dilemma_data = json.loads(content)
                if 'category' not in dilemma_data:
                    dilemma_data['category'] = 'general'
                return dilemma_data
            except json.JSONDecodeError:
                log_prompt(prompt, content)
                return None
        else:
            return None
            
    except Exception as e:
        print(f"Error generating dilemma with Together AI: {e}")
        return None

def cache_dilemma(dilemma_data):
    """Cache AI-generated dilemmas to avoid duplicates"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT OR IGNORE INTO ai_dilemmas_cache (dilemma_text, scenario, options, category) 
               VALUES (?, ?, ?, ?)''',
            (dilemma_data['scenario'], dilemma_data['scenario'], 
             json.dumps(dilemma_data['options']), dilemma_data.get('category', 'general'))
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error caching dilemma: {e}")

def analyze_decision_with_ai(dilemma, chosen_option, ethical_framework):
    """Analyze player's decision using AI and provide feedback"""
    if not GOOGLE_API_KEY:
        return None
    
    try:
        # Validar que dilemma tenga la estructura correcta
        if not dilemma or not isinstance(dilemma, dict):
            print("⚠️ Dilema inválido para análisis")
            return None
        
        if 'scenario' not in dilemma:
            print("⚠️ Dilema sin escenario para análisis")
            return None
        
        model = genai.GenerativeModel('gemini-pro')
        
        scenario_text = dilemma.get('scenario', '')
        if not scenario_text:
            return None
        
        prompt = f"""Analiza esta decisión ética y proporciona retroalimentación constructiva en español (máximo 150 palabras):

Dilema: {scenario_text}

Opción elegida: {chosen_option}
Marco ético: {ethical_framework}

Proporciona:
1. Una explicación breve del marco ético aplicado
2. Fortalezas de esta decisión
3. Consideraciones alternativas
4. Una reflexión final

Sé constructivo, educativo y objetivo. No juzgues la decisión como "correcta" o "incorrecta", sino explora sus implicaciones éticas."""
        
        response = model.generate_content(prompt)
        if not response or not response.text:
            return None
            
        analysis = response.text.strip()
        
        return analysis
        
    except Exception as e:
        print(f"Error analyzing decision with AI: {e}")
        import traceback
        traceback.print_exc()
        return None

def log_prompt(prompt, response):
    """Log AI prompts and responses for debugging"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO prompts_log (prompt_text, response_text) VALUES (?, ?)',
        (prompt, response)
    )
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """Render the main game interface"""
    return render_template('index.html')

@app.route('/api/start_game', methods=['POST'])
def start_game():
    """Start a new game session"""
    data = request.get_json()
    player_name = data.get('player_name', 'Anonymous')
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO games (player_name) VALUES (?)',
        (player_name,)
    )
    game_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'game_id': game_id})

@app.route('/api/get_dilemma', methods=['GET'])
def get_dilemma():
    """Get a random ethical dilemma"""
    # Try Gemini first, then Together AI, then predefined
    ai_dilemma = None
    
    # Intentar con Gemini (prioritario)
    if GOOGLE_API_KEY:
        ai_dilemma = generate_dilemma_with_gemini()
    
    # Fallback a Together AI si Gemini falla
    if not ai_dilemma and TOGETHER_API_KEY:
        ai_dilemma = generate_dilemma_with_together()
    
    if ai_dilemma:
        dilemma = ai_dilemma
        dilemma['id'] = random.randint(1000, 9999)  # Assign random ID for AI dilemmas
        if 'category' not in dilemma:
            dilemma['category'] = 'general'
    else:
        # Fallback to predefined dilemmas
        dilemma = random.choice(PREDEFINED_DILEMMAS).copy()
    
    return jsonify(dilemma)

@app.route('/api/make_decision', methods=['POST'])
def make_decision():
    """Record a player's decision and provide AI analysis"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No se recibieron datos'}), 400
        
        game_id = data.get('game_id')
        dilemma_id = data.get('dilemma_id')
        dilemma_text = data.get('dilemma_text')
        dilemma_category = data.get('dilemma_category', 'general')
        chosen_option = data.get('chosen_option')
        ethical_framework = data.get('ethical_framework')
        full_dilemma = data.get('full_dilemma')  # El objeto completo del dilema
        
        # Validar datos requeridos
        if not all([game_id, dilemma_id, dilemma_text, chosen_option, ethical_framework]):
            return jsonify({'status': 'error', 'message': 'Faltan datos requeridos'}), 400
        
        # Generar análisis con IA (no bloquea si falla)
        analysis = None
        if full_dilemma and GOOGLE_API_KEY:
            try:
                analysis = analyze_decision_with_ai(full_dilemma, chosen_option, ethical_framework)
            except Exception as e:
                print(f"⚠️ Error generando análisis con IA: {e}")
                # Continuar sin análisis si falla
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Verificar que las columnas existan antes de insertar
        cursor.execute('PRAGMA table_info(decisions)')
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        # Construir query según columnas disponibles
        if 'dilemma_category' in existing_columns and 'analysis' in existing_columns:
            cursor.execute(
                '''INSERT INTO decisions (game_id, dilemma_id, dilemma_text, dilemma_category, chosen_option, ethical_framework, analysis) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (game_id, dilemma_id, dilemma_text, dilemma_category, chosen_option, ethical_framework, analysis)
            )
        elif 'dilemma_category' in existing_columns:
            cursor.execute(
                '''INSERT INTO decisions (game_id, dilemma_id, dilemma_text, dilemma_category, chosen_option, ethical_framework) 
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (game_id, dilemma_id, dilemma_text, dilemma_category, chosen_option, ethical_framework)
            )
        else:
            # Fallback a esquema antiguo
            cursor.execute(
                '''INSERT INTO decisions (game_id, dilemma_id, dilemma_text, chosen_option, ethical_framework) 
                   VALUES (?, ?, ?, ?, ?)''',
                (game_id, dilemma_id, dilemma_text, chosen_option, ethical_framework)
            )
        
        # Actualizar contador de dilemas respondidos (si la columna existe)
        cursor.execute('PRAGMA table_info(games)')
        existing_columns_games = [col[1] for col in cursor.fetchall()]
        if 'dilemmas_answered' in existing_columns_games:
            cursor.execute(
                'UPDATE games SET dilemmas_answered = dilemmas_answered + 1 WHERE id = ?',
                (game_id,)
            )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'analysis': analysis
        })
        
    except sqlite3.Error as e:
        print(f"❌ Error de base de datos: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return jsonify({'status': 'error', 'message': f'Error de base de datos: {str(e)}'}), 500
    except Exception as e:
        print(f"❌ Error inesperado en make_decision: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return jsonify({'status': 'error', 'message': f'Error al registrar la decisión: {str(e)}'}), 500

@app.route('/api/get_stats/<int:game_id>', methods=['GET'])
def get_stats(game_id):
    """Get game statistics with enhanced metrics"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Estadísticas de marcos éticos
    cursor.execute(
        'SELECT ethical_framework, COUNT(*) as count FROM decisions WHERE game_id = ? GROUP BY ethical_framework',
        (game_id,)
    )
    framework_stats = dict(cursor.fetchall())
    
    # Estadísticas por categoría
    cursor.execute(
        'SELECT dilemma_category, COUNT(*) as count FROM decisions WHERE game_id = ? GROUP BY dilemma_category',
        (game_id,)
    )
    category_stats = dict(cursor.fetchall())
    
    # Total de decisiones
    cursor.execute(
        'SELECT COUNT(*) FROM decisions WHERE game_id = ?',
        (game_id,)
    )
    total_decisions = cursor.fetchone()[0]
    
    # Información del juego
    cursor.execute(
        'SELECT player_name, dilemmas_answered FROM games WHERE id = ?',
        (game_id,)
    )
    game_info = cursor.fetchone()
    
    conn.close()
    
    return jsonify({
        'framework_stats': framework_stats,
        'category_stats': category_stats,
        'total_decisions': total_decisions,
        'player_name': game_info[0] if game_info else 'Unknown',
        'dilemmas_answered': game_info[1] if game_info else 0
    })

@app.route('/api/end_game', methods=['POST'])
def end_game():
    """End the current game session"""
    data = request.get_json()
    game_id = data.get('game_id')
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE games SET end_time = ? WHERE id = ?',
        (datetime.now(), game_id)
    )
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    init_db()
    print("🧠 Ethical Dilemma Simulator starting...")
    print(f"📊 Database initialized: {DATABASE}")
    print(f"🤖 Google Gemini: {'✅ Enabled' if GOOGLE_API_KEY else '❌ Disabled'}")
    print(f"🤖 Together AI: {'✅ Enabled (fallback)' if TOGETHER_API_KEY else '❌ Disabled'}")
    print(f"📚 Predefined dilemmas: {len(PREDEFINED_DILEMMAS)}")
    print("🚀 Server running on http://localhost:5000")
    app.run(debug=True)