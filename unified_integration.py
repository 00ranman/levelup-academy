#!/usr/bin/env python3
"""
LevelUp Academy Unified Integration
Connects LevelUp Academy to the Extropy ecosystem with unified auth and XP tracking
"""

import asyncio
import aiohttp
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import sqlite3
import hashlib
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LearningXPTransaction:
    user_id: str
    action_type: str
    description: str
    entropy_delta: float
    closure_speed: float
    domain: str
    metadata: Dict[str, Any]

class LevelUpIntegration:
    def __init__(self):
        self.auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://localhost:3002")
        self.xp_ledger_url = os.getenv("XP_LEDGER_URL", "http://localhost:3001")
        self.gateway_url = os.getenv("GATEWAY_URL", "http://localhost:3000")
        
        self.auth_token = None
        self.user_data = None
        self.session = None
        
        # Initialize local database for learning progress sync
        self.init_local_db()
    
    def init_local_db(self):
        """Initialize local database for storing learning progress and XP transactions"""
        conn = sqlite3.connect('levelup_integration.db')
        cursor = conn.cursor()
        
        # Learning XP transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_xp_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                description TEXT NOT NULL,
                entropy_delta REAL NOT NULL,
                closure_speed REAL NOT NULL,
                domain TEXT NOT NULL,
                metadata TEXT NOT NULL,
                synced BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ledger_transaction_id TEXT
            )
        ''')
        
        # Learning progress table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                course_id TEXT NOT NULL,
                module_id TEXT,
                lesson_id TEXT,
                progress_type TEXT NOT NULL,
                completion_percentage REAL DEFAULT 0,
                time_spent INTEGER DEFAULT 0,
                comprehension_score REAL DEFAULT 0,
                knowledge_gained REAL DEFAULT 0,
                skill_level_before REAL DEFAULT 0,
                skill_level_after REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                xp_transaction_id INTEGER,
                FOREIGN KEY (xp_transaction_id) REFERENCES learning_xp_transactions (id)
            )
        ''')
        
        # Knowledge graph table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_graph (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                concept_id TEXT NOT NULL,
                concept_name TEXT NOT NULL,
                mastery_level REAL DEFAULT 0,
                confidence_level REAL DEFAULT 0,
                last_reinforced TIMESTAMP,
                connection_strength REAL DEFAULT 0,
                prerequisite_concepts TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Learning achievements table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                achievement_type TEXT NOT NULL,
                achievement_name TEXT NOT NULL,
                description TEXT NOT NULL,
                xp_reward REAL NOT NULL,
                unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                xp_transaction_id INTEGER,
                FOREIGN KEY (xp_transaction_id) REFERENCES learning_xp_transactions (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def authenticate_user(self, email: str, password: str = None, token: str = None) -> bool:
        """Authenticate user with unified auth service"""
        try:
            async with aiohttp.ClientSession() as session:
                if token:
                    # Verify existing token
                    headers = {"Authorization": f"Bearer {token}"}
                    async with session.get(f"{self.auth_service_url}/api/users/me", headers=headers) as response:
                        if response.status == 200:
                            self.user_data = await response.json()
                            self.auth_token = token
                            await self.connect_platform()
                            return True
                else:
                    # Login with credentials
                    login_data = {"email": email, "password": password}
                    async with session.post(f"{self.auth_service_url}/api/auth/login", json=login_data) as response:
                        if response.status == 200:
                            result = await response.json()
                            self.auth_token = result["token"]
                            self.user_data = result["user"]
                            await self.connect_platform()
                            return True
                        
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            
        return False
    
    async def connect_platform(self) -> bool:
        """Connect LevelUp Academy to the unified platform"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            platform_data = {
                "platformUserId": self.user_data["userId"],
                "username": self.user_data.get("profile", {}).get("displayName", "LevelUp Student"),
                "credentials": {
                    "levelup_version": "3.0",
                    "capabilities": [
                        "adaptive_learning", "knowledge_tracking", "skill_assessment", 
                        "progress_analytics", "achievement_system", "peer_learning"
                    ]
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.auth_service_url}/api/platforms/connect/levelup-academy",
                    json=platform_data,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("LevelUp Academy connected to unified platform")
                        return True
                        
        except Exception as e:
            logger.error(f"Platform connection failed: {e}")
            
        return False
    
    def calculate_learning_entropy(self, learning_data: Dict[str, Any]) -> float:
        """Calculate entropy reduction for learning activities based on knowledge theory"""
        
        # Base entropy for knowledge acquisition
        base_entropy = 15.0
        
        # Difficulty multiplier (how challenging the material is)
        difficulty = learning_data.get("difficulty", 1.0)
        
        # Comprehension score (how well understood)
        comprehension = learning_data.get("comprehension_score", 0.8)
        
        # Knowledge gain (measured change in understanding)
        knowledge_gain = learning_data.get("knowledge_gained", 0.5)
        
        # Time investment efficiency
        time_spent = learning_data.get("time_spent", 60)  # minutes
        optimal_time = learning_data.get("optimal_time", 60)
        time_efficiency = min(2.0, optimal_time / time_spent) if time_spent > 0 else 1.0
        
        # Skill level progression
        skill_before = learning_data.get("skill_level_before", 0.0)
        skill_after = learning_data.get("skill_level_after", 0.0)
        skill_progression = skill_after - skill_before
        
        # Retention factor (spaced repetition effectiveness)
        retention_factor = learning_data.get("retention_factor", 1.0)
        
        # Peer interaction bonus
        peer_interactions = learning_data.get("peer_interactions", 0)
        social_learning_bonus = min(3.0, peer_interactions * 0.3)
        
        # Calculate entropy reduction using learning theory
        entropy_delta = (
            base_entropy * 
            difficulty * 
            comprehension * 
            knowledge_gain * 
            time_efficiency * 
            retention_factor * 
            (1 + skill_progression)
        ) + social_learning_bonus
        
        return round(entropy_delta, 2)
    
    async def track_learning_progress(self, learning_data: Dict[str, Any]) -> Optional[str]:
        """Track learning progress and calculate XP"""
        if not self.user_data:
            logger.error("User not authenticated")
            return None
        
        # Calculate entropy reduction
        entropy_delta = self.calculate_learning_entropy(learning_data)
        
        # Determine causal closure speed based on learning type
        learning_type = learning_data.get("learning_type", "concept")
        closure_speeds = {
            "concept": 1e6,      # Cognitive - understanding concepts
            "skill": 1e5,        # Psychomotor - developing skills
            "social": 1e3,       # Social - collaborative learning
            "habit": 1e2,        # Behavioral - forming learning habits
            "mastery": 1e4       # Expert - achieving mastery
        }
        closure_speed = closure_speeds.get(learning_type, 1e6)
        
        # Create XP transaction
        transaction = LearningXPTransaction(
            user_id=self.user_data["userId"],
            action_type=f"learning_{learning_data.get('action_type', 'progress')}",
            description=f"Learning progress: {learning_data.get('title', 'Unknown Content')}",
            entropy_delta=entropy_delta,
            closure_speed=closure_speed,
            domain="cognitive",
            metadata={
                "course_id": learning_data.get("course_id"),
                "module_id": learning_data.get("module_id"),
                "lesson_id": learning_data.get("lesson_id"),
                "learning_type": learning_type,
                "difficulty": learning_data.get("difficulty", 1.0),
                "comprehension_score": learning_data.get("comprehension_score", 0.8),
                "time_spent": learning_data.get("time_spent", 0),
                "knowledge_gained": learning_data.get("knowledge_gained", 0.5),
                "skill_progression": learning_data.get("skill_level_after", 0) - learning_data.get("skill_level_before", 0),
                "platform": "levelup-academy"
            }
        )
        
        # Track XP transaction
        return await self.track_xp_transaction(transaction)
    
    async def track_xp_transaction(self, transaction: LearningXPTransaction) -> Optional[str]:
        """Track XP transaction locally and sync with ledger"""
        try:
            # Store locally first
            local_id = self.store_local_xp_transaction(transaction)
            
            # Sync with XP Ledger
            if self.auth_token:
                ledger_id = await self.sync_to_xp_ledger(transaction)
                if ledger_id:
                    self.update_transaction_sync_status(local_id, ledger_id)
                    return ledger_id
            
            return str(local_id)
            
        except Exception as e:
            logger.error(f"XP tracking failed: {e}")
            return None
    
    def store_local_xp_transaction(self, transaction: LearningXPTransaction) -> int:
        """Store XP transaction in local database"""
        conn = sqlite3.connect('levelup_integration.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO learning_xp_transactions 
            (user_id, action_type, description, entropy_delta, closure_speed, domain, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            transaction.user_id,
            transaction.action_type,
            transaction.description,
            transaction.entropy_delta,
            transaction.closure_speed,
            transaction.domain,
            json.dumps(transaction.metadata)
        ))
        
        local_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return local_id
    
    async def sync_to_xp_ledger(self, transaction: LearningXPTransaction) -> Optional[str]:
        """Sync XP transaction to the central ledger"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            ledger_data = {
                "userId": transaction.user_id,
                "platform": "levelup-academy",
                "actionType": transaction.action_type,
                "actionDescription": transaction.description,
                "entropyDelta": transaction.entropy_delta,
                "causalClosureSpeed": transaction.closure_speed,
                "domain": transaction.domain,
                "validators": [
                    {
                        "type": "learning_analytics",
                        "validatorId": "levelup_analytics",
                        "score": 0.95,
                        "timestamp": datetime.now().isoformat()
                    }
                ],
                "metadata": {
                    **transaction.metadata,
                    "source": "levelup-academy",
                    "integration_version": "3.0"
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.xp_ledger_url}/api/xp/transaction",
                    json=ledger_data,
                    headers=headers
                ) as response:
                    if response.status == 201:
                        result = await response.json()
                        return result["transaction"]["transactionId"]
                        
        except Exception as e:
            logger.error(f"XP Ledger sync failed: {e}")
            
        return None
    
    def update_transaction_sync_status(self, local_id: int, ledger_id: str):
        """Update local transaction with sync status"""
        conn = sqlite3.connect('levelup_integration.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE learning_xp_transactions 
            SET synced = TRUE, ledger_transaction_id = ?
            WHERE id = ?
        ''', (ledger_id, local_id))
        
        conn.commit()
        conn.close()
    
    async def handle_course_completion(self, course_data: Dict[str, Any]) -> Optional[str]:
        """Handle course completion and award XP"""
        completion_data = {
            **course_data,
            "action_type": "course_completion",
            "learning_type": "mastery",
            "knowledge_gained": 1.0,  # Full course completion
            "comprehension_score": course_data.get("final_score", 0.9),
            "retention_factor": 1.2,  # Bonus for full completion
        }
        
        return await self.track_learning_progress(completion_data)
    
    async def handle_quiz_completion(self, quiz_data: Dict[str, Any]) -> Optional[str]:
        """Handle quiz completion and award XP based on performance"""
        quiz_progress = {
            **quiz_data,
            "action_type": "quiz_completion",
            "learning_type": "skill",
            "comprehension_score": quiz_data.get("score", 0.8),
            "knowledge_gained": min(1.0, quiz_data.get("score", 0.8) * 1.2),
            "difficulty": quiz_data.get("difficulty", 1.0),
        }
        
        return await self.track_learning_progress(quiz_progress)
    
    async def handle_study_session(self, session_data: Dict[str, Any]) -> Optional[str]:
        """Handle study session and award XP for focused learning"""
        study_progress = {
            **session_data,
            "action_type": "study_session",
            "learning_type": "concept",
            "time_spent": session_data.get("duration", 30),
            "optimal_time": 45,  # Optimal study session length
            "comprehension_score": session_data.get("engagement_score", 0.8),
            "knowledge_gained": session_data.get("progress_made", 0.3),
        }
        
        return await self.track_learning_progress(study_progress)
    
    async def handle_peer_interaction(self, interaction_data: Dict[str, Any]) -> Optional[str]:
        """Handle peer learning interaction and award XP"""
        peer_progress = {
            **interaction_data,
            "action_type": "peer_interaction",
            "learning_type": "social",
            "peer_interactions": 1,
            "knowledge_gained": interaction_data.get("value_gained", 0.4),
            "comprehension_score": interaction_data.get("quality_score", 0.7),
        }
        
        return await self.track_learning_progress(peer_progress)
    
    async def handle_achievement_unlock(self, achievement_data: Dict[str, Any]) -> Optional[str]:
        """Handle achievement unlock and award bonus XP"""
        achievement_progress = {
            **achievement_data,
            "action_type": "achievement_unlock",
            "learning_type": "mastery",
            "knowledge_gained": 0.8,
            "comprehension_score": 1.0,
            "retention_factor": 1.5,  # Achievement bonus
            "difficulty": achievement_data.get("difficulty", 1.2),
        }
        
        return await self.track_learning_progress(achievement_progress)
    
    def get_learning_analytics(self, user_id: str = None) -> Dict[str, Any]:
        """Get learning analytics for the user"""
        if not user_id and self.user_data:
            user_id = self.user_data["userId"]
        
        if not user_id:
            return {}
        
        conn = sqlite3.connect('levelup_integration.db')
        cursor = conn.cursor()
        
        # Learning XP by action type
        cursor.execute('''
            SELECT action_type, SUM(entropy_delta) as total_xp, COUNT(*) as count
            FROM learning_xp_transactions
            WHERE user_id = ?
            GROUP BY action_type
        ''', (user_id,))
        
        action_stats = {row[0]: {"total_xp": row[1], "count": row[2]} for row in cursor.fetchall()}
        
        # Overall learning stats
        cursor.execute('''
            SELECT 
                SUM(entropy_delta) as total_xp,
                COUNT(*) as total_transactions,
                AVG(entropy_delta) as avg_xp_per_action,
                COUNT(CASE WHEN synced = TRUE THEN 1 END) as synced_count
            FROM learning_xp_transactions
            WHERE user_id = ?
        ''', (user_id,))
        
        overall = cursor.fetchone()
        
        # Recent learning progress
        cursor.execute('''
            SELECT course_id, module_id, AVG(comprehension_score) as avg_comprehension,
                   SUM(time_spent) as total_time, MAX(created_at) as last_activity
            FROM learning_progress
            WHERE user_id = ?
            GROUP BY course_id, module_id
            ORDER BY last_activity DESC
            LIMIT 10
        ''', (user_id,))
        
        recent_progress = [
            {
                "course_id": row[0],
                "module_id": row[1],
                "avg_comprehension": row[2],
                "total_time": row[3],
                "last_activity": row[4]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return {
            "total_learning_xp": overall[0] or 0,
            "total_learning_actions": overall[1] or 0,
            "avg_xp_per_action": overall[2] or 0,
            "synced_transactions": overall[3] or 0,
            "action_breakdown": action_stats,
            "recent_progress": recent_progress,
            "learning_velocity": len(recent_progress) / 7 if recent_progress else 0  # actions per week
        }

# Global integration instance
integration = LevelUpIntegration()

# Integration functions for LevelUp Academy
async def initialize_integration(email: str, password: str = None, token: str = None) -> bool:
    """Initialize the unified integration"""
    return await integration.authenticate_user(email, password, token)

async def track_course_completion(course_data: Dict[str, Any]) -> Optional[str]:
    """Track course completion XP"""
    return await integration.handle_course_completion(course_data)

async def track_quiz_completion(quiz_data: Dict[str, Any]) -> Optional[str]:
    """Track quiz completion XP"""
    return await integration.handle_quiz_completion(quiz_data)

async def track_study_session(session_data: Dict[str, Any]) -> Optional[str]:
    """Track study session XP"""
    return await integration.handle_study_session(session_data)

async def track_peer_interaction(interaction_data: Dict[str, Any]) -> Optional[str]:
    """Track peer interaction XP"""
    return await integration.handle_peer_interaction(interaction_data)

async def track_achievement_unlock(achievement_data: Dict[str, Any]) -> Optional[str]:
    """Track achievement unlock XP"""
    return await integration.handle_achievement_unlock(achievement_data)

def get_integration_status() -> Dict[str, Any]:
    """Get integration status"""
    return {
        "authenticated": integration.auth_token is not None,
        "user": integration.user_data,
        "learning_analytics": integration.get_learning_analytics()
    }

if __name__ == "__main__":
    # Test the integration
    async def test_integration():
        # Test authentication
        success = await initialize_integration("student@xpengine.org", token="test-token")
        print(f"Authentication: {'Success' if success else 'Failed'}")
        
        if success:
            # Test learning XP tracking
            course_data = {
                "course_id": "intro-physics",
                "title": "Introduction to Physics",
                "final_score": 0.92,
                "difficulty": 1.8,
                "time_spent": 240,  # 4 hours
                "comprehension_score": 0.92
            }
            
            xp_id = await track_course_completion(course_data)
            print(f"Course Completion XP Transaction ID: {xp_id}")
            
            # Test quiz completion
            quiz_data = {
                "course_id": "intro-physics",
                "quiz_id": "chapter-1-quiz",
                "score": 0.85,
                "difficulty": 1.2,
                "time_spent": 15
            }
            
            quiz_xp_id = await track_quiz_completion(quiz_data)
            print(f"Quiz Completion XP Transaction ID: {quiz_xp_id}")
            
            # Get learning analytics
            analytics = get_integration_status()
            print(f"Learning Analytics: {analytics}")
    
    asyncio.run(test_integration())