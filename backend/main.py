import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 1. Load environment variables first
load_dotenv()

# 2. Import routes after environment initialization
from .routes import categories, products, reviews

# 3. Initialize FastAPI Application
app = FastAPI(title="Product Dashboard API")

# 4. Define allowed cross-origins (handling both localhost and 127.0.0.1 loopbacks)
origins = [
    "http://localhost:8800",
    "http://127.0.0.1:8800",
]

# 5. Apply CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 6. Include API Sub-routers
app.include_router(products.router)
app.include_router(categories.router)
app.include_router(reviews.router)


@app.get("/")
def root():
    return {"status": "ok"}