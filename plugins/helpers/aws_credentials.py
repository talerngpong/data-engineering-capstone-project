from dataclasses import dataclass


@dataclass
class AwsCredentials:
    access_key_id: str
    secret_access_key: str
