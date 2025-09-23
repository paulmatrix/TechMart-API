# TechMart API Documentation

## Overview

TechMart API is a Django REST Framework-based backend service for an electronics store. It provides comprehensive CRUD operations for managing customers, categories, products, and orders with hierarchical category support using django-mptt.

## Base URL

```
http://localhost:8001/api/v1/
```

## Authentication

The API uses Token Authentication. Include the token in the Authorization header:

```
Authorization: Token your_token_here
```

## API Endpoints

### 1. Categories

#### List Categories
```
GET /api/v1/categories/
```

**Query Parameters:**
- `is_active` (boolean): Filter by active status
- `parent` (integer): Filter by parent category ID (use 'null' for root categories)
- `search` (string): Search by category name

**Response:**
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Electronics",
      "slug": "electronics",
      "parent": null,
      "parent_name": null,
      "is_active": true,
      "product_count": 3,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### Get Category Details
```
GET /api/v1/categories/{id}/
```

**Response:**
```json
{
  "id": 1,
  "name": "Electronics",
  "slug": "electronics",
  "description": "Electronic devices and gadgets",
  "parent": null,
  "parent_name": null,
  "is_active": true,
  "children": [
    {
      "id": 2,
      "name": "Phones",
      "slug": "phones",
      "description": "Mobile phones and accessories",
      "parent": 1,
      "parent_name": "Electronics",
      "is_active": true,
      "children": [...],
      "product_count": 2,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "product_count": 3,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### Create Category
```
POST /api/v1/categories/
```

**Request Body:**
```json
{
  "name": "Tablets",
  "description": "Tablet devices",
  "parent": 1
}
```

#### Get Category Tree
```
GET /api/v1/categories/tree/
```

Returns the complete category hierarchy starting from root categories.

#### Get Category Average Price
```
GET /api/v1/categories/{id}/average_price/
```

**Response:**
```json
{
  "category_id": 1,
  "category_name": "Electronics",
  "average_price": "1299.99",
  "product_count": 3,
  "descendant_categories": ["Electronics", "Phones", "Smartphones"]
}
```

### 2. Products

#### List Products
```
GET /api/v1/products/
```

**Query Parameters:**
- `is_active` (boolean): Filter by active status
- `category` (integer): Filter by category ID
- `in_stock` (boolean): Filter by stock availability
- `min_price` (decimal): Minimum price filter
- `max_price` (decimal): Maximum price filter
- `search` (string): Search by name or SKU

**Response:**
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "iPhone 15",
      "sku": "IPH15-128",
      "description": "Latest iPhone model",
      "category": 3,
      "category_name": "Smartphones",
      "price": "999.99",
      "stock_quantity": 10,
      "is_active": true,
      "is_in_stock": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### Get Product Details
```
GET /api/v1/products/{id}/
```

#### Create Product
```
POST /api/v1/products/
```

**Request Body:**
```json
{
  "name": "iPad Pro",
  "sku": "IPAD-PRO-12",
  "description": "Apple iPad Pro 12.9-inch",
  "category": 1,
  "price": "1099.99",
  "stock_quantity": 8
}
```

#### Add Stock
```
POST /api/v1/products/{id}/add_stock/
```

**Request Body:**
```json
{
  "quantity": 10
}
```

#### Reduce Stock
```
POST /api/v1/products/{id}/reduce_stock/
```

**Request Body:**
```json
{
  "quantity": 5
}
```

### 3. Orders

#### List Orders
```
GET /api/v1/orders/
```

**Query Parameters:**
- `status` (string): Filter by order status
- `date_from` (date): Filter orders from date
- `date_to` (date): Filter orders to date

**Response:**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "customer": 1,
      "customer_name": "Test User",
      "customer_email": "test@example.com",
      "status": "pending",
      "total": "2899.97",
      "items": [
        {
          "id": 1,
          "product": 1,
          "product_name": "iPhone 15",
          "product_sku": "IPH15-128",
          "quantity": 2,
          "purchase_price": "999.99",
          "total_price": "1999.98",
          "created_at": "2024-01-01T00:00:00Z"
        }
      ],
      "item_count": 2,
      "can_be_cancelled": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### Create Order
```
POST /api/v1/orders/
```

**Request Body:**
```json
{
  "items": [
    {
      "product": 1,
      "quantity": 2
    },
    {
      "product": 2,
      "quantity": 1
    }
  ]
}
```

#### Cancel Order
```
POST /api/v1/orders/{id}/cancel/
```

#### Update Order Status (Staff Only)
```
POST /api/v1/orders/{id}/update_status/
```

**Request Body:**
```json
{
  "status": "confirmed"
}
```

**Available Statuses:**
- `pending`
- `confirmed`
- `processing`
- `shipped`
- `delivered`
- `cancelled`

### 4. Customer Profiles

#### List Customer Profiles
```
GET /api/v1/customer-profiles/
```

#### Get Customer Profile
```
GET /api/v1/customer-profiles/{id}/
```

#### Create Customer Profile
```
POST /api/v1/customer-profiles/
```

**Request Body:**
```json
{
  "user": 1,
  "phone": "+1234567890",
  "address": "123 Test Street, Test City"
}
```

## API Documentation

### Swagger UI
```
http://localhost:8001/api/docs/
```

### ReDoc
```
http://localhost:8001/api/redoc/
```

### OpenAPI Schema
```
http://localhost:8001/api/schema/
```

## Error Responses

### 400 Bad Request
```json
{
  "field_name": ["Error message"]
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

## Business Logic

### Order Processing
1. When an order is created, stock is automatically reduced for all items
2. Order total is calculated automatically using `Order.calculate_total()`
3. Purchase price is locked at the time of order creation
4. When an order is cancelled, stock is restored

### Category Hierarchy
- Categories support unlimited nesting using django-mptt
- Average price calculation includes all descendant categories
- Category tree endpoint provides complete hierarchy structure

### Stock Management
- Products track current stock quantity
- Stock is automatically managed during order creation/cancellation
- Stock can be manually adjusted using add_stock/reduce_stock endpoints

## Testing

Run the test suite:

```bash
# Using pytest
docker-compose exec web pytest

# With coverage
docker-compose exec web pytest --cov=catalog

# Specific test file
docker-compose exec web pytest catalog/tests/test_api.py
```

## Example Usage

### 1. Create a Category Hierarchy
```bash
# Create root category
curl -X POST http://localhost:8001/api/v1/categories/ \
  -H "Authorization: Token your_token" \
  -H "Content-Type: application/json" \
  -d '{"name": "Electronics", "description": "Electronic devices"}'

# Create subcategory
curl -X POST http://localhost:8001/api/v1/categories/ \
  -H "Authorization: Token your_token" \
  -H "Content-Type: application/json" \
  -d '{"name": "Smartphones", "description": "Mobile phones", "parent": 1}'
```

### 2. Create Products
```bash
curl -X POST http://localhost:8001/api/v1/products/ \
  -H "Authorization: Token your_token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "iPhone 15",
    "sku": "IPH15-128",
    "description": "Latest iPhone",
    "category": 2,
    "price": "999.99",
    "stock_quantity": 10
  }'
```

### 3. Place an Order
```bash
curl -X POST http://localhost:8001/api/v1/orders/ \
  -H "Authorization: Token your_token" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"product": 1, "quantity": 2}
    ]
  }'
```

### 4. Get Category Average Price
```bash
curl -X GET http://localhost:8001/api/v1/categories/1/average_price/ \
  -H "Authorization: Token your_token"
```

## Future Enhancements

- SMS notifications via Africa's Talking
- Email notifications to admin
- OpenID Connect authentication
- Advanced filtering and search
- Order status webhooks
- Inventory alerts
- Product reviews and ratings
