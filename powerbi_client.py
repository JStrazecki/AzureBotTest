# powerbi_client.py - Power BI Authentication and API Client
"""
Power BI Client - Handles authentication and API calls to Power BI service
Fixed version with proper datetime handling and better error messages
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
            current_time = datetime.now()
            
            if cache_key in self.token_cache:
                cached_token = self.token_cache[cache_key]
                expires_at = cached_token.get("expires_at")
                
                # Handle both datetime and timestamp formats for backward compatibility
                if expires_at:
                    if isinstance(expires_at, (int, float)):
                        # Convert timestamp to datetime
                        expires_at_dt = datetime.fromtimestamp(expires_at)
                    elif isinstance(expires_at, datetime):
                        expires_at_dt = expires_at
                    else:
                        # Invalid format, get new token
                        logger.warning(f"Invalid expires_at format: {type(expires_at)}")
                        expires_at_dt = current_time
                    
                    # Check if token is still valid (with 5 minute buffer)
                    if expires_at_dt > current_time + timedelta(minutes=5):
                        logger.info("Using cached Power BI access token")
                        return cached_token["access_token"]
                    else:
                        logger.info("Cached token expired, acquiring new token")
            
            logger.info("Acquiring new Power BI access token...")
            
            # Get new token
            result = self.msal_app.acquire_token_for_client(scopes=self.credentials.scope)
            
            if "access_token" in result:
                # Cache the token with datetime object
                expires_in = result.get("expires_in", 3600)
                self.token_cache[cache_key] = {
                    "access_token": result["access_token"],
                    "expires_at": current_time + timedelta(seconds=expires_in)
                }
                logger.info(f"Successfully acquired Power BI access token (expires in {expires_in} seconds)")
                
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
                # Try to get group workspaces
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
                            workspace_name = ws.get('name', 'Unknown')
                            workspace_id = ws.get('id', 'Unknown')
                            workspace_state = ws.get('state', 'Active')
                            
                            logger.info(f"Found workspace: {workspace_name} (ID: {workspace_id[:8]}..., State: {workspace_state})")
                            
                            workspace = WorkspaceInfo(
                                id=workspace_id,
                                name=workspace_name,
                                description=ws.get("description"),
                                is_personal=ws.get("isPersonal", False),
                                capacity_id=ws.get("capacityId"),
                                type=ws.get("type", "Workspace"),
                                state=workspace_state
                            )
                            
                            # Only include active workspaces
                            if workspace_state == "Active":
                                workspaces.append(workspace)
                            else:
                                logger.info(f"Skipping inactive workspace: {workspace_name}")
                        
                        # Always try to check personal workspace (My Workspace)
                        logger.info("Checking for personal workspace access...")
                        try:
                            async with session.get(
                                f"{self.base_url}/datasets",
                                headers=headers,
                                timeout=aiohttp.ClientTimeout(total=10)
                            ) as dataset_response:
                                
                                if dataset_response.status == 200:
                                    dataset_data = await dataset_response.json()
                                    personal_datasets = dataset_data.get("value", [])
                                    
                                    if personal_datasets:
                                        logger.info(f"Found {len(personal_datasets)} datasets in personal workspace")
                                        # Add My Workspace if we found personal datasets
                                        personal_workspace = WorkspaceInfo(
                                            id="me",  # Special ID for personal workspace
                                            name="My Workspace",
                                            description="Personal workspace",
                                            is_personal=True,
                                            state="Active"
                                        )
                                        
                                        # Check if not already added
                                        if not any(ws.is_personal for ws in workspaces):
                                            workspaces.insert(0, personal_workspace)  # Add at beginning
                                            logger.info("Added My Workspace to available workspaces")
                                    else:
                                        logger.info("No datasets found in personal workspace")
                                elif dataset_response.status == 401:
                                    logger.warning("Unauthorized access to personal workspace datasets")
                                else:
                                    logger.warning(f"Could not check personal workspace: Status {dataset_response.status}")
                                    
                        except Exception as e:
                            logger.warning(f"Error checking personal workspace: {e}")
                        
                        logger.info(f"Total accessible workspaces: {len(workspaces)}")
                        
                        # Provide helpful messages if no workspaces found
                        if len(workspaces) == 0:
                            logger.warning("No workspaces found. Troubleshooting steps:")
                            logger.warning("1. Verify the app registration has Power BI API permissions:")
                            logger.warning("   - Workspace.Read.All")
                            logger.warning("   - Dataset.Read.All")
                            logger.warning("   - Dataset.ReadWrite.All (if writing)")
                            logger.warning("2. Grant the app access to specific workspaces:")
                            logger.warning("   - Log into Power BI Service (app.powerbi.com)")
                            logger.warning("   - Go to the workspace")
                            logger.warning("   - Click 'Manage access' or the access icon")
                            logger.warning("   - Click '+ Add people or groups'")
                            logger.warning("   - Search for your app name or use the Application ID")
                            logger.warning(f"   - Application ID: {self.credentials.client_id}")
                            logger.warning("   - Grant at least 'Viewer' role")
                            logger.warning("   - Click 'Add'")
                            logger.warning("3. Wait 1-2 minutes for permissions to propagate")
                            logger.warning("4. Try refreshing the page")
                        
                        return workspaces
                    
                    elif response.status == 401:
                        error_text = await response.text()
                        logger.error(f"Unauthorized access to workspaces API: {error_text}")
                        logger.error("The access token may be invalid or expired")
                        return []
                    
                    elif response.status == 403:
                        error_text = await response.text()
                        logger.error(f"Forbidden access to workspaces API: {error_text}")
                        logger.error("The app registration needs the following API permissions:")
                        logger.error("- Workspace.Read.All")
                        logger.error("- Dataset.Read.All")
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
                            dataset_name = ds.get('name', 'Unknown')
                            dataset_id = ds.get('id', 'Unknown')
                            
                            logger.info(f"Found dataset: {dataset_name} (ID: {dataset_id[:8]}...)")
                            
                            # Include all datasets (don't filter)
                            dataset = DatasetInfo(
                                id=dataset_id,
                                name=dataset_name,
                                workspace_id=workspace_id,
                                workspace_name=workspace_name or ("My Workspace" if workspace_id == "me" else workspace_name),
                                configured_by=ds.get("configuredBy"),
                                created_date=ds.get("createdDate"),
                                content_provider_type=ds.get("contentProviderType")
                            )
                            datasets.append(dataset)
                        
                        logger.info(f"Retrieved {len(datasets)} datasets from workspace {workspace_name}")
                        
                        if len(datasets) == 0:
                            logger.warning(f"No datasets found in workspace {workspace_name}")
                            logger.warning("Possible reasons:")
                            logger.warning("1. The workspace may be empty")
                            logger.warning("2. The app may not have Dataset.Read.All permission")
                            logger.warning("3. Datasets may be in a Premium capacity that requires additional permissions")
                        
                        return datasets
                    
                    elif response.status == 401:
                        error_text = await response.text()
                        logger.error(f"Unauthorized access to datasets in workspace {workspace_name}: {error_text}")
                        return []
                    
                    elif response.status == 403:
                        error_text = await response.text()
                        logger.error(f"Forbidden access to datasets in workspace {workspace_name}: {error_text}")
                        logger.error("The app needs at least 'Viewer' role in this workspace")
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
                "relationships": [],
                "dataset_id": dataset_id
            }
            
            # First, try to get dataset info
            async with aiohttp.ClientSession() as session:
                try:
                    # Get dataset details
                    async with session.get(
                        f"{self.base_url}/datasets/{dataset_id}",
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        
                        if response.status == 200:
                            dataset_info = await response.json()
                            metadata["name"] = dataset_info.get("name", "Unknown")
                            metadata["configured_by"] = dataset_info.get("configuredBy")
                            logger.info(f"Dataset name: {metadata['name']}")
                except Exception as e:
                    logger.warning(f"Could not get dataset info: {e}")
                
                # Try to get refresh history
                try:
                    async with session.get(
                        f"{self.base_url}/datasets/{dataset_id}/refreshes",
                        headers=headers,
                        params={"$top": 1},
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        
                        if response.status == 200:
                            refresh_data = await response.json()
                            if refresh_data.get("value"):
                                last_refresh = refresh_data["value"][0]
                                metadata["last_refresh"] = last_refresh.get("endTime")
                                metadata["refresh_status"] = last_refresh.get("status")
                                logger.info(f"Last refresh: {metadata['last_refresh']} - Status: {metadata['refresh_status']}")
                except Exception as e:
                    logger.warning(f"Could not get refresh history: {e}")
                
                # Try different approaches to get schema information
                # Approach 1: Try DISCOVER_SCHEMA query
                discover_query = "EVALUATE INFO.TABLES()"
                
                logger.info("Attempting to discover dataset schema...")
                result = await self.execute_dax_query(access_token, dataset_id, discover_query, "metadata")
                
                if result.success and result.data:
                    for item in result.data:
                        table_name = item.get("Name", item.get("TABLE_NAME", ""))
                        if table_name:
                            metadata["tables"].append({
                                "name": table_name,
                                "type": "Table"
                            })
                    logger.info(f"Discovered {len(metadata['tables'])} tables using INFO.TABLES()")
                else:
                    # Approach 2: Try a simpler query
                    logger.info("INFO.TABLES() failed, trying alternative approach...")
                    
                    # Just verify we can query the dataset
                    test_query = "EVALUATE ROW(\"Test\", 1)"
                    test_result = await self.execute_dax_query(access_token, dataset_id, test_query, "test")
                    
                    if test_result.success:
                        metadata["queryable"] = True
                        metadata["status"] = "accessible"
                        logger.info("Dataset is queryable")
                        
                        # Since we can't get schema, provide generic guidance
                        metadata["schema_discovery_failed"] = True
                        metadata["notes"] = [
                            "Dataset is accessible but schema discovery is not available",
                            "You can still run queries if you know the table and measure names",
                            "Common tables: 'Sales', 'Customer', 'Product', 'Date'",
                            "Common measures: '[Total Sales]', '[Total Revenue]', '[Customer Count]'"
                        ]
                    else:
                        metadata["queryable"] = False
                        metadata["status"] = "not_queryable"
                        metadata["error"] = test_result.error
                        logger.warning(f"Dataset is not queryable: {test_result.error}")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error fetching dataset metadata: {e}", exc_info=True)
            return {
                "error": str(e),
                "dataset_id": dataset_id,
                "status": "error"
            }
    
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
                                
                                # Convert rows to list of dictionaries if needed
                                formatted_rows = []
                                for row in rows:
                                    if isinstance(row, dict):
                                        formatted_rows.append(row)
                                    else:
                                        # Handle other row formats if necessary
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
                            # Check for errors in response
                            if "error" in data:
                                error_msg = self._extract_error_message(data)
                                logger.error(f"Query error: {error_msg}")
                                return QueryResult(
                                    success=False,
                                    error=error_msg,
                                    execution_time_ms=execution_time
                                )
                            else:
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
                            error=f"Dataset not found or not accessible",
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
        try:
            if "error" in error_data:
                error = error_data["error"]
                if isinstance(error, dict):
                    # Try different error message locations
                    if "message" in error:
                        return error["message"]
                    elif "pbi.error" in error:
                        pbi_error = error["pbi.error"]
                        if "details" in pbi_error and isinstance(pbi_error["details"], list) and len(pbi_error["details"]) > 0:
                            detail = pbi_error["details"][0]
                            if "detail" in detail and isinstance(detail["detail"], dict) and "value" in detail["detail"]:
                                return detail["detail"]["value"]
                        if "message" in pbi_error:
                            return pbi_error["message"]
                    elif "code" in error and "message" in error:
                        return f"{error['code']}: {error['message']}"
                else:
                    return str(error)
            
            # Fallback: return the entire error data as string
            return json.dumps(error_data)[:500]  # Limit length
            
        except Exception as e:
            logger.error(f"Error extracting error message: {e}")
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
        try:
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
                        validation_result["workspace_names"] = [ws.name for ws in workspaces[:5]]  # First 5
                        logger.info(f"✓ Found {len(workspaces)} accessible workspaces")
                        
                        # Log workspace names
                        for ws in workspaces[:5]:
                            logger.info(f"  - {ws.name} (Personal: {ws.is_personal})")
                        if len(workspaces) > 5:
                            logger.info(f"  ... and {len(workspaces) - 5} more")
                    else:
                        validation_result["warnings"].append("No workspaces accessible - see troubleshooting steps below")
                        validation_result["warnings"].append(f"App Client ID: {self.credentials.client_id}")
                        validation_result["warnings"].append("Grant this app access to workspaces in Power BI Service")
                        logger.warning("⚠ No workspaces accessible")
                        
                except Exception as e:
                    validation_result["errors"].append(f"API access error: {str(e)}")
                    logger.error(f"✗ API access error: {str(e)}")
            else:
                validation_result["errors"].append("Failed to acquire access token - check credentials and permissions")
                logger.error("✗ Failed to acquire access token")
                
        except Exception as e:
            validation_result["errors"].append(f"Token acquisition error: {str(e)}")
            logger.error(f"✗ Token acquisition error: {str(e)}")
        
        # Add guidance
        if not validation_result["workspaces_accessible"]:
            validation_result["troubleshooting"] = [
                "1. Ensure app registration has API permissions:",
                "   - Workspace.Read.All",
                "   - Dataset.Read.All",
                "   - Dataset.ReadWrite.All (optional)",
                "2. Grant admin consent for the permissions",
                "3. Add the app to Power BI workspaces:",
                "   - Log into app.powerbi.com",
                "   - Go to your workspace",
                "   - Click 'Manage access'",
                "   - Add the app with Viewer or higher role",
                f"   - App Client ID: {self.credentials.client_id}",
                "4. Wait 1-2 minutes and try again"
            ]
        
        # Summary
        if validation_result["workspaces_accessible"]:
            logger.info("✓ Power BI configuration is valid and working")
        else:
            logger.warning("⚠ Power BI configuration needs attention - check errors and warnings")
        
        return validation_result
    
    def is_configured(self) -> bool:
        """Check if Power BI client is properly configured"""
        return self.configured and MSAL_AVAILABLE

# Create singleton instance
powerbi_client = PowerBIClient()

# Export
__all__ = ['PowerBIClient', 'powerbi_client', 'WorkspaceInfo', 'DatasetInfo', 'QueryResult']