# Service pour la gestion des professions et progression
import logging
from typing import List, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from models import Profession, ProgressionMetier, UserProgression, PROFESSIONS_SEED, PROGRESSION_SEED

logger = logging.getLogger(__name__)

class ProfessionService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def seed_professions(self):
        """Seeder les professions et progressions si elles n'existent pas"""
        try:
            # Vérifier si les professions existent déjà
            existing_count = await self.db.professions.count_documents({})
            if existing_count > 0:
                logger.info("Professions already seeded")
                return
            
            # Seed professions
            professions_to_insert = []
            for prof_data in PROFESSIONS_SEED:
                profession = Profession(**prof_data)
                professions_to_insert.append(profession.dict())
            
            if professions_to_insert:
                await self.db.professions.insert_many(professions_to_insert)
                logger.info(f"Seeded {len(professions_to_insert)} professions")
            
            # Seed progressions métiers
            progressions_to_insert = []
            for prog_data in PROGRESSION_SEED:
                progression = ProgressionMetier(**prog_data)
                progressions_to_insert.append(progression.dict())
            
            if progressions_to_insert:
                await self.db.progression_metiers.insert_many(progressions_to_insert)
                logger.info(f"Seeded {len(progressions_to_insert)} progressions métiers")
                
        except Exception as e:
            logger.error(f"Error seeding professions: {str(e)}")
    
    async def get_active_professions(self) -> List[Dict]:
        """Récupérer toutes les professions actives"""
        try:
            professions = await self.db.professions.find(
                {"is_active": True}
            ).sort("order_index", 1).to_list(100)
            
            return [self._serialize_profession(prof) for prof in professions]
        except Exception as e:
            logger.error(f"Error getting professions: {str(e)}")
            return []
    
    async def get_profession_by_slug(self, slug: str) -> Optional[Dict]:
        """Récupérer une profession par son slug"""
        try:
            profession = await self.db.professions.find_one({"slug": slug, "is_active": True})
            return self._serialize_profession(profession) if profession else None
        except Exception as e:
            logger.error(f"Error getting profession {slug}: {str(e)}")
            return None
    
    async def get_progression_for_profession(self, profession_slug: str) -> List[Dict]:
        """Récupérer la progression complète pour une profession"""
        try:
            progressions = await self.db.progression_metiers.find(
                {"profession_slug": profession_slug}
            ).sort("order_index", 1).to_list(10)
            
            return [self._serialize_progression(prog) for prog in progressions]
        except Exception as e:
            logger.error(f"Error getting progression for {profession_slug}: {str(e)}")
            return []
    
    async def get_user_progression(self, user_id: str) -> Optional[Dict]:
        """Récupérer la progression utilisateur"""
        try:
            progression = await self.db.user_progressions.find_one({"user_id": user_id})
            return self._serialize_progression(progression) if progression else None
        except Exception as e:
            logger.error(f"Error getting user progression: {str(e)}")
            return None
    
    async def init_user_progression(self, user_id: str, profession_slug: str) -> Dict:
        """Initialiser la progression d'un utilisateur pour sa profession"""
        try:
            # Vérifier si l'utilisateur a déjà une progression
            existing = await self.db.user_progressions.find_one({"user_id": user_id})
            if existing:
                return self._serialize_progression(existing)
            
            # Créer nouvelle progression
            user_progression = UserProgression(
                user_id=user_id,
                profession_slug=profession_slug
            )
            
            await self.db.user_progressions.insert_one(user_progression.dict())
            return user_progression.dict()
            
        except Exception as e:
            logger.error(f"Error initializing user progression: {str(e)}")
            return {}
    
    async def update_user_progression(self, user_id: str, niveau_complete: int, xp_gained: int) -> bool:
        """Mettre à jour la progression utilisateur"""
        try:
            # Récupérer progression actuelle
            progression = await self.db.user_progressions.find_one({"user_id": user_id})
            if not progression:
                return False
            
            # Calculer nouveaux niveaux complétés
            niveaux_completes = progression.get("niveaux_completes", [])
            if niveau_complete not in niveaux_completes:
                niveaux_completes.append(niveau_complete)
            
            # Nouveau niveau actuel
            nouveau_niveau = max(niveaux_completes) + 1 if niveaux_completes else 1
            
            # Mettre à jour
            await self.db.user_progressions.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "niveau_actuel": min(nouveau_niveau, 5),  # Max niveau 5
                        "niveaux_completes": niveaux_completes
                    },
                    "$inc": {"xp_total": xp_gained}
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating user progression: {str(e)}")
            return False
    
    async def check_progression_completion(self, user_id: str, habit_data: Dict) -> List[Dict]:
        """Vérifier si l'utilisateur a complété des niveaux de progression"""
        try:
            # Récupérer progression utilisateur
            user_prog = await self.get_user_progression(user_id)
            if not user_prog:
                return []
            
            profession_slug = user_prog.get("profession_slug")
            if not profession_slug:
                return []
            
            # Récupérer progression métier
            progression_levels = await self.get_progression_for_profession(profession_slug)
            if not progression_levels:
                return []
            
            completed_levels = []
            for level in progression_levels:
                niveau = level.get("niveau")
                objectif = level.get("objectif", "")
                
                # Vérifier si ce niveau n'est pas déjà complété
                if niveau in user_prog.get("niveaux_completes", []):
                    continue
                
                # Logic simple de vérification (peut être étendue)
                is_completed = False
                
                if "hydratation" in objectif.lower() and habit_data.get("water_ml", 0) >= 2000:
                    is_completed = True
                elif "sommeil" in objectif.lower() and habit_data.get("sleep_h", 0) >= 7:
                    is_completed = True
                elif "activité" in objectif.lower() and habit_data.get("activity_min", 0) >= 30:
                    is_completed = True
                elif "sérénité" in objectif.lower() and habit_data.get("serenity_min", 0) >= 10:
                    is_completed = True
                
                if is_completed:
                    completed_levels.append(level)
                    # Mettre à jour la progression
                    reward_xp = 50 + (niveau - 1) * 20  # XP croissant par niveau
                    await self.update_user_progression(user_id, niveau, reward_xp)
            
            return completed_levels
            
        except Exception as e:
            logger.error(f"Error checking progression completion: {str(e)}")
            return []
    
    def _serialize_profession(self, profession: Dict) -> Dict:
        """Sérialiser une profession pour l'API"""
        if not profession:
            return {}
        return {
            "id": profession.get("id"),
            "label": profession.get("label"),
            "slug": profession.get("slug"),
            "icon": profession.get("icon"),
            "order_index": profession.get("order_index"),
            "is_active": profession.get("is_active"),
            "recommended_quests": profession.get("recommended_quests", [])
        }
    
    def _serialize_progression(self, progression: Dict) -> Dict:
        """Sérialiser une progression pour l'API"""
        if not progression:
            return {}
        return {
            "id": progression.get("id"),
            "profession_slug": progression.get("profession_slug"),
            "niveau": progression.get("niveau"),
            "titre": progression.get("titre"),
            "icon": progression.get("icon"),
            "objectif": progression.get("objectif"),
            "reward": progression.get("reward"),
            "order_index": progression.get("order_index"),
            "user_id": progression.get("user_id"),
            "niveau_actuel": progression.get("niveau_actuel"),
            "xp_total": progression.get("xp_total"),
            "niveaux_completes": progression.get("niveaux_completes", [])
        }