from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
from passlib.context import CryptContext
import jwt
from enum import Enum


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Security
SECRET_KEY = os.environ.get('SECRET_KEY', 'energie-bien-etre-secret-key-2025')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Enums
class ProfessionType(str, Enum):
    infirmier = "infirmier"
    aide_soignant = "aide-soignant"
    medecin = "medecin"
    autre = "autre"

class QuestStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    missed = "missed"

class QuestType(str, Enum):
    respiration = "respiration"
    etirement = "etirement" 
    hydratation = "hydratation"
    meditation = "meditation"
    pause = "pause"

# Models
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    profession: ProfessionType
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    profession: ProfessionType
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    profession: ProfessionType
    created_at: datetime
    is_active: bool

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class Quest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    type: QuestType
    duration_minutes: int
    points: int = 10
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserQuest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    quest_id: str
    status: QuestStatus = QuestStatus.pending
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserProgress(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    date: datetime = Field(default_factory=lambda: datetime.utcnow().date())
    quests_completed: int = 0
    total_points: int = 0
    streak_days: int = 0

class DailyStats(BaseModel):
    day: str
    valeur: int

# Keep existing models for backward compatibility
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

# Authentication utilities
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"id": user_id})
    if user is None:
        raise credentials_exception
    return User(**user)

# Initialize default quests
async def initialize_default_quests():
    existing_quests = await db.quests.count_documents({})
    if existing_quests == 0:
        default_quests = [
            {
                "id": str(uuid.uuid4()),
                "title": "Pause respiration",
                "description": "Exercice de respiration profonde pour se détendre",
                "type": "respiration",
                "duration_minutes": 3,
                "points": 15,
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Étirement rapide",
                "description": "Quelques étirements pour détendre les muscles",
                "type": "etirement",
                "duration_minutes": 5,
                "points": 20,
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Hydratation",
                "description": "Boire un grand verre d'eau",
                "type": "hydratation",
                "duration_minutes": 1,
                "points": 10,
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Mini méditation",
                "description": "2 minutes de pleine conscience",
                "type": "meditation",
                "duration_minutes": 2,
                "points": 25,
                "created_at": datetime.utcnow()
            }
        ]
        await db.quests.insert_many(default_quests)
# Authentication routes
@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        profession=user_data.profession,
        hashed_password=hashed_password
    )
    
    await db.users.insert_one(user.dict())
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    user_response = UserResponse(**user.dict())
    return Token(access_token=access_token, token_type="bearer", user=user_response)

@api_router.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    user = await db.users.find_one({"email": user_credentials.email})
    if not user or not verify_password(user_credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["id"]}, expires_delta=access_token_expires
    )
    
    user_response = UserResponse(**user)
    return Token(access_token=access_token, token_type="bearer", user=user_response)

@api_router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return UserResponse(**current_user.dict())

# Quest routes
@api_router.get("/quests", response_model=List[Quest])
async def get_quests(current_user: User = Depends(get_current_user)):
    quests = await db.quests.find().to_list(1000)
    return [Quest(**quest) for quest in quests]

@api_router.get("/user-quests/today")
async def get_today_quests(current_user: User = Depends(get_current_user)):
    today = datetime.utcnow().date()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = datetime.combine(today, datetime.max.time())
    
    # Get user's quests for today
    user_quests = await db.user_quests.find({
        "user_id": current_user.id,
        "created_at": {"$gte": start_of_day, "$lte": end_of_day}
    }).to_list(1000)
    
    if not user_quests:
        # Create today's quests
        all_quests = await db.quests.find().to_list(1000)
        today_quests = []
        for quest in all_quests:
            user_quest = UserQuest(
                user_id=current_user.id,
                quest_id=quest["id"]
            )
            today_quests.append(user_quest.dict())
        
        if today_quests:
            await db.user_quests.insert_many(today_quests)
            user_quests = today_quests
    
    # Get quest details
    result = []
    for user_quest in user_quests:
        quest = await db.quests.find_one({"id": user_quest["quest_id"]})
        if quest:
            result.append({
                "id": user_quest["id"],
                "title": quest["title"],
                "description": quest["description"],
                "type": quest["type"],
                "duration_minutes": quest["duration_minutes"],
                "points": quest["points"],
                "status": user_quest["status"],
                "completed_at": user_quest.get("completed_at")
            })
    
    return result

@api_router.post("/user-quests/{quest_id}/complete")
async def complete_quest(quest_id: str, current_user: User = Depends(get_current_user)):
    # Find the user quest
    user_quest = await db.user_quests.find_one({
        "id": quest_id,
        "user_id": current_user.id
    })
    
    if not user_quest:
        raise HTTPException(status_code=404, detail="Quest not found")
    
    if user_quest["status"] == "completed":
        raise HTTPException(status_code=400, detail="Quest already completed")
    
    # Update quest status
    await db.user_quests.update_one(
        {"id": quest_id},
        {
            "$set": {
                "status": "completed",
                "completed_at": datetime.utcnow()
            }
        }
    )
    
    # Update user progress
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    progress = await db.user_progress.find_one({
        "user_id": current_user.id,
        "date": today
    })
    
    quest_info = await db.quests.find_one({"id": user_quest["quest_id"]})
    points = quest_info["points"] if quest_info else 10
    
    if not progress:
        new_progress = UserProgress(
            user_id=current_user.id,
            date=today,
            quests_completed=1,
            total_points=points,
            streak_days=1
        )
        await db.user_progress.insert_one(new_progress.dict())
    else:
        await db.user_progress.update_one(
            {"id": progress["id"]},
            {
                "$inc": {
                    "quests_completed": 1,
                    "total_points": points
                }
            }
        )
    
    return {"message": "Quest completed successfully", "points_earned": points}

# Dashboard routes
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    # Get last 7 days progress
    end_date = datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=999999)
    start_date = (end_date - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    progress_data = await db.user_progress.find({
        "user_id": current_user.id,
        "date": {"$gte": start_date, "$lte": end_date}
    }).to_list(1000)
    
    # Create weekly chart data
    days = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    weekly_data = []
    
    for i in range(7):
        current_date = start_date + timedelta(days=i)
        day_progress = next((p for p in progress_data if p["date"].date() == current_date.date()), None)
        weekly_data.append({
            "day": days[i],
            "valeur": day_progress["quests_completed"] if day_progress else 0
        })
    
    # Get today's stats
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_progress = await db.user_progress.find_one({
        "user_id": current_user.id,
        "date": today
    })
    
    total_quests_today = await db.user_quests.count_documents({
        "user_id": current_user.id,
        "created_at": {
            "$gte": datetime.combine(today, datetime.min.time()),
            "$lte": datetime.combine(today, datetime.max.time())
        }
    })
    
    completed_today = today_progress["quests_completed"] if today_progress else 0
    total_points = today_progress["total_points"] if today_progress else 0
    
    return {
        "weekly_data": weekly_data,
        "today_stats": {
            "quests_completed": completed_today,
            "total_quests": total_quests_today,
            "total_points": total_points,
            "completion_percentage": int((completed_today / total_quests_today * 100)) if total_quests_today > 0 else 0
        }
    }

@api_router.get("/")
async def root():
    return {"message": "Énergie & Bien-être™ API - Ready for healthcare workers!"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    await initialize_default_quests()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
