from dataclasses import dataclass


@dataclass
class RichQuery:
    value: str
    table_name: str


default_query = RichQuery(value='', table_name='')
