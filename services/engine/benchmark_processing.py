"""
Performance Benchmark Script
10,000개 후보 처리 성능 측정 (SLA 60초 준수 확인)
"""
import asyncio
import time
import random
import uuid
from typing import List, Dict, Any
import structlog
from app.services.scoring import ScoringService
from app.services.pareto import ParetoService

logger = structlog.get_logger()

class MockDB:
    def table(self, name):
        return self
    def select(self, *args):
        return self
    def eq(self, *args):
        return self
    def limit(self, *args):
        return self
    def in_(self, *args):
        return self
    async def execute(self):
        return type('obj', (object,), {'data': [{"weights": {"bio": 0.25, "safety": 0.25, "eng": 0.25, "clin": 0.25}, "thresholds": {"hard_reject": 20.0}}]})

async def run_benchmark():
    db = MockDB()
    scoring_service = ScoringService(db)
    pareto_service = ParetoService(db)
    
    # 1. 10,000개 후보 생성
    print("Generating 10,000 mock candidates...")
    candidates = []
    for i in range(10000):
        candidates.append({
            "id": str(uuid.uuid4()),
            "bio_score": random.uniform(0, 100),
            "safety_score": random.uniform(0, 100),
            "eng_score": random.uniform(0, 100),
            "clin_score": random.uniform(0, 100)
        })
        
    # 2. 스코어링 벤치마크
    print("Starting Scoring Benchmark...")
    start_time = time.time()
    scores = await scoring_service.calculate_scores("bench_run", candidates)
    scoring_duration = time.time() - start_time
    print(f"Scoring completed in {scoring_duration:.2f} seconds")
    
    # 3. 파레토 최적화 벤치마크
    print("Starting Pareto Benchmark...")
    # ScoreResult 객체를 dict로 변환
    score_dicts = []
    for s in scores:
        if not s.is_rejected:
            d = vars(s).copy()
            # ParetoService는 dimensions 리스트에 있는 키를 찾음
            # ScoreResult 필드명은 bio_fit, safety_fit 등임
            # ParetoService는 'id' 키를 기대하므로 candidate_id를 id로 복사
            d['id'] = d['candidate_id']
            score_dicts.append(d)
            
    dimensions = ["bio_fit", "safety_fit", "eng_fit", "clin_fit"]
    
    start_time = time.time()
    fronts = pareto_service.calculate_pareto_fronts(score_dicts, dimensions)
    pareto_duration = time.time() - start_time
    print(f"Pareto completed in {pareto_duration:.2f} seconds")
    
    total_duration = scoring_duration + pareto_duration
    print(f"Total Processing Time: {total_duration:.2f} seconds")
    
    if total_duration < 60:
        print("SUCCESS: SLA (60s) met.")
    else:
        print("FAILURE: SLA (60s) exceeded.")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
