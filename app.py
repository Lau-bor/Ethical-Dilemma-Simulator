import os
import json
import sqlite3
import random
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

app = Flask(__name__)

# Detect Vercel environment
IS_VERCEL = os.getenv('VERCEL') == '1'

# Use /tmp for Vercel (writable in serverless) or local for development
if IS_VERCEL:
    DATABASE = '/tmp/ethical_game.db'
else:
    DATABASE = 'ethical_game.db'

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')

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

def get_db_connection():
    """Get a database connection with proper settings for Vercel"""
    try:
        # Ensure /tmp exists in Vercel (it should, but just in case)
        if IS_VERCEL:
            # /tmp already exists in Vercel serverless, no need to create
            pass
        else:
            # Ensure directory exists locally
            db_dir = os.path.dirname(DATABASE) if os.path.dirname(DATABASE) else '.'
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
    except Exception as e:
        print(f"Warning: Error creando directorio BD: {e}")
    
    # Connect with timeout and allow different threads (for serverless)
    # This is necessary for Vercel's serverless functions
    return sqlite3.connect(DATABASE, timeout=10.0, check_same_thread=False)

def init_db():
    """Initialize the database with required tables"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
    except Exception as e:
        print(f"ERROR: No se pudo conectar a la base de datos: {e}")
        raise
    
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
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla para logros disponibles
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            icon TEXT NOT NULL,
            achievement_type TEXT NOT NULL,
            condition_value TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla para logros desbloqueados por jugadores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT NOT NULL,
            achievement_id INTEGER NOT NULL,
            unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (achievement_id) REFERENCES achievements (id),
            UNIQUE(player_name, achievement_id)
        )
    ''')
    
    # Migración: Agregar columnas faltantes si no existen
    migrate_db(cursor)
    
    # Inicializar logros predefinidos
    init_achievements(cursor)
    
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
        
        # Verificar columnas existentes en ai_dilemmas_cache
        cursor.execute('PRAGMA table_info(ai_dilemmas_cache)')
        existing_columns_cache = [col[1] for col in cursor.fetchall()]
        
        # Agregar image_url si no existe
        if 'image_url' not in existing_columns_cache:
            cursor.execute('ALTER TABLE ai_dilemmas_cache ADD COLUMN image_url TEXT')
            print("✅ Agregada columna 'image_url' a la tabla ai_dilemmas_cache")
            
    except Exception as e:
        print(f"⚠️ Error durante la migración: {e}")
        # No lanzar excepción, solo registrar el error

# ==================== SISTEMA DE IMÁGENES ====================
# URLs públicas de imágenes de Unsplash organizadas por categoría
# Estas son URLs directas que no requieren API key

# Mapeo de palabras clave a imágenes específicas para selección inteligente
KEYWORD_IMAGE_MAP = {
    # Medicina - Dilemas específicos
    'medicina': {
        'hospital': 'https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=800',
        'medicamento': 'https://images.unsplash.com/photo-1587854692152-cbe660dbde88?w=800',
        'paciente': 'https://images.unsplash.com/photo-1576091160399-112ba8d25d1f?w=800',
        'doctor': 'https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=800',
        'tratamiento': 'https://images.unsplash.com/photo-1559757175-0eb30cd8c063?w=800',
        'urgencia': 'https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=800',
        'recursos': 'https://images.unsplash.com/photo-1551601651-2a8555f1a136?w=800',
        'salud': 'https://images.unsplash.com/photo-1579154204601-01588f351e67?w=800',
    },
    'tecnología': {
        'ia': 'https://images.unsplash.com/photo-1677442136019-21780ecad995?w=800',
        'algoritmo': 'https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=800',
        'datos': 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800',
        'privacidad': 'https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=800',
        'redes': 'https://images.unsplash.com/photo-1518770660439-4636190af475?w=800',
        'aplicación': 'https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=800',
    },
    'medio ambiente': {
        'naturaleza': 'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=800',
        'contaminación': 'https://images.unsplash.com/photo-1581094794329-c8112a89af12?w=800',
        'árboles': 'https://images.unsplash.com/photo-1511497584788-876760111969?w=800',
        'animales': 'https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=800',
        'energía': 'https://images.unsplash.com/photo-1466611653911-95081537e5b7?w=800',
        'ecosistema': 'https://images.unsplash.com/photo-1472214103451-9374bd1c798e?w=800',
    },
    'negocios': {
        'empresa': 'https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=800',
        'trabajo': 'https://images.unsplash.com/photo-1521737604893-d14cc237f11d?w=800',
        'dinero': 'https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?w=800',
        'oficina': 'https://images.unsplash.com/photo-1497366216548-37526070297c?w=800',
    },
    'sociedad': {
        'gente': 'https://images.unsplash.com/photo-1521737852567-6949f3f9f2b5?w=800',
        'comunidad': 'https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=800',
        'familia': 'https://images.unsplash.com/photo-1511632765486-a01980e01a18?w=800',
        'justicia': 'https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=800',
    },
    'clásico': {
        'tren': 'https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=800',
        'vías': 'https://images.unsplash.com/photo-1517817748493-49b5541a82ad?w=800',
        'decisión': 'https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=800',
        'elección': 'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=800',
    },
}

IMAGE_BANK = {
    'medicina': [
        'https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=800',  # Hospital
        'https://images.unsplash.com/photo-1587854692152-cbe660dbde88?w=800',  # Medicamentos
        'https://images.unsplash.com/photo-1576091160399-112ba8d25d1f?w=800',  # Paciente
        'https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=800',  # Doctor
        'https://images.unsplash.com/photo-1559757175-0eb30cd8c063?w=800',  # Tratamiento
        'https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=800',  # Urgencia
        'https://images.unsplash.com/photo-1551601651-2a8555f1a136?w=800',  # Recursos médicos
        'https://images.unsplash.com/photo-1579154204601-01588f351e67?w=800',  # Salud
    ],
    'tecnología': [
        'https://images.unsplash.com/photo-1677442136019-21780ecad995?w=800',  # IA/Cerebro
        'https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=800',  # Algoritmos
        'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800',  # Datos
        'https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=800',  # Privacidad
        'https://images.unsplash.com/photo-1518770660439-4636190af475?w=800',  # Redes
        'https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=800',  # App desarrollo
    ],
    'medio ambiente': [
        'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=800',  # Naturaleza
        'https://images.unsplash.com/photo-1581094794329-c8112a89af12?w=800',  # Contaminación
        'https://images.unsplash.com/photo-1511497584788-876760111969?w=800',  # Árboles
        'https://images.unsplash.com/photo-1472214103451-9374bd1c798e?w=800',  # Ecosistema
        'https://images.unsplash.com/photo-1466611653911-95081537e5b7?w=800',  # Energía
        'https://images.unsplash.com/photo-1518531933037-91b2f5f229cc?w=800',  # Planeta
    ],
    'negocios': [
        'https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=800',  # Empresa
        'https://images.unsplash.com/photo-1521737604893-d14cc237f11d?w=800',  # Trabajo
        'https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?w=800',  # Dinero
        'https://images.unsplash.com/photo-1497366216548-37526070297c?w=800',  # Oficina
        'https://images.unsplash.com/photo-1552664730-d307ca884978?w=800',  # Reunión
    ],
    'sociedad': [
        'https://images.unsplash.com/photo-1521737852567-6949f3f9f2b5?w=800',  # Gente
        'https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=800',  # Comunidad
        'https://images.unsplash.com/photo-1511632765486-a01980e01a18?w=800',  # Familia
        'https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=800',  # Justicia
        'https://images.unsplash.com/photo-1488521787991-ed7bbaae773c?w=800',  # Sociedad
    ],
    'clásico': [
        'https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=800',  # Tren
        'https://images.unsplash.com/photo-1517817748493-49b5541a82ad?w=800',  # Vías
        'https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=800',  # Decisión
        'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=800',  # Elección
    ],
    'educación': [
        'https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=800',  # Educación
        'https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=800',  # Aprendizaje
        'https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=800',  # Estudio
        'https://images.unsplash.com/photo-1509062522246-3755977927d7?w=800',  # Escuela
    ],
    'política': [
        'https://images.unsplash.com/photo-1582213782179-e0d53f98f2ca?w=800',  # Política
        'https://images.unsplash.com/photo-1543269865-cbf427effbad?w=800',  # Gobierno
        'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800',  # Elecciones
        'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800',  # Democracia
    ],
    'general': [
        'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800',  # General
        'https://images.unsplash.com/photo-1488590528505-98d2b5aba04b?w=800',  # Tecnología
        'https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=800',  # Mundo
        'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=800',  # Pensamiento
    ]
}

# Imágenes para marcos éticos - Representativas conceptualmente de cada filosofía
ETHICAL_FRAMEWORK_IMAGES = {
    # Utilitarismo: Maximizar bienestar/beneficios para la mayoría (balance, números, beneficios, gráficos)
    'utilitarianismo': 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=600',  # Gráficos/estadísticas (maximizar resultados)
    
    # Deontología: Deberes y principios morales absolutos (justicia, ley, principios)
    'deontologia': 'https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=600',  # Justicia/balanza de la justicia
    
    # Autonomía: Respeto por la libertad y decisiones individuales (libertad, elección, independencia)
    'autonomia': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600',  # Persona independiente/pensando
    
    # Paternalismo: Proteger a otros incluso contra su voluntad (cuidado, protección, ayuda)
    'paternalismo': 'https://images.unsplash.com/photo-1511632765486-a01980e01a18?w=600',  # Protección/cuidado familiar
    
    # Ecocentrismo: Valor intrínseco del medio ambiente (naturaleza, ecosistema, vida silvestre)
    'ecocentrismo': 'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=600',  # Naturaleza/medio ambiente
    
    # Antropocentrismo: Los humanos son el centro de valor (personas, sociedad, humanidad)
    'antropocentrismo': 'https://images.unsplash.com/photo-1521737852567-6949f3f9f2b5?w=600'  # Personas/comunidad humana
}

def get_dilemma_image(scenario, category='general'):
    """Obtiene una imagen para el dilema basada en categoría y palabras clave del escenario"""
    try:
        # Normalizar categoría y escenario
        category = category.lower() if category else 'general'
        scenario_lower = scenario.lower() if scenario else ''
        
        # Intentar encontrar imagen por palabras clave específicas
        if category in KEYWORD_IMAGE_MAP:
            keyword_map = KEYWORD_IMAGE_MAP[category]
            
            # Buscar palabras clave en el escenario
            for keyword, image_url in keyword_map.items():
                # Buscar variaciones de la palabra clave
                keyword_variations = [
                    keyword,
                    keyword + 's',  # plural
                    keyword + 'es',  # plural español
                ]
                
                # También buscar en español común
                if keyword == 'hospital':
                    keyword_variations.extend(['hospital', 'hospitales'])
                elif keyword == 'medicamento':
                    keyword_variations.extend(['medicamento', 'medicamentos', 'medicina', 'fármaco'])
                elif keyword == 'paciente':
                    keyword_variations.extend(['paciente', 'pacientes'])
                elif keyword == 'doctor':
                    keyword_variations.extend(['doctor', 'médico', 'médica', 'doctores'])
                elif keyword == 'tratamiento':
                    keyword_variations.extend(['tratamiento', 'tratamientos', 'terapia'])
                elif keyword == 'recursos':
                    keyword_variations.extend(['recurso', 'recursos', 'limitado', 'limitados', 'asignar', 'asignación', 'distribuir'])
                elif keyword == 'medicamento':
                    keyword_variations.extend(['medicamento', 'medicamentos', 'fármaco', 'fármacos', 'medicina experimental', 'tratamiento experimental'])
                elif keyword == 'ia':
                    keyword_variations.extend(['ia', 'inteligencia artificial', 'artificial', 'algoritmo'])
                elif keyword == 'datos':
                    keyword_variations.extend(['dato', 'datos', 'información', 'privacidad'])
                elif keyword == 'tren':
                    keyword_variations.extend(['tren', 'trenes', 'vías', 'vía'])
                elif keyword == 'empresa':
                    keyword_variations.extend(['empresa', 'empresas', 'compañía', 'negocio'])
                
                for variation in keyword_variations:
                    if variation in scenario_lower:
                        return image_url
        
        # Si no se encontró por palabras clave, usar banco de imágenes de la categoría
        if category in IMAGE_BANK:
            images = IMAGE_BANK[category]
        else:
            images = IMAGE_BANK['general']
        
        # Seleccionar imagen determinística basada en hash del escenario
        # Esto asegura que el mismo dilema siempre tenga la misma imagen
        scenario_hash = hash(scenario) % len(images)
        return images[scenario_hash]
        
    except Exception as e:
        print(f"Error obteniendo imagen del dilema: {e}")
        # Fallback a imagen general
        return IMAGE_BANK['general'][0]

def get_ethical_framework_image(ethical_framework):
    """Obtiene una imagen para el marco ético del análisis"""
    try:
        framework = ethical_framework.lower() if ethical_framework else 'general'
        return ETHICAL_FRAMEWORK_IMAGES.get(framework, IMAGE_BANK['general'][0])
    except Exception as e:
        print(f"Error obteniendo imagen del marco ético: {e}")
        return IMAGE_BANK['general'][0]

def cache_dilemma_image(scenario, image_url):
    """Guarda la URL de imagen en el cache del dilema"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE ai_dilemmas_cache SET image_url = ? WHERE dilemma_text = ?',
            (image_url, scenario)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error cacheando imagen: {e}")

def get_cached_dilemma_image(scenario):
    """Obtiene la imagen en cache para un dilema"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT image_url FROM ai_dilemmas_cache WHERE dilemma_text = ?',
            (scenario,)
        )
        result = cursor.fetchone()
        conn.close()
        return result[0] if result and result[0] else None
    except Exception as e:
        print(f"Error obteniendo imagen cacheada: {e}")
        return None

# ==================== FIN SISTEMA DE IMÁGENES ====================

# ==================== SISTEMA DE LOGROS ====================

def init_achievements(cursor):
    """Inicializa los logros predefinidos en la base de datos"""
    achievements = [
        # Logros por cantidad
        ('first_dilemma', 'Primer Paso', 'Completa tu primer dilema ético', '🎯', 'quantity', '1'),
        ('ten_dilemmas', 'Decidido', 'Completa 10 dilemas éticos', '🔟', 'quantity', '10'),
        ('twenty_five_dilemmas', 'Pensador', 'Completa 25 dilemas éticos', '📚', 'quantity', '25'),
        ('fifty_dilemmas', 'Filósofo', 'Completa 50 dilemas éticos', '🧠', 'quantity', '50'),
        ('hundred_dilemmas', 'Maestro Ético', 'Completa 100 dilemas éticos', '👑', 'quantity', '100'),
        
        # Logros por diversidad - Categorías
        ('explorer', 'Explorador', 'Responde dilemas de todas las categorías', '🗺️', 'diversity_categories', None),
        
        # Logros por diversidad - Marcos éticos
        ('philosopher', 'Filósofo Completo', 'Usa todos los marcos éticos diferentes', '🎓', 'diversity_frameworks', None),
        
        # Logros por consistencia - Marcos éticos
        ('utilitarian', 'Utilitarista', 'Elige utilitarismo 5 veces', '⚖️', 'consistency', 'utilitarianismo:5'),
        ('deontologist', 'Deontólogo', 'Elige deontología 5 veces', '📜', 'consistency', 'deontologia:5'),
        ('autonomous', 'Defensor de la Autonomía', 'Elige autonomía 5 veces', '🕊️', 'consistency', 'autonomia:5'),
        ('paternalist', 'Paternalista', 'Elige paternalismo 5 veces', '🛡️', 'consistency', 'paternalismo:5'),
        ('ecocentrist', 'Ecocentrista', 'Elige ecocentrismo 5 veces', '🌱', 'consistency', 'ecocentrismo:5'),
        ('anthropocentrist', 'Antropocentrista', 'Elige antropocentrismo 5 veces', '👥', 'consistency', 'antropocentrismo:5'),
        
        # Logros especiales
        ('thinker', 'Pensador Profundo', 'Completa 10 análisis con IA', '💭', 'special', 'analyses:10'),
        ('speedster', 'Velocista', 'Completa 10 dilemas en una sola sesión', '⚡', 'special', 'session:10'),
    ]
    
    for code, name, description, icon, achievement_type, condition_value in achievements:
        cursor.execute('''
            INSERT OR IGNORE INTO achievements (code, name, description, icon, achievement_type, condition_value)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (code, name, description, icon, achievement_type, condition_value))

def check_and_unlock_achievements(player_name, game_id=None):
    """Verifica y desbloquea logros para un jugador"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Obtener todas las decisiones del jugador
    if game_id:
        cursor.execute('''
            SELECT d.ethical_framework, d.dilemma_category, d.analysis, g.start_time
            FROM decisions d
            JOIN games g ON d.game_id = g.id
            WHERE g.player_name = ? AND d.game_id = ?
        ''', (player_name, game_id))
    else:
        cursor.execute('''
            SELECT d.ethical_framework, d.dilemma_category, d.analysis, g.start_time
            FROM decisions d
            JOIN games g ON d.game_id = g.id
            WHERE g.player_name = ?
        ''', (player_name,))
    
    all_decisions = cursor.fetchall()
    
    if not all_decisions:
        conn.close()
        return []
    
    # Obtener logros ya desbloqueados
    cursor.execute('''
        SELECT a.code FROM achievements a
        JOIN player_achievements pa ON a.id = pa.achievement_id
        WHERE pa.player_name = ?
    ''', (player_name,))
    unlocked_codes = {row[0] for row in cursor.fetchall()}
    
    # Obtener todos los logros disponibles
    cursor.execute('SELECT id, code, achievement_type, condition_value FROM achievements')
    all_achievements = cursor.fetchall()
    
    newly_unlocked = []
    
    for achievement_id, code, achievement_type, condition_value in all_achievements:
        if code in unlocked_codes:
            continue
        
        unlocked = False
        
        if achievement_type == 'quantity':
            # Logros por cantidad total
            total_count = len(all_decisions)
            required = int(condition_value)
            if total_count >= required:
                unlocked = True
        
        elif achievement_type == 'diversity_categories':
            # Explorador: todas las categorías
            categories = {d[1] for d in all_decisions if d[1]}
            required_categories = {'clásico', 'medicina', 'tecnología', 'medio ambiente', 'negocios', 'sociedad'}
            if required_categories.issubset(categories):
                unlocked = True
        
        elif achievement_type == 'diversity_frameworks':
            # Filósofo: todos los marcos éticos
            frameworks = {d[0] for d in all_decisions if d[0]}
            required_frameworks = {'utilitarianismo', 'deontologia', 'autonomia', 'paternalismo', 'ecocentrismo', 'antropocentrismo'}
            if required_frameworks.issubset(frameworks):
                unlocked = True
        
        elif achievement_type == 'consistency':
            # Logros por consistencia: usar el mismo marco X veces
            framework, count = condition_value.split(':')
            framework_count = sum(1 for d in all_decisions if d[0] == framework)
            if framework_count >= int(count):
                unlocked = True
        
        elif achievement_type == 'special':
            if condition_value.startswith('analyses:'):
                # Pensador: análisis completados
                required = int(condition_value.split(':')[1])
                analyses_count = sum(1 for d in all_decisions if d[2] and d[2].strip())
                if analyses_count >= required:
                    unlocked = True
            elif condition_value.startswith('session:'):
                # Velocista: dilemas en una sesión
                if game_id:
                    required = int(condition_value.split(':')[1])
                    cursor.execute('SELECT COUNT(*) FROM decisions WHERE game_id = ?', (game_id,))
                    session_count = cursor.fetchone()[0]
                    if session_count >= required:
                        unlocked = True
        
        if unlocked:
            # Desbloquear logro
            try:
                cursor.execute('''
                    INSERT INTO player_achievements (player_name, achievement_id)
                    VALUES (?, ?)
                ''', (player_name, achievement_id))
                
                # Obtener información del logro
                cursor.execute('SELECT name, description, icon FROM achievements WHERE id = ?', (achievement_id,))
                achievement_info = cursor.fetchone()
                newly_unlocked.append({
                    'code': code,
                    'name': achievement_info[0],
                    'description': achievement_info[1],
                    'icon': achievement_info[2]
                })
            except sqlite3.IntegrityError:
                # Ya estaba desbloqueado (race condition)
                pass
    
    conn.commit()
    conn.close()
    return newly_unlocked

def get_player_achievements(player_name):
    """Obtiene todos los logros de un jugador"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT a.code, a.name, a.description, a.icon, pa.unlocked_at
        FROM achievements a
        JOIN player_achievements pa ON a.id = pa.achievement_id
        WHERE pa.player_name = ?
        ORDER BY pa.unlocked_at DESC
    ''', (player_name,))
    
    unlocked = [{
        'code': row[0],
        'name': row[1],
        'description': row[2],
        'icon': row[3],
        'unlocked_at': row[4]
    } for row in cursor.fetchall()]
    
    # Obtener todos los logros disponibles para mostrar progreso
    cursor.execute('SELECT code, name, description, icon FROM achievements ORDER BY id')
    all_achievements = cursor.fetchall()
    
    unlocked_codes = {a['code'] for a in unlocked}
    
    all_achievements_list = []
    for code, name, description, icon in all_achievements:
        all_achievements_list.append({
            'code': code,
            'name': name,
            'description': description,
            'icon': icon,
            'unlocked': code in unlocked_codes
        })
    
    conn.close()
    return {
        'unlocked': unlocked,
        'all': all_achievements_list,
        'total': len(all_achievements_list),
        'unlocked_count': len(unlocked)
    }

def calculate_retroactive_achievements():
    """Calcula logros retroactivamente para todos los jugadores existentes"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Obtener todos los nombres de jugadores únicos
    cursor.execute('SELECT DISTINCT player_name FROM games')
    players = [row[0] for row in cursor.fetchall()]
    
    total_unlocked = 0
    for player_name in players:
        newly_unlocked = check_and_unlock_achievements(player_name)
        total_unlocked += len(newly_unlocked)
        if newly_unlocked:
            print(f"✅ {player_name}: {len(newly_unlocked)} logros desbloqueados retroactivamente")
    
    conn.close()
    return total_unlocked

# ==================== FIN SISTEMA DE LOGROS ====================

def generate_dilemma_with_gemini():
    """Generate a new ethical dilemma using Google Gemini"""
    if not GOOGLE_API_KEY:
        return None
    
    try:
        # Usar gemini-2.5-flash (más reciente y estable)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
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

def cache_dilemma(dilemma_data):
    """Cache AI-generated dilemmas to avoid duplicates"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener imagen para el dilema
        category = dilemma_data.get('category', 'general')
        scenario = dilemma_data['scenario']
        image_url = get_dilemma_image(scenario, category)
        
        cursor.execute(
            '''INSERT OR IGNORE INTO ai_dilemmas_cache (dilemma_text, scenario, options, category, image_url) 
               VALUES (?, ?, ?, ?, ?)''',
            (scenario, scenario, 
             json.dumps(dilemma_data['options']), category, image_url)
        )
        
        # Si el registro ya existía, actualizar la imagen
        cursor.execute(
            'UPDATE ai_dilemmas_cache SET image_url = ? WHERE dilemma_text = ? AND image_url IS NULL',
            (image_url, scenario)
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
        
        # Usar gemini-2.5-flash (más reciente y estable)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
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
    try:
        return render_template('index.html')
    except Exception as e:
        print(f"ERROR rendering template: {e}")
        return f"Error loading template: {str(e)}", 500

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
    """Get a random ethical dilemma with image"""
    # Try Gemini first, then predefined
    ai_dilemma = None
    
    # Intentar con Gemini
    if GOOGLE_API_KEY:
        ai_dilemma = generate_dilemma_with_gemini()
    
    if ai_dilemma:
        dilemma = ai_dilemma
        dilemma['id'] = random.randint(1000, 9999)  # Assign random ID for AI dilemmas
        if 'category' not in dilemma:
            dilemma['category'] = 'general'
        
        # Obtener imagen del dilema (verificar cache primero)
        scenario = dilemma.get('scenario', '')
        cached_image = get_cached_dilemma_image(scenario)
        if cached_image:
            dilemma['image_url'] = cached_image
        else:
            dilemma['image_url'] = get_dilemma_image(scenario, dilemma.get('category', 'general'))
    else:
        # Fallback to predefined dilemmas
        dilemma = random.choice(PREDEFINED_DILEMMAS).copy()
        # Obtener imagen para dilema predefinido
        scenario = dilemma.get('scenario', '')
        category = dilemma.get('category', 'general')
        dilemma['image_url'] = get_dilemma_image(scenario, category)
    
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
        
        conn = get_db_connection()
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
        
        # Obtener nombre del jugador para verificar logros
        cursor.execute('SELECT player_name FROM games WHERE id = ?', (game_id,))
        player_result = cursor.fetchone()
        player_name = player_result[0] if player_result else None
        
        conn.commit()
        conn.close()
        
        # Verificar y desbloquear logros (no bloquea si falla)
        newly_unlocked = []
        if player_name:
            try:
                newly_unlocked = check_and_unlock_achievements(player_name, game_id)
            except Exception as e:
                print(f"⚠️ Error verificando logros: {e}")
        
        # Obtener imagen para el análisis ético
        ethical_image_url = get_ethical_framework_image(ethical_framework)
        
        return jsonify({
            'status': 'success',
            'analysis': analysis,
            'ethical_framework_image': ethical_image_url,
            'newly_unlocked_achievements': newly_unlocked
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
    player_name = game_info[0] if game_info else None
    
    conn.close()
    
    # Verificar logros una vez más al ver estadísticas (por si acaso)
    if player_name:
        try:
            check_and_unlock_achievements(player_name, game_id)
        except Exception as e:
            print(f"⚠️ Error verificando logros en stats: {e}")
    
    return jsonify({
        'framework_stats': framework_stats,
        'category_stats': category_stats,
        'total_decisions': total_decisions,
        'player_name': player_name if player_name else 'Unknown',
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

@app.route('/api/get_achievements/<player_name>', methods=['GET'])
def get_achievements(player_name):
    """Get all achievements for a player"""
    try:
        achievements_data = get_player_achievements(player_name)
        return jsonify(achievements_data)
    except Exception as e:
        print(f"❌ Error obteniendo logros: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    init_db()
    print("🧠 Ethical Dilemma Simulator starting...")
    print(f"📊 Database initialized: {DATABASE}")
    print(f"🤖 Google Gemini: {'✅ Enabled' if GOOGLE_API_KEY else '❌ Disabled'}")
    print(f"📚 Predefined dilemmas: {len(PREDEFINED_DILEMMAS)}")
    
    # Calcular logros retroactivamente para jugadores existentes
    print("🏆 Calculando logros retroactivos...")
    try:
        total_unlocked = calculate_retroactive_achievements()
        if total_unlocked > 0:
            print(f"✅ {total_unlocked} logros desbloqueados retroactivamente")
        else:
            print("✅ No hay logros nuevos para desbloquear")
    except Exception as e:
        print(f"⚠️ Error calculando logros retroactivos: {e}")
    
    print("🚀 Server running on http://localhost:5000")
    app.run(debug=True)