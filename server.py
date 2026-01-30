import uvicorn
import os

if __name__ == "__main__":
    # Run the server using uvicorn
    # Host 0.0.0.0 allows external access (e.g. for ngrok)
    # Port 8000 is standard
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
