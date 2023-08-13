import json

from tortoise import fields, Tortoise
from tortoise.fields import JSONField, BooleanField
from tortoise.models import Model
from yoyo import get_backend, read_migrations


class BaseModel(Model):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    def json(self):
        json_dict = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
        json_dict.pop("created_at")
        json_dict.pop("updated_at")
        return json.dumps(json_dict)

    class Meta:
        abstract = True


class BodyModel(BaseModel):
    INCLUSIVE_PREFETCH = "task_executions__steps__document_steps__document"

    task = fields.TextField()

    class Meta:
        table = "body"


class TaskExecutionModel(BaseModel):
    body = fields.ForeignKeyField("models.BodyModel", related_name="task_executions")
    agent = fields.TextField()
    state = fields.TextField(default="waiting")
    instructions = fields.TextField()
    inputs = JSONField(default=list)
    outputs = JSONField(default=list)
    complete = BooleanField(default=False)
    variables = JSONField(default=dict)

    class Meta:
        table = "task_execution"


class StepModel(BaseModel):
    task_execution = fields.ForeignKeyField(
        "models.TaskExecutionModel", related_name="steps"
    )
    plan = fields.ForeignKeyField("models.Plan", related_name="steps", null=True)
    decision = fields.ForeignKeyField(
        "models.Decision", related_name="steps", null=True
    )
    observation = fields.ForeignKeyField(
        "models.Observation", related_name="steps", null=True
    )
    oversight = fields.ForeignKeyField(
        "models.Oversight", related_name="steps", null=True
    )

    class Meta:
        table = "step"


class Oversight(BaseModel):
    original_plan_text = fields.TextField()
    modified_plan_text = fields.TextField()
    modifications = JSONField(default=dict)
    prompt_variables = JSONField(default=dict)
    llm_response = fields.TextField(default="")

    class Meta:
        table = "oversight"


class Decision(BaseModel):
    tool_name = fields.TextField()
    tool_args = JSONField(default=dict)
    prompt_variables = JSONField(default=dict)
    llm_response = fields.TextField(default="")

    class Meta:
        table = "decision"


class Observation(BaseModel):
    response = fields.TextField(null=True)
    error_reason = fields.TextField(null=True)
    success = fields.BooleanField(default=True)

    class Meta:
        table = "observation"


class Plan(BaseModel):
    plan_text = fields.TextField()
    prompt_variables = JSONField(default=dict)
    llm_response = fields.TextField(default="")

    class Meta:
        table = "plan"


class DocumentModel(BaseModel):
    name = fields.TextField()
    content = fields.TextField()

    class Meta:
        table = "document"


class DocumentStep(BaseModel):
    step = fields.ForeignKeyField("models.StepModel", related_name="document_steps")
    document = fields.ForeignKeyField(
        "models.DocumentModel", related_name="document_steps"
    )

    class Meta:
        table = "document_step"


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
