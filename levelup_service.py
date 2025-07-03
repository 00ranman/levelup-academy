#!/usr/bin/env python3
"""
LevelUp Academy Service
Educational platform integrated with Extropy unified ecosystem
Port: 3004
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

import aiohttp
from aiohttp import web, WSMsgType
import aiohttp_cors

# Import enhanced learning system
sys.path.append(os.path.dirname(__file__))
from enhanced_learning_system import (
    learning_engine, authenticate_learner, get_available_courses,
    start_course, study_module, take_quiz, show_dashboard
)
from unified_integration import get_integration_status

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LevelUpAcademyService:
    def __init__(self):
        self.port = int(os.getenv("LEVELUP_PORT", 3004))
        self.gateway_url = os.getenv("GATEWAY_URL", "http://localhost:3000")
        self.app = web.Application()
        self.active_sessions = {}  # WebSocket connections
        
        # Setup routes
        self.setup_routes()
        
        # Setup CORS
        self.setup_cors()
    
    def setup_routes(self):
        """Setup HTTP routes"""
        self.app.router.add_get('/', self.index)
        self.app.router.add_get('/api/health', self.health_check)
        
        # Authentication routes
        self.app.router.add_post('/api/auth/login', self.login)
        self.app.router.add_get('/api/auth/status', self.auth_status)
        
        # Course management routes
        self.app.router.add_get('/api/courses', self.get_courses)
        self.app.router.add_post('/api/courses/{course_id}/enroll', self.enroll_course)
        self.app.router.add_get('/api/courses/{course_id}/path', self.get_learning_path)
        
        # Learning activity routes
        self.app.router.add_post('/api/study/session', self.create_study_session)
        self.app.router.add_post('/api/quiz/take', self.take_adaptive_quiz)
        self.app.router.add_post('/api/quiz/submit', self.submit_quiz)
        
        # Progress and analytics routes
        self.app.router.add_get('/api/progress/dashboard', self.get_dashboard)
        self.app.router.add_get('/api/analytics/learning', self.get_learning_analytics)
        
        # XP and achievement routes
        self.app.router.add_post('/api/xp/track', self.track_learning_xp)
        self.app.router.add_get('/api/achievements', self.get_achievements)
        
        # WebSocket route
        self.app.router.add_get('/ws/{user_id}', self.websocket_handler)
    
    def setup_cors(self):
        """Setup CORS for cross-origin requests"""
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # Add CORS to all routes
        for route in list(self.app.router.routes()):
            cors.add(route)
    
    async def index(self, request):
        """Service information endpoint"""
        return web.json_response({
            "service": "LevelUp Academy",
            "description": "Adaptive learning platform with physics-based XP tracking",
            "version": "3.0",
            "port": self.port,
            "features": [
                "Adaptive Learning Engine",
                "Personalized Learning Paths", 
                "Real-time XP Tracking",
                "Knowledge Graph Mapping",
                "Peer Learning Networks",
                "Achievement System"
            ],
            "integration": {
                "unified_auth": True,
                "xp_ledger": True,
                "contribution_tokens": True,
                "real_time_updates": True
            },
            "endpoints": {
                "health": "/api/health",
                "courses": "/api/courses",
                "dashboard": "/api/progress/dashboard",
                "websocket": "/ws/{user_id}"
            }
        })
    
    async def health_check(self, request):
        """Health check endpoint"""
        try:
            # Check database connectivity
            dashboard = show_dashboard("health_check")
            
            # Check integration status
            integration_status = get_integration_status()
            
            return web.json_response({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "database": "connected",
                "integration": {
                    "unified_auth": integration_status.get("authenticated", False),
                    "xp_tracking": "available"
                },
                "learning_engine": "operational",
                "active_sessions": len(self.active_sessions)
            })
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return web.json_response({
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }, status=500)
    
    async def login(self, request):
        """Authenticate user with unified system"""
        try:
            data = await request.json()
            email = data.get("email")
            password = data.get("password")
            token = data.get("token")
            
            if not email:
                return web.json_response({
                    "error": "Email required"
                }, status=400)
            
            # Authenticate with unified system
            success = await authenticate_learner(email, password, token)
            
            if success:
                integration_status = get_integration_status()
                
                return web.json_response({
                    "success": True,
                    "message": "Authentication successful",
                    "user": integration_status.get("user"),
                    "learning_analytics": integration_status.get("learning_analytics")
                })
            else:
                return web.json_response({
                    "error": "Authentication failed"
                }, status=401)
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return web.json_response({
                "error": "Authentication error"
            }, status=500)
    
    async def auth_status(self, request):
        """Get current authentication status"""
        integration_status = get_integration_status()
        
        return web.json_response({
            "authenticated": integration_status.get("authenticated", False),
            "user": integration_status.get("user"),
            "learning_analytics": integration_status.get("learning_analytics")
        })
    
    async def get_courses(self, request):
        """Get available courses"""
        try:
            courses = get_available_courses()
            
            return web.json_response({
                "courses": courses,
                "total_courses": len(courses)
            })
            
        except Exception as e:
            logger.error(f"Get courses error: {e}")
            return web.json_response({
                "error": "Failed to retrieve courses"
            }, status=500)
    
    async def enroll_course(self, request):
        """Enroll user in a course"""
        try:
            course_id = request.match_info['course_id']
            user_id = request.headers.get('X-User-ID')
            
            if not user_id:
                return web.json_response({
                    "error": "User ID required"
                }, status=400)
            
            course_data = await start_course(user_id, course_id)
            
            # Broadcast enrollment update
            await self.broadcast_update(user_id, {
                "type": "course_enrolled",
                "course_id": course_id,
                "learning_path": course_data["learning_path"]
            })
            
            return web.json_response({
                "success": True,
                "message": f"Enrolled in course {course_id}",
                "course_data": course_data
            })
            
        except Exception as e:
            logger.error(f"Course enrollment error: {e}")
            return web.json_response({
                "error": "Enrollment failed"
            }, status=500)
    
    async def get_learning_path(self, request):
        """Get personalized learning path for a course"""
        try:
            course_id = request.match_info['course_id']
            user_id = request.headers.get('X-User-ID')
            
            if not user_id:
                return web.json_response({
                    "error": "User ID required"
                }, status=400)
            
            learning_path = learning_engine.get_personalized_learning_path(user_id, course_id)
            
            return web.json_response({
                "course_id": course_id,
                "learning_path": learning_path,
                "total_modules": len(learning_path),
                "estimated_completion": sum(m["estimated_minutes"] for m in learning_path)
            })
            
        except Exception as e:
            logger.error(f"Learning path error: {e}")
            return web.json_response({
                "error": "Failed to generate learning path"
            }, status=500)
    
    async def create_study_session(self, request):
        """Create and complete a study session"""
        try:
            data = await request.json()
            user_id = request.headers.get('X-User-ID')
            module_id = data.get("module_id")
            duration = data.get("duration_minutes", 30)
            
            if not all([user_id, module_id]):
                return web.json_response({
                    "error": "User ID and module ID required"
                }, status=400)
            
            # Simulate study session
            result = await study_module(user_id, module_id, duration)
            
            # Broadcast study update
            await self.broadcast_update(user_id, {
                "type": "study_session_completed",
                "module_id": module_id,
                "xp_earned": result.get("xp_transaction_id") is not None,
                "focus_score": result["focus_score"]
            })
            
            return web.json_response({
                "success": True,
                "study_session": result
            })
            
        except Exception as e:
            logger.error(f"Study session error: {e}")
            return web.json_response({
                "error": "Study session failed"
            }, status=500)
    
    async def take_adaptive_quiz(self, request):
        """Generate an adaptive quiz"""
        try:
            data = await request.json()
            user_id = request.headers.get('X-User-ID')
            module_id = data.get("module_id")
            num_questions = data.get("num_questions", 5)
            
            if not all([user_id, module_id]):
                return web.json_response({
                    "error": "User ID and module ID required"
                }, status=400)
            
            quiz = await learning_engine.take_adaptive_quiz(user_id, module_id, num_questions)
            
            return web.json_response({
                "success": True,
                "quiz": quiz
            })
            
        except Exception as e:
            logger.error(f"Quiz generation error: {e}")
            return web.json_response({
                "error": "Quiz generation failed"
            }, status=500)
    
    async def submit_quiz(self, request):
        """Submit quiz answers and get results"""
        try:
            data = await request.json()
            user_id = request.headers.get('X-User-ID')
            
            if not user_id:
                return web.json_response({
                    "error": "User ID required"
                }, status=400)
            
            results = await learning_engine.submit_quiz_answers(user_id, data)
            
            # Broadcast quiz completion
            await self.broadcast_update(user_id, {
                "type": "quiz_completed",
                "module_id": data.get("module_id"),
                "score": results["score"],
                "performance": results["performance_rating"],
                "xp_earned": results.get("xp_transaction_id") is not None
            })
            
            return web.json_response({
                "success": True,
                "results": results
            })
            
        except Exception as e:
            logger.error(f"Quiz submission error: {e}")
            return web.json_response({
                "error": "Quiz submission failed"
            }, status=500)
    
    async def get_dashboard(self, request):
        """Get user learning dashboard"""
        try:
            user_id = request.headers.get('X-User-ID')
            
            if not user_id:
                return web.json_response({
                    "error": "User ID required"
                }, status=400)
            
            dashboard = show_dashboard(user_id)
            
            return web.json_response({
                "success": True,
                "dashboard": dashboard
            })
            
        except Exception as e:
            logger.error(f"Dashboard error: {e}")
            return web.json_response({
                "error": "Dashboard retrieval failed"
            }, status=500)
    
    async def get_learning_analytics(self, request):
        """Get detailed learning analytics"""
        try:
            user_id = request.headers.get('X-User-ID')
            
            if not user_id:
                return web.json_response({
                    "error": "User ID required"
                }, status=400)
            
            integration_status = get_integration_status()
            analytics = integration_status.get("learning_analytics", {})
            
            return web.json_response({
                "success": True,
                "analytics": analytics,
                "integration_active": integration_status.get("authenticated", False)
            })
            
        except Exception as e:
            logger.error(f"Analytics error: {e}")
            return web.json_response({
                "error": "Analytics retrieval failed"
            }, status=500)
    
    async def track_learning_xp(self, request):
        """Manually track learning XP"""
        try:
            data = await request.json()
            user_id = request.headers.get('X-User-ID')
            
            if not user_id:
                return web.json_response({
                    "error": "User ID required"
                }, status=400)
            
            # Track XP through learning engine
            xp_id = await learning_engine.track_learning_progress(data)
            
            if xp_id:
                return web.json_response({
                    "success": True,
                    "xp_transaction_id": xp_id,
                    "message": "XP tracked successfully"
                })
            else:
                return web.json_response({
                    "success": False,
                    "message": "XP tracking failed"
                }, status=500)
                
        except Exception as e:
            logger.error(f"XP tracking error: {e}")
            return web.json_response({
                "error": "XP tracking failed"
            }, status=500)
    
    async def get_achievements(self, request):
        """Get user achievements"""
        try:
            user_id = request.headers.get('X-User-ID')
            
            if not user_id:
                return web.json_response({
                    "error": "User ID required"
                }, status=400)
            
            # For now, return mock achievements
            achievements = [
                {
                    "id": "first_course",
                    "name": "First Course",
                    "description": "Completed your first course",
                    "xp_reward": 50,
                    "unlocked": True
                },
                {
                    "id": "quiz_master",
                    "name": "Quiz Master",
                    "description": "Score 90% or higher on 5 quizzes",
                    "xp_reward": 100,
                    "unlocked": False,
                    "progress": 0.6
                }
            ]
            
            return web.json_response({
                "success": True,
                "achievements": achievements
            })
            
        except Exception as e:
            logger.error(f"Achievements error: {e}")
            return web.json_response({
                "error": "Achievements retrieval failed"
            }, status=500)
    
    async def websocket_handler(self, request):
        """Handle WebSocket connections for real-time updates"""
        user_id = request.match_info['user_id']
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        # Store connection
        self.active_sessions[user_id] = ws
        logger.info(f"WebSocket connected: {user_id}")
        
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self.handle_websocket_message(user_id, data)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON from {user_id}")
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f"WebSocket error from {user_id}: {ws.exception()}")
        except Exception as e:
            logger.error(f"WebSocket error for {user_id}: {e}")
        finally:
            # Clean up
            if user_id in self.active_sessions:
                del self.active_sessions[user_id]
            logger.info(f"WebSocket disconnected: {user_id}")
        
        return ws
    
    async def handle_websocket_message(self, user_id: str, data: Dict[str, Any]):
        """Handle incoming WebSocket messages"""
        message_type = data.get("type")
        
        if message_type == "ping":
            await self.send_to_user(user_id, {"type": "pong", "timestamp": datetime.now().isoformat()})
        elif message_type == "request_dashboard":
            dashboard = show_dashboard(user_id)
            await self.send_to_user(user_id, {"type": "dashboard_update", "dashboard": dashboard})
        elif message_type == "request_analytics":
            integration_status = get_integration_status()
            analytics = integration_status.get("learning_analytics", {})
            await self.send_to_user(user_id, {"type": "analytics_update", "analytics": analytics})
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send message to specific user via WebSocket"""
        if user_id in self.active_sessions:
            try:
                await self.active_sessions[user_id].send_str(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to {user_id}: {e}")
                # Remove broken connection
                if user_id in self.active_sessions:
                    del self.active_sessions[user_id]
    
    async def broadcast_update(self, user_id: str, update: Dict[str, Any]):
        """Broadcast update to user"""
        message = {
            "type": "learning_update",
            "timestamp": datetime.now().isoformat(),
            "update": update
        }
        
        await self.send_to_user(user_id, message)
    
    async def start_server(self):
        """Start the LevelUp Academy service"""
        logger.info(f"Starting LevelUp Academy service on port {self.port}")
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        
        logger.info(f"🎓 LevelUp Academy service running on http://localhost:{self.port}")
        logger.info("📚 Adaptive learning with physics-based XP tracking")
        
        # Keep the server running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down LevelUp Academy service...")
        finally:
            await runner.cleanup()

async def main():
    """Main entry point"""
    service = LevelUpAcademyService()
    await service.start_server()

if __name__ == "__main__":
    asyncio.run(main())