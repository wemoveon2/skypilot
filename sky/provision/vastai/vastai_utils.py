"""FluidStack API client."""

import json
import csv
import uuid
from pathlib import Path

import requests


def get_key_suffix():
    return str(uuid.uuid4()).replace('-', '')[:8]


ENDPOINT = 'https://console.vast.ai/api/v0/'
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

    def __init__(self, endpoint = ENDPOINT, key_path = VASTAI_API_KEY_PATH):
        self.api_key = read_contents(key_path)
        self.endpoint = endpoint
    
    def get_instances(self): 
      response = requests.get(self.endpoint + 'bundles', auth=('Key', self.api_key), params={
      "verified": {"eq": True},
      "rentable": {"eq": True},
      "order": [["dphtotal","asc"],["total_flops","asc"]],
      "cuda_max_good": {"gte":12.1},
      "limit": 192
    })
      raise_vastai_error(response)
      offers: dict = response.json()
      parsed_offers = list()
      for offer in offers['offers']:
        parsed_offers.append(self.__parse_offer(offer))
      return parsed_offers

    def __parse_offer(self, offer) -> dict:
      def get_gpu_info(offer) -> str: 
        return json.dumps({
        'Gpus': [{
            'Name': offer['gpu_name'],
            'Manufacturer': offer.get('gpu_arch', 'unk').upper(),
            'Count': offer['num_gpus'],
            'MemoryInfo': {
                'SizeInMiB': offer['gpu_ram']
            }
          }],
        'TotalGpuMemoryInMiB': float(offer['gpu_ram']) * int(offer['num_gpus'])
        })
      return {
          "InstanceType": f"{offer['cpu_name']}_{offer['gpu_name']}".replace(" ", "_").lower(),
          "AcceleratorName": offer["gpu_name"].replace(" ", ""),
          "AcceleratorCount": str(offer["num_gpus"]).strip(),
          "vCPUs": offer["cpu_cores"],
          "MemoryGiB": offer["cpu_ram"] // 1024,  # Convert MiB to GiB
          "Price": offer["dph_total"],
          "Region": offer["geolocation"],
          "GpuInfo": get_gpu_info(offer),
          "SpotPrice": offer["min_bid"],
        } 
        
