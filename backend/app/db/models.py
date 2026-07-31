import uuid
from sqlalchemy import Column, String, Integer, Boolean, Float, ForeignKey, DateTime, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .database import Base
import enum

class PlayerRole(str, enum.Enum):
    BATTER = "Batter"
    BOWLER = "Bowler"
    ALL_ROUNDER = "All-Rounder"
    WICKETKEEPER = "Wicket-Keeper"

class PitchTendency(str, enum.Enum):
    SPIN_FRIENDLY = "SPIN_FRIENDLY"
    PACE_FRIENDLY = "PACE_FRIENDLY"
    BALANCED = "BALANCED"
    BATTING_FRIENDLY = "BATTING_FRIENDLY"

class RoomStatus(str, enum.Enum):
    LOBBY = "LOBBY"
    RETENTION = "RETENTION"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"

class AcquisitionType(str, enum.Enum):
    AUCTION = "AUCTION"
    RETENTION = "RETENTION"
    RTM = "RTM"

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Room(Base):
    __tablename__ = "rooms"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_code = Column(String(6), unique=True, index=True, nullable=False)
    host_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    status = Column(Enum(RoomStatus), default=RoomStatus.LOBBY)
    config_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=False)
    franchise_code = Column(String, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    purse_remaining_lakh = Column(Integer, nullable=False)
    overseas_slots_used = Column(Integer, default=0)
    is_ai = Column(Boolean, default=True)

class Player(Base):
    __tablename__ = "players"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True, nullable=False)
    nationality = Column(String, nullable=False)
    role = Column(Enum(PlayerRole), nullable=False)
    is_capped = Column(Boolean, default=False)
    base_price_lakh = Column(Integer, nullable=False)
    set_name = Column(String, nullable=True)
    is_overseas = Column(Boolean, default=False)
    age = Column(Integer, nullable=True)
    is_fallback_price = Column(Boolean, default=False)

class Squad2024Entry(Base):
    __tablename__ = "squad_2024_entries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    franchise_code = Column(String, index=True, nullable=False)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False)
    role = Column(Enum(PlayerRole), nullable=False)
    was_capped = Column(Boolean, default=False)

class PlayerStats(Base):
    __tablename__ = "player_stats"
    
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), primary_key=True)
    matches = Column(Integer, default=0)
    innings = Column(Integer, default=0)
    batting_avg = Column(Float, nullable=True)
    strike_rate = Column(Float, nullable=True)
    powerplay_sr = Column(Float, nullable=True)
    death_overs_sr = Column(Float, nullable=True)
    boundary_pct = Column(Float, nullable=True)
    bowling_avg = Column(Float, nullable=True)
    economy = Column(Float, nullable=True)
    wickets = Column(Integer, nullable=True)
    bowling_sr = Column(Float, nullable=True)
    death_overs_economy = Column(Float, nullable=True)
    dot_ball_pct = Column(Float, nullable=True)
    match_winning_innings = Column(Integer, default=0)
    base_impact_score = Column(Float, nullable=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now())

class Venue(Base):
    __tablename__ = "venues"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    franchise_code = Column(String, index=True, nullable=False)
    ground_name = Column(String, nullable=False)
    avg_first_innings_score = Column(Float, nullable=True)
    chase_success_pct = Column(Float, nullable=True)
    pitch_tendency = Column(Enum(PitchTendency), nullable=True)
    boundary_size_category = Column(String, nullable=True)
    source_url = Column(String, nullable=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now())

class RosterEntry(Base):
    __tablename__ = "roster_entries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False)
    acquisition_type = Column(Enum(AcquisitionType), nullable=False)
    price_lakh = Column(Integer, nullable=False)
    round_number = Column(Integer, nullable=True)

class RetentionSlab(Base):
    __tablename__ = "retention_slabs"
    
    slot_no = Column(Integer, primary_key=True)
    capped_cost_lakh = Column(Integer, nullable=False)
    uncapped_cost_lakh = Column(Integer, nullable=False)

class TeamRetention(Base):
    __tablename__ = "team_retentions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False)
    retention_cost_lakh = Column(Integer, nullable=False)
    slot_no = Column(Integer, nullable=True)
    is_uncapped = Column(Boolean, default=False)
    confirmed_at = Column(DateTime(timezone=True), server_default=func.now())

class RTMCard(Base):
    __tablename__ = "rtm_cards"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    cards_remaining = Column(Integer, default=0)

