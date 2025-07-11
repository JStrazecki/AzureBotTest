# sql_console_html.py - SQL Console HTML Generation with Cancel Button
"""
SQL Console HTML - Enhanced with cancel button and better UI
"""

from sql_console_ui import get_sql_console_css
from sql_console_javascript import get_sql_console_javascript

def get_sql_console_html():
    """Generate the complete SQL console HTML with cancel button"""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SQL Assistant Console</title>
    <style>
        {get_sql_console_css()}
        
        /* Additional styles for cancel button and spinner */
        .cancel-button {{
            display: none;
            padding: 0.75rem 1.5rem;
            background-color: #ef4444;
            color: white;
            border: none;
            border-radius: 0.5rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 0.875rem;
        }}
        
        .cancel-button:hover {{
            background-color: #dc2626;
        }}
        
        .spinner {{
            display: inline-block;
            width: 14px;
            height: 14px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}
        
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        
        /* Log message styles */
        .log-message .message-content {{
            border-left: 3px solid;
            background-color: rgba(30, 41, 59, 0.5) !important;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Sidebar -->
        <div class="sidebar">
            <div class="sidebar-header">
                <div class="sidebar-title">SQL Explorer</div>
                <div class="current-db">Current: <span id="currentDatabase">master</span></div>
                <div class="user-info">
                    <div class="user-label">Logged in as:</div>
                    <div class="user-name" id="currentUser">Loading...</div>
                </div>
            </div>
            
            <div class="database-section">
                <div class="section-header">
                    <div class="section-title">Databases (MSI Access)</div>
                    <button class="refresh-button" onclick="refreshDatabases()">Refresh</button>
                </div>
                
                <!-- Multi-database query toggle -->
                <div class="multi-db-toggle">
                    <label class="toggle-container">
                        <input type="checkbox" id="multiDbMode" onchange="toggleMultiDbMode()">
                        <span class="toggle-label">Multi-Database Query</span>
                    </label>
                    <button id="selectAllDbBtn" class="select-all-btn" style="display: none;" onclick="toggleAllDatabases()">
                        Select All
                    </button>
                </div>
                
                <div class="database-list" id="databaseList">
                    <!-- Will be populated with known databases -->
                </div>
                
                <!-- Selected databases indicator -->
                <div id="selectedDbIndicator" class="selected-db-indicator" style="display: none;">
                    <div class="selected-count">0 databases selected</div>
                </div>
            </div>
            
            <div class="database-section">
                <div class="section-header">
                    <div class="section-title">Tables</div>
                </div>
                <div class="table-list" id="tableList">
                    <div class="loading-indicator">Select a database</div>
                </div>
            </div>
        </div>

        <!-- Main Content -->
        <div class="main-content">
            <div class="header">
                <div class="header-content">
                    <h1 class="title">SQL Assistant Console</h1>
                    <div class="quick-actions">
                        <button class="quick-action" onclick="quickCommand('SELECT TOP 10 * FROM ')">Select Top 10</button>
                        <button class="quick-action" onclick="quickCommand('SHOW TABLES')">Show Tables</button>
                        <button class="quick-action" onclick="quickCommand('sp_databases')">List All DBs</button>
                        <button class="quick-action" onclick="quickCommand('help')">Help</button>
                        <a href="/admin" class="quick-action" style="text-decoration: none;">Admin</a>
                    </div>
                </div>
            </div>

            <div class="chat-container">
                <div class="messages-container" id="messagesContainer">
                    <!-- Welcome message -->
                    <div class="message bot">
                        <div class="message-content">
                            <div class="message-header">SQL Assistant</div>
                            <div class="message-text">Welcome to SQL Assistant Console! I can help you explore databases and write SQL queries.

<strong>Available Databases (MSI Access):</strong>
• master - System metadata
• _support - Support database  
• demo - Demo database

Try commands like:
• "Show me all tables"
• "What columns does the users table have?"
• "Find the top 10 customers by order count"
• Direct SQL queries: SELECT, WITH, etc.

<strong>Multi-Database Queries:</strong>
• Toggle "Multi-Database Query" mode in the sidebar
• Select multiple databases to query across them
• Results will be grouped by database

Type 'help' for more information.

<strong>Note:</strong> The console now shows detailed processing steps for better visibility.</div>
                        </div>
                    </div>
                </div>

                <div class="input-area">
                    <!-- Multi-database indicator -->
                    <div id="multiDbIndicator" class="multi-db-indicator" style="display: none;">
                        <span class="indicator-icon">🗄️</span>
                        <span class="indicator-text">Multi-database mode: <span id="selectedDbCount">0</span> databases selected</span>
                    </div>
                    
                    <div class="input-container">
                        <div class="input-wrapper">
                            <textarea 
                                id="messageInput" 
                                placeholder="Type your SQL query or ask a question..."
                                rows="1"
                                onkeydown="handleKeyPress(event)"
                            ></textarea>
                        </div>
                        <button id="sendButton" class="send-button" onclick="sendMessage()">
                            Send
                        </button>
                        <button id="cancelButton" class="cancel-button" onclick="cancelRequest()">
                            Cancel
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        {get_sql_console_javascript()}
    </script>
</body>
</html>'''