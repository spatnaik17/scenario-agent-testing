from pydantic import BaseModel

import json


class SerializableAndPydanticEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, BaseModel):
            return o.model_dump(exclude_unset=True)
        return super().default(o)
