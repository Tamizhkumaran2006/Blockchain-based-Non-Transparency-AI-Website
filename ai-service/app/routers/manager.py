"""
Manager router — SQLite version
GET  /api/manager/all              — list all applications
GET  /api/manager/requests/:id      — get single application
POST /api/manager/approve           — approve/reject application
GET  /api/manager/stats             — dashboard statistics
GET  /api/manager/settings          — get loan eligibility settings
POST /api/manager/settings          — update loan eligibility settings
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func

from app.config.database import UserModel, LoanVerificationModel, async_session_maker
from app.services.token_service import get_current_user
from app.ocr.document_verifier import document_verifier

logger = logging.getLogger("verity-ai.manager")
router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────

class ApproveBody(BaseModel):
    application_id: str
    action: str  # "approve" or "reject"
    comment: str


class LoanSettingsBody(BaseModel):
    min_salary: Optional[float] = None
    personal_multiplier: Optional[float] = None
    home_multiplier: Optional[float] = None
    auto_multiplier: Optional[float] = None
    business_multiplier: Optional[float] = None
    education_multiplier: Optional[float] = None


# ── Helper function to check if user is manager ──────────────

def require_manager(current_user: UserModel = Depends(get_current_user)):
    if current_user.role not in ("manager", "admin"):
        raise HTTPException(status_code=403, detail="Manager access required")
    return current_user


# ── GET /api/manager/all ──────────────────────────────────────

@router.get("/all")
async def get_all_applications(
    status: Optional[str] = Query(None),
    current_user: UserModel = Depends(require_manager),
):
    """Get all loan applications for manager review"""
    try:
        async with async_session_maker() as session:
            query = select(LoanVerificationModel, UserModel).join(
                UserModel, LoanVerificationModel.user_id == UserModel.id
            ).order_by(LoanVerificationModel.created_at.desc())
            
            if status:
                query = query.where(LoanVerificationModel.status == status)
            
            result = await session.execute(query)
            rows = result.all()
            
            applications = []
            for verification, user in rows:
                applications.append({
                    "id": verification.id,
                    "application_id": verification.application_id,
                    "status": verification.status,
                    "result": verification.result,
                    "reason": verification.reason,
                    "loan_type": verification.extracted_data.get("loan_type") if verification.extracted_data else None,
                    "loan_amount": verification.extracted_data.get("loan_amount") if verification.extracted_data else None,
                    "verification_result": {
                        "is_eligible": verification.ai_decision.get("is_eligible") if verification.ai_decision else None,
                        "max_eligible_loan": verification.ai_decision.get("details", {}).get("max_eligible_loan") if verification.ai_decision else None,
                        "utilization_percent": verification.ai_decision.get("details", {}).get("utilization_percent") if verification.ai_decision else None,
                    } if verification.ai_decision else None,
                    "blockchain_hash": verification.ai_decision.get("blockchain_hash") if verification.ai_decision else None,
                    "created_at": verification.created_at.isoformat() if verification.created_at else None,
                    "user": {
                        "id": user.id,
                        "name": user.name,
                        "email": user.email,
                    }
                })
            
            return {
                "success": True,
                "applications": applications
            }
    except Exception as e:
        logger.error(f"Error fetching applications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── POST /api/manager/approve ─────────────────────────────────

@router.post("/approve")
async def approve_or_reject_application(
    body: ApproveBody,
    current_user: UserModel = Depends(require_manager),
):
    """Approve or reject a loan application"""
    try:
        async with async_session_maker() as session:
            result = await session.execute(
                select(LoanVerificationModel).where(
                    LoanVerificationModel.application_id == body.application_id
                )
            )
            verification = result.scalar_one_or_none()
            
            if not verification:
                raise HTTPException(status_code=404, detail="Application not found")
            
            if verification.status not in ("pending_manager_approval", "ai_reviewed"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot {body.action} application in status: {verification.status}"
                )
            
            # Update status based on action
            if body.action == "approve":
                verification.status = "approved"
                verification.result = "Approved"
                verification.reason = body.comment or "Approved by manager"
                message = "Application approved successfully"
            elif body.action == "reject":
                verification.status = "rejected"
                verification.result = "Rejected"
                verification.reason = body.comment or "Rejected by manager"
                message = "Application rejected"
            else:
                raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'reject'")
            
            # Store manager action in ai_decision
            if not verification.ai_decision:
                verification.ai_decision = {}
            
            verification.ai_decision["manager_action"] = {
                "manager_id": current_user.id,
                "manager_name": current_user.name,
                "action": body.action,
                "comment": body.comment,
                "action_at": datetime.utcnow().isoformat()
            }
            
            verification.updated_at = datetime.utcnow()
            await session.commit()
            
            logger.info(f"Application {body.application_id} {body.action}ed by {current_user.email}")
            
            return {
                "success": True,
                "message": message,
                "application_id": verification.application_id,
                "status": verification.status
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing application: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── GET /api/manager/stats ────────────────────────────────────

@router.get("/stats")
async def get_stats(current_user: UserModel = Depends(require_manager)):
    """Get dashboard statistics for manager"""
    try:
        async with async_session_maker() as session:
            # Count by status
            total_result = await session.execute(
                select(func.count(LoanVerificationModel.id))
            )
            total = total_result.scalar() or 0
            
            pending_result = await session.execute(
                select(func.count(LoanVerificationModel.id)).where(
                    LoanVerificationModel.status == "pending_manager_approval"
                )
            )
            pending = pending_result.scalar() or 0
            
            approved_result = await session.execute(
                select(func.count(LoanVerificationModel.id)).where(
                    LoanVerificationModel.status == "approved"
                )
            )
            approved = approved_result.scalar() or 0
            
            rejected_result = await session.execute(
                select(func.count(LoanVerificationModel.id)).where(
                    LoanVerificationModel.status == "rejected"
                )
            )
            rejected = rejected_result.scalar() or 0
            
            return {
                "success": True,
                "stats": {
                    "total": total,
                    "pending": pending,
                    "approved": approved,
                    "rejected": rejected,
                    "approval_rate": f"{(approved / total * 100):.1f}%" if total > 0 else "0%"
                }
            }
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── GET /api/manager/settings ─────────────────────────────────

@router.get("/settings")
async def get_loan_settings(current_user: UserModel = Depends(require_manager)):
    """Get current loan eligibility settings"""
    return {
        "success": True,
        "settings": {
            "min_salary": document_verifier.min_salary,
            "eligibility_rules": document_verifier.ELIGIBILITY_RULES,
            "description": {
                "min_salary": "Minimum monthly salary required for any loan",
                "personal": "Personal loan multiplier (e.g., 5 = 5x monthly salary)",
                "home": "Home loan multiplier (e.g., 60 = 60x monthly salary)",
                "auto": "Auto loan multiplier (e.g., 10 = 10x monthly salary)",
                "business": "Business loan multiplier (e.g., 8 = 8x monthly salary)",
                "education": "Education loan multiplier (e.g., 12 = 12x monthly salary)"
            }
        }
    }


# ── POST /api/manager/settings ────────────────────────────────

@router.post("/settings")
async def update_loan_settings(
    body: LoanSettingsBody,
    current_user: UserModel = Depends(require_manager)
):
    """Update loan eligibility settings (bank policy)"""
    try:
        updated_fields = []
        
        if body.min_salary is not None and body.min_salary > 0:
            document_verifier.min_salary = body.min_salary
            updated_fields.append(f"min_salary={body.min_salary}")
        
        if body.personal_multiplier is not None and body.personal_multiplier > 0:
            document_verifier.ELIGIBILITY_RULES["personal"] = body.personal_multiplier
            updated_fields.append(f"personal={body.personal_multiplier}")
        
        if body.home_multiplier is not None and body.home_multiplier > 0:
            document_verifier.ELIGIBILITY_RULES["home"] = body.home_multiplier
            updated_fields.append(f"home={body.home_multiplier}")
        
        if body.auto_multiplier is not None and body.auto_multiplier > 0:
            document_verifier.ELIGIBILITY_RULES["auto"] = body.auto_multiplier
            updated_fields.append(f"auto={body.auto_multiplier}")
        
        if body.business_multiplier is not None and body.business_multiplier > 0:
            document_verifier.ELIGIBILITY_RULES["business"] = body.business_multiplier
            updated_fields.append(f"business={body.business_multiplier}")
        
        if body.education_multiplier is not None and body.education_multiplier > 0:
            document_verifier.ELIGIBILITY_RULES["education"] = body.education_multiplier
            updated_fields.append(f"education={body.education_multiplier}")
        
        if not updated_fields:
            raise HTTPException(status_code=400, detail="No valid settings provided")
        
        logger.info(f"Loan settings updated by {current_user.email}: {', '.join(updated_fields)}")
        
        return {
            "success": True,
            "message": "Loan eligibility settings updated successfully",
            "updated_fields": updated_fields,
            "current_settings": {
                "min_salary": document_verifier.min_salary,
                "eligibility_rules": document_verifier.ELIGIBILITY_RULES
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))
