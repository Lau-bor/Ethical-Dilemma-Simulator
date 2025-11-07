#!/usr/bin/env python3
"""
Script de migración de base de datos
Ejecuta este script para actualizar la base de datos con las nuevas columnas
"""
import sqlite3

DATABASE = 'ethical_game.db'

def migrate_db():
    """Migrate database schema to add new columns if they don't exist"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Verificar columnas existentes en decisions
        cursor.execute('PRAGMA table_info(decisions)')
        existing_columns = [col[1] for col in cursor.fetchall()]
        print(f"Columnas actuales en 'decisions': {existing_columns}")
        
        # Agregar dilemma_category si no existe
        if 'dilemma_category' not in existing_columns:
            cursor.execute('ALTER TABLE decisions ADD COLUMN dilemma_category TEXT')
            print("[OK] Agregada columna 'dilemma_category' a la tabla decisions")
        else:
            print("[INFO] La columna 'dilemma_category' ya existe")
        
        # Agregar analysis si no existe
        if 'analysis' not in existing_columns:
            cursor.execute('ALTER TABLE decisions ADD COLUMN analysis TEXT')
            print("[OK] Agregada columna 'analysis' a la tabla decisions")
        else:
            print("[INFO] La columna 'analysis' ya existe")
        
        # Verificar columnas existentes en games
        cursor.execute('PRAGMA table_info(games)')
        existing_columns_games = [col[1] for col in cursor.fetchall()]
        print(f"Columnas actuales en 'games': {existing_columns_games}")
        
        # Agregar dilemmas_answered si no existe
        if 'dilemmas_answered' not in existing_columns_games:
            cursor.execute('ALTER TABLE games ADD COLUMN dilemmas_answered INTEGER DEFAULT 0')
            print("[OK] Agregada columna 'dilemmas_answered' a la tabla games")
        else:
            print("[INFO] La columna 'dilemmas_answered' ya existe")
        
        conn.commit()
        conn.close()
        
        print("\n[SUCCESS] Migracion completada exitosamente!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error durante la migracion: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Iniciando migracion de base de datos...")
    print("-" * 50)
    migrate_db()
    print("-" * 50)

