# powerbi_client.py - Power BI Authentication and API Client
"""
Power BI Client - Handles authentication and API calls to Power BI service
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import aiohttp
from msal import ConfidentialClientApplication
import jwt

logger = logging.getLogger(__name__)

@dataclass
class PowerBICredentials:
    """Power BI authentication credentials"""
    tenant_id: str
    client_id: str
    client_secret: str
    scope: List[str] = field(default_factory=lambda: ["https://analysis.windows.net/powerbi/api/.default"])

@dataclass
class WorkspaceInfo:
    """Power BI workspace information"""
    id: str
    name: str
    description: Optional[str] = None
    is_personal: bool = False
    capacity_id: Optional[str] = None

@dataclass
class DatasetInfo:
    """Power BI dataset information"""
    id: str
    name: str
    workspace_id: str
    workspace_name: str
    configured_by: Optional[str] = None
    created_date: Optional[str] = None
    content_provider_type: Optional[str] = None
    tables: List[Dict[str, Any]] = field(default_factory=list)
    measures: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class QueryResult:
    """Result from a DAX query execution"""
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    execution_time_ms: Optional[int] = None
    dataset_id: Optional[str] = None
    dataset_name: Optional[str] = None
    row_count: int = 0

class PowerBIClient:
    """Client for interacting with Power BI REST API"""
    
    def __init__(self):
        # Load credentials from environment
        self.credentials = PowerBICredentials(
            tenant_id=os.environ.get("POWERBI_TENANT_ID", ""),
            client_id=os.environ.get("POWERBI_CLIENT_ID", ""),
            client_secret=os.environ.get("POWERBI_CLIENT_SECRET", "")
        )
        
        # Validate credentials
        if not all([self.credentials.tenant_id, self.credentials.client_id, self.credentials.client_secret]):
            logger.warning("Power BI credentials not fully configured")
            self.configured = False
        else:
            self.configured = True
        
        # Initialize MSAL client
        if self.configured:
            self.msal_app = ConfidentialClientApplication(
                self.credentials.client_id,
                authority=f"https://login.microsoftonline.com/{self.credentials.tenant_id}",
                client_credential=self.credentials.client_secret
            )
        else:
            self.msal_app = None
        
        # Base URLs
        self.base_url = "https://api.powerbi.com/v1.0/myorg"
        self.token_cache = {}
        
        logger.info(f"Power BI Client initialized - Configured: {self.configured}")
    
    async def get_access_token(self) -> Optional[str]:
        """Get access token for Power BI API"""
        if not self.configured:
            logger.error("Power BI client not configured")
            return None
        
        try:
            # Check cache
            cache_key = "powerbi_token"
            if cache_key in self.token_cache:
                cached_token = self.token_cache[cache_key]
                # Check if token is still valid (with 5 min buffer)
                if cached_token["expires_at"] > datetime.now() + timedelta(minutes=5):
                    return cached_token["access_token"]
            
            # Get new token
            result = self.msal_app.acquire_token_for_client(scopes=self.credentials.scope)
            
            if "access_token" in result:
                # Cache the token
                self.token_cache[cache_key] = {
                    "access_token": result["access_token"],
                    "expires_at": datetime.now() + timedelta(seconds=result.get("expires_in", 3600))
                }
                logger.info("Successfully acquired Power BI access token")
                return result["access_token"]
            else:
                logger.error(f"Failed to acquire token: {result.get('error_description', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting access token: {e}")
            return None
    
    async def get_user_workspaces(self, access_token: str) -> List[WorkspaceInfo]:
        """Get list of workspaces accessible to the user"""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/groups",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        workspaces = []
                        
                        for ws in data.get("value", []):
                            workspace = WorkspaceInfo(
                                id=ws["id"],
                                name=ws["name"],
                                description=ws.get("description"),
                                is_personal=ws.get("isPersonal", False),
                                capacity_id=ws.get("capacityId")
                            )
                            workspaces.append(workspace)
                        
                        logger.info(f"Retrieved {len(workspaces)} workspaces")
                        return workspaces
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get workspaces: {response.status} - {error_text}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error fetching workspaces: {e}")
            return []
    
    async def get_workspace_datasets(self, access_token: str, workspace_id: str, workspace_name: str = "") -> List[DatasetInfo]:
        """Get datasets in a specific workspace"""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/groups/{workspace_id}/datasets",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        datasets = []
                        
                        for ds in data.get("value", []):
                            # Only include datasets that can be queried
                            if ds.get("isRefreshable", True):
                                dataset = DatasetInfo(
                                    id=ds["id"],
                                    name=ds["name"],
                                    workspace_id=workspace_id,
                                    workspace_name=workspace_name,
                                    configured_by=ds.get("configuredBy"),
                                    created_date=ds.get("createdDate"),
                                    content_provider_type=ds.get("contentProviderType")
                                )
                                datasets.append(dataset)
                        
                        logger.info(f"Retrieved {len(datasets)} datasets from workspace {workspace_name}")
                        return datasets
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get datasets: {response.status} - {error_text}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error fetching datasets: {e}")
            return []
    
    async def get_dataset_metadata(self, access_token: str, dataset_id: str) -> Dict[str, Any]:
        """Get detailed metadata for a dataset including tables and measures"""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            metadata = {
                "tables": [],
                "measures": [],
                "relationships": []
            }
            
            # First, try to get dataset schema
            async with aiohttp.ClientSession() as session:
                # Get dataset refresh history to understand the model better
                async with session.get(
                    f"{self.base_url}/datasets/{dataset_id}/refreshes",
                    headers=headers,
                    params={"$top": 1},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        refresh_data = await response.json()
                        if refresh_data.get("value"):
                            metadata["last_refresh"] = refresh_data["value"][0].get("endTime")
                
                # Execute a metadata query to discover tables and measures
                metadata_query = """
                EVALUATE
                    UNION(
                        SELECTCOLUMNS(
                            INFO.TABLES(),
                            "Type", "Table",
                            "Name", [Name],
                            "Description", [Description]
                        ),
                        SELECTCOLUMNS(
                            INFO.MEASURES(),
                            "Type", "Measure",
                            "Name", [Name],
                            "Description", [Description]
                        )
                    )
                """
                
                # Try to execute metadata query
                result = await self.execute_dax_query(access_token, dataset_id, metadata_query)
                
                if result.success and result.data:
                    for item in result.data:
                        if item.get("Type") == "Table":
                            metadata["tables"].append({
                                "name": item.get("Name", ""),
                                "description": item.get("Description", "")
                            })
                        elif item.get("Type") == "Measure":
                            metadata["measures"].append({
                                "name": item.get("Name", ""),
                                "description": item.get("Description", "")
                            })
                else:
                    # Fallback: Try simpler queries
                    logger.info("Metadata query failed, using fallback approach")
                    
                    # Try to get at least some basic info
                    simple_query = """
                    EVALUATE
                    ROW("Dataset", "Available")
                    """
                    
                    test_result = await self.execute_dax_query(access_token, dataset_id, simple_query)
                    if test_result.success:
                        metadata["status"] = "accessible"
                    else:
                        metadata["status"] = "inaccessible"
                        metadata["error"] = test_result.error
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error fetching dataset metadata: {e}")
            return {"error": str(e)}
    
    async def execute_dax_query(self, access_token: str, dataset_id: str, dax_query: str, dataset_name: str = "") -> QueryResult:
        """Execute a DAX query against a Power BI dataset"""
        start_time = datetime.now()
        
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Prepare the query payload
            payload = {
                "queries": [
                    {
                        "query": dax_query
                    }
                ],
                "serializerSettings": {
                    "includeNulls": True
                }
            }
            
            logger.info(f"Executing DAX query on dataset {dataset_id}: {dax_query[:100]}...")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/datasets/{dataset_id}/executeQueries",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract results from the response
                        if "results" in data and len(data["results"]) > 0:
                            result = data["results"][0]
                            
                            if "tables" in result and len(result["tables"]) > 0:
                                table = result["tables"][0]
                                rows = table.get("rows", [])
                                
                                # Convert rows to list of dictionaries
                                formatted_rows = []
                                for row in rows:
                                    formatted_rows.append(row)
                                
                                logger.info(f"Query successful: {len(formatted_rows)} rows returned")
                                
                                return QueryResult(
                                    success=True,
                                    data=formatted_rows,
                                    row_count=len(formatted_rows),
                                    execution_time_ms=execution_time,
                                    dataset_id=dataset_id,
                                    dataset_name=dataset_name
                                )
                            else:
                                # Query executed but no data returned
                                return QueryResult(
                                    success=True,
                                    data=[],
                                    row_count=0,
                                    execution_time_ms=execution_time,
                                    dataset_id=dataset_id,
                                    dataset_name=dataset_name
                                )
                        else:
                            # No results in response
                            return QueryResult(
                                success=False,
                                error="No results returned from query",
                                execution_time_ms=execution_time
                            )
                    
                    elif response.status == 400:
                        # Bad request - likely DAX syntax error
                        error_data = await response.json()
                        error_message = self._extract_error_message(error_data)
                        
                        logger.error(f"DAX syntax error: {error_message}")
                        
                        return QueryResult(
                            success=False,
                            error=f"DAX syntax error: {error_message}",
                            execution_time_ms=execution_time
                        )
                    
                    elif response.status == 401:
                        # Unauthorized
                        return QueryResult(
                            success=False,
                            error="Unauthorized: Access token may be expired or invalid",
                            execution_time_ms=execution_time
                        )
                    
                    elif response.status == 404:
                        # Dataset not found
                        return QueryResult(
                            success=False,
                            error=f"Dataset {dataset_id} not found or not accessible",
                            execution_time_ms=execution_time
                        )
                    
                    else:
                        # Other error
                        error_text = await response.text()
                        logger.error(f"Query failed with status {response.status}: {error_text}")
                        
                        return QueryResult(
                            success=False,
                            error=f"Query failed with status {response.status}: {error_text[:200]}",
                            execution_time_ms=execution_time
                        )
                        
        except asyncio.TimeoutError:
            return QueryResult(
                success=False,
                error="Query timeout: The query took too long to execute",
                execution_time_ms=60000
            )
        except Exception as e:
            logger.error(f"Error executing DAX query: {e}")
            return QueryResult(
                success=False,
                error=f"Error executing query: {str(e)}",
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )
    
    def _extract_error_message(self, error_data: Dict[str, Any]) -> str:
        """Extract meaningful error message from Power BI error response"""
        if "error" in error_data:
            error = error_data["error"]
            if isinstance(error, dict):
                # Check for detailed error information
                if "pbi.error" in error:
                    pbi_error = error["pbi.error"]
                    if "details" in pbi_error and len(pbi_error["details"]) > 0:
                        detail = pbi_error["details"][0]
                        return detail.get("detail", {}).get("value", error.get("message", "Unknown error"))
                return error.get("message", "Unknown error")
            else:
                return str(error)
        
        return "Unknown error occurred"
    
    async def validate_configuration(self) -> Dict[str, Any]:
        """Validate Power BI configuration and connectivity"""
        validation_result = {
            "configured": self.configured,
            "credentials_present": False,
            "token_acquired": False,
            "api_accessible": False,
            "workspaces_accessible": False,
            "errors": []
        }
        
        # Check credentials
        if all([self.credentials.tenant_id, self.credentials.client_id, self.credentials.client_secret]):
            validation_result["credentials_present"] = True
        else:
            validation_result["errors"].append("Missing Power BI credentials")
            return validation_result
        
        # Try to get access token
        token = await self.get_access_token()
        if token:
            validation_result["token_acquired"] = True
            
            # Try to access API
            try:
                workspaces = await self.get_user_workspaces(token)
                if workspaces:
                    validation_result["api_accessible"] = True
                    validation_result["workspaces_accessible"] = True
                    validation_result["workspace_count"] = len(workspaces)
                else:
                    validation_result["errors"].append("No workspaces accessible")
            except Exception as e:
                validation_result["errors"].append(f"API access error: {str(e)}")
        else:
            validation_result["errors"].append("Failed to acquire access token")
        
        return validation_result
    
    def is_configured(self) -> bool:
        """Check if Power BI client is properly configured"""
        return self.configured

# Create singleton instance
powerbi_client = PowerBIClient()

# Export
__all__ = ['PowerBIClient', 'powerbi_client', 'WorkspaceInfo', 'DatasetInfo', 'QueryResult']