import os

import json
from typing import List, Optional
from fastapi import HTTPException
from app.database import get_DB_connection
from app.models import Claim, ClaimCreate, ClaimUpdate, AuditLogEntry

# --- Core Claim Service Functions (Database Operations) ---
async def create_claim(claim: ClaimCreate):
    """
    Creates a new customer claim.
    """
    conn = get_DB_connection()
    cur = conn.cursor()
    try:
        initial_audit_log_entry_dict = AuditLogEntry(
            action="Claim Submitted",
            details={"customer_id": claim.customer_id}
        ).model_dump()

        audit_log_for_db = json.dumps([initial_audit_log_entry_dict]) 

        cur.execute(
            """
            INSERT INTO claims (customer_id, description, status, audit_log)
            VALUES (%s, %s, %s, %s) RETURNING id, customer_id, description, status, submission_date, root_cause, resolution_type, refund_amount, audit_log;
            """,
            (claim.customer_id, claim.description, 'submitted', audit_log_for_db)
        )
        new_claim_data = cur.fetchone()
        conn.commit()

        new_claim_data_dict = {
            "id": new_claim_data[0],
            "customer_id": new_claim_data[1],
            "description": new_claim_data[2],
            "status": new_claim_data[3],
            "submission_date": new_claim_data[4],
            "root_cause": new_claim_data[5],
            "resolution_type": new_claim_data[6],
            "refund_amount": new_claim_data[7],
            "audit_log": new_claim_data[8] if new_claim_data[8] else []
        }
        return Claim(**new_claim_data_dict)
    except Exception as e:
        conn.rollback()
        print(f"Error creating claim: {e}")
        raise HTTPException(status_code=500, detail="Failed to create claim.")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

async def get_all_claims():
    """
    Retrieves a list of all claims.
    """
    conn = get_DB_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, customer_id, description, status, submission_date, root_cause, resolution_type, refund_amount, audit_log
            FROM claims;
            """
        )
        claims_data = cur.fetchall()
        
        claims_list = []
        for row in claims_data:
            claim_dict = {
                "id": row[0],
                "customer_id": row[1],
                "description": row[2],
                "status": row[3],
                "submission_date": row[4],
                "root_cause": row[5],
                "resolution_type": row[6],
                "refund_amount": row[7],
                "audit_log": row[8] if row[8] else []
            }
            claims_list.append(Claim(**claim_dict))
        return claims_list
    except Exception as e:
        print(f"Error fetching claims: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve claims.")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

async def get_claim_by_id(claim_id: int):
    """
    Retrieves a single claim by its ID.
    """
    conn = get_DB_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, customer_id, description, status, submission_date, root_cause, resolution_type, refund_amount, audit_log
            FROM claims WHERE id = %s;
            """,
            (claim_id,)
        )
        claim_data = cur.fetchone()
        if not claim_data:
            raise HTTPException(status_code=404, detail="Claim not found.")
        
        claim_dict = {
            "id": claim_data[0],
            "customer_id": claim_data[1],
            "description": claim_data[2],
            "status": claim_data[3],
            "submission_date": claim_data[4],
            "root_cause": claim_data[5],
            "resolution_type": claim_data[6],
            "refund_amount": claim_data[7],
            "audit_log": claim_data[8] if claim_data[8] else []
        }
        return Claim(**claim_dict)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching claim by ID: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve claim.")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


async def update_claim_status(claim_id: int, status_update: ClaimUpdate):
    """
    Updates the status of a claim and appends to its audit log.
    """
    conn = get_DB_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT audit_log, status FROM claims WHERE id = %s FOR UPDATE;
            """,
            (claim_id,)
        )
        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Claim not found.")
        
        current_audit_log = result[0] if result[0] is not None else []
        current_status = result[1]

        new_entry = AuditLogEntry(
            action=f"Status Updated to {status_update.status}",
            details={"previous_status": current_status, "new_status": status_update.status}
        ).model_dump()

        current_audit_log.append(new_entry)
        
        updated_audit_log_for_db = json.dumps(current_audit_log)

        cur.execute(
            """
            UPDATE claims
            SET status = %s, audit_log = %s
            WHERE id = %s
            RETURNING id, customer_id, description, status, submission_date, root_cause, resolution_type, refund_amount, audit_log;
            """,
            (status_update.status, updated_audit_log_for_db, claim_id)
        )
        updated_claim_data = cur.fetchone()
        conn.commit()

        updated_claim_dict = {
            "id": updated_claim_data[0],
            "customer_id": updated_claim_data[1],
            "description": updated_claim_data[2],
            "status": updated_claim_data[3],
            "submission_date": updated_claim_data[4],
            "root_cause": updated_claim_data[5],
            "resolution_type": updated_claim_data[6],
            "refund_amount": updated_claim_data[7],
            "audit_log": updated_claim_data[8] if updated_claim_data[8] else []
        }
        return Claim(**updated_claim_dict)
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        print(f"Error updating claim status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update claim status.")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def validate_claim(claim_id: int) -> Optional[Claim]:
    """
    Performs AI triage and validation on a claim, updating its status and audit log.
    Returns the updated claim or None if not found.
    """
    conn = get_DB_connection()
    cur = conn.cursor()
    try:
        # Fetch current claim data
        cur.execute(
            """
            SELECT id, customer_id, description, status, submission_date, root_cause, resolution_type, refund_amount, audit_log
            FROM claims WHERE id = %s FOR UPDATE;
            """,
            (claim_id,)
        )
        current_claim_data_tuple = cur.fetchone()
        if not current_claim_data_tuple:
            return None # Claim not found

        current_claim_dict = {
            "id": current_claim_data_tuple[0],
            "customer_id": current_claim_data_tuple[1],
            "description": current_claim_data_tuple[2],
            "status": current_claim_data_tuple[3],
            "submission_date": current_claim_data_tuple[4],
            "root_cause": current_claim_data_tuple[5],
            "resolution_type": current_claim_data_tuple[6],
            "refund_amount": current_claim_data_tuple[7],
            "audit_log": current_claim_data_tuple[8] if current_claim_data_tuple[8] else []
        }

        # Ensure claim is in a status that can be validated (e.g., 'submitted' or 'pending_manual_review')
        if current_claim_dict["status"] not in ['submitted', 'pending_manual_review']:
            raise HTTPException(status_code=400, detail=f"Claim {claim_id} cannot be validated from status '{current_claim_dict['status']}'.")

        # Perform AI Triage and Validation
        triage_result = ai_triage(current_claim_dict["description"])
        new_status = triage_result["status"]
        triage_details = triage_result["details"]

        # Update audit log
        new_audit_entry = AuditLogEntry(
            action=f"AI Triage/Validation: Status changed to {new_status}",
            details=triage_details
        ).model_dump()
        
        current_claim_dict["audit_log"].append(new_audit_entry)
        updated_audit_log_for_db = json.dumps(current_claim_dict["audit_log"])

        # Update the database
        cur.execute(
            """
            UPDATE claims
            SET status = %s, audit_log = %s
            WHERE id = %s
            RETURNING id, customer_id, description, status, submission_date, root_cause, resolution_type, refund_amount, audit_log;
            """,
            (new_status, updated_audit_log_for_db, claim_id)
        )
        updated_claim_data_tuple = cur.fetchone()
        conn.commit()

        updated_claim_dict = {
            "id": updated_claim_data_tuple[0],
            "customer_id": updated_claim_data_tuple[1],
            "description": updated_claim_data_tuple[2],
            "status": updated_claim_data_tuple[3],
            "submission_date": updated_claim_data_tuple[4],
            "root_cause": updated_claim_data_tuple[5],
            "resolution_type": updated_claim_data_tuple[6],
            "refund_amount": updated_claim_data_tuple[7],
            "audit_log": updated_claim_data_tuple[8] if updated_claim_data_tuple[8] else []
        }
        return Claim(**updated_claim_dict)

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        print(f"Error validating claim: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate claim: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def ai_triage(description: str) -> dict:
    """
    Simulates AI-driven triage and validation of a claim description.
    Returns a dictionary with 'status' and 'details' for audit logging.
    """
    description_lower = description.lower()
    new_status = 'pending_manual_review' # Default status
    validation_reason = "No clear keywords, requires manual review."

    if "missing" in description_lower or "damaged" in description_lower or "faulty" in description_lower:
        new_status = 'validated'
        validation_reason = "Keywords detected (missing/damaged/faulty)."
    elif "spam" in description_lower or "test claim" in description_lower or "junk" in description_lower:
        new_status = 'rejected'
        validation_reason = "Flagged as spam/test/junk."
    
    return {
        "status": new_status,
        "details": {"validation_reason": validation_reason}
    }