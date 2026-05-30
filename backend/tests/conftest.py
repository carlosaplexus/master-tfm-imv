import pytest
from backend.app import app, db

print(">>> conftest de backend/tests cargado")

@pytest.fixture
def client():
    # Cambiar la base de datos ANTES de crear el contexto
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True

    with app.app_context():
        # Cerrar conexiones previas a PostgreSQL
        db.session.remove()
        db.engine.dispose()

        # Crear tablas en SQLite
        db.create_all()

        client = app.test_client()
        yield client

        # Limpieza
        db.session.remove()
        db.drop_all()
