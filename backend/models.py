# Models pour le système de professions et progression
from pydantic import BaseModel, EmailStr, Field
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
import uuid

# User models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: Optional[str] = None
    role: str = "user"
    settings: Optional[Dict] = {}
    profession_slug: Optional[str] = None
    profession_label: Optional[str] = None
    profession_icon: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    has_paid: bool = False
    xp_total: int = 0
    level_number: int = 1

class HabitLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    date: datetime
    water_ml: float = 0
    sleep_h: float = 0
    nutrition_score_0_100: int = 0
    activity_min: float = 0
    serenity_min: float = 0
    mood_1_10: int = 5
    stress_0_10: int = 5
    notes: Optional[str] = None

class Quest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    type: str  # daily, weekly, special
    points_reward: int
    badge_id: Optional[str] = None
    branch: Optional[str] = None  # stress, sleep, hydration, strength, resilience
    is_global: bool = True
    is_active: bool = True

class UserQuest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    quest_id: str
    date_assigned: datetime
    status: str = "todo"  # todo, in_progress, done
    completed_at: Optional[datetime] = None

class Badge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    label: str
    description: str
    icon: str

class UserBadge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    badge_id: str
    earned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Quote(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    author: Optional[str] = None

class PaymentTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_email: str
    amount: float
    currency: str = "EUR"
    status: str = "pending"
    payment_status: str = "pending"
    metadata: Optional[Dict] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Profession models

class Profession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    label: str
    slug: str
    icon: str
    order_index: int = 100
    is_active: bool = True
    recommended_quests: List[Dict] = []
    progression_tree: List[Dict] = []

class ProgressionMetier(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    profession_slug: str
    niveau: int
    titre: str
    icon: str
    objectif: str
    reward: str
    order_index: int

class UserProgression(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    profession_slug: str
    niveau_actuel: int = 1
    xp_total: int = 0
    niveaux_completes: List[int] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProfessionQuest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    profession_slug: str
    title: str
    description: str
    points_reward: int
    type: str  # daily, weekly
    branch: Optional[str] = None
    is_active: bool = True

# Données de seed pour les professions
PROFESSIONS_SEED = [
    {
        "label": "Infirmier·ère",
        "slug": "infirmier",
        "icon": "🩺",
        "order_index": 1,
        "recommended_quests": [
            {"title": "Hydratation 2L au service", "description": "Boire 2L d'eau pendant votre garde", "points_reward": 10, "type": "daily"},
            {"title": "3 pauses respiration pendant les gardes", "description": "Prendre 3 pauses de 5 min de respiration", "points_reward": 30, "type": "weekly"}
        ]
    },
    {
        "label": "Aide-soignant·e", 
        "slug": "aide_soignant",
        "icon": "❤️",
        "order_index": 2,
        "recommended_quests": [
            {"title": "S'étirer 5 min après chaque relève", "description": "Étirements courts après changement d'équipe", "points_reward": 10, "type": "daily"},
            {"title": "Tenir 5 jours avec 7h de sommeil minimum", "description": "Maintenir un sommeil réparateur", "points_reward": 30, "type": "weekly"}
        ]
    },
    {
        "label": "Kinésithérapeute",
        "slug": "kine", 
        "icon": "🏋️",
        "order_index": 3,
        "recommended_quests": [
            {"title": "3 exercices de mobilité personnelle", "description": "Travailler épaules, hanches, dos", "points_reward": 15, "type": "daily"},
            {"title": "5 séances d'auto-renforcement", "description": "Renforcement musculaire 10 min", "points_reward": 40, "type": "weekly"}
        ]
    },
    {
        "label": "Médecin",
        "slug": "medecin",
        "icon": "⚕️", 
        "order_index": 4,
        "recommended_quests": [
            {"title": "Pause 5 min hors écran entre consultations", "description": "Déconnexion numérique régulière", "points_reward": 10, "type": "daily"},
            {"title": "Limiter les cafés sucrés pendant 3 jours", "description": "Réduire le sucre ajouté", "points_reward": 30, "type": "weekly"}
        ]
    },
    {
        "label": "Sage-femme",
        "slug": "sage_femme",
        "icon": "👶",
        "order_index": 5,
        "recommended_quests": [
            {"title": "10 respirations profondes après chaque accouchement", "description": "Récupération post-intervention", "points_reward": 10, "type": "daily"},
            {"title": "3 pauses détente 10 min dans la semaine", "description": "Moments de sérénité programmés", "points_reward": 30, "type": "weekly"}
        ]
    },
    {
        "label": "Ambulancier·ère",
        "slug": "ambulancier",
        "icon": "🚑",
        "order_index": 6,
        "recommended_quests": [
            {"title": "Respiration guidée 5 min après intervention", "description": "Récupération post-urgence", "points_reward": 10, "type": "daily"},
            {"title": "3 séances d'étirement dos/jambes", "description": "Entretien postural", "points_reward": 30, "type": "weekly"}
        ]
    },
    {
        "label": "Ergothérapeute",
        "slug": "ergo",
        "icon": "✋",
        "order_index": 7,
        "recommended_quests": [
            {"title": "Prendre 5 min pour une activité manuelle", "description": "Dessin, écriture créative", "points_reward": 10, "type": "daily"},
            {"title": "3 jours de suite avec ≥7h sommeil", "description": "Régularité du sommeil", "points_reward": 30, "type": "weekly"}
        ]
    },
    {
        "label": "Psychologue",
        "slug": "psy",
        "icon": "🧠",
        "order_index": 8,
        "recommended_quests": [
            {"title": "Écrire une pensée positive après chaque séance", "description": "Journal de gratitude professionnel", "points_reward": 10, "type": "daily"},
            {"title": "2 jours de méditation 10 min", "description": "Pratique méditative régulière", "points_reward": 30, "type": "weekly"}
        ]
    },
    {
        "label": "Manipulateur·trice radio",
        "slug": "manip_radio",
        "icon": "📸",
        "order_index": 9,
        "recommended_quests": [
            {"title": "5 min étirements poignets/épaules", "description": "Prévention TMS", "points_reward": 10, "type": "daily"},
            {"title": "Marcher 20 min 3x/semaine", "description": "Activité cardiovasculaire douce", "points_reward": 30, "type": "weekly"}
        ]
    },
    {
        "label": "ASH (Agent de Service Hospitalier)",
        "slug": "ash",
        "icon": "🧹",
        "order_index": 10,
        "recommended_quests": [
            {"title": "Pause respiration 3 min entre deux tâches", "description": "Micro-récupération active", "points_reward": 10, "type": "daily"},
            {"title": "Hydratation ≥ 1,5L/jour sur 5 jours", "description": "Maintien hydratation optimale", "points_reward": 30, "type": "weekly"}
        ]
    },
    {
        "label": "Étudiant·e en soins infirmiers",
        "slug": "etudiant",
        "icon": "📚",
        "order_index": 11,
        "recommended_quests": [
            {"title": "Révision rapide 10 min", "description": "Flashcards ou notes de cours", "points_reward": 10, "type": "daily"},
            {"title": "Sommeil ≥ 7h sur 4 nuits", "description": "Récupération étudiante", "points_reward": 30, "type": "weekly"}
        ]
    },
    {
        "label": "Auxiliaire de puériculture",
        "slug": "aux_puer",
        "icon": "🍼",
        "order_index": 12,
        "recommended_quests": [
            {"title": "Hydratation régulière (1 verre toutes les 2h)", "description": "Rythme hydratation structuré", "points_reward": 10, "type": "daily"},
            {"title": "2 séances relaxation 10 min", "description": "Techniques de détente", "points_reward": 30, "type": "weekly"}
        ]
    },
    {
        "label": "Cadre de santé",
        "slug": "cadre",
        "icon": "🗂️",
        "order_index": 13,
        "recommended_quests": [
            {"title": "Check bien-être : humeur/stress en début de journée", "description": "Auto-évaluation matinale", "points_reward": 10, "type": "daily"},
            {"title": "Bloquer 30 min dans la semaine pour soi", "description": "Temps personnel programmé", "points_reward": 30, "type": "weekly"}
        ]
    },
    {
        "label": "Ostéopathe",
        "slug": "osteo",
        "icon": "🤲",
        "order_index": 14,
        "recommended_quests": [
            {"title": "Auto-étirement 5 min après chaque patient", "description": "Maintenance corporelle continue", "points_reward": 10, "type": "daily"},
            {"title": "3 séances renfo musculaire 15 min", "description": "Renforcement préventif", "points_reward": 40, "type": "weekly"}
        ]
    },
    {
        "label": "Nutritionniste / Diététicien·ne",
        "slug": "nutri",
        "icon": "🥗",
        "order_index": 15,
        "recommended_quests": [
            {"title": "Prendre un repas équilibré sans écran", "description": "Alimentation consciente", "points_reward": 10, "type": "daily"},
            {"title": "Préparer 3 repas maison dans la semaine", "description": "Cuisine thérapeutique", "points_reward": 30, "type": "weekly"}
        ]
    }
]

# Données de progression par métier
PROGRESSION_SEED = [
    # INFIRMIER
    {"profession_slug": "infirmier", "niveau": 1, "titre": "Gardien de l'hydratation", "icon": "💧", "objectif": "2L d'eau/jour × 5 jours", "reward": "+50 XP", "order_index": 1},
    {"profession_slug": "infirmier", "niveau": 2, "titre": "Veilleur·se du sommeil", "icon": "💤", "objectif": "≥7h sur 5 nuits", "reward": "+70 XP", "order_index": 2},
    {"profession_slug": "infirmier", "niveau": 3, "titre": "Champion·ne des pauses", "icon": "🌬", "objectif": "10 respirations guidées", "reward": "+100 XP", "order_index": 3},
    {"profession_slug": "infirmier", "niveau": 4, "titre": "Force tranquille", "icon": "🪷", "objectif": "3 semaines ≥70% habitudes", "reward": "+150 XP", "order_index": 4},
    {"profession_slug": "infirmier", "niveau": 5, "titre": "Modèle de constance", "icon": "⭐", "objectif": "30 jours de suivi", "reward": "+200 XP + Badge ⭐", "order_index": 5},
    
    # AIDE-SOIGNANT
    {"profession_slug": "aide_soignant", "niveau": 1, "titre": "Soulagement rapide", "icon": "🤸", "objectif": "5 étirements courts", "reward": "+50 XP", "order_index": 1},
    {"profession_slug": "aide_soignant", "niveau": 2, "titre": "Soutien vital", "icon": "💤", "objectif": "5 jours ≥7h sommeil", "reward": "+70 XP", "order_index": 2},
    {"profession_slug": "aide_soignant", "niveau": 3, "titre": "Énergie au service", "icon": "💧", "objectif": "7 jours ≥80% hydratation", "reward": "+100 XP", "order_index": 3},
    {"profession_slug": "aide_soignant", "niveau": 4, "titre": "Endurance douce", "icon": "🏃", "objectif": "3 semaines ≥70% activité", "reward": "+150 XP", "order_index": 4},
    {"profession_slug": "aide_soignant", "niveau": 5, "titre": "Pilier du service", "icon": "🏅", "objectif": "30 jours constance", "reward": "+200 XP + Badge 🏅", "order_index": 5},
    
    # KINE
    {"profession_slug": "kine", "niveau": 1, "titre": "Mobilité active", "icon": "🦵", "objectif": "3 exercices mobilité × 5 jours", "reward": "+50 XP", "order_index": 1},
    {"profession_slug": "kine", "niveau": 2, "titre": "Équilibre postural", "icon": "🪑", "objectif": "3 séances renfo en 1 semaine", "reward": "+70 XP", "order_index": 2},
    {"profession_slug": "kine", "niveau": 3, "titre": "Expert du mouvement", "icon": "⚡", "objectif": "10 jours ≥80% activité", "reward": "+100 XP", "order_index": 3},
    {"profession_slug": "kine", "niveau": 4, "titre": "Santé incarnée", "icon": "🥗", "objectif": "4 semaines ≥70% nutrition+activité", "reward": "+150 XP", "order_index": 4},
    {"profession_slug": "kine", "niveau": 5, "titre": "Maître kiné", "icon": "🏆", "objectif": "40 jours suivis", "reward": "+200 XP + Badge 🏆", "order_index": 5},

    # MEDECIN
    {"profession_slug": "medecin", "niveau": 1, "titre": "Pause bien méritée", "icon": "☕", "objectif": "5 min hors écran entre consultations", "reward": "+50 XP", "order_index": 1},
    {"profession_slug": "medecin", "niveau": 2, "titre": "Détox caféinée", "icon": "🥤", "objectif": "Limiter cafés sucrés pendant 3 jours", "reward": "+70 XP", "order_index": 2},
    {"profession_slug": "medecin", "niveau": 3, "titre": "Récup rapide", "icon": "🧘", "objectif": "Activité douce ≥70% sur 7 jours", "reward": "+100 XP", "order_index": 3},
    {"profession_slug": "medecin", "niveau": 4, "titre": "Calme du praticien", "icon": "🪷", "objectif": "4 semaines ≥70% sérénité", "reward": "+150 XP", "order_index": 4},
    {"profession_slug": "medecin", "niveau": 5, "titre": "Force soignante", "icon": "🩺", "objectif": "30 jours constance", "reward": "+200 XP + Badge 🩺", "order_index": 5},

    # SAGE-FEMME
    {"profession_slug": "sage_femme", "niveau": 1, "titre": "Soutien maternel", "icon": "👶", "objectif": "10 min respiration consciente", "reward": "+50 XP", "order_index": 1},
    {"profession_slug": "sage_femme", "niveau": 2, "titre": "Douceur nocturne", "icon": "🌙", "objectif": "≥7h de sommeil × 5 nuits", "reward": "+70 XP", "order_index": 2},
    {"profession_slug": "sage_femme", "niveau": 3, "titre": "Accompagnante sereine", "icon": "🤱", "objectif": "7 jours ≥70% hydratation", "reward": "+100 XP", "order_index": 3},
    {"profession_slug": "sage_femme", "niveau": 4, "titre": "Pilier du calme", "icon": "🪷", "objectif": "3 semaines constance bien-être", "reward": "+150 XP", "order_index": 4},
    {"profession_slug": "sage_femme", "niveau": 5, "titre": "Modèle inspirant", "icon": "👩‍👧", "objectif": "30 jours constance", "reward": "+200 XP + Badge 💎", "order_index": 5},

    # AMBULANCIER
    {"profession_slug": "ambulancier", "niveau": 1, "titre": "Réactivité saine", "icon": "🚑", "objectif": "Hydratation régulière × 5 jours", "reward": "+50 XP", "order_index": 1},
    {"profession_slug": "ambulancier", "niveau": 2, "titre": "Pause éclair", "icon": "⚡", "objectif": "3 pauses respiration", "reward": "+70 XP", "order_index": 2},
    {"profession_slug": "ambulancier", "niveau": 3, "titre": "Force mobile", "icon": "💪", "objectif": "7 jours ≥80% activité douce", "reward": "+100 XP", "order_index": 3},
    {"profession_slug": "ambulancier", "niveau": 4, "titre": "Calme en urgence", "icon": "🧘", "objectif": "3 semaines sérénité", "reward": "+150 XP", "order_index": 4},
    {"profession_slug": "ambulancier", "niveau": 5, "titre": "Pilier des routes", "icon": "🏅", "objectif": "30 jours constance", "reward": "+200 XP + Badge 🚑", "order_index": 5},

    # PSYCHOLOGUE
    {"profession_slug": "psy", "niveau": 1, "titre": "Écoute intérieure", "icon": "🧠", "objectif": "5 min méditation/jour", "reward": "+50 XP", "order_index": 1},
    {"profession_slug": "psy", "niveau": 2, "titre": "Sérénité active", "icon": "🌿", "objectif": "≥7h sommeil × 5 nuits", "reward": "+70 XP", "order_index": 2},
    {"profession_slug": "psy", "niveau": 3, "titre": "Clarté d'esprit", "icon": "✨", "objectif": "7 jours ≥70% hydratation", "reward": "+100 XP", "order_index": 3},
    {"profession_slug": "psy", "niveau": 4, "titre": "Présence calme", "icon": "🪷", "objectif": "3 semaines ≥70% habitudes", "reward": "+150 XP", "order_index": 4},
    {"profession_slug": "psy", "niveau": 5, "titre": "Maître de l'équilibre", "icon": "💎", "objectif": "30 jours constance", "reward": "+200 XP + Badge 🧠", "order_index": 5}
]