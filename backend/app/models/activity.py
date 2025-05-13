from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Activity(Base):
    __tablename__ = "activities"

    # ─────────────────── 기본 정보 ───────────────────
    id = Column(Integer, primary_key=True, index=True)  # 내부 DB용 고유 ID
    activity_id = Column(Integer, index=True)  # 가민 활동 고유 ID
    user_id = Column(Integer, index=True)  # 사용자 ID
    activity_name = Column(String)  # 활동 이름 (예: 서울하프마라톤 10k)
    start_time_local = Column(DateTime)  # 활동 시작 시간 (로컬 기준)
    start_time_gmt = Column(DateTime)  # 활동 시작 시간 (GMT 기준)
    end_time_gmt = Column(DateTime)  # 활동 종료 시간 (GMT 기준)
    activity_type = Column(JSON)  # 활동 종류 정보 (예: running, parentType 등 포함)
    event_type = Column(JSON)  # 이벤트 유형 (ex: uncategorized 등)

    # ─────────────────── 거리 및 시간 정보 ───────────────────
    distance = Column(Float)  # 총 이동 거리 (단위: 미터)
    duration = Column(Float)  # 총 활동 시간 (단위: 초)
    elapsed_duration = Column(Float)  # 정지 시간 포함 전체 소요 시간
    moving_duration = Column(Float)  # 실제 움직인 시간

    # ─────────────────── 고도 및 속도 정보 ───────────────────
    elevation_gain = Column(Float)  # 총 상승 고도 (미터)
    elevation_loss = Column(Float)  # 총 하강 고도 (미터)
    min_elevation = Column(Float)  # 최소 고도
    max_elevation = Column(Float)  # 최대 고도
    elevation_corrected = Column(Boolean, default=False)  # 고도 보정 여부

    average_speed = Column(Float)  # 평균 속도 (단위: m/s)
    max_speed = Column(Float)  # 최대 속도 (단위: m/s)

    # ─────────────────── 위치 정보 ───────────────────
    start_latitude = Column(Float)  # 시작 지점 위도
    start_longitude = Column(Float)  # 시작 지점 경도
    end_latitude = Column(Float)  # 종료 지점 위도
    end_longitude = Column(Float)  # 종료 지점 경도

    # ─────────────────── 생리적 정보 (심박, 파워 등) ───────────────────
    average_hr = Column(Float)  # 평균 심박수 (bpm)
    max_hr = Column(Float)  # 최대 심박수
    hr_time_in_zones = Column(JSON)  # 심박수 영역별 시간 (zone1~zone5)

    avg_power = Column(Float)  # 평균 파워 (Watt)
    max_power = Column(Float)  # 최대 파워
    power_time_in_zones = Column(JSON)  # 파워 영역별 시간

    aerobic_training_effect = Column(Float)  # 유산소 트레이닝 효과 (0.0~5.0)
    anaerobic_training_effect = Column(Float)  # 무산소 트레이닝 효과 (0.0~5.0)
    training_effect_label = Column(String)  # 효과 구분 라벨 (ex: VO2MAX)

    vo2max_value = Column(Float)  # VO2max 추정치 (ml/kg/min)

    # ─────────────────── 러닝 자세 및 리듬 정보 ───────────────────
    average_cadence = Column(Float)  # 평균 케이던스 (단위: steps/min)
    max_cadence = Column(Float)  # 최대 케이던스
    avg_vertical_oscillation = Column(Float)  # 상하 진동 (cm)
    avg_ground_contact_time = Column(Float)  # 지면 접촉 시간 (ms)
    avg_stride_length = Column(Float)  # 평균 보폭 (cm)

    # ─────────────────── 운동 강도 및 에너지 ───────────────────
    calories = Column(Float)  # 소모 칼로리 (kcal)
    water_estimated = Column(Float)  # 추정 수분 손실량 (ml)
    activity_training_load = Column(Float)  # Training Load (훈련 부하)
    moderate_intensity_minutes = Column(Integer)  # 중강도 운동 시간 (분)
    vigorous_intensity_minutes = Column(Integer)  # 고강도 운동 시간 (분)

    # ─────────────────── 기타 정보 ───────────────────
    steps = Column(Integer)  # 총 걸음 수
    time_zone_id = Column(Integer)  # 타임존 ID
    sport_type_id = Column(Integer)  # 스포츠 유형 ID
    device_id = Column(Integer)  # 기록에 사용된 디바이스 ID
    manufacturer = Column(String)  # 디바이스 제조사 (예: GARMIN)
    lap_count = Column(Integer)  # 랩 수
    privacy = Column(JSON)  # 공개/비공개 설정 정보
    favorite = Column(Boolean, default=False)  # 즐겨찾기 여부
    manual_activity = Column(Boolean, default=False)  # 수동으로 추가된 활동인지 여부

    # 관계 설정
    splits = relationship("ActivitySplit", back_populates="activity")
    activity_feedbacks = relationship("ActivityFeedback", back_populates="activity")
    activity_comments = relationship("ActivityComment", back_populates="activity")

class ActivitySplit(Base):
    __tablename__ = "activity_splits"

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id"))
    lap_index = Column(Integer)
    start_time_gmt = Column(DateTime)
    distance = Column(Float)  # 미터 단위
    duration = Column(Float)  # 초 단위
    moving_duration = Column(Float)  # 초 단위
    average_speed = Column(Float)  # m/s
    max_speed = Column(Float)  # m/s
    average_hr = Column(Float)  # bpm
    max_hr = Column(Float)  # bpm
    average_run_cadence = Column(Float)  # spm
    max_run_cadence = Column(Float)  # spm
    average_power = Column(Float)  # watts
    max_power = Column(Float)  # watts
    ground_contact_time = Column(Float)  # ms
    stride_length = Column(Float)  # cm
    vertical_oscillation = Column(Float)  # cm
    vertical_ratio = Column(Float)  # %
    calories = Column(Float)
    elevation_gain = Column(Float)  # m
    elevation_loss = Column(Float)  # m
    max_elevation = Column(Float)  # m
    min_elevation = Column(Float)  # m
    start_latitude = Column(Float)
    start_longitude = Column(Float)
    end_latitude = Column(Float)
    end_longitude = Column(Float)

    # 관계 설정
    activity = relationship("Activity", back_populates="splits")

class ActivityFeedback(Base):
    __tablename__ = "activity_feedbacks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    activity_id = Column(Integer, ForeignKey("activities.activity_id"))
    created_at = Column(DateTime)
    feedback_data = Column(String)
    
    user = relationship("User", back_populates="activity_feedbacks") 
    activity = relationship("Activity", back_populates="activity_feedbacks") 

class ActivityComment(Base):
    __tablename__ = "activity_comments"

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id"))
    comment = Column(String)
    created_at = Column(DateTime)

    activity = relationship("Activity", back_populates="activity_comments")
