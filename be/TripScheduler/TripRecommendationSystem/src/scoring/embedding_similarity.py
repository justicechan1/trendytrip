"""
임베딩 기반 해시태그 유사도 계산 시스템
"""

import numpy as np
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

# 상대 import
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.simple_connection import SimpleDBConnection

@dataclass
class HashtagEmbedding:
    """해시태그 임베딩 데이터"""
    hashtag_id: int
    hashtag: str
    embedding: np.ndarray
    
    def __post_init__(self):
        if isinstance(self.embedding, list):
            self.embedding = np.array(self.embedding, dtype=np.float32)

class EmbeddingSimilarityCalculator:
    """임베딩 기반 유사도 계산기"""
    
    def __init__(self, db: Optional[SimpleDBConnection] = None):
        self.db = db or SimpleDBConnection()
        self._hashtag_embeddings_cache = {}  # 캐시
    
    def normalize_vectors(self, vectors: np.ndarray, axis: int = -1) -> np.ndarray:
        """
        벡터 정규화 (L2 정규화)
        
        Args:
            vectors: 정규화할 벡터들
            axis: 정규화할 축
            
        Returns:
            np.ndarray: 정규화된 벡터들
        """
        # 작은 값 추가하여 0으로 나누는 것 방지
        norm = np.linalg.norm(vectors, axis=axis, keepdims=True) + 1e-8
        return vectors / norm
    
    def cosine_similarity_embedding(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        정규화된 벡터 간 코사인 유사도 계산
        
        Args:
            vec1: 첫 번째 벡터 (정규화된)
            vec2: 두 번째 벡터 (정규화된)
            
        Returns:
            float: 코사인 유사도 (0~1)
        """
        # 이미 정규화된 벡터라면 내적이 코사인 유사도
        similarity = float(np.dot(vec1, vec2))
        
        # 0~1 범위로 클램핑 (부동소수점 오차 방지)
        return max(0.0, min(1.0, similarity))
    
    def get_hashtag_embeddings(self, hashtag_texts: List[str]) -> Dict[str, HashtagEmbedding]:
        """
        해시태그 텍스트들에 대한 임베딩 조회
        
        Args:
            hashtag_texts: 조회할 해시태그 텍스트들
            
        Returns:
            Dict[str, HashtagEmbedding]: 해시태그 텍스트 -> 임베딩 데이터
        """
        result = {}
        uncached_hashtags = []
        
        # 캐시에서 먼저 확인
        for hashtag in hashtag_texts:
            if hashtag in self._hashtag_embeddings_cache:
                result[hashtag] = self._hashtag_embeddings_cache[hashtag]
            else:
                uncached_hashtags.append(hashtag)
        
        if not uncached_hashtags:
            return result
        
        # 데이터베이스에서 조회
        placeholders = ', '.join(['%s'] * len(uncached_hashtags))
        query = f"""
        SELECT hashtag_id, hashtag, embeddings 
        FROM hashtag 
        WHERE hashtag IN ({placeholders})
        AND embeddings IS NOT NULL
        """
        
        rows = self.db.execute_query(query, tuple(uncached_hashtags))
        
        for row in rows:
            hashtag_text = row['hashtag']
            
            try:
                # JSON 형태의 임베딩을 파싱
                if isinstance(row['embeddings'], str):
                    embedding_data = json.loads(row['embeddings'])
                else:
                    embedding_data = row['embeddings']
                
                # HashtagEmbedding 객체 생성
                hashtag_embedding = HashtagEmbedding(
                    hashtag_id=row['hashtag_id'],
                    hashtag=hashtag_text,
                    embedding=embedding_data
                )
                
                # 캐시에 저장
                self._hashtag_embeddings_cache[hashtag_text] = hashtag_embedding
                result[hashtag_text] = hashtag_embedding
                
            except Exception as e:
                print(f"[WARNING] 해시태그 '{hashtag_text}' 임베딩 파싱 실패: {e}")
                continue
        
        return result
    
    def calculate_hashtag_similarity_with_embeddings(
        self,
        place_hashtags: List[str],
        reference_hashtags: List[str]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        임베딩 기반 해시태그 유사도 계산
        
        Args:
            place_hashtags: 장소의 해시태그들
            reference_hashtags: 참조 해시태그들
            
        Returns:
            Tuple[float, Dict]: (유사도 점수, 상세 정보)
        """
        if not place_hashtags or not reference_hashtags:
            return 0.0, {'method': 'embedding', 'reason': 'empty_hashtags'}
        
        # 해시태그 임베딩 조회
        all_hashtags = list(set(place_hashtags + reference_hashtags))
        hashtag_embeddings = self.get_hashtag_embeddings(all_hashtags)
        
        # 임베딩이 있는 해시태그들만 필터링
        place_embeddings = []
        reference_embeddings = []
        
        for hashtag in place_hashtags:
            if hashtag in hashtag_embeddings:
                place_embeddings.append(hashtag_embeddings[hashtag].embedding)
        
        for hashtag in reference_hashtags:
            if hashtag in hashtag_embeddings:
                reference_embeddings.append(hashtag_embeddings[hashtag].embedding)
        
        if not place_embeddings or not reference_embeddings:
            return 0.0, {
                'method': 'embedding',
                'reason': 'no_embeddings_found',
                'place_embeddings_count': len(place_embeddings),
                'reference_embeddings_count': len(reference_embeddings)
            }
        
        # 임베딩을 numpy 배열로 변환
        place_vectors = np.array(place_embeddings)
        reference_vectors = np.array(reference_embeddings)
        
        # 벡터 정규화
        place_vectors_norm = self.normalize_vectors(place_vectors)
        reference_vectors_norm = self.normalize_vectors(reference_vectors)
        
        # 각 장소 해시태그와 참조 해시태그 간의 유사도 계산
        similarities = []
        
        for place_vec in place_vectors_norm:
            max_similarity = 0.0
            for ref_vec in reference_vectors_norm:
                similarity = self.cosine_similarity_embedding(place_vec, ref_vec)
                max_similarity = max(max_similarity, similarity)
            similarities.append(max_similarity)
        
        # 평균 유사도 계산
        avg_similarity = float(np.mean(similarities)) if similarities else 0.0
        
        details = {
            'method': 'embedding',
            'place_hashtags_with_embeddings': len(place_embeddings),
            'reference_hashtags_with_embeddings': len(reference_embeddings),
            'total_place_hashtags': len(place_hashtags),
            'total_reference_hashtags': len(reference_hashtags),
            'individual_similarities': similarities,
            'max_similarity': float(np.max(similarities)) if similarities else 0.0,
            'min_similarity': float(np.min(similarities)) if similarities else 0.0,
            'avg_similarity': avg_similarity
        }
        
        return avg_similarity, details
    
    def search_similar_hashtags(
        self,
        query_hashtag: str,
        top_k: int = 10,
        min_similarity: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        특정 해시태그와 유사한 해시태그들 검색
        
        Args:
            query_hashtag: 검색할 해시태그
            top_k: 반환할 최대 개수
            min_similarity: 최소 유사도 임계값
            
        Returns:
            List[Dict]: 유사한 해시태그들과 유사도 정보
        """
        # 쿼리 해시태그의 임베딩 조회
        query_embeddings = self.get_hashtag_embeddings([query_hashtag])
        
        if query_hashtag not in query_embeddings:
            return []
        
        query_vector = query_embeddings[query_hashtag].embedding
        query_vector_norm = self.normalize_vectors(query_vector.reshape(1, -1))[0]
        
        # 모든 해시태그 임베딩 조회 (성능상 제한 필요시 수정)
        all_hashtags_query = """
        SELECT hashtag_id, hashtag, embeddings 
        FROM hashtag 
        WHERE embeddings IS NOT NULL 
        AND hashtag != %s
        LIMIT 1000
        """
        
        rows = self.db.execute_query(all_hashtags_query, (query_hashtag,))
        
        similarities = []
        
        for row in rows:
            try:
                if isinstance(row['embeddings'], str):
                    embedding_data = json.loads(row['embeddings'])
                else:
                    embedding_data = row['embeddings']
                
                target_vector = np.array(embedding_data, dtype=np.float32)
                target_vector_norm = self.normalize_vectors(target_vector.reshape(1, -1))[0]
                
                similarity = self.cosine_similarity_embedding(query_vector_norm, target_vector_norm)
                
                if similarity >= min_similarity:
                    similarities.append({
                        'hashtag_id': row['hashtag_id'],
                        'hashtag': row['hashtag'],
                        'similarity': similarity
                    })
                    
            except Exception as e:
                print(f"[WARNING] 해시태그 '{row['hashtag']}' 처리 실패: {e}")
                continue
        
        # 유사도 순으로 정렬하여 상위 k개 반환
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:top_k]

# 편의를 위한 전역 계산기 인스턴스
default_embedding_calculator = EmbeddingSimilarityCalculator()

def calculate_embedding_similarity(
    place_hashtags: List[str],
    reference_hashtags: List[str]
) -> Tuple[float, Dict[str, Any]]:
    """
    임베딩 기반 해시태그 유사도 계산 - 편의 함수
    
    Args:
        place_hashtags: 장소의 해시태그들
        reference_hashtags: 참조 해시태그들
        
    Returns:
        Tuple[float, Dict]: (유사도 점수, 상세 정보)
    """
    return default_embedding_calculator.calculate_hashtag_similarity_with_embeddings(
        place_hashtags, reference_hashtags
    )

def find_similar_hashtags(
    query_hashtag: str,
    top_k: int = 10
) -> List[Dict[str, Any]]:
    """
    유사한 해시태그 검색 - 편의 함수
    
    Args:
        query_hashtag: 검색할 해시태그
        top_k: 반환할 최대 개수
        
    Returns:
        List[Dict]: 유사한 해시태그들
    """
    return default_embedding_calculator.search_similar_hashtags(query_hashtag, top_k)