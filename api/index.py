"""
Vercel serverless entry point for Flask app
"""
import sys
import os

# Detect Vercel environment
os.environ['VERCEL'] = '1'

# Add parent directory to Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Change to parent directory so Flask can find templates and static
os.chdir(parent_dir)

# Import Flask app after setting up path
try:
    from app import app, init_db
    
    # Initialize database (only once per serverless instance)
    try:
        init_db()
    except Exception as e:
        print(f"Warning: Error inicializando BD (continuando): {e}")
        # Continue even if DB init fails - app can still serve predefined dilemmas
        
except Exception as e:
    print(f"ERROR: No se pudo importar la app: {e}")
    import traceback
    traceback.print_exc()
    raise

# Export app for Vercel Python runtime
# Vercel will use this as the WSGI application
__all__ = ['app']

