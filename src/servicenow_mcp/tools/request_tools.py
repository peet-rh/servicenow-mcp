"""
Request tools for the ServiceNow MCP server.

This module provides tools for reading service catalog requests (sc_request)
and requested items (sc_req_item) in ServiceNow.
"""

import logging
from typing import Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)


class GetUniversalRequestParams(BaseModel):
    """Parameters for fetching a Universal Request by its UR number."""

    request_number: str = Field(..., description="The UR number to fetch (e.g. UR0118585)")


class GetRequestByNumberParams(BaseModel):
    """Parameters for fetching a request by its number."""

    request_number: str = Field(..., description="The number of the request to fetch (e.g. UR0148393)")


class ListRequestsParams(BaseModel):
    """Parameters for listing requests."""

    limit: int = Field(10, description="Maximum number of requests to return")
    offset: int = Field(0, description="Offset for pagination")
    state: Optional[str] = Field(None, description="Filter by request state")
    requested_for: Optional[str] = Field(None, description="Filter by requested_for user")
    query: Optional[str] = Field(None, description="Search query for requests")


class GetRequestItemByNumberParams(BaseModel):
    """Parameters for fetching a requested item by its number."""

    item_number: str = Field(..., description="The number of the requested item to fetch (e.g. RITM0123456)")


class ListRequestItemsParams(BaseModel):
    """Parameters for listing requested items for a request."""

    request_number: Optional[str] = Field(None, description="Filter by parent request number")
    limit: int = Field(10, description="Maximum number of items to return")
    offset: int = Field(0, description="Offset for pagination")
    state: Optional[str] = Field(None, description="Filter by item state")
    query: Optional[str] = Field(None, description="Search query for requested items")


class GetCatalogTaskByNumberParams(BaseModel):
    """Parameters for fetching a catalog task (CTASK) by its number."""

    task_number: str = Field(..., description="The number of the catalog task to fetch (e.g. CTASK0123456)")


class ListCatalogTasksParams(BaseModel):
    """Parameters for listing catalog tasks (sc_task), e.g. fulfillment tasks under a RITM."""

    request_item_number: Optional[str] = Field(None, description="Filter by parent requested item number (e.g. RITM0123456)")
    limit: int = Field(10, description="Maximum number of tasks to return")
    offset: int = Field(0, description="Offset for pagination")
    state: Optional[str] = Field(None, description="Filter by task state")
    query: Optional[str] = Field(None, description="Search query for catalog tasks")


def get_universal_request(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetUniversalRequestParams,
) -> dict:
    """Fetch a Universal Request from the task table by its UR number."""
    api_url = f"{config.api_url}/table/task"

    query_params = {
        "sysparm_query": f"number={params.request_number}^sys_class_name=Universal Request",
        "sysparm_limit": 1,
        "sysparm_display_value": "true",
        "sysparm_exclude_reference_link": "true",
    }

    try:
        response = requests.get(
            api_url,
            params=query_params,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        data = response.json()
        result = data.get("result", [])

        if not result:
            return {
                "success": False,
                "message": f"Universal Request not found: {params.request_number}",
            }

        req_data = result[0]

        def _display(field):
            val = req_data.get(field)
            if isinstance(val, dict):
                return val.get("display_value")
            return val

        request_record = {
            "sys_id": req_data.get("sys_id"),
            "number": req_data.get("number"),
            "short_description": req_data.get("short_description"),
            "description": req_data.get("description"),
            "state": req_data.get("state"),
            "priority": req_data.get("priority"),
            "impact": req_data.get("impact"),
            "urgency": req_data.get("urgency"),
            "opened_by": _display("opened_by"),
            "opened_at": req_data.get("opened_at"),
            "assigned_to": _display("assigned_to"),
            "assignment_group": _display("assignment_group"),
            "closed_at": req_data.get("closed_at"),
            "closed_by": _display("closed_by"),
            "close_notes": req_data.get("close_notes"),
            "approval": req_data.get("approval"),
            "work_notes": req_data.get("work_notes"),
            "comments": req_data.get("comments"),
            "created_on": req_data.get("sys_created_on"),
            "updated_on": req_data.get("sys_updated_on"),
        }

        return {
            "success": True,
            "message": f"Universal Request {params.request_number} found",
            "request": request_record,
        }

    except requests.RequestException as e:
        logger.error(f"Failed to fetch universal request: {e}")
        return {
            "success": False,
            "message": f"Failed to fetch universal request: {str(e)}",
        }


def get_request_by_number(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetRequestByNumberParams,
) -> dict:
    """Fetch a single service catalog request from ServiceNow by its number."""
    api_url = f"{config.api_url}/table/sc_request"

    query_params = {
        "sysparm_query": f"number={params.request_number}",
        "sysparm_limit": 1,
        "sysparm_display_value": "true",
        "sysparm_exclude_reference_link": "true",
    }

    try:
        response = requests.get(
            api_url,
            params=query_params,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        data = response.json()
        result = data.get("result", [])

        if not result:
            return {
                "success": False,
                "message": f"Request not found: {params.request_number}",
            }

        req_data = result[0]

        def _display(field):
            val = req_data.get(field)
            if isinstance(val, dict):
                return val.get("display_value")
            return val

        request_record = {
            "sys_id": req_data.get("sys_id"),
            "number": req_data.get("number"),
            "short_description": req_data.get("short_description"),
            "description": req_data.get("description"),
            "state": _display("request_state") or req_data.get("request_state"),
            "stage": _display("stage"),
            "priority": req_data.get("priority"),
            "requested_for": _display("requested_for"),
            "opened_by": _display("opened_by"),
            "assigned_to": _display("assigned_to"),
            "assignment_group": _display("assignment_group"),
            "approval": req_data.get("approval"),
            "created_on": req_data.get("sys_created_on"),
            "updated_on": req_data.get("sys_updated_on"),
            "closed_at": req_data.get("closed_at"),
        }

        return {
            "success": True,
            "message": f"Request {params.request_number} found",
            "request": request_record,
        }

    except requests.RequestException as e:
        logger.error(f"Failed to fetch request: {e}")
        return {
            "success": False,
            "message": f"Failed to fetch request: {str(e)}",
        }


def list_requests(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListRequestsParams,
) -> dict:
    """List service catalog requests from ServiceNow."""
    api_url = f"{config.api_url}/table/sc_request"

    query_params = {
        "sysparm_limit": params.limit,
        "sysparm_offset": params.offset,
        "sysparm_display_value": "true",
        "sysparm_exclude_reference_link": "true",
    }

    filters = []
    if params.state:
        filters.append(f"request_state={params.state}")
    if params.requested_for:
        filters.append(f"requested_for={params.requested_for}")
    if params.query:
        filters.append(f"short_descriptionLIKE{params.query}^ORdescriptionLIKE{params.query}")

    if filters:
        query_params["sysparm_query"] = "^".join(filters)

    try:
        response = requests.get(
            api_url,
            params=query_params,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        data = response.json()
        results = []

        for req_data in data.get("result", []):
            def _display(field, d=req_data):
                val = d.get(field)
                if isinstance(val, dict):
                    return val.get("display_value")
                return val

            results.append({
                "sys_id": req_data.get("sys_id"),
                "number": req_data.get("number"),
                "short_description": req_data.get("short_description"),
                "state": _display("request_state") or req_data.get("request_state"),
                "priority": req_data.get("priority"),
                "requested_for": _display("requested_for"),
                "assigned_to": _display("assigned_to"),
                "created_on": req_data.get("sys_created_on"),
                "updated_on": req_data.get("sys_updated_on"),
            })

        return {
            "success": True,
            "message": f"Found {len(results)} requests",
            "requests": results,
        }

    except requests.RequestException as e:
        logger.error(f"Failed to list requests: {e}")
        return {
            "success": False,
            "message": f"Failed to list requests: {str(e)}",
            "requests": [],
        }


def get_request_item_by_number(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetRequestItemByNumberParams,
) -> dict:
    """Fetch a single requested item (RITM) from ServiceNow by its number."""
    api_url = f"{config.api_url}/table/sc_req_item"

    query_params = {
        "sysparm_query": f"number={params.item_number}",
        "sysparm_limit": 1,
        "sysparm_display_value": "true",
        "sysparm_exclude_reference_link": "true",
    }

    try:
        response = requests.get(
            api_url,
            params=query_params,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        data = response.json()
        result = data.get("result", [])

        if not result:
            return {
                "success": False,
                "message": f"Requested item not found: {params.item_number}",
            }

        item_data = result[0]

        def _display(field):
            val = item_data.get(field)
            if isinstance(val, dict):
                return val.get("display_value")
            return val

        item_record = {
            "sys_id": item_data.get("sys_id"),
            "number": item_data.get("number"),
            "short_description": item_data.get("short_description"),
            "description": item_data.get("description"),
            "state": _display("state"),
            "stage": _display("stage"),
            "priority": item_data.get("priority"),
            "request": _display("request"),
            "cat_item": _display("cat_item"),
            "requested_for": _display("requested_for"),
            "opened_by": _display("opened_by"),
            "assigned_to": _display("assigned_to"),
            "assignment_group": _display("assignment_group"),
            "approval": item_data.get("approval"),
            "created_on": item_data.get("sys_created_on"),
            "updated_on": item_data.get("sys_updated_on"),
            "closed_at": item_data.get("closed_at"),
        }

        return {
            "success": True,
            "message": f"Requested item {params.item_number} found",
            "item": item_record,
        }

    except requests.RequestException as e:
        logger.error(f"Failed to fetch requested item: {e}")
        return {
            "success": False,
            "message": f"Failed to fetch requested item: {str(e)}",
        }


def list_request_items(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListRequestItemsParams,
) -> dict:
    """List requested items from ServiceNow, optionally filtered by parent request."""
    api_url = f"{config.api_url}/table/sc_req_item"

    query_params = {
        "sysparm_limit": params.limit,
        "sysparm_offset": params.offset,
        "sysparm_display_value": "true",
        "sysparm_exclude_reference_link": "true",
    }

    filters = []
    if params.request_number:
        filters.append(f"request.number={params.request_number}")
    if params.state:
        filters.append(f"state={params.state}")
    if params.query:
        filters.append(f"short_descriptionLIKE{params.query}^ORdescriptionLIKE{params.query}")

    if filters:
        query_params["sysparm_query"] = "^".join(filters)

    try:
        response = requests.get(
            api_url,
            params=query_params,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        data = response.json()
        items = []

        for item_data in data.get("result", []):
            def _display(field, d=item_data):
                val = d.get(field)
                if isinstance(val, dict):
                    return val.get("display_value")
                return val

            items.append({
                "sys_id": item_data.get("sys_id"),
                "number": item_data.get("number"),
                "short_description": item_data.get("short_description"),
                "state": _display("state"),
                "request": _display("request"),
                "cat_item": _display("cat_item"),
                "requested_for": _display("requested_for"),
                "assigned_to": _display("assigned_to"),
                "created_on": item_data.get("sys_created_on"),
                "updated_on": item_data.get("sys_updated_on"),
            })

        return {
            "success": True,
            "message": f"Found {len(items)} requested items",
            "items": items,
        }

    except requests.RequestException as e:
        logger.error(f"Failed to list requested items: {e}")
        return {
            "success": False,
            "message": f"Failed to list requested items: {str(e)}",
            "items": [],
        }


def get_catalog_task_by_number(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetCatalogTaskByNumberParams,
) -> dict:
    """Fetch a single catalog task (CTASK) from ServiceNow by its number."""
    api_url = f"{config.api_url}/table/sc_task"

    query_params = {
        "sysparm_query": f"number={params.task_number}",
        "sysparm_limit": 1,
        "sysparm_display_value": "true",
        "sysparm_exclude_reference_link": "true",
    }

    try:
        response = requests.get(
            api_url,
            params=query_params,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        data = response.json()
        result = data.get("result", [])

        if not result:
            return {
                "success": False,
                "message": f"Catalog task not found: {params.task_number}",
            }

        task_data = result[0]

        def _display(field):
            val = task_data.get(field)
            if isinstance(val, dict):
                return val.get("display_value")
            return val

        task_record = {
            "sys_id": task_data.get("sys_id"),
            "number": task_data.get("number"),
            "short_description": task_data.get("short_description"),
            "description": task_data.get("description"),
            "state": _display("state"),
            "priority": task_data.get("priority"),
            "request_item": _display("request_item"),
            "requested_for": _display("requested_for"),
            "opened_by": _display("opened_by"),
            "assigned_to": _display("assigned_to"),
            "assignment_group": _display("assignment_group"),
            "comments": task_data.get("comments"),
            "work_notes": task_data.get("work_notes"),
            "created_on": task_data.get("sys_created_on"),
            "updated_on": task_data.get("sys_updated_on"),
            "closed_at": task_data.get("closed_at"),
        }

        return {
            "success": True,
            "message": f"Catalog task {params.task_number} found",
            "task": task_record,
        }

    except requests.RequestException as e:
        logger.error(f"Failed to fetch catalog task: {e}")
        return {
            "success": False,
            "message": f"Failed to fetch catalog task: {str(e)}",
        }


def list_catalog_tasks(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListCatalogTasksParams,
) -> dict:
    """List catalog tasks (sc_task) from ServiceNow, e.g. fulfillment tasks under a RITM."""
    api_url = f"{config.api_url}/table/sc_task"

    query_params = {
        "sysparm_limit": params.limit,
        "sysparm_offset": params.offset,
        "sysparm_display_value": "true",
        "sysparm_exclude_reference_link": "true",
    }

    filters = []
    if params.request_item_number:
        filters.append(f"request_item.number={params.request_item_number}")
    if params.state:
        filters.append(f"state={params.state}")
    if params.query:
        filters.append(f"short_descriptionLIKE{params.query}^ORdescriptionLIKE{params.query}")

    if filters:
        query_params["sysparm_query"] = "^".join(filters)

    try:
        response = requests.get(
            api_url,
            params=query_params,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        data = response.json()
        tasks = []

        for task_data in data.get("result", []):
            def _display(field, d=task_data):
                val = d.get(field)
                if isinstance(val, dict):
                    return val.get("display_value")
                return val

            tasks.append({
                "sys_id": task_data.get("sys_id"),
                "number": task_data.get("number"),
                "short_description": task_data.get("short_description"),
                "state": _display("state"),
                "request_item": _display("request_item"),
                "assigned_to": _display("assigned_to"),
                "assignment_group": _display("assignment_group"),
                "comments": task_data.get("comments"),
                "work_notes": task_data.get("work_notes"),
                "created_on": task_data.get("sys_created_on"),
                "updated_on": task_data.get("sys_updated_on"),
            })

        return {
            "success": True,
            "message": f"Found {len(tasks)} catalog tasks",
            "tasks": tasks,
        }

    except requests.RequestException as e:
        logger.error(f"Failed to list catalog tasks: {e}")
        return {
            "success": False,
            "message": f"Failed to list catalog tasks: {str(e)}",
            "tasks": [],
        }
