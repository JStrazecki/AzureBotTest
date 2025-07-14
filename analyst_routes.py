# analyst_routes.py - Power BI Analyst Routes and API Endpoints
"""
Power BI Analyst Routes - Handles the /analyst endpoint and related API calls
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

# Import components
from powerbi_client import powerbi_client, WorkspaceInfo, DatasetInfo, QueryResult
from analyst_translator import analyst_translator, DAXQuery, TranslationContext
from analysis_agent import analysis_agent, AnalysisContext, InsightResult

# Import UI
from analyst_ui import get_analyst_html

logger = logging.getLogger(__name__)

class PowerBIAnalyst:
    """Power BI Analyst endpoint handler"""
    
    def __init__(self):
        self.powerbi_client = powerbi_client
        self.translator = analyst_translator
        self.analysis_agent = analysis_agent
        
        # Cache for workspace and dataset information
        self.workspace_cache = {}
        self.dataset_cache = {}
        self.cache_duration = 300  # 5 minutes
        
        # Active sessions
        self.sessions = {}
        
        logger.info("Power BI Analyst initialized")
        logger.info(f"Power BI configured: {self.powerbi_client.is_configured()}")
    
    async def analyst_page(self, request: Request) -> Response:
        """Serve the analyst HTML page"""
        html_content = get_analyst_html()
        return Response(text=html_content, content_type='text/html')
    
    async def check_configuration(self, request: Request) -> Response:
        """API endpoint to check Power BI configuration"""
        try:
            validation = await self.powerbi_client.validate_configuration()
            
            return json_response({
                "status": "success",
                "configured": validation["configured"],
                "validation": validation
            })
            
        except Exception as e:
            logger.error(f"Configuration check error: {e}")
            return json_response({
                "status": "error",
                "error": str(e)
            })
    
    async def get_workspaces(self, request: Request) -> Response:
        """API endpoint to get user's Power BI workspaces"""
        try:
            # Get access token
            token = await self.powerbi_client.get_access_token()
            if not token:
                return json_response({
                    "status": "error",
                    "error": "Failed to authenticate with Power BI"
                })
            
            # Check cache
            cache_key = "workspaces"
            if cache_key in self.workspace_cache:
                cached_data = self.workspace_cache[cache_key]
                if cached_data["expires"] > datetime.now():
                    logger.info("Returning cached workspaces")
                    return json_response({
                        "status": "success",
                        "workspaces": cached_data["data"]
                    })
            
            # Get workspaces
            workspaces = await self.powerbi_client.get_user_workspaces(token)
            
            # Convert to serializable format
            workspace_list = [
                {
                    "id": ws.id,
                    "name": ws.name,
                    "description": ws.description,
                    "is_personal": ws.is_personal
                }
                for ws in workspaces
            ]
            
            # Cache the results
            self.workspace_cache[cache_key] = {
                "data": workspace_list,
                "expires": datetime.now().timestamp() + self.cache_duration
            }
            
            return json_response({
                "status": "success",
                "workspaces": workspace_list
            })
            
        except Exception as e:
            logger.error(f"Error getting workspaces: {e}")
            return json_response({
                "status": "error",
                "error": str(e)
            })
    
    async def get_datasets(self, request: Request) -> Response:
        """API endpoint to get datasets in a workspace"""
        try:
            workspace_id = request.query.get('workspace_id')
            workspace_name = request.query.get('workspace_name', 'Unknown')
            
            if not workspace_id:
                return json_response({
                    "status": "error",
                    "error": "workspace_id parameter required"
                })
            
            # Get access token
            token = await self.powerbi_client.get_access_token()
            if not token:
                return json_response({
                    "status": "error",
                    "error": "Failed to authenticate with Power BI"
                })
            
            # Check cache
            cache_key = f"datasets_{workspace_id}"
            if cache_key in self.dataset_cache:
                cached_data = self.dataset_cache[cache_key]
                if cached_data["expires"] > datetime.now():
                    logger.info(f"Returning cached datasets for workspace {workspace_name}")
                    return json_response({
                        "status": "success",
                        "datasets": cached_data["data"]
                    })
            
            # Get datasets
            datasets = await self.powerbi_client.get_workspace_datasets(token, workspace_id, workspace_name)
            
            # Convert to serializable format
            dataset_list = [
                {
                    "id": ds.id,
                    "name": ds.name,
                    "workspace_id": ds.workspace_id,
                    "workspace_name": ds.workspace_name,
                    "configured_by": ds.configured_by,
                    "created_date": ds.created_date
                }
                for ds in datasets
            ]
            
            # Cache the results
            self.dataset_cache[cache_key] = {
                "data": dataset_list,
                "expires": datetime.now().timestamp() + self.cache_duration
            }
            
            return json_response({
                "status": "success",
                "datasets": dataset_list
            })
            
        except Exception as e:
            logger.error(f"Error getting datasets: {e}")
            return json_response({
                "status": "error",
                "error": str(e)
            })
    
    async def analyze_query(self, request: Request) -> Response:
        """Main API endpoint for natural language query analysis"""
        try:
            data = await request.json()
            query = data.get('query', '').strip()
            dataset_id = data.get('dataset_id')
            dataset_name = data.get('dataset_name', 'Unknown Dataset')
            session_id = data.get('session_id')
            
            if not query:
                return json_response({
                    "status": "error",
                    "error": "Query is required"
                })
            
            if not dataset_id:
                return json_response({
                    "status": "error",
                    "error": "Please select a dataset first"
                })
            
            logger.info(f"Analyzing query: {query[:100]}... for dataset {dataset_name}")
            
            # Get access token
            token = await self.powerbi_client.get_access_token()
            if not token:
                return json_response({
                    "status": "error",
                    "error": "Failed to authenticate with Power BI"
                })
            
            # Get dataset metadata (cached if possible)
            metadata = await self._get_dataset_metadata(token, dataset_id)
            
            # Create translation context
            context = TranslationContext(
                dataset_metadata=metadata,
                available_measures=metadata.get("measures", []),
                available_tables=metadata.get("tables", []),
                business_context={
                    "dataset_id": dataset_id,
                    "dataset_name": dataset_name
                }
            )
            
            # Add to query history
            if session_id and session_id in self.sessions:
                context.query_history = self.sessions[session_id].get("query_history", [])
            
            # Translate to DAX
            logger.info("Translating natural language to DAX...")
            dax_result = await self.translator.translate_to_dax(query, context)
            
            if dax_result.error:
                return json_response({
                    "status": "error",
                    "error": dax_result.error,
                    "query_type": "translation_failed"
                })
            
            logger.info(f"Generated DAX query: {dax_result.query[:200]}...")
            
            # Execute DAX query
            logger.info("Executing DAX query...")
            query_result = await self.powerbi_client.execute_dax_query(
                token,
                dataset_id,
                dax_result.query,
                dataset_name
            )
            
            if not query_result.success:
                # Try to analyze and fix the error
                if self.translator and dax_result.query:
                    logger.info("Analyzing DAX error...")
                    error_analysis = await self.translator.analyze_dax_error(
                        dax_result.query,
                        query_result.error,
                        context
                    )
                    
                    return json_response({
                        "status": "success",
                        "query_type": "error_with_analysis",
                        "original_query": query,
                        "dax_query": dax_result.query,
                        "error": query_result.error,
                        "error_analysis": error_analysis,
                        "explanation": dax_result.explanation
                    })
                else:
                    return json_response({
                        "status": "error",
                        "error": query_result.error,
                        "dax_query": dax_result.query
                    })
            
            # Perform progressive analysis
            logger.info("Performing progressive analysis...")
            insight_result = await self.analysis_agent.perform_progressive_analysis(
                query,
                query_result,
                metadata,
                self.powerbi_client,
                token
            )
            
            # Update session history
            if session_id:
                if session_id not in self.sessions:
                    self.sessions[session_id] = {"query_history": []}
                self.sessions[session_id]["query_history"].append(query)
            
            # Format response
            response_data = {
                "status": "success",
                "query_type": "analysis_complete",
                "original_query": query,
                "dax_query": dax_result.query,
                "explanation": dax_result.explanation,
                "data": query_result.data,
                "row_count": query_result.row_count,
                "execution_time_ms": query_result.execution_time_ms,
                "insights": {
                    "summary": insight_result.summary,
                    "insights": insight_result.insights,
                    "recommendations": insight_result.recommendations,
                    "confidence": insight_result.confidence,
                    "investigation_complete": insight_result.investigation_complete
                },
                "follow_up_queries": self._generate_follow_up_suggestions(query, insight_result)
            }
            
            return json_response(response_data)
            
        except Exception as e:
            logger.error(f"Error analyzing query: {e}", exc_info=True)
            return json_response({
                "status": "error",
                "error": str(e)
            })
    
    async def execute_dax(self, request: Request) -> Response:
        """Direct DAX execution endpoint (for fixed queries)"""
        try:
            data = await request.json()
            dax_query = data.get('dax_query')
            dataset_id = data.get('dataset_id')
            dataset_name = data.get('dataset_name', 'Unknown Dataset')
            
            if not dax_query or not dataset_id:
                return json_response({
                    "status": "error",
                    "error": "dax_query and dataset_id are required"
                })
            
            # Get access token
            token = await self.powerbi_client.get_access_token()
            if not token:
                return json_response({
                    "status": "error",
                    "error": "Failed to authenticate with Power BI"
                })
            
            # Execute query
            result = await self.powerbi_client.execute_dax_query(
                token,
                dataset_id,
                dax_query,
                dataset_name
            )
            
            if result.success:
                return json_response({
                    "status": "success",
                    "data": result.data,
                    "row_count": result.row_count,
                    "execution_time_ms": result.execution_time_ms
                })
            else:
                return json_response({
                    "status": "error",
                    "error": result.error
                })
                
        except Exception as e:
            logger.error(f"Error executing DAX: {e}")
            return json_response({
                "status": "error",
                "error": str(e)
            })
    
    async def test_connection(self, request: Request) -> Response:
        """Test Power BI connection and configuration"""
        try:
            # Validate configuration
            validation = await self.powerbi_client.validate_configuration()
            
            test_results = {
                "configuration": validation,
                "test_steps": []
            }
            
            # Step 1: Check credentials
            test_results["test_steps"].append({
                "step": "Check credentials",
                "success": validation["credentials_present"],
                "details": "Power BI credentials are configured" if validation["credentials_present"] else "Missing credentials"
            })
            
            # Step 2: Get access token
            if validation["token_acquired"]:
                test_results["test_steps"].append({
                    "step": "Acquire access token",
                    "success": True,
                    "details": "Successfully authenticated with Azure AD"
                })
                
                # Step 3: Access API
                if validation["api_accessible"]:
                    test_results["test_steps"].append({
                        "step": "Access Power BI API",
                        "success": True,
                        "details": f"Found {validation.get('workspace_count', 0)} accessible workspaces"
                    })
                else:
                    test_results["test_steps"].append({
                        "step": "Access Power BI API",
                        "success": False,
                        "details": "Could not access Power BI API"
                    })
            else:
                test_results["test_steps"].append({
                    "step": "Acquire access token",
                    "success": False,
                    "details": "Failed to authenticate - check credentials"
                })
            
            # Overall status
            all_success = all(step["success"] for step in test_results["test_steps"])
            
            return json_response({
                "status": "success" if all_success else "partial",
                "test_results": test_results,
                "ready": validation["configured"] and validation["workspaces_accessible"]
            })
            
        except Exception as e:
            logger.error(f"Connection test error: {e}")
            return json_response({
                "status": "error",
                "error": str(e)
            })
    
    async def _get_dataset_metadata(self, token: str, dataset_id: str) -> Dict[str, Any]:
        """Get dataset metadata with caching"""
        cache_key = f"metadata_{dataset_id}"
        
        # Check cache
        if cache_key in self.dataset_cache:
            cached_data = self.dataset_cache[cache_key]
            if cached_data["expires"] > datetime.now():
                logger.info(f"Using cached metadata for dataset {dataset_id}")
                return cached_data["data"]
        
        # Fetch metadata
        logger.info(f"Fetching metadata for dataset {dataset_id}")
        metadata = await self.powerbi_client.get_dataset_metadata(token, dataset_id)
        
        # Cache the results
        self.dataset_cache[cache_key] = {
            "data": metadata,
            "expires": datetime.now().timestamp() + self.cache_duration
        }
        
        return metadata
    
    def _generate_follow_up_suggestions(self, original_query: str, insight_result: InsightResult) -> List[Dict[str, str]]:
        """Generate follow-up query suggestions based on the analysis"""
        suggestions = []
        
        # Use the translator's suggestion capability if available
        if hasattr(self.translator, 'suggest_follow_up_queries'):
            context = TranslationContext(
                dataset_metadata={},
                available_measures=[],
                available_tables=[],
                business_context={}
            )
            
            translator_suggestions = self.translator.suggest_follow_up_queries(
                original_query,
                insight_result,
                context
            )
            suggestions.extend(translator_suggestions)
        
        # Add generic suggestions based on query type
        query_lower = original_query.lower()
        
        if "revenue" in query_lower and not any("trend" in s.get("question", "").lower() for s in suggestions):
            suggestions.append({
                "question": "Show me the revenue trend over the last 12 months",
                "purpose": "Understand revenue patterns"
            })
        
        if "customer" in query_lower and not any("segment" in s.get("question", "").lower() for s in suggestions):
            suggestions.append({
                "question": "Which customer segments are most valuable?",
                "purpose": "Customer segmentation analysis"
            })
        
        # Limit to 3 suggestions
        return suggestions[:3]

def add_analyst_routes(app, sql_translator=None):
    """Add Power BI Analyst routes to the application"""
    
    analyst = PowerBIAnalyst()
    
    # Main page
    app.router.add_get('/analyst', analyst.analyst_page)
    app.router.add_get('/analyst/', analyst.analyst_page)
    
    # API endpoints
    app.router.add_get('/analyst/api/check-config', analyst.check_configuration)
    app.router.add_get('/analyst/api/workspaces', analyst.get_workspaces)
    app.router.add_get('/analyst/api/datasets', analyst.get_datasets)
    app.router.add_post('/analyst/api/analyze', analyst.analyze_query)
    app.router.add_post('/analyst/api/execute-dax', analyst.execute_dax)
    app.router.add_get('/analyst/api/test-connection', analyst.test_connection)
    
    logger.info("Power BI Analyst routes added successfully")
    return analyst