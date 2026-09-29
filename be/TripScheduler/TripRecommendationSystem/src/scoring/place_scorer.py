"""
장소 점수 계산 시스템
평점과 해시태그 유사도를 활용한 점수 계산
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import math
from collections import Counter

# 임베딩 유사도 계산 추가
try:
    from .embedding_similarity import EmbeddingSimilarityCalculator
    EMBEDDING_AVAILABLE = True
except ImportError:
    EMBEDDING_AVAILABLE = False

@dataclass
class ScoringConfig:
    """점수 계산 설정"""
    rating_weight: float = 0.6        # 평점 가중치 (60%)
    hashtag_weight: float = 0.4       # 해시태그 유사도 가중치 (40%)
    max_rating: float = 5.0           # 최대 평점 기준
    min_rating: float = 0.0           # 최소 평점 기준

class HashtagSimilarity:
    """해시태그 유사도 계산"""
    
    @staticmethod
    def jaccard_similarity(set1: set, set2: set) -> float:
        """
        자카드 유사도 계산 (교집합 / 합집합)
        
        Args:
            set1: 첫 번째 해시태그 집합
            set2: 두 번째 해시태그 집합
            
        Returns:
            float: 0~1 사이의 유사도 점수
        """
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
            
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    @staticmethod
    def cosine_similarity(list1: List[str], list2: List[str]) -> float:
        """
        코사인 유사도 계산 (해시태그 빈도 기반)
        
        Args:
            list1: 첫 번째 해시태그 리스트
            list2: 두 번째 해시태그 리스트
            
        Returns:
            float: 0~1 사이의 유사도 점수
        """
        if not list1 and not list2:
            return 1.0
        if not list1 or not list2:
            return 0.0
        
        # 해시태그 빈도 계산
        counter1 = Counter(list1)
        counter2 = Counter(list2)
        
        # 모든 해시태그 집합
        all_hashtags = set(counter1.keys()).union(set(counter2.keys()))
        
        # 벡터 생성
        vec1 = [counter1.get(tag, 0) for tag in all_hashtags]
        vec2 = [counter2.get(tag, 0) for tag in all_hashtags]
        
        # 코사인 유사도 계산
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)

class PlaceScorer:
    """장소 점수 계산기"""

    def __init__(self, config: Optional[ScoringConfig] = None):
        self.config = config or ScoringConfig()
        self.similarity_calc = HashtagSimilarity()

        # 임베딩 유사도 계산기 초기화
        if EMBEDDING_AVAILABLE:
            try:
                self.embedding_calc = EmbeddingSimilarityCalculator()
            except Exception as e:
                print(f"[WARNING] 임베딩 계산기 초기화 실패: {e}")
                self.embedding_calc = None
        else:
            self.embedding_calc = None
    
    def calculate_rating_score(self, rating: Optional[float]) -> float:
        """
        평점 점수 계산 (0~1 정규화)
        
        Args:
            rating: 장소 평점
            
        Returns:
            float: 정규화된 평점 점수 (0~1)
        """
        if rating is None:
            return 0.5  # 평점이 없으면 중간값
        
        # 평점을 0~1 사이로 정규화
        normalized = (rating - self.config.min_rating) / (self.config.max_rating - self.config.min_rating)
        
        # 0~1 범위로 클램핑
        return max(0.0, min(1.0, normalized))
    
    def calculate_hashtag_similarity_score(
        self, 
        place_hashtags: List[str], 
        reference_hashtags: List[str],
        method: str = 'embedding'
    ) -> Tuple[float, Dict[str, Any]]:
        """
        해시태그 유사도 점수 계산
        
        Args:
            place_hashtags: 장소의 해시태그들
            reference_hashtags: 참조할 해시태그들 (사용자 선호도 등)
            method: 유사도 계산 방법 ('jaccard', 'cosine', 'embedding')
            
        Returns:
            Tuple[float, Dict]: (유사도 점수 (0~1), 상세 정보)
        """
        if not place_hashtags:
            return 0.0, {'method': method, 'reason': 'no_place_hashtags'}
        
        if not reference_hashtags:
            return 0.5, {'method': method, 'reason': 'no_reference_hashtags'}
        
        # 임베딩 방법 우선 시도
        if method == 'embedding':
            if self.embedding_calc is not None:
                try:
                    similarity, details = self.embedding_calc.calculate_hashtag_similarity_with_embeddings(
                        place_hashtags, reference_hashtags
                    )
                    return similarity, details
                except Exception as e:
                    print(f"[WARNING] 임베딩 유사도 계산 실패, 기본 방법 사용: {e}")
            # 임베딩 실패시 또는 embedding_calc가 None인 경우 자카드 유사도로 fallback
            similarity = self.similarity_calc.jaccard_similarity(
                set(place_hashtags), set(reference_hashtags)
            )
            return similarity, {'method': 'jaccard_fallback', 'reason': 'embedding_unavailable'}
        
        # 기존 텍스트 기반 방법들
        if method == 'jaccard':
            similarity = self.similarity_calc.jaccard_similarity(
                set(place_hashtags), set(reference_hashtags)
            )
            return similarity, {'method': 'jaccard'}
        elif method == 'cosine':
            similarity = self.similarity_calc.cosine_similarity(
                place_hashtags, reference_hashtags
            )
            return similarity, {'method': 'cosine'}
        else:
            raise ValueError(f"Unknown similarity method: {method}")
    
    def calculate_total_score(
        self,
        rating: Optional[float],
        place_hashtags: List[str],
        reference_hashtags: Optional[List[str]] = None,
        similarity_method: str = 'embedding',
        place_coords: Optional[Tuple[float, float]] = None,
        reference_coords: Optional[Tuple[float, float]] = None
    ) -> Dict[str, Any]:
        """
        전체 점수 계산

        Args:
            rating: 장소 평점
            place_hashtags: 장소의 해시태그들
            reference_hashtags: 참조 해시태그들
            similarity_method: 유사도 계산 방법
            place_coords: 장소 좌표 (사용 안 함)
            reference_coords: 참조 지점 좌표 (사용 안 함)

        Returns:
            Dict: 점수 상세 정보
        """
        # 평점 점수 계산
        rating_score = self.calculate_rating_score(rating)

        # 해시태그 유사도 점수 계산
        if reference_hashtags:
            hashtag_score, similarity_details = self.calculate_hashtag_similarity_score(
                place_hashtags, reference_hashtags, similarity_method
            )
        else:
            # 참조 해시태그가 없으면 해시태그 수로 점수 계산
            hashtag_score = min(1.0, len(place_hashtags) / 10.0)  # 10개 이상이면 만점
            similarity_details = {'method': 'count_based', 'hashtag_count': len(place_hashtags)}

        # 가중치 적용하여 최종 점수 계산
        total_score = (
            rating_score * self.config.rating_weight +
            hashtag_score * self.config.hashtag_weight
        )

        return {
            'total_score': total_score,
            'rating_score': rating_score,
            'hashtag_score': hashtag_score,
            'rating_weight': self.config.rating_weight,
            'hashtag_weight': self.config.hashtag_weight,
            'original_rating': rating,
            'hashtag_count': len(place_hashtags),
            'similarity_details': similarity_details
        }
    
    def score_places_batch(
        self,
        places: List[Any],  # BasePlace 객체들
        reference_hashtags: Optional[List[str]] = None,
        similarity_method: str = 'embedding',
        reference_coords: Optional[Tuple[float, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        여러 장소의 점수를 일괄 계산

        Args:
            places: 점수를 계산할 장소들
            reference_hashtags: 참조 해시태그들
            similarity_method: 유사도 계산 방법
            reference_coords: 참조 좌표 (y_cord, x_cord) = (lat, lon)

        Returns:
            List[Dict]: 각 장소의 점수 정보
        """
        results = []

        for place in places:
            # 장소 좌표 추출
            place_coords = None
            if hasattr(place, 'y_cord') and hasattr(place, 'x_cord'):
                place_coords = (place.y_cord, place.x_cord)

            score_info = self.calculate_total_score(
                rating=getattr(place, 'score', None),  # DB의 score 필드 사용
                place_hashtags=getattr(place, 'hashtags', []),
                reference_hashtags=reference_hashtags,
                similarity_method=similarity_method,
                place_coords=place_coords,
                reference_coords=reference_coords
            )

            # 장소 정보와 점수 정보 결합
            result = {
                'place': place,
                'place_id': place.get_id(),
                'place_name': place.name,
                'place_type': place.get_place_type(),
                'score_info': score_info
            }

            results.append(result)

        # 총 점수 기준으로 정렬
        results.sort(key=lambda x: x['score_info']['total_score'], reverse=True)

        return results

# 편의를 위한 전역 스코어러 인스턴스
default_scorer = PlaceScorer()

def score_place(
    rating: Optional[float],
    hashtags: List[str],
    reference_hashtags: Optional[List[str]] = None,
    config: Optional[ScoringConfig] = None
) -> Dict[str, float]:
    """
    단일 장소 점수 계산 - 편의 함수
    
    Args:
        rating: 장소 평점
        hashtags: 장소 해시태그들
        reference_hashtags: 참조 해시태그들
        config: 점수 계산 설정
        
    Returns:
        Dict: 점수 정보
    """
    scorer = PlaceScorer(config) if config else default_scorer
    return scorer.calculate_total_score(rating, hashtags, reference_hashtags)