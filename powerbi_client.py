# powerbi_client.py - Power BI Authentication and API Client
"""
Power BI Client - Handles authentication and API calls to Power BI service
Fixed version with datetime comparison bug fix and better workspace access handling
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import aiohttp

# Handle MSAL import with fallback
try:
    from msal import ConfidentialClientApplication
    MSAL_AVAILABLE = True
except ImportError:
    MSAL_AVAILABLE = False
    ConfidentialClientApplication = None

# Handle JWT import (pyjwt installs as jwt)
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

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
    type: Optional[str] = None
    state: Optional[str] = None

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
        # Check dependencies first
        if not MSAL_AVAILABLE:
            logger.error("MSAL library not available. Install with: pip install msal")
            self.configured = False
            self.msal_app = None
            return
            
        # Load credentials from environment
        self.credentials = PowerBICredentials(
            tenant_id=os.environ.get("POWERBI_TENANT_ID", "").strip(),
            client_id=os.environ.get("POWERBI_CLIENT_ID", "").strip(),
            client_secret=os.environ.get("POWERBI_CLIENT_SECRET", "").strip()
        )
        
        # Log credential status (without exposing secrets)
        logger.info("Power BI Client initialization:")
        logger.info(f"  Tenant ID: {'SET' if self.credentials.tenant_id else 'NOT SET'}")
        logger.info(f"  Client ID: {'SET' if self.credentials.client_id else 'NOT SET'}")
        logger.info(f"  Client Secret: {'SET' if self.credentials.client_secret else 'NOT SET'}")
        logger.info(f"  MSAL Available: {MSAL_AVAILABLE}")
        logger.info(f"  JWT Available: {JWT_AVAILABLE}")
        
        # Validate credentials
        if not all([self.credentials.tenant_id, self.credentials.client_id, self.credentials.client_secret]):
            logger.warning("Power BI credentials not fully configured")
            self.configured = False
            self.msal_app = None
        else:
            self.configured = True
            logger.info("Power BI credentials are fully configured")
        
        # Initialize MSAL client
        if self.configured and MSAL_AVAILABLE:
            try:
                self.msal_app = ConfidentialClientApplication(
                    self.credentials.client_id,
                    authority=f"https://login.microsoftonline.com/{self.credentials.tenant_id}",
                    client_credential=self.credentials.client_secret
                )
                logger.info("MSAL client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize MSAL client: {e}")
                self.msal_app = None
                self.configured = False
        else:
            self.msal_app = None
        
        # Base URLs
        self.base_url = "https://api.powerbi.com/v1.0/myorg"
        self.token_cache = {}
        
        logger.info(f"Power BI Client initialized - Configured: {self.configured}")
    
    async def get_access_token(self) -> Optional[str]:
        """Get access token for Power BI API"""
        if not self.configured:
            logger.error("Power BI client not configured - cannot get access token")
            return None
        
        if not self.msal_app:
            logger.error("MSAL app not initialized - cannot get access token")
            return None
        
        try:
            # Check cache
            cache_key = "powerbi_token"
            if cache_key in self.token_cache:
                cached_token = self.token_cache[cache_key]
                # FIX: Compare datetime to datetime, not float to datetime
                if cached_token["expires_at"] > datetime.now() + timedelta(minutes=5):
                    logger.info("Using cached Power BI access token")
                    return cached_token["access_token"]
            
            logger.info("Acquiring new Power BI access token...")
            
            # Get new token
            result = self.msal_app.acquire_token_for_client(scopes=self.credentials.scope)
            
            if "access_token" in result:
                # Cache the token with datetime object (not timestamp)
                self.token_cache[cache_key] = {
                    "access_token": result["access_token"],
                    "expires_at": datetime.now() + timedelta(seconds=result.get("expires_in", 3600))
                }
                logger.info("Successfully acquired Power BI access token")
                
                # Log token details (without exposing the actual token)
                if "expires_in" in result:
                    logger.info(f"Token expires in {result['expires_in']} seconds")
                
                return result["access_token"]
            else:
                error_msg = result.get('error_description', result.get('error', 'Unknown error'))
                logger.error(f"Failed to acquire token: {error_msg}")
                
                # Provide more specific error guidance
                if "AADSTS700016" in str(error_msg):
                    logger.error("Application not found - check POWERBI_CLIENT_ID")
                elif "AADSTS7000215" in str(error_msg):
                    logger.error("Invalid client secret - check POWERBI_CLIENT_SECRET")
                elif "AADSTS90002" in str(error_msg):
                    logger.error("Tenant not found - check POWERBI_TENANT_ID")
                
                return None
                
        except Exception as e:
            logger.error(f"Exception while getting access token: {e}", exc_info=True)
            return None
    
    async def get_user_workspaces(self, access_token: str) -> List[WorkspaceInfo]:
        """Get list of workspaces accessible to the user/app"""
        try:
            logger.info("Fetching accessible workspaces...")
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                # First try the regular groups endpoint
                async with session.get(
                    f"{self.base_url}/groups",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    logger.info(f"Workspace API response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        workspaces = []
                        
                        # Process workspaces from groups endpoint
                        for ws in data.get("value", []):
                            logger.info(f"Found workspace: {ws.get('name', 'Unknown')} (ID: {ws.get('id', 'Unknown')[:8]}...)")
                            
                            workspace = WorkspaceInfo(
                                id=ws["id"],
                                name=ws["name"],
                                description=ws.get("description"),
                                is_personal=ws.get("isPersonal", False),
                                capacity_id=ws.get("capacityId"),
                                type=ws.get("type", "Workspace"),
                                state=ws.get("state", "Active")
                            )
                            
                            # Only include active workspaces
                            if workspace.state == "Active":
                                workspaces.append(workspace)
                            else:
                                logger.info(f"Skipping inactive workspace: {workspace.name}")
                        
                        # If no workspaces found, try to get My Workspace (personal workspace)
                        if len(workspaces) == 0:
                            logger.info("No shared workspaces found. Checking for personal workspace...")
                            
                            # Try to access datasets directly to verify access
                            try:
                                async with session.get(
                                    f"{self.base_url}/datasets",
                                    headers=headers,
                                    timeout=aiohttp.ClientTimeout(total=10)
                                ) as dataset_response:
                                    
                                    if dataset_response.status == 200:
                                        dataset_data = await dataset_response.json()
                                        if dataset_data.get("value"):
                                            logger.info("Found datasets in personal workspace")
                                            # Add a virtual "My Workspace" entry
                                            workspaces.append(WorkspaceInfo(
                                                id="me",  # Special ID for personal workspace
                                                name="My Workspace",
                                                description="Personal workspace",
                                                is_personal=True,
                                                state="Active"
                                            ))
                            except Exception as e:
                                logger.warning(f"Could not check personal workspace: {e}")
                        
                        logger.info(f"Retrieved {len(workspaces)} accessible workspaces")
                        
                        # Provide helpful messages if no workspaces found
                        if len(workspaces) == 0:
                            logger.warning("No workspaces found. Possible reasons:")
                            logger.warning("1. The app registration needs to be granted access to workspaces in Power BI")
                            logger.warning("2. In Power BI Service (app.powerbi.com):")
                            logger.warning("   - Go to the workspace")
                            logger.warning("   - Click 'Manage access' or 'Access'")
                            logger.warning("   - Add the app (using the app's name or client ID)")
                            logger.warning("   - Grant at least 'Viewer' role")
                            logger.warning("3. Wait a few minutes for permissions to propagate")
                        
                        return workspaces
                    
                    elif response.status == 401:
                        error_text = await response.text()
                        logger.error(f"Unauthorized access to workspaces API: {error_text}")
                        logger.error("Check that the app registration has the correct API permissions (Workspace.Read.All)")
                        return []
                    
                    elif response.status == 403:
                        error_text = await response.text()
                        logger.error(f"Forbidden access to workspaces API: {error_text}")
                        logger.error("The app registration may not have the required permissions")
                        return []
                    
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get workspaces: {response.status} - {error_text}")
                        return []
                        
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching workspaces: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching workspaces: {e}", exc_info=True)
            return []
    
    async def get_workspace_datasets(self, access_token: str, workspace_id: str, workspace_name: str = "") -> List[DatasetInfo]:
        """Get datasets in a specific workspace"""
        try:
            logger.info(f"Fetching datasets for workspace: {workspace_name} (ID: {workspace_id[:8] if workspace_id != 'me' else 'personal'}...)")
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Handle personal workspace differently
            if workspace_id == "me":
                url = f"{self.base_url}/datasets"
            else:
                url = f"{self.base_url}/groups/{workspace_id}/datasets"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    logger.info(f"Dataset API response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        datasets = []
                        
                        for ds in data.get("value", []):
                            # Log dataset info
                            logger.info(f"Found dataset: {ds.get('name', 'Unknown')} (ID: {ds.get('id', 'Unknown')[:8]}...)")
                            
                            # Only include datasets that can be queried
                            if ds.get("isRefreshable", True) or ds.get("isEffectiveIdentityRequired", False) or True:  # Be more permissive
                                dataset = DatasetInfo(
                                    id=ds["id"],
                                    name=ds["name"],
                                    workspace_id=workspace_id,
                                    workspace_name=workspace_name or "My Workspace" if workspace_id == "me" else workspace_name,
                                    configured_by=ds.get("configuredBy"),
                                    created_date=ds.get("createdDate"),
                                    content_provider_type=ds.get("contentProviderType")
                                )
                                datasets.append(dataset)
                            else:
                                logger.info(f"Skipping non-queryable dataset: {ds.get('name', 'Unknown')}")
                        
                        logger.info(f"Retrieved {len(datasets)} queryable datasets from workspace {workspace_name}")
                        return datasets
                    
                    elif response.status == 401:
                        error_text = await response.text()
                        logger.error(f"Unauthorized access to datasets in workspace {workspace_name}: {error_text}")
                        return []
                    
                    elif response.status == 403:
                        error_text = await response.text()
                        logger.error(f"Forbidden access to datasets in workspace {workspace_name}: {error_text}")
                        logger.error("The app may not have access to this workspace's datasets")
                        return []
                    
                    elif response.status == 404:
                        logger.error(f"Workspace {workspace_name} not found or not accessible")
                        return []
                    
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get datasets: {response.status} - {error_text}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error fetching datasets for workspace {workspace_name}: {e}", exc_info=True)
            return []
    
    async def get_dataset_metadata(self, access_token: str, dataset_id: str) -> Dict[str, Any]:
        """Get detailed metadata for a dataset including tables and measures"""
        try:
            logger.info(f"Fetching metadata for dataset: {dataset_id[:8]}...")
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            metadata = {
                "tables": [],
                "measures": [],
                "relationships": []
            }
            
            # First, try to get dataset refresh history to understand the model better
            async with aiohttp.ClientSession() as session:
                try:
                    # Get dataset refresh history
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
                                logger.info(f"Dataset last refreshed: {metadata['last_refresh']}")
                except Exception as e:
                    logger.warning(f"Could not get refresh history: {e}")
                
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
                logger.info("Attempting to discover dataset schema using DAX query...")
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
                    
                    logger.info(f"Discovered {len(metadata['tables'])} tables and {len(metadata['measures'])} measures")
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
                        logger.info("Dataset is accessible for queries")
                    else:
                        metadata["status"] = "inaccessible"
                        metadata["error"] = test_result.error
                        logger.warning(f"Dataset may not be fully accessible: {test_result.error}")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error fetching dataset metadata: {e}", exc_info=True)
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
            
            logger.info(f"Executing DAX query on dataset {dataset_name or dataset_id[:8]}: {dax_query[:100]}...")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/datasets/{dataset_id}/executeQueries",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
                    
                    logger.info(f"DAX query response status: {response.status}")
                    
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
                                
                                logger.info(f"Query successful: {len(formatted_rows)} rows returned in {execution_time}ms")
                                
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
                                logger.info("Query executed successfully but returned no data")
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
                            logger.warning("Query response contains no results")
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
                        error_text = await response.text()
                        logger.error(f"Unauthorized access to dataset: {error_text}")
                        return QueryResult(
                            success=False,
                            error="Unauthorized: Access token may be expired or invalid",
                            execution_time_ms=execution_time
                        )
                    
                    elif response.status == 403:
                        # Forbidden
                        error_text = await response.text()
                        logger.error(f"Forbidden access to dataset: {error_text}")
                        return QueryResult(
                            success=False,
                            error="Access denied: The app may not have permission to query this dataset",
                            execution_time_ms=execution_time
                        )
                    
                    elif response.status == 404:
                        # Dataset not found
                        logger.error(f"Dataset {dataset_id} not found")
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
            logger.error("DAX query timed out after 60 seconds")
            return QueryResult(
                success=False,
                error="Query timeout: The query took too long to execute",
                execution_time_ms=60000
            )
        except Exception as e:
            logger.error(f"Error executing DAX query: {e}", exc_info=True)
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
            "errors": [],
            "warnings": [],
            "dependencies": {
                "msal": MSAL_AVAILABLE,
                "jwt": JWT_AVAILABLE
            }
        }
        
        logger.info("Starting Power BI configuration validation...")
        
        # Check dependencies
        if not MSAL_AVAILABLE:
            validation_result["errors"].append("MSAL library not installed. Run: pip install msal")
            logger.error("✗ MSAL library not available")
            return validation_result
            
        # Check credentials
        if all([self.credentials.tenant_id, self.credentials.client_id, self.credentials.client_secret]):
            validation_result["credentials_present"] = True
            logger.info("✓ Power BI credentials are present")
        else:
            missing = []
            if not self.credentials.tenant_id:
                missing.append("POWERBI_TENANT_ID")
            if not self.credentials.client_id:
                missing.append("POWERBI_CLIENT_ID")
            if not self.credentials.client_secret:
                missing.append("POWERBI_CLIENT_SECRET")
            
            error_msg = f"Missing Power BI credentials: {', '.join(missing)}"
            validation_result["errors"].append(error_msg)
            logger.error(f"✗ {error_msg}")
            return validation_result
        
        # Try to get access token
        token = await self.get_access_token()
        if token:
            validation_result["token_acquired"] = True
            logger.info("✓ Successfully acquired access token")
            
            # Try to access API
            try:
                workspaces = await self.get_user_workspaces(token)
                validation_result["api_accessible"] = True
                
                if workspaces:
                    validation_result["workspaces_accessible"] = True
                    validation_result["workspace_count"] = len(workspaces)
                    logger.info(f"✓ Found {len(workspaces)} accessible workspaces")
                else:
                    validation_result["warnings"].append("No workspaces accessible - grant app access to workspaces in Power BI Service")
                    validation_result["warnings"].append("To grant access: Go to workspace > Manage access > Add app with Viewer role")
                    logger.warning("⚠ No workspaces accessible")
                    
            except Exception as e:
                validation_result["errors"].append(f"API access error: {str(e)}")
                logger.error(f"✗ API access error: {str(e)}")
        else:
            validation_result["errors"].append("Failed to acquire access token - check credentials")
            logger.error("✗ Failed to acquire access token")
            
            # Add specific guidance
            validation_result["warnings"].append("Ensure app registration has correct API permissions (Workspace.Read.All, Dataset.Read.All)")
            validation_result["warnings"].append("Verify the client secret hasn't expired")
        
        # Summary
        if validation_result["workspaces_accessible"]:
            logger.info("✓ Power BI configuration is valid and working")
        else:
            logger.warning("⚠ Power BI configuration has issues - check errors and warnings")
        
        return validation_result
    
    def is_configured(self) -> bool:
        """Check if Power BI client is properly configured"""
        return self.configured and MSAL_AVAILABLE

# Create singleton instance
powerbi_client = PowerBIClient()

# Export
__all__ = ['PowerBIClient', 'powerbi_client', 'WorkspaceInfo', 'DatasetInfo', 'QueryResult']