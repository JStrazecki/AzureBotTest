# sql_translator_simple.py - Simple Azure OpenAI SQL Translator
"""
Simple SQL Translator using Azure OpenAI
Focused on basic natural language to SQL translation
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from openai import AzureOpenAI

logger = logging.getLogger(__name__)

@dataclass
class SQLQuery:
    """Represents a translated SQL query"""
    query: str
    database: str
    explanation: str
    confidence: float
    error: Optional[str] = None

class SimpleSQLTranslator:
    """Simple SQL translator using Azure OpenAI"""
    
    def __init__(self):
        self.endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
        self.api_key = os.environ.get("AZURE_OPENAI_API_KEY", "")
        self.deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini")
        
        if not self.endpoint or not self.api_key:
            raise ValueError("Azure OpenAI endpoint and API key must be set")
        
        self.client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version="2024-02-01"
        )
        
        self.system_prompt = """You are an expert SQL translator for Microsoft SQL Server (T-SQL).
Convert natural language questions into T-SQL queries.

Rules:
1. ONLY generate SELECT queries - never generate INSERT, UPDATE, DELETE, DROP, or any DDL/DML commands
2. Always validate that queries are read-only
3. Use proper T-SQL syntax (TOP instead of LIMIT, GETDATE() for current time)
4. Quote identifiers with square brackets if they contain spaces or special characters
5. Add appropriate WHERE clauses to prevent full table scans on large tables
6. For "show tables" commands, use: EXEC sp_tables @table_type = "'TABLE'"
7. For "show columns" or "describe table", use INFORMATION_SCHEMA.COLUMNS
8. When asked about columns in a table, generate appropriate SELECT query

QUERY GUIDELINES:
1. For counting: Use COUNT(*) or COUNT(DISTINCT column)
2. For aggregations: Include appropriate GROUP BY clauses
3. For large tables: Always use TOP to limit results unless specifically asked for all
4. For date ranges: Use proper date functions and consider indexes
5. For joins: Prefer INNER JOIN unless outer joins are specifically needed
6. Always explain what the query does and why you structured it that way

Special Commands:
- "show tables" → EXEC sp_tables @table_type = "'TABLE'"
- "show columns in [table]" → SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '[table]'
- "describe [table]" → SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '[table]'

RESPONSE FORMAT:
Always respond with a JSON object containing:
{
    "query": "the SQL query",
    "database": "target database name or 'master'",
    "explanation": "detailed explanation of what this query does",
    "confidence": 0.0-1.0
}"""

    async def translate_to_sql(self, 
                             user_query: str, 
                             database: str = "master",
                             schema_context: Optional[str] = None) -> SQLQuery:
        """Translate natural language to SQL"""
        try:
            # Build the user message
            user_message = f"Database: {database}\n"
            if schema_context:
                user_message += f"{schema_context}\n"
            user_message += f"Question: {user_query}"
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=0.1,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Ensure the query is properly formatted
            query = result.get("query", "").strip()
            
            # Handle common natural language patterns
            if user_query.lower().startswith("show columns in"):
                # Extract table name
                table_name = user_query.lower().replace("show columns in", "").strip()
                # Remove "table" word if present
                table_name = table_name.replace("table", "").strip()
                # Remove database reference if present
                if " in " in table_name:
                    parts = table_name.split(" in ")
                    table_name = parts[0].strip()
                
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
                """.strip()
                
                result["query"] = query
                result["explanation"] = f"Show column information for table {table_name}"
            
            return SQLQuery(
                query=query,
                database=result.get("database", database),
                explanation=result.get("explanation", ""),
                confidence=float(result.get("confidence", 0.8))
            )
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return SQLQuery(
                query="",
                database=database,
                explanation=f"Error: {str(e)}",
                confidence=0.0,
                error=str(e)
            )