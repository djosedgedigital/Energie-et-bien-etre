from fastapi import FastAPI, APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager
import os
import logging
import uuid
import json
import asyncio
import hashlib
import requests
import random
from pathlib import Path
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest

# Import des nouveaux modèles et services
from models import User, HabitLog, Quest, UserQuest, Badge, UserBadge, Quote, PaymentTransaction, Profession, ProgressionMetier, UserProgression
from profession_service import ProfessionService

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize services
profession_service = ProfessionService(db)

# Initialize Stripe
stripe_api_key = os.environ.get('STRIPE_SECRET_KEY')  # Updated to use STRIPE_SECRET_KEY instead of STRIPE_API_KEY
stripe_public_key = os.environ.get('STRIPE_PUBLIC_KEY')

# Email configuration
brevo_api_key = os.environ.get('BREVO_API_KEY')
email_from = os.environ.get('EMAIL_FROM', 'app@discipline90.com')
email_reply_to = os.environ.get('EMAIL_REPLY_TO', 'support@discipline90.com')

# App configuration
app_name = os.environ.get('APP_NAME', 'Énergie & Bien-être pour soignants™')
app_base_url = os.environ.get('APP_BASE_URL', 'https://app.discipline90.com')
landing_url = os.environ.get('LANDING_URL', 'https://energie-bien-etre.discipline90.com')
price_eur_cents = int(os.environ.get('PRICE_EUR', '3900'))  # Price in cents
price_name = os.environ.get('PRICE_NAME', 'energie-bien-etre-access')

# CRON configuration
cron_enabled = os.environ.get('CRON_DAILY_RECAP_ENABLED', 'true').lower() == 'true'
cron_hour = int(os.environ.get('CRON_DAILY_RECAP_HOUR_UTC', '5'))
cron_minute = int(os.environ.get('CRON_DAILY_RECAP_MINUTE', '0'))

# Template IDs (optional)
template_welcome_id = os.environ.get('BREVO_TEMPLATE_WELCOME_ID')
template_purchase_id = os.environ.get('BREVO_TEMPLATE_PURCHASE_ID')
template_daily_recap_id = os.environ.get('BREVO_TEMPLATE_DAILY_RECAP_ID')

# Initialize scheduler
scheduler = AsyncIOScheduler()

# Pydantic Models
class UserCreate(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    profession_slug: Optional[str] = None

class HabitUpdate(BaseModel):
    water_ml: Optional[float] = None
    sleep_h: Optional[float] = None
    nutrition_score_0_100: Optional[int] = None
    activity_min: Optional[float] = None
    serenity_min: Optional[float] = None
    mood_1_10: Optional[int] = None
    stress_0_10: Optional[int] = None
    notes: Optional[str] = None

class CheckoutRequest(BaseModel):
    origin_url: str

class UserUpdateProfession(BaseModel):
    profession_slug: str

# Email service
class BrevoEmailService:
    def __init__(self):
        self.api_key = brevo_api_key
        self.base_url = "https://api.brevo.com/v3"
        self.default_sender = {"name": "Énergie & Bien-être", "email": email_from}
        self.reply_to = email_reply_to
    
    def _get_headers(self):
        return {
            "accept": "application/json", 
            "api-key": self.api_key,
            "content-type": "application/json"
        }
    
    async def send_email(self, to_email: str, subject: str, html_content: str = None, template_id: int = None, template_params: Dict = None):
        if not self.api_key:
            logger.warning("Brevo API key not configured, skipping email")
            return True
            
        url = f"{self.base_url}/smtp/email"
        
        payload = {
            "sender": self.default_sender,
            "to": [{"email": to_email}],
            "subject": subject,
            "replyTo": {"email": self.reply_to}
        }
        
        if template_id:
            payload["templateId"] = template_id
            if template_params:
                payload["params"] = template_params
        elif html_content:
            payload["htmlContent"] = html_content
        
        try:
            response = requests.post(url, headers=self._get_headers(), data=json.dumps(payload), timeout=30)
            if response.status_code == 201:
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"Failed to send email: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {str(e)}")
            return False
    
    async def send_welcome_email(self, user_email: str, user_name: str):
        """Send welcome email after payment confirmation"""
        if template_welcome_id:
            return await self.send_email(
                to_email=user_email,
                subject="Bienvenue dans Énergie & Bien-être !",
                template_id=int(template_welcome_id),
                template_params={
                    "user_name": user_name or "Soignant",
                    "dashboard_url": f"{app_base_url}/app/dashboard",
                    "app_name": app_name
                }
            )
        else:
            html_content = f"""
            <div style="max-width: 600px; margin: 0 auto; font-family: 'Inter', sans-serif; color: #24313A;">
                <div style="background: linear-gradient(135deg, #0E3A53 0%, #3FB28C 100%); padding: 40px 20px; text-align: center; border-radius: 12px 12px 0 0;">
                    <h1 style="color: white; margin: 0; font-size: 28px; font-weight: 600;">Bienvenue dans {app_name}</h1>
                </div>
                
                <div style="background: white; padding: 40px 30px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                    <h2 style="color: #0E3A53; margin-bottom: 20px;">Félicitations {user_name or 'Soignant'} !</h2>
                    
                    <p style="color: #64748B; line-height: 1.6; margin-bottom: 25px;">
                        Votre paiement a été confirmé avec succès. Vous avez maintenant accès à toutes les fonctionnalités d'Énergie & Bien-être pour soignants™.
                    </p>
                    
                    <div style="background: #f8fafc; padding: 25px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #3FB28C;">
                        <h3 style="color: #0E3A53; margin: 0 0 15px 0; font-size: 18px;">🎯 Prochaines étapes :</h3>
                        <ul style="color: #64748B; margin: 0; padding-left: 20px;">
                            <li>Définissez vos objectifs personnalisés</li>
                            <li>Découvrez votre première quête quotidienne</li>
                            <li>Commencez à tracker vos habitudes bien-être</li>
                        </ul>
                    </div>
                    
                    <div style="text-align: center; margin: 35px 0;">
                        <a href="{app_base_url}/app/dashboard" style="background: #3FB28C; color: white; padding: 14px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; display: inline-block; transition: all 0.2s;">
                            🚀 Accéder au tableau de bord
                        </a>
                    </div>
                    
                    <p style="color: #64748B; line-height: 1.6; font-size: 14px; margin-top: 30px;">
                        Prenez soin de vous,<br>
                        <strong style="color: #0E3A53;">L'équipe Discipline 90™</strong>
                    </p>
                </div>
            </div>
            """
            
            return await self.send_email(
                to_email=user_email,
                subject="Bienvenue dans Énergie & Bien-être !",
                html_content=html_content
            )

email_service = BrevoEmailService()

# Helper functions
def prepare_for_mongo(data):
    """Prepare data for MongoDB insertion"""
    if isinstance(data, dict):
        # Remove None values and prepare data
        return {k: v for k, v in data.items() if v is not None}
    return data

def serialize_mongo_doc(doc):
    """Convert MongoDB document to JSON-serializable format"""
    if not doc:
        return None
    if isinstance(doc, list):
        return [serialize_mongo_doc(item) for item in doc]
    if isinstance(doc, dict):
        # Remove MongoDB _id field and convert other ObjectIds
        serialized = {}
        for key, value in doc.items():
            if key == '_id':
                continue  # Skip MongoDB _id field
            elif hasattr(value, 'isoformat'):  # datetime objects
                serialized[key] = value.isoformat()
            elif isinstance(value, dict):
                serialized[key] = serialize_mongo_doc(value)
            elif isinstance(value, list):
                serialized[key] = [serialize_mongo_doc(item) for item in value]
            else:
                serialized[key] = value
        return serialized
    return doc

def calculate_energy_percentage(habit_log: HabitLog, user_settings: Dict):
    """Calculate daily energy percentage based on habit completion"""
    goals = {
        'water_goal_ml': user_settings.get('water_goal_ml', 2000),
        'sleep_goal_h': user_settings.get('sleep_goal_h', 7.5),
        'activity_goal_min': user_settings.get('activity_goal_min', 30),
        'serenity_goal_min': user_settings.get('serenity_goal_min', 10)
    }
    
    hydration_pct = min(100, (habit_log.water_ml / goals['water_goal_ml']) * 100)
    sleep_pct = min(100, (habit_log.sleep_h / goals['sleep_goal_h']) * 100)
    activity_pct = min(100, (habit_log.activity_min / goals['activity_goal_min']) * 100)
    serenity_pct = min(100, (habit_log.serenity_min / goals['serenity_goal_min']) * 100)
    nutrition_pct = habit_log.nutrition_score_0_100
    
    energy = min(100, round(
        hydration_pct * 0.25 + 
        sleep_pct * 0.30 + 
        nutrition_pct * 0.20 + 
        activity_pct * 0.15 + 
        serenity_pct * 0.10
    ))
    
    return energy

async def award_points_and_check_badges(user_id: str, points: int):
    """Award points to user and check for badge achievements"""
    await db.users.update_one(
        {"id": user_id},
        {"$inc": {"xp_total": points}}
    )
    
    # Update level based on XP (every 150 XP = new level)
    user = await db.users.find_one({"id": user_id})
    if user:
        new_level = (user["xp_total"] // 150) + 1
        if new_level > user.get("level_number", 1):
            await db.users.update_one(
                {"id": user_id},
                {"$set": {"level_number": new_level}}
            )
            logger.info(f"User {user_id} reached level {new_level}")

async def get_daily_quest_for_user(user_id: str) -> Optional[Dict]:
    """Get today's daily quest for user"""
    try:
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Check if user already has today's quest
        user_quest = await db.user_quests.find_one({
            "user_id": user_id,
            "date_assigned": {"$gte": today}
        })
        
        if user_quest:
            quest = await db.quests.find_one({"id": user_quest["quest_id"]})
            if quest:
                return {
                    **serialize_mongo_doc(quest), 
                    "user_quest": serialize_mongo_doc(user_quest)
                }
        
        # Assign new daily quest
        daily_quests = await db.quests.find({"type": "daily", "is_active": True}).to_list(100)
        if daily_quests:
            selected_quest = random.choice(daily_quests)
            
            user_quest_data = UserQuest(
                user_id=user_id,
                quest_id=selected_quest["id"],
                date_assigned=datetime.now(timezone.utc)
            )
            
            await db.user_quests.insert_one(user_quest_data.dict())
            return {
                **serialize_mongo_doc(selected_quest), 
                "user_quest": serialize_mongo_doc(user_quest_data.dict())
            }
        
        return None
    except Exception as e:
        logger.error(f"Error getting daily quest for user {user_id}: {str(e)}")
        return None

# Scheduler functions
async def send_daily_recap_emails():
    """Send daily recap emails to all eligible users"""
    logger.info("Starting daily recap email batch")
    
    users = await db.users.find({
        "has_paid": True,
        "settings.notifications_daily": {"$ne": False}
    }).to_list(1000)
    
    for user in users:
        try:
            # Get yesterday's habit log
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            habit_log = await db.habit_logs.find_one({
                "user_id": user["id"],
                "date": {
                    "$gte": yesterday.replace(hour=0, minute=0, second=0, microsecond=0),
                    "$lt": yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
                }
            })
            
            if habit_log:
                energy = calculate_energy_percentage(HabitLog(**habit_log), user.get("settings", {}))
                
                # Get random quote
                quotes = await db.quotes.find({}).to_list(50)
                quote = random.choice(quotes) if quotes else {"text": "Chaque jour est une nouvelle opportunité", "author": "Équipe Discipline 90"}
                
                html_content = f"""
                <h2>Votre récap quotidien - {yesterday.strftime('%d %B %Y')}</h2>
                <p>Bonjour {user.get('name', 'Soignant')},</p>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3>🔋 Énergie du jour : {energy}%</h3>
                    <p>Votre niveau d'énergie d'hier était de {energy}% - {"Excellent travail !" if energy >= 70 else "Continue tes efforts !"}</p>
                </div>
                
                <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h4>💭 Citation du jour</h4>
                    <p><em>"{quote['text']}"</em></p>
                    <p>- {quote.get('author', 'Anonyme')}</p>
                </div>
                
                <p>Rendez-vous sur votre tableau de bord pour voir votre progression et votre quête du jour !</p>
                <p>Bien à vous,<br>L'équipe Énergie & Bien-être</p>
                """
                
                await email_service.send_email(
                    to_email=user["email"],
                    subject=f"Votre récap quotidien - {yesterday.strftime('%d %B')}",
                    html_content=html_content
                )
        except Exception as e:
            logger.error(f"Error sending daily recap to {user['email']}: {str(e)}")

# Application lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start scheduler
    if cron_enabled:
        scheduler.add_job(
            func=send_daily_recap_emails,
            trigger=CronTrigger(hour=cron_hour, minute=cron_minute, timezone=os.environ.get('TIMEZONE', 'UTC')),
            id='daily_recap_emails',
            max_instances=1,
            replace_existing=True
        )
        scheduler.start()
        logger.info(f"Daily recap scheduler started (UTC {cron_hour:02d}:{cron_minute:02d})")
    else:
        logger.info("Daily recap scheduler disabled")
    
    # Seed initial data
    await seed_initial_data()
    
    # Seed professions data
    await profession_service.seed_professions()
    
    yield
    
    # Shutdown
    scheduler.shutdown()
    client.close()
    logger.info("Application shutdown complete")

# Create FastAPI app with lifespan
app = FastAPI(
    title="Énergie & Bien-être pour soignants™",
    description="La récupération ludique pour soignants",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Router
api_router = APIRouter(prefix="/api")

# Seed data
async def seed_initial_data():
    """Seed database with initial data"""
    try:
        # Check if data already exists
        existing_quests = await db.quests.count_documents({})
        if existing_quests > 0:
            return
        
        # Seed quotes
        quotes_data = [
            {"text": "Prendre soin de soi n'est pas un luxe, c'est une nécessité", "author": "Équipe Discipline 90"},
            {"text": "Chaque petit geste compte vers votre bien-être", "author": ""},
            {"text": "Vous méritez de vous sentir énergique et épanoui(e)", "author": ""},
            {"text": "L'hydratation est la base d'une énergie durable", "author": ""},
            {"text": "Un sommeil réparateur transforme vos journées", "author": ""},
            {"text": "Quelques minutes de sérénité valent des heures de stress", "author": ""},
            {"text": "Votre corps est votre temple, prenez-en soin", "author": ""},
            {"text": "Chaque jour est une nouvelle opportunité de briller", "author": ""},
            {"text": "La constance dans les petites habitudes crée de grands changements", "author": ""},
            {"text": "Vous êtes plus fort(e) que vous ne le pensez", "author": ""},
            {"text": "Prendre une pause n'est pas abandonner, c'est se ressourcer", "author": ""},
            {"text": "Votre bien-être rayonne sur ceux qui vous entourent", "author": ""}
        ]
        
        for quote_data in quotes_data:
            quote = Quote(**quote_data)
            await db.quotes.insert_one(quote.dict())
        
        # Seed quests
        quests_data = [
            {
                "title": "1L avant midi",
                "description": "Boire 1 litre d'eau avant 12h pour bien commencer la journée",
                "type": "daily",
                "points_reward": 10,
                "branch": "hydration"
            },
            {
                "title": "Respiration 5 min",
                "description": "Prendre 5 minutes pour une respiration consciente",
                "type": "daily", 
                "points_reward": 10,
                "branch": "stress"
            },
            {
                "title": "Marche 20 min",
                "description": "Faire une marche de 20 minutes, même dans les couloirs",
                "type": "daily",
                "points_reward": 10,
                "branch": "strength"
            },
            {
                "title": "Noter 3 gratitudes",
                "description": "Écrire 3 choses pour lesquelles vous êtes reconnaissant(e)",
                "type": "daily",
                "points_reward": 15,
                "branch": "resilience"
            },
            {
                "title": "3 étirements express",
                "description": "Faire 3 étirements rapides pendant la semaine",
                "type": "weekly",
                "points_reward": 30,
                "branch": "strength"
            },
            {
                "title": "5 jours de petit-déj protéiné",
                "description": "Prendre un petit-déjeuner riche en protéines 5 jours cette semaine",
                "type": "weekly",
                "points_reward": 30,
                "branch": "nutrition"
            },
            {
                "title": "Semaine sans soda sucré",
                "description": "Éviter les boissons sucrées pendant une semaine complète",
                "type": "special",
                "points_reward": 50,
                "branch": "hydration"
            },
            {
                "title": "Sommeil régulier 7j",
                "description": "Maintenir des horaires de coucher réguliers (±30 min) pendant 7 jours",
                "type": "special",
                "points_reward": 50,
                "branch": "sleep"
            }
        ]
        
        for quest_data in quests_data:
            quest = Quest(**quest_data)
            await db.quests.insert_one(quest.dict())
        
        # Seed badges
        badges_data = [
            {
                "code": "hydra_pro",
                "label": "Hydra-Pro",
                "description": "7 jours consécutifs avec objectif eau atteint",
                "icon": "💧"
            },
            {
                "code": "sommeil_or",
                "label": "Sommeil d'or", 
                "description": "5 nuits de 8h ou plus",
                "icon": "🌙"
            },
            {
                "code": "zen_line",
                "label": "Zen Line",
                "description": "10 sessions de respiration consciente",
                "icon": "🧘"
            },
            {
                "code": "routine_plus",
                "label": "Routine+",
                "description": "14 jours d'habitudes à 70% ou plus",
                "icon": "⭐"
            },
            {
                "code": "force_douce",
                "label": "Force douce",
                "description": "8 séances d'activité physique",
                "icon": "💪"
            }
        ]
        
        for badge_data in badges_data:
            badge = Badge(**badge_data)
            await db.badges.insert_one(badge.dict())
        
        logger.info("Initial data seeded successfully")
        
    except Exception as e:
        logger.error(f"Error seeding initial data: {str(e)}")

# Payment endpoints
@api_router.post("/checkout/session")
async def create_checkout_session(checkout_request: CheckoutRequest):
    """Create Stripe checkout session"""
    try:
        if not stripe_api_key:
            raise HTTPException(status_code=500, detail="Payment not configured")
        
        # Initialize Stripe checkout
        host_url = checkout_request.origin_url
        webhook_url = f"{host_url}/api/webhook/stripe"
        stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
        
        # Fixed price for the service (39€ = 3900 cents)
        amount = price_eur_cents / 100  # Convert cents to euros for emergentintegrations
        
        # Use configured URLs or fallback to request origin
        success_url = os.environ.get('STRIPE_SUCCESS_URL', f"{host_url}/app/dashboard?payment=success&session_id={{CHECKOUT_SESSION_ID}}")
        cancel_url = os.environ.get('STRIPE_CANCEL_URL', f"{host_url}/?payment=canceled")
        
        # Create checkout session
        session_request = CheckoutSessionRequest(
            amount=amount,
            currency="EUR", 
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"product": price_name, "app": app_name}
        )
        
        session = await stripe_checkout.create_checkout_session(session_request)
        
        # Store payment transaction
        transaction = PaymentTransaction(
            session_id=session.session_id,
            user_email="",  # Will be updated after payment
            amount=amount,
            currency="EUR",
            metadata={"product": price_name, "app": app_name}
        )
        await db.payment_transactions.insert_one(transaction.dict())
        
        return {"url": session.url, "session_id": session.session_id}
        
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create payment session")

@api_router.get("/checkout/status/{session_id}")
async def get_checkout_status(session_id: str):
    """Get payment status"""
    try:
        if not stripe_api_key:
            raise HTTPException(status_code=500, detail="Payment not configured")
        
        stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url="")
        status = await stripe_checkout.get_checkout_status(session_id)
        
        # Update transaction in database
        transaction = await db.payment_transactions.find_one({"session_id": session_id})
        if transaction and status.payment_status == "paid":
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": {"status": "completed", "payment_status": "paid"}}
            )
            
            # Create or update user account
            if status.metadata and status.metadata.get("customer_email"):
                user_email = status.metadata["customer_email"]
                
                user = await db.users.find_one({"email": user_email})
                if not user:
                    # Create new user
                    new_user = User(email=user_email, has_paid=True)
                    await db.users.insert_one(new_user.dict())
                else:
                    # Update existing user
                    await db.users.update_one(
                        {"email": user_email},
                        {"$set": {"has_paid": True}}
                    )
                
                # Send welcome email
                await email_service.send_welcome_email(user_email, user.get('name', 'Soignant'))
        
        return {
            "status": status.status,
            "payment_status": status.payment_status,
            "amount_total": status.amount_total,
            "currency": status.currency
        }
        
    except Exception as e:
        logger.error(f"Error checking payment status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to check payment status")

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    try:
        if not stripe_api_key:
            return {"status": "payment not configured"}
        
        body = await request.body()
        signature = request.headers.get("stripe-signature", "")
        
        stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url="")
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        if webhook_response.event_type == "checkout.session.completed":
            # Update transaction
            await db.payment_transactions.update_one(
                {"session_id": webhook_response.session_id},
                {"$set": {
                    "status": "completed",
                    "payment_status": webhook_response.payment_status
                }}
            )
            
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return {"status": "error", "message": str(e)}

# User endpoints
@api_router.post("/users", response_model=User)
async def create_user(user_data: UserCreate):
    """Create new user"""
    try:
        # Check if user exists
        existing_user = await db.users.find_one({"email": user_data.email})
        if existing_user:
            return serialize_mongo_doc(existing_user)
        
        # Create new user with default settings
        default_settings = {
            "water_goal_ml": 2000,
            "sleep_goal_h": 7.5,
            "activity_goal_min": 30,
            "serenity_goal_min": 10,
            "notifications_daily": True,
            "theme_pref": "forest"
        }
        
        user = User(**user_data.dict(), settings=default_settings)
        await db.users.insert_one(user.dict())
        return serialize_mongo_doc(user.dict())
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating user")

@api_router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    """Get user by ID"""
    try:
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return serialize_mongo_doc(user)
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving user")

@api_router.get("/users/email/{email}", response_model=User)
async def get_user_by_email(email: str):
    """Get user by email"""
    try:
        user = await db.users.find_one({"email": email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return serialize_mongo_doc(user)
    except Exception as e:
        logger.error(f"Error getting user by email: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving user")

# Dashboard endpoints
@api_router.get("/dashboard/{user_id}")
async def get_dashboard_data(user_id: str):
    """Get dashboard data for user"""
    try:
        # Get user
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user = serialize_mongo_doc(user)
        
        # Get today's habit log
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        habit_log = await db.habit_logs.find_one({
            "user_id": user_id,
            "date": {"$gte": today}
        })
        
        if not habit_log:
            # Create empty habit log for today
            habit_log_data = HabitLog(user_id=user_id, date=datetime.now(timezone.utc))
            await db.habit_logs.insert_one(habit_log_data.dict())
            habit_log = habit_log_data.dict()
        else:
            habit_log = serialize_mongo_doc(habit_log)
        
        # Calculate energy
        energy = calculate_energy_percentage(HabitLog(**habit_log), user.get("settings", {}))
        
        # Get daily quest
        daily_quest = await get_daily_quest_for_user(user_id)
        if daily_quest:
            daily_quest = serialize_mongo_doc(daily_quest)
        
        # Get random quote
        quotes = await db.quotes.find({}).to_list(50)
        if quotes:
            quote = serialize_mongo_doc(random.choice(quotes))
        else:
            quote = {"text": "Bonne journée !", "author": ""}
        
        return {
            "user": user,
            "energy_percentage": energy,
            "habit_log": habit_log,
            "daily_quest": daily_quest,
            "quote": quote,
            "level": user.get("level_number", 1),
            "xp_total": user.get("xp_total", 0),
            "xp_to_next_level": 150 - (user.get("xp_total", 0) % 150)
        }
    except Exception as e:
        logger.error(f"Error getting dashboard data for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error loading dashboard data")

# Habits endpoints
@api_router.put("/habits/{user_id}")
async def update_habits(user_id: str, habit_update: HabitUpdate):
    """Update today's habits for user"""
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Get or create habit log
    habit_log = await db.habit_logs.find_one({
        "user_id": user_id,
        "date": {"$gte": today}
    })
    
    update_data = {k: v for k, v in habit_update.dict().items() if v is not None}
    
    if habit_log:
        await db.habit_logs.update_one(
            {"id": habit_log["id"]},
            {"$set": update_data}
        )
    else:
        new_log = HabitLog(user_id=user_id, date=datetime.now(timezone.utc), **update_data)
        await db.habit_logs.insert_one(new_log.dict())
    
    # Award points for good habits
    user = await db.users.find_one({"id": user_id})
    user_settings = user.get("settings", {}) if user else {}
    
    points_earned = 0
    updated_log = await db.habit_logs.find_one({"user_id": user_id, "date": {"$gte": today}})
    log_obj = HabitLog(**updated_log)
    
    # Check for point-worthy achievements
    goals = {
        'water_goal_ml': user_settings.get('water_goal_ml', 2000),
        'sleep_goal_h': user_settings.get('sleep_goal_h', 7.5),
        'activity_goal_min': user_settings.get('activity_goal_min', 30),
        'serenity_goal_min': user_settings.get('serenity_goal_min', 10)
    }
    
    if log_obj.water_ml >= goals['water_goal_ml'] * 0.8:
        points_earned += 5
    if log_obj.sleep_h >= goals['sleep_goal_h'] * 0.8:
        points_earned += 5
    if log_obj.activity_min >= goals['activity_goal_min'] * 0.8:
        points_earned += 5
    if log_obj.serenity_min >= goals['serenity_goal_min']:
        points_earned += 5
    if log_obj.nutrition_score_0_100 >= 70:
        points_earned += 5
    
    if points_earned > 0:
        await award_points_and_check_badges(user_id, points_earned)
    
    return {"message": "Habits updated successfully", "points_earned": points_earned}

# Quests endpoints
@api_router.get("/quests/{user_id}")
async def get_user_quests(user_id: str):
    """Get user's quests"""
    # Get daily quest
    daily_quest = await get_daily_quest_for_user(user_id)
    
    # Get weekly and special quests (simplified for MVP)
    all_quests = await db.quests.find({
        "type": {"$in": ["weekly", "special"]},
        "is_active": True
    }).to_list(20)
    
    return {
        "daily_quest": daily_quest,
        "other_quests": [serialize_mongo_doc(quest) for quest in all_quests[:6]]  # Limit for UI
    }

@api_router.post("/quests/{user_id}/{quest_id}/complete")
async def complete_quest(user_id: str, quest_id: str):
    """Mark quest as completed"""
    # Get quest
    quest = await db.quests.find_one({"id": quest_id})
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")
    
    # Update user quest status
    await db.user_quests.update_one(
        {"user_id": user_id, "quest_id": quest_id, "status": {"$ne": "done"}},
        {
            "$set": {
                "status": "done",
                "completed_at": datetime.now(timezone.utc)
            }
        }
    )
    
    # Award points
    points = quest.get("points_reward", 0)
    await award_points_and_check_badges(user_id, points)
    
    return {"message": "Quest completed!", "points_earned": points}

# Quotes endpoint
@api_router.get("/quotes/random")
async def get_random_quote():
    """Get random motivational quote"""
    import random
    quotes = await db.quotes.find({}).to_list(100)
    if quotes:
        selected_quote = random.choice(quotes)
        return serialize_mongo_doc(selected_quote)
    else:
        return {"text": "Bonne journée !", "author": ""}

# Include router
app.include_router(api_router)

# Landing page endpoint
@app.get("/", response_class=HTMLResponse)
async def landing_page():
    """Serve the landing page"""
    return """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Énergie & Bien-être pour soignants™</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            .gradient-bg { background: linear-gradient(135deg, #0E3A53 0%, #3FB28C 100%); }
            .glass-effect { backdrop-filter: blur(12px); background: rgba(255, 255, 255, 0.1); }
        </style>
    </head>
    <body class="bg-gray-50">
        <div id="root"></div>
        <script src="/static/js/bundle.js"></script>
    </body>
    </html>
    """

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "energie-bien-etre"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)