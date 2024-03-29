"""FluidStack API client."""

import json
import uuid
from pathlib import Path

import requests


def get_key_suffix():
    return str(uuid.uuid4()).replace('-', '')[:8]


ENDPOINT = Path('https://console.vast.ai/api/v0')
VASTAI_API_KEY_PATH = Path('~/.vastai/api_key').expanduser()


def read_contents(path: str) -> str:
    with open(path, mode='r', encoding='utf-8') as f:
        return f.read().strip()


class VastAIAPIError(Exception):

    def __init__(self, message: str, code: int = 400):
        self.code = code
        super().__init__(message)


def raise_vastai_error(response: requests.Response) -> None:
    status_code = response.status_code
    if response.ok:
        return
    try:
        resp_json = response.json()
        message = resp_json.get('error', response.text)
    except (KeyError, json.decoder.JSONDecodeError) as e:
        raise VastAIAPIError(
            f'Unexpected error. Status code: {status_code} \n {response.text}'
            f'\n {str(e)}',
            code=status_code) from e
    raise VastAIAPIError(f'{message}', status_code)


class VastAIClient:
    """Vast AI API Client"""

    def __init__(self):
        self.api_key = read_contents(VASTAI_API_KEY_PATH)
