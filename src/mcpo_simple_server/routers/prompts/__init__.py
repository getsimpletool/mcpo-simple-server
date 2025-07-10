"""
Package/Module: Prompts Router - Prompt management endpoints

High Level Concept:
-------------------
The Prompts Router provides endpoints for managing and accessing prompts within the
MCPoSimpleServer. It enables the creation, retrieval, updating, and deletion of
prompt templates that can be used with MCP tools, supporting both public shared
prompts and user-specific private prompts.

Architecture:
-------------
- CRUD operations for prompt management
- Support for both public and private prompts
- Structured prompt templates with metadata
- Integration with the prompt manager service

Endpoints:
----------
* /prompts - Prompt management endpoints
  - GET /prompts - List all available prompts (public or user-specific)
  - GET /prompts/{prompt_id} - Get a specific prompt by ID
  - POST /prompts - Create a new prompt
  - PUT /prompts/{prompt_id} - Update an existing prompt
  - DELETE /prompts/{prompt_id} - Delete a prompt

Workflow:
---------
1. Requests are routed to specialized handlers based on the operation type:
   * GET /prompts - List all available prompts (public or user-specific)
   * GET /prompts/{prompt_id} - Get a specific prompt by ID
   * POST /prompts - Create a new prompt
   * PUT /prompts/{prompt_id} - Update an existing prompt
   * DELETE /prompts/{prompt_id} - Delete a prompt

2. Authentication and authorization is handled differently based on prompt type:
   * Public prompts are accessible without authentication
   * Private prompts require user authentication and ownership verification

3. Prompt operations are executed through the prompt manager service

4. Results are returned with standardized response formats

Notes:
------
- Prompts are stored in a structured format with content and metadata
- Public prompts are shared across all users of the system
- Private prompts are only accessible to their owners
- Prompts can be used as templates for MCP tool interactions
- The system supports versioning and tagging of prompts
"""
from fastapi import APIRouter

router = APIRouter(prefix="/prompts", tags=["Prompts"])

# Import handlers to register routes
from . import handlers  # noqa: F401, E402
