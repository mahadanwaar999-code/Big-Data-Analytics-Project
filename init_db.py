# init_db.py
print("Initializing database...")
try:
    from app import create_tables
    create_tables()
    print("Database initialization complete!")
except Exception as e:
    print(f"Error initializing database: {e}")
    # Still try to start Flask
    print("Starting Flask anyway...")