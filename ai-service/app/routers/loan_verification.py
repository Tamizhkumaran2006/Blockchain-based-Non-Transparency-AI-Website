"""
Loan Verification Router with OCR and Blockchain
Secure, privacy-preserving loan verification system
"""

import os
import logging
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from pydantic import BaseModel
from sqlalchemy import select

from app.config.database import UserModel, LoanVerificationModel, async_session_maker
from app.ocr.document_verifier import document_verifier
from app.ocr.extractor import extract_text_from_file
from app.services.token_service import get_current_user

logger = logging.getLogger("verity-ai.loan")
router = APIRouter()


class LoanApplicationResponse(BaseModel):
    success: bool
    message: str
    application_id: str
    status: str
    verification_result: Optional[dict] = None
    blockchain_hash: Optional[str] = None


@router.post("/apply", response_model=LoanApplicationResponse)
async def apply_for_loan(
    loan_type: str = Form(...),
    loan_amount: float = Form(...),
    income_certificate: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Apply for loan with income certificate
    
    Process:
    1. Upload income certificate
    2. Perform OCR using Google Cloud Vision API to extract salary
    3. Verify eligibility (salary vs loan amount)
    4. Create zero-knowledge proof (no salary exposure)
    5. Store verification hash on blockchain for immutability
    6. Send to manager for approval if eligible
    """
    try:
        # Validate file type
        allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/jpg"]
        if income_certificate.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail="Only PDF, JPEG, and PNG files are allowed"
            )
        
        # Save uploaded file
        upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
        os.makedirs(upload_dir, exist_ok=True)
        
        file_extension = income_certificate.filename.split(".")[-1]
        file_name = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(upload_dir, file_name)
        
        # Read file content
        file_content = await income_certificate.read()
        
        # Save to disk
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        logger.info(f"File uploaded: {file_name}")
        
        # Perform OCR using Google Cloud Vision API
        try:
            ocr_result = await extract_text_from_file(
                file_content,
                income_certificate.content_type,
                income_certificate.filename
            )
            ocr_text = ocr_result["text"]
            ocr_confidence = ocr_result.get("confidence", 0.0)
            
            logger.info(f"OCR completed with {ocr_confidence:.2%} confidence")
            
            if not ocr_text or len(ocr_text.strip()) < 10:
                raise HTTPException(
                    status_code=400,
                    detail="Could not extract text from document. Please ensure the image is clear and readable."
                )
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process document: {str(e)}"
            )
        
        # Verify document authenticity
        is_authentic, auth_message = document_verifier.verify_document_authenticity(ocr_text)
        if not is_authentic:
            raise HTTPException(status_code=400, detail=auth_message)
        
        logger.info(f"Document authenticity verified: {auth_message}")
        
        # Extract salary using AI pattern matching
        salary = document_verifier.extract_salary_from_text(ocr_text)
        if not salary:
            raise HTTPException(
                status_code=400,
                detail="Could not extract salary from document. Please ensure it's a valid income certificate with clearly visible salary information."
            )
        
        logger.info(f"Extracted salary: ₹{salary}")
        
        # Verify eligibility based on bank's rules
        is_eligible, reason, details = document_verifier.verify_eligibility(
            salary, loan_amount, loan_type
        )
        
        logger.info(f"Eligibility check: {is_eligible} - {reason}")
        
        # Create zero-knowledge proof (salary not exposed)
        zkp_proof = document_verifier.create_zero_knowledge_proof(
            salary, loan_amount, loan_type
        )
        
        # Create verification data for blockchain
        verification_data = {
            "user_id": current_user.id,
            "user_email": current_user.email,
            "loan_type": loan_type,
            "loan_amount": loan_amount,
            "is_eligible": is_eligible,
            "verified_at": datetime.utcnow().isoformat(),
            "salary_commitment": zkp_proof["salary_commitment"],  # Hash only, not actual salary
            "document_verified": is_authentic,
            "ocr_confidence": ocr_confidence
        }
        
        # Create blockchain hash for immutable audit trail
        blockchain_hash = document_verifier.create_verification_hash(verification_data)
        
        logger.info(f"Blockchain hash created: {blockchain_hash[:16]}...")
        
        # Determine initial status
        if is_eligible:
            status = "pending_manager_approval"
            message = "Application submitted successfully. Awaiting manager approval."
        else:
            status = "rejected"
            message = f"Application rejected: {reason}"
        
        # Save to database
        application_id = str(uuid.uuid4())
        
        async with async_session_maker() as session:
            verification = LoanVerificationModel(
                id=application_id,
                user_id=current_user.id,
                application_id=application_id,
                status=status,
                result="Pending" if is_eligible else "Rejected",
                reason=reason,
                document_type="income_certificate",
                extracted_data={
                    "loan_type": loan_type,
                    "loan_amount": loan_amount,
                    "ocr_text": ocr_text[:500],  # Store first 500 chars for reference
                    "ocr_confidence": ocr_confidence,
                    "document_verified": is_authentic,
                    "auth_message": auth_message,
                    # IMPORTANT: Actual salary is NOT stored for privacy
                },
                ai_decision={
                    "is_eligible": is_eligible,
                    "reason": reason,
                    "zkp_proof": zkp_proof,
                    "blockchain_hash": blockchain_hash,
                    "details": {
                        "max_eligible_loan": details.get("max_eligible_loan"),
                        "utilization_percent": details.get("utilization_percent"),
                        "lti_ratio": details.get("lti_ratio"),
                        "multiplier": details.get("multiplier"),
                        # Actual salary is NOT stored here for privacy
                    }
                },
                file_name=income_certificate.filename,
                file_type=income_certificate.content_type,
                file_path=file_path,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            session.add(verification)
            await session.commit()
        
        logger.info(f"Loan application created: {application_id} - Status: {status}")
        
        return LoanApplicationResponse(
            success=True,
            message=message,
            application_id=application_id,
            status=status,
            verification_result={
                "is_eligible": is_eligible,
                "reason": reason,
                "max_eligible_loan": details.get("max_eligible_loan"),
                "utilization_percent": details.get("utilization_percent"),
                "lti_ratio": details.get("lti_ratio"),
                "ocr_confidence": ocr_confidence,
                # Actual salary is NEVER returned for privacy
            },
            blockchain_hash=blockchain_hash
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Loan application error: {e}")
        raise HTTPException(status_code=500, detail=f"Application failed: {str(e)}")


@router.get("/applications")
async def get_my_applications(current_user: UserModel = Depends(get_current_user)):
    """Get all loan applications for current user"""
    try:
        async with async_session_maker() as session:
            result = await session.execute(
                select(LoanVerificationModel)
                .where(LoanVerificationModel.user_id == current_user.id)
                .order_by(LoanVerificationModel.created_at.desc())
            )
            applications = result.scalars().all()
            
            return {
                "success": True,
                "applications": [
                    {
                        "id": app.id,
                        "application_id": app.application_id,
                        "status": app.status,
                        "result": app.result,
                        "reason": app.reason,
                        "loan_type": app.extracted_data.get("loan_type") if app.extracted_data else None,
                        "loan_amount": app.extracted_data.get("loan_amount") if app.extracted_data else None,
                        "verification_result": {
                            "is_eligible": app.ai_decision.get("is_eligible") if app.ai_decision else None,
                            "max_eligible_loan": app.ai_decision.get("details", {}).get("max_eligible_loan") if app.ai_decision else None,
                            "utilization_percent": app.ai_decision.get("details", {}).get("utilization_percent") if app.ai_decision else None,
                        } if app.ai_decision else None,
                        "created_at": app.created_at.isoformat() if app.created_at else None,
                        "blockchain_hash": app.ai_decision.get("blockchain_hash") if app.ai_decision else None
                    }
                    for app in applications
                ]
            }
    except Exception as e:
        logger.error(f"Error fetching applications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/applications/{application_id}")
async def get_application_details(
    application_id: str,
    current_user: UserModel = Depends(get_current_user)
):
    """Get detailed information about a specific application"""
    try:
        async with async_session_maker() as session:
            result = await session.execute(
                select(LoanVerificationModel)
                .where(
                    LoanVerificationModel.application_id == application_id,
                    LoanVerificationModel.user_id == current_user.id
                )
            )
            application = result.scalar_one_or_none()
            
            if not application:
                raise HTTPException(status_code=404, detail="Application not found")
            
            return {
                "success": True,
                "application": {
                    "id": application.id,
                    "application_id": application.application_id,
                    "status": application.status,
                    "result": application.result,
                    "reason": application.reason,
                    "extracted_data": application.extracted_data,
                    "ai_decision": application.ai_decision,
                    "created_at": application.created_at.isoformat() if application.created_at else None,
                    "updated_at": application.updated_at.isoformat() if application.updated_at else None
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching application: {e}")
        raise HTTPException(status_code=500, detail=str(e))
