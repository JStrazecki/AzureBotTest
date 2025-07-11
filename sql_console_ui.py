<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SQL Assistant Console</title>
    <style>
        /* sql_console_ui.py - CSS styles */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #0f172a;
            color: #e2e8f0;
            height: 100vh;
            overflow: hidden;
        }

        .container {
            display: flex;
            height: 100vh;
        }

        /* Sidebar */
        .sidebar {
            width: 280px;
            background-color: #1e293b;
            border-right: 1px solid #334155;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .sidebar-header {
            padding: 1.5rem;
            border-bottom: 1px solid #334155;
        }

        .sidebar-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: #f1f5f9;
            margin-bottom: 0.5rem;
        }

        .current-db {
            font-size: 0.875rem;
            color: #94a3b8;
        }

        .current-db span {
            color: #3b82f6;
            font-weight: 500;
        }

        /* Database section */
        .database-section {
            flex: 1;
            overflow-y: auto;
            padding: 1rem;
        }

        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }

        .section-title {
            font-size: 0.875rem;
            font-weight: 600;
            color: #cbd5e1;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .refresh-button {
            background: none;
            border: none;
            color: #3b82f6;
            cursor: pointer;
            font-size: 0.875rem;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            transition: all 0.2s;
        }

        .refresh-button:hover {
            background-color: #1e3a8a;
            color: #93bbfc;
        }

        .database-list, .table-list {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }

        .database-item, .table-item {
            padding: 0.5rem 0.75rem;
            border-radius: 0.375rem;
            cursor: pointer;
            font-size: 0.875rem;
            color: #e2e8f0;
            transition: all 0.2s;
            position: relative;
        }

        .database-item:hover, .table-item:hover {
            background-color: #334155;
        }

        .database-item.active {
            background-color: #1e3a8a;
            color: #93bbfc;
        }

        .table-item {
            padding-left: 1.5rem;
            color: #94a3b8;
        }

        .table-item:before {
            content: "📊";
            position: absolute;
            left: 0.5rem;
        }

        /* Main content */
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        /* Header */
        .header {
            background-color: #1e293b;
            border-bottom: 1px solid #334155;
            padding: 1.5rem 2rem;
        }

        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .title {
            font-size: 1.75rem;
            font-weight: 700;
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .quick-actions {
            display: flex;
            gap: 0.5rem;
        }

        .quick-action {
            padding: 0.5rem 1rem;
            background-color: #334155;
            border: 1px solid #475569;
            border-radius: 0.375rem;
            color: #e2e8f0;
            font-size: 0.75rem;
            cursor: pointer;
            transition: all 0.2s;
        }

        .quick-action:hover {
            background-color: #475569;
            border-color: #64748b;
        }

        /* Chat container */
        .chat-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .messages-container {
            flex: 1;
            overflow-y: auto;
            padding: 2rem;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        /* Messages */
        .message {
            max-width: 80%;
            animation: fadeIn 0.3s ease-out;
        }

        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .message.user {
            align-self: flex-end;
        }

        .message.bot {
            align-self: flex-start;
        }

        .message-content {
            padding: 1rem 1.5rem;
            border-radius: 1rem;
            position: relative;
        }

        .message.user .message-content {
            background-color: #3b82f6;
            color: white;
            border-bottom-right-radius: 0.25rem;
        }

        .message.bot .message-content {
            background-color: #1e293b;
            border: 1px solid #334155;
            border-bottom-left-radius: 0.25rem;
        }

        .message-header {
            font-size: 0.75rem;
            color: #94a3b8;
            margin-bottom: 0.5rem;
        }

        .message-text {
            font-size: 0.875rem;
            line-height: 1.5;
            white-space: pre-wrap;
            word-wrap: break-word;
        }

        /* SQL Result */
        .sql-result {
            background-color: #1e293b;
            border: 1px solid #334155;
            border-radius: 0.5rem;
            padding: 1rem;
            margin-top: 0.5rem;
            overflow-x: auto;
        }

        .result-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid #334155;
        }

        .result-info {
            font-size: 0.75rem;
            color: #94a3b8;
        }

        .sql-query {
            background-color: #0f172a;
            border: 1px solid #334155;
            border-radius: 0.375rem;
            padding: 0.75rem;
            margin-bottom: 1rem;
            font-family: 'Courier New', monospace;
            font-size: 0.875rem;
            color: #93bbfc;
            overflow-x: auto;
        }

        .result-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.875rem;
        }

        .result-table th {
            background-color: #0f172a;
            color: #cbd5e1;
            padding: 0.5rem;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #334155;
        }

        .result-table td {
            padding: 0.5rem;
            border-bottom: 1px solid #1e293b;
            color: #e2e8f0;
        }

        .result-table tr:hover {
            background-color: #334155;
        }

        /* Error message */
        .error-message {
            background-color: #7f1d1d;
            border: 1px solid #991b1b;
            color: #fecaca;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-top: 0.5rem;
        }

        /* Input area */
        .input-area {
            padding: 1.5rem 2rem;
            background-color: #1e293b;
            border-top: 1px solid #334155;
        }

        .input-container {
            display: flex;
            gap: 1rem;
            align-items: flex-end;
        }

        .input-wrapper {
            flex: 1;
            position: relative;
        }

        #messageInput {
            width: 100%;
            padding: 0.75rem 1rem;
            background-color: #0f172a;
            border: 1px solid #334155;
            border-radius: 0.5rem;
            color: #e2e8f0;
            font-size: 0.875rem;
            resize: none;
            min-height: 2.5rem;
            max-height: 8rem;
            font-family: inherit;
            line-height: 1.5;
        }

        #messageInput:focus {
            outline: none;
            border-color: #3b82f6;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        #messageInput::placeholder {
            color: #64748b;
        }

        .send-button {
            padding: 0.75rem 1.5rem;
            background-color: #3b82f6;
            color: white;
            border: none;
            border-radius: 0.5rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 0.875rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .send-button:hover:not(:disabled) {
            background-color: #2563eb;
        }

        .send-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        /* Typing indicator */
        .typing-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 1rem;
            background-color: #1e293b;
            border: 1px solid #334155;
            border-radius: 1rem;
            border-bottom-left-radius: 0.25rem;
            max-width: 200px;
        }

        .typing-dot {
            width: 8px;
            height: 8px;
            background-color: #64748b;
            border-radius: 50%;
            animation: typing 1.4s infinite ease-in-out;
        }

        .typing-dot:nth-child(1) {
            animation-delay: -0.32s;
        }

        .typing-dot:nth-child(2) {
            animation-delay: -0.16s;
        }

        @keyframes typing {
            0%, 80%, 100% {
                transform: scale(0.8);
                opacity: 0.5;
            }
            40% {
                transform: scale(1);
                opacity: 1;
            }
        }

        /* Loading indicator */
        .loading-indicator {
            text-align: center;
            color: #64748b;
            font-size: 0.875rem;
            padding: 1rem;
        }

        /* Console debug panel */
        .debug-panel {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background-color: #1e293b;
            border: 1px solid #334155;
            border-radius: 0.5rem;
            padding: 1rem;
            max-width: 400px;
            max-height: 200px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.75rem;
            display: none;
        }

        .debug-panel.active {
            display: block;
        }

        .debug-entry {
            margin-bottom: 0.5rem;
            padding: 0.25rem;
            border-left: 2px solid #3b82f6;
            padding-left: 0.5rem;
        }

        .debug-entry.error {
            border-left-color: #ef4444;
            color: #fca5a5;
        }

        .debug-entry.success {
            border-left-color: #10b981;
            color: #86efac;
        }

        .debug-toggle {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background-color: #3b82f6;
            color: white;
            border: none;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            cursor: pointer;
            font-size: 1.2rem;
            z-index: 1000;
        }

        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: #0f172a;
        }

        ::-webkit-scrollbar-thumb {
            background: #334155;
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #475569;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .sidebar {
                width: 200px;
            }
            
            .header {
                padding: 1rem;
            }
            
            .title {
                font-size: 1.25rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Sidebar -->
        <div class="sidebar">
            <div class="sidebar-header">
                <div class="sidebar-title">SQL Explorer</div>
                <div class="current-db">Current: <span id="currentDatabase">master</span></div>
            </div>
            
            <div class="database-section">
                <div class="section-header">
                    <div class="section-title">Databases</div>
                    <button class="refresh-button" onclick="refreshDatabases()">Refresh</button>
                </div>
                <div class="database-list" id="databaseList">
                    <div class="loading-indicator">Loading databases...</div>
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
                        <button class="quick-action" onclick="quickCommand('sp_databases')">List Databases</button>
                        <button class="quick-action" onclick="quickCommand('sp_tables')">List Tables</button>
                        <button class="quick-action" onclick="quickCommand('SELECT name FROM sys.schemas')">List Schemas</button>
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

Try commands like:
• "sp_databases" - List all accessible databases
• "sp_tables" - List tables in current database
• "SELECT name FROM sys.schemas" - List schemas
• Direct SQL queries: SELECT, WITH, etc.

Current MSI has access to: master, _support, demo

Type 'help' for more information.</div>
                        </div>
                    </div>
                </div>

                <div class="input-area">
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
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Debug Panel -->
    <button class="debug-toggle" onclick="toggleDebug()">🐛</button>
    <div class="debug-panel" id="debugPanel"></div>

    <script>
        /* sql_console_javascript.py - JavaScript code */
        let currentDatabase = 'master';
        let isProcessing = false;
        let sessionId = generateSessionId();
        let debugMode = false;

        // Initialize
        window.onload = async function() {
            await refreshDatabases();
            document.getElementById('messageInput').focus();
            
            // Auto-resize textarea
            const textarea = document.getElementById('messageInput');
            textarea.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = this.scrollHeight + 'px';
            });
            
            debugLog('Console initialized', 'success');
        };

        function generateSessionId() {
            return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function debugLog(message, type = 'info') {
            const debugPanel = document.getElementById('debugPanel');
            const entry = document.createElement('div');
            entry.className = `debug-entry ${type}`;
            const timestamp = new Date().toLocaleTimeString();
            entry.textContent = `[${timestamp}] ${message}`;
            debugPanel.appendChild(entry);
            debugPanel.scrollTop = debugPanel.scrollHeight;
            
            // Also log to console
            console.log(`[SQL Console Debug] ${message}`);
        }

        function toggleDebug() {
            debugMode = !debugMode;
            const debugPanel = document.getElementById('debugPanel');
            debugPanel.classList.toggle('active');
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }

        function quickCommand(command) {
            document.getElementById('messageInput').value = command;
            document.getElementById('messageInput').focus();
        }

        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message || isProcessing) return;
            
            debugLog(`Sending message: ${message}`, 'info');
            
            isProcessing = true;
            document.getElementById('sendButton').disabled = true;
            
            // Add user message
            addMessage(message, 'user');
            input.value = '';
            input.style.height = 'auto';
            
            // Show typing indicator
            showTypingIndicator();
            
            try {
                const payload = {
                    message: message,
                    database: currentDatabase,
                    session_id: sessionId
                };
                
                debugLog(`Request payload: ${JSON.stringify(payload)}`, 'info');
                
                const response = await fetch('/console/api/message', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(payload)
                });
                
                const result = await response.json();
                
                debugLog(`Response received: ${JSON.stringify(result).substring(0, 200)}...`, 'info');
                
                hideTypingIndicator();
                
                if (result.status === 'success') {
                    // Add bot response
                    if (result.response_type === 'sql_result') {
                        addSQLResult(result);
                    } else if (result.response_type === 'help') {
                        addMessage(result.content, 'bot');
                    } else if (result.response_type === 'error') {
                        addErrorMessage(result.error);
                    } else {
                        addMessage(result.content, 'bot');
                    }
                    
                    // Update current database if changed
                    if (result.current_database && result.current_database !== currentDatabase) {
                        selectDatabase(result.current_database);
                    }
                    
                    // Refresh tables if needed
                    if (result.refresh_tables) {
                        await loadTables(currentDatabase);
                    }
                } else {
                    debugLog(`Error: ${result.error}`, 'error');
                    addErrorMessage(result.error || 'An error occurred');
                }
            } catch (error) {
                debugLog(`Network error: ${error.message}`, 'error');
                hideTypingIndicator();
                addErrorMessage('Connection error: ' + error.message);
            } finally {
                isProcessing = false;
                document.getElementById('sendButton').disabled = false;
                input.focus();
            }
        }

        function addMessage(text, sender) {
            const messagesContainer = document.getElementById('messagesContainer');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;
            
            const time = new Date().toLocaleTimeString();
            const header = sender === 'user' ? 'You' : 'SQL Assistant';
            
            messageDiv.innerHTML = `
                <div class="message-content">
                    <div class="message-header">${header} • ${time}</div>
                    <div class="message-text">${escapeHtml(text)}</div>
                </div>
            `;
            
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function addSQLResult(result) {
            debugLog(`Adding SQL result: ${result.row_count} rows`, 'success');
            
            const messagesContainer = document.getElementById('messagesContainer');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message bot';
            
            const time = new Date().toLocaleTimeString();
            
            let content = `
                <div class="message-content">
                    <div class="message-header">SQL Assistant • ${time}</div>
                    <div class="message-text">${escapeHtml(result.explanation || 'Query executed successfully')}</div>
            `;
            
            if (result.sql_query) {
                content += `
                    <div class="sql-result">
                        <div class="result-header">
                            <div class="result-info">
                                Database: ${result.database || currentDatabase}
                            </div>
                            <div class="result-info">
                                ${result.row_count || 0} rows • ${result.execution_time || 0}ms
                            </div>
                        </div>
                        <div class="sql-query">${escapeHtml(result.sql_query)}</div>
                `;
                
                if (result.rows && result.rows.length > 0) {
                    // Create table
                    const columns = Object.keys(result.rows[0]);
                    content += '<table class="result-table"><thead><tr>';
                    columns.forEach(col => {
                        content += `<th>${escapeHtml(col)}</th>`;
                    });
                    content += '</tr></thead><tbody>';
                    
                    result.rows.forEach(row => {
                        content += '<tr>';
                        columns.forEach(col => {
                            const value = row[col] === null ? 'NULL' : String(row[col]);
                            content += `<td>${escapeHtml(value)}</td>`;
                        });
                        content += '</tr>';
                    });
                    
                    content += '</tbody></table>';
                } else {
                    content += '<div style="color: #64748b; padding: 1rem;">No results returned</div>';
                }
                
                content += '</div>';
            }
            
            content += '</div>';
            
            messageDiv.innerHTML = content;
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function addErrorMessage(error) {
            debugLog(`Error message: ${error}`, 'error');
            
            const messagesContainer = document.getElementById('messagesContainer');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message bot';
            
            const time = new Date().toLocaleTimeString();
            
            messageDiv.innerHTML = `
                <div class="message-content">
                    <div class="message-header">SQL Assistant • ${time}</div>
                    <div class="error-message">❌ ${escapeHtml(error)}</div>
                </div>
            `;
            
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function showTypingIndicator() {
            const messagesContainer = document.getElementById('messagesContainer');
            const typingDiv = document.createElement('div');
            typingDiv.id = 'typingIndicator';
            typingDiv.className = 'message bot';
            typingDiv.innerHTML = `
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <span>SQL Assistant is thinking...</span>
                </div>
            `;
            
            messagesContainer.appendChild(typingDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function hideTypingIndicator() {
            const indicator = document.getElementById('typingIndicator');
            if (indicator) {
                indicator.remove();
            }
        }

        async function refreshDatabases() {
            debugLog('Refreshing databases...', 'info');
            
            const databaseList = document.getElementById('databaseList');
            databaseList.innerHTML = '<div class="loading-indicator">Loading databases...</div>';
            
            try {
                const response = await fetch('/console/api/databases');
                const result = await response.json();
                
                debugLog(`Databases loaded: ${result.databases ? result.databases.length : 0}`, 'success');
                
                if (result.status === 'success' && result.databases) {
                    databaseList.innerHTML = '';
                    
                    result.databases.forEach(db => {
                        const dbItem = document.createElement('div');
                        dbItem.className = 'database-item';
                        if (db === currentDatabase) {
                            dbItem.classList.add('active');
                        }
                        dbItem.textContent = db;
                        dbItem.onclick = () => selectDatabase(db);
                        databaseList.appendChild(dbItem);
                    });
                    
                    if (result.databases.length === 0) {
                        databaseList.innerHTML = '<div style="color: #666; font-size: 0.85rem;">No databases found</div>';
                    }
                } else {
                    databaseList.innerHTML = '<div style="color: #dc2626; font-size: 0.85rem;">Error loading databases</div>';
                }
            } catch (error) {
                debugLog(`Database loading error: ${error.message}`, 'error');
                databaseList.innerHTML = '<div style="color: #dc2626; font-size: 0.85rem;">Connection error</div>';
            }
        }

        async function selectDatabase(dbName) {
            debugLog(`Switching to database: ${dbName}`, 'info');
            
            currentDatabase = dbName;
            document.getElementById('currentDatabase').textContent = dbName;
            
            // Update active state in list
            document.querySelectorAll('.database-item').forEach(item => {
                item.classList.remove('active');
                if (item.textContent === dbName) {
                    item.classList.add('active');
                }
            });
            
            // Load tables
            await loadTables(dbName);
            
            // Add notification
            addMessage(`Database changed to: ${dbName}`, 'bot');
        }

        async function loadTables(database) {
            if (!database) return;
            
            debugLog(`Loading tables for database: ${database}`, 'info');
            
            const tableList = document.getElementById('tableList');
            tableList.innerHTML = '<div class="loading-indicator">Loading tables...</div>';
            
            try {
                const response = await fetch(`/console/api/tables?database=${encodeURIComponent(database)}`);
                const result = await response.json();
                
                debugLog(`Tables loaded: ${result.tables ? result.tables.length : 0}`, 'success');
                
                if (result.status === 'success' && result.tables) {
                    tableList.innerHTML = '';
                    
                    if (result.tables.length === 0) {
                        tableList.innerHTML = '<div style="color: #666; font-size: 0.85rem;">No tables found</div>';
                    } else {
                        result.tables.forEach(table => {
                            const tableItem = document.createElement('div');
                            tableItem.className = 'table-item';
                            tableItem.textContent = table;
                            tableItem.onclick = () => {
                                document.getElementById('messageInput').value = `SELECT TOP 10 * FROM ${table}`;
                                document.getElementById('messageInput').focus();
                            };
                            tableList.appendChild(tableItem);
                        });
                    }
                } else {
                    tableList.innerHTML = '<div style="color: #dc2626; font-size: 0.85rem;">Error loading tables</div>';
                }
            } catch (error) {
                debugLog(`Table loading error: ${error.message}`, 'error');
                tableList.innerHTML = '<div style="color: #dc2626; font-size: 0.85rem;">Connection error</div>';
            }
        }
    </script>
</body>
</html>