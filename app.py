#!/usr/bin/env python3
# app.py - Main SQL Assistant Application with Enhanced Error Handling and Power BI Analyst
"""
SQL Assistant Application - Fixed Power BI Analyst Integration
Now includes better error handling and route registration
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
logging.getLogger('msal').setLevel(logging.WARNING)

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
    
    # Power BI variables (optional but needed for analyst)
    powerbi_vars = {
        "POWERBI_TENANT_ID": "Power BI Tenant ID",
        "POWERBI_CLIENT_ID": "Power BI Client ID",
        "POWERBI_CLIENT_SECRET": "Power BI Client Secret"
    }
    
    logger.info("=== Environment Check ===")
    missing_vars = []
    missing_powerbi = []
    powerbi_status = {}
    
    # Check required vars
    for var, description in required_vars.items():
        value = os.environ.get(var)
        if value:
            if "KEY" in var or "PASSWORD" in var or "SECRET" in var:
                masked = value[:4] + "***" + value[-4:] if len(value) > 8 else "***"
                logger.info(f"✓ {var}: {masked}")
            else:
                logger.info(f"✓ {var}: {value[:30]}...")
        else:
            logger.error(f"❌ {var}: NOT SET ({description})")
            missing_vars.append(var)
    
    # Check Power BI vars
    logger.info("\n=== Power BI Configuration ===")
    for var, description in powerbi_vars.items():
        value = os.environ.get(var)
        if value:
            powerbi_status[var] = True
            if "SECRET" in var:
                masked = value[:4] + "***" + value[-4:] if len(value) > 8 else "***"
                logger.info(f"✓ {var}: {masked}")
            else:
                logger.info(f"✓ {var}: {value[:30]}...")
        else:
            powerbi_status[var] = False
            logger.info(f"ℹ️ {var}: NOT SET ({description})")
            missing_powerbi.append(var)
    
    # Check if URL has embedded authentication
    function_url = os.environ.get("AZURE_FUNCTION_URL", "")
    if function_url and "code=" in function_url:
        logger.info("✅ Azure Function authentication: URL-embedded (recommended)")
    
    # Power BI status
    all_powerbi_configured = all(powerbi_status.values())
    if all_powerbi_configured:
        logger.info("✅ Power BI Analyst: Fully configured")
    elif any(powerbi_status.values()):
        logger.info("⚠️ Power BI Analyst: Partially configured")
    else:
        logger.info("ℹ️ Power BI Analyst: Not configured (optional feature)")
    
    return missing_vars, powerbi_status

# Run environment check
missing_vars, powerbi_status = check_environment()

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
        # Check actual Power BI configuration status
        powerbi_configured = all([
            os.environ.get("POWERBI_TENANT_ID"),
            os.environ.get("POWERBI_CLIENT_ID"),
            os.environ.get("POWERBI_CLIENT_SECRET")
        ])
        
        # Check if analyst routes are actually registered
        analyst_routes_registered = any('/analyst' in str(r) for r in req.app.router.routes())
        
        health_status = {
            "status": "healthy",
            "version": "2.2.1",  # Updated version
            "timestamp": datetime.now().isoformat(),
            "environment": DEPLOYMENT_ENV,
            "services": {
                "console": "available",
                "admin_dashboard": "available",
                "sql_translator": "available" if SQL_TRANSLATOR else "not available",
                "sql_function": "configured" if os.environ.get("AZURE_FUNCTION_URL") else "not configured",
                "powerbi_analyst": "available" if analyst_routes_registered else "not available"
            },
            "features": {
                "error_analysis": SQL_TRANSLATOR is not None,
                "query_fixing": SQL_TRANSLATOR is not None,
                "multi_database": True,
                "standardization_checks": True,
                "powerbi_integration": powerbi_configured,
                "business_intelligence": powerbi_configured
            },
            "powerbi_config": {
                "tenant_id_set": bool(os.environ.get("POWERBI_TENANT_ID")),
                "client_id_set": bool(os.environ.get("POWERBI_CLIENT_ID")),
                "client_secret_set": bool(os.environ.get("POWERBI_CLIENT_SECRET")),
                "all_configured": powerbi_configured,
                "routes_registered": analyst_routes_registered
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
    
    # Check if analyst routes are registered
    analyst_routes_registered = any('/analyst' in str(r) for r in req.app.router.routes())
    
    # Check Power BI configuration
    powerbi_configured = all([
        os.environ.get("POWERBI_TENANT_ID"),
        os.environ.get("POWERBI_CLIENT_ID"),
        os.environ.get("POWERBI_CLIENT_SECRET")
    ])
    
    analyst_section = ""
    if analyst_routes_registered:
        analyst_section = '''
                <a href="/analyst">Power BI Analyst</a>
                <span class="new-badge">NEW</span>'''
    elif powerbi_configured:
        analyst_section = '''
                <a href="/analyst" style="opacity: 0.7;">Power BI Analyst</a>
                <span style="font-size: 12px; color: #666;">(Routes not loaded)</span>'''
    else:
        analyst_section = '''
                <a href="/analyst" style="opacity: 0.5; cursor: not-allowed;">Power BI Analyst</a>
                <span style="font-size: 12px; color: #666;">(Not configured)</span>'''
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>SQL Assistant - Enhanced with Power BI</title>
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
                position: relative;
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
                position: absolute;
                right: 20px;
                top: 50%;
                transform: translateY(-50%);
            }}
            .section {{
                margin: 20px 0;
                text-align: left;
            }}
            .section h4 {{
                color: #667eea;
                margin-bottom: 10px;
            }}
            .debug-info {{
                margin-top: 20px;
                padding: 10px;
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 8px;
                font-size: 12px;
                text-align: left;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 SQL Assistant</h1>
            <div class="version">Version 2.2.1 - Enhanced with Power BI Integration</div>
            
            <div class="features">
                <h3>✨ What's New</h3>
                <ul>
                    <li>📊 <strong>Power BI Analyst</strong> <span class="new-badge" style="position: relative;">NEW</span><br>
                        Natural language business intelligence from your Power BI datasets</li>
                    <li>🔧 <strong>Intelligent Error Analysis</strong><br>
                        When queries fail, get detailed analysis and fix suggestions</li>
                    <li>🤖 <strong>Automatic Query Fixing</strong><br>
                        One-click application of suggested fixes</li>
                    <li>🔍 <strong>Discovery Queries</strong><br>
                        Find correct table and column names easily</li>
                    <li>📊 <strong>Database Standardization</strong><br>
                        Check schema compliance across systems</li>
                    <li>🗄️ <strong>Multi-Database Support</strong><br>
                        Compare and analyze across multiple databases</li>
                </ul>
            </div>
            
            <div class="section">
                <h4>🚀 Available Tools</h4>
            </div>
            
            <div class="links">
                <a href="/console">SQL Console</a>
                <a href="/admin">Admin Dashboard</a>
                {analyst_section}
                <a href="/health">Health Status</a>
            </div>
            
            <div class="status">
                Environment: {DEPLOYMENT_ENV}<br>
                SQL Translator: {'✅ Ready with Error Analysis' if SQL_TRANSLATOR else '❌ Not Available'}<br>
                Power BI Analyst: {'✅ Available' if analyst_routes_registered else '⚠️ Not Loaded' if powerbi_configured else '❌ Not Configured'}<br>
                Token Usage: {'Check /health for details' if SQL_TRANSLATOR else 'N/A'}
            </div>
            
            <div class="debug-info">
                <strong>Debug Info:</strong><br>
                Analyst Routes Registered: {analyst_routes_registered}<br>
                Power BI Env Vars Set: {powerbi_configured}<br>
                Check /health endpoint for detailed configuration status
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

# Import and add Power BI Analyst - ALWAYS TRY TO ADD ROUTES
# This ensures routes are registered even if there's a partial configuration issue
try:
    logger.info("Attempting to add Power BI Analyst routes...")
    
    # Check if any Power BI variables are set
    any_powerbi_vars = any([
        os.environ.get("POWERBI_TENANT_ID"),
        os.environ.get("POWERBI_CLIENT_ID"),
        os.environ.get("POWERBI_CLIENT_SECRET")
    ])
    
    if any_powerbi_vars:
        logger.info("At least one Power BI variable is set, attempting to load analyst...")
        
        # Try to import and add routes
        from analyst_routes import add_analyst_routes
        analyst_endpoint = add_analyst_routes(APP)
        logger.info("✓ Power BI Analyst routes added successfully")
        
        # Check if all variables are set
        if not all([os.environ.get("POWERBI_TENANT_ID"), 
                    os.environ.get("POWERBI_CLIENT_ID"),
                    os.environ.get("POWERBI_CLIENT_SECRET")]):
            logger.warning("⚠️ Power BI Analyst routes added but configuration is incomplete")
    else:
        logger.info("No Power BI variables set, creating placeholder route")
        
        # Add a placeholder route that explains the configuration requirement
        async def analyst_placeholder(request):
            return Response(text="""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Power BI Analyst - Configuration Required</title>
                <style>
                    body { font-family: Arial, sans-serif; padding: 40px; background: #f5f5f5; }
                    .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    h1 { color: #333; }
                    .error { background: #fee; padding: 15px; border-radius: 5px; border: 1px solid #fcc; margin: 20px 0; }
                    .info { background: #e7f3ff; padding: 15px; border-radius: 5px; border: 1px solid #b3d9ff; margin: 20px 0; }
                    code { background: #f0f0f0; padding: 2px 5px; border-radius: 3px; }
                    a { color: #667eea; text-decoration: none; }
                    a:hover { text-decoration: underline; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>📊 Power BI Analyst - Configuration Required</h1>
                    
                    <div class="error">
                        <h3>⚠️ Power BI Integration Not Configured</h3>
                        <p>The Power BI Analyst feature requires configuration of Azure Active Directory credentials.</p>
                    </div>
                    
                    <div class="info">
                        <h3>📋 Required Environment Variables</h3>
                        <p>Please set the following environment variables in your Azure App Service:</p>
                        <ul>
                            <li><code>POWERBI_TENANT_ID</code> - Your Azure AD tenant ID</li>
                            <li><code>POWERBI_CLIENT_ID</code> - App registration client ID</li>
                            <li><code>POWERBI_CLIENT_SECRET</code> - App registration client secret</li>
                        </ul>
                    </div>
                    
                    <div class="info">
                        <h3>🔧 Setup Instructions</h3>
                        <ol>
                            <li>Create an app registration in Azure AD</li>
                            <li>Grant Power BI API permissions (Dataset.Read.All)</li>
                            <li>Create a client secret</li>
                            <li>Add the environment variables to your App Service</li>
                            <li>Restart the application</li>
                        </ol>
                    </div>
                    
                    <p><a href="/">← Back to Home</a> | <a href="/health">Check Health Status</a></p>
                </div>
            </body>
            </html>
            """, content_type='text/html')
        
        APP.router.add_get('/analyst', analyst_placeholder)
        APP.router.add_get('/analyst/', analyst_placeholder)
        logger.info("✓ Added placeholder route for Power BI Analyst")
        
except ImportError as e:
    logger.error(f"❌ Failed to import Power BI Analyst: {e}")
    logger.error("This might be due to missing dependencies or import errors")
except Exception as e:
    logger.error(f"❌ Error initializing Power BI Analyst: {e}", exc_info=True)

# Startup tasks
async def on_startup(app):
    """Perform startup tasks"""
    logger.info("=== SQL Assistant Enhanced Startup ===")
    logger.info(f"Environment: {DEPLOYMENT_ENV}")
    logger.info("Features: Error Analysis, Query Fixing, Discovery Queries, Power BI Integration")
    
    if missing_vars:
        logger.warning(f"⚠️ Missing environment variables: {', '.join(missing_vars)}")
    else:
        logger.info("✓ All required environment variables are set")
    
    # Log Power BI status
    powerbi_configured = all([
        os.environ.get("POWERBI_TENANT_ID"),
        os.environ.get("POWERBI_CLIENT_ID"),
        os.environ.get("POWERBI_CLIENT_SECRET")
    ])
    
    logger.info(f"Power BI Configuration Status: {powerbi_configured}")
    if not powerbi_configured:
        logger.info("Power BI variables status:")
        logger.info(f"  POWERBI_TENANT_ID: {'SET' if os.environ.get('POWERBI_TENANT_ID') else 'NOT SET'}")
        logger.info(f"  POWERBI_CLIENT_ID: {'SET' if os.environ.get('POWERBI_CLIENT_ID') else 'NOT SET'}")
        logger.info(f"  POWERBI_CLIENT_SECRET: {'SET' if os.environ.get('POWERBI_CLIENT_SECRET') else 'NOT SET'}")
    
    # Log registered routes
    logger.info("Registered routes:")
    for route in app.router.routes():
        if hasattr(route, 'resource'):
            logger.info(f"  {route.resource}")
    
    # Create necessary directories
    dirs = ['.token_usage', 'logs', '.query_history', '.error_logs', '.analyst_cache']
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
    
    # Check Power BI configuration
    powerbi_configured = all([
        os.environ.get("POWERBI_TENANT_ID"),
        os.environ.get("POWERBI_CLIENT_ID"),
        os.environ.get("POWERBI_CLIENT_SECRET")
    ])
    
    # Check if analyst routes are registered
    analyst_routes_registered = any('/analyst' in str(r) for r in req.app.router.routes())
    
    info_data = {
        'name': 'SQL Assistant Enhanced with Power BI',
        'version': '2.2.1',
        'features': [
            'SQL Console with natural language support',
            'Intelligent error analysis and query fixing',
            'Multi-database standardization checks',
            'Discovery queries for finding correct object names',
            'Admin Dashboard with system monitoring',
            'Azure OpenAI integration with token tracking',
            'Azure SQL Function connectivity',
            f'Power BI integration {"(available)" if analyst_routes_registered else "(not loaded)" if powerbi_configured else "(not configured)"}'
        ],
        'new_features': [
            'Power BI Analyst - Natural language BI from Power BI datasets',
            'Progressive analysis with automatic follow-up queries',
            'Business recommendations based on data insights',
            'DAX query generation and error fixing',
            'Multi-workspace and multi-dataset support'
        ],
        'endpoints': [
            {'path': '/', 'description': 'Home page'},
            {'path': '/console', 'description': 'SQL Console with error handling'},
            {'path': '/admin', 'description': 'Admin Dashboard'},
            {'path': '/analyst', 'description': f'Power BI Analyst {"(available)" if analyst_routes_registered else "(placeholder)" }'},
            {'path': '/health', 'description': 'Health check with detailed status'},
            {'path': '/info', 'description': 'This endpoint'},
            {'path': '/api/test-translation', 'description': 'Test SQL translation'},
            {'path': '/api/test-error-analysis', 'description': 'Test error analysis'}
        ],
        'configuration': {
            'sql_translator': SQL_TRANSLATOR is not None,
            'powerbi_analyst_configured': powerbi_configured,
            'powerbi_analyst_loaded': analyst_routes_registered,
            'azure_function': bool(os.environ.get("AZURE_FUNCTION_URL"))
        },
        'debug': {
            'powerbi_vars': {
                'tenant_id': 'SET' if os.environ.get('POWERBI_TENANT_ID') else 'NOT SET',
                'client_id': 'SET' if os.environ.get('POWERBI_CLIENT_ID') else 'NOT SET',
                'client_secret': 'SET' if os.environ.get('POWERBI_CLIENT_SECRET') else 'NOT SET'
            }
        }
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
        logger.info("  - /analyst (Power BI Analyst)")
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