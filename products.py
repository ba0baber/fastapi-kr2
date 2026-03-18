from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List

router = APIRouter()

products_db = [
    {"product_id": 123, "name": "Smartphone", "category": "Electronics", "price": 599.99},
    {"product_id": 456, "name": "Phone Case", "category": "Accessories", "price": 19.99},
    {"product_id": 789, "name": "Iphone", "category": "Electronics", "price": 1299.99},
    {"product_id": 101, "name": "Headphones", "category": "Accessories", "price": 99.99},
    {"product_id": 202, "name": "Smartwatch", "category": "Electronics", "price": 299.99},
]

@router.get("/product/{product_id}")
async def get_product(product_id: int):
    """Получить продукт по ID"""
    for product in products_db:
        if product["product_id"] == product_id:
            return product
    raise HTTPException(status_code=404, detail="Product not found")

@router.get("/products/search")
async def search_products(
    keyword: str = Query(..., description="Keyword to search in product names"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(10, ge=1, le=100, description="Max number of products to return")
):
    """Поиск продуктов по ключевому слову и категории"""
    results = []
    
    for product in products_db:
        if keyword.lower() in product["name"].lower():
            if category and product["category"].lower() != category.lower():
                continue
            results.append(product)
    
    return results[:limit]