"""
Airbyte Connection Manager
Configures and manages Airbyte data source connections
"""
import requests
import json
from typing import Optional
from ..utils.config import config
from ..utils.logger import logger

class AirbyteClient:
    def __init__(self):
        self.host = config.airbyte_host
        self.port = config.airbyte_port
        self.base_url = f"http://{self.host}:{self.port}"
        self.workspace_id = None

    def _get_headers(self, api_key: str = None) -> dict:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    def get_workspaces(self, api_key: str = None) -> list:
        """Get list of Airbyte workspaces"""
        url = f"{self.base_url}/api/v1/workspaces/list"
        try:
            response = requests.post(url, json={}, headers=self._get_headers(api_key), timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data.get("workspaces", [])
            logger.error(f"Failed to get workspaces: {response.status_code}")
            return []
        except Exception as e:
            logger.error(f"Error getting workspaces: {e}")
            return []

    def create_connection(
        self,
        workspace_id: str,
        source_id: str,
        destination_id: str,
        name: str,
        api_key: str = None
    ) -> Optional[str]:
        """Create a connection between source and destination"""
        url = f"{self.base_url}/api/v1/connections/create"
        data = {
            "name": name,
            "workspaceId": workspace_id,
            "sourceId": source_id,
            "destinationId": destination_id,
            "syncCatalog": {"streams": []},
            "schedule": {"units": 3600, "timeUnit": "hours"},
            "status": "active"
        }
        try:
            response = requests.post(url, json=data, headers=self._get_headers(api_key), timeout=30)
            if response.status_code == 200:
                conn = response.json()
                logger.info(f"Created connection: {name}")
                return conn.get("connectionId")
            logger.error(f"Failed to create connection: {response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Error creating connection: {e}")
            return None


AIRBYTE_SOURCE_CONFIGS = {
    "coingecko": {
        "name": "CoinGecko",
        "source_type": "coingecko",
        "config": {
            "api_key": "",  # Free tier doesn't require key
            "coin_ids": "bitcoin,ethereum",
            "currencies": "usd",
            "rate_limit": 10
        }
    },
    "coinglass": {
        "name": "Coinglass",
        "source_type": "api",
        "config": {
            "api_key": "",  # Requires API key
            "endpoint": "https://api.coinglass.com/api/v1"
        }
    },
    "alternative_me": {
        "name": "Alternative.me Fear & Greed",
        "source_type": "api",
        "config": {
            "api_key": "",  # Free API
            "endpoint": "https://api.alternative.me/fng/"
        }
    },
    "fred": {
        "name": "FRED Economic Data",
        "source_type": "api",
        "config": {
            "api_key": "",  # Requires free API key from https://fred.stlouisfed.org/
            "series_ids": "CPIAUCSL,DXY,DFEDTARU"
        }
    },
    "news": {
        "name": "Google News",
        "source_type": "api",
        "config": {
            "api_key": "",  # Requires API key
            "keywords": "Bitcoin,ETH,crypto,regulation,SEC"
        }
    }
}


def generate_airbyte_config_file():
    """Generate a JSON config file for Airbyte UI import"""
    config = {
        "version": "0.50.0",
        "sources": []
    }
    
    for source_id, source_info in AIRBYTE_SOURCE_CONFIGS.items():
        config["sources"].append({
            "sourceDefinitionId": source_info["source_type"],
            "name": source_info["name"],
            "configuration": source_info["config"]
        })
    
    output_file = "/home/ubuntu/crash_radar/airbyte_sources.json"
    with open(output_file, "w") as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Generated Airbyte config: {output_file}")
    return output_file


def check_airbyte_status() -> dict:
    """Check Airbyte API status"""
    client = AirbyteClient()
    status = {
        "api_reachable": False,
        "workspaces": 0,
        "message": ""
    }
    
    try:
        response = requests.get(f"{client.base_url}/api/v1/health", timeout=5)
        if response.status_code == 200:
            status["api_reachable"] = True
            status["message"] = "Airbyte API is healthy"
        else:
            status["message"] = f"Airbyte returned status {response.status_code}"
    except requests.exceptions.ConnectionError:
        status["message"] = "Cannot connect to Airbyte API"
    except Exception as e:
        status["message"] = str(e)
    
    return status


if __name__ == "__main__":
    print("Airbyte Connection Manager")
    print("=" * 40)
    
    status = check_airbyte_status()
    print(f"Status: {status['message']}")
    
    config_file = generate_airbyte_config_file()
    print(f"Config saved to: {config_file}")
