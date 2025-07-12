# sql_console_routes.py - SQL Console Routes and Logic with Enhanced Logging
"""
SQL Console Routes - Enhanced with detailed logging and fixed database access
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from aiohttp import web
from aiohttp.web import Request, Response, json_response
import aiohttp
import asyncio

# Import UI components
from sql_console_html import get_sql_console_html

logger = logging.getLogger(__name__)

# Known accessible databases from MSI check - hardcoded based on CheckDatabaseAccess result
KNOWN_ACCESSIBLE_DATABASES = ['master', '_support', 'demo']

class SQLConsole:
    """SQL Console handler with proper authentication and multi-database support"""
    
    def __init__(self, sql_translator=None):
        self.sql_translator = sql_translator
        self.function_url = os.environ.get("AZURE_FUNCTION_URL", "")
        self.sessions = {}
        self.active_requests = {}  # Track active requests for cancellation
        
        # Check if authentication is embedded in URL
        self.url_has_auth = "code=" in self.function_url
        
        logger.info(f"SQL Console initialized")
        logger.info(f"Function URL configured: {'Yes' if self.function_url else 'No'}")
        logger.info(f"Authentication method: {'URL-embedded' if self.url_has_auth else 'Header-based'}")
        logger.info(f"SQL Translator available: {'Yes' if sql_translator else 'No'}")
    
    async def console_page(self, request: Request) -> Response:
        """Serve the SQL console HTML page"""
        html_content = get_sql_console_html()
        return Response(text=html_content, content_type='text/html')
    
    async def handle_message(self, request: Request) -> Response:
        """Handle incoming console messages with enhanced logging"""
        request_id = datetime.now().strftime("%H%M%S%f")[:10]
        
        try:
            data = await request.json()
            message = data.get('message', '').strip()
            database = data.get('database', 'master')
            session_id = data.get('session_id')
            multi_db_mode = data.get('multi_db_mode', False)
            databases = data.get('databases', [])
            
            # Store request for potential cancellation
            self.active_requests[session_id] = request_id
            
            logger.info(f"[{request_id}] Console message: {message[:50]}... in database: {database}")
            
            # Send initial acknowledgment
            await self._send_log_message(session_id, f"🔍 Processing: {message}", "info")
            
            if multi_db_mode:
                await self._send_log_message(session_id, f"📊 Multi-database mode: {len(databases)} databases selected", "info")
            
            # Check for special commands
            if message.lower() in ['help', '?']:
                await self._send_log_message(session_id, "📖 Showing help information", "info")
                return json_response({
                    'status': 'success',
                    'response_type': 'help',
                    'content': self._get_help_text()
                })
            
            if message.lower() in ['show databases', 'databases', 'sp_databases']:
                await self._send_log_message(session_id, "🗄️ Fetching database list...", "info")
                databases = await self._get_databases_with_logging(session_id)
                
                content = f"Available databases ({len(databases)}):\n" + "\n".join(f"• {db}" for db in databases)
                return json_response({
                    'status': 'success',
                    'response_type': 'text',
                    'content': content
                })
            
            if message.lower() in ['show tables', 'tables']:
                await self._send_log_message(session_id, f"📋 Getting tables from database: {database}", "info")
                tables = await self._get_tables_with_logging(database, session_id)
                
                if tables:
                    content = f"Tables in {database} ({len(tables)}):\n" + "\n".join(f"• {table}" for table in tables)
                else:
                    content = f"No tables found in {database} or access denied"
                    await self._send_log_message(session_id, f"⚠️ No tables found in {database}", "warning")
                
                return json_response({
                    'status': 'success',
                    'response_type': 'text',
                    'content': content,
                    'refresh_tables': True
                })
            
            # Process SQL query
            if self.sql_translator:
                try:
                    # Check if it's already a SQL query
                    if self._is_sql_query(message):
                        await self._send_log_message(session_id, "✅ Detected direct SQL query", "info")
                        sql_query = message
                        explanation = "Direct SQL query execution"
                    else:
                        await self._send_log_message(session_id, "🤖 Translating natural language to SQL...", "info")
                        
                        # Get schema context
                        schema_context = await self._get_schema_context(database)
                        if schema_context:
                            await self._send_log_message(session_id, f"📊 Schema context: {schema_context[:100]}...", "debug")
                        
                        # Translate
                        result = await self.sql_translator.translate_to_sql(
                            message,
                            database=database,
                            schema_context=schema_context
                        )
                        
                        if result.error or not result.query:
                            error_msg = result.error or 'Could not translate to SQL query'
                            await self._send_log_message(session_id, f"❌ Translation failed: {error_msg}", "error")
                            return json_response({
                                'status': 'error',
                                'error': error_msg
                            })
                        
                        sql_query = result.query
                        explanation = result.explanation
                        await self._send_log_message(session_id, f"✅ Translated to SQL: {sql_query[:100]}...", "success")
                    
                    # Execute the query
                    if multi_db_mode and databases:
                        await self._send_log_message(session_id, f"🔄 Executing across {len(databases)} databases...", "info")
                        multi_results = await self._execute_multi_db_query_with_logging(sql_query, databases, session_id)
                        
                        # Count total results
                        total_rows = sum(r.get('row_count', 0) for r in multi_results)
                        total_time = sum(r.get('execution_time_ms', 0) for r in multi_results)
                        
                        await self._send_log_message(session_id, f"✅ Multi-DB execution complete: {total_rows} total rows in {total_time:.0f}ms", "success")
                        
                        return json_response({
                            'status': 'success',
                            'response_type': 'sql_result',
                            'sql_query': sql_query,
                            'explanation': explanation,
                            'multi_db_results': multi_results,
                            'total_rows': total_rows,
                            'total_execution_time': total_time,
                            'database_count': len(databases)
                        })
                    else:
                        await self._send_log_message(session_id, f"🔄 Executing query on {database}...", "info")
                        execution_result = await self._execute_sql_query_with_logging(sql_query, database, session_id)
                        
                        if execution_result.get('error'):
                            await self._send_log_message(session_id, f"❌ Query failed: {execution_result['error']}", "error")
                            return json_response({
                                'status': 'error',
                                'error': execution_result['error']
                            })
                        
                        rows = execution_result.get('row_count', 0)
                        time_ms = execution_result.get('execution_time_ms', 0)
                        await self._send_log_message(session_id, f"✅ Query complete: {rows} rows in {time_ms:.0f}ms", "success")
                        
                        return json_response({
                            'status': 'success',
                            'response_type': 'sql_result',
                            'sql_query': sql_query,
                            'database': database,
                            'explanation': explanation,
                            'rows': execution_result.get('rows', []),
                            'row_count': rows,
                            'execution_time': time_ms,
                            'current_database': database
                        })
                    
                except Exception as e:
                    logger.error(f"[{request_id}] Error processing query: {e}", exc_info=True)
                    await self._send_log_message(session_id, f"❌ Error: {str(e)}", "error")
                    return json_response({
                        'status': 'error',
                        'error': f'Query processing error: {str(e)}'
                    })
            else:
                await self._send_log_message(session_id, "❌ SQL translator not available", "error")
                return json_response({
                    'status': 'error',
                    'error': 'SQL translator not available. Please check Azure OpenAI configuration.'
                })
                
        except Exception as e:
            logger.error(f"[{request_id}] Console message error: {e}", exc_info=True)
            await self._send_log_message(session_id, f"❌ Unexpected error: {str(e)}", "error")
            return json_response({
                'status': 'error',
                'error': str(e)
            })
        finally:
            # Remove from active requests
            if session_id in self.active_requests:
                del self.active_requests[session_id]
    
    async def _send_log_message(self, session_id: str, message: str, level: str = "info"):
        """Send a log message to the client (placeholder for WebSocket implementation)"""
        # In a real implementation, this would send via WebSocket
        # For now, just log it
        logger.info(f"[Console-{session_id}] {level.upper()}: {message}")
    
    def _is_sql_query(self, message: str) -> bool:
        """Check if message is a SQL query"""
        sql_keywords = ['select', 'with', 'show', 'describe', 'exec', 'sp_']
        message_lower = message.lower().strip()
        return any(message_lower.startswith(keyword) for keyword in sql_keywords)
    
    def _get_help_text(self) -> str:
        """Get help text for console"""
        return """SQL Assistant Console Commands:

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
• show databases - List all databases
• show tables - List tables in current database
• sp_databases - List all databases (T-SQL)
• sp_tables - List tables using system procedure

**Multi-Database Queries:**
• Toggle "Multi-Database Query" mode in the sidebar
• Select multiple databases using checkboxes
• Run the same query across all selected databases
• Results are grouped by database

**Available Databases (MSI Access):**
• master - System metadata
• _support - Support database
• demo - Demo database

**Tips:**
• Click on a database to switch context
• Click on a table name to create a SELECT query
• Use natural language or SQL syntax
• Results are limited to prevent overload
• The console shows detailed steps for each operation
• If tables don't show with 'show tables', try 'sp_tables' or 'SELECT name FROM sys.tables'"""
    
    async def _get_databases_with_logging(self, session_id: str, force_refresh: bool = False) -> List[str]:
        """Get list of databases with logging"""
        try:
            if not self.function_url:
                await self._send_log_message(session_id, "⚠️ Azure Function URL not configured, using fallback", "warning")
                return KNOWN_ACCESSIBLE_DATABASES.copy()
            
            await self._send_log_message(session_id, "🔍 Discovering accessible databases from server...", "info")
            
            # Call Azure Function to get databases
            payload = {
                "query_type": "metadata",
                "force_refresh": force_refresh
            }
            
            result = await self._call_function_with_logging(payload, session_id)
            
            if result and 'databases' in result:
                databases = result['databases']
                await self._send_log_message(session_id, f"✅ Found {len(databases)} accessible databases", "success")
                
                # Log additional info if available
                if 'msi_identity' in result:
                    await self._send_log_message(session_id, f"🔐 MSI Identity: {result['msi_identity']}", "debug")
                
                if 'cache_info' in result and result['cache_info'].get('cached'):
                    cache_age = result['cache_info'].get('cache_age_seconds', 0)
                    await self._send_log_message(session_id, f"📦 Using cached results (age: {cache_age}s)", "debug")
                else:
                    await self._send_log_message(session_id, "🔄 Fresh discovery completed", "debug")
                
                return databases
            else:
                await self._send_log_message(session_id, "⚠️ No database list received, using fallback", "warning")
                return KNOWN_ACCESSIBLE_DATABASES.copy()
                
        except Exception as e:
            logger.error(f"Error getting databases: {e}")
            await self._send_log_message(session_id, f"❌ Error getting databases: {str(e)}", "error")
            return KNOWN_ACCESSIBLE_DATABASES.copy()
    
    async def _get_tables_with_logging(self, database: str, session_id: str) -> List[str]:
        """Get list of tables in database with logging"""
        try:
            if not self.function_url:
                await self._send_log_message(session_id, "⚠️ Azure Function URL not configured", "warning")
                return []
            
            # First try using sp_tables which is more reliable
            sp_tables_query = "EXEC sp_tables @table_type = \"'TABLE'\""
            
            await self._send_log_message(session_id, f"🔍 Trying sp_tables to list tables in {database}", "info")
            
            result = await self._execute_sql_query_with_logging(sp_tables_query, database, session_id)
            
            if result.get('rows'):
                # sp_tables returns TABLE_QUALIFIER, TABLE_OWNER, TABLE_NAME, TABLE_TYPE, REMARKS
                tables = []
                for row in result['rows']:
                    # Get table name, handling different column name possibilities
                    table_name = row.get('TABLE_NAME') or row.get('table_name') or row.get('3')
                    if table_name:
                        # Optional: include schema
                        owner = row.get('TABLE_OWNER') or row.get('table_owner') or row.get('2')
                        if owner and owner != 'dbo':
                            tables.append(f"{owner}.{table_name}")
                        else:
                            tables.append(table_name)
                
                if tables:
                    await self._send_log_message(session_id, f"✅ Found {len(tables)} tables using sp_tables", "success")
                    return sorted(tables)
            
            # If sp_tables didn't work, try sys.tables
            await self._send_log_message(session_id, f"🔍 Trying sys.tables approach", "info")
            
            sys_tables_query = """
            SELECT 
                SCHEMA_NAME(schema_id) as SchemaName,
                name as TableName
            FROM sys.tables
            ORDER BY SchemaName, TableName
            """
            
            result = await self._execute_sql_query_with_logging(sys_tables_query, database, session_id)
            
            if result.get('rows'):
                tables = []
                for row in result['rows']:
                    schema = row.get('SchemaName', 'dbo')
                    table = row.get('TableName', '')
                    if table:
                        if schema != 'dbo':
                            tables.append(f"{schema}.{table}")
                        else:
                            tables.append(table)
                
                await self._send_log_message(session_id, f"✅ Found {len(tables)} tables using sys.tables", "success")
                return tables
            
            # Last resort: try INFORMATION_SCHEMA
            await self._send_log_message(session_id, f"🔍 Trying INFORMATION_SCHEMA as fallback", "info")
            
            info_schema_query = """
            SELECT TABLE_SCHEMA, TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE' 
            ORDER BY TABLE_SCHEMA, TABLE_NAME
            """
            
            result = await self._execute_sql_query_with_logging(info_schema_query, database, session_id)
            
            if result.get('rows'):
                tables = []
                for row in result['rows']:
                    schema = row.get('TABLE_SCHEMA', 'dbo')
                    table = row.get('TABLE_NAME', '')
                    if table:
                        if schema != 'dbo':
                            tables.append(f"{schema}.{table}")
                        else:
                            tables.append(table)
                
                await self._send_log_message(session_id, f"✅ Found {len(tables)} tables using INFORMATION_SCHEMA", "success")
                return tables
            
            # If all methods failed
            await self._send_log_message(session_id, f"⚠️ Could not retrieve tables from {database}", "warning")
            await self._send_log_message(session_id, f"💡 Try running: sp_tables or SELECT name FROM sys.tables", "info")
            return []
                
        except Exception as e:
            logger.error(f"Error getting tables: {e}")
            await self._send_log_message(session_id, f"❌ Error getting tables: {str(e)}", "error")
            return []
    
    async def _get_schema_context(self, database: str) -> str:
        """Get schema context for translation"""
        try:
            # Don't query for schema context, just use database name
            return f"Database: {database}. Available databases: {', '.join(KNOWN_ACCESSIBLE_DATABASES)}"
        except:
            return ""
    
    async def _call_function_with_logging(self, payload: Dict[str, Any], session_id: str) -> Optional[Dict]:
        """Call Azure Function with logging"""
        try:
            headers = {"Content-Type": "application/json"}
            
            await self._send_log_message(session_id, f"📡 Calling Azure Function: {payload.get('query_type', 'unknown')}", "debug")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.function_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        await self._send_log_message(session_id, "✅ Function call successful", "debug")
                        return result
                    else:
                        error_text = await response.text()
                        await self._send_log_message(session_id, f"❌ Function call failed: {response.status}", "error")
                        logger.error(f"Function call failed: {response.status} - {error_text}")
                        return None
                        
        except asyncio.TimeoutError:
            await self._send_log_message(session_id, "❌ Function call timed out after 30 seconds", "error")
            return None
        except Exception as e:
            logger.error(f"Error calling function: {e}")
            await self._send_log_message(session_id, f"❌ Function call error: {str(e)}", "error")
            return None
    
    async def _execute_sql_query_with_logging(self, query: str, database: str, session_id: str) -> Dict[str, Any]:
        """Execute SQL query with logging"""
        if not self.function_url:
            return {'error': 'Azure Function URL not configured'}
        
        try:
            payload = {
                "query_type": "single",
                "query": query,
                "database": database,
                "output_format": "raw"
            }
            
            await self._send_log_message(session_id, f"📤 Sending query to database '{database}'", "debug")
            
            result = await self._call_function_with_logging(payload, session_id)
            
            if result:
                if 'error' in result:
                    # Enhanced error messages for common issues
                    error_msg = result['error']
                    if "Invalid object name" in error_msg:
                        await self._send_log_message(session_id, f"⚠️ Table not found - database might be empty or table doesn't exist", "warning")
                    elif "Login failed" in error_msg:
                        await self._send_log_message(session_id, f"⚠️ Access denied to database '{database}'", "warning")
                    return {'error': error_msg}
                
                rows = result.get('row_count', 0)
                await self._send_log_message(session_id, f"📥 Received {rows} rows from database", "debug")
                
                return {
                    'rows': result.get('rows', []),
                    'row_count': rows,
                    'execution_time_ms': result.get('execution_time_ms', 0)
                }
            else:
                return {'error': 'Failed to execute query - no response from function'}
                
        except Exception as e:
            logger.error(f"Error executing query: {e}", exc_info=True)
            return {'error': f'Query execution error: {str(e)}'}
    
    async def _execute_multi_db_query_with_logging(self, query: str, databases: List[str], session_id: str) -> List[Dict[str, Any]]:
        """Execute SQL query across multiple databases with logging"""
        if not self.function_url:
            return [{'database': db, 'error': 'Azure Function URL not configured'} for db in databases]
        
        try:
            payload = {
                "query_type": "multi_database",
                "query": query,
                "databases": databases,
                "output_format": "raw"
            }
            
            await self._send_log_message(session_id, f"📤 Sending multi-DB query to {len(databases)} databases", "info")
            
            result = await self._call_function_with_logging(payload, session_id)
            
            if result and isinstance(result, list):
                formatted_results = []
                for db_result in result:
                    db_name = db_result.get('database', 'Unknown')
                    if db_result.get('error'):
                        await self._send_log_message(session_id, f"❌ {db_name}: {db_result['error']}", "error")
                    else:
                        rows = db_result.get('row_count', 0)
                        await self._send_log_message(session_id, f"✅ {db_name}: {rows} rows", "success")
                    
                    formatted_results.append({
                        'database': db_name,
                        'rows': db_result.get('rows', []),
                        'row_count': db_result.get('row_count', 0),
                        'execution_time': db_result.get('execution_time_ms', 0),
                        'error': db_result.get('error')
                    })
                return formatted_results
            else:
                await self._send_log_message(session_id, "❌ Invalid response from multi-database query", "error")
                return [{
                    'database': db,
                    'error': 'Failed to execute multi-database query',
                    'rows': [],
                    'row_count': 0,
                    'execution_time': 0
                } for db in databases]
                
        except Exception as e:
            logger.error(f"Error executing multi-database query: {e}", exc_info=True)
            await self._send_log_message(session_id, f"❌ Multi-DB query error: {str(e)}", "error")
            return [{
                'database': db,
                'error': f'Query execution error: {str(e)}',
                'rows': [],
                'row_count': 0,
                'execution_time': 0
            } for db in databases]
    
    async def get_databases_api(self, request: Request) -> Response:
        """API endpoint to get databases"""
        try:
            session_id = request.query.get('session_id', 'api')
            force_refresh = request.query.get('force_refresh', '').lower() == 'true'
            
            databases = await self._get_databases_with_logging(session_id, force_refresh)
            
            logger.info(f"Returning {len(databases)} accessible databases")
            
            return json_response({
                'status': 'success',
                'databases': databases,
                'note': 'Showing databases with confirmed MSI access'
            })
        except Exception as e:
            logger.error(f"Database API error: {e}", exc_info=True)
            return json_response({
                'status': 'error',
                'error': str(e)
            })
    
    async def get_tables_api(self, request: Request) -> Response:
        """API endpoint to get tables"""
        try:
            database = request.query.get('database', 'master')
            session_id = request.query.get('session_id', 'api')
            
            tables = await self._get_tables_with_logging(database, session_id)
            
            return json_response({
                'status': 'success',
                'tables': tables,
                'database': database
            })
        except Exception as e:
            logger.error(f"Tables API error: {e}", exc_info=True)
            return json_response({
                'status': 'error',
                'error': str(e)
            })
    
    async def cancel_request_api(self, request: Request) -> Response:
        """API endpoint to cancel active request"""
        try:
            data = await request.json()
            session_id = data.get('session_id')
            
            if session_id in self.active_requests:
                request_id = self.active_requests[session_id]
                del self.active_requests[session_id]
                
                logger.info(f"Cancelled request {request_id} for session {session_id}")
                
                return json_response({
                    'status': 'success',
                    'message': 'Request cancelled'
                })
            else:
                return json_response({
                    'status': 'success',
                    'message': 'No active request to cancel'
                })
                
        except Exception as e:
            logger.error(f"Cancel request error: {e}", exc_info=True)
            return json_response({
                'status': 'error',
                'error': str(e)
            })
    
    async def get_current_user_api(self, request: Request) -> Response:
        """API endpoint to get current user information"""
        try:
            # Check if user info is in request headers (from Azure App Service authentication)
            user_info = {
                'name': 'SQL User',
                'email': None,
                'auth_type': 'Managed Service Identity',
                'sql_user': '6dd880ac-0e1b-43ed-b83b-a6e0021e9d8a@aa9eb9c3-b2af-4522-969c-82cb9efc0e88'
            }
            
            # Azure App Service puts authenticated user info in headers
            headers_to_check = {
                'X-MS-CLIENT-PRINCIPAL-NAME': 'email',
                'X-MS-CLIENT-PRINCIPAL': 'principal',
                'X-MS-CLIENT-PRINCIPAL-ID': 'id'
            }
            
            for header, field in headers_to_check.items():
                value = request.headers.get(header)
                if value:
                    if field == 'email':
                        user_info['email'] = value
                        user_info['name'] = value.split('@')[0]
                    logger.info(f"Found {field}: {value[:20]}...")
            
            return json_response({
                'status': 'success',
                'user': user_info
            })
            
        except Exception as e:
            logger.error(f"Current user API error: {e}", exc_info=True)
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
    app.router.add_get('/console/api/current-user', console.get_current_user_api)
    app.router.add_post('/console/api/cancel', console.cancel_request_api)
    
    logger.info("SQL Console routes added successfully with enhanced logging")
    return console