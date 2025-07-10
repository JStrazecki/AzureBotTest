# sql_console_routes.py - SQL Console Routes and Logic
"""
SQL Console Routes - Separated backend logic from UI with multi-database support
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from aiohttp import web
from aiohttp.web import Request, Response, json_response
import aiohttp

# Import UI components
from sql_console_html import get_sql_console_html

logger = logging.getLogger(__name__)

class SQLConsole:
    """SQL Console handler with proper authentication and multi-database support"""
    
    def __init__(self, sql_translator=None):
        self.sql_translator = sql_translator
        self.function_url = os.environ.get("AZURE_FUNCTION_URL", "")
        self.sessions = {}
        
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
        """Handle incoming console messages with multi-database support"""
        try:
            data = await request.json()
            message = data.get('message', '').strip()
            database = data.get('database', 'master')
            session_id = data.get('session_id')
            multi_db_mode = data.get('multi_db_mode', False)
            databases = data.get('databases', [])
            
            logger.info(f"Console message: {message[:50]}... in database: {database}")
            if multi_db_mode:
                logger.info(f"Multi-database mode: {len(databases)} databases selected")
            
            # Check for special commands
            if message.lower() in ['help', '?']:
                return json_response({
                    'status': 'success',
                    'response_type': 'help',
                    'content': self._get_help_text()
                })
            
            if message.lower() in ['show databases', 'databases', 'sp_databases']:
                databases = await self._get_databases()
                return json_response({
                    'status': 'success',
                    'response_type': 'text',
                    'content': f"Available databases:\n" + "\n".join(f"• {db}" for db in databases)
                })
            
            if message.lower() in ['show tables', 'tables']:
                tables = await self._get_tables(database)
                if tables:
                    content = f"Tables in {database}:\n" + "\n".join(f"• {table}" for table in tables)
                else:
                    content = f"No tables found in {database} or access denied"
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
                        # Direct SQL query
                        sql_query = message
                        explanation = "Direct SQL query execution"
                        if multi_db_mode and databases:
                            explanation = f"Executing query across {len(databases)} databases"
                    else:
                        # Translate natural language to SQL
                        result = await self.sql_translator.translate_to_sql(
                            message,
                            database=database,
                            schema_context=await self._get_schema_context(database)
                        )
                        
                        if result.error or not result.query:
                            return json_response({
                                'status': 'error',
                                'error': result.error or 'Could not translate to SQL query'
                            })
                        
                        sql_query = result.query
                        explanation = result.explanation
                        if multi_db_mode and databases:
                            explanation = f"{explanation} (across {len(databases)} databases)"
                    
                    # Execute the query
                    if multi_db_mode and databases:
                        # Multi-database execution
                        multi_results = await self._execute_multi_db_query(sql_query, databases)
                        
                        # Count total results
                        total_rows = sum(r.get('row_count', 0) for r in multi_results)
                        total_time = sum(r.get('execution_time_ms', 0) for r in multi_results)
                        
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
                        # Single database execution
                        execution_result = await self._execute_sql_query(sql_query, database)
                        
                        if execution_result.get('error'):
                            return json_response({
                                'status': 'error',
                                'error': execution_result['error']
                            })
                        
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
                    logger.error(f"Error processing query: {e}", exc_info=True)
                    return json_response({
                        'status': 'error',
                        'error': f'Query processing error: {str(e)}'
                    })
            else:
                return json_response({
                    'status': 'error',
                    'error': 'SQL translator not available. Please check Azure OpenAI configuration.'
                })
                
        except Exception as e:
            logger.error(f"Console message error: {e}", exc_info=True)
            return json_response({
                'status': 'error',
                'error': str(e)
            })
    
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

**Multi-Database Queries (NEW!):**
• Toggle "Multi-Database Query" mode in the sidebar
• Select multiple databases using checkboxes
• Run the same query across all selected databases
• Results are grouped by database

**Tips:**
• Click on a database to switch context
• Click on a table name to create a SELECT query
• Use natural language or SQL syntax
• Results are limited to prevent overload
• In multi-database mode, ensure your query works for all selected databases"""
    
    async def _get_databases(self) -> List[str]:
        """Get list of databases"""
        try:
            if not self.function_url:
                logger.warning("Azure Function URL not configured")
                return ['master']
            
            # Call Azure Function with proper auth
            result = await self._call_function({
                "query_type": "metadata"
            })
            
            if result and 'databases' in result:
                return result['databases']
            else:
                return ['master']
                
        except Exception as e:
            logger.error(f"Error getting databases: {e}")
            return ['master']
    
    async def _get_tables(self, database: str) -> List[str]:
        """Get list of tables in database"""
        try:
            if not self.function_url:
                return []
            
            # Execute query to get tables
            query = """
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE' 
            ORDER BY TABLE_NAME
            """
            
            result = await self._execute_sql_query(query, database)
            
            if result.get('rows'):
                return [row['TABLE_NAME'] for row in result['rows']]
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting tables: {e}")
            return []
    
    async def _get_schema_context(self, database: str) -> str:
        """Get schema context for translation"""
        try:
            tables = await self._get_tables(database)
            if tables:
                return f"Available tables: {', '.join(tables[:10])}"
            return ""
        except:
            return ""
    
    async def _call_function(self, payload: Dict[str, Any]) -> Optional[Dict]:
        """Call Azure Function with proper authentication"""
        try:
            headers = {"Content-Type": "application/json"}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.function_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Function call failed: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error calling function: {e}")
            return None
    
    async def _execute_sql_query(self, query: str, database: str) -> Dict[str, Any]:
        """Execute SQL query using Azure Function"""
        if not self.function_url:
            return {'error': 'Azure Function URL not configured'}
        
        try:
            payload = {
                "query_type": "single",
                "query": query,
                "database": database,
                "output_format": "raw"
            }
            
            result = await self._call_function(payload)
            
            if result:
                if 'error' in result:
                    return {'error': result['error']}
                return {
                    'rows': result.get('rows', []),
                    'row_count': result.get('row_count', 0),
                    'execution_time_ms': result.get('execution_time_ms', 0)
                }
            else:
                return {'error': 'Failed to execute query'}
                
        except Exception as e:
            logger.error(f"Error executing query: {e}", exc_info=True)
            return {'error': f'Query execution error: {str(e)}'}
    
    async def _execute_multi_db_query(self, query: str, databases: List[str]) -> List[Dict[str, Any]]:
        """Execute SQL query across multiple databases"""
        if not self.function_url:
            return [{'database': db, 'error': 'Azure Function URL not configured'} for db in databases]
        
        try:
            payload = {
                "query_type": "multi_database",
                "query": query,
                "databases": databases,
                "output_format": "raw"
            }
            
            result = await self._call_function(payload)
            
            if result and isinstance(result, list):
                # Format results for frontend
                formatted_results = []
                for db_result in result:
                    formatted_results.append({
                        'database': db_result.get('database', 'Unknown'),
                        'rows': db_result.get('rows', []),
                        'row_count': db_result.get('row_count', 0),
                        'execution_time': db_result.get('execution_time_ms', 0),
                        'error': db_result.get('error')
                    })
                return formatted_results
            else:
                # Return error for each database
                return [{
                    'database': db,
                    'error': 'Failed to execute multi-database query',
                    'rows': [],
                    'row_count': 0,
                    'execution_time': 0
                } for db in databases]
                
        except Exception as e:
            logger.error(f"Error executing multi-database query: {e}", exc_info=True)
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
            databases = await self._get_databases()
            return json_response({
                'status': 'success',
                'databases': databases
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
            tables = await self._get_tables(database)
            return json_response({
                'status': 'success',
                'tables': tables
            })
        except Exception as e:
            logger.error(f"Tables API error: {e}", exc_info=True)
            return json_response({
                'status': 'error',
                'error': str(e)
            })
    
    async def get_current_user_api(self, request: Request) -> Response:
        """API endpoint to get current user information"""
        try:
            # Check if user info is in request headers (from Azure App Service authentication)
            user_info = {
                'name': None,
                'email': None,
                'auth_type': 'Microsoft',
                'sql_user': None
            }
            
            # Azure App Service puts authenticated user info in headers
            # Check various possible header names
            headers_to_check = {
                'X-MS-CLIENT-PRINCIPAL-NAME': 'email',
                'X-MS-CLIENT-PRINCIPAL': 'principal',
                'X-MS-CLIENT-PRINCIPAL-ID': 'id',
                'X-MS-TOKEN-AAD-ID-TOKEN': 'aad_token'
            }
            
            for header, field in headers_to_check.items():
                value = request.headers.get(header)
                if value:
                    if field == 'email':
                        user_info['email'] = value
                        user_info['name'] = value.split('@')[0]  # Use email prefix as name
                    logger.info(f"Found {field}: {value[:20]}...")
            
            # Try to get SQL user from the database
            try:
                if self.function_url:
                    # Query to get current SQL user
                    sql_result = await self._execute_sql_query(
                        "SELECT SUSER_NAME() as LoginName, USER_NAME() as UserName, SYSTEM_USER as SystemUser",
                        "master"
                    )
                    
                    if sql_result.get('rows') and len(sql_result['rows']) > 0:
                        sql_user_info = sql_result['rows'][0]
                        user_info['sql_user'] = sql_user_info.get('LoginName', 'Unknown')
                        
                        # If no email/name from headers, try to extract from SQL login
                        if not user_info['email'] and '@' in str(sql_user_info.get('LoginName', '')):
                            user_info['email'] = sql_user_info['LoginName']
                            user_info['name'] = sql_user_info['LoginName'].split('@')[0]
            except Exception as e:
                logger.warning(f"Could not get SQL user info: {e}")
            
            # Default values if nothing found
            if not user_info['name'] and not user_info['email']:
                user_info['name'] = 'Guest User'
                user_info['auth_type'] = 'None'
            
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
    
    logger.info("SQL Console routes added successfully with multi-database support")
    return console