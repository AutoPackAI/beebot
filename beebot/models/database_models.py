from tortoise import fields, Tortoise
from tortoise.fields import JSONField
from tortoise.models import Model
from yoyo import get_backend, read_migrations


class BaseModel(Model):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        abstract = True


class BodyModel(BaseModel):
    INCLUSIVE_PREFETCH = "memory_chains__memories__document_memories__document"

    id = fields.IntField(pk=True)
    initial_task = fields.TextField()
    current_task = fields.TextField()
    state = fields.TextField(default="setup")
    packs = JSONField(default=list)

    class Meta:
        table = "body"


class MemoryChainModel(BaseModel):
    id = fields.IntField(pk=True)
    body = fields.ForeignKeyField("models.BodyModel", related_name="memory_chains")

    class Meta:
        table = "memory_chain"


class MemoryModel(BaseModel):
    id = fields.IntField(pk=True)
    memory_chain = fields.ForeignKeyField(
        "models.MemoryChainModel", related_name="memories"
    )
    plan = JSONField(default=dict)
    decision = JSONField(default=dict)
    observation = JSONField(default=dict)

    class Meta:
        table = "memory"


class DocumentModel(BaseModel):
    id = fields.IntField(pk=True)
    name = fields.TextField()
    content = fields.TextField()

    class Meta:
        table = "document"


class DocumentMemoryModel(BaseModel):
    id = fields.IntField(pk=True)
    memory = fields.ForeignKeyField(
        "models.MemoryModel", related_name="document_memories"
    )
    document = fields.ForeignKeyField(
        "models.DocumentModel", related_name="document_memories"
    )

    class Meta:
        table = "document_memory"


def apply_migrations(db_url: str):
    """Apply any outstanding migrations"""
    backend = get_backend(db_url)
    backend.init_database()
    migrations = read_migrations("migrations")

    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))


async def initialize_db(db_url: str):
    # Don't re-initialize an already initialized database
    if Tortoise.describe_models():
        return

    await Tortoise.init(
        db_url=db_url,
        modules={"models": ["beebot.models.database_models"]},
        use_tz=True,
    )
    if db_url == "sqlite://:memory:":
        await Tortoise.generate_schemas()
    else:
        apply_migrations(db_url)
