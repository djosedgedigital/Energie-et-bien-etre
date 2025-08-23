from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
from passlib.context import CryptContext
import jwt
from enum import Enum
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'energie-bien-etre-secret-key-2025')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')
PRICE_EUR = 39.00  # Fixed price for energie-bien-etre-access

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the FastAPI app
app = FastAPI(title="Énergie & Bien-être API", description="API for healthcare workers wellness platform")
api_router = APIRouter(prefix="/api")

# Enums
class ProfessionType(str, Enum):
    infirmier = "infirmier"
    aide_soignant = "aide-soignant"
    medecin = "medecin"
    autre = "autre"

class UserRole(str, Enum):
    user = "user"
    admin = "admin"

class QuestStatus(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"

class QuestType(str, Enum):
    daily = "daily"
    weekly = "weekly"
    special = "special"

class SkillBranch(str, Enum):
    stress = "stress"
    sleep = "sleep"
    hydration = "hydration"
    strength = "strength"
    resilience = "resilience"

class LibraryCategory(str, Enum):
    recette = "recette"
    etirement = "etirement"
    playlist = "playlist"
    fiche5 = "fiche5"

class PaymentStatus(str, Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"
    expired = "expired"

# Core Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    profession: ProfessionType
    role: UserRole = UserRole.user
    hashed_password: str
    is_active: bool = True
    has_paid_access: bool = False
    settings: Dict[str, Any] = Field(default_factory=lambda: {
        "water_goal_ml": 2000,
        "sleep_goal_h": 8,
        "activity_goal_min": 30,
        "serenity_goal_min": 10,
        "notifications_daily": True,
        "theme_pref": "forest"
    })
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        extra = "allow"  # Allow extra fields like demo_expires_at

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    profession: ProfessionType
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    profession: ProfessionType
    role: UserRole
    has_paid_access: bool
    settings: Dict[str, Any]
    created_at: datetime
    is_active: bool

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Payment Models
class PaymentTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    email: Optional[str] = None
    session_id: str
    amount: float
    currency: str
    payment_status: PaymentStatus
    metadata: Dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CheckoutRequest(BaseModel):
    origin_url: str

# Habit and Progress Models
class HabitLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    date: datetime = Field(default_factory=lambda: datetime.utcnow().date())
    water_ml: int = 0
    sleep_h: float = 0.0
    nutrition_score_0_100: int = 0
    activity_min: int = 0
    serenity_min: int = 0
    mood_1_10: int = 5
    stress_0_10: int = 5
    notes: Optional[str] = None
    energy_score: int = 0

class Quest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    type: QuestType
    points_reward: int = 10
    badge_id: Optional[str] = None
    branch: Optional[SkillBranch] = None
    is_global: bool = True
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserQuest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    quest_id: str
    date_assigned: datetime = Field(default_factory=datetime.utcnow)
    status: QuestStatus = QuestStatus.todo
    completed_at: Optional[datetime] = None

class Badge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    label: str
    description: str
    icon: str

class Level(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    number: int
    xp_required: int

class UserXP(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    xp_total: int = 0
    level_number: int = 1

class Quote(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    author: Optional[str] = None

class LibraryItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: LibraryCategory
    title: str
    content_md: str
    media_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

class Theme(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    label: str
    accent: str
    bg: str
    audio_url: Optional[str] = None

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

# Demo Premium Models
class DemoAccess(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    demo_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

# Demo Premium utilities
def generate_demo_token():
    return str(uuid.uuid4())

async def is_demo_access_valid(demo_token: str) -> Optional[DemoAccess]:
    """Check if demo access token is valid and not expired"""
    demo_access = await db.demo_access.find_one({
        "demo_token": demo_token,
        "is_active": True,
        "expires_at": {"$gt": datetime.utcnow()}
    })
    return DemoAccess(**demo_access) if demo_access else None

async def get_user_with_demo_check(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user and check for demo access"""
    # First get the regular user
    user = await get_current_user(credentials)
    
    # If user already has paid access, return as is
    if user.has_paid_access:
        return user
    
    # Check if user has active demo access
    demo_access = await db.demo_access.find_one({
        "user_id": user.id,
        "is_active": True,
        "expires_at": {"$gt": datetime.utcnow()}
    })
    
    if demo_access:
        # Temporarily grant premium access for this request
        user.has_paid_access = True
        # Set demo expiration as a dynamic attribute (not part of Pydantic model)
        setattr(user, 'demo_expires_at', demo_access["expires_at"])
    
    return user
def calculate_energy_score(habit_log: HabitLog, user_settings: Dict[str, Any]) -> int:
    """Calculate energy score based on habit completion"""
    hydration_pct = min(100, (habit_log.water_ml / user_settings.get("water_goal_ml", 2000)) * 100)
    sleep_pct = min(100, (habit_log.sleep_h / user_settings.get("sleep_goal_h", 8)) * 100)
    nutrition_pct = habit_log.nutrition_score_0_100
    activity_pct = min(100, (habit_log.activity_min / user_settings.get("activity_goal_min", 30)) * 100)
    serenity_pct = min(100, (habit_log.serenity_min / user_settings.get("serenity_goal_min", 10)) * 100)
    
    energy = round(hydration_pct * 0.25 + sleep_pct * 0.30 + nutrition_pct * 0.20 + activity_pct * 0.15 + serenity_pct * 0.10)
    return min(100, energy)

# Initialize default data
async def initialize_default_data():
    # Initialize default quests
    existing_quests = await db.quests.count_documents({})
    if existing_quests == 0:
        default_quests = [
            {
                "id": str(uuid.uuid4()),
                "title": "Pause respiration profonde",
                "description": "3 minutes de respiration consciente pour réduire le stress",
                "type": "daily",
                "points_reward": 15,
                "branch": "stress",
                "is_global": True,
                "is_active": True,
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Étirement express",
                "description": "5 minutes d'étirements pour détendre les muscles",
                "type": "daily",
                "points_reward": 20,
                "branch": "strength",
                "is_global": True,
                "is_active": True,
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Hydratation consciente",
                "description": "Boire un grand verre d'eau en pleine conscience",
                "type": "daily",
                "points_reward": 10,
                "branch": "hydration",
                "is_global": True,
                "is_active": True,
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Moment de gratitude",
                "description": "2 minutes pour noter 3 choses positives de la journée",
                "type": "daily",
                "points_reward": 25,
                "branch": "resilience",
                "is_global": True,
                "is_active": True,
                "created_at": datetime.utcnow()
            }
        ]
        await db.quests.insert_many(default_quests)

    # Initialize quotes
    existing_quotes = await db.quotes.count_documents({})
    if existing_quotes == 0:
        default_quotes = [
            {"id": str(uuid.uuid4()), "text": "Prendre soin des autres commence par prendre soin de soi.", "author": "Anonyme"},
            {"id": str(uuid.uuid4()), "text": "Chaque petit geste de bien-être compte dans votre quotidien.", "author": "Discipline-90"},
            {"id": str(uuid.uuid4()), "text": "Votre énergie est précieuse, rechargez-la consciemment.", "author": "Discipline-90"},
            {"id": str(uuid.uuid4()), "text": "La respiration est le pont entre le corps et l'esprit.", "author": "Thich Nhat Hanh"},
            {"id": str(uuid.uuid4()), "text": "Il n'y a pas de honte à prendre une pause, c'est de la sagesse.", "author": "Anonyme"},
        ]
        await db.quotes.insert_many(default_quotes)

# Demo Premium routes
@api_router.post("/demo/activate")
async def activate_demo_premium(current_user: User = Depends(get_current_user)):
    """Activate 10-minute demo premium access for current user"""
    
    # Check if user already has paid access
    if current_user.has_paid_access:
        raise HTTPException(
            status_code=400,
            detail="User already has premium access"
        )
    
    # Check if user already has an active demo
    existing_demo = await db.demo_access.find_one({
        "user_id": current_user.id,
        "is_active": True,
        "expires_at": {"$gt": datetime.utcnow()}
    })
    
    if existing_demo:
        demo_access = DemoAccess(**existing_demo)
        remaining_minutes = int((demo_access.expires_at - datetime.utcnow()).total_seconds() / 60)
        return {
            "message": f"Demo already active! {remaining_minutes} minutes remaining",
            "demo_token": demo_access.demo_token,
            "expires_at": demo_access.expires_at,
            "demo_link": f"{os.environ.get('APP_BASE_URL', 'https://soignant-recharge.preview.emergentagent.com')}/dashboard?demo={demo_access.demo_token}"
        }
    
    # Create new demo access
    demo_token = generate_demo_token()
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    demo_access = DemoAccess(
        user_id=current_user.id,
        demo_token=demo_token,
        expires_at=expires_at
    )
    
    await db.demo_access.insert_one(demo_access.dict())
    
    return {
        "message": "Demo Premium activated for 10 minutes!",
        "demo_token": demo_token,
        "expires_at": expires_at,
        "demo_link": f"{os.environ.get('APP_BASE_URL', 'https://soignant-recharge.preview.emergentagent.com')}/dashboard?demo={demo_token}",
        "remaining_minutes": 10
    }

@api_router.get("/demo/status")
async def get_demo_status(current_user: User = Depends(get_current_user)):
    """Get current demo status for user"""
    
    if current_user.has_paid_access:
        return {
            "has_demo": False,
            "has_premium": True,
            "message": "User has full premium access"
        }
    
    # Check for active demo
    demo_access = await db.demo_access.find_one({
        "user_id": current_user.id,
        "is_active": True,
        "expires_at": {"$gt": datetime.utcnow()}
    })
    
    if demo_access:
        remaining_seconds = (demo_access["expires_at"] - datetime.utcnow()).total_seconds()
        remaining_minutes = max(0, int(remaining_seconds / 60))
        
        return {
            "has_demo": True,
            "has_premium": False,
            "demo_token": demo_access["demo_token"],
            "expires_at": demo_access["expires_at"],
            "remaining_minutes": remaining_minutes,
            "remaining_seconds": int(remaining_seconds)
        }
    
    return {
        "has_demo": False,
        "has_premium": False,
        "message": "No active demo or premium access"
    }

@api_router.post("/demo/validate/{demo_token}")
async def validate_demo_token(demo_token: str, current_user: User = Depends(get_current_user)):
    """Validate and activate demo token for user"""
    
    demo_access = await is_demo_access_valid(demo_token)
    if not demo_access:
        raise HTTPException(
            status_code=404,
            detail="Demo token is invalid or expired"
        )
    
    if demo_access.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Demo token belongs to different user"
        )
    
    remaining_seconds = (demo_access.expires_at - datetime.utcnow()).total_seconds()
    remaining_minutes = max(0, int(remaining_seconds / 60))
    
    return {
        "message": "Demo access validated!",
        "expires_at": demo_access.expires_at,
        "remaining_minutes": remaining_minutes,
        "remaining_seconds": int(remaining_seconds)
    }
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

# Payment routes
@api_router.post("/payments/checkout/session")
async def create_checkout_session(
    request: CheckoutRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user)
):
    try:
        # Initialize Stripe checkout
        host_url = str(http_request.base_url).rstrip('/')
        webhook_url = f"{host_url}/api/stripe/webhook"
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
        
        # Build URLs from frontend origin
        success_url = f"{request.origin_url}/dashboard?purchase=success&session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{request.origin_url}/pricing?canceled=1"
        
        # Create checkout session
        checkout_request = CheckoutSessionRequest(
            amount=PRICE_EUR,
            currency="eur",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "user_id": current_user.id,
                "user_email": current_user.email,
                "product": "energie-bien-etre-access"
            }
        )
        
        session = await stripe_checkout.create_checkout_session(checkout_request)
        
        # Create payment transaction record
        payment_transaction = PaymentTransaction(
            user_id=current_user.id,
            email=current_user.email,
            session_id=session.session_id,
            amount=PRICE_EUR,
            currency="eur",
            payment_status=PaymentStatus.pending,
            metadata=checkout_request.metadata
        )
        
        await db.payment_transactions.insert_one(payment_transaction.dict())
        
        return {"url": session.url, "session_id": session.session_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating checkout session: {str(e)}")

@api_router.get("/payments/checkout/status/{session_id}")
async def get_checkout_status(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    try:
        # Initialize Stripe checkout
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url="")
        
        # Get checkout status from Stripe
        checkout_status = await stripe_checkout.get_checkout_status(session_id)
        
        # Update payment transaction in database
        payment_transaction = await db.payment_transactions.find_one({"session_id": session_id})
        if payment_transaction:
            new_status = PaymentStatus.paid if checkout_status.payment_status == "paid" else PaymentStatus.pending
            if checkout_status.status == "expired":
                new_status = PaymentStatus.expired
            
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "payment_status": new_status,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # If payment is successful, grant access to user
            if new_status == PaymentStatus.paid and not current_user.has_paid_access:
                await db.users.update_one(
                    {"id": current_user.id},
                    {"$set": {"has_paid_access": True}}
                )
        
        return {
            "status": checkout_status.status,
            "payment_status": checkout_status.payment_status,
            "amount_total": checkout_status.amount_total,
            "currency": checkout_status.currency
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking payment status: {str(e)}")

@api_router.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    try:
        body = await request.body()
        signature = request.headers.get("Stripe-Signature")
        
        # Initialize Stripe checkout
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url="")
        
        # Handle webhook
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        # Process webhook events
        if webhook_response.event_type == "checkout.session.completed":
            session_id = webhook_response.session_id
            
            # Update payment transaction
            payment_transaction = await db.payment_transactions.find_one({"session_id": session_id})
            if payment_transaction:
                await db.payment_transactions.update_one(
                    {"session_id": session_id},
                    {
                        "$set": {
                            "payment_status": PaymentStatus.paid,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                
                # Grant access to user
                if payment_transaction.get("user_id"):
                    await db.users.update_one(
                        {"id": payment_transaction["user_id"]},
                        {"$set": {"has_paid_access": True}}
                    )
        
        return {"status": "success"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")

# Quest routes with demo access support
@api_router.get("/quests", response_model=List[Quest])
async def get_quests(current_user: User = Depends(get_user_with_demo_check)):
    quests = await db.quests.find({"is_active": True}).to_list(1000)
    
    # Freemium users get access to limited quests (unless demo is active)
    if not current_user.has_paid_access:
        quests = quests[:2]
    
    return [Quest(**quest) for quest in quests]

@api_router.get("/user-quests/today")
async def get_today_quests(current_user: User = Depends(get_user_with_demo_check)):
    today = datetime.utcnow().date()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = datetime.combine(today, datetime.max.time())
    
    # Get user's quests for today
    user_quests = await db.user_quests.find({
        "user_id": current_user.id,
        "date_assigned": {"$gte": start_of_day, "$lte": end_of_day}
    }).to_list(1000)
    
    if not user_quests:
        # Create today's quests
        all_quests = await db.quests.find({"is_active": True, "type": "daily"}).to_list(1000)
        
        # Freemium limitation: only 2 quests for free users (unless demo is active)
        if not current_user.has_paid_access:
            all_quests = all_quests[:2]
        
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
                "points_reward": quest["points_reward"],
                "status": user_quest["status"],
                "completed_at": user_quest.get("completed_at"),
                "is_premium": not current_user.has_paid_access
            })
    
    return result

@api_router.post("/user-quests/{quest_id}/complete")
async def complete_quest(quest_id: str, current_user: User = Depends(get_user_with_demo_check)):
    # Find the user quest
    user_quest = await db.user_quests.find_one({
        "id": quest_id,
        "user_id": current_user.id
    })
    
    if not user_quest:
        raise HTTPException(status_code=404, detail="Quest not found")
    
    if user_quest["status"] == "done":
        raise HTTPException(status_code=400, detail="Quest already completed")
    
    # Freemium users have daily limits (unless demo is active)
    if not current_user.has_paid_access:
        today = datetime.utcnow().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        
        completed_today = await db.user_quests.count_documents({
            "user_id": current_user.id,
            "status": "done",
            "completed_at": {"$gte": start_of_day, "$lte": end_of_day}
        })
        
        if completed_today >= 2:
            raise HTTPException(
                status_code=403, 
                detail="Daily limit reached. Upgrade to premium for unlimited access!"
            )
    
    # Update quest status
    await db.user_quests.update_one(
        {"id": quest_id},
        {
            "$set": {
                "status": "done",
                "completed_at": datetime.utcnow()
            }
        }
    )
    
    # Update user XP
    quest_info = await db.quests.find_one({"id": user_quest["quest_id"]})
    points = quest_info["points_reward"] if quest_info else 10
    
    user_xp = await db.user_xp.find_one({"user_id": current_user.id})
    if not user_xp:
        new_xp = UserXP(user_id=current_user.id, xp_total=points)
        await db.user_xp.insert_one(new_xp.dict())
    else:
        await db.user_xp.update_one(
            {"user_id": current_user.id},
            {"$inc": {"xp_total": points}}
        )
    
    return {"message": "Quest completed successfully", "points_earned": points}

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_user_with_demo_check)):
    # Basic stats available for all users
    weekly_data = [
        {"day": "Lun", "valeur": 3},
        {"day": "Mar", "valeur": 4},
        {"day": "Mer", "valeur": 2},
        {"day": "Jeu", "valeur": 5},
        {"day": "Ven", "valeur": 4},
        {"day": "Sam", "valeur": 6},
        {"day": "Dim", "valeur": 3},
    ]
    
    # Get today's quest completion
    today = datetime.utcnow().date()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = datetime.combine(today, datetime.max.time())
    
    total_quests_today = await db.user_quests.count_documents({
        "user_id": current_user.id,
        "date_assigned": {"$gte": start_of_day, "$lte": end_of_day}
    })
    
    completed_today = await db.user_quests.count_documents({
        "user_id": current_user.id,
        "date_assigned": {"$gte": start_of_day, "$lte": end_of_day},
        "status": "done"
    })
    
    # Get user XP
    user_xp = await db.user_xp.find_one({"user_id": current_user.id})
    total_points = user_xp["xp_total"] if user_xp else 0
    
    # Add demo/freemium limitations info
    stats = {
        "weekly_data": weekly_data,
        "today_stats": {
            "quests_completed": completed_today,
            "total_quests": total_quests_today,
            "total_points": total_points,
            "completion_percentage": int((completed_today / total_quests_today * 100)) if total_quests_today > 0 else 0
        },
        "is_premium": current_user.has_paid_access,
        "is_demo": hasattr(current_user, 'demo_expires_at'),
        "demo_expires_at": getattr(current_user, 'demo_expires_at', None),
        "freemium_limits": {
            "daily_quests_limit": 2 if not current_user.has_paid_access else None,
            "daily_completions_limit": 2 if not current_user.has_paid_access else None,
            "has_full_stats": current_user.has_paid_access,
            "has_advanced_features": current_user.has_paid_access
        }
    }
    
    return stats

@api_router.get("/")
async def root():
    return {"message": "Énergie & Bien-être™ API - Ready for healthcare workers!"}

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
    await initialize_default_data()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()