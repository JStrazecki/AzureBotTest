# sql_console_javascript.py - SQL Console JavaScript with Enhanced Logging
"""
SQL Console JavaScript - Enhanced with step-by-step logging and cancel functionality
"""

def get_sql_console_javascript():
    """Return the JavaScript code for the SQL console with enhanced logging"""
    return '''
    let currentDatabase = 'master';
    let isProcessing = false;
    let sessionId = generateSessionId();
    let multiDbMode = false;
    let selectedDatabases = new Set();
    let currentRequest = null;

    // Initialize
    window.onload = async function() {
        await getCurrentUser();
        document.getElementById('messageInput').focus();
        
        // Auto-resize textarea
        const textarea = document.getElementById('messageInput');
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
        
        // Add initial log message
        addLogMessage('System initialized. Ready for queries.', 'success');
        addLogMessage('Available databases: master, _support, demo', 'info');
        
        // Don't auto-refresh databases - wait for user action
        await loadInitialDatabases();
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
        sendMessage();
    }

    async function loadInitialDatabases() {
        const databaseList = document.getElementById('databaseList');
        databaseList.innerHTML = '<div class="loading-indicator">Discovering databases...</div>';
        
        addLogMessage('Initializing database discovery...', 'info');
        
        try {
            // Instead of hardcoding, fetch from server
            const response = await fetch('/console/api/databases');
            const result = await response.json();
            
            if (result.status === 'success' && result.databases) {
                databaseList.innerHTML = '';
                
                result.databases.forEach(db => {
                    const dbItem = document.createElement('div');
                    dbItem.className = 'database-item';
                    dbItem.setAttribute('data-db-name', db);
                    
                    if (db === currentDatabase) {
                        dbItem.classList.add('active');
                    }
                    
                    dbItem.textContent = db;
                    dbItem.onclick = () => {
                        if (!multiDbMode) {
                            selectDatabase(db);
                        }
                    };
                    
                    databaseList.appendChild(dbItem);
                });
                
                addLogMessage(`Discovered ${result.databases.length} accessible databases: ${result.databases.join(', ')}`, 'success');
            } else {
                // Fallback to known databases
                const knownDatabases = ['master', '_support', 'demo'];
                knownDatabases.forEach(db => {
                    const dbItem = document.createElement('div');
                    dbItem.className = 'database-item';
                    dbItem.setAttribute('data-db-name', db);
                    
                    if (db === currentDatabase) {
                        dbItem.classList.add('active');
                    }
                    
                    dbItem.textContent = db;
                    dbItem.onclick = () => {
                        if (!multiDbMode) {
                            selectDatabase(db);
                        }
                    };
                    
                    databaseList.appendChild(dbItem);
                });
                
                addLogMessage('Using fallback database list', 'warning');
            }
        } catch (error) {
            addLogMessage(`Error discovering databases: ${error.message}`, 'error');
            addLogMessage('Using known accessible databases: master, _support, demo', 'info');
            
            // Fallback to known databases
            const knownDatabases = ['master', '_support', 'demo'];
            databaseList.innerHTML = '';
            
            knownDatabases.forEach(db => {
                const dbItem = document.createElement('div');
                dbItem.className = 'database-item';
                dbItem.setAttribute('data-db-name', db);
                
                if (db === currentDatabase) {
                    dbItem.classList.add('active');
                }
                
                dbItem.textContent = db;
                dbItem.onclick = () => {
                    if (!multiDbMode) {
                        selectDatabase(db);
                    }
                };
                
                databaseList.appendChild(dbItem);
            });
        }
    }

    function toggleMultiDbMode() {
        multiDbMode = document.getElementById('multiDbMode').checked;
        
        // Show/hide multi-db UI elements
        document.getElementById('selectAllDbBtn').style.display = multiDbMode ? 'block' : 'none';
        document.getElementById('selectedDbIndicator').style.display = multiDbMode ? 'block' : 'none';
        document.getElementById('multiDbIndicator').style.display = multiDbMode ? 'block' : 'none';
        
        // Update database items
        const dbItems = document.querySelectorAll('.database-item');
        dbItems.forEach(item => {
            if (multiDbMode) {
                item.classList.add('multi-select-mode');
                
                // Add checkbox if not exists
                if (!item.querySelector('.database-checkbox')) {
                    const checkbox = document.createElement('input');
                    checkbox.type = 'checkbox';
                    checkbox.className = 'database-checkbox';
                    checkbox.onclick = (e) => {
                        e.stopPropagation();
                        toggleDatabaseSelection(item.getAttribute('data-db-name'));
                    };
                    item.insertBefore(checkbox, item.firstChild);
                }
            } else {
                item.classList.remove('multi-select-mode');
                const checkbox = item.querySelector('.database-checkbox');
                if (checkbox) checkbox.remove();
            }
        });
        
        if (!multiDbMode) {
            selectedDatabases.clear();
            updateSelectedDatabasesUI();
        }
        
        addLogMessage(multiDbMode ? 'Multi-database mode enabled' : 'Multi-database mode disabled', 'info');
    }

    function toggleDatabaseSelection(dbName) {
        if (selectedDatabases.has(dbName)) {
            selectedDatabases.delete(dbName);
        } else {
            selectedDatabases.add(dbName);
        }
        updateSelectedDatabasesUI();
    }

    function toggleAllDatabases() {
        const dbItems = document.querySelectorAll('.database-item');
        const allSelected = selectedDatabases.size === dbItems.length;
        
        if (allSelected) {
            selectedDatabases.clear();
        } else {
            dbItems.forEach(item => {
                selectedDatabases.add(item.getAttribute('data-db-name'));
            });
        }
        updateSelectedDatabasesUI();
    }

    function updateSelectedDatabasesUI() {
        const count = selectedDatabases.size;
        
        // Update selected count
        document.querySelector('.selected-count').textContent = `${count} database${count !== 1 ? 's' : ''} selected`;
        document.getElementById('selectedDbCount').textContent = count;
        
        // Update button text
        const selectAllBtn = document.getElementById('selectAllDbBtn');
        const dbItems = document.querySelectorAll('.database-item');
        selectAllBtn.textContent = count === dbItems.length ? 'Deselect All' : 'Select All';
        
        // Update checkboxes and highlighting
        dbItems.forEach(item => {
            const dbName = item.getAttribute('data-db-name');
            const checkbox = item.querySelector('.database-checkbox');
            
            if (selectedDatabases.has(dbName)) {
                item.classList.add('selected');
                if (checkbox) checkbox.checked = true;
            } else {
                item.classList.remove('selected');
                if (checkbox) checkbox.checked = false;
            }
        });
    }

    function addLogMessage(message, type = 'info') {
        const messagesContainer = document.getElementById('messagesContainer');
        const logDiv = document.createElement('div');
        logDiv.className = 'message bot log-message';
        
        const time = new Date().toLocaleTimeString();
        
        let icon = '';
        let color = '';
        switch(type) {
            case 'info': icon = 'ℹ️'; color = '#3b82f6'; break;
            case 'success': icon = '✅'; color = '#10b981'; break;
            case 'warning': icon = '⚠️'; color = '#f59e0b'; break;
            case 'error': icon = '❌'; color = '#ef4444'; break;
            case 'debug': icon = '🔍'; color = '#6b7280'; break;
        }
        
        logDiv.innerHTML = `
            <div class="message-content" style="background-color: rgba(30, 41, 59, 0.5); border-color: ${color};">
                <div class="message-header" style="color: ${color};">${icon} System Log • ${time}</div>
                <div class="message-text" style="color: #cbd5e1; font-size: 0.875rem;">${escapeHtml(message)}</div>
            </div>
        `;
        
        messagesContainer.appendChild(logDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    async function sendMessage() {
        const input = document.getElementById('messageInput');
        const message = input.value.trim();
        
        if (!message || isProcessing) return;
        
        isProcessing = true;
        document.getElementById('sendButton').disabled = true;
        document.getElementById('sendButton').innerHTML = '<span class="spinner"></span> Processing...';
        
        // Show cancel button
        const cancelBtn = document.getElementById('cancelButton');
        if (cancelBtn) cancelBtn.style.display = 'inline-block';
        
        // Add user message
        addMessage(message, 'user');
        input.value = '';
        input.style.height = 'auto';
        
        // Show typing indicator
        showTypingIndicator();
        
        // Log the start of processing
        addLogMessage(`Processing query: "${message.substring(0, 50)}${message.length > 50 ? '...' : ''}"`, 'info');
        
        try {
            // Prepare request data
            const requestData = {
                message: message,
                database: currentDatabase,
                session_id: sessionId
            };
            
            // Add multi-database info if in multi-db mode
            if (multiDbMode && selectedDatabases.size > 0) {
                requestData.multi_db_mode = true;
                requestData.databases = Array.from(selectedDatabases);
                addLogMessage(`Multi-database query: ${requestData.databases.join(', ')}`, 'info');
            }
            
            addLogMessage('Sending request to server...', 'debug');
            
            currentRequest = fetch('/console/api/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            const response = await currentRequest;
            
            addLogMessage(`Server response received: ${response.status} ${response.statusText}`, 'debug');
            
            const result = await response.json();
            
            hideTypingIndicator();
            
            if (result.status === 'success') {
                addLogMessage('Query processed successfully', 'success');
                
                // Add bot response
                if (result.response_type === 'sql_result') {
                    if (result.sql_query) {
                        addLogMessage(`SQL Query executed: ${result.sql_query}`, 'info');
                    }
                    
                    if (result.multi_db_results) {
                        const successCount = result.multi_db_results.filter(r => !r.error).length;
                        addLogMessage(`Multi-DB results: ${successCount}/${result.multi_db_results.length} successful`, 'info');
                        addMultiDbSQLResult(result);
                    } else {
                        if (result.row_count !== undefined) {
                            addLogMessage(`Query returned ${result.row_count} rows in ${result.execution_time}ms`, 'success');
                        }
                        addSQLResult(result);
                    }
                } else if (result.response_type === 'help') {
                    addMessage(result.content, 'bot');
                } else if (result.response_type === 'error') {
                    addLogMessage(`Error: ${result.error}`, 'error');
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
                    addLogMessage('Refreshing table list...', 'info');
                    await loadTables(currentDatabase);
                }
            } else {
                const errorMsg = result.error || 'An error occurred';
                addLogMessage(`Error: ${errorMsg}`, 'error');
                addErrorMessage(errorMsg);
            }
        } catch (error) {
            hideTypingIndicator();
            if (error.name === 'AbortError') {
                addLogMessage('Request cancelled by user', 'warning');
                addErrorMessage('Request cancelled');
            } else {
                addLogMessage(`Connection error: ${error.message}`, 'error');
                addErrorMessage('Connection error: ' + error.message);
            }
        } finally {
            isProcessing = false;
            document.getElementById('sendButton').disabled = false;
            document.getElementById('sendButton').innerHTML = 'Send';
            
            // Hide cancel button
            const cancelBtn = document.getElementById('cancelButton');
            if (cancelBtn) cancelBtn.style.display = 'none';
            
            currentRequest = null;
            input.focus();
        }
    }

    async function cancelRequest() {
        if (currentRequest) {
            addLogMessage('Cancelling request...', 'warning');
            
            try {
                // Send cancel request to server
                await fetch('/console/api/cancel', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ session_id: sessionId })
                });
            } catch (e) {
                console.error('Error sending cancel request:', e);
            }
            
            // Note: Fetch API doesn't support true cancellation
            // This is a placeholder for future WebSocket implementation
            addLogMessage('Cancel request sent to server', 'warning');
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

    function addMultiDbSQLResult(result) {
        const messagesContainer = document.getElementById('messagesContainer');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot';
        
        const time = new Date().toLocaleTimeString();
        
        let content = `
            <div class="message-content">
                <div class="message-header">SQL Assistant • ${time}</div>
                <div class="message-text">${escapeHtml(result.explanation || 'Multi-database query executed successfully')}</div>
                <div class="sql-result">
                    <div class="sql-query">${escapeHtml(result.sql_query)}</div>
                    <div class="multi-db-results">
        `;
        
        // Process results for each database
        result.multi_db_results.forEach(dbResult => {
            content += `
                <div class="db-result-section">
                    <div class="db-result-header">
                        <div class="db-name">📊 ${escapeHtml(dbResult.database)}</div>
                        <div class="db-result-stats">
                            ${dbResult.row_count || 0} rows • ${dbResult.execution_time || 0}ms
                        </div>
                    </div>
            `;
            
            if (dbResult.error) {
                content += `<div class="error-message">❌ ${escapeHtml(dbResult.error)}</div>`;
            } else if (dbResult.rows && dbResult.rows.length > 0) {
                // Create table for this database
                const columns = Object.keys(dbResult.rows[0]);
                content += '<table class="result-table"><thead><tr>';
                columns.forEach(col => {
                    content += `<th>${escapeHtml(col)}</th>`;
                });
                content += '</tr></thead><tbody>';
                
                dbResult.rows.forEach(row => {
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
        });
        
        content += `
                    </div>
                </div>
            </div>
        `;
        
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

    async function refreshDatabases(forceRefresh = false) {
        const databaseList = document.getElementById('databaseList');
        databaseList.innerHTML = '<div class="loading-indicator">Loading databases...</div>';
        
        addLogMessage('Refreshing database list...', 'info');
        
        try {
            const url = forceRefresh ? '/console/api/databases?force_refresh=true' : '/console/api/databases';
            const response = await fetch(url);
            const result = await response.json();
            
            if (result.status === 'success' && result.databases) {
                databaseList.innerHTML = '';
                
                addLogMessage(`Found ${result.databases.length} accessible databases`, 'success');
                
                result.databases.forEach(db => {
                    const dbItem = document.createElement('div');
                    dbItem.className = 'database-item';
                    dbItem.setAttribute('data-db-name', db);
                    
                    if (db === currentDatabase) {
                        dbItem.classList.add('active');
                    }
                    
                    dbItem.textContent = db;
                    dbItem.onclick = () => {
                        if (!multiDbMode) {
                            selectDatabase(db);
                        }
                    };
                    
                    databaseList.appendChild(dbItem);
                });
                
                // Re-apply multi-db mode if active
                if (multiDbMode) {
                    toggleMultiDbMode();
                }
                
                if (result.databases.length === 0) {
                    databaseList.innerHTML = '<div style="color: #666; font-size: 0.85rem;">No databases found</div>';
                    addLogMessage('No accessible databases found', 'warning');
                }
                
                if (result.note) {
                    addLogMessage(result.note, 'info');
                }
            } else {
                databaseList.innerHTML = '<div style="color: #dc2626; font-size: 0.85rem;">Error loading databases</div>';
                addLogMessage('Error loading databases', 'error');
            }
        } catch (error) {
            databaseList.innerHTML = '<div style="color: #dc2626; font-size: 0.85rem;">Connection error</div>';
            addLogMessage(`Connection error: ${error.message}`, 'error');
        }
    }

    async function selectDatabase(dbName) {
        currentDatabase = dbName;
        document.getElementById('currentDatabase').textContent = dbName;
        
        // Update active state in list
        document.querySelectorAll('.database-item').forEach(item => {
            item.classList.remove('active');
            if (item.getAttribute('data-db-name') === dbName) {
                item.classList.add('active');
            }
        });
        
        // Load tables
        await loadTables(dbName);
        
        // Add notification
        addMessage(`Database changed to: ${dbName}`, 'bot');
        addLogMessage(`Switched to database: ${dbName}`, 'info');
    }

    async function loadTables(database) {
        if (!database) return;
        
        const tableList = document.getElementById('tableList');
        tableList.innerHTML = '<div class="loading-indicator">Loading tables...</div>';
        
        addLogMessage(`Loading tables for database: ${database}`, 'info');
        
        try {
            const response = await fetch(`/console/api/tables?database=${encodeURIComponent(database)}&session_id=${sessionId}`);
            const result = await response.json();
            
            if (result.status === 'success' && result.tables) {
                tableList.innerHTML = '';
                
                if (result.tables.length === 0) {
                    tableList.innerHTML = '<div style="color: #666; font-size: 0.85rem;">No tables found</div>';
                    addLogMessage(`No tables found in ${database}`, 'warning');
                } else {
                    addLogMessage(`Found ${result.tables.length} tables in ${database}`, 'success');
                    
                    result.tables.forEach(table => {
                        const tableItem = document.createElement('div');
                        tableItem.className = 'table-item';
                        tableItem.textContent = table;
                        tableItem.onclick = () => {
                            document.getElementById('messageInput').value = `SELECT TOP 10 * FROM ${table}`;
                            addLogMessage(`Query template created for table: ${table}`, 'info');
                        };
                        tableList.appendChild(tableItem);
                    });
                }
            } else {
                tableList.innerHTML = '<div style="color: #dc2626; font-size: 0.85rem;">Error loading tables</div>';
                addLogMessage(`Error loading tables: ${result.error || 'Unknown error'}`, 'error');
            }
        } catch (error) {
            tableList.innerHTML = '<div style="color: #dc2626; font-size: 0.85rem;">Connection error</div>';
            addLogMessage(`Connection error loading tables: ${error.message}`, 'error');
        }
    }

    async function getCurrentUser() {
        try {
            const response = await fetch('/console/api/current-user');
            const result = await response.json();
            
            if (result.status === 'success' && result.user) {
                // Update user display
                const userElement = document.getElementById('currentUser');
                userElement.textContent = result.user.name || result.user.email || 'Unknown User';
                
                // Add title attribute for full details
                if (result.user.sql_user) {
                    userElement.title = `SQL User: ${result.user.sql_user}\\nAuth: ${result.user.auth_type || 'Microsoft'}`;
                }
                
                addLogMessage(`Logged in as: ${result.user.name || result.user.sql_user}`, 'info');
            } else {
                document.getElementById('currentUser').textContent = 'Not authenticated';
                addLogMessage('User authentication status: Not authenticated', 'warning');
            }
        } catch (error) {
            console.error('Error getting current user:', error);
            document.getElementById('currentUser').textContent = 'Authentication error';
            addLogMessage('Error checking authentication status', 'error');
        }
    }
   
    '''