from peewee import (
    Model,
    TextField,
    DateTimeField,
    ForeignKeyField,
    Database,
)
from playhouse.db_url import connect
from playhouse.postgres_ext import JSONField
from yoyo import get_backend
from yoyo import read_migrations


class BaseModel(Model):
    class Meta:
        database = None

    @classmethod
    def set_database(cls, database: Database):
        cls._meta.database = database


class BodyModel(BaseModel):
    class Meta:
        table_name = "body"

    initial_task = TextField()
    current_task = TextField()
    state = TextField()
    created_at = DateTimeField()
    updated_at = DateTimeField()


class MemoryChainModel(BaseModel):
    class Meta:
        table_name = "memory_chain"

    body = ForeignKeyField(BodyModel, backref="memory_chains")
    created_at = DateTimeField()
    updated_at = DateTimeField()


class MemoryModel(BaseModel):
    class Meta:
        table_name = "memory"

    memory_chain = ForeignKeyField(MemoryChainModel, backref="memories")
    plan = JSONField()
    decision = JSONField()
    observation = JSONField()
    created_at = DateTimeField()
    updated_at = DateTimeField()


def apply_migrations(db_url: str):
    """Apply any outstanding migrations"""
    backend = get_backend(db_url)
    migrations = read_migrations("migrations")

    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))


def initialize_db(db_url: str) -> Database:
    database = connect(db_url)
    for model_class in [BaseModel, BodyModel, MemoryChainModel, MemoryModel]:
        model_class.set_database(database)

    apply_migrations(db_url)
    return database
