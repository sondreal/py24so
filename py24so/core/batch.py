from typing import Any, Dict, List, Optional, TypeVar, Union

import httpx

T = TypeVar("T")


class BatchRequest:
    """
    Handles batching of API requests.
    
    This class collects multiple API requests and sends them as a single batch request
    to improve performance and reduce API calls.
    """

    def __init__(self, max_batch_size: int = 20):
        """
        Initialize a batch request.
        
        Args:
            max_batch_size: Maximum number of requests in a batch
        """
        self.max_batch_size = max_batch_size
        self.requests: List[Dict[str, Any]] = []
        self.request_ids: List[str] = []
        
    def add(
        self, 
        method: str,
        path: str,
        request_id: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """
        Add a request to the batch.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: API endpoint path
            request_id: Optional identifier for the request
            **kwargs: Additional request parameters
            
        Returns:
            Request ID for tracking the response
            
        Raises:
            ValueError: If batch is full
        """
        if len(self.requests) >= self.max_batch_size:
            raise ValueError(f"Batch is full (max size: {self.max_batch_size})")
            
        if request_id is None:
            request_id = f"req_{len(self.requests)}"
            
        request = {
            "id": request_id,
            "method": method.upper(),
            "path": path,
        }
        
        # Add body if available
        if "json" in kwargs:
            request["body"] = kwargs["json"]
        elif "data" in kwargs:
            request["body"] = kwargs["data"]
            
        # Add query parameters if available
        if "params" in kwargs:
            request["query_params"] = kwargs["params"]
            
        self.requests.append(request)
        self.request_ids.append(request_id)
        return request_id
        
    def clear(self) -> None:
        """Clear all requests in the batch."""
        self.requests = []
        self.request_ids = []
        
    def is_empty(self) -> bool:
        """
        Check if the batch is empty.
        
        Returns:
            True if the batch has no requests
        """
        return len(self.requests) == 0
        
    def is_full(self) -> bool:
        """
        Check if the batch is full.
        
        Returns:
            True if the batch has reached max_batch_size
        """
        return len(self.requests) >= self.max_batch_size
        
    def prepare_request(self) -> Dict[str, Any]:
        """
        Prepare the batch request payload.
        
        Returns:
            Dictionary containing the batch request payload
        """
        return {"requests": self.requests}
        
        
class BatchResponse:
    """
    Handles responses from a batch request.
    
    This class processes the response from a batch API request and provides
    methods to access individual response data.
    """
    
    def __init__(self, response: httpx.Response, request_ids: List[str]):
        """
        Initialize a batch response.
        
        Args:
            response: HTTP response from the API
            request_ids: List of request IDs in the batch
        """
        self.raw_response = response
        self.request_ids = request_ids
        self.responses: Dict[str, Dict[str, Any]] = {}
        
        # Parse the response
        try:
            response_data = response.json()
            responses = response_data.get("responses", [])
            
            for resp in responses:
                req_id = resp.get("id")
                if req_id:
                    self.responses[req_id] = resp
        except (ValueError, AttributeError):
            # Handle invalid response format
            pass
            
    def get_response(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an individual response by request ID.
        
        Args:
            request_id: The ID of the request
            
        Returns:
            Response data or None if not found
        """
        return self.responses.get(request_id)
        
    def get_all_responses(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all responses.
        
        Returns:
            Dictionary mapping request IDs to response data
        """
        return self.responses
        
    def get_status_code(self, request_id: str) -> Optional[int]:
        """
        Get the status code for a specific request.
        
        Args:
            request_id: The ID of the request
            
        Returns:
            HTTP status code or None if not found
        """
        response = self.get_response(request_id)
        return response.get("status") if response else None
        
    def get_body(self, request_id: str) -> Optional[Any]:
        """
        Get the response body for a specific request.
        
        Args:
            request_id: The ID of the request
            
        Returns:
            Response body or None if not found
        """
        response = self.get_response(request_id)
        return response.get("body") if response else None
        
    def is_successful(self, request_id: str) -> bool:
        """
        Check if a specific request was successful.
        
        Args:
            request_id: The ID of the request
            
        Returns:
            True if the status code is between 200 and 299
        """
        status_code = self.get_status_code(request_id)
        return status_code is not None and 200 <= status_code < 300
        
    def all_successful(self) -> bool:
        """
        Check if all requests were successful.
        
        Returns:
            True if all requests have status codes between 200 and 299
        """
        return all(self.is_successful(req_id) for req_id in self.request_ids) 