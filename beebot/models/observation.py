from dataclasses import dataclass


@dataclass
class Observation:
    response: any = ""
    error_reason: str = ""
    success: bool = True

    def compressed(self) -> str:
        """Return this output as a str that is smaller so that it uses fewer tokens"""
        result = self.response
        # Make dicts more readable
        if type(result) == dict:
            if self.success:
                return ", ".join([f"{k}: {v}" for (k, v) in result.items()])
            else:
                return "Error: " + ", ".join([f"{k}: {v}" for (k, v) in result.items()])
        else:
            if self.success:
                return result
            else:
                return f"Error: {result}"

    @property
    def persisted_dict(self):
        return self.__dict__
