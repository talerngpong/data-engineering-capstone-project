from typing import List, Optional
import requests
from requests.models import Response
from dataclasses import dataclass


@dataclass
class Country:
    name: str
    code: str


class BattutaDataSource:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_countries(self) -> List[Country]:
        response: Response = requests.get(
            url=f'http://battuta.medunes.net/api/country/all/?key={self.api_key}'
        )
        j = response.json()
        return BattutaDataSource.convert_battuta_response_json_to_countries(j)

    @staticmethod
    def convert_battuta_response_json_to_countries(json: any) -> List[Country]:
        if not isinstance(json, list):
            return []

        nullable_countries: List[Optional[Country]] = [
            BattutaDataSource.convert_j_country_to_country(j_country)
            for j_country
            in json
        ]

        return [
            nullable_country
            for nullable_country
            in nullable_countries
            if nullable_country is not None
        ]

    @staticmethod
    def convert_j_country_to_country(j_country: any) -> Optional[Country]:
        if not isinstance(j_country, dict):
            return None

        dict_keys = j_country.keys()
        if ('name' not in dict_keys) or ('code' not in dict_keys):
            return None
        if (not isinstance(j_country['name'], str)) or (not isinstance(j_country['code'], str)):
            return None

        return Country(name=j_country['name'], code=j_country['code'])
