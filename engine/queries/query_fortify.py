from typing import Literal

from engine.queries.base_query import BaseQuery


class QueryFortifyTerritory(BaseQuery):
    query_type: Literal["fortify"] = "fortify"