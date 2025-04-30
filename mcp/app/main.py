from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List
import json

app = FastAPI()

class CoachingResponse(BaseModel):
    training_plan: List[Dict]
    rest_days: List[str]
    target_pace: Dict
    recommendations: List[str]

@app.post("/analyze")
async def analyze_user_data(request: Dict):
    try:
        user_id = request.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")
        
        # 여기에 실제 AI 모델 호출 및 분석 로직이 들어갑니다
        # 예시 응답:
        response = CoachingResponse(
            training_plan=[
                {"day": "Monday", "type": "Easy Run", "distance": 5, "pace": "6:00"},
                {"day": "Wednesday", "type": "Interval", "distance": 8, "pace": "5:30"},
                {"day": "Saturday", "type": "Long Run", "distance": 15, "pace": "6:30"}
            ],
            rest_days=["Tuesday", "Thursday", "Friday", "Sunday"],
            target_pace={"easy": "6:00", "tempo": "5:30", "race": "5:00"},
            recommendations=[
                "수면 시간을 7-8시간으로 유지하세요",
                "주 2회 이상 근력 운동을 추가하세요",
                "충분한 수분 섭취를 유지하세요"
            ]
        )
        
        return response.dict()
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 