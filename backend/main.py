from typing import List
from fastapi import FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware

from app.database import initialize_database
from app.models import Claim, ClaimCreate, ClaimUpdate 
import app.services.ClaimService as ClaimService

app = FastAPI(
    title="WayTOO CMS Backend API",
    description="API for managing customer claims for WayTOO.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    await initialize_database() 

# --- API Endpoints ---

@app.post("/claims/", response_model=Claim, status_code=201)
async def create_claim(claim: ClaimCreate):
    """
    Creates a new customer claim.
    """
    try:
        new_claim = await ClaimService.create_claim(claim) 
        return new_claim
    except Exception as e:
        print(f"Error creating claim via API: {e}")
        raise HTTPException(status_code=500, detail="Failed to create claim.")

@app.get("/claims/", response_model=List[Claim])
async def get_all_claims():
    """
    Retrieves a list of all claims.
    """
    try:
        claims = await ClaimService.get_all_claims() 
        return claims
    except Exception as e:
        print(f"Error fetching claims via API: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve claims.")

@app.get("/claims/{claim_id}", response_model=Claim)
async def get_claim_by_id(claim_id: int):
    """
    Retrieves a single claim by its ID.
    """
    try:
        claim = await ClaimService.get_claim_by_id(claim_id) 
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found.")
        return claim
    except HTTPException: 
        raise
    except Exception as e:
        print(f"Error fetching claim by ID via API: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve claim.")


@app.put("/claims/{claim_id}/validate", response_model=Claim)
async def handle_AI_triage(claim_id: int):
    try:
        AI_updated_claim = await ClaimService.validate_claim(claim_id)
        if not AI_updated_claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        return AI_updated_claim
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating claim status via API: {e}")
        raise HTTPException(status_code=500, detail="Failed to update claim status.")

@app.put("/claims/{claim_id}/status", response_model=Claim)
async def update_claim_status(claim_id: int, status_update: ClaimUpdate):
    """
    Updates the status of a claim and appends to its audit log.
    """
    try:
        updated_claim = await ClaimService.update_claim_status(claim_id, status_update) 
        if not updated_claim:
            raise HTTPException(status_code=404, detail="Claim not found.")
        return updated_claim
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating claim status manually via API: {e}")
        raise HTTPException(status_code=500, detail="Failed to update claim status.")