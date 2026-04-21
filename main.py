import os
import requests
import asyncio
from datetime import datetime, timedelta, timezone
from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright

# ================= 1. 配置区域 =================
ROCOM_API_KEY = os.environ.get("ROCOM_API_KEY")
IMGBB_KEY = os.environ.get("IMGBB_KEY")
NOTIFYME_UUID = os.environ.get("NOTIFYME_UUID")
BARK_KEY = os.environ.get("BARK_KEY")

GAME_API_URL = "https://wegame.shallow.ink/api/v1/games/rocom/merchant/info?refresh=true"
NOTIFYME_SERVER = "https://notifyme-server.wzn556.top/api/send"
ASSETS_DIR = os.path.abspath("assets/yuanxing-shangren")
HTML_TEMPLATE_FILE = "index.html"
TEMP_RENDER_FILE = "temp_render.html"

# ================= 2. 时间与数据逻辑处理 =================

def get_beijing_time():
    """获取精准的北京时间"""
    return datetime.now(timezone(timedelta(hours=8)))

def format_timestamp(ts_ms):
    """格式化 API 返回的毫秒时间戳为 HH:mm"""
    if not ts_ms: return "--:--"
    dt = datetime.fromtimestamp(int(ts_ms) / 1000, tz=timezone(timedelta(hours=8)))
    return dt.strftime("%H:%M")

def get_round_info():
    """计算当前远行商人的轮次信息"""
    now = get_beijing_time()
    # 商人 08:00 开市
    start_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
    
    if now < start_time:
        return {"is_open": False, "current": 0, "countdown": "尚未开市"}
    
    # 每 4 小时一轮，共 4 轮 (08-12, 12-16, 16-20, 20-00)
    delta_seconds = int((now - start_time).total_seconds())
    round_index = (delta_seconds // (4 * 3600)) + 1
    
    if round_index > 4:
        return {"is_open": False, "current": 0, "countdown": "已收市"}
    
    # 计算当前轮次结束时间
    round_end = start_time + timedelta(hours=round_index * 4)
    remaining = round_end - now
    hours, rem = divmod(int(remaining.total_seconds()), 3600)
    minutes, _ = divmod(rem, 60)
    
    countdown_str = f"{hours}小时{minutes}分钟" if hours > 0 else f"{minutes}分钟"
    
    return {
        "is_open": True,
        "current": round_index,
        "total": 4,
        "countdown": countdown_str,
        "date": now.strftime("%Y-%m-%d")
    }

def process_data_for_template(data):
    """筛选当前轮次商品并加工数据"""
    if not data: return {}
    
    now_ms = int(get_beijing_time().timestamp() * 1000)
    round_info = get_round_info()
    
    activities = data.get("merchantActivities") or []
    activity = activities[0] if activities else {}
    all_items = (activity.get("get_props") or []) + (activity.get("get_pets") or [])
    
    active_products = []
    for item in all_items:
        s_time = item.get("start_time")
        e_time = item.get("end_time")
        
        # 核心过滤逻辑：只有当前时间在商品的起止时间内的才显示（解决显示上一轮内容的问题）
        if s_time and e_time:
            if int(s_time) <= now_ms < int(e_time):
                active_products.append({
                    "name": item.get("name", "未知"),
                    "image": item.get("icon_url", ""),
                    "time_label": f"{format_timestamp(s_time)} - {format_timestamp(e_time)}"
                })
        else:
            # 如果没有时间戳（兜底），则全部显示
            active_products.append({
                "name": item.get("name", "未知"),
                "image": item.get("icon_url", ""),
                "time_label": "全天供应"
            })
            
    return {
        "title": activity.get("name", "远行商人"),
        "subtitle": activity.get("start_date", "每日 08:00 / 12:00 / 16:00 / 20:00 刷新"),
        "product_count": len(active_products),
        "round_info": round_info,
        "products": active_products
    }

# ================= 3. 渲染与上传 =================

async def render_to_image(processed_data):
    if not processed_data or processed_data["product_count"] == 0:
        print("当前无活跃商品，跳过渲染")
        return None
    
    screenshot_file = "merchant_render.jpg"
    temp_html_path = os.path.join(ASSETS_DIR, TEMP_RENDER_FILE)
    
    try:
        env = Environment(loader=FileSystemLoader(ASSETS_DIR))
        template = env.get_template(HTML_TEMPLATE_FILE)
        rendered_html = template.render(processed_data)
        
        with open(temp_html_path, "w", encoding="utf-8") as f:
            f.write(rendered_html)
            
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.set_viewport_size({"width": 1600, "height": 1200})
            await page.goto(f"file://{temp_html_path}")
            await page.wait_for_load_state("networkidle")
            await page.screenshot(path=screenshot_file, type="jpeg", quality=90, full_page=True)
            await browser.close()
        return screenshot_file
    except Exception as e:
        print(f"渲染失败: {e}")
        return None
    finally:
        if os.path.exists(temp_html_path): os.remove(temp_html_path)

async def upload_to_imgbb(image_path):
    if not image_path or not IMGBB_KEY: return None
    try:
        with open(image_path, "rb") as f:
            res = requests.post("https://api.imgbb.com/1/upload", data={"key": IMGBB_KEY}, files={"image": f}, timeout=30)
            return res.json()["data"]["url"]
    except: return None

# ================= 4. 推送 =================

def push_all(title, body, markdown, image_url):
    # NotifyMe
    if NOTIFYME_UUID:
        payload = {
            "data": {
                "uuid": NOTIFYME_UUID, "ttl": 86400, "priority": "high",
                "data": {
                    "title": title, "body": body, "group": "洛克王国", "bigText": True, "record": 1,
                    "markdown": f"{markdown}\n\n![render]({image_url})" if image_url else markdown
                }
            }
        }
        requests.post(NOTIFYME_SERVER, json=payload, timeout=10)
    
    # Bark
    if BARK_KEY:
        requests.post(f"https://api.day.app/{BARK_KEY}", data={
            "title": title, "body": body, "group": "洛克王国", "image": image_url, "isArchive": 1
        }, timeout=10)

async def main():
    raw_data, err = await (asyncio.to_thread(lambda: (requests.get(GAME_API_URL, headers={"X-API-Key": ROCOM_API_KEY}, timeout=30).json().get("data"), None) if requests.get(GAME_API_URL, headers={"X-API-Key": ROCOM_API_KEY}, timeout=30).status_code==200 else (None, "接口异常")))
    
    if err or not raw_data:
        push_all("⚠️ 监控异常", err or "无法获取数据", "无法获取数据", None)
        return

    processed = process_data_for_template(raw_data)
    # 获取当前商品名称列表作为推送文字（解决文字内容问题）
    item_names = [p["name"] for p in processed["products"]]
    push_body = f"当前售卖: {'、'.join(item_names)}" if item_names else "当前暂无商品"
    
    local_img = await render_to_image(processed)
    img_url = await upload_to_imgbb(local_img)
    
    push_all("📢 远行商人刷新", push_body, "### 🛒 商人刷新详情", img_url)

if __name__ == "__main__":
    asyncio.run(main())
