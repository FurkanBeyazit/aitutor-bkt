from fastapi import APIRouter
from exam_router import exam_router
from llm_router import llm_router
from user_router import user_router
from type_based_bkt_router import bkt_router

# main router
router = APIRouter()

# sub-routers
router.include_router(exam_router)
router.include_router(llm_router)
router.include_router(user_router)
router.include_router(bkt_router)


