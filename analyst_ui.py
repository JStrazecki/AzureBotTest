# analyst_ui.py - Power BI Analyst User Interface
"""
Power BI Analyst UI - Clean, business-focused interface for Power BI analysis
"""

def get_analyst_html(authenticated: bool = False) -> str:
    """Generate the Power BI Analyst HTML interface"""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Power BI Analyst - Business Intelligence Assistant</title>
    <style>
        {get_analyst_css()}
    </style>
</head>
<body>
    <div class="app-container">
        <!-- Header -->
        <header class="app-header">
            <div class="header-content">
                <div class="logo-section">
                    <div class="logo">📊</div>
                    <h1>Power BI Analyst</h1>
                    <span class="tagline">Your AI Business Intelligence Assistant</span>
                </div>
                <div class="header-actions">
                    <button id="connectBtn" class="btn btn-primary">
                        <span class="icon">🔗</span> Connect to Power BI
                    </button>
                    <div id="userInfo" class="user-info" style="display: none;">
                        <span class="user-name"></span>
                        <button class="btn btn-small" onclick="disconnect()">Disconnect</button>
                    </div>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <div class="main-container">
            <!-- Sidebar -->
            <aside class="sidebar" id="sidebar">
                <div class="sidebar-section">
                    <h3>Workspaces</h3>
                    <div id="workspaceList" class="workspace-list">
                        <div class="empty-state">
                            <span class="icon">📁</span>
                            <p>Connect to Power BI to see your workspaces</p>
                        </div>
                    </div>
                </div>
                
                <div class="sidebar-section">
                    <h3>Current Dataset</h3>
                    <div id="datasetInfo" class="dataset-info">
                        <div class="empty-state">
                            <span class="icon">📊</span>
                            <p>No dataset selected</p>
                        </div>
                    </div>
                </div>
                
                <div class="sidebar-section">
                    <h3>Quick Actions</h3>
                    <div class="quick-actions">
                        <button class="action-btn" onclick="showSuggestions()" disabled>
                            <span class="icon">💡</span> Suggested Queries
                        </button>
                        <button class="action-btn" onclick="showHelp()">
                            <span class="icon">❓</span> How to Use
                        </button>
                    </div>
                </div>
            </aside>

            <!-- Chat Area -->
            <main class="chat-container">
                <div class="chat-messages" id="chatMessages">
                    <!-- Welcome Message -->
                    <div class="message assistant">
                        <div class="message-avatar">🤖</div>
                        <div class="message-content">
                            <div class="message-header">Power BI Analyst</div>
                            <div class="message-text">
                                Welcome! I'm your AI-powered business analyst. I can help you:
                                
                                <ul>
                                    <li>📈 Analyze your Power BI data with natural language queries</li>
                                    <li>🔍 Automatically investigate trends and anomalies</li>
                                    <li>💡 Provide actionable business recommendations</li>
                                    <li>📊 Compare performance across time periods and segments</li>
                                </ul>
                                
                                To get started, connect to your Power BI workspace and select a dataset.
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Input Area -->
                <div class="chat-input-container">
                    <div class="input-wrapper">
                        <textarea 
                            id="queryInput" 
                            class="query-input" 
                            placeholder="Ask me about your business data... (e.g., 'How did we perform last quarter?')"
                            rows="1"
                            disabled
                        ></textarea>
                        <div class="input-actions">
                            <button id="analyzeBtn" class="btn btn-primary" onclick="analyzeQuery()" disabled>
                                <span class="icon">🔍</span> Analyze
                            </button>
                        </div>
                    </div>
                    <div class="input-hints" id="inputHints" style="display: none;">
                        <span class="hint-label">Try asking:</span>
                        <div class="hint-chips" id="hintChips"></div>
                    </div>
                </div>
            </main>
        </div>

        <!-- Modals -->
        <div id="connectModal" class="modal" style="display: none;">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Connect to Power BI</h2>
                    <button class="close-btn" onclick="closeModal('connectModal')">×</button>
                </div>
                <div class="modal-body">
                    <p>Choose how to connect to your Power BI workspace:</p>
                    
                    <div class="auth-options">
                        <button class="auth-option" onclick="authenticate('delegated')">
                            <span class="icon">👤</span>
                            <div>
                                <h4>Use My Account</h4>
                                <p>Access your personal workspaces and datasets</p>
                            </div>
                        </button>
                        
                        <button class="auth-option" onclick="authenticate('app')">
                            <span class="icon">🏢</span>
                            <div>
                                <h4>Use Organization Account</h4>
                                <p>Access shared organizational datasets</p>
                            </div>
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <div id="suggestionsModal" class="modal" style="display: none;">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Suggested Queries</h2>
                    <button class="close-btn" onclick="closeModal('suggestionsModal')">×</button>
                </div>
                <div class="modal-body">
                    <div id="suggestionsList" class="suggestions-list">
                        <div class="loading">Loading suggestions...</div>
                    </div>
                </div>
            </div>
        </div>

        <div id="helpModal" class="modal" style="display: none;">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>How to Use Power BI Analyst</h2>
                    <button class="close-btn" onclick="closeModal('helpModal')">×</button>
                </div>
                <div class="modal-body">
                    <div class="help-content">
                        <h3>Getting Started</h3>
                        <ol>
                            <li>Click "Connect to Power BI" and authenticate</li>
                            <li>Select a workspace from the sidebar</li>
                            <li>Choose a dataset to analyze</li>
                            <li>Ask questions in natural language</li>
                        </ol>

                        <h3>Example Questions</h3>
                        <ul>
                            <li>"How did revenue perform last quarter?"</li>
                            <li>"What are our top 10 customers by sales?"</li>
                            <li>"Compare this year's performance to last year"</li>
                            <li>"Show me sales trends by region"</li>
                            <li>"Which products have declining sales?"</li>
                        </ul>

                        <h3>Features</h3>
                        <ul>
                            <li><strong>Progressive Analysis:</strong> I automatically investigate deeper when I find interesting patterns</li>
                            <li><strong>Error Fixing:</strong> If a query fails, I'll suggest fixes</li>
                            <li><strong>Export Results:</strong> Download your analysis as JSON or CSV</li>
                            <li><strong>Business Context:</strong> I understand your business terminology and rules</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        {get_analyst_javascript()}
    </script>
</body>
</html>'''

def get_analyst_css() -> str:
    """Return CSS styles for the analyst interface"""
    return '''
    /* Reset and Base Styles */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        background-color: #f5f5f5;
        color: #333;
        line-height: 1.6;
    }

    /* App Container */
    .app-container {
        display: flex;
        flex-direction: column;
        height: 100vh;
        overflow: hidden;
    }

    /* Header */
    .app-header {
        background: linear-gradient(135deg, #0078d4 0%, #005a9e 100%);
        color: white;
        padding: 1rem 2rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .header-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
        max-width: 1400px;
        margin: 0 auto;
    }

    .logo-section {
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .logo {
        font-size: 2rem;
    }

    .app-header h1 {
        font-size: 1.5rem;
        font-weight: 600;
    }

    .tagline {
        font-size: 0.875rem;
        opacity: 0.9;
    }

    .header-actions {
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .user-info {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 0.5rem 1rem;
        background: rgba(255,255,255,0.1);
        border-radius: 8px;
    }

    .user-name {
        font-weight: 500;
    }

    /* Main Container */
    .main-container {
        display: flex;
        flex: 1;
        overflow: hidden;
    }

    /* Sidebar */
    .sidebar {
        width: 300px;
        background: white;
        border-right: 1px solid #e0e0e0;
        overflow-y: auto;
        transition: transform 0.3s ease;
    }

    .sidebar-section {
        padding: 1.5rem;
        border-bottom: 1px solid #e0e0e0;
    }

    .sidebar-section h3 {
        font-size: 0.875rem;
        text-transform: uppercase;
        color: #666;
        margin-bottom: 1rem;
        font-weight: 600;
    }

    .workspace-list {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .workspace-item, .dataset-item {
        padding: 0.75rem;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .workspace-item:hover, .dataset-item:hover {
        background: #f0f0f0;
    }

    .workspace-item.active, .dataset-item.active {
        background: #e3f2fd;
        color: #0078d4;
    }

    .empty-state {
        text-align: center;
        padding: 2rem 1rem;
        color: #999;
    }

    .empty-state .icon {
        font-size: 2rem;
        display: block;
        margin-bottom: 0.5rem;
    }

    .dataset-info {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        font-size: 0.875rem;
    }

    .dataset-info .metric {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.5rem;
    }

    .quick-actions {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .action-btn {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.75rem;
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s;
        font-size: 0.875rem;
        text-align: left;
    }

    .action-btn:hover:not(:disabled) {
        background: #f0f0f0;
        border-color: #0078d4;
    }

    .action-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    /* Chat Container */
    .chat-container {
        flex: 1;
        display: flex;
        flex-direction: column;
        background: #f8f9fa;
    }

    .chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: 2rem;
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
    }

    /* Messages */
    .message {
        display: flex;
        gap: 1rem;
        max-width: 900px;
        width: 100%;
        margin: 0 auto;
    }

    .message.user {
        flex-direction: row-reverse;
    }

    .message-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        background: #e3f2fd;
        flex-shrink: 0;
    }

    .message.user .message-avatar {
        background: #e8f5e9;
    }

    .message-content {
        flex: 1;
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    .message.user .message-content {
        background: #0078d4;
        color: white;
    }

    .message-header {
        font-weight: 600;
        margin-bottom: 0.5rem;
        font-size: 0.875rem;
        opacity: 0.8;
    }

    .message-text {
        line-height: 1.6;
    }

    .message-text ul {
        margin: 1rem 0;
        padding-left: 1.5rem;
    }

    .message-text li {
        margin-bottom: 0.5rem;
    }

    /* Analysis Results */
    .analysis-result {
        margin-top: 1rem;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 8px;
        border-left: 4px solid #0078d4;
    }

    .result-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }

    .result-metrics {
        display: flex;
        gap: 2rem;
        font-size: 0.875rem;
        color: #666;
    }

    .data-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 1rem;
        font-size: 0.875rem;
    }

    .data-table th {
        background: #f0f0f0;
        padding: 0.75rem;
        text-align: left;
        font-weight: 600;
        border-bottom: 2px solid #e0e0e0;
    }

    .data-table td {
        padding: 0.75rem;
        border-bottom: 1px solid #e0e0e0;
    }

    .data-table tr:hover {
        background: #f8f9fa;
    }

    /* Insights Section */
    .insights-section {
        margin-top: 1.5rem;
        padding: 1.5rem;
        background: #fff3cd;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
    }

    .insights-section h4 {
        margin-bottom: 1rem;
        color: #856404;
    }

    .insight-item {
        margin-bottom: 0.75rem;
        padding-left: 1.5rem;
        position: relative;
    }

    .insight-item::before {
        content: "•";
        position: absolute;
        left: 0;
        color: #ffc107;
    }

    /* Recommendations */
    .recommendations-section {
        margin-top: 1.5rem;
        padding: 1.5rem;
        background: #d4edda;
        border-radius: 8px;
        border-left: 4px solid #28a745;
    }

    .recommendations-section h4 {
        margin-bottom: 1rem;
        color: #155724;
    }

    .recommendation-item {
        margin-bottom: 0.75rem;
        padding: 0.75rem;
        background: white;
        border-radius: 6px;
        display: flex;
        align-items: start;
        gap: 0.75rem;
    }

    .recommendation-number {
        background: #28a745;
        color: white;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.875rem;
        font-weight: 600;
        flex-shrink: 0;
    }

    /* Input Area */
    .chat-input-container {
        background: white;
        border-top: 1px solid #e0e0e0;
        padding: 1.5rem 2rem;
    }

    .input-wrapper {
        display: flex;
        gap: 1rem;
        max-width: 900px;
        margin: 0 auto;
    }

    .query-input {
        flex: 1;
        padding: 0.75rem 1rem;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        font-size: 1rem;
        resize: none;
        outline: none;
        transition: border-color 0.2s;
        font-family: inherit;
    }

    .query-input:focus {
        border-color: #0078d4;
    }

    .query-input:disabled {
        background: #f5f5f5;
        cursor: not-allowed;
    }

    .input-actions {
        display: flex;
        align-items: flex-end;
    }

    .input-hints {
        margin-top: 0.5rem;
        max-width: 900px;
        margin: 0.5rem auto 0;
    }

    .hint-label {
        font-size: 0.875rem;
        color: #666;
        margin-right: 0.5rem;
    }

    .hint-chips {
        display: inline-flex;
        gap: 0.5rem;
        flex-wrap: wrap;
    }

    .hint-chip {
        padding: 0.25rem 0.75rem;
        background: #e3f2fd;
        color: #0078d4;
        border-radius: 16px;
        font-size: 0.875rem;
        cursor: pointer;
        transition: all 0.2s;
    }

    .hint-chip:hover {
        background: #0078d4;
        color: white;
    }

    /* Buttons */
    .btn {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.75rem 1.5rem;
        border: none;
        border-radius: 8px;
        font-size: 1rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
        text-decoration: none;
        outline: none;
    }

    .btn-primary {
        background: #0078d4;
        color: white;
    }

    .btn-primary:hover:not(:disabled) {
        background: #005a9e;
    }

    .btn-secondary {
        background: white;
        color: #333;
        border: 1px solid #e0e0e0;
    }

    .btn-secondary:hover:not(:disabled) {
        background: #f0f0f0;
        border-color: #0078d4;
    }

    .btn-small {
        padding: 0.5rem 1rem;
        font-size: 0.875rem;
    }

    .btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    .btn .icon {
        font-size: 1.2em;
    }

    /* Loading States */
    .loading {
        text-align: center;
        padding: 2rem;
        color: #666;
    }

    .spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(0,0,0,0.1);
        border-left-color: #0078d4;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    /* Modals */
    .modal {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    }

    .modal-content {
        background: white;
        border-radius: 12px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        max-width: 600px;
        width: 90%;
        max-height: 90vh;
        overflow: hidden;
        display: flex;
        flex-direction: column;
    }

    .modal-header {
        padding: 1.5rem;
        border-bottom: 1px solid #e0e0e0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .modal-header h2 {
        font-size: 1.5rem;
        font-weight: 600;
    }

    .close-btn {
        background: none;
        border: none;
        font-size: 1.5rem;
        cursor: pointer;
        color: #666;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 4px;
        transition: all 0.2s;
    }

    .close-btn:hover {
        background: #f0f0f0;
    }

    .modal-body {
        padding: 1.5rem;
        overflow-y: auto;
    }

    .auth-options {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        margin-top: 1rem;
    }

    .auth-option {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1.5rem;
        background: #f8f9fa;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s;
        text-align: left;
    }

    .auth-option:hover {
        border-color: #0078d4;
        background: #e3f2fd;
    }

    .auth-option .icon {
        font-size: 2rem;
    }

    .auth-option h4 {
        margin-bottom: 0.25rem;
    }

    .auth-option p {
        color: #666;
        font-size: 0.875rem;
    }

    /* Suggestions List */
    .suggestions-list {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }

    .suggestion-item {
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s;
        border: 1px solid transparent;
    }

    .suggestion-item:hover {
        background: #e3f2fd;
        border-color: #0078d4;
    }

    .suggestion-category {
        font-size: 0.75rem;
        color: #666;
        text-transform: uppercase;
        margin-bottom: 0.25rem;
    }

    .suggestion-query {
        font-weight: 500;
        color: #333;
    }

    /* Help Content */
    .help-content h3 {
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
        color: #0078d4;
    }

    .help-content h3:first-child {
        margin-top: 0;
    }

    .help-content ol, .help-content ul {
        padding-left: 1.5rem;
    }

    .help-content li {
        margin-bottom: 0.5rem;
    }

    /* Error States */
    .error-message {
        padding: 1rem;
        background: #f8d7da;
        border-left: 4px solid #dc3545;
        border-radius: 8px;
        color: #721c24;
        margin-top: 1rem;
    }

    .error-actions {
        margin-top: 1rem;
        display: flex;
        gap: 0.5rem;
    }

    /* Responsive Design */
    @media (max-width: 768px) {
        .sidebar {
            position: fixed;
            left: 0;
            top: 0;
            bottom: 0;
            z-index: 100;
            transform: translateX(-100%);
            box-shadow: 2px 0 10px rgba(0,0,0,0.1);
        }

        .sidebar.open {
            transform: translateX(0);
        }

        .main-container {
            flex-direction: column;
        }

        .chat-messages {
            padding: 1rem;
        }

        .message {
            max-width: 100%;
        }

        .modal-content {
            margin: 1rem;
        }
    }
    '''

def get_analyst_javascript() -> str:
    """Return JavaScript code for the analyst interface"""
    return '''
    // Global state
    let currentSession = null;
    let currentWorkspace = null;
    let currentDataset = null;
    let isAnalyzing = false;
    let queryHistory = [];

    // Initialize
    document.addEventListener('DOMContentLoaded', function() {
        // Set up event listeners
        document.getElementById('connectBtn').addEventListener('click', () => showModal('connectModal'));
        document.getElementById('queryInput').addEventListener('keydown', handleKeyPress);
        
        // Auto-resize textarea
        const textarea = document.getElementById('queryInput');
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
        
        // Check for saved session
        const savedSession = localStorage.getItem('powerbi_session');
        if (savedSession) {
            currentSession = savedSession;
            checkSession();
        }
    });

    // Authentication
    async function authenticate(authType) {
        try {
            showLoading('Connecting to Power BI...');
            
            const response = await fetch('/analyst/api/authenticate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    auth_type: authType,
                    user_token: authType === 'delegated' ? await getUserToken() : null
                })
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                currentSession = result.session_id;
                localStorage.setItem('powerbi_session', currentSession);
                
                // Update UI
                document.getElementById('connectBtn').style.display = 'none';
                document.getElementById('userInfo').style.display = 'flex';
                document.querySelector('.user-name').textContent = authType === 'delegated' ? 'Personal Workspace' : 'Organization';
                
                // Load workspaces
                displayWorkspaces(result.workspaces);
                
                // Close modal
                closeModal('connectModal');
                
                addMessage('assistant', `Successfully connected! Found ${result.workspace_count} workspace(s). Please select one to continue.`);
            } else {
                showError('Failed to connect: ' + result.error);
            }
        } catch (error) {
            showError('Connection error: ' + error.message);
        } finally {
            hideLoading();
        }
    }

    async function getUserToken() {
        // In a real implementation, this would use MSAL.js to get the user's token
        // For now, we'll prompt for it or use a mock
        return prompt('Please enter your Power BI access token:') || '';
    }

    function disconnect() {
        currentSession = null;
        currentWorkspace = null;
        currentDataset = null;
        localStorage.removeItem('powerbi_session');
        
        // Reset UI
        document.getElementById('connectBtn').style.display = 'block';
        document.getElementById('userInfo').style.display = 'none';
        document.getElementById('workspaceList').innerHTML = '<div class="empty-state"><span class="icon">📁</span><p>Connect to Power BI to see your workspaces</p></div>';
        document.getElementById('datasetInfo').innerHTML = '<div class="empty-state"><span class="icon">📊</span><p>No dataset selected</p></div>';
        document.getElementById('queryInput').disabled = true;
        document.getElementById('analyzeBtn').disabled = true;
        
        addMessage('assistant', 'Disconnected from Power BI. Your session has been cleared.');
    }

    async function checkSession() {
        // Verify session is still valid
        try {
            const response = await fetch('/analyst/api/health', {
                headers: {
                    'X-Session-ID': currentSession
                }
            });
            
            if (response.ok) {
                // Session is valid, restore UI state
                document.getElementById('connectBtn').style.display = 'none';
                document.getElementById('userInfo').style.display = 'flex';
                addMessage('assistant', 'Welcome back! Your session has been restored.');
            } else {
                // Session expired
                disconnect();
            }
        } catch (error) {
            disconnect();
        }
    }

    // Workspace Management
    function displayWorkspaces(workspaces) {
        const container = document.getElementById('workspaceList');
        container.innerHTML = '';
        
        if (workspaces.length === 0) {
            container.innerHTML = '<div class="empty-state"><span class="icon">😕</span><p>No workspaces found</p></div>';
            return;
        }
        
        workspaces.forEach(ws => {
            const item = document.createElement('div');
            item.className = 'workspace-item';
            item.innerHTML = `
                <span class="icon">📁</span>
                <div>
                    <div>${escapeHtml(ws.name)}</div>
                    ${ws.description ? `<div style="font-size: 0.75rem; color: #666;">${escapeHtml(ws.description)}</div>` : ''}
                </div>
            `;
            item.onclick = () => selectWorkspace(ws);
            container.appendChild(item);
        });
    }

    async function selectWorkspace(workspace) {
        currentWorkspace = workspace;
        
        // Update UI
        document.querySelectorAll('.workspace-item').forEach(item => item.classList.remove('active'));
        event.currentTarget.classList.add('active');
        
        // Load datasets
        try {
            showLoading('Loading datasets...');
            
            const response = await fetch(`/analyst/api/datasets?workspace_id=${workspace.id}`, {
                headers: {
                    'X-Session-ID': currentSession
                }
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                displayDatasets(result.datasets);
                addMessage('assistant', `Found ${result.dataset_count} dataset(s) in workspace "${workspace.name}".`);
            } else {
                showError('Failed to load datasets: ' + result.error);
            }
        } catch (error) {
            showError('Error loading datasets: ' + error.message);
        } finally {
            hideLoading();
        }
    }

    function displayDatasets(datasets) {
        const container = document.getElementById('workspaceList');
        
        // Add datasets section
        const datasetsHtml = datasets.map(ds => `
            <div class="dataset-item" onclick="selectDataset(${JSON.stringify(ds).replace(/"/g, '&quot;')})">
                <span class="icon">📊</span>
                <div>
                    <div>${escapeHtml(ds.name)}</div>
                    <div style="font-size: 0.75rem; color: #666;">
                        ${ds.table_count} tables, ${ds.measure_count} measures
                    </div>
                </div>
            </div>
        `).join('');
        
        container.innerHTML += '<div style="margin-top: 1rem;">' + datasetsHtml + '</div>';
    }

    function selectDataset(dataset) {
        currentDataset = dataset;
        
        // Update UI
        document.querySelectorAll('.dataset-item').forEach(item => item.classList.remove('active'));
        event.currentTarget.classList.add('active');
        
        // Show dataset info
        const infoHtml = `
            <h4>${escapeHtml(dataset.name)}</h4>
            <div class="metric">
                <span>Tables:</span>
                <strong>${dataset.table_count}</strong>
            </div>
            <div class="metric">
                <span>Measures:</span>
                <strong>${dataset.measure_count}</strong>
            </div>
            <div class="metric">
                <span>Last Refresh:</span>
                <strong>${formatDate(dataset.data_freshness)}</strong>
            </div>
        `;
        
        document.getElementById('datasetInfo').innerHTML = infoHtml;
        
        // Enable query input
        document.getElementById('queryInput').disabled = false;
        document.getElementById('analyzeBtn').disabled = false;
        document.querySelector('.action-btn[onclick="showSuggestions()"]').disabled = false;
        
        addMessage('assistant', `Great! I'm ready to analyze "${dataset.name}". What would you like to know?`);
        
        // Show hints
        showHints();
    }

    // Query Analysis
    async function analyzeQuery() {
        const input = document.getElementById('queryInput');
        const query = input.value.trim();
        
        if (!query || isAnalyzing || !currentDataset) return;
        
        isAnalyzing = true;
        input.disabled = true;
        document.getElementById('analyzeBtn').disabled = true;
        document.getElementById('analyzeBtn').innerHTML = '<span class="spinner"></span> Analyzing...';
        
        // Add user message
        addMessage('user', query);
        queryHistory.push(query);
        
        // Clear input
        input.value = '';
        input.style.height = 'auto';
        
        try {
            const response = await fetch('/analyst/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    dataset_id: currentDataset.id,
                    dataset_name: currentDataset.name,
                    session_id: currentSession,
                    enable_progressive: true
                })
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                displayAnalysisResult(result);
            } else {
                displayError(result);
            }
        } catch (error) {
            addMessage('assistant', 'Sorry, I encountered an error while analyzing your query: ' + error.message, 'error');
        } finally {
            isAnalyzing = false;
            input.disabled = false;
            document.getElementById('analyzeBtn').disabled = false;
            document.getElementById('analyzeBtn').innerHTML = '<span class="icon">🔍</span> Analyze';
            input.focus();
        }
    }

    function displayAnalysisResult(result) {
        let messageHtml = `<div class="message-text">${escapeHtml(result.explanation)}</div>`;
        
        // Add data table if available
        if (result.data && result.data.length > 0) {
            messageHtml += `
                <div class="analysis-result">
                    <div class="result-header">
                        <h4>Query Results</h4>
                        <div class="result-metrics">
                            <span>${result.row_count} rows</span>
                            <span>${result.execution_time_ms}ms</span>
                        </div>
                    </div>
                    ${createDataTable(result.data)}
                    <div style="margin-top: 1rem;">
                        <button class="btn btn-small btn-secondary" onclick="exportResults(${JSON.stringify(result).replace(/"/g, '&quot;')})">
                            Export Results
                        </button>
                    </div>
                </div>
            `;
        }
        
        // Add insights if available
        if (result.insights) {
            messageHtml += `
                <div class="insights-section">
                    <h4>🔍 Key Insights</h4>
                    ${result.insights.key_insights.map(insight => 
                        `<div class="insight-item">${escapeHtml(insight)}</div>`
                    ).join('')}
                </div>
            `;
            
            // Add recommendations
            if (result.insights.recommendations && result.insights.recommendations.length > 0) {
                messageHtml += `
                    <div class="recommendations-section">
                        <h4>💡 Recommendations</h4>
                        ${result.insights.recommendations.map((rec, idx) => 
                            `<div class="recommendation-item">
                                <div class="recommendation-number">${idx + 1}</div>
                                <div>${escapeHtml(rec)}</div>
                            </div>`
                        ).join('')}
                    </div>
                `;
            }
        }
        
        // Add formatted analysis if available
        if (result.formatted_analysis) {
            messageHtml = `<div class="message-text">${escapeHtml(result.formatted_analysis).replace(/\\n/g, '<br>')}</div>`;
        }
        
        addMessage('assistant', messageHtml, 'html');
    }

    function displayError(result) {
        let errorHtml = `
            <div class="error-message">
                <strong>Error:</strong> ${escapeHtml(result.error)}
            </div>
        `;
        
        // Add error analysis if available
        if (result.error_analysis) {
            const analysis = result.error_analysis;
            errorHtml += `
                <div class="analysis-result" style="margin-top: 1rem;">
                    <h4>Error Analysis</h4>
                    <p><strong>Type:</strong> ${escapeHtml(analysis.error_type)}</p>
                    <p><strong>Explanation:</strong> ${escapeHtml(analysis.explanation)}</p>
                    <p><strong>Suggested Fix:</strong> ${escapeHtml(analysis.suggested_fix)}</p>
                    
                    <div class="error-actions">
                        <button class="btn btn-primary btn-small" onclick="applyFix('${analysis.fixed_query.replace(/'/g, "\\'")}')">
                            Apply Fix
                        </button>
                        ${analysis.alternative_approaches ? 
                            `<button class="btn btn-secondary btn-small" onclick="showAlternatives(${JSON.stringify(analysis.alternative_approaches).replace(/"/g, '&quot;')})">
                                Show Alternatives
                            </button>` : ''
                        }
                    </div>
                </div>
            `;
        }
        
        addMessage('assistant', errorHtml, 'html');
    }

    async function applyFix(fixedQuery) {
        try {
            showLoading('Applying fix...');
            
            const response = await fetch('/analyst/api/fix-error', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    fixed_query: fixedQuery,
                    dataset_id: currentDataset.id,
                    dataset_name: currentDataset.name,
                    session_id: currentSession
                })
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                addMessage('assistant', 'Fix applied successfully!');
                displayAnalysisResult(result);
            } else {
                addMessage('assistant', 'Failed to apply fix: ' + result.error, 'error');
            }
        } catch (error) {
            addMessage('assistant', 'Error applying fix: ' + error.message, 'error');
        } finally {
            hideLoading();
        }
    }

    // Suggestions
    async function showSuggestions() {
        if (!currentDataset) return;
        
        showModal('suggestionsModal');
        
        try {
            const response = await fetch(`/analyst/api/suggestions?dataset_id=${currentDataset.id}`, {
                headers: {
                    'X-Session-ID': currentSession
                }
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                displaySuggestions(result.suggestions);
            } else {
                document.getElementById('suggestionsList').innerHTML = '<div class="error-message">Failed to load suggestions</div>';
            }
        } catch (error) {
            document.getElementById('suggestionsList').innerHTML = '<div class="error-message">Error: ' + error.message + '</div>';
        }
    }

    function displaySuggestions(suggestions) {
        const html = suggestions.map(s => `
            <div class="suggestion-item" onclick="useSuggestion('${s.query.replace(/'/g, "\\'")}')">
                <div class="suggestion-category">${escapeHtml(s.category)}</div>
                <div class="suggestion-query">${escapeHtml(s.query)}</div>
            </div>
        `).join('');
        
        document.getElementById('suggestionsList').innerHTML = html;
    }

    function useSuggestion(query) {
        closeModal('suggestionsModal');
        document.getElementById('queryInput').value = query;
        document.getElementById('queryInput').focus();
    }

    // Hints
    function showHints() {
        const hints = [
            "How did we perform last quarter?",
            "Show me top customers",
            "Compare revenue by region",
            "What are the trends?"
        ];
        
        const hintsHtml = hints.map(hint => 
            `<span class="hint-chip" onclick="useHint('${hint}')">${hint}</span>`
        ).join('');
        
        document.getElementById('hintChips').innerHTML = hintsHtml;
        document.getElementById('inputHints').style.display = 'block';
    }

    function useHint(hint) {
        document.getElementById('queryInput').value = hint;
        document.getElementById('queryInput').focus();
    }

    // Export functionality
    async function exportResults(analysisData) {
        try {
            const format = prompt('Export format: json or csv?', 'csv') || 'csv';
            
            const response = await fetch('/analyst/api/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    analysis_data: analysisData,
                    format: format
                })
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `powerbi_analysis_${new Date().toISOString().split('T')[0]}.${format}`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            } else {
                showError('Export failed');
            }
        } catch (error) {
            showError('Export error: ' + error.message);
        }
    }

    // UI Helpers
    function addMessage(sender, content, type = 'text') {
        const container = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const avatar = sender === 'user' ? '👤' : '🤖';
        const name = sender === 'user' ? 'You' : 'Power BI Analyst';
        
        if (type === 'html') {
            messageDiv.innerHTML = `
                <div class="message-avatar">${avatar}</div>
                <div class="message-content">
                    <div class="message-header">${name}</div>
                    ${content}
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="message-avatar">${avatar}</div>
                <div class="message-content">
                    <div class="message-header">${name}</div>
                    <div class="message-text">${escapeHtml(content)}</div>
                </div>
            `;
        }
        
        container.appendChild(messageDiv);
        container.scrollTop = container.scrollHeight;
    }

    function createDataTable(data) {
        if (!data || data.length === 0) return '<p>No data to display</p>';
        
        const columns = Object.keys(data[0]);
        const maxRows = 10;
        const displayData = data.slice(0, maxRows);
        
        let html = '<table class="data-table"><thead><tr>';
        columns.forEach(col => {
            html += `<th>${escapeHtml(col)}</th>`;
        });
        html += '</tr></thead><tbody>';
        
        displayData.forEach(row => {
            html += '<tr>';
            columns.forEach(col => {
                const value = row[col];
                html += `<td>${value === null ? 'null' : escapeHtml(String(value))}</td>`;
            });
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        
        if (data.length > maxRows) {
            html += `<p style="margin-top: 0.5rem; font-size: 0.875rem; color: #666;">Showing ${maxRows} of ${data.length} rows</p>`;
        }
        
        return html;
    }

    function showModal(modalId) {
        document.getElementById(modalId).style.display = 'flex';
    }

    function closeModal(modalId) {
        document.getElementById(modalId).style.display = 'none';
    }

    function showLoading(message) {
        // Implementation for loading overlay
        console.log('Loading:', message);
    }

    function hideLoading() {
        // Implementation to hide loading overlay
        console.log('Loading complete');
    }

    function showError(message) {
        addMessage('assistant', message, 'error');
    }

    function showHelp() {
        showModal('helpModal');
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function formatDate(dateStr) {
        if (!dateStr) return 'Unknown';
        try {
            const date = new Date(dateStr);
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
        } catch {
            return dateStr;
        }
    }

    function handleKeyPress(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            analyzeQuery();
        }
    }

    // Close modals when clicking outside
    window.onclick = function(event) {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = 'none';
        }
    }
    '''