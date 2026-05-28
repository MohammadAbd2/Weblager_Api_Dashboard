from fastapi import APIRouter, HTTPException
from datetime import datetime
from ..db import get_conn, insert_record, row_to_dict
from ..models import ReviewCreate, ReviewUpdate

router = APIRouter(tags=["reviews"])


@router.get("/products/{product_id}/reviews")
def list_reviews(product_id: int):
    """Extracts non-deleted reviews listed under a unique product index."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM reviews WHERE product_id = ? AND deleted_at IS NULL ORDER BY id DESC",
            (product_id,),
        ).fetchall()
        return [row_to_dict(r) for r in rows]


@router.post("/reviews", status_code=201)
def create_review(review: ReviewCreate):
    """Saves a fresh submitted client review straight into the reviews database."""
    payload = review.model_dump(mode="json")
    return insert_record("reviews", payload)


@router.put("/reviews/{review_id}")
def update_review(review_id: int, review: ReviewUpdate):
    """Performs updates on specified review text payload configurations."""
    fields = review.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    set_clauses = ", ".join(f"{k} = ?" for k in fields)
    vals = list(fields.values()) + [review_id]
    with get_conn() as conn:
        cur = conn.execute(
            f"UPDATE reviews SET {set_clauses} WHERE id = ? RETURNING *",
            vals,
        )
        row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Review not found")
        conn.commit()
        return row_to_dict(row)


@router.delete("/reviews/{review_id}", status_code=204)
def delete_review(review_id: int):
    """Executes a logical safe soft-delete via writing current timestamp marker parameters inside deleted_at column."""
    with get_conn() as conn:
        current_time = datetime.utcnow().isoformat()
        cur = conn.execute(
            "UPDATE reviews SET deleted_at = ? WHERE id = ?",
            (current_time, review_id)
        )
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Review not found")