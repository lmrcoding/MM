from fastapi.responses import JSONResponse

def bad_request(detail="Invalid input"):
    return JSONResponse(status_code=400, content={"error": detail})

def forbidden(detail="Access denied"):
    return JSONResponse(status_code=403, content={"error": detail})

def internal_error(detail="Something went wrong"):
    return JSONResponse(status_code=500, content={"error": detail})
