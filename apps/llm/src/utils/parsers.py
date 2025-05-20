import json
import re
from typing import Dict

def parse_json_response(response: str) -> Dict:
    """LLM 응답에서 JSON 부분을 추출하고 파싱"""
    try:
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            return json.loads(json_str)
        
        return json.loads(response)
    except json.JSONDecodeError:
        return {}
