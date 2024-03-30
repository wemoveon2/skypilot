import csv
import json
import os

import requests
from sky.provision.vastai.vastai_utils import VastAIAPIError as client

ENDPOINT = 'https://console.vast.ai/api/v0/bundles'
OUTPUT_DIR = 'vastai'

def parse_offer(offer) -> dict:

    def get_gpu_info(offer) -> str:
        return json.dumps(
            {
                "Gpus": [
                    {
                        "Name": offer["gpu_name"],
                        "Manufacturer": offer.get("gpu_arch", "unk").upper(),
                        "Count": offer["num_gpus"],
                        "MemoryInfo": {"SizeInMiB": offer["gpu_ram"]},
                    }
                ],
                "TotalGpuMemoryInMiB": float(offer["gpu_ram"]) * int(offer["num_gpus"]),
            }
        )

    return {
        "InstanceType": f"{offer['cpu_name']}_{offer['gpu_name']}".replace(
            " ", "_"
        ).lower(),
        "AcceleratorName": offer["gpu_name"].replace(" ", ""),
        "AcceleratorCount": str(offer["num_gpus"]).strip(),
        "vCPUs": offer["cpu_cores"],
        "MemoryGiB": offer["cpu_ram"] // 1024,  # Convert MiB to GiB
        "Price": offer["dph_total"],
        "Region": offer["geolocation"],
        "AvailabilityZone": None,
        "GpuInfo": get_gpu_info(offer),
        "SpotPrice": offer["min_bid"],
    }

def create_catalog(output_dir: str) -> None:
    # FIXME(alanyu) - Vast AI has 
    response = requests.get(ENDPOINT, param={
      "verified": {"eq": True},
      "rentable": {"eq": True},
      "order": [["dphtotal","asc"],["total_flops","asc"]],
      "cuda_max_good": {"gte":12.1},
      "limit": 192
    })
    assert response.ok, response
    offers: list[dict] = response.json().get('offers', [{}])
    with open(os.path.join(output_dir, 'vms.csv'), mode='w',
              encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=',', quotechar='"')
        writer.writerow(
            [
                "InstanceType",
                "AcceleratorName",
                "AcceleratorCount",
                "vCPUs",
                "MemoryGiB",
                "Price",
                "Region",
                "AvailabilityZone",
                "GpuInfo",
                "SpotPrice",
            ]
        )
        for offer in offers:
            writer.writerow(
            list(parse_offer(offer).values())
          )

if __name__ == '__main__':
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    create_catalog(OUTPUT_DIR)
    print(f'vastai catalog saved to {OUTPUT_DIR}/vms.csv')
