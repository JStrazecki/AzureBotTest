# sql_console_ui.py - SQL Console UI Components with Enhanced CSS
"""
SQL Console UI - Enhanced CSS for error analysis features
"""

def get_sql_console_css():
    """Return the CSS styles for the SQL console with error analysis styling"""
    return '''
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
        margin-bottom: 0.25rem;
    }

    .current-db span {
        color: #3b82f6;
        font-weight: 500;
    }

    /* User info styles */
    .user-info {
        margin-top: 0.75rem;
        padding-top: 0.75rem;
        border-top: 1px solid #334155;
    }

    .user-label {
        font-size: 0.75rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.25rem;
    }

    .user-name {
        font-size: 0.875rem;
        color: #10b981;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 0.375rem;
    }

    .user-name::before {
        content: "👤";
        font-size: 1rem;
    }

    /* Multi-database toggle */
    .multi-db-toggle {
        padding: 1rem;
        border-bottom: 1px solid #334155;
        background-color: #0f172a;
    }

    .toggle-container {
        display: flex;
        align-items: center;
        cursor: pointer;
        user-select: none;
    }

    .toggle-container input[type="checkbox"] {
        width: 1.25rem;
        height: 1.25rem;
        margin-right: 0.5rem;
        cursor: pointer;
    }

    .toggle-label {
        font-size: 0.875rem;
        color: #e2e8f0;
        font-weight: 500;
    }

    .select-all-btn {
        margin-top: 0.5rem;
        width: 100%;
        padding: 0.375rem 0.75rem;
        background-color: #3b82f6;
        color: white;
        border: none;
        border-radius: 0.375rem;
        font-size: 0.75rem;
        cursor: pointer;
        transition: all 0.2s;
    }

    .select-all-btn:hover {
        background-color: #2563eb;
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
        display: flex;
        align-items: center;
    }

    /* Multi-select checkbox for databases */
    .database-item.multi-select-mode {
        padding-left: 2.5rem;
    }

    .database-checkbox {
        position: absolute;
        left: 0.75rem;
        width: 1rem;
        height: 1rem;
        cursor: pointer;
    }

    .database-item:hover, .table-item:hover {
        background-color: #334155;
    }

    .database-item.active {
        background-color: #1e3a8a;
        color: #93bbfc;
    }

    .database-item.selected {
        background-color: #1e3a8a;
        color: #93bbfc;
        border-left: 3px solid #3b82f6;
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

    /* Selected databases indicator */
    .selected-db-indicator {
        padding: 1rem;
        background-color: #0f172a;
        border-radius: 0.375rem;
        margin-top: 0.5rem;
    }

    .selected-count {
        font-size: 0.875rem;
        color: #3b82f6;
        font-weight: 500;
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
        flex-wrap: wrap;
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

    /* Multi-database results */
    .multi-db-results {
        margin-top: 1rem;
    }

    .db-result-section {
        margin-bottom: 1.5rem;
        background-color: #0f172a;
        border: 1px solid #334155;
        border-radius: 0.5rem;
        padding: 1rem;
    }

    .db-result-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #334155;
    }

    .db-name {
        font-weight: 600;
        color: #3b82f6;
        font-size: 1rem;
    }

    .db-result-stats {
        font-size: 0.75rem;
        color: #94a3b8;
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

    /* Enhanced Error Analysis Styles */
    .error-analysis {
        background-color: rgba(99, 102, 241, 0.1);
        border: 1px solid #6366f1;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }

    .error-analysis h4 {
        color: #6366f1;
        margin-bottom: 0.5rem;
        font-size: 1.1rem;
    }

    .error-analysis > div {
        margin-bottom: 0.75rem;
    }

    .error-analysis strong {
        color: #93bbfc;
        display: inline-block;
        margin-right: 0.5rem;
    }

    .db-error-analysis {
        background-color: rgba(239, 68, 68, 0.1);
        border: 1px solid #ef4444;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
    }

    .db-error-analysis h5 {
        color: #ef4444;
        margin-bottom: 0.5rem;
        font-size: 1rem;
    }

    /* Discovery result styles */
    .discovery-results {
        background-color: rgba(59, 130, 246, 0.1);
        border: 1px solid #3b82f6;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-top: 1rem;
    }

    /* Fixed query indicator */
    .fixed-query-indicator {
        display: inline-block;
        background-color: #10b981;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 0.375rem;
        font-size: 0.75rem;
        font-weight: 600;
        margin-left: 0.5rem;
    }

    /* Input area */
    .input-area {
        padding: 1.5rem 2rem;
        background-color: #1e293b;
        border-top: 1px solid #334155;
    }

    /* Multi-database indicator */
    .multi-db-indicator {
        background-color: #1e3a8a;
        color: #93bbfc;
        padding: 0.5rem 1rem;
        border-radius: 0.375rem;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.875rem;
    }

    .indicator-icon {
        font-size: 1.25rem;
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

    /* Log message styles */
    .log-message .message-content {
        border-left: 3px solid;
        background-color: rgba(30, 41, 59, 0.5) !important;
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
        
        .quick-actions {
            flex-wrap: wrap;
        }
    }
    '''