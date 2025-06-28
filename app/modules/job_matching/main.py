# from fastapi import FastAPI
# import httpx

# app = FastAPI()

# @app.get("/call-external-api")
# async def call_api():
#     async with httpx.AsyncClient() as client:
#         response = await client.get("http://api.example.com/data")
#         data = response.json()
#     return {"message": "Success", "data": data}

app.include_router(
    job_matching_router,
    prefix="/api/v1/job-matching",
    tags=["Job Matching"]
)