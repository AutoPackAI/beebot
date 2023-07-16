class Plan:
    """Holder for a plan. Ideally this will have steps that are broken down into a list. And maybe persistence?"""

    plan_text: str

    def __init__(self, plan_text: str):
        self.plan_text = plan_text
