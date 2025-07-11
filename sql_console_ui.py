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

        .refresh-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
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

        .message.system {
            align-self: center;
            max-width: 90%;
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

        .message.system .message-content {
            background-color: #0f172a;
            border: 1px solid #475569;
            font-size: 0.875rem;
            padding: 0.75rem 1rem;
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

        /* Process steps */
        .process-steps {
            background-color: #0f172a;
            border: 1px solid #334155;
            border-radius: 0.5rem;
            padding: 1rem;
            margin-top: 0.5rem;
            font-family: 'Courier New', monospace;
            font-size: 0.8rem;
        }

        .process-step {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.5rem;
            color: #94a3b8;
        }

        .process-step.completed {
            color: #10b981;
        }

        .process-step.error {
            color: #ef4444;
        }

        .process-step.active {
            color: #3b82f6;
        }

        .step-icon {
            width: 16px;
            height: 16px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }

        .step-spinner {
            width: 12px;
            height: 12px;
            border: 2px solid #3b82f6;
            border-top-color: transparent;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
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

        .action-buttons {
            display: flex;
            gap: 0.5rem;
        }

        .send-button, .cancel-button {
            padding: 0.75rem 1.5rem;
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

        .send-button {
            background-color: #3b82f6;
            color: white;
        }

        .send-button:hover:not(:disabled) {
            background-color: #2563eb;
        }

        .send-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .cancel-button {
            background-color: #dc2626;
            color: white;
            display: none;
        }

        .cancel-button.active {
            display: flex;
        }

        .cancel-button:hover {
            background-color: #b91c1c;
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

        /* Empty state */
        .empty-state {
            text-align: center;
            color: #64748b;
            padding: 2rem;
            font-size: 0.875rem;
        }

        .empty-state-icon {
            font-size: 2rem;
            margin-bottom: 1rem;
            opacity: 0.5;
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
                <div class="current-db">Current: <span id="currentDatabase">Not Connected</span></div>
            </div>
            
            <div class="database-section">
                <div class="section-header">
                    <div class="section-title">Databases</div>
                    <button class="refresh-button" id="refreshDbButton" onclick="refreshDatabases()">Load</button>
                </div>
                <div class="database-list" id="databaseList">
                    <div class="empty-state">
                        <div class="empty-state-icon">🗄️</div>
                        <div>Click "Load" to fetch databases</div>
                    </div>
                </div>
            </div>
            
            <div class="database-section">
                <div class="section-header">
                    <div class="section-title">Tables</div>
                </div>
                <div class="table-list" id="tableList">
                    <div class="empty-state">
                        <div class="empty-state-icon">📊</div>
                        <div>Select a database first</div>
                    </div>
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

⚠️ Important: Click "Load" in the sidebar to fetch available databases. No automatic loading for security.

Try commands like:
• "sp_databases" - List all accessible databases
• "sp_tables" - List tables in current database
• "SELECT name FROM sys.schemas" - List schemas
• Direct SQL queries: SELECT, WITH, etc.

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
                        <div class="action-buttons">
                            <button id="cancelButton" class="cancel-button" onclick="cancelOperation()">
                                Cancel
                            </button>
                            <button id="sendButton" class="send-button" onclick="sendMessage()">
                                Send
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        /* sql_console_javascript.py - JavaScript code with enhanced features */
        let currentDatabase = null;
        let isProcessing = false;
        let sessionId = generateSessionId();
        let currentAbortController = null;
        let databasesLoaded = false;

        // Initialize
        window.onload = function() {
            document.getElementById('messageInput').focus();
            
            // Auto-resize textarea
            const textarea = document.getElementById('messageInput');
            textarea.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = this.scrollHeight + 'px';
            });
            
            addSystemMessage('Console initialized. Click "Load" in the sidebar to fetch available databases.');
        };

        function generateSessionId() {
            return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
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

        function addSystemMessage(text) {
            const messagesContainer = document.getElementById('messagesContainer');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message system';
            
            const time = new Date().toLocaleTimeString();
            
            messageDiv.innerHTML = `
                <div class="message-content">
                    <div class="message-text">ℹ️ ${escapeHtml(text)}</div>
                </div>
            `;
            
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function showProcessSteps(processId) {
            const messagesContainer = document.getElementById('messagesContainer');
            const processDiv = document.createElement('div');
            processDiv.className = 'message system';
            processDiv.id = `process-${processId}`;
            
            processDiv.innerHTML = `
                <div class="message-content">
                    <div class="message-header">Processing...</div>
                    <div class="process-steps" id="steps-${processId}">
                    </div>
                </div>
            `;
            
            messagesContainer.appendChild(processDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
            
            return processId;
        }

        function updateProcessStep(processId, stepId, text, status = 'active') {
            const stepsContainer = document.getElementById(`steps-${processId}`);
            if (!stepsContainer) return;
            
            let stepElement = document.getElementById(`step-${processId}-${stepId}`);
            
            if (!stepElement) {
                stepElement = document.createElement('div');
                stepElement.id = `step-${processId}-${stepId}`;
                stepElement.className = 'process-step';
                stepsContainer.appendChild(stepElement);
            }
            
            stepElement.className = `process-step ${status}`;
            
            let icon = '';
            if (status === 'active') {
                icon = '<div class="step-spinner"></div>';
            } else if (status === 'completed') {
                icon = '✓';
            } else if (status === 'error') {
                icon = '✗';
            }
            
            stepElement.innerHTML = `
                <span class="step-icon">${icon}</span>
                <span>${escapeHtml(text)}</span>
            `;
            
            // Scroll to bottom
            const messagesContainer = document.getElementById('messagesContainer');
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message || isProcessing) return;
            
            // Check if databases are loaded for non-database commands
            if (!databasesLoaded && !currentDatabase && !message.toLowerCase().includes('sp_databases')) {
                addSystemMessage('Please load databases first by clicking "Load" in the sidebar.');
                return;
            }
            
            isProcessing = true;
            document.getElementById('sendButton').disabled = true;
            document.getElementById('cancelButton').classList.add('active');
            
            // Create abort controller for cancellation
            currentAbortController = new AbortController();
            
            // Add user message
            addMessage(message, 'user');
            input.value = '';
            input.style.height = 'auto';
            
            // Show process steps
            const processId = Date.now();
            showProcessSteps(processId);
            
            try {
                // Step 1: Validate input
                updateProcessStep(processId, 1, 'Validating input...', 'active');
                await sleep(300);
                updateProcessStep(processId, 1, 'Input validated', 'completed');
                
                // Step 2: Check database context
                updateProcessStep(processId, 2, `Checking database context: ${currentDatabase || 'None selected'}`, 'active');
                await sleep(300);
                
                if (!currentDatabase && !message.toLowerCase().includes('database')) {
                    updateProcessStep(processId, 2, 'No database selected, using master', 'completed');
                    currentDatabase = 'master';
                } else {
                    updateProcessStep(processId, 2, `Using database: ${currentDatabase || 'master'}`, 'completed');
                }
                
                // Step 3: Prepare request
                updateProcessStep(processId, 3, 'Preparing request...', 'active');
                
                const payload = {
                    message: message,
                    database: currentDatabase || 'master',
                    session_id: sessionId
                };
                
                updateProcessStep(processId, 3, 'Request prepared', 'completed');
                
                // Step 4: Send to server
                updateProcessStep(processId, 4, 'Sending to SQL Assistant server...', 'active');
                
                const response = await fetch('/console/api/message', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(payload),
                    signal: currentAbortController.signal
                });
                
                updateProcessStep(processId, 4, 'Response received from server', 'completed');
                
                // Step 5: Process response
                updateProcessStep(processId, 5, 'Processing response...', 'active');
                
                const result = await response.json();
                
                // Hide process steps
                const processDiv = document.getElementById(`process-${processId}`);
                if (processDiv) {
                    processDiv.style.display = 'none';
                }
                
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
                    
                    // Refresh databases if sp_databases was called
                    if (message.toLowerCase().includes('sp_databases')) {
                        await refreshDatabasesFromResult(result);
                    }
                } else {
                    updateProcessStep(processId, 5, 'Error in response', 'error');
                    addErrorMessage(result.error || 'An error occurred');
                }
            } catch (error) {
                if (error.name === 'AbortError') {
                    addSystemMessage('Operation cancelled by user');
                } else {
                    addErrorMessage('Connection error: ' + error.message);
                }
                
                // Update process step to show error
                const processDiv = document.getElementById(`process-${processId}`);
                if (processDiv) {
                    updateProcessStep(processId, 99, `Error: ${error.message}`, 'error');
                }
            } finally {
                isProcessing = false;
                document.getElementById('sendButton').disabled = false;
                document.getElementById('cancelButton').classList.remove('active');
                currentAbortController = null;
                input.focus();
            }
        }

        function cancelOperation() {
            if (currentAbortController) {
                currentAbortController.abort();
                addSystemMessage('Cancelling operation...');
            }
        }

        function sleep(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
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
                                Database: ${result.database || currentDatabase || 'master'}
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

        async function refreshDatabases() {
            if (isProcessing) {
                addSystemMessage('Another operation is in progress. Please wait...');
                return;
            }
            
            const refreshButton = document.getElementById('refreshDbButton');
            const databaseList = document.getElementById('databaseList');
            
            refreshButton.disabled = true;
            refreshButton.textContent = 'Loading...';
            databaseList.innerHTML = '<div class="loading-indicator">Fetching databases...</div>';
            
            addSystemMessage('Loading databases from server...');
            
            try {
                const response = await fetch('/console/api/databases');
                const result = await response.json();
                
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
                        databaseList.innerHTML = '<div class="empty-state"><div class="empty-state-icon">❌</div><div>No databases found</div></div>';
                    } else {
                        databasesLoaded = true;
                        addSystemMessage(`Loaded ${result.databases.length} databases: ${result.databases.join(', ')}`);
                        
                        // Auto-select first database if none selected
                        if (!currentDatabase && result.databases.length > 0) {
                            selectDatabase(result.databases[0]);
                        }
                    }
                } else {
                    databaseList.innerHTML = '<div style="color: #dc2626; font-size: 0.85rem;">Error loading databases</div>';
                    addSystemMessage('Failed to load databases: ' + (result.error || 'Unknown error'));
                }
            } catch (error) {
                databaseList.innerHTML = '<div style="color: #dc2626; font-size: 0.85rem;">Connection error</div>';
                addSystemMessage('Failed to connect to server: ' + error.message);
            } finally {
                refreshButton.disabled = false;
                refreshButton.textContent = 'Load';
            }
        }

        async function refreshDatabasesFromResult(result) {
            // Update sidebar with databases from sp_databases result
            if (result.content && result.content.includes('Available databases:')) {
                const databaseList = document.getElementById('databaseList');
                databaseList.innerHTML = '';
                
                // Extract database names from the content
                const lines = result.content.split('\n');
                const databases = [];
                
                lines.forEach(line => {
                    if (line.startsWith('• ')) {
                        const dbName = line.substring(2).trim();
                        databases.push(dbName);
                    }
                });
                
                if (databases.length > 0) {
                    databases.forEach(db => {
                        const dbItem = document.createElement('div');
                        dbItem.className = 'database-item';
                        if (db === currentDatabase) {
                            dbItem.classList.add('active');
                        }
                        dbItem.textContent = db;
                        dbItem.onclick = () => selectDatabase(db);
                        databaseList.appendChild(dbItem);
                    });
                    
                    databasesLoaded = true;
                    addSystemMessage(`Sidebar updated with ${databases.length} databases`);
                }
            }
        }

        async function selectDatabase(dbName) {
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
            
            const tableList = document.getElementById('tableList');
            tableList.innerHTML = '<div class="loading-indicator">Loading tables...</div>';
            
            try {
                const response = await fetch(`/console/api/tables?database=${encodeURIComponent(database)}`);
                const result = await response.json();
                
                if (result.status === 'success' && result.tables) {
                    tableList.innerHTML = '';
                    
                    if (result.tables.length === 0) {
                        tableList.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📭</div><div>No tables found</div></div>';
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
                        
                        addSystemMessage(`Loaded ${result.tables.length} tables from ${database}`);
                    }
                } else {
                    tableList.innerHTML = '<div style="color: #dc2626; font-size: 0.85rem;">Error loading tables</div>';
                }
            } catch (error) {
                tableList.innerHTML = '<div style="color: #dc2626; font-size: 0.85rem;">Connection error</div>';
            }
        }
    </script>
</body>
</html>