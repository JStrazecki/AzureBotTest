# admin_dashboard.py - Built-in admin dashboard for the SQL Assistant Bot
"""
Admin Dashboard Route Handler
Provides a web-based dashboard for monitoring bot health and testing components
"""

import os
import json
import asyncio
import aiohttp
from datetime import datetime
from aiohttp.web import Request, Response, json_response
from aiohttp import web

class AdminDashboard:
    """Admin dashboard for monitoring and testing the SQL Assistant Bot"""
    
    def __init__(self, sql_translator=None, executor=None):
        self.sql_translator = sql_translator
        self.executor = executor
        
    async def dashboard_page(self, request: Request) -> Response:
        """Serve the main dashboard HTML page"""
        
        # Get environment variables for pre-population
        config = {
            "botUrl": f"https://{request.host}",
            "functionUrl": os.environ.get("AZURE_FUNCTION_URL", ""),
            "functionKey": os.environ.get("AZURE_FUNCTION_KEY", ""),
            "openaiEndpoint": os.environ.get("AZURE_OPENAI_ENDPOINT", ""),
            "openaiDeployment": os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4"),
            "environment": os.environ.get("DEPLOYMENT_ENV", "production")
        }
        
        # Dashboard HTML with embedded config
        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SQL Assistant Bot - Admin Dashboard</title>
    <style>
        {self._get_dashboard_css()}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>🤖 SQL Assistant Bot - Admin Dashboard</h1>
            <p>Real-time monitoring and testing • Environment: {config["environment"]}</p>
            <div class="server-info">
                <span>Server: {request.host}</span> • 
                <span>Time: <span id="currentTime">{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</span></span>
            </div>
        </div>

        <!-- Quick Status Overview -->
        <div class="quick-status">
            <div class="status-item" id="overallStatus">
                <div class="status-icon status-loading">⟳</div>
                <div class="status-text">
                    <div class="status-title">System Status</div>
                    <div class="status-subtitle">Checking...</div>
                </div>
            </div>
        </div>

        <!-- Environment Configuration (Read-only display) -->
        <div class="config-section">
            <h2>⚙️ Environment Configuration</h2>
            <div class="config-grid">
                <div class="config-display">
                    <label>Bot URL:</label>
                    <div class="config-value">{config["botUrl"]}</div>
                </div>
                <div class="config-display">
                    <label>Azure Function:</label>
                    <div class="config-value">{config["functionUrl"] or "Not configured"}</div>
                </div>
                <div class="config-display">
                    <label>Function Key:</label>
                    <div class="config-value">{"***" + config["functionKey"][-4:] if config["functionKey"] else "Not configured"}</div>
                </div>
                <div class="config-display">
                    <label>OpenAI Endpoint:</label>
                    <div class="config-value">{config["openaiEndpoint"] or "Not configured"}</div>
                </div>
                <div class="config-display">
                    <label>OpenAI Deployment:</label>
                    <div class="config-value">{config["openaiDeployment"]}</div>
                </div>
            </div>
            <div class="action-buttons">
                <button class="test-button primary" onclick="runAllTests()">🚀 Run All Tests</button>
                <button class="test-button" onclick="refreshStatus()">🔄 Refresh</button>
                <button class="test-button" onclick="exportReport()">📊 Export Report</button>
            </div>
        </div>

        <!-- Test Results Grid -->
        <div class="status-grid">
            <!-- Bot Health -->
            <div class="status-card">
                <div class="card-header">
                    <div class="status-icon status-unknown" id="botHealthIcon">?</div>
                    <div class="card-title">Bot Health</div>
                    <div class="card-actions">
                        <button class="mini-button" onclick="testBotHealth()">Test</button>
                    </div>
                </div>
                <div class="card-content">
                    <div class="status-details" id="botHealthDetails">Ready for testing...</div>
                </div>
            </div>

            <!-- Azure OpenAI -->
            <div class="status-card">
                <div class="card-header">
                    <div class="status-icon status-unknown" id="openaiIcon">?</div>
                    <div class="card-title">Azure OpenAI</div>
                    <div class="card-actions">
                        <button class="mini-button" onclick="testOpenAI()">Test</button>
                    </div>
                </div>
                <div class="card-content">
                    <div class="status-details" id="openaiDetails">Ready for testing...</div>
                </div>
            </div>

            <!-- SQL Function -->
            <div class="status-card">
                <div class="card-header">
                    <div class="status-icon status-unknown" id="functionIcon">?</div>
                    <div class="card-title">SQL Function</div>
                    <div class="card-actions">
                        <button class="mini-button" onclick="testSQLFunction()">Test</button>
                    </div>
                </div>
                <div class="card-content">
                    <div class="status-details" id="functionDetails">Ready for testing...</div>
                </div>
            </div>

            <!-- Bot Messaging -->
            <div class="status-card">
                <div class="card-header">
                    <div class="status-icon status-unknown" id="messagingIcon">?</div>
                    <div class="card-title">Bot Messaging</div>
                    <div class="card-actions">
                        <button class="mini-button" onclick="testMessaging()">Test</button>
                    </div>
                </div>
                <div class="card-content">
                    <div class="status-details" id="messagingDetails">Ready for testing...</div>
                </div>
            </div>

            <!-- Environment -->
            <div class="status-card">
                <div class="card-header">
                    <div class="status-icon status-unknown" id="envIcon">?</div>
                    <div class="card-title">Environment</div>
                    <div class="card-actions">
                        <button class="mini-button" onclick="testEnvironment()">Test</button>
                    </div>
                </div>
                <div class="card-content">
                    <div class="status-details" id="envDetails">Ready for testing...</div>
                </div>
            </div>

            <!-- Performance -->
            <div class="status-card">
                <div class="card-header">
                    <div class="status-icon status-unknown" id="perfIcon">?</div>
                    <div class="card-title">Performance</div>
                    <div class="card-actions">
                        <button class="mini-button" onclick="testPerformance()">Test</button>
                    </div>
                </div>
                <div class="card-content">
                    <div class="status-details" id="perfDetails">Ready for testing...</div>
                </div>
            </div>
        </div>

        <!-- Live Activity Log -->
        <div class="log-section">
            <div class="log-header">
                <h2>📋 Live Activity Log</h2>
                <div class="log-controls">
                    <button class="mini-button" onclick="clearLogs()">Clear</button>
                    <button class="mini-button" onclick="exportLogs()">Export</button>
                    <label class="auto-refresh">
                        <input type="checkbox" id="autoRefresh" onchange="toggleAutoRefresh()"> Auto Refresh
                    </label>
                </div>
            </div>
            <div class="log-viewer" id="logViewer">
                <div class="log-entry info">
                    <span class="timestamp">[{datetime.now().strftime("%H:%M:%S")}]</span>
                    <span class="message">Admin dashboard initialized</span>
                </div>
            </div>
        </div>

        <!-- Bot Chat Console -->
        <div class="config-section">
            <h2>💬 Bot Chat Console</h2>
            <p>Test your bot by sending messages directly (simulates Teams chat)</p>
            
            <div class="chat-container">
                <div class="chat-messages" id="chatMessages">
                    <div class="chat-message system">
                        <div class="message-content">
                            <strong>System:</strong> Chat console ready. Type a message to test your bot!
                        </div>
                        <div class="message-time">{datetime.now().strftime("%H:%M")}</div>
                    </div>
                </div>
                
                <div class="chat-input-container">
                    <input type="text" id="chatInput" placeholder="Type your message here..." onkeypress="handleChatKeypress(event)">
                    <button class="test-button primary" onclick="sendChatMessage()">Send</button>
                    <button class="test-button" onclick="clearChat()">Clear</button>
                </div>
                
                <div class="chat-suggestions">
                    <button class="suggestion-button" onclick="sendQuickMessage('hello')">hello</button>
                    <button class="suggestion-button" onclick="sendQuickMessage('/help')">/help</button>
                    <button class="suggestion-button" onclick="sendQuickMessage('/database list')">/database list</button>
                    <button class="suggestion-button" onclick="sendQuickMessage('show me tables')">show me tables</button>
                    <button class="suggestion-button" onclick="sendQuickMessage('/stats')">/stats</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Embedded configuration from server
        const CONFIG = {json.dumps(config)};
        
        {self._get_dashboard_javascript()}
    </script>
</body>
</html>'''
        
        return Response(text=html_content, content_type='text/html')
    
    async def api_test_health(self, request: Request) -> Response:
        """API endpoint for testing bot health"""
        try:
            # Get comprehensive health information
            health_data = await self._get_comprehensive_health()
            return json_response({
                "status": "success",
                "data": health_data,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            return json_response({
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }, status=500)
    
    async def api_test_openai(self, request: Request) -> Response:
        """API endpoint for testing Azure OpenAI"""
        try:
            if not self.sql_translator:
                return json_response({
                    "status": "error",
                    "error": "SQL translator not available"
                })
            
            # Test OpenAI connection
            result = await self._test_openai_connection()
            return json_response({
                "status": "success" if result["success"] else "error",
                "data": result,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            return json_response({
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }, status=500)
    
    async def api_test_function(self, request: Request) -> Response:
        """API endpoint for testing SQL function"""
        try:
            result = await self._test_sql_function()
            return json_response({
                "status": "success" if result["success"] else "error",
                "data": result,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            return json_response({
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }, status=500)
    
    async def api_test_performance(self, request: Request) -> Response:
        """API endpoint for testing performance"""
        try:
            result = await self._test_performance()
            return json_response({
                "status": "success",
                "data": result,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            return json_response({
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }, status=500)
    
    async def _get_comprehensive_health(self) -> dict:
        """Get comprehensive health information"""
        # Environment variables check
        required_vars = [
            "MICROSOFT_APP_ID", "MICROSOFT_APP_PASSWORD",
            "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY",
            "AZURE_FUNCTION_URL"
        ]
        
        env_status = {}
        missing_vars = []
        
        for var in required_vars:
            value = os.environ.get(var)
            env_status[var] = bool(value)
            if not value:
                missing_vars.append(var)
        
        # Optional variables
        optional_vars = ["AZURE_FUNCTION_KEY", "AZURE_OPENAI_DEPLOYMENT_NAME"]
        for var in optional_vars:
            env_status[var] = bool(os.environ.get(var))
        
        return {
            "environment_variables": env_status,
            "missing_variables": missing_vars,
            "has_critical_vars": len(missing_vars) == 0,
            "sql_translator_available": self.sql_translator is not None,
            "executor_available": self.executor is not None,
            "python_version": os.sys.version,
            "working_directory": os.getcwd()
        }
    
    async def _test_openai_connection(self) -> dict:
        """Test Azure OpenAI connection"""
        endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
        
        if not endpoint or not api_key:
            return {
                "success": False,
                "error": "Missing OpenAI configuration",
                "details": {
                    "has_endpoint": bool(endpoint),
                    "has_api_key": bool(api_key)
                }
            }
        
        try:
            # Test with a simple request
            if endpoint.endswith('/'):
                endpoint = endpoint.rstrip('/')
            
            test_url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version=2024-02-01"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    test_url,
                    headers={
                        "api-key": api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "messages": [{"role": "user", "content": "Test"}],
                        "max_tokens": 5
                    },
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        return {
                            "success": True,
                            "details": {
                                "status_code": response.status,
                                "deployment": deployment,
                                "endpoint": endpoint
                            }
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"OpenAI API error: {response.status}",
                            "details": {
                                "status_code": response.status,
                                "response": error_text[:200]
                            }
                        }
                        
        except Exception as e:
            return {
                "success": False,
                "error": f"Connection error: {str(e)}",
                "details": {"exception_type": type(e).__name__}
            }
    
    async def _test_sql_function(self) -> dict:
        """Test SQL function connection"""
        function_url = os.environ.get("AZURE_FUNCTION_URL")
        function_key = os.environ.get("AZURE_FUNCTION_KEY")
        
        if not function_url:
            return {
                "success": False,
                "error": "SQL Function URL not configured"
            }
        
        try:
            # Test metadata query
            test_url = function_url
            headers = {"Content-Type": "application/json"}
            
            if function_key:
                headers["x-functions-key"] = function_key
            
            payload = {"query_type": "metadata"}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    test_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "details": {
                                "status_code": response.status,
                                "databases_found": len(data.get("databases", [])),
                                "has_function_key": bool(function_key)
                            }
                        }
                    elif response.status == 401:
                        return {
                            "success": False,
                            "error": "Authentication failed - function key required or invalid",
                            "details": {
                                "status_code": response.status,
                                "has_function_key": bool(function_key)
                            }
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"Function error: {response.status}",
                            "details": {
                                "status_code": response.status,
                                "response": error_text[:200]
                            }
                        }
                        
        except Exception as e:
            return {
                "success": False,
                "error": f"Connection error: {str(e)}",
                "details": {"exception_type": type(e).__name__}
            }
    
    async def _test_performance(self) -> dict:
        """Test performance metrics"""
        try:
            # Test response time for health endpoint
            start_time = asyncio.get_event_loop().time()
            
            # Simulate internal health check
            await asyncio.sleep(0.001)  # Minimal delay to simulate processing
            
            end_time = asyncio.get_event_loop().time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            return {
                "response_time_ms": round(response_time, 2),
                "memory_info": self._get_memory_info(),
                "uptime": self._get_uptime()
            }
            
        except Exception as e:
            return {
                "error": f"Performance test failed: {str(e)}"
            }
    
    def _get_memory_info(self) -> dict:
        """Get memory information if available"""
        try:
            import psutil
            process = psutil.Process()
            return {
                "memory_usage_mb": round(process.memory_info().rss / 1024 / 1024, 2),
                "cpu_percent": round(process.cpu_percent(), 2)
            }
        except ImportError:
            return {"info": "psutil not available"}
        except Exception:
            return {"info": "memory info unavailable"}
    
    def _get_uptime(self) -> str:
        """Get approximate uptime"""
        # This is a simplified uptime - in production you'd track actual start time
        return "Runtime information not available"
    
    def _get_dashboard_css(self) -> str:
        """Return the CSS styles for the dashboard"""
        return '''
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }

        .dashboard {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
            color: white;
        }

        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
            margin-bottom: 5px;
        }

        .server-info {
            font-size: 0.9rem;
            opacity: 0.8;
        }

        .quick-status {
            display: flex;
            justify-content: center;
            margin-bottom: 30px;
        }

        .status-item {
            background: white;
            border-radius: 12px;
            padding: 20px 40px;
            display: flex;
            align-items: center;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        }

        .status-icon {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            margin-right: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: white;
            font-size: 18px;
        }

        .status-unknown { background: #6c757d; }
        .status-success { background: #28a745; }
        .status-error { background: #dc3545; }
        .status-warning { background: #ffc107; color: #333; }
        .status-loading { 
            background: #17a2b8; 
            animation: spin 2s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .status-text {
            display: flex;
            flex-direction: column;
        }

        .status-title {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 2px;
        }

        .status-subtitle {
            font-size: 0.9rem;
            color: #666;
        }

        .config-section {
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        }

        .config-section h2 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.4rem;
        }

        .config-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }

        .config-display {
            padding: 12px;
            background: #f8f9fa;
            border-radius: 6px;
            border-left: 4px solid #667eea;
        }

        .config-display label {
            font-weight: 600;
            color: #555;
            font-size: 0.9rem;
        }

        .config-value {
            margin-top: 5px;
            font-family: monospace;
            font-size: 0.9rem;
            color: #333;
            word-break: break-all;
        }

        .action-buttons {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }

        .test-button {
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s;
            font-size: 14px;
        }

        .test-button.primary {
            background: linear-gradient(45deg, #28a745, #20c997);
            color: white;
        }

        .test-button:not(.primary) {
            background: #f8f9fa;
            color: #495057;
            border: 1px solid #dee2e6;
        }

        .test-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }

        .mini-button {
            padding: 4px 8px;
            font-size: 11px;
            border: none;
            border-radius: 4px;
            background: #e9ecef;
            color: #495057;
            cursor: pointer;
            transition: background 0.2s;
        }

        .mini-button:hover {
            background: #dee2e6;
        }

        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .status-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }

        .status-card:hover {
            transform: translateY(-3px);
        }

        .card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 15px;
        }

        .card-header .status-icon {
            width: 24px;
            height: 24px;
            font-size: 14px;
            margin-right: 10px;
        }

        .card-title {
            font-size: 1.1rem;
            font-weight: 600;
            flex-grow: 1;
        }

        .card-actions {
            display: flex;
            gap: 5px;
        }

        .status-details {
            background: #f8f9fa;
            border-radius: 6px;
            padding: 12px;
            font-family: monospace;
            font-size: 12px;
            max-height: 120px;
            overflow-y: auto;
            white-space: pre-wrap;
            border-left: 4px solid #dee2e6;
        }

        .log-section {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        }

        .log-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }

        .log-header h2 {
            font-size: 1.4rem;
            color: #333;
        }

        .log-controls {
            display: flex;
            gap: 10px;
            align-items: center;
        }

        .auto-refresh {
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 12px;
            color: #666;
        }

        .log-viewer {
            background: #2d3748;
            color: #e2e8f0;
            border-radius: 8px;
            padding: 15px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            max-height: 300px;
            overflow-y: auto;
        }

        .log-entry {
            margin-bottom: 5px;
            display: flex;
            align-items: flex-start;
        }

        .timestamp {
            color: #a0aec0;
            margin-right: 10px;
            flex-shrink: 0;
        }

        .message {
            flex-grow: 1;
        }

        .log-entry.info .message { color: #63b3ed; }
        .log-entry.success .message { color: #68d391; }
        .log-entry.warning .message { color: #fbb041; }
        .log-entry.error .message { color: #fc8181; }

        /* Chat Console Styles */
        .chat-container {
            border: 1px solid #dee2e6;
            border-radius: 8px;
            overflow: hidden;
        }

        .chat-messages {
            height: 300px;
            overflow-y: auto;
            padding: 15px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }

        .chat-message {
            margin-bottom: 15px;
            padding: 10px;
            border-radius: 8px;
            position: relative;
        }

        .chat-message.user {
            background: #e3f2fd;
            margin-left: 20px;
            border-left: 4px solid #2196f3;
        }

        .chat-message.bot {
            background: #e8f5e8;
            margin-right: 20px;
            border-left: 4px solid #4caf50;
        }

        .chat-message.system {
            background: #fff3e0;
            border-left: 4px solid #ff9800;
            font-style: italic;
        }

        .chat-message.error {
            background: #ffebee;
            border-left: 4px solid #f44336;
        }

        .message-content {
            margin-bottom: 5px;
            line-height: 1.4;
        }

        .message-time {
            font-size: 11px;
            color: #666;
            text-align: right;
        }

        .chat-input-container {
            display: flex;
            padding: 15px;
            background: white;
            gap: 10px;
            align-items: center;
        }

        .chat-input-container input {
            flex: 1;
            padding: 10px;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            font-size: 14px;
        }

        .chat-input-container input:focus {
            outline: none;
            border-color: #667eea;
        }

        .chat-suggestions {
            padding: 10px 15px;
            background: #f8f9fa;
            border-top: 1px solid #dee2e6;
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }

        .suggestion-button {
            padding: 6px 12px;
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 15px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .suggestion-button:hover {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }

        @media (max-width: 768px) {
            .dashboard { padding: 10px; }
            .header h1 { font-size: 2rem; }
            .status-grid { grid-template-columns: 1fr; }
            .config-grid { grid-template-columns: 1fr; }
        }
        '''
    
    def _get_dashboard_javascript(self) -> str:
        """Return the JavaScript code for the dashboard"""
        return '''
        let testResults = {};
        let logs = [];
        let autoRefreshTimer = null;

        function log(message, type = 'info') {
            const timestamp = new Date().toLocaleTimeString();
            logs.push({ timestamp, message, type });
            
            const logViewer = document.getElementById('logViewer');
            const logEntry = document.createElement('div');
            logEntry.className = `log-entry ${type}`;
            logEntry.innerHTML = `
                <span class="timestamp">[${timestamp}]</span>
                <span class="message">${message}</span>
            `;
            logViewer.appendChild(logEntry);
            logViewer.scrollTop = logViewer.scrollHeight;
        }

        function updateStatus(test, status, details = '') {
            testResults[test] = status;
            
            const icon = document.getElementById(test + 'Icon');
            if (icon) {
                icon.className = `status-icon status-${status}`;
                icon.textContent = status === 'success' ? '✓' : 
                                 status === 'error' ? '✗' : 
                                 status === 'warning' ? '⚠' : 
                                 status === 'loading' ? '⟳' : '?';
            }
            
            const detailsEl = document.getElementById(test + 'Details');
            if (detailsEl && details) {
                detailsEl.textContent = details;
            }
            
            updateOverallStatus();
        }

        function updateOverallStatus() {
            const results = Object.values(testResults);
            const passed = results.filter(r => r === 'success').length;
            const failed = results.filter(r => r === 'error').length;
            const total = Math.max(results.length, 6); // We have 6 test categories
            
            const overallEl = document.getElementById('overallStatus');
            const statusIcon = overallEl.querySelector('.status-icon');
            const statusTitle = overallEl.querySelector('.status-title');
            const statusSubtitle = overallEl.querySelector('.status-subtitle');
            
            if (passed === total) {
                statusIcon.className = 'status-icon status-success';
                statusIcon.textContent = '✓';
                statusTitle.textContent = 'All Systems Operational';
                statusSubtitle.textContent = `${passed}/${total} tests passed`;
            } else if (failed > 0) {
                statusIcon.className = 'status-icon status-error';
                statusIcon.textContent = '✗';
                statusTitle.textContent = 'Issues Detected';
                statusSubtitle.textContent = `${failed} failures, ${passed} passing`;
            } else {
                statusIcon.className = 'status-icon status-warning';
                statusIcon.textContent = '⚠';
                statusTitle.textContent = 'Partial Functionality';
                statusSubtitle.textContent = `${passed}/${total} tests completed`;
            }
        }

        async function testBotHealth() {
            updateStatus('botHealth', 'loading');
            log('Testing bot health...', 'info');
            
            try {
                const response = await fetch('/admin/api/test-health');
                const result = await response.json();
                
                if (result.status === 'success') {
                    const data = result.data;
                    const details = `Environment: ${data.has_critical_vars ? 'OK' : 'Missing vars'}
Python: ${data.python_version.split(' ')[0]}
Translator: ${data.sql_translator_available ? 'Available' : 'Not available'}`;
                    
                    updateStatus('botHealth', 'success', details);
                    log('✅ Bot health check passed', 'success');
                } else {
                    updateStatus('botHealth', 'error', result.error);
                    log(`❌ Bot health check failed: ${result.error}`, 'error');
                }
            } catch (error) {
                updateStatus('botHealth', 'error', `Connection failed: ${error.message}`);
                log(`❌ Bot health test failed: ${error.message}`, 'error');
            }
        }

        async function testOpenAI() {
            updateStatus('openai', 'loading');
            log('Testing Azure OpenAI connection...', 'info');
            
            try {
                const response = await fetch('/admin/api/test-openai');
                const result = await response.json();
                
                if (result.status === 'success' && result.data.success) {
                    const details = `Status: Connected
Deployment: ${result.data.details.deployment}
Response: ${result.data.details.status_code}`;
                    
                    updateStatus('openai', 'success', details);
                    log('✅ Azure OpenAI connection successful', 'success');
                } else {
                    const error = result.data ? result.data.error : result.error;
                    updateStatus('openai', 'error', error);
                    log(`❌ Azure OpenAI test failed: ${error}`, 'error');
                }
            } catch (error) {
                updateStatus('openai', 'error', `Test failed: ${error.message}`);
                log(`❌ OpenAI test error: ${error.message}`, 'error');
            }
        }

        async function testSQLFunction() {
            updateStatus('sqlFunction', 'loading');
            log('Testing SQL Function...', 'info');
            
            try {
                const response = await fetch('/admin/api/test-function');
                const result = await response.json();
                
                if (result.status === 'success' && result.data.success) {
                    const details = `Status: Connected
Databases: ${result.data.details.databases_found}
Auth: ${result.data.details.has_function_key ? 'Key provided' : 'No key'}`;
                    
                    updateStatus('sqlFunction', 'success', details);
                    log(`✅ SQL Function test passed - ${result.data.details.databases_found} databases found`, 'success');
                } else {
                    const error = result.data ? result.data.error : result.error;
                    updateStatus('sqlFunction', 'error', error);
                    log(`❌ SQL Function test failed: ${error}`, 'error');
                }
            } catch (error) {
                updateStatus('sqlFunction', 'error', `Test failed: ${error.message}`);
                log(`❌ Function test error: ${error.message}`, 'error');
            }
        }

        async function testMessaging() {
            updateStatus('messaging', 'loading');
            log('Testing bot messaging endpoint...', 'info');
            
            try {
                const response = await fetch('/api/messages');
                
                if (response.status === 405) {
                    updateStatus('messaging', 'success', 'Endpoint responding (405 = Method Not Allowed for GET is expected)');
                    log('✅ Bot messaging endpoint is working correctly', 'success');
                } else if (response.status === 401) {
                    updateStatus('messaging', 'warning', 'Authentication required but endpoint accessible');
                    log('⚠️ Bot messaging requires authentication', 'warning');
                } else {
                    updateStatus('messaging', 'warning', `Unexpected response: ${response.status}`);
                    log(`⚠️ Messaging endpoint returned: ${response.status}`, 'warning');
                }
            } catch (error) {
                updateStatus('messaging', 'error', `Cannot reach endpoint: ${error.message}`);
                log(`❌ Messaging test failed: ${error.message}`, 'error');
            }
        }

        async function testEnvironment() {
            updateStatus('environment', 'loading');
            log('Testing environment configuration...', 'info');
            
            try {
                const response = await fetch('/admin/api/test-health');
                const result = await response.json();
                
                if (result.status === 'success') {
                    const data = result.data;
                    const missing = data.missing_variables.length;
                    const details = `Variables: ${missing === 0 ? 'All configured' : `${missing} missing`}
Working Dir: ${data.working_directory}
Critical Vars: ${data.has_critical_vars ? 'OK' : 'Missing'}`;
                    
                    const status = missing === 0 ? 'success' : 'error';
                    updateStatus('environment', status, details);
                    log(`${status === 'success' ? '✅' : '❌'} Environment check: ${missing} missing variables`, status === 'success' ? 'success' : 'error');
                } else {
                    updateStatus('environment', 'error', result.error);
                    log(`❌ Environment test failed: ${result.error}`, 'error');
                }
            } catch (error) {
                updateStatus('environment', 'error', `Test failed: ${error.message}`);
                log(`❌ Environment test error: ${error.message}`, 'error');
            }
        }

        async function testPerformance() {
            updateStatus('performance', 'loading');
            log('Testing performance...', 'info');
            
            try {
                const startTime = performance.now();
                const response = await fetch('/admin/api/test-performance');
                const endTime = performance.now();
                const clientLatency = Math.round(endTime - startTime);
                
                const result = await response.json();
                
                if (result.status === 'success') {
                    const data = result.data;
                    const details = `Response Time: ${clientLatency}ms
Server Time: ${data.response_time_ms}ms
Memory: ${data.memory_info.memory_usage_mb || 'N/A'}MB`;
                    
                    const status = clientLatency > 2000 ? 'warning' : 'success';
                    updateStatus('performance', status, details);
                    log(`${status === 'success' ? '✅' : '⚠️'} Performance test: ${clientLatency}ms latency`, status === 'success' ? 'success' : 'warning');
                } else {
                    updateStatus('performance', 'error', result.error);
                    log(`❌ Performance test failed: ${result.error}`, 'error');
                }
            } catch (error) {
                updateStatus('performance', 'error', `Test failed: ${error.message}`);
                log(`❌ Performance test error: ${error.message}`, 'error');
            }
        }

        async function runAllTests() {
            log('🚀 Starting comprehensive test suite...', 'info');
            
            // Reset all status indicators
            const tests = ['botHealth', 'openai', 'sqlFunction', 'messaging', 'environment', 'performance'];
            tests.forEach(test => updateStatus(test, 'loading'));
            
            // Run tests in sequence with small delays
            await testBotHealth();
            await new Promise(resolve => setTimeout(resolve, 500));
            
            await testEnvironment();
            await new Promise(resolve => setTimeout(resolve, 500));
            
            await testMessaging();
            await new Promise(resolve => setTimeout(resolve, 500));
            
            await testOpenAI();
            await new Promise(resolve => setTimeout(resolve, 500));
            
            await testSQLFunction();
            await new Promise(resolve => setTimeout(resolve, 500));
            
            await testPerformance();
            
            // Final summary
            const results = Object.values(testResults);
            const passed = results.filter(r => r === 'success').length;
            const total = results.length;
            
            if (passed === total) {
                log('🎉 All tests passed! System is fully operational.', 'success');
            } else {
                log(`⚠️ Testing completed: ${passed}/${total} tests passed`, 'warning');
            }
        }

        function refreshStatus() {
            log('🔄 Refreshing dashboard...', 'info');
            runAllTests();
        }

        function clearLogs() {
            logs = [];
            document.getElementById('logViewer').innerHTML = '';
            log('Logs cleared', 'info');
        }

        function exportLogs() {
            const logText = logs.map(log => `[${log.timestamp}] ${log.type.toUpperCase()}: ${log.message}`).join('\\n');
            const blob = new Blob([logText], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `bot-dashboard-logs-${new Date().toISOString().split('T')[0]}.txt`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            log('📥 Logs exported to file', 'success');
        }

        function exportReport() {
            const report = {
                timestamp: new Date().toISOString(),
                config: CONFIG,
                testResults: testResults,
                logs: logs,
                summary: {
                    totalTests: Object.keys(testResults).length,
                    passedTests: Object.values(testResults).filter(r => r === 'success').length,
                    failedTests: Object.values(testResults).filter(r => r === 'error').length
                }
            };
            
            const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `bot-status-report-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            log('📊 Status report exported', 'success');
        }

        function toggleAutoRefresh() {
            const checkbox = document.getElementById('autoRefresh');
            
            if (checkbox.checked) {
                autoRefreshTimer = setInterval(() => {
                    log('⏰ Auto-refresh triggered', 'info');
                    runAllTests();
                }, 60000); // Every minute
                
                log('⏰ Auto-refresh enabled (every 60 seconds)', 'success');
            } else {
                if (autoRefreshTimer) {
                    clearInterval(autoRefreshTimer);
                    autoRefreshTimer = null;
                }
                log('⏹️ Auto-refresh disabled', 'info');
            }
        }

        function updateCurrentTime() {
            document.getElementById('currentTime').textContent = new Date().toLocaleString();
        }

        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            log('🚀 Admin dashboard initialized', 'success');
            log(`📍 Server: ${CONFIG.botUrl}`, 'info');
            log('💡 Tip: Enable auto-refresh to monitor system continuously', 'info');
            
            // Update time every second
            setInterval(updateCurrentTime, 1000);
            
            // Run initial health check
            setTimeout(() => {
                log('🔄 Running initial system check...', 'info');
                testBotHealth();
            }, 1000);
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 'r':
                        e.preventDefault();
                        runAllTests();
                        break;
                    case 'l':
                        e.preventDefault();
                        clearLogs();
                        break;
                }
            }
        });

        // Chat Console Functions
        function addChatMessage(content, sender = 'user', type = 'normal') {
            const chatMessages = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            
            let className = 'chat-message ';
            if (sender === 'user') className += 'user';
            else if (sender === 'bot') className += 'bot';
            else if (sender === 'system') className += 'system';
            else if (type === 'error') className += 'error';
            
            messageDiv.className = className;
            messageDiv.innerHTML = `
                <div class="message-content">${sender === 'user' ? '<strong>You:</strong> ' : sender === 'bot' ? '<strong>Bot:</strong> ' : '<strong>System:</strong> '}${content}</div>
                <div class="message-time">${new Date().toLocaleTimeString()}</div>
            `;
            
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        async function sendChatMessage() {
            const input = document.getElementById('chatInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message to chat
            addChatMessage(message, 'user');
            input.value = '';
            
            // Log the attempt
            log(`💬 Sending message to bot: "${message}"`, 'info');
            
            try {
                // Create mock Teams activity
                const mockActivity = {
                    type: 'message',
                    id: 'admin-test-' + Date.now(),
                    timestamp: new Date().toISOString(),
                    channelId: 'admin-console',
                    from: {
                        id: 'admin-user',
                        name: 'Admin Console User'
                    },
                    conversation: {
                        id: 'admin-console-conversation'
                    },
                    recipient: {
                        id: 'sql-assistant-bot',
                        name: 'SQL Assistant Bot'
                    },
                    text: message,
                    locale: 'en-US'
                };
                
                // Send to bot
                const response = await fetch('/api/messages', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(mockActivity)
                });
                
                if (response.status === 200) {
                    // Bot processed successfully but we can't get the response
                    // (Bot Framework doesn't return response content)
                    addChatMessage('Message processed successfully! (Bot response would appear in Teams)', 'system');
                    log('✅ Bot processed message successfully', 'success');
                } else if (response.status === 401) {
                    addChatMessage('Authentication required - but message format was accepted', 'system');
                    log('⚠️ Bot requires authentication for full processing', 'warning');
                } else {
                    const errorText = await response.text();
                    addChatMessage(`Error: ${response.status} - ${errorText}`, 'system', 'error');
                    log(`❌ Bot returned error: ${response.status}`, 'error');
                }
                
            } catch (error) {
                addChatMessage(`Connection error: ${error.message}`, 'system', 'error');
                log(`❌ Chat error: ${error.message}`, 'error');
            }
        }

        function sendQuickMessage(message) {
            document.getElementById('chatInput').value = message;
            sendChatMessage();
        }

        function handleChatKeypress(event) {
            if (event.key === 'Enter') {
                sendChatMessage();
            }
        }

        function clearChat() {
            const chatMessages = document.getElementById('chatMessages');
            chatMessages.innerHTML = `
                <div class="chat-message system">
                    <div class="message-content">
                        <strong>System:</strong> Chat cleared. Ready for new conversation!
                    </div>
                    <div class="message-time">${new Date().toLocaleTimeString()}</div>
                </div>
            `;
            log('💬 Chat console cleared', 'info');
        '''

# Add routes to the main app
def add_admin_routes(app, sql_translator=None, executor=None):
    """Add admin dashboard routes to the main Flask/aiohttp app"""
    
    dashboard = AdminDashboard(sql_translator, executor)
    
    # Main dashboard page
    app.router.add_get('/admin', dashboard.dashboard_page)
    app.router.add_get('/admin/', dashboard.dashboard_page)
    
    # API endpoints
    app.router.add_get('/admin/api/test-health', dashboard.api_test_health)
    app.router.add_get('/admin/api/test-openai', dashboard.api_test_openai)
    app.router.add_get('/admin/api/test-function', dashboard.api_test_function)
    app.router.add_get('/admin/api/test-performance', dashboard.api_test_performance)
    
    return dashboard