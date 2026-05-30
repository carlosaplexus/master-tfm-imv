import pytest
from backend.app import app, db

@pytest.fixture
def client():
    # 1. Cambiar la URI ANTES de crear el contexto
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True

    # 2. Crear un contexto de aplicación
    with app.app_context():

        # 3. Cerrar conexiones previas a PostgreSQL
        db.session.remove()
        db.engine.dispose()

        # 4. Recrear las tablas en SQLite
        db.create_all()

        # 5. Crear el cliente de pruebas
        testing_client = app.test_client()

        yield testing_client

        # 6. Limpieza final
        db.session.remove()
        db.drop_all()
