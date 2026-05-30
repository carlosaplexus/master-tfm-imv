import pytest
from backend.app import create_app, db

@pytest.fixture
def client():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
    })

    with app.app_context():

        # PARCHE SOLO PARA SQLITE
        if "sqlite" in app.config["SQLALCHEMY_DATABASE_URI"]:
            for table in db.metadata.tables.values():
                for col in table.columns:
                    if str(col.type) == "BIGINT" and col.primary_key:
                        col.type = db.Integer()

        db.create_all()

        client = app.test_client()
        yield client

        db.drop_all()


