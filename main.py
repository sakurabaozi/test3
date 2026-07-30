import os
import requests
from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI(title="今日油价与调价预测 API")

# 支持通过环境变量配置 API Key，本地或默认可以使用自定义变量
APIZERO_KEY = os.getenv("APIZERO_API_KEY", "sk_test_0c392e2e6eb1305e17b43166998b289aeeb68246db7786e7")
API_URL = "https://v1.apizero.cn/api/oil-price-forecast"

class OilPriceRequest(BaseModel):
    action: Optional[str] = Field("price", description="操作类型: price(指定省份油价), forecast(调价预测), price-all(所有省份油价), schedule(调价日历)")
    province: Optional[str] = Field("北京", description="省份名称(仅当 action=price 时必填)，如 '北京'、'广东'")
    year: Optional[int] = Field(2026, description="年份(仅当 action=schedule 时可用)，如 2025、2026")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Oil Price & Forecast API (apizero.cn) is running!"}

@app.post("/query_oil")
def query_oil(data: OilPriceRequest):
    action = data.action or "price"
    params = {"action": action}
    
    if action == "price":
        if not data.province:
            return {"status": "error", "message": "当 action=price 时，province 参数为必填项"}
        params["province"] = data.province.strip().replace("省", "").replace("市", "")
    elif action == "schedule":
        params["year"] = data.year or 2026

    headers = {
        "X-API-Key": APIZERO_KEY,
        "Authorization": f"Bearer {APIZERO_KEY}"
    }

    try:
        response = requests.get(API_URL, params=params, headers=headers, timeout=8)
        
        if response.status_code == 429:
            return {"status": "error", "message": "请求过频（超出 QPS 限制），请稍后再试"}
            
        response.raise_for_status()
        res_data = response.json()
        
        return {
            "status": "success",
            "action": action,
            "raw_data": res_data
        }

    except requests.exceptions.Timeout:
        return {"status": "error", "message": "请求 apizero 油价接口超时"}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"网络请求失败: {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": f"程序执行异常: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)