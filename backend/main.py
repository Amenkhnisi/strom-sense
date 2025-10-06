from fastapi import FastAPI

app = FastAPI(title="AI-Powered Home Energy Optimizer")


@app.get("/")
def read_root():
    return {"message": "StromSense backend is running"}
