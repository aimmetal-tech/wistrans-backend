from fastapi import FastAPI

app = FastAPI()

# 智慧译项目根路由
@app.get("/")
def wistrans():
    return {"message": "欢迎来到wistrans智慧译"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)