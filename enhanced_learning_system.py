#!/usr/bin/env python3
"""
Enhanced LevelUp Academy Learning System
Integrated with Extropy Unified System for XP tracking and adaptive learning
"""

import asyncio
import json
import logging
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import random
import math

# Import unified integration
sys.path.append(os.path.dirname(__file__))
from unified_integration import (
    initialize_integration, track_course_completion, track_quiz_completion,
    track_study_session, track_peer_interaction, track_achievement_unlock,
    get_integration_status
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdaptiveLearningEngine:
    """AI-powered adaptive learning engine for personalized education"""
    
    def __init__(self):
        self.db_path = 'enhanced_learning.db'
        self.unified_integration_active = False
        self.current_user = None
        self.init_database()
    
    def init_database(self):
        """Initialize enhanced learning database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Courses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                difficulty_level REAL DEFAULT 1.0,
                estimated_hours INTEGER DEFAULT 10,
                prerequisites TEXT,
                learning_objectives TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Modules table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS modules (
                id TEXT PRIMARY KEY,
                course_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                module_order INTEGER,
                estimated_minutes INTEGER DEFAULT 60,
                difficulty_multiplier REAL DEFAULT 1.0,
                FOREIGN KEY (course_id) REFERENCES courses (id)
            )
        ''')
        
        # Lessons table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lessons (
                id TEXT PRIMARY KEY,
                module_id TEXT NOT NULL,
                title TEXT NOT NULL,
                content_type TEXT DEFAULT 'text',
                content TEXT,
                lesson_order INTEGER,
                estimated_minutes INTEGER DEFAULT 15,
                difficulty_rating REAL DEFAULT 1.0,
                FOREIGN KEY (module_id) REFERENCES modules (id)
            )
        ''')
        
        # User progress table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                course_id TEXT,
                module_id TEXT,
                lesson_id TEXT,
                completion_percentage REAL DEFAULT 0,
                mastery_level REAL DEFAULT 0,
                time_spent INTEGER DEFAULT 0,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                xp_earned REAL DEFAULT 0,
                xp_transaction_id TEXT
            )
        ''')
        
        # Adaptive assessments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assessments (
                id TEXT PRIMARY KEY,
                course_id TEXT,
                module_id TEXT,
                lesson_id TEXT,
                question_type TEXT DEFAULT 'multiple_choice',
                question TEXT NOT NULL,
                options TEXT,
                correct_answer TEXT NOT NULL,
                difficulty REAL DEFAULT 1.0,
                cognitive_load REAL DEFAULT 0.5,
                bloom_taxonomy_level TEXT DEFAULT 'remember'
            )
        ''')
        
        # Learning sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_end TIMESTAMP,
                focus_score REAL DEFAULT 0.8,
                engagement_level REAL DEFAULT 0.7,
                concepts_learned INTEGER DEFAULT 0,
                xp_earned REAL DEFAULT 0,
                session_quality REAL DEFAULT 0.8
            )
        ''')
        
        # Knowledge graph table  
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_graph (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                concept_id TEXT NOT NULL,
                concept_name TEXT NOT NULL,
                mastery_level REAL DEFAULT 0.0,
                confidence_score REAL DEFAULT 0.0,
                last_reviewed TIMESTAMP,
                review_count INTEGER DEFAULT 0,
                forgetting_curve REAL DEFAULT 0.5,
                prerequisite_concepts TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Initialize with sample data
        self.create_sample_courses()
    
    def create_sample_courses(self):
        """Create sample courses for demonstration"""
        sample_courses = [
            {
                "id": "intro-physics",
                "title": "Introduction to Physics",
                "description": "Fundamental concepts in classical physics",
                "difficulty_level": 1.5,
                "estimated_hours": 40,
                "learning_objectives": "Understand motion, forces, energy, and momentum"
            },
            {
                "id": "quantum-mechanics",
                "title": "Quantum Mechanics Fundamentals", 
                "description": "Basic principles of quantum mechanics",
                "difficulty_level": 2.5,
                "estimated_hours": 60,
                "prerequisites": "intro-physics",
                "learning_objectives": "Understand wave-particle duality, uncertainty principle, Schrödinger equation"
            },
            {
                "id": "complexity-science",
                "title": "Complexity Science",
                "description": "Study of complex adaptive systems",
                "difficulty_level": 2.0,
                "estimated_hours": 35,
                "learning_objectives": "Understand emergence, self-organization, network theory"
            }
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for course in sample_courses:
            cursor.execute('''
                INSERT OR IGNORE INTO courses 
                (id, title, description, difficulty_level, estimated_hours, prerequisites, learning_objectives)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                course["id"], course["title"], course["description"],
                course["difficulty_level"], course["estimated_hours"],
                course.get("prerequisites", ""), course["learning_objectives"]
            ))
        
        # Add sample modules for intro-physics
        physics_modules = [
            {
                "id": "motion-kinematics",
                "course_id": "intro-physics",
                "title": "Motion and Kinematics",
                "description": "Basic motion concepts",
                "module_order": 1,
                "estimated_minutes": 120
            },
            {
                "id": "forces-dynamics",
                "course_id": "intro-physics", 
                "title": "Forces and Dynamics",
                "description": "Newton's laws and force analysis",
                "module_order": 2,
                "estimated_minutes": 180
            },
            {
                "id": "energy-work",
                "course_id": "intro-physics",
                "title": "Energy and Work",
                "description": "Conservation of energy principles",
                "module_order": 3,
                "estimated_minutes": 150
            }
        ]
        
        for module in physics_modules:
            cursor.execute('''
                INSERT OR IGNORE INTO modules
                (id, course_id, title, description, module_order, estimated_minutes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                module["id"], module["course_id"], module["title"],
                module["description"], module["module_order"], module["estimated_minutes"]
            ))
        
        conn.commit()
        conn.close()
    
    async def authenticate_user(self, email: str, password: str = None, token: str = None) -> bool:
        """Authenticate user with unified system"""
        self.unified_integration_active = await initialize_integration(email, password, token)
        
        if self.unified_integration_active:
            status = get_integration_status()
            self.current_user = status.get("user", {}).get("userId")
            logger.info(f"LevelUp Academy authenticated: {email}")
            return True
        
        return False
    
    def get_personalized_learning_path(self, user_id: str, course_id: str) -> List[Dict[str, Any]]:
        """Generate personalized learning path based on user's knowledge graph"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get user's current knowledge state
        cursor.execute('''
            SELECT concept_id, concept_name, mastery_level, confidence_score
            FROM knowledge_graph
            WHERE user_id = ?
            ORDER BY mastery_level ASC
        ''', (user_id,))
        
        knowledge_state = cursor.fetchall()
        
        # Get course modules
        cursor.execute('''
            SELECT id, title, description, estimated_minutes, difficulty_multiplier
            FROM modules
            WHERE course_id = ?
            ORDER BY module_order
        ''', (course_id,))
        
        modules = cursor.fetchall()
        
        # Get user's progress
        cursor.execute('''
            SELECT module_id, completion_percentage, mastery_level
            FROM user_progress
            WHERE user_id = ? AND course_id = ?
        ''', (user_id, course_id))
        
        progress = {row[0]: {"completion": row[1], "mastery": row[2]} for row in cursor.fetchall()}
        
        conn.close()
        
        # Generate adaptive learning path
        learning_path = []
        
        for module in modules:
            module_id, title, description, est_minutes, difficulty = module
            user_progress = progress.get(module_id, {"completion": 0, "mastery": 0})
            
            # Calculate adaptive difficulty based on user's current mastery
            avg_mastery = sum(k[2] for k in knowledge_state) / len(knowledge_state) if knowledge_state else 0.5
            adaptive_difficulty = difficulty * (1 + (0.5 - avg_mastery))
            
            # Estimate time based on user's learning velocity
            estimated_time = est_minutes * (1 + (1 - avg_mastery) * 0.5)
            
            learning_path.append({
                "module_id": module_id,
                "title": title,
                "description": description,
                "estimated_minutes": int(estimated_time),
                "adaptive_difficulty": round(adaptive_difficulty, 2),
                "current_completion": user_progress["completion"],
                "current_mastery": user_progress["mastery"],
                "recommended_next": user_progress["completion"] < 100
            })
        
        return learning_path
    
    async def start_learning_session(self, user_id: str, module_id: str) -> Dict[str, Any]:
        """Start an adaptive learning session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create learning session record
        cursor.execute('''
            INSERT INTO learning_sessions (user_id, session_start)
            VALUES (?, ?)
        ''', (user_id, datetime.now()))
        
        session_id = cursor.lastrowid
        
        # Get module details
        cursor.execute('''
            SELECT m.title, m.description, m.estimated_minutes, c.title as course_title
            FROM modules m
            JOIN courses c ON m.course_id = c.id
            WHERE m.id = ?
        ''', (module_id,))
        
        module_info = cursor.fetchone()
        
        conn.commit()
        conn.close()
        
        if module_info:
            return {
                "session_id": session_id,
                "module_id": module_id,
                "module_title": module_info[0],
                "description": module_info[1],
                "estimated_minutes": module_info[2],
                "course_title": module_info[3],
                "start_time": datetime.now().isoformat()
            }
        
        return {}
    
    async def complete_learning_session(self, session_id: int, session_data: Dict[str, Any]) -> Optional[str]:
        """Complete learning session and track XP"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update session record
        cursor.execute('''
            UPDATE learning_sessions
            SET session_end = ?, focus_score = ?, engagement_level = ?,
                concepts_learned = ?, session_quality = ?
            WHERE id = ?
        ''', (
            datetime.now(),
            session_data.get("focus_score", 0.8),
            session_data.get("engagement_level", 0.7),
            session_data.get("concepts_learned", 1),
            session_data.get("session_quality", 0.8),
            session_id
        ))
        
        # Get session details for XP calculation
        cursor.execute('''
            SELECT user_id, session_start, session_end, focus_score, engagement_level, 
                   concepts_learned, session_quality
            FROM learning_sessions
            WHERE id = ?
        ''', (session_id,))
        
        session_record = cursor.fetchone()
        
        if session_record and self.unified_integration_active:
            user_id, start_time, end_time, focus, engagement, concepts, quality = session_record
            
            # Calculate session duration
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
            duration_minutes = (end_dt - start_dt).total_seconds() / 60
            
            # Track XP for study session
            study_session_data = {
                "user_id": user_id,
                "module_id": session_data.get("module_id"),
                "title": session_data.get("module_title", "Learning Session"),
                "duration": int(duration_minutes),
                "engagement_score": engagement,
                "progress_made": concepts * 0.3,  # Each concept = 30% progress
                "difficulty": session_data.get("difficulty", 1.0),
                "comprehension_score": quality
            }
            
            xp_transaction_id = await track_study_session(study_session_data)
            
            # Update session with XP transaction ID
            if xp_transaction_id:
                cursor.execute('''
                    UPDATE learning_sessions
                    SET xp_earned = ?
                    WHERE id = ?
                ''', (session_data.get("xp_earned", 10.0), session_id))
            
            conn.commit()
            conn.close()
            
            return xp_transaction_id
        
        conn.close()
        return None
    
    async def take_adaptive_quiz(self, user_id: str, module_id: str, num_questions: int = 5) -> Dict[str, Any]:
        """Generate and administer adaptive quiz"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get user's current mastery level for the module
        cursor.execute('''
            SELECT mastery_level FROM user_progress
            WHERE user_id = ? AND module_id = ?
        ''', (user_id, module_id))
        
        result = cursor.fetchone()
        current_mastery = result[0] if result else 0.0
        
        # Generate adaptive questions based on mastery level
        questions = self.generate_adaptive_questions(module_id, current_mastery, num_questions)
        
        conn.close()
        
        return {
            "quiz_id": f"quiz_{module_id}_{int(datetime.now().timestamp())}",
            "module_id": module_id,
            "questions": questions,
            "adaptive_difficulty": current_mastery + 0.2,  # Slightly above current level
            "time_limit_minutes": num_questions * 3  # 3 minutes per question
        }
    
    def generate_adaptive_questions(self, module_id: str, mastery_level: float, num_questions: int) -> List[Dict[str, Any]]:
        """Generate adaptive questions based on user's mastery level"""
        # This would normally pull from a question bank, for demo we'll generate sample questions
        
        question_templates = {
            "motion-kinematics": [
                {
                    "question": "An object moves with constant velocity. What is its acceleration?",
                    "options": ["0 m/s²", "9.8 m/s²", "Velocity²", "Cannot be determined"],
                    "correct": "0 m/s²",
                    "difficulty": 0.3,
                    "bloom_level": "understand"
                },
                {
                    "question": "If an object travels 100m in 10 seconds, what is its average velocity?",
                    "options": ["1 m/s", "10 m/s", "100 m/s", "1000 m/s"],
                    "correct": "10 m/s",
                    "difficulty": 0.5,
                    "bloom_level": "apply"
                },
                {
                    "question": "Analyze the motion of a projectile at the peak of its trajectory.",
                    "options": ["Zero velocity", "Zero horizontal velocity", "Zero vertical velocity", "Maximum acceleration"],
                    "correct": "Zero vertical velocity",
                    "difficulty": 0.8,
                    "bloom_level": "analyze"
                }
            ]
        }
        
        available_questions = question_templates.get(module_id, [])
        
        # Select questions based on mastery level
        selected_questions = []
        
        for question in available_questions[:num_questions]:
            # Adjust difficulty based on mastery
            adjusted_difficulty = question["difficulty"] + (mastery_level - 0.5) * 0.3
            adjusted_difficulty = max(0.1, min(1.0, adjusted_difficulty))
            
            selected_questions.append({
                **question,
                "id": f"q_{len(selected_questions) + 1}",
                "adaptive_difficulty": round(adjusted_difficulty, 2)
            })
        
        return selected_questions
    
    async def submit_quiz_answers(self, user_id: str, quiz_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process quiz submission and calculate results"""
        answers = quiz_data.get("answers", {})
        questions = quiz_data.get("questions", [])
        
        correct_count = 0
        total_questions = len(questions)
        difficulty_sum = 0
        
        for question in questions:
            question_id = question["id"]
            user_answer = answers.get(question_id)
            
            if user_answer == question["correct"]:
                correct_count += 1
            
            difficulty_sum += question["adaptive_difficulty"]
        
        # Calculate performance metrics
        score = correct_count / total_questions if total_questions > 0 else 0
        avg_difficulty = difficulty_sum / total_questions if total_questions > 0 else 1.0
        
        # Track XP for quiz completion
        if self.unified_integration_active:
            quiz_completion_data = {
                "user_id": user_id,
                "course_id": quiz_data.get("course_id"),
                "module_id": quiz_data.get("module_id"),
                "quiz_id": quiz_data.get("quiz_id"),
                "score": score,
                "difficulty": avg_difficulty,
                "time_spent": quiz_data.get("time_taken", 15)
            }
            
            xp_transaction_id = await track_quiz_completion(quiz_completion_data)
        else:
            xp_transaction_id = None
        
        # Update user progress
        self.update_user_progress(user_id, quiz_data.get("module_id"), score, avg_difficulty)
        
        return {
            "score": score,
            "correct_answers": correct_count,
            "total_questions": total_questions,
            "difficulty_level": avg_difficulty,
            "performance_rating": self.calculate_performance_rating(score, avg_difficulty),
            "xp_transaction_id": xp_transaction_id,
            "recommendations": self.generate_learning_recommendations(score, avg_difficulty)
        }
    
    def update_user_progress(self, user_id: str, module_id: str, score: float, difficulty: float):
        """Update user progress based on quiz performance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate new mastery level
        mastery_gain = score * difficulty * 0.3  # 30% max mastery gain per quiz
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_progress
            (user_id, module_id, completion_percentage, mastery_level, last_accessed)
            VALUES (?, ?, 
                COALESCE((SELECT completion_percentage FROM user_progress 
                         WHERE user_id = ? AND module_id = ?), 0) + ?,
                COALESCE((SELECT mastery_level FROM user_progress 
                         WHERE user_id = ? AND module_id = ?), 0) + ?,
                ?)
        ''', (user_id, module_id, user_id, module_id, score * 20, 
              user_id, module_id, mastery_gain, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def calculate_performance_rating(self, score: float, difficulty: float) -> str:
        """Calculate performance rating based on score and difficulty"""
        performance_index = score * (1 + difficulty)
        
        if performance_index >= 1.8:
            return "Exceptional"
        elif performance_index >= 1.4:
            return "Excellent"
        elif performance_index >= 1.0:
            return "Good"
        elif performance_index >= 0.6:
            return "Satisfactory"
        else:
            return "Needs Improvement"
    
    def generate_learning_recommendations(self, score: float, difficulty: float) -> List[str]:
        """Generate personalized learning recommendations"""
        recommendations = []
        
        if score < 0.6:
            recommendations.append("Review the fundamental concepts before proceeding")
            recommendations.append("Consider additional practice problems")
        elif score < 0.8:
            recommendations.append("Good progress! Focus on areas where you struggled")
            recommendations.append("Try some challenging practice questions")
        else:
            recommendations.append("Excellent work! You're ready for advanced topics")
            recommendations.append("Consider exploring related concepts")
        
        if difficulty < 0.5:
            recommendations.append("Try more challenging material to accelerate learning")
        elif difficulty > 1.5:
            recommendations.append("Take time to consolidate your understanding")
        
        return recommendations
    
    async def complete_course(self, user_id: str, course_id: str) -> Optional[str]:
        """Handle course completion and award XP"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get course details and user progress
        cursor.execute('''
            SELECT c.title, c.difficulty_level, c.estimated_hours,
                   AVG(up.mastery_level) as avg_mastery,
                   SUM(up.time_spent) as total_time
            FROM courses c
            LEFT JOIN user_progress up ON c.id = up.course_id AND up.user_id = ?
            WHERE c.id = ?
            GROUP BY c.id
        ''', (user_id, course_id))
        
        result = cursor.fetchone()
        
        if result and self.unified_integration_active:
            title, difficulty, est_hours, avg_mastery, total_time = result
            
            course_completion_data = {
                "user_id": user_id,
                "course_id": course_id,
                "title": title,
                "final_score": min(1.0, avg_mastery or 0.7),
                "difficulty": difficulty,
                "time_spent": total_time or (est_hours * 60),
                "comprehension_score": min(1.0, avg_mastery or 0.7)
            }
            
            xp_transaction_id = await track_course_completion(course_completion_data)
            
            conn.close()
            return xp_transaction_id
        
        conn.close()
        return None
    
    def get_learning_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive learning dashboard data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # User's enrolled courses and progress
        cursor.execute('''
            SELECT c.id, c.title, c.difficulty_level,
                   AVG(up.completion_percentage) as avg_completion,
                   AVG(up.mastery_level) as avg_mastery,
                   SUM(up.time_spent) as total_time
            FROM courses c
            LEFT JOIN user_progress up ON c.id = up.course_id AND up.user_id = ?
            GROUP BY c.id, c.title, c.difficulty_level
            HAVING avg_completion > 0 OR total_time > 0
        ''', (user_id,))
        
        courses = [
            {
                "course_id": row[0],
                "title": row[1],
                "difficulty": row[2],
                "completion": row[3] or 0,
                "mastery": row[4] or 0,
                "time_spent": row[5] or 0
            }
            for row in cursor.fetchall()
        ]
        
        # Recent learning sessions
        cursor.execute('''
            SELECT session_start, session_end, focus_score, engagement_level,
                   concepts_learned, xp_earned
            FROM learning_sessions
            WHERE user_id = ?
            ORDER BY session_start DESC
            LIMIT 10
        ''', (user_id,))
        
        recent_sessions = [
            {
                "start": row[0],
                "end": row[1],
                "focus": row[2],
                "engagement": row[3],
                "concepts": row[4],
                "xp": row[5] or 0
            }
            for row in cursor.fetchall()
        ]
        
        # Knowledge graph summary
        cursor.execute('''
            SELECT COUNT(*) as concepts_learned,
                   AVG(mastery_level) as avg_mastery,
                   AVG(confidence_score) as avg_confidence
            FROM knowledge_graph
            WHERE user_id = ?
        ''', (user_id,))
        
        knowledge_stats = cursor.fetchone()
        
        conn.close()
        
        # Get integration status
        integration_status = get_integration_status()
        
        return {
            "user_id": user_id,
            "courses_in_progress": courses,
            "recent_sessions": recent_sessions,
            "knowledge_stats": {
                "concepts_learned": knowledge_stats[0] or 0,
                "avg_mastery": knowledge_stats[1] or 0,
                "avg_confidence": knowledge_stats[2] or 0
            },
            "integration_status": integration_status,
            "learning_velocity": len(recent_sessions) / 7 if recent_sessions else 0  # sessions per week
        }

# Global learning engine instance
learning_engine = AdaptiveLearningEngine()

# CLI-like functions for the enhanced learning system
async def authenticate_learner(email: str, password: str = None, token: str = None) -> bool:
    """Authenticate learner with unified system"""
    return await learning_engine.authenticate_user(email, password, token)

def get_available_courses() -> List[Dict[str, Any]]:
    """Get list of available courses"""
    conn = sqlite3.connect(learning_engine.db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, title, description, difficulty_level, estimated_hours, learning_objectives
        FROM courses
        ORDER BY difficulty_level
    ''')
    
    courses = [
        {
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "difficulty": row[3],
            "estimated_hours": row[4],
            "objectives": row[5]
        }
        for row in cursor.fetchall()
    ]
    
    conn.close()
    return courses

async def start_course(user_id: str, course_id: str) -> Dict[str, Any]:
    """Start a course and get personalized learning path"""
    learning_path = learning_engine.get_personalized_learning_path(user_id, course_id)
    return {
        "course_id": course_id,
        "learning_path": learning_path,
        "estimated_completion": sum(m["estimated_minutes"] for m in learning_path)
    }

async def study_module(user_id: str, module_id: str, duration_minutes: int = 30) -> Dict[str, Any]:
    """Simulate studying a module"""
    session = await learning_engine.start_learning_session(user_id, module_id)
    
    # Simulate learning session
    session_data = {
        "module_id": module_id,
        "module_title": session.get("module_title"),
        "focus_score": 0.7 + random.random() * 0.3,
        "engagement_level": 0.6 + random.random() * 0.4,
        "concepts_learned": random.randint(1, 3),
        "session_quality": 0.7 + random.random() * 0.3,
        "difficulty": 1.0 + random.random()
    }
    
    xp_id = await learning_engine.complete_learning_session(session["session_id"], session_data)
    
    return {
        "session_completed": True,
        "duration_minutes": duration_minutes,
        "xp_transaction_id": xp_id,
        **session_data
    }

async def take_quiz(user_id: str, module_id: str) -> Dict[str, Any]:
    """Take an adaptive quiz for a module"""
    quiz = await learning_engine.take_adaptive_quiz(user_id, module_id)
    
    # Simulate quiz answers (in real implementation, user would provide answers)
    answers = {}
    for question in quiz["questions"]:
        # Simulate performance based on difficulty
        difficulty = question["adaptive_difficulty"]
        success_rate = max(0.2, 1.0 - difficulty * 0.6)
        
        if random.random() < success_rate:
            answers[question["id"]] = question["correct"]
        else:
            # Pick wrong answer
            options = [opt for opt in question["options"] if opt != question["correct"]]
            answers[question["id"]] = random.choice(options) if options else question["correct"]
    
    # Submit quiz
    quiz_data = {
        **quiz,
        "answers": answers,
        "time_taken": len(quiz["questions"]) * 2  # 2 minutes per question
    }
    
    results = await learning_engine.submit_quiz_answers(user_id, quiz_data)
    
    return {
        "quiz_completed": True,
        "quiz_results": results,
        "questions_answered": len(answers)
    }

def show_dashboard(user_id: str) -> Dict[str, Any]:
    """Show learning dashboard"""
    return learning_engine.get_learning_dashboard(user_id)

if __name__ == "__main__":
    async def demo_enhanced_learning():
        print("🎓 Enhanced LevelUp Academy Learning System Demo")
        print("=" * 60)
        
        # Authenticate
        success = await authenticate_learner("student@xpengine.org", token="demo-token")
        print(f"Authentication: {'✅ Success' if success else '❌ Failed'}")
        
        if not success:
            return
        
        user_id = "demo_student_123"
        
        # Show available courses
        courses = get_available_courses()
        print(f"\n📚 Available Courses ({len(courses)}):")
        for course in courses:
            print(f"  • {course['title']} (Difficulty: {course['difficulty']}/3.0)")
        
        # Start a course
        course_id = "intro-physics"
        course_start = await start_course(user_id, course_id)
        print(f"\n🚀 Started Course: {course_id}")
        print(f"Learning Path: {len(course_start['learning_path'])} modules")
        
        # Study a module
        module_id = "motion-kinematics"
        study_result = await study_module(user_id, module_id, 45)
        print(f"\n📖 Study Session Completed:")
        print(f"  Focus Score: {study_result['focus_score']:.2f}")
        print(f"  XP Transaction: {study_result.get('xp_transaction_id', 'Local only')}")
        
        # Take a quiz
        quiz_result = await take_quiz(user_id, module_id)
        print(f"\n🧪 Quiz Completed:")
        results = quiz_result['quiz_results']
        print(f"  Score: {results['score']:.2%}")
        print(f"  Performance: {results['performance_rating']}")
        print(f"  XP Transaction: {results.get('xp_transaction_id', 'Local only')}")
        
        # Show dashboard
        dashboard = show_dashboard(user_id)
        print(f"\n📊 Learning Dashboard:")
        print(f"  Courses in Progress: {len(dashboard['courses_in_progress'])}")
        print(f"  Recent Sessions: {len(dashboard['recent_sessions'])}")
        print(f"  Concepts Learned: {dashboard['knowledge_stats']['concepts_learned']}")
        print(f"  Learning Velocity: {dashboard['learning_velocity']:.1f} sessions/week")
        
        print("\n🎯 Demo completed! Enhanced learning system with XP tracking active.")
    
    asyncio.run(demo_enhanced_learning())