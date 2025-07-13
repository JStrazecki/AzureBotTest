#!/usr/bin/env python3
# app.py - Main SQL Assistant Application with Enhanced Error Handling
"""
SQL Assistant Application - Updated with Unified SQL Translator
Now includes intelligent error analysis and query fixing
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Web framework
from aiohttp import web
from aiohttp.web import Request, Response, json_response, middleware
import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress verbose logs
logging.getLogger('openai').setLevel(logging.WARNING)
logging.getLogger('tiktoken').setLevel(logging.WARNING)

# Environment Configuration
DEPLOYMENT_ENV = os.environ.get("DEPLOYMENT_ENV", "production")

# Check environment variables
def check_environment():
    """Check and log environment variable status"""
    required_vars = {
        "AZURE_OPENAI_ENDPOINT": "Azure OpenAI Endpoint",
        "AZURE_OPENAI_API_KEY": "Azure OpenAI API Key",
        "AZURE_OPENAI_DEPLOYMENT_NAME": "OpenAI Deployment Name",
        "AZURE_FUNCTION_URL": "Azure Function URL"
    }
    
    logger.info("=== Environment Check ===")
    missing_vars = []
    
    for var, description in required_vars.items():
        value = os.environ.get(var)
        if value:
            if "KEY" in var or "PASSWORD" in var:
                masked = value[:4] + "***" + value[-4:] if len(value) > 8 else "***"
                logger.info(f"✓ {var}: {masked}")
            else:
                logger.info(f"✓ {var}: {value[:30]}...")
        else:
            logger.error(f"❌ {var}: NOT SET ({description})")
            missing_vars.append(var)
    
    # Check if URL has embedded authentication
    function_url = os.environ.get("AZURE_FUNCTION_URL", "")
    if function_url and "code=" in function_url:
        logger.info("✅ Azure Function authentication: URL-embedded (recommended)")
    
    return missing_vars

# Run environment check
missing_vars = check_environment()

# Error handling middleware
@middleware
async def aiohttp_error_middleware(request: Request, handler):
    """Global error handler for aiohttp"""
    try:
        response = await handler(request)
        return response
    except web.HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unhandled error: {e}", exc_info=True)
        return json_response({
            "error": "Internal server error",
            "message": str(e),
            "type": type(e).__name__
        }, status=500)

# Initialize SQL translator if available
SQL_TRANSLATOR = None
if not missing_vars or all(var not in missing_vars for var in ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY"]):
    try:
        # Import the unified SQL translator
        from sql_translator import SQLTranslator
        SQL_TRANSLATOR = SQLTranslator()
        logger.info("✓ Unified SQL Translator initialized with error analysis")
    except Exception as e:
        logger.error(f"❌ Failed to initialize SQL Translator: {e}")

# Health check endpoint
async def health(req: Request) -> Response:
    """Health check endpoint"""
    try:
        health_status = {
            "status": "healthy",
            "version": "2.1.0",  # Updated version
            "timestamp": datetime.now().isoformat(),
            "environment": DEPLOYMENT_ENV,
            "services": {
                "console": "available",
                "admin_dashboard": "available",
                "sql_translator": "available" if SQL_TRANSLATOR else "not available",
                "sql_function": "configured" if os.environ.get("AZURE_FUNCTION_URL") else "not configured"
            },
            "features": {
                "error_analysis": SQL_TRANSLATOR is not None,
                "query_fixing": SQL_TRANSLATOR is not None,
                "multi_database": True,
                "standardization_checks": True
            },
            "missing_vars": missing_vars
        }
        
        # Add token usage if available
        if SQL_TRANSLATOR:
            health_status["token_usage"] = SQL_TRANSLATOR.get_usage_summary()
        
        return json_response(health_status)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return json_response({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status=503)

# Root endpoint
async def index(req: Request) -> Response:
    """Root endpoint with navigation"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>SQL Assistant - Enhanced</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0;
            }}
            .container {{
                background: white;
                padding: 40px;
                border-radius: 16px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                text-align: center;
                max-width: 600px;
            }}
            h1 {{
                color: #333;
                margin-bottom: 20px;
            }}
            .version {{
                color: #666;
                font-size: 14px;
                margin-bottom: 30px;
            }}
            .features {{
                text-align: left;
                background: #f7f7f7;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 30px;
            }}
            .features h3 {{
                color: #667eea;
                margin-top: 0;
            }}
            .features ul {{
                margin: 10px 0;
                padding-left: 20px;
            }}
            .features li {{
                margin: 5px 0;
            }}
            .links {{
                display: flex;
                flex-direction: column;
                gap: 15px;
            }}
            a {{
                display: block;
                padding: 15px 30px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 600;
                transition: transform 0.2s;
            }}
            a:hover {{
                transform: translateY(-2px);
            }}
            .status {{
                margin-top: 20px;
                padding: 10px;
                background: #f0f0f0;
                border-radius: 8px;
                font-size: 14px;
            }}
            .new-badge {{
                background: #10b981;
                color: white;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 12px;
                margin-left: 5px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 SQL Assistant</h1>
            <div class="version">Version 2.1.0 - Enhanced with Error Analysis</div>
            
            <div class="features">
                <h3>✨ What's New</h3>
                <ul>
                    <li>🔧 <strong>Intelligent Error Analysis</strong> <span class="new-badge">NEW</span><br>
                        When queries fail, get detailed analysis and fix suggestions</li>
                    <li>🤖 <strong>Automatic Query Fixing</strong> <span class="new-badge">NEW</span><br>
                        One-click application of suggested fixes</li>
                    <li>🔍 <strong>Discovery Queries</strong> <span class="new-badge">NEW</span><br>
                        Find correct table and column names easily</li>
                    <li>📊 <strong>Database Standardization</strong><br>
                        Check schema compliance across systems</li>
                    <li>🗄️ <strong>Multi-Database Support</strong><br>
                        Compare and analyze across multiple databases</li>
                </ul>
            </div>
            
            <div class="links">
                <a href="/console">SQL Console</a>
                <a href="/admin">Admin Dashboard</a>
                <a href="/health">Health Status</a>
            </div>
            
            <div class="status">
                Environment: {DEPLOYMENT_ENV}<br>
                SQL Translator: {'✅ Ready with Error Analysis' if SQL_TRANSLATOR else '❌ Not Available'}<br>
                Token Usage: {'Check /health for details' if SQL_TRANSLATOR else 'N/A'}
            </div>
        </div>
    </body>
    </html>
    """
    
    return Response(text=html, content_type='text/html')

# Create the application
APP = web.Application(middlewares=[aiohttp_error_middleware])

# Add main routes
APP.router.add_get("/", index)
APP.router.add_get("/health", health)

# Import and add admin dashboard
try:
    from admin_dashboard_routes import add_admin_routes
    add_admin_routes(APP, SQL_TRANSLATOR)
    logger.info("✓ Admin dashboard routes added")
except ImportError as e:
    logger.error(f"❌ Failed to add admin dashboard: {e}")

# Import and add SQL console with enhanced error handling
try:
    from sql_console_routes import add_console_routes
    add_console_routes(APP, SQL_TRANSLATOR)
    logger.info("✓ Enhanced SQL console routes added with error analysis")
except ImportError as e:
    logger.error(f"❌ Failed to add SQL console: {e}")

# Startup tasks
async def on_startup(app):
    """Perform startup tasks"""
    logger.info("=== SQL Assistant Enhanced Startup ===")
    logger.info(f"Environment: {DEPLOYMENT_ENV}")
    logger.info("Features: Error Analysis, Query Fixing, Discovery Queries")
    
    if missing_vars:
        logger.warning(f"⚠️ Missing environment variables: {', '.join(missing_vars)}")
    else:
        logger.info("✓ All required environment variables are set")
    
    # Create necessary directories
    dirs = ['.token_usage', 'logs', '.query_history', '.error_logs']
    for dir_name in dirs:
        try:
            os.makedirs(dir_name, exist_ok=True)
        except Exception as e:
            logger.warning(f"Failed to create directory {dir_name}: {e}")
    
    logger.info("=== Startup completed ===")

# Cleanup tasks
async def on_cleanup(app):
    """Perform cleanup tasks"""
    logger.info("SQL Assistant shutting down...")
    
    # Save token usage if available
    if SQL_TRANSLATOR:
        usage = SQL_TRANSLATOR.get_usage_summary()
        logger.info(f"Final token usage: {usage['total_tokens']} tokens, ${usage['estimated_cost']:.4f}")

# Register startup and cleanup handlers
APP.on_startup.append(on_startup)
APP.on_cleanup.append(on_cleanup)

# Add additional utility routes
async def test_sql_translation(req: Request) -> Response:
    """Test endpoint for SQL translation with error analysis"""
    try:
        data = await req.json()
        query = data.get('query', 'show me all tables')
        
        if not SQL_TRANSLATOR:
            return json_response({
                'status': 'error',
                'error': 'SQL Translator not available'
            })
        
        result = await SQL_TRANSLATOR.translate_to_sql(query)
        
        return json_response({
            'status': 'success',
            'query': result.query,
            'database': result.database,
            'explanation': result.explanation,
            'confidence': result.confidence,
            'warnings': result.warnings,
            'error': result.error
        })
    except Exception as e:
        return json_response({
            'status': 'error',
            'error': str(e)
        }, status=500)

async def test_error_analysis(req: Request) -> Response:
    """Test endpoint for error analysis"""
    try:
        data = await req.json()
        
        if not SQL_TRANSLATOR:
            return json_response({
                'status': 'error',
                'error': 'SQL Translator not available'
            })
        
        analysis = await SQL_TRANSLATOR.analyze_sql_error(
            original_query=data.get('query', ''),
            error_message=data.get('error', ''),
            database=data.get('database', 'demo'),
            user_intent=data.get('user_intent')
        )
        
        return json_response({
            'status': 'success',
            'error_type': analysis.error_type,
            'explanation': analysis.explanation,
            'suggested_fix': analysis.suggested_fix,
            'fixed_query': analysis.fixed_query,
            'confidence': analysis.confidence,
            'alternatives': analysis.alternative_queries,
            'discovery_queries': analysis.discovery_queries
        })
    except Exception as e:
        return json_response({
            'status': 'error',
            'error': str(e)
        }, status=500)

# Add test routes
APP.router.add_post("/api/test-translation", test_sql_translation)
APP.router.add_post("/api/test-error-analysis", test_error_analysis)

# Simple info endpoint
async def info(req: Request) -> Response:
    """Information about the application"""
    info_data = {
        'name': 'SQL Assistant Enhanced',
        'version': '2.1.0',
        'features': [
            'SQL Console with natural language support',
            'Intelligent error analysis and query fixing',
            'Multi-database standardization checks',
            'Discovery queries for finding correct object names',
            'Admin Dashboard with system monitoring',
            'Azure OpenAI integration with token tracking',
            'Azure SQL Function connectivity'
        ],
        'new_features': [
            'Error analysis when queries fail',
            'One-click query fixes',
            'Alternative query suggestions',
            'Discovery queries to find tables/columns',
            'Enhanced multi-database support'
        ],
        'endpoints': [
            {'path': '/', 'description': 'Home page'},
            {'path': '/console', 'description': 'SQL Console with error handling'},
            {'path': '/admin', 'description': 'Admin Dashboard'},
            {'path': '/health', 'description': 'Health check with token usage'},
            {'path': '/info', 'description': 'This endpoint'},
            {'path': '/api/test-translation', 'description': 'Test SQL translation'},
            {'path': '/api/test-error-analysis', 'description': 'Test error analysis'}
        ]
    }
    
    # Add token usage if available
    if SQL_TRANSLATOR:
        info_data['token_usage'] = SQL_TRANSLATOR.get_usage_summary()
    
    return json_response(info_data)

APP.router.add_get("/info", info)

# Main entry point
if __name__ == "__main__":
    try:
        PORT = int(os.environ.get("PORT", 8000))
        logger.info(f"Starting enhanced application on port {PORT}")
        logger.info(f"Access the application at: http://localhost:{PORT}")
        
        # Log available endpoints
        logger.info("Available endpoints:")
        logger.info("  - / (Home)")
        logger.info("  - /console (SQL Console with Error Analysis)")
        logger.info("  - /admin (Admin Dashboard)")
        logger.info("  - /health (Health Check)")
        logger.info("  - /info (Application Info)")
        logger.info("  - /api/test-translation (Test Translation)")
        logger.info("  - /api/test-error-analysis (Test Error Analysis)")
        
        web.run_app(
            APP,
            host="0.0.0.0",
            port=PORT,
            access_log_format='%a %t "%r" %s %b "%{Referer}i" "%{User-Agent}i" %Tf'
        )
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        raise

# End of file