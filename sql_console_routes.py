# sql_console_routes.py - SQL Console Routes with Enhanced Logging
"""
SQL Console Routes - Updated with detailed step-by-step logging
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from aiohttp import web
from aiohttp.web import Request, Response, json_response
import aiohttp

# Import UI components
from sql_console_html import get_sql_console_html

logger = logging.getLogger(__name__)

class SQLConsole:
    """SQL Console handler with detailed logging and manual database loading"""
    
    def __init__(self, sql_translator=None):
        self.sql_translator = sql_translator
        self.function_url = os.environ.get("AZURE_FUNCTION_URL", "")
        self.sessions = {}
        
        # Check if authentication is embedded in URL
        self.url_has_auth = "code=" in self.function_url
        
        # Start with empty databases - require manual loading
        self.accessible_databases = []
        self.databases_loaded = False
        
        logger.info(f"[SQLConsole] Initialized")
        logger.info(f"[SQLConsole] Function URL configured: {'Yes' if self.function_url else 'No'}")
        logger.info(f"[SQLConsole] Authentication method: {'URL-embedded' if self.url_has_auth else 'Header-based'}")
        logger.info(f"[SQLConsole] SQL Translator available: {'Yes' if sql_translator else 'No'}")
        logger.info(f"[SQLConsole] Manual database loading required - no auto-load")
    
    async def console_page(self, request: Request) -> Response:
        """Serve the SQL console HTML page"""
        # Use the updated HTML with manual loading
        try:
            with open('sql_console_html_v2.html', 'r') as f:
                html_content = f.read()
        except:
            # Fallback to get_sql_console_html if file not found
            html_content = get_sql_console_html()
        return Response(text=html_content, content_type='text/html')
    
    async def handle_message(self, request: Request) -> Response:
        """Handle incoming console messages with detailed step logging"""
        request_id = datetime.now().strftime("%H%M%S%f")[:10]
        
        try:
            # Log step 1: Receive request
            logger.info(f"[{request_id}] Step 1: Receiving console message request")
            
            data = await request.json()
            message = data.get('message', '').strip()
            database = data.get('database', 'master')
            session_id = data.get('session_id')
            
            logger.info(f"[{request_id}] Step 2: Parsed request - Message: '{message[:50]}...', Database: '{database}', Session: {session_id}")
            
            # Check if databases are loaded
            if not self.databases_loaded and database == 'master':
                logger.warning(f"[{request_id}] Step 3: Databases not loaded yet, prompting user")
                return json_response({
                    'status': 'error',
                    'error': 'Please load databases first by clicking "Load" in the sidebar.'
                })
            
            # Step 3: Validate database access
            logger.info(f"[{request_id}] Step 3: Validating database access")
            if self.accessible_databases and database not in self.accessible_databases:
                logger.warning(f"[{request_id}] Database '{database}' not in accessible list, defaulting to first available")
                if self.accessible_databases:
                    database = self.accessible_databases[0]
                else:
                    database = 'master'
            
            # Step 4: Check for special commands
            logger.info(f"[{request_id}] Step 4: Checking for special commands")
            
            # Handle sp_databases
            if message.lower() == 'sp_databases':
                logger.info(f"[{request_id}] Detected sp_databases command")
                return await self._handle_sp_databases(request_id)
            
            # Handle sp_tables
            if message.lower() == 'sp_tables':
                logger.info(f"[{request_id}] Detected sp_tables command")
                return await self._handle_sp_tables(database, request_id)
            
            # Handle help
            if message.lower() in ['help', '?']:
                logger.info(f"[{request_id}] Returning help text")
                return json_response({
                    'status': 'success',
                    'response_type': 'help',
                    'content': self._get_help_text()
                })
            
            # Step 5: Process SQL query
            logger.info(f"[{request_id}] Step 5: Processing as SQL query")
            
            if self.sql_translator:
                try:
                    # Step 6: Check if direct SQL or needs translation
                    if self._is_sql_query(message):
                        logger.info(f"[{request_id}] Step 6: Detected direct SQL query")
                        sql_query = message
                        explanation = "Direct SQL query execution"
                    else:
                        # Step 6: Translate natural language
                        logger.info(f"[{request_id}] Step 6: Translating natural language to SQL")
                        
                        # Get schema context
                        logger.info(f"[{request_id}] Step 6a: Fetching schema context for {database}")
                        schema_context = await self._get_schema_context(database)
                        
                        logger.info(f"[{request_id}] Step 6b: Calling SQL translator")
                        result = await self.sql_translator.translate_to_sql(
                            message,
                            database=database,
                            schema_context=schema_context
                        )
                        
                        if result.error or not result.query:
                            logger.error(f"[{request_id}] Step 6c: Translation failed - {result.error}")
                            return json_response({
                                'status': 'error',
                                'error': result.error or 'Could not translate to SQL query'
                            })
                        
                        sql_query = result.query
                        explanation = result.explanation
                        logger.info(f"[{request_id}] Step 6c: Translated to SQL: {sql_query[:100]}...")
                    
                    # Step 7: Execute query
                    logger.info(f"[{request_id}] Step 7: Executing SQL query on database '{database}'")
                    execution_result = await self._execute_sql_query(sql_query, database, request_id)
                    
                    if execution_result.get('error'):
                        logger.error(f"[{request_id}] Step 8: Query execution failed - {execution_result['error']}")
                        return json_response({
                            'status': 'error',
                            'error': execution_result['error']
                        })
                    
                    logger.info(f"[{request_id}] Step 8: Query executed successfully - {execution_result.get('row_count', 0)} rows returned")
                    
                    return json_response({
                        'status': 'success',
                        'response_type': 'sql_result',
                        'sql_query': sql_query,
                        'database': database,
                        'explanation': explanation,
                        'rows': execution_result.get('rows', []),
                        'row_count': execution_result.get('row_count', 0),
                        'execution_time': execution_result.get('execution_time_ms', 0),
                        'current_database': database
                    })
                    
                except Exception as e:
                    logger.error(f"[{request_id}] Error in query processing: {e}", exc_info=True)
                    return json_response({
                        'status': 'error',
                        'error': f'Query processing error: {str(e)}'
                    })
            else:
                logger.error(f"[{request_id}] SQL translator not available")
                return json_response({
                    'status': 'error',
                    'error': 'SQL translator not available. Please check Azure OpenAI configuration.'
                })
                
        except Exception as e:
            logger.error(f"[{request_id}] Unexpected error in handle_message: {e}", exc_info=True)
            return json_response({
                'status': 'error',
                'error': str(e)
            })
    
    async def _handle_sp_databases(self, request_id: str) -> Response:
        """Handle sp_databases system procedure"""
        logger.info(f"[{request_id}] Executing sp_databases procedure")
        
        try:
            # Get databases from the function
            databases = await self._get_databases(force_reload=True, request_id=request_id)
            
            # Format like sp_databases output
            content = "Available databases:\n" + "\n".join(f"• {db}" for db in databases)
            
            logger.info(f"[{request_id}] sp_databases returned {len(databases)} databases")
            
            return json_response({
                'status': 'success',
                'response_type': 'text',
                'content': content,
                'refresh_databases': True
            })
            
        except Exception as e:
            logger.error(f"[{request_id}] sp_databases error: {e}")
            return json_response({
                'status': 'error',
                'error': f'Error listing databases: {str(e)}'
            })
    
    async def _handle_sp_tables(self, database: str, request_id: str) -> Response:
        """Handle sp_tables system procedure"""
        logger.info(f"[{request_id}] Executing sp_tables for database: {database}")
        
        try:
            # Execute sp_tables query
            query = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME"
            
            logger.info(f"[{request_id}] Running INFORMATION_SCHEMA query")
            result = await self._execute_sql_query(query, database, request_id)
            
            if result.get('error'):
                # If failed, try alternative query
                logger.info(f"[{request_id}] First query failed, trying sys.tables")
                query = "SELECT name AS TABLE_NAME FROM sys.tables ORDER BY name"
                result = await self._execute_sql_query(query, database, request_id)
            
            if result.get('rows'):
                tables = [row.get('TABLE_NAME') or row.get('name') for row in result['rows']]
                content = f"Tables in {database}:\n" + "\n".join(f"• {table}" for table in tables)
                logger.info(f"[{request_id}] Found {len(tables)} tables")
            else:
                content = f"No tables found in {database}"
                logger.warning(f"[{request_id}] No tables found")
            
            return json_response({
                'status': 'success',
                'response_type': 'text',
                'content': content,
                'refresh_tables': True
            })
            
        except Exception as e:
            logger.error(f"[{request_id}] sp_tables error: {e}")
            return json_response({
                'status': 'error',
                'error': f'Error listing tables: {str(e)}'
            })
    
    def _is_sql_query(self, message: str) -> bool:
        """Check if message is a SQL query"""
        sql_keywords = ['select', 'with', 'show', 'describe', 'exec', 'sp_', 'execute']
        message_lower = message.lower().strip()
        return any(message_lower.startswith(keyword) for keyword in sql_keywords)
    
    def _get_help_text(self) -> str:
        """Get help text for console"""
        return """SQL Assistant Console Commands:

**IMPORTANT**: You must click "Load" in the sidebar to fetch available databases first!

**System Procedures (SQL Server):**
• sp_databases - List all accessible databases
• sp_tables - List tables in current database
• SELECT name FROM sys.schemas - List schemas
• SELECT name FROM sys.tables - List tables

**Natural Language Queries:**
• "Show me all customers"
• "What's the total revenue by month?"
• "Find products with low inventory"
• "List all tables in the database"

**SQL Commands:**
• SELECT, WITH, and other read queries
• Direct SQL syntax supported
• Use TOP to limit results (T-SQL syntax)

**Special Commands:**
• help - Show this help message

**Security Note:**
• No automatic database loading for security
• Click "Load" to manually fetch databases
• Only accessible databases will be shown

**Tips:**
• Watch the process steps to see what's happening
• Use the Cancel button to stop long operations
• Click on a table name to create a SELECT query"""
    
    async def _get_databases(self, force_reload: bool = False, request_id: str = "") -> List[str]:
        """Get list of databases with detailed logging"""
        try:
            # Return cached if available and not forcing reload
            if self.accessible_databases and not force_reload:
                logger.info(f"[{request_id}] Returning cached databases: {len(self.accessible_databases)} databases")
                return self.accessible_databases
            
            if not self.function_url:
                logger.warning(f"[{request_id}] Azure Function URL not configured")
                return []
            
            logger.info(f"[{request_id}] Fetching databases from Azure Function")
            
            # Call Azure Function
            result = await self._call_function({
                "query_type": "metadata"
            }, request_id)
            
            if result and 'databases' in result:
                databases = result['databases']
                logger.info(f"[{request_id}] Retrieved {len(databases)} databases: {', '.join(databases)}")
                
                # Update cache
                self.accessible_databases = databases
                self.databases_loaded = True
                return databases
            else:
                logger.warning(f"[{request_id}] No databases returned from function")
                return []
                
        except Exception as e:
            logger.error(f"[{request_id}] Error getting databases: {e}")
            return []
    
    async def _get_tables(self, database: str, request_id: str = "") -> List[str]:
        """Get list of tables in database"""
        try:
            if not self.function_url:
                return []
            
            logger.info(f"[{request_id}] Fetching tables for database: {database}")
            
            # Execute query to get tables
            query = """
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE' 
            ORDER BY TABLE_NAME
            """
            
            result = await self._execute_sql_query(query, database, request_id)
            
            if result.get('error'):
                # Try alternative query
                logger.info(f"[{request_id}] First query failed, trying sys.tables")
                query = "SELECT name AS TABLE_NAME FROM sys.tables ORDER BY name"
                result = await self._execute_sql_query(query, database, request_id)
            
            if result.get('rows'):
                tables = [row['TABLE_NAME'] for row in result['rows'] if 'TABLE_NAME' in row]
                logger.info(f"[{request_id}] Found {len(tables)} tables")
                return tables
            else:
                logger.warning(f"[{request_id}] No tables found in {database}")
                return []
                
        except Exception as e:
            logger.error(f"[{request_id}] Error getting tables: {e}")
            return []
    
    async def _get_schema_context(self, database: str) -> str:
        """Get schema context for translation"""
        try:
            tables = await self._get_tables(database)
            if tables:
                return f"Available tables in {database}: {', '.join(tables[:10])}"
            return f"Database: {database}"
        except:
            return f"Database: {database}"
    
    async def _call_function(self, payload: Dict[str, Any], request_id: str = "") -> Optional[Dict]:
        """Call Azure Function with detailed logging"""
        try:
            headers = {"Content-Type": "application/json"}
            
            logger.info(f"[{request_id}] Calling Azure Function")
            logger.info(f"[{request_id}] URL: {self.function_url[:50]}...")
            logger.info(f"[{request_id}] Payload: {json.dumps(payload)}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.function_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_text = await response.text()
                    logger.info(f"[{request_id}] Response status: {response.status}")
                    
                    if response.status == 200:
                        result = json.loads(response_text)
                        logger.info(f"[{request_id}] Response preview: {json.dumps(result)[:200]}...")
                        return result
                    else:
                        logger.error(f"[{request_id}] Function error: {response.status} - {response_text[:200]}")
                        return None
                        
        except Exception as e:
            logger.error(f"[{request_id}] Function call exception: {e}")
            return None
    
    async def _execute_sql_query(self, query: str, database: str, request_id: str = "") -> Dict[str, Any]:
        """Execute SQL query with detailed logging"""
        if not self.function_url:
            return {'error': 'Azure Function URL not configured'}
        
        try:
            logger.info(f"[{request_id}] Executing SQL query")
            logger.info(f"[{request_id}] Database: {database}")
            logger.info(f"[{request_id}] Query: {query[:100]}...")
            
            payload = {
                "query_type": "single",
                "query": query,
                "database": database,
                "output_format": "raw"
            }
            
            result = await self._call_function(payload, request_id)
            
            if result:
                if 'error' in result:
                    logger.error(f"[{request_id}] Query error: {result['error']}")
                    return {'error': result['error']}
                
                logger.info(f"[{request_id}] Query success: {result.get('row_count', 0)} rows")
                return {
                    'rows': result.get('rows', []),
                    'row_count': result.get('row_count', 0),
                    'execution_time_ms': result.get('execution_time_ms', 0)
                }
            else:
                return {'error': 'Failed to execute query - no response from function'}
                
        except Exception as e:
            logger.error(f"[{request_id}] Query execution exception: {e}", exc_info=True)
            return {'error': f'Query execution error: {str(e)}'}
    
    async def get_databases_api(self, request: Request) -> Response:
        """API endpoint to get databases"""
        request_id = datetime.now().strftime("%H%M%S%f")[:10]
        
        try:
            logger.info(f"[{request_id}] API: Getting databases")
            databases = await self._get_databases(force_reload=True, request_id=request_id)
            
            return json_response({
                'status': 'success',
                'databases': databases
            })
        except Exception as e:
            logger.error(f"[{request_id}] API: Database error: {e}", exc_info=True)
            return json_response({
                'status': 'error',
                'error': str(e)
            })
    
    async def get_tables_api(self, request: Request) -> Response:
        """API endpoint to get tables"""
        request_id = datetime.now().strftime("%H%M%S%f")[:10]
        
        try:
            database = request.query.get('database', 'master')
            logger.info(f"[{request_id}] API: Getting tables for {database}")
            
            tables = await self._get_tables(database, request_id)
            return json_response({
                'status': 'success',
                'tables': tables
            })
        except Exception as e:
            logger.error(f"[{request_id}] API: Tables error: {e}", exc_info=True)
            return json_response({
                'status': 'error',
                'error': str(e)
            })

def add_console_routes(app, sql_translator=None):
    """Add SQL console routes to the main app"""
    
    console = SQLConsole(sql_translator)
    
    # Console UI
    app.router.add_get('/console', console.console_page)
    app.router.add_get('/console/', console.console_page)
    
    # Console API endpoints
    app.router.add_post('/console/api/message', console.handle_message)
    app.router.add_get('/console/api/databases', console.get_databases_api)
    app.router.add_get('/console/api/tables', console.get_tables_api)
    
    logger.info("[SQLConsole] Routes added successfully")
    return console