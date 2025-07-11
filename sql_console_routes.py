# sql_console_routes.py - SQL Console Routes and Logic
"""
SQL Console Routes - Updated with better database handling and debugging
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
    """SQL Console handler with proper authentication and debugging"""
    
    def __init__(self, sql_translator=None):
        self.sql_translator = sql_translator
        self.function_url = os.environ.get("AZURE_FUNCTION_URL", "")
        self.sessions = {}
        
        # Check if authentication is embedded in URL
        self.url_has_auth = "code=" in self.function_url
        
        # List of accessible databases from the MSI check
        self.accessible_databases = ['master', '_support', 'demo']
        
        logger.info(f"SQL Console initialized")
        logger.info(f"Function URL configured: {'Yes' if self.function_url else 'No'}")
        logger.info(f"Authentication method: {'URL-embedded' if self.url_has_auth else 'Header-based'}")
        logger.info(f"SQL Translator available: {'Yes' if sql_translator else 'No'}")
        logger.info(f"Accessible databases: {', '.join(self.accessible_databases)}")
    
    async def console_page(self, request: Request) -> Response:
        """Serve the SQL console HTML page"""
        # Use the updated HTML
        with open('sql_console_html_updated.html', 'r') as f:
            html_content = f.read()
        return Response(text=html_content, content_type='text/html')
    
    async def handle_message(self, request: Request) -> Response:
        """Handle incoming console messages with enhanced debugging"""
        try:
            data = await request.json()
            message = data.get('message', '').strip()
            database = data.get('database', 'master')
            session_id = data.get('session_id')
            
            logger.info(f"[Console] Message: '{message}' | Database: '{database}' | Session: {session_id}")
            
            # Ensure database is accessible
            if database not in self.accessible_databases:
                logger.warning(f"[Console] Database '{database}' not accessible, defaulting to 'master'")
                database = 'master'
            
            # Check for special SQL Server system procedures
            if message.lower() == 'sp_databases':
                return await self._handle_sp_databases()
            
            if message.lower() == 'sp_tables':
                return await self._handle_sp_tables(database)
            
            # Check for other special commands
            if message.lower() in ['help', '?']:
                return json_response({
                    'status': 'success',
                    'response_type': 'help',
                    'content': self._get_help_text()
                })
            
            if message.lower() in ['show databases', 'databases']:
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
                        logger.info(f"[Console] Executing direct SQL: {sql_query[:100]}...")
                    else:
                        # Translate natural language to SQL
                        logger.info(f"[Console] Translating natural language to SQL")
                        result = await self.sql_translator.translate_to_sql(
                            message,
                            database=database,
                            schema_context=await self._get_schema_context(database)
                        )
                        
                        if result.error or not result.query:
                            logger.error(f"[Console] Translation failed: {result.error}")
                            return json_response({
                                'status': 'error',
                                'error': result.error or 'Could not translate to SQL query'
                            })
                        
                        sql_query = result.query
                        explanation = result.explanation
                        logger.info(f"[Console] Translated to SQL: {sql_query[:100]}...")
                    
                    # Execute the query
                    execution_result = await self._execute_sql_query(sql_query, database)
                    
                    if execution_result.get('error'):
                        logger.error(f"[Console] Execution error: {execution_result['error']}")
                        return json_response({
                            'status': 'error',
                            'error': execution_result['error']
                        })
                    
                    logger.info(f"[Console] Query successful: {execution_result.get('row_count', 0)} rows")
                    
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
                    logger.error(f"[Console] Error processing query: {e}", exc_info=True)
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
            logger.error(f"[Console] Message handler error: {e}", exc_info=True)
            return json_response({
                'status': 'error',
                'error': str(e)
            })
    
    async def _handle_sp_databases(self) -> Response:
        """Handle sp_databases system procedure"""
        logger.info("[Console] Executing sp_databases")
        
        try:
            # Get databases from the function
            databases = await self._get_databases()
            
            # Return in a format similar to sp_databases
            return json_response({
                'status': 'success',
                'response_type': 'text',
                'content': f"Available databases:\n" + "\n".join(f"• {db}" for db in databases),
                'refresh_databases': True
            })
            
        except Exception as e:
            logger.error(f"[Console] sp_databases error: {e}")
            return json_response({
                'status': 'error',
                'error': f'Error listing databases: {str(e)}'
            })
    
    async def _handle_sp_tables(self, database: str) -> Response:
        """Handle sp_tables system procedure"""
        logger.info(f"[Console] Executing sp_tables for database: {database}")
        
        try:
            # Execute sp_tables query
            query = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME"
            
            result = await self._execute_sql_query(query, database)
            
            if result.get('error'):
                # If failed, try alternative query
                query = "SELECT name FROM sys.tables ORDER BY name"
                result = await self._execute_sql_query(query, database)
            
            if result.get('rows'):
                tables = [row.get('TABLE_NAME') or row.get('name') for row in result['rows']]
                content = f"Tables in {database}:\n" + "\n".join(f"• {table}" for table in tables)
            else:
                content = f"No tables found in {database}"
            
            return json_response({
                'status': 'success',
                'response_type': 'text',
                'content': content,
                'refresh_tables': True
            })
            
        except Exception as e:
            logger.error(f"[Console] sp_tables error: {e}")
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
• show databases - List all databases
• show tables - List tables in current database

**Current Access:**
• Databases: master, _support, demo
• Use the sidebar to switch databases
• Click on a table name to create a SELECT query

**Tips:**
• Results are limited to prevent overload
• Use natural language or SQL syntax
• Check the debug panel (🐛) for details"""
    
    async def _get_databases(self) -> List[str]:
        """Get list of databases"""
        try:
            if not self.function_url:
                logger.warning("[Console] Azure Function URL not configured")
                return self.accessible_databases
            
            logger.info("[Console] Fetching databases from Azure Function")
            
            # Call Azure Function with proper auth
            result = await self._call_function({
                "query_type": "metadata"
            })
            
            if result and 'databases' in result:
                databases = result['databases']
                logger.info(f"[Console] Retrieved {len(databases)} databases from function")
                
                # Update accessible databases cache
                self.accessible_databases = databases
                return databases
            else:
                logger.warning("[Console] No databases returned from function, using cache")
                return self.accessible_databases
                
        except Exception as e:
            logger.error(f"[Console] Error getting databases: {e}")
            return self.accessible_databases
    
    async def _get_tables(self, database: str) -> List[str]:
        """Get list of tables in database"""
        try:
            if not self.function_url:
                return []
            
            logger.info(f"[Console] Fetching tables for database: {database}")
            
            # Execute query to get tables
            query = """
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE' 
            ORDER BY TABLE_NAME
            """
            
            result = await self._execute_sql_query(query, database)
            
            if result.get('error'):
                # Try alternative query
                logger.info("[Console] First query failed, trying sys.tables")
                query = "SELECT name AS TABLE_NAME FROM sys.tables ORDER BY name"
                result = await self._execute_sql_query(query, database)
            
            if result.get('rows'):
                tables = [row['TABLE_NAME'] for row in result['rows'] if 'TABLE_NAME' in row]
                logger.info(f"[Console] Found {len(tables)} tables")
                return tables
            else:
                logger.warning(f"[Console] No tables found in {database}")
                return []
                
        except Exception as e:
            logger.error(f"[Console] Error getting tables: {e}")
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
    
    async def _call_function(self, payload: Dict[str, Any]) -> Optional[Dict]:
        """Call Azure Function with proper authentication"""
        try:
            headers = {"Content-Type": "application/json"}
            
            logger.info(f"[Console] Calling Azure Function: {self.function_url[:50]}...")
            logger.info(f"[Console] Payload: {json.dumps(payload)}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.function_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_text = await response.text()
                    logger.info(f"[Console] Function response status: {response.status}")
                    
                    if response.status == 200:
                        result = json.loads(response_text)
                        logger.info(f"[Console] Function response: {json.dumps(result)[:200]}...")
                        return result
                    else:
                        logger.error(f"[Console] Function call failed: {response.status} - {response_text[:200]}")
                        return None
                        
        except Exception as e:
            logger.error(f"[Console] Error calling function: {e}")
            return None
    
    async def _execute_sql_query(self, query: str, database: str) -> Dict[str, Any]:
        """Execute SQL query using Azure Function"""
        if not self.function_url:
            return {'error': 'Azure Function URL not configured'}
        
        try:
            logger.info(f"[Console] Executing SQL query on {database}: {query[:100]}...")
            
            payload = {
                "query_type": "single",
                "query": query,
                "database": database,
                "output_format": "raw"
            }
            
            result = await self._call_function(payload)
            
            if result:
                if 'error' in result:
                    logger.error(f"[Console] Query execution error: {result['error']}")
                    return {'error': result['error']}
                
                logger.info(f"[Console] Query executed successfully: {result.get('row_count', 0)} rows")
                return {
                    'rows': result.get('rows', []),
                    'row_count': result.get('row_count', 0),
                    'execution_time_ms': result.get('execution_time_ms', 0)
                }
            else:
                return {'error': 'Failed to execute query'}
                
        except Exception as e:
            logger.error(f"[Console] Error executing query: {e}", exc_info=True)
            return {'error': f'Query execution error: {str(e)}'}
    
    async def get_databases_api(self, request: Request) -> Response:
        """API endpoint to get databases"""
        try:
            logger.info("[Console API] Getting databases")
            databases = await self._get_databases()
            return json_response({
                'status': 'success',
                'databases': databases
            })
        except Exception as e:
            logger.error(f"[Console API] Database API error: {e}", exc_info=True)
            return json_response({
                'status': 'error',
                'error': str(e)
            })
    
    async def get_tables_api(self, request: Request) -> Response:
        """API endpoint to get tables"""
        try:
            database = request.query.get('database', 'master')
            logger.info(f"[Console API] Getting tables for database: {database}")
            
            tables = await self._get_tables(database)
            return json_response({
                'status': 'success',
                'tables': tables
            })
        except Exception as e:
            logger.error(f"[Console API] Tables API error: {e}", exc_info=True)
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
    
    logger.info("SQL Console routes added successfully")
    return console