import requests
import os
from typing import List, Dict, Optional
import time
from ..config import settings

class KakaoMapAPI:
    """카카오 Map API를 사용한 장소 검색 서비스"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'KAKAO_API_KEY', os.getenv('KAKAO_API_KEY'))
        self.base_url = "https://dapi.kakao.com/v2/local"
        
        self._cache = {}
        self._cache_duration = 3600
        self._max_size = 10
        
        if not self.api_key:
            raise ValueError("카카오 API 키가 설정되지 않았습니다. KAKAO_API_KEY 환경변수를 설정해주세요.")
    
    def _get_cache_key(self, endpoint: str, params: Dict) -> str:
        """캐시 키 생성"""
        return f"{endpoint}:{hash(str(sorted(params.items())))}"
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """캐시 유효성 검사"""
        return time.time() - cache_entry['timestamp'] < self._cache_duration
    
    def _make_request(self, endpoint: str, params: Dict) -> Dict:
        """카카오 API 요청을 보내는 공통 메서드"""
        cache_key = self._get_cache_key(endpoint, params)
        if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key]):
            return self._cache[cache_key]['data']
        
        headers = {
            "Authorization": f"KakaoAK {self.api_key}",
            "Content-Type": "application/json;charset=UTF-8"
        }
        
        url = f"{self.base_url}/{endpoint}"
        
        debug_mode = os.getenv("DEBUG_KAKAO_API", "false").lower() == "true"
        
        if debug_mode:
            print(f"🌐 카카오 API 요청: {url}")
            print(f"🔧 파라미터: {params}")
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            if debug_mode and response.status_code != 200:
                print(f"❌ 카카오 API 오류 {response.status_code}: {response.text}")
            
            response.raise_for_status()
            result = response.json()
            
            self._cache[cache_key] = {
                'data': result,
                'timestamp': time.time()
            }
            
            return result
        except requests.exceptions.RequestException as e:
            if debug_mode:
                print(f"카카오 API 요청 실패: {e}")
            return {"documents": [], "meta": {"total_count": 0}}
    
    def search_places_by_keyword(self, 
                                keyword: str, 
                                region: Optional[str] = None,
                                category_group_code: Optional[str] = None,
                                size: int = 15,
                                page: int = 1) -> List[Dict]:
        """키워드로 장소 검색"""
        params = {
            "query": f"{region} {keyword}" if region else keyword,
            "size": min(size, self._max_size),
            "page": page
        }
        
        if category_group_code:
            params["category_group_code"] = category_group_code
        
        result = self._make_request("search/keyword.json", params)
        
        places = []
        for doc in result.get("documents", []):
            place = {
                "id": doc.get("id"),
                "name": doc.get("place_name"),
                "category": doc.get("category_name"),
                "address": doc.get("address_name"),
                "road_address": doc.get("road_address_name"),
                "phone": doc.get("phone"),
                "place_url": doc.get("place_url"),
                "x": float(doc.get("x", 0)),
                "y": float(doc.get("y", 0)),
                "distance": doc.get("distance")
            }
            places.append(place)
        
        return places
    
    def search_restaurants(self, region: str, cuisine_type: Optional[str] = None) -> List[Dict]:
        """음식점 검색"""
        keyword = f"맛집 {cuisine_type}" if cuisine_type else "맛집"
        return self.search_places_by_keyword(
            keyword=keyword,
            region=region,
            category_group_code="FD6",
            size=self._max_size
        )
    
    def search_tourist_attractions(self, region: str, attraction_type: Optional[str] = None) -> List[Dict]:
        """관광지 검색"""
        keyword = f"관광지 {attraction_type}" if attraction_type else "관광지"
        return self.search_places_by_keyword(
            keyword=keyword,
            region=region,
            category_group_code="AT4",
            size=self._max_size
        )
    
    def search_accommodations(self, region: str, accommodation_type: Optional[str] = None) -> List[Dict]:
        """숙박시설 검색"""
        keyword = accommodation_type if accommodation_type else "호텔"
        return self.search_places_by_keyword(
            keyword=keyword,
            region=region,
            category_group_code="AD5",
            size=self._max_size
        )
    
    def search_cultural_facilities(self, region: str) -> List[Dict]:
        """문화시설 검색"""
        return self.search_places_by_keyword(
            keyword="문화시설",
            region=region,
            category_group_code="CT1",
            size=self._max_size
        )
    
    def search_shopping(self, region: str) -> List[Dict]:
        """쇼핑 관련 장소 검색"""
        return self.search_places_by_keyword(
            keyword="쇼핑",
            region=region,
            size=self._max_size
        )
    
    def get_places_by_preferences(self, region: str, preferences: List[str]) -> Dict[str, List[Dict]]:
        """사용자 선호도에 따른 장소 검색"""
        results = {}
        
        preference_mapping = {
            "맛집": self.search_restaurants,
            "관광": self.search_tourist_attractions,
            "쇼핑": self.search_shopping,
            "문화체험": self.search_cultural_facilities,
            "자연/아웃도어": lambda r: self.search_places_by_keyword("자연 공원", r),
            "휴식": lambda r: self.search_places_by_keyword("카페 공원", r)
        }
        
        for preference in preferences:
            if preference in preference_mapping:
                try:
                    places = preference_mapping[preference](region)
                    results[preference] = places
                except Exception as e:
                    print(f"{preference} 검색 중 오류 발생: {e}")
                    results[preference] = []
            else:
                places = self.search_places_by_keyword(preference, region)
                results[preference] = places
        
        return results
    
    def search_route_places(self, start_region: str, end_region: str, preferences: List[str]) -> Dict:
        """경로상의 장소들 검색"""
        start_places = self.get_places_by_preferences(start_region, preferences)
        end_places = self.get_places_by_preferences(end_region, preferences)
        
        return {
            "start_region": start_region,
            "end_region": end_region,
            "start_places": start_places,
            "end_places": end_places
        }


kakao_map_api = None

def get_kakao_map_api() -> KakaoMapAPI:
    """카카오 Map API 인스턴스 반환"""
    global kakao_map_api
    if kakao_map_api is None:
        try:
            kakao_map_api = KakaoMapAPI()
        except ValueError as e:
            print(f"카카오 Map API 초기화 실패: {e}")
            return None
    return kakao_map_api 