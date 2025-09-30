from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from pymongo import MongoClient
import certifi
from sentence_transformers import SentenceTransformer, util
import json

# -------------------------------
# MongoDB Setup
# -------------------------------
MONGO_URI = "mongodb+srv://price-analytics-admin:vue52gIfe4BCUABK@price-analytics-pl-0.dj2lqq.mongodb.net/stockprice?retryWrites=true&w=majority"
MONGO_CLIENT = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
DB_NAME = "marketplacetaxonomy"
PRODUCT_COLLECTION = "ProductsV1"
TAXONOMY_COLLECTION = "NeptuneTaxonomy"
db = MONGO_CLIENT[DB_NAME]
product_col = db[PRODUCT_COLLECTION]
taxonomy_col = db[TAXONOMY_COLLECTION]

# -------------------------------
# Load Model
# -------------------------------
model = SentenceTransformer("all-MiniLM-L6-v2")

# -------------------------------
# FastAPI Setup
# -------------------------------
app = FastAPI(title="Marketplace Category Validator V5", version="1.5")

# -------------------------------
# Pydantic Models
# -------------------------------
class Product(BaseModel):
    title: str
    description: str
    ean: str
    chosen_category: Optional[str] = None

class CategorySuggestion(BaseModel):
    code: str
    name: str
    miraklpath: Optional[str] = None
    producttype: Optional[str] = None
    parent: List[dict] = []

class PredictionResponse(BaseModel):
    best_category: CategorySuggestion
    top_suggestions: List[dict]
    confidence: float
    is_valid: bool

# -------------------------------
# Utility Functions
# -------------------------------
def flatten_taxonomy(taxonomy, parent_hierarchy=None):
    if parent_hierarchy is None:
        parent_hierarchy = []
    flat = []
    for key, value in taxonomy.items():
        current_parent = parent_hierarchy.copy()
        if "children" in value:
            children = value.pop("children")
        else:
            children = {}
        flat.append({
            "code": value["code"],
            "name": value["name"],
            "miraklpath": value.get("miraklpath"),
            "producttype": value.get("producttype"),
            "parent_hierarchy": current_parent
        })
        if children:
            flat.extend(flatten_taxonomy(children, current_parent + [{"code": value["code"], "name": value["name"]}]))
    return flat

def encode_text(texts: List[str]):
    # Avoid NoneType error
    return model.encode([t if t else "" for t in texts], convert_to_tensor=True)

# -------------------------------
# API Endpoints
# -------------------------------

@app.post("/predict-category", response_model=PredictionResponse)
def predict_category(product: Product):
    try:
        # 1. Flatten taxonomy and encode names
        taxonomy_data = list(taxonomy_col.find({}, {"_id": 0}))
        flat_taxonomy = flatten_taxonomy({t["code"]: t for t in taxonomy_data})
        taxonomy_texts = [t["name"] for t in flat_taxonomy]
        taxonomy_embeddings = encode_text(taxonomy_texts)

        # 2. Encode incoming product info
        combined_text = f"{product.title} {product.description} {product.ean} {product.chosen_category or ''}"
        product_embedding = encode_text([combined_text])

        # 3. Compute similarity with taxonomy
        similarities = util.cos_sim(product_embedding, taxonomy_embeddings)[0]
        top_indices = similarities.argsort(descending=True)[:5]

        top_suggestions = []
        for idx in top_indices:
            t = flat_taxonomy[idx]
            top_suggestions.append({
                "category": {
                    "code": t["code"],
                    "name": t["name"],
                    "miraklpath": t.get("miraklpath"),
                    "producttype": t.get("producttype"),
                    "parent": t["parent_hierarchy"]
                },
                "confidence": float(similarities[idx])
            })

        best_category = top_suggestions[0]["category"]
        confidence = top_suggestions[0]["confidence"]
        is_valid = True if confidence > 0.5 else False

        return PredictionResponse(
            best_category=best_category,
            top_suggestions=top_suggestions,
            confidence=confidence,
            is_valid=is_valid
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/load-products-batch")
def load_products_batch(file_path: str):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            products = json.load(f)
        for p in products:
            combined_text = f"{p.get('productNameEn','')} {p.get('productNameAr','')} {p.get('ean','')} {p.get('brandName','')}"
            p["embedding"] = encode_text([combined_text])[0].tolist()
        product_col.insert_many(products)
        return {"status": "success", "count": len(products)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
