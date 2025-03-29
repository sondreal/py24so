from typing import Dict, List, Optional, Union, Any, cast

import httpx

from py24so.core.batch import BatchRequest
from py24so.core.client import APIClient, AsyncAPIClient
from py24so.core.exceptions import NotFoundError
from py24so.models.customer import Customer, CustomerCreate, CustomerUpdate


class CustomerEndpoint:
    """
    Customer endpoint for the 24SevenOffice API.
    
    This class provides methods for working with customers in the API.
    """
    
    def __init__(self, client: APIClient):
        """
        Initialize the customer endpoint.
        
        Args:
            client: API client
        """
        self.client = client
        self.base_path = "/customers"
        
    def list(
        self,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Customer]:
        """
        List customers.
        
        Args:
            page: Page number
            page_size: Number of items per page
            search: Search query
            **kwargs: Additional query parameters
            
        Returns:
            List of customers
        """
        params = {
            "page": page,
            "pageSize": page_size,
            **kwargs,
        }
        
        if search:
            params["search"] = search
            
        response = self.client.get(self.base_path, params=params)
        return self.client.parse_response_list(response, Customer)
        
    def get(self, customer_id: str) -> Customer:
        """
        Get a customer by ID.
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Customer
            
        Raises:
            NotFoundError: If the customer is not found
        """
        response = self.client.get(f"{self.base_path}/{customer_id}")
        return self.client.parse_response(response, Customer)
        
    def create(self, customer: Union[Dict[str, Any], CustomerCreate]) -> Customer:
        """
        Create a new customer.
        
        Args:
            customer: Customer data
            
        Returns:
            Created customer
        """
        if isinstance(customer, CustomerCreate):
            data = customer.model_dump(exclude_unset=True)
        else:
            data = customer
            
        response = self.client.post(self.base_path, json=data)
        return self.client.parse_response(response, Customer)
        
    def update(
        self,
        customer_id: str,
        customer: Union[Dict[str, Any], CustomerUpdate],
    ) -> Customer:
        """
        Update a customer.
        
        Args:
            customer_id: Customer ID
            customer: Customer data
            
        Returns:
            Updated customer
            
        Raises:
            NotFoundError: If the customer is not found
        """
        if isinstance(customer, CustomerUpdate):
            data = customer.model_dump(exclude_unset=True, exclude_none=True)
        else:
            data = customer
            
        response = self.client.patch(f"{self.base_path}/{customer_id}", json=data)
        return self.client.parse_response(response, Customer)
        
    def delete(self, customer_id: str) -> None:
        """
        Delete a customer.
        
        Args:
            customer_id: Customer ID
            
        Raises:
            NotFoundError: If the customer is not found
        """
        response = self.client.delete(f"{self.base_path}/{customer_id}")
        if response.status_code != 204:
            # If not 204 No Content, then parse the response
            self.client.parse_response(response, dict)
            
    def batch_get(self, customer_ids: List[str]) -> Dict[str, Customer]:
        """
        Get multiple customers in a single batch request.
        
        Args:
            customer_ids: List of customer IDs
            
        Returns:
            Dictionary mapping customer IDs to customer objects
        """
        batch = BatchRequest()
        
        for customer_id in customer_ids:
            batch.add(
                method="GET",
                path=f"{self.base_path}/{customer_id}",
                request_id=customer_id,
            )
            
        batch_response = self.client.send_batch_request(batch)
        
        # Process the responses
        customers: Dict[str, Customer] = {}
        for customer_id in customer_ids:
            if batch_response.is_successful(customer_id):
                body = batch_response.get_body(customer_id)
                if body:
                    customers[customer_id] = Customer.model_validate(body)
                    
        return customers


class AsyncCustomerEndpoint:
    """
    Asynchronous customer endpoint for the 24SevenOffice API.
    
    This class provides asynchronous methods for working with customers in the API.
    """
    
    def __init__(self, client: AsyncAPIClient):
        """
        Initialize the async customer endpoint.
        
        Args:
            client: Async API client
        """
        self.client = client
        self.base_path = "/customers"
        
    async def list(
        self,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Customer]:
        """
        List customers asynchronously.
        
        Args:
            page: Page number
            page_size: Number of items per page
            search: Search query
            **kwargs: Additional query parameters
            
        Returns:
            List of customers
        """
        params = {
            "page": page,
            "pageSize": page_size,
            **kwargs,
        }
        
        if search:
            params["search"] = search
            
        response = await self.client.get(self.base_path, params=params)
        return await self.client.parse_response_list(response, Customer)
        
    async def get(self, customer_id: str) -> Customer:
        """
        Get a customer by ID asynchronously.
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Customer
            
        Raises:
            NotFoundError: If the customer is not found
        """
        response = await self.client.get(f"{self.base_path}/{customer_id}")
        return await self.client.parse_response(response, Customer)
        
    async def create(self, customer: Union[Dict[str, Any], CustomerCreate]) -> Customer:
        """
        Create a new customer asynchronously.
        
        Args:
            customer: Customer data
            
        Returns:
            Created customer
        """
        if isinstance(customer, CustomerCreate):
            data = customer.model_dump(exclude_unset=True)
        else:
            data = customer
            
        response = await self.client.post(self.base_path, json=data)
        return await self.client.parse_response(response, Customer)
        
    async def update(
        self,
        customer_id: str,
        customer: Union[Dict[str, Any], CustomerUpdate],
    ) -> Customer:
        """
        Update a customer asynchronously.
        
        Args:
            customer_id: Customer ID
            customer: Customer data
            
        Returns:
            Updated customer
            
        Raises:
            NotFoundError: If the customer is not found
        """
        if isinstance(customer, CustomerUpdate):
            data = customer.model_dump(exclude_unset=True, exclude_none=True)
        else:
            data = customer
            
        response = await self.client.patch(f"{self.base_path}/{customer_id}", json=data)
        return await self.client.parse_response(response, Customer)
        
    async def delete(self, customer_id: str) -> None:
        """
        Delete a customer asynchronously.
        
        Args:
            customer_id: Customer ID
            
        Raises:
            NotFoundError: If the customer is not found
        """
        response = await self.client.delete(f"{self.base_path}/{customer_id}")
        if response.status_code != 204:
            # If not 204 No Content, then parse the response
            await self.client.parse_response(response, dict)
            
    async def batch_get(self, customer_ids: List[str]) -> Dict[str, Customer]:
        """
        Get multiple customers in a single batch request asynchronously.
        
        Args:
            customer_ids: List of customer IDs
            
        Returns:
            Dictionary mapping customer IDs to customer objects
        """
        batch = BatchRequest()
        
        for customer_id in customer_ids:
            batch.add(
                method="GET",
                path=f"{self.base_path}/{customer_id}",
                request_id=customer_id,
            )
            
        batch_response = await self.client.send_batch_request(batch)
        
        # Process the responses
        customers: Dict[str, Customer] = {}
        for customer_id in customer_ids:
            if batch_response.is_successful(customer_id):
                body = batch_response.get_body(customer_id)
                if body:
                    customers[customer_id] = Customer.model_validate(body)
                    
        return customers 