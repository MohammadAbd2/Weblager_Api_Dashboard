import json
from fastapi import APIRouter, HTTPException
from ..db import get_conn, insert_record, row_to_dict
from ..helpers import build_sort_clause
from ..models import ProductCreate

router = APIRouter(prefix="/products", tags=["products"])


@router.get("")
def list_products(
        category: int | None = None,
        sort: str = "name",
        direction: str = "asc",
        min_price: float | None = None,
        max_price: float | None = None,
):
    """Queries, filters, and sorts products from the catalog."""
    sort_clause = build_sort_clause(sort, direction)
    where: list[str] = []
    args: list = []

    # Optional Default: Fallback context fallback constraint if no query specified
    if category is None:
        category = 1

    if category is not None:
        args.append(category)
        where.append("category_id = ?")
    if min_price is not None:
        args.append(min_price)
        where.append("price >= ?")
    if max_price is not None:
        args.append(max_price)
        where.append("price <= ?")

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    query = f"SELECT id, name, category_id, price, stock, release_date AS released_on, specs, created_at FROM products {where_sql} {sort_clause}"

    with get_conn() as conn:
        rows = conn.execute(query, args).fetchall()
        return [row_to_dict(r) for r in rows]


@router.get("/{product_id}")
def get_product(product_id: int):
    """Fetches full specifications profile for an explicit product instance."""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        return row_to_dict(row)


@router.post("", status_code=201)
def create_product(product: ProductCreate):
    """Creates a catalog product instance, parsing nested specs dictionary as raw JSON text string."""
    payload = product.model_dump(mode="json")
    payload["specs"] = json.dumps(payload.get("specs", {}))
    return insert_record("products", payload)


@router.put("/{product_id}")
def update_product(product_id: int, product: ProductCreate):
    """Updates fields on an existing product profile using SQL inline modifications."""
    payload = product.model_dump(mode="json")
    payload["specs"] = json.dumps(payload.get("specs", {}))
    set_clauses = ", ".join(f"{k} = ?" for k in payload)
    vals = list(payload.values()) + [product_id]

    with get_conn() as conn:
        cur = conn.execute(
            f"UPDATE products SET {set_clauses} WHERE id = ? RETURNING *",
            vals,
        )
        row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        conn.commit()
        return row_to_dict(row)


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int):
    """Removes a physical entity completely from the products table."""
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Product not found")