# sql_console_routes.py - Enhanced SQL Console Routes with Multi-DB Support
"""
SQL Console Routes - Fixed table loading query
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from aiohttp import web
from aiohttp.web import Request, Response, json_response
import aiohttp
import asyncio

# Import UI components
from sql_console_html import get_sql_console_html

logger = logging.getLogger(__name__)

class SQLConsole:
    """Enhanced SQL Console with multi-database support and result analysis"""
    
    def __init__(self, sql_translator=None):
        self.sql_translator = sql_translator
        self.function_url = os.environ.get("AZURE_FUNCTION_URL", "")
        self.sessions = {}
        self.active_requests = {}
        self.database_cache = {}
        self.cache_timeout = 300  # 5 minutes
        
        # Check if authentication is embedded in URL
        self.url_has_auth = "code=" in self.function_url
        
        logger.info(f"SQL Console initialized with enhanced features")
        logger.info(f"Function URL configured: {'Yes' if self.function_url else 'No'}")
        logger.info(f"SQL Translator available: {'Yes' if sql_translator else 'No'}")
    
    async def console_page(self, request: Request) -> Response:
        """Serve the SQL console HTML page"""
        html_content = get_sql_console_html()
        return Response(text=html_content, content_type='text/html')
    
    async def get_tables_api(self, request: Request) -> Response:
        """API endpoint to get tables - FIXED query format"""
        try:
            database = request.query.get('database', 'demo')
            session_id = request.query.get('session_id', 'api')
            
            logger.info(f"Getting tables for database: {database}")
            
            # FIXED: Use simpler query format that works better
            # Try multiple approaches to ensure we get tables
            queries_to_try = [
                # Method 1: Direct sp_tables call
                "sp_tables",
                # Method 2: INFORMATION_SCHEMA query
                """SELECT TABLE_SCHEMA + '.' + TABLE_NAME as TABLE_NAME 
                   FROM INFORMATION_SCHEMA.TABLES 
                   WHERE TABLE_TYPE = 'BASE TABLE' 
                   ORDER BY TABLE_SCHEMA, TABLE_NAME""",
                # Method 3: sys tables query
                """SELECT s.name + '.' + t.name as TABLE_NAME
                   FROM sys.tables t
                   JOIN sys.schemas s ON t.schema_id = s.schema_id
                   WHERE t.type = 'U'
                   ORDER BY s.name, t.name"""
            ]
            
            for query_idx, query in enumerate(queries_to_try):
                logger.info(f"Trying query method {query_idx + 1}: {query[:50]}...")
                
                result = await self._execute_sql_query_with_logging(query, database, session_id)
                
                if result.get('rows'):
                    tables = []
                    
                    # Handle different result formats
                    for row in result['rows']:
                        # sp_tables format
                        if 'TABLE_NAME' in row and row.get('TABLE_TYPE') == 'TABLE':
                            table_name = row['TABLE_NAME']
                            owner = row.get('TABLE_OWNER', 'dbo')
                            qualifier = row.get('TABLE_QUALIFIER')
                            
                            # Build full table name
                            if owner and owner != 'dbo':
                                tables.append(f"{owner}.{table_name}")
                            else:
                                tables.append(table_name)
                        
                        # INFORMATION_SCHEMA or sys.tables format
                        elif 'TABLE_NAME' in row and 'TABLE_TYPE' not in row:
                            tables.append(row['TABLE_NAME'])
                    
                    if tables:
                        logger.info(f"Found {len(tables)} tables using method {query_idx + 1}")
                        
                        return json_response({
                            'status': 'success',
                            'tables': sorted(list(set(tables))),  # Remove duplicates and sort
                            'database': database,
                            'method': f'query_method_{query_idx + 1}'
                        })
                
                # If we get an error with sp_tables, try next method
                if result.get('error'):
                    logger.warning(f"Method {query_idx + 1} failed: {result['error']}")
                    continue
            
            # If all methods fail, return empty list
            logger.warning(f"No tables found in {database} after trying all methods")
            return json_response({
                'status': 'success',
                'tables': [],
                'database': database,
                'note': 'No tables found or access denied'
            })
                
        except Exception as e:
            logger.error(f"Tables API error: {e}", exc_info=True)
            return json_response({
                'status': 'error',
                'error': str(e)
            })
    
    async def handle_message(self, request: Request) -> Response:
        """Handle incoming console messages with enhanced multi-database support"""
        request_id = datetime.now().strftime("%H%M%S%f")[:10]
        
        try:
            data = await request.json()
            message = data.get('message', '').strip()
            database = data.get('database', 'demo')  # Default to demo instead of master
            session_id = data.get('session_id')
            multi_db_mode = data.get('multi_db_mode', False)
            databases = data.get('databases', [])
            
            # Store request for potential cancellation
            self.active_requests[session_id] = request_id
            
            logger.info(f"[{request_id}] Console message: {message[:50]}...")
            
            # Send initial acknowledgment
            await self._send_log_message(session_id, f"🔍 Processing: {message}", "info")
            
            if multi_db_mode and databases:
                await self._send_log_message(session_id, f"📊 Multi-database mode: {len(databases)} databases selected", "info")
            
            # Check for special commands
            if message.lower() in ['help', '?']:
                return json_response({
                    'status': 'success',
                    'response_type': 'help',
                    'content': self._get_enhanced_help_text()
                })
            
            # Handle schema comparison commands
            if message.lower().startswith('compare schemas'):
                return await self._handle_schema_comparison(message, databases, session_id)
            
            # Handle standardization check commands
            if message.lower().startswith('check standardization'):
                return await self._handle_standardization_check(message, databases, session_id)
            
            # Determine if it's SQL or natural language
            is_sql = self._is_sql_query(message)
            
            if is_sql:
                await self._send_log_message(session_id, "✅ Detected direct SQL query", "info")
                sql_query = message
                explanation = "Direct SQL query execution"
            else:
                # Natural language - needs translation
                if not self.sql_translator:
                    return json_response({
                        'status': 'error',
                        'error': 'SQL translator not available. Please check Azure OpenAI configuration.'
                    })
                
                await self._send_log_message(session_id, "🤖 Translating natural language to SQL...", "info")
                
                # Enhanced translation with schema context
                schema_context = await self._get_enhanced_schema_context(database, databases if multi_db_mode else None)
                
                result = await self.sql_translator.translate_to_sql(
                    message,
                    database=database,
                    schema_context=schema_context
                )
                
                if result.error or not result.query:
                    return json_response({
                        'status': 'error',
                        'error': result.error or 'Could not translate to SQL query'
                    })
                
                sql_query = result.query
                explanation = result.explanation
                await self._send_log_message(session_id, f"✅ Translated to SQL: {sql_query[:100]}...", "success")
            
            # Execute the query with enhanced multi-database support
            if multi_db_mode and databases:
                # Check if query needs intelligent splitting
                if await self._should_split_query(sql_query, len(databases)):
                    await self._send_log_message(session_id, "🔄 Using intelligent query splitting for better performance", "info")
                    results = await self._execute_split_queries(sql_query, databases, session_id)
                else:
                    results = await self._execute_multi_db_query_enhanced(sql_query, databases, session_id)
                
                # Analyze results if AI analysis is requested
                analysis_requested = data.get('analyze_results', True)
                if analysis_requested and self.sql_translator:
                    await self._send_log_message(session_id, "🤖 Analyzing results...", "info")
                    analysis = await self._analyze_multi_db_results(results, sql_query, message)
                    
                    return json_response({
                        'status': 'success',
                        'response_type': 'analyzed_result',
                        'sql_query': sql_query,
                        'explanation': explanation,
                        'multi_db_results': results,
                        'analysis': analysis
                    })
                else:
                    return json_response({
                        'status': 'success',
                        'response_type': 'sql_result',
                        'sql_query': sql_query,
                        'explanation': explanation,
                        'multi_db_results': results
                    })
            else:
                # Single database query
                execution_result = await self._execute_sql_query_with_logging(sql_query, database, session_id)
                
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
                    'execution_time': execution_result.get('execution_time_ms', 0)
                })
                
        except Exception as e:
            logger.error(f"[{request_id}] Console message error: {e}", exc_info=True)
            return json_response({
                'status': 'error',
                'error': str(e)
            })
        finally:
            if session_id in self.active_requests:
                del self.active_requests[session_id]
    
    async def _should_split_query(self, query: str, database_count: int) -> bool:
        """Determine if query should be split for better performance"""
        query_lower = query.lower()
        
        # Complex queries that benefit from splitting
        if database_count > 3:
            if any(x in query_lower for x in ['join', 'group by', 'order by', 'union']):
                return True
        
        return False
    
    async def _execute_split_queries(self, query: str, databases: List[str], session_id: str) -> List[Dict]:
        """Execute queries in a more efficient split manner"""
        # This is a simplified implementation - in production, you'd want more sophisticated query analysis
        results = []
        
        # For now, just execute in parallel with smaller batches
        batch_size = 3
        for i in range(0, len(databases), batch_size):
            batch = databases[i:i+batch_size]
            batch_results = await self._execute_multi_db_query_enhanced(query, batch, session_id)
            results.extend(batch_results)
        
        return results
    
    async def _handle_schema_comparison(self, message: str, databases: List[str], session_id: str) -> Response:
        """Handle schema comparison requests"""
        await self._send_log_message(session_id, "📊 Performing schema comparison...", "info")
        
        # Extract table name from message
        parts = message.lower().split()
        table_name = parts[-1] if len(parts) > 2 else None
        
        if not table_name or not databases or len(databases) < 2:
            return json_response({
                'status': 'error',
                'error': 'Please specify a table name and select at least 2 databases for comparison'
            })
        
        # Query to get column information
        query = f"""
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE,
            COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{table_name}'
        ORDER BY ORDINAL_POSITION
        """
        
        # Execute across selected databases
        results = await self._execute_multi_db_query_enhanced(query, databases, session_id, output_format='comparison')
        
        return json_response({
            'status': 'success',
            'response_type': 'schema_comparison',
            'table_name': table_name,
            'comparison': results
        })
    
    async def _handle_standardization_check(self, message: str, databases: List[str], session_id: str) -> Response:
        """Handle database standardization checks"""
        await self._send_log_message(session_id, "🔍 Checking database standardization...", "info")
        
        # Query to check view schemas
        query = """
        SELECT 
            s.name as SchemaName,
            COUNT(DISTINCT v.name) as ViewCount
        FROM sys.schemas s
        JOIN sys.views v ON s.schema_id = v.schema_id
        WHERE s.name IN ('acc', 'inv', 'hr', 'crm')
        GROUP BY s.name
        ORDER BY s.name
        """
        
        results = await self._execute_multi_db_query_enhanced(query, databases, session_id)
        
        # Analyze standardization
        analysis = {
            'standardized_schemas': ['acc', 'inv', 'hr', 'crm'],
            'database_compliance': []
        }
        
        for result in results:
            if not result.get('error'):
                schemas_found = [row['SchemaName'] for row in result.get('rows', [])]
                analysis['database_compliance'].append({
                    'database': result['database'],
                    'schemas_found': schemas_found,
                    'compliance_score': len(schemas_found) / len(analysis['standardized_schemas'])
                })
        
        return json_response({
            'status': 'success',
            'response_type': 'standardization_check',
            'analysis': analysis,
            'raw_results': results
        })
    
    async def _analyze_multi_db_results(self, results: List[Dict], query: str, original_question: str) -> Dict:
        """Use AI to analyze multi-database results"""
        if not self.sql_translator:
            return {"error": "AI analysis not available"}
        
        # Prepare summary for AI
        summary = {
            'query': query,
            'question': original_question,
            'database_count': len(results),
            'results_summary': []
        }
        
        for result in results:
            if result.get('error'):
                summary['results_summary'].append({
                    'database': result['database'],
                    'status': 'error',
                    'error': result['error']
                })
            else:
                summary['results_summary'].append({
                    'database': result['database'],
                    'status': 'success',
                    'row_count': result.get('row_count', 0),
                    'sample_data': result.get('rows', [])[:3]  # First 3 rows
                })
        
        # Use the SQL translator's explain_results method
        analysis_text = await self.sql_translator.explain_results(
            query, 
            results, 
            original_question,
            formatted_result={'summary': summary}
        )
        
        return {
            'analysis_text': analysis_text,
            'summary': summary
        }
    
    async def _execute_multi_db_query_enhanced(self, query: str, databases: List[str], session_id: str, output_format: str = 'raw') -> List[Dict]:
        """Execute query across multiple databases with enhanced formatting"""
        if not self.function_url:
            return [{'database': db, 'error': 'Azure Function URL not configured'} for db in databases]
        
        try:
            payload = {
                "query_type": "multi_database",
                "query": query,
                "databases": databases,
                "output_format": output_format
            }
            
            await self._send_log_message(session_id, f"📤 Executing across {len(databases)} databases", "info")
            
            result = await self._call_function_with_logging(payload, session_id)
            
            if result:
                if output_format == 'comparison' and 'comparison' in result:
                    return result['comparison']
                elif isinstance(result, list):
                    return result
                else:
                    return [{'error': 'Invalid response format'}]
            else:
                return [{'database': db, 'error': 'No response from function'} for db in databases]
                
        except Exception as e:
            logger.error(f"Error executing multi-database query: {e}")
            return [{'database': db, 'error': str(e)} for db in databases]
    
    async def _get_enhanced_schema_context(self, database: str, additional_databases: Optional[List[str]] = None) -> str:
        """Get enhanced schema context for translation"""
        context_parts = [f"Primary database: {database}"]
        
        if additional_databases:
            context_parts.append(f"Additional databases: {', '.join(additional_databases)}")
        
        # Add standardization context
        context_parts.append("Standard schemas: acc (accounting), inv (inventory), hr (human resources), crm (customer relations)")
        
        return "\n".join(context_parts)
    
    def _get_enhanced_help_text(self) -> str:
        """Get enhanced help text with new features"""
        return """SQL Assistant Console - Enhanced Features:

**Natural Language Queries:**
- "Show me all customers"
- "Compare columns in AD table across all databases"
- "Check standardization of accounting views"
- "Find differences in table structure between systems"

**Multi-Database Features:**
- Toggle "Multi-Database Query" mode in sidebar
- Select databases for comparison
- Automatic result analysis and formatting
- Intelligent query splitting for performance

**Standardization Commands:**
- "compare schemas [table]" - Compare table structure across databases
- "check standardization" - Verify schema compliance
- "show [schema] views" - List views in specific schema (acc, inv, hr, crm)

**SQL Commands:**
- SELECT, WITH, and other read queries
- System procedures (sp_tables, sp_columns, etc.)
- Direct SQL syntax with T-SQL support

**Available Databases:**
- _support - Support database
- demo - Demo database with standardized schemas
- Additional databases discovered dynamically

**Schema Standards:**
- acc - Accounting (financial data)
- inv - Inventory management
- hr - Human resources
- crm - Customer relationship management

**Tips:**
- Results are automatically analyzed for insights
- Use multi-database mode for standardization checks
- Copy conversation logs with the copy button
- The console shows processing steps in real-time"""
    
    async def get_databases_api(self, request: Request) -> Response:
        """API endpoint to get databases (excluding master)"""
        try:
            session_id = request.query.get('session_id', 'api')
            force_refresh = request.query.get('force_refresh', '').lower() == 'true'
            
            # Get databases from Azure Function
            payload = {
                "query_type": "metadata",
                "force_refresh": force_refresh
            }
            
            result = await self._call_function_with_logging(payload, session_id)
            
            if result and 'databases' in result:
                # Filter out excluded databases (master is excluded in the function now)
                databases = result['databases']
                
                return json_response({
                    'status': 'success',
                    'databases': databases,
                    'msi_identity': result.get('msi_identity', 'Unknown'),
                    'note': 'Showing user-accessible databases only'
                })
            else:
                # Fallback list without master
                return json_response({
                    'status': 'success',
                    'databases': ['_support', 'demo'],
                    'note': 'Using fallback database list'
                })
                
        except Exception as e:
            logger.error(f"Database API error: {e}")
            return json_response({
                'status': 'error',
                'error': str(e)
            })
    
    async def export_logs_api(self, request: Request) -> Response:
        """API endpoint to export conversation logs"""
        try:
            data = await request.json()
            logs = data.get('logs', [])
            format_type = data.get('format', 'text')
            
            if format_type == 'json':
                content = json.dumps(logs, indent=2)
                content_type = 'application/json'
                filename = f'sql_console_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            else:
                # Text format
                lines = []
                for log in logs:
                    timestamp = log.get('timestamp', '')
                    level = log.get('type', 'info').upper()
                    message = log.get('message', '')
                    lines.append(f"[{timestamp}] {level}: {message}")
                
                content = '\n'.join(lines)
                content_type = 'text/plain'
                filename = f'sql_console_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
            
            return Response(
                text=content,
                content_type=content_type,
                headers={
                    'Content-Disposition': f'attachment; filename="{filename}"'
                }
            )
            
        except Exception as e:
            logger.error(f"Export logs error: {e}")
            return json_response({
                'status': 'error',
                'error': str(e)
            })
    
    # Include other helper methods from original file
    async def _send_log_message(self, session_id: str, message: str, level: str = "info"):
        """Send a log message to the client"""
        logger.info(f"[Console-{session_id}] {level.upper()}: {message}")
    
    def _is_sql_query(self, message: str) -> bool:
        """Check if message is a SQL query"""
        sql_keywords = ['select', 'with', 'exec', 'execute', 'sp_']
        message_lower = message.lower().strip()
        
        for keyword in sql_keywords:
            if message_lower.startswith(keyword):
                return True
        
        sql_patterns = ['from ', 'where ', 'join ', 'group by', 'order by']
        if any(pattern in message_lower for pattern in sql_patterns):
            return True
        
        return False
    
    async def _call_function_with_logging(self, payload: Dict[str, Any], session_id: str) -> Optional[Dict]:
        """Call Azure Function with logging"""
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
            
            result = await self._call_function_with_logging(payload, session_id)
            
            if result:
                return result
            else:
                return {'error': 'No response from function'}
                
        except Exception as e:
            return {'error': str(e)}
    
    async def cancel_request_api(self, request: Request) -> Response:
        """API endpoint to cancel active request"""
        try:
            data = await request.json()
            session_id = data.get('session_id')
            
            if session_id in self.active_requests:
                del self.active_requests[session_id]
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
            return json_response({
                'status': 'error',
                'error': str(e)
            })
    
    async def get_current_user_api(self, request: Request) -> Response:
        """API endpoint to get current user information"""
        try:
            user_info = {
                'name': 'SQL User',
                'email': None,
                'auth_type': 'Managed Service Identity',
                'sql_user': 'Function App MSI'
            }
            
            # Check for Azure App Service headers
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
            
            return json_response({
                'status': 'success',
                'user': user_info
            })
            
        except Exception as e:
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
    app.router.add_post('/console/api/export-logs', console.export_logs_api)
    
    logger.info("Enhanced SQL Console routes added successfully")
    return console