"""
Script de prueba para verificar la conexion con Gemini API
"""
import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

# Configurar codificacion UTF-8 para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def test_gemini_connection():
    """Prueba la conexion con Gemini API"""
    
    print("=" * 60)
    print("PRUEBA DE CONEXION CON GEMINI API")
    print("=" * 60)
    print()
    
    # Cargar variables de entorno
    print("[*] Cargando archivo .env...")
    load_dotenv()
    
    # Obtener API key
    api_key = os.getenv('GOOGLE_API_KEY')
    
    if not api_key:
        print("[ERROR] No se encontro GOOGLE_API_KEY en el archivo .env")
        print()
        print("Solucion:")
        print("  1. Crea un archivo .env en la raiz del proyecto")
        print("  2. Agrega la linea: GOOGLE_API_KEY=tu_api_key_aqui")
        print("  3. Reemplaza 'tu_api_key_aqui' con tu API key real de Gemini")
        return False
    
    print(f"[OK] API Key encontrada: {api_key[:10]}...{api_key[-5:]}")
    print()
    
    # Configurar Gemini
    print("[*] Configurando Gemini API...")
    try:
        genai.configure(api_key=api_key)
        print("[OK] Gemini API configurada correctamente")
        print()
    except Exception as e:
        print(f"[ERROR] Al configurar Gemini API: {e}")
        return False
    
    # Listar modelos disponibles
    print("[*] Listando modelos disponibles...")
    try:
        available_models = genai.list_models()
        model_names = [model.name for model in available_models if 'generateContent' in model.supported_generation_methods]
        print(f"[OK] Se encontraron {len(model_names)} modelos disponibles")
        if model_names:
            print("   Modelos disponibles:")
            for name in model_names[:5]:  # Mostrar solo los primeros 5
                display_name = name.split('/')[-1] if '/' in name else name
                print(f"     - {display_name}")
        print()
    except Exception as e:
        print(f"[WARNING] No se pudieron listar los modelos: {e}")
        print("   Usando lista predeterminada de modelos...")
        print()
        model_names = []
    
    # Lista de modelos a probar (prioridad - modelos más recientes primero)
    preferred_models = [
        'gemini-2.5-flash',
        'gemini-2.5-pro',
        'gemini-2.0-flash-exp',
        'gemini-1.5-flash-latest',
        'gemini-1.5-pro-latest',
        'gemini-1.5-flash',
        'gemini-1.5-pro',
        'gemini-pro'
    ]
    
    # Si encontramos modelos disponibles, usar los que están disponibles
    if model_names:
        available_short_names = [name.split('/')[-1] for name in model_names]
        # Priorizar modelos preferidos que estén disponibles
        models_to_test = [m for m in preferred_models if m in available_short_names]
        # Si no hay modelos preferidos disponibles, usar los primeros disponibles
        if not models_to_test:
            models_to_test = [name.split('/')[-1] for name in model_names[:3]]
    else:
        # Si no se pudieron listar modelos, usar la lista predeterminada
        models_to_test = preferred_models
    
    if not models_to_test:
        print("[ERROR] No se encontraron modelos disponibles para probar")
        return False
    
    success = False
    
    # Probar cada modelo
    for model_name in models_to_test:
        print(f"[*] Probando modelo: {model_name}")
        try:
            model = genai.GenerativeModel(model_name)
            
            # Hacer una prueba simple
            prompt = "Responde con una sola palabra: 'funciona'"
            response = model.generate_content(prompt)
            
            if response and response.text:
                print(f"   [OK] Modelo {model_name} funciona correctamente")
                print(f"   [RESPONSE] {response.text.strip()}")
                print()
                success = True
                break
            else:
                print(f"   [WARNING] Modelo {model_name} respondio vacio")
                print()
                
        except google_exceptions.ResourceExhausted as e:
            error_msg = str(e)
            if "quota" in error_msg.lower() or "429" in error_msg:
                print(f"   [ERROR] Cuota de API excedida")
                print(f"   Tu API key ha alcanzado el limite de uso gratuito")
                print(f"   Espera un tiempo o verifica tu plan en Google AI Studio")
                print()
                return False
            else:
                print(f"   [WARNING] Error de recursos: {e}")
                print()
                
        except google_exceptions.PermissionDenied as e:
            print(f"   [ERROR] Permiso denegado")
            print(f"   Verifica que tu API key sea valida y tenga los permisos necesarios")
            print(f"   Verifica en: https://ai.google.dev/")
            print()
            return False
            
        except google_exceptions.InvalidArgument as e:
            print(f"   [ERROR] Argumento invalido")
            print(f"   El modelo {model_name} podria no estar disponible")
            print(f"   Error: {e}")
            print()
            continue
            
        except Exception as e:
            print(f"   [WARNING] Error con modelo {model_name}: {e}")
            print()
            continue
    
    # Resumen final
    print("=" * 60)
    if success:
        print("[SUCCESS] PRUEBA EXITOSA: La conexion con Gemini API funciona correctamente")
        print()
        print("Tu aplicacion puede usar Gemini API para:")
        print("  - Generar dilemas eticos")
        print("  - Analizar decisiones de los jugadores")
    else:
        print("[FAILED] PRUEBA FALLIDA: No se pudo conectar con ningun modelo de Gemini")
        print()
        print("Posibles soluciones:")
        print("  1. Verifica que tu API key sea correcta")
        print("  2. Verifica que tengas conexion a internet")
        print("  3. Verifica que el modelo este disponible en tu region")
        print("  4. Revisa tu cuenta en: https://ai.google.dev/")
    print("=" * 60)
    
    return success

if __name__ == '__main__':
    try:
        test_gemini_connection()
    except KeyboardInterrupt:
        print("\n\n[INFO] Prueba interrumpida por el usuario")
    except Exception as e:
        print(f"\n\n[ERROR] ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()

