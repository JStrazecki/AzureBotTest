# powerbi_client.py - Power BI API Client for Authentication and Data Access
"""
Power BI Client - Handles authentication, workspace discovery, and DAX query execution
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import aiohttp
from msal import ConfidentialClientApplication
import jwt

logger = logging.getLogger(__name__)

@dataclass
class PowerBIConfig:
    """Power BI configuration"""
    tenant_id: str
    client_id: str
    client_secret: str
    scope: List[str] = field(default_factory=lambda: ["https://analysis.windows.net/powerbi/api/.default"])
    authority_url: str = field(init=False)
    
    def __post_init__(self):
        self.authority_url = f"https://login.microsoftonline.com/{self.tenant_id}"

@dataclass
class Workspace:
    """Power BI Workspace"""
    id: str
    name: str
    description: Optional[str] = None
    type: Optional[str] = None
    state: Optional[str] = None

@dataclass
class Dataset:
    """Power BI Dataset"""
    id: str
    name: str
    workspace_id: str
    configured_by: Optional[str] = None
    created_date: Optional[datetime] = None
    content_provider_type: Optional[str] = None
    description: Optional[str] = None
    
@dataclass
class Measure:
    """Power BI Measure"""
    name: str
    expression: str
    description: Optional[str] = None
    format_string: Optional[str] = None
    table_name: Optional[str] = None

@dataclass
class Table:
    """Power BI Table"""
    name: str
    columns: List[Dict[str, Any]]
    measures: List[Measure]
    description: Optional[str] = None
    
@dataclass
class DAXQueryResult:
    """Result of a DAX query execution"""
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    execution_time_ms: Optional[int] = None
    row_count: Optional[int] = None
    dataset_id: Optional[str] = None
    dataset_name: Optional[str] = None

class PowerBIClient:
    """Client for interacting with Power BI REST API"""
    
    def __init__(self):
        # Load configuration from environment
        self.config = PowerBIConfig(
            tenant_id=os.environ.get("POWERBI_TENANT_ID", ""),
            client_id=os.environ.get("POWERBI_CLIENT_ID", ""),
            client_secret=os.environ.get("POWERBI_CLIENT_SECRET", "")
        )
        
        if not all([self.config.tenant_id, self.config.client_id, self.config.client_secret]):
            logger.warning("Power BI configuration incomplete")
            self.configured = False
        else:
            self.configured = True
            
        # Initialize MSAL client
        self.msal_app = ConfidentialClientApplication(
            self.config.client_id,
            authority=self.config.authority_url,
            client_credential=self.config.client_secret
        ) if self.configured else None
        
        # Cache for access tokens
        self._token_cache = {}
        self._workspace_cache = {}
        self._dataset_cache = {}
        
        # API endpoints
        self.base_url = "https://api.powerbi.com/v1.0/myorg"
        
    async def get_access_token(self, user_token: Optional[str] = None) -> Optional[str]:
        """Get access token for Power BI API"""
        if not self.configured:
            return None
            
        try:
            if user_token:
                # Use on-behalf-of flow for user delegation
                result = self.msal_app.acquire_token_on_behalf_of(
                    user_assertion=user_token,
                    scopes=self.config.scope
                )
            else:
                # Use client credentials flow
                result = self.msal_app.acquire_token_silent(
                    scopes=self.config.scope,
                    account=None
                )
                
                if not result:
                    result = self.msal_app.acquire_token_for_client(
                        scopes=self.config.scope
                    )
            
            if "access_token" in result:
                return result["access_token"]
            else:
                logger.error(f"Failed to get access token: {result.get('error_description', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting access token: {e}")
            return None
    
    async def get_user_workspaces(self, access_token: str) -> List[Workspace]:
        """Get workspaces accessible to the user"""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/groups",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        workspaces = []
                        
                        for ws in data.get("value", []):
                            workspace = Workspace(
                                id=ws["id"],
                                name=ws["name"],
                                description=ws.get("description"),
                                type=ws.get("type"),
                                state=ws.get("state")
                            )
                            workspaces.append(workspace)
                            
                            # Cache workspace
                            self._workspace_cache[workspace.id] = workspace
                        
                        return workspaces
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get workspaces: {response.status} - {error_text}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error getting workspaces: {e}")
            return []
    
    async def get_datasets(self, access_token: str, workspace_id: str) -> List[Dataset]:
        """Get datasets in a workspace"""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/groups/{workspace_id}/datasets",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        datasets = []
                        
                        for ds in data.get("value", []):
                            dataset = Dataset(
                                id=ds["id"],
                                name=ds["name"],
                                workspace_id=workspace_id,
                                configured_by=ds.get("configuredBy"),
                                created_date=datetime.fromisoformat(ds["createdDate"].replace("Z", "+00:00")) if ds.get("createdDate") else None,
                                content_provider_type=ds.get("contentProviderType"),
                                description=ds.get("description")
                            )
                            datasets.append(dataset)
                            
                            # Cache dataset
                            self._dataset_cache[dataset.id] = dataset
                        
                        return datasets
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get datasets: {response.status} - {error_text}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error getting datasets: {e}")
            return []
    
    async def get_dataset_metadata(self, access_token: str, dataset_id: str) -> Dict[str, Any]:
        """Get detailed metadata for a dataset including tables and measures"""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Get dataset refresh history to understand data freshness
            refresh_history = await self._get_refresh_history(access_token, dataset_id)
            
            # Execute DISCOVER queries to get schema
            tables = await self._discover_tables(access_token, dataset_id)
            measures = await self._discover_measures(access_token, dataset_id)
            
            # Get cached dataset info
            dataset_info = self._dataset_cache.get(dataset_id, {})
            
            metadata = {
                "dataset_id": dataset_id,
                "dataset_name": dataset_info.name if hasattr(dataset_info, 'name') else "Unknown",
                "tables": tables,
                "measures": measures,
                "table_count": len(tables),
                "measure_count": len(measures),
                "last_refresh": refresh_history.get("last_refresh"),
                "refresh_status": refresh_history.get("status")
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting dataset metadata: {e}")
            return {}
    
    async def execute_dax_query(self, access_token: str, dataset_id: str, dax_query: str, dataset_name: Optional[str] = None) -> DAXQueryResult:
        """Execute a DAX query against a dataset"""
        start_time = datetime.now()
        
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Find the workspace ID for this dataset
            workspace_id = await self._find_workspace_for_dataset(access_token, dataset_id)
            if not workspace_id:
                return DAXQueryResult(
                    success=False,
                    error="Could not find workspace for dataset"
                )
            
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
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/groups/{workspace_id}/datasets/{dataset_id}/executeQueries",
                    headers=headers,
                    json=payload
                ) as response:
                    execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract results from the response
                        if data.get("results") and len(data["results"]) > 0:
                            query_result = data["results"][0]
                            
                            if "tables" in query_result and len(query_result["tables"]) > 0:
                                table = query_result["tables"][0]
                                rows = table.get("rows", [])
                                
                                # Convert to list of dictionaries
                                formatted_rows = []
                                if rows and "columns" in table:
                                    columns = [col["name"] for col in table["columns"]]
                                    for row in rows:
                                        row_dict = {}
                                        for i, col in enumerate(columns):
                                            row_dict[col] = row.get(col) if isinstance(row, dict) else row[i] if i < len(row) else None
                                        formatted_rows.append(row_dict)
                                
                                return DAXQueryResult(
                                    success=True,
                                    data=formatted_rows,
                                    row_count=len(formatted_rows),
                                    execution_time_ms=execution_time,
                                    dataset_id=dataset_id,
                                    dataset_name=dataset_name
                                )
                            else:
                                # Query executed but returned no data
                                return DAXQueryResult(
                                    success=True,
                                    data=[],
                                    row_count=0,
                                    execution_time_ms=execution_time,
                                    dataset_id=dataset_id,
                                    dataset_name=dataset_name
                                )
                        else:
                            return DAXQueryResult(
                                success=False,
                                error="Query returned no results",
                                execution_time_ms=execution_time
                            )
                    else:
                        error_text = await response.text()
                        error_json = {}
                        try:
                            error_json = json.loads(error_text)
                            error_message = error_json.get("error", {}).get("message", error_text)
                        except:
                            error_message = error_text
                            
                        logger.error(f"DAX query failed: {response.status} - {error_message}")
                        
                        return DAXQueryResult(
                            success=False,
                            error=error_message,
                            execution_time_ms=execution_time
                        )
                        
        except Exception as e:
            logger.error(f"Error executing DAX query: {e}")
            return DAXQueryResult(
                success=False,
                error=str(e)
            )
    
    async def _find_workspace_for_dataset(self, access_token: str, dataset_id: str) -> Optional[str]:
        """Find which workspace contains a dataset"""
        # First check cache
        for ws_id, ws in self._workspace_cache.items():
            # Need to check if dataset belongs to this workspace
            datasets = await self.get_datasets(access_token, ws_id)
            if any(d.id == dataset_id for d in datasets):
                return ws_id
        
        # If not in cache, search all workspaces
        workspaces = await self.get_user_workspaces(access_token)
        for workspace in workspaces:
            datasets = await self.get_datasets(access_token, workspace.id)
            if any(d.id == dataset_id for d in datasets):
                return workspace.id
        
        return None
    
    async def _get_refresh_history(self, access_token: str, dataset_id: str) -> Dict[str, Any]:
        """Get refresh history for a dataset"""
        try:
            workspace_id = await self._find_workspace_for_dataset(access_token, dataset_id)
            if not workspace_id:
                return {}
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/groups/{workspace_id}/datasets/{dataset_id}/refreshes",
                    headers=headers,
                    params={"$top": 1}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        refreshes = data.get("value", [])
                        
                        if refreshes:
                            latest = refreshes[0]
                            return {
                                "last_refresh": latest.get("endTime"),
                                "status": latest.get("status"),
                                "refresh_type": latest.get("refreshType")
                            }
                    
                    return {}
                    
        except Exception as e:
            logger.error(f"Error getting refresh history: {e}")
            return {}
    
    async def _discover_tables(self, access_token: str, dataset_id: str) -> List[Dict[str, Any]]:
        """Discover tables in a dataset using DAX query"""
        query = """
        EVALUATE
        SELECTCOLUMNS(
            INFO.TABLES(),
            "TableName", [Name],
            "Description", [Description],
            "IsHidden", [IsHidden]
        )
        """
        
        result = await self.execute_dax_query(access_token, dataset_id, query)
        
        if result.success and result.data:
            return [
                {
                    "name": row.get("TableName"),
                    "description": row.get("Description"),
                    "is_hidden": row.get("IsHidden", False)
                }
                for row in result.data
                if not row.get("IsHidden", False)
            ]
        
        return []
    
    async def _discover_measures(self, access_token: str, dataset_id: str) -> List[Dict[str, Any]]:
        """Discover measures in a dataset using DAX query"""
        query = """
        EVALUATE
        SELECTCOLUMNS(
            INFO.MEASURES(),
            "MeasureName", [Name],
            "TableName", [TableName],
            "Expression", [Expression],
            "Description", [Description],
            "FormatString", [FormatString]
        )
        """
        
        result = await self.execute_dax_query(access_token, dataset_id, query)
        
        if result.success and result.data:
            return [
                {
                    "name": row.get("MeasureName"),
                    "table": row.get("TableName"),
                    "expression": row.get("Expression"),
                    "description": row.get("Description"),
                    "format_string": row.get("FormatString")
                }
                for row in result.data
            ]
        
        return []
    
    def validate_dax_query(self, query: str) -> Tuple[bool, Optional[str]]:
        """Basic validation of DAX query syntax"""
        query = query.strip()
        
        # Check if query is empty
        if not query:
            return False, "Query cannot be empty"
        
        # Check for required EVALUATE statement
        if not query.upper().startswith("EVALUATE"):
            return False, "DAX query must start with EVALUATE"
        
        # Check for basic syntax errors
        open_parens = query.count("(")
        close_parens = query.count(")")
        if open_parens != close_parens:
            return False, f"Mismatched parentheses: {open_parens} opening, {close_parens} closing"
        
        # Check for dangerous operations (we only want read operations)
        dangerous_keywords = ["REFRESH", "CREATE", "DELETE", "DROP", "ALTER"]
        for keyword in dangerous_keywords:
            if keyword in query.upper():
                return False, f"Query contains forbidden operation: {keyword}"
        
        return True, None
    
    async def get_quick_insights(self, access_token: str, dataset_id: str) -> Dict[str, Any]:
        """Get quick insights about a dataset"""
        try:
            # Get basic metrics
            table_count_query = """
            EVALUATE
            ROW(
                "TableCount", COUNTROWS(INFO.TABLES()),
                "MeasureCount", COUNTROWS(INFO.MEASURES())
            )
            """
            
            result = await self.execute_dax_query(access_token, dataset_id, table_count_query)
            
            insights = {
                "table_count": 0,
                "measure_count": 0,
                "key_measures": [],
                "data_freshness": "Unknown"
            }
            
            if result.success and result.data:
                insights["table_count"] = result.data[0].get("TableCount", 0)
                insights["measure_count"] = result.data[0].get("MeasureCount", 0)
            
            # Get refresh history
            refresh_info = await self._get_refresh_history(access_token, dataset_id)
            if refresh_info.get("last_refresh"):
                insights["data_freshness"] = refresh_info["last_refresh"]
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting quick insights: {e}")
            return {}

# Create singleton instance
powerbi_client = PowerBIClient()

# Export
__all__ = ['PowerBIClient', 'powerbi_client', 'Workspace', 'Dataset', 'DAXQueryResult']