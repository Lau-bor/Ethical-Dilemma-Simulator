# 🧠 Ethical Dilemma Simulator

Simulador web de dilemas éticos con generación opcional de contenido y análisis mediante Google Gemini. Proporciona dilemas predefinidos, caché de dilemas generados por IA, sistema de logros y API REST para interacción desde el frontend.

🔧 **Requisito principal:** `Python 3.12.7`

⚠️ **Aviso:** El proyecto fue desarrollado y probado con `Python 3.12.7`. Se recomienda usar exactamente esa versión para evitar incompatibilidades con dependencias.

📦 **Contenido del repositorio (resumen):**

- `app.py` — Aplicación Flask con la lógica principal del juego, endpoints y manejo de base de datos SQLite.
- `migrate_db.py` — Script para aplicar migraciones a la base de datos `ethical_game.db`.
- `requirements.txt` — Dependencias del proyecto.
- `test_gemini_connection.py` — Script para verificar la conexión con la API de Gemini (opcional).
- `templates/index.html` — Interfaz web principal.
- `static/` — Recursos estáticos, incluido `generated_images/`.

🗄️ **Base de datos:** `ethical_game.db` (SQLite) se crea en la raíz del proyecto al inicializar la app o ejecutar las migraciones.

✨ **Características principales:**

- 🤖 Generación opcional de dilemas con Google Gemini (`GOOGLE_API_KEY`).
- 🧾 Caché de dilemas generados por IA en la BD.
- 🏆 Sistema de logros y estadísticas por sesión.
- 🖼️ Imágenes para dilemas y marcos éticos (banco de imágenes y mapeos a Unsplash).

🚀 **Preparación rápida (Windows PowerShell)**

1. Verificar versión de Python (debe ser 3.12.7):

```powershell
py -3.12 --version
```

2. Crear y activar un entorno virtual (recomendado):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Actualizar `pip` e instalar dependencias:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

4. (Opcional) Añadir tu API key de Google Gemini en un archivo `.env` en la raíz:

```text
GOOGLE_API_KEY=tu_api_key_aqui
```

5. Migrar/crear la base de datos (recomendado):

```powershell
python migrate_db.py
```

6. Levantar la aplicación (usar `flask run` para exponer el servidor):

```powershell
$env:FLASK_APP = 'app.py'
$env:FLASK_ENV = 'development'  # opcional
flask run --host=0.0.0.0 --port=5000
```

> Nota: `app.py` inicializa la BD cuando se importa/ejecuta, pero no llama a `app.run()` directamente; por eso recomendamos usar `flask run` para arrancar el servidor de desarrollo.

🔎 **Probar la conexión a Gemini (opcional)**

Si configuraste `GOOGLE_API_KEY` en `.env`, puedes probar la conexión con:

```powershell
python test_gemini_connection.py
```

Este script intentará listar modelos y ejecutar una pequeña prueba con modelos preferidos (p. ej. `gemini-2.5-flash`).

📡 **Endpoints principales (resumen)**

- `GET /` — Interfaz web principal (renderiza `templates/index.html`).
- `POST /api/start_game` — Inicia una sesión de juego. Cuerpo JSON: `{ "player_name": "TuNombre" }`.
- `GET /api/get_dilemma` — Obtiene un dilema (prioriza Gemini si `GOOGLE_API_KEY` está presente; si no, selecciona uno predefinido).
- `POST /api/make_decision` — Registra una decisión y devuelve análisis opcional. Cuerpo JSON esperado contiene `game_id`, `dilemma_id`, `dilemma_text`, `chosen_option`, `ethical_framework` y `full_dilemma` (opcional para análisis con IA).
- `GET /api/get_stats/<game_id>` — Obtiene estadísticas de la sesión.
- `POST /api/end_game` — Marca el final de la sesión. Cuerpo JSON: `{ "game_id": <id> }`.
- `GET /api/get_achievements/<player_name>` — Devuelve logros del jugador.

Ejemplo rápido con PowerShell para obtener un dilema:

```powershell
$d = Invoke-RestMethod -Uri http://127.0.0.1:5000/api/get_dilemma
$d | ConvertTo-Json -Depth 5
```

Ejemplo para iniciar juego y enviar decisión (PowerShell):

```powershell
$start = Invoke-RestMethod -Uri http://127.0.0.1:5000/api/start_game -Method Post -Body (@{ player_name = 'Tester' } | ConvertTo-Json) -ContentType 'application/json'
$game_id = $start.game_id

# Hacer una petición para enviar decisión (ejemplo simplificado)
$body = @{ game_id = $game_id; dilemma_id = 1; dilemma_text = 'Texto del dilema'; chosen_option = 'Accionar'; ethical_framework = 'utilitarianismo' } | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:5000/api/make_decision -Method Post -Body $body -ContentType 'application/json'
```

🔬 **Cómo funciona (resumen técnico)**

- `app.py` mantiene un arreglo `PREDEFINED_DILEMMAS` y funciones para generar dilemas con Gemini mediante `google.generativeai` cuando `GOOGLE_API_KEY` está configurada.
- Los dilemas AI se cachean en la tabla `ai_dilemmas_cache` para evitar duplicados y mejorar performance.
- Cada decisión que envía el cliente se guarda en la tabla `decisions` y, opcionalmente, se envía a Gemini para obtener un análisis (si existe la API key).
- El sistema de logros se administra en `achievements` y `player_achievements`, y hay funciones que verifican y desbloquean logros tras cada decisión.
- El módulo de imágenes selecciona imágenes de un banco (Unsplash) basándose en categoría y palabras clave del escenario.

🛠️ **Puntos a tener en cuenta / Troubleshooting**

- 🐍 Asegúrate de usar `Python 3.12.7` (si no tienes esa versión, instala o usa `pyenv`/`py -3.12`).
- ⚙️ Si no quieres usar Gemini, omite `GOOGLE_API_KEY`; la app caerá a los dilemas predefinidos.
- ✅ Si al ejecutar `flask run` ves errores de migración o tablas faltantes, ejecuta primero `python migrate_db.py`.
- 🔐 En Windows PowerShell, para persistir variables de entorno entre sesiones, considera usar `setx` (ej.: `setx GOOGLE_API_KEY "tu_api_key"`).

🧪 **Pruebas**

Hay `pytest` en `requirements.txt`. Para ejecutar pruebas (si se añaden):

```powershell
pytest -q
```

💡 **Siguientes pasos recomendados**

- (Opcional) Añadir `Procfile` o script para producción.
- Revisar el final de `app.py` si prefieres que el script arranque el servidor directamente con `app.run()`.

