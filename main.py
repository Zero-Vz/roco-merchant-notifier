import requests

# 洛克王国公开 API 地址
API_URL = "https://wegame.shallow.ink/api/v1/games/rocom/merchant/info?refresh=true"

# ！！！将这里替换成你 NotifyMe 设备的真实 UUID ！！！
NOTIFYME_UUID = "jk9JwjyvKZ8FL75eei4c3Z"

# 新版 NotifyMe 官方服务端地址
NOTIFYME_SERVER_URL = "https://notifyme-server.wzn556.top" 

def get_merchant_data():
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        res_json = response.json()
        
        if res_json.get("code") != 0:
            return None, f"接口返回错误: {res_json.get('message', '未知错误')}"
            
        data = res_json.get("data", {})
        activities = data.get("merchantActivities") or data.get("merchant_activities") or []
        
        if not activities:
            return None, "当前暂无远行商人数据"
            
        activity = activities[0]
        props = activity.get("get_props", [])
        pets = activity.get("get_pets", [])
        
        if not props and not pets:
            return None, "当前轮次商人没有携带任何商品"
        
        # 提取商品纯文本名称（用于在手机通知栏简略显示）
        item_names = [item.get("name", "未知") for item in props + pets]
        body_text = f"当前售卖: {'、'.join(item_names)}"
        
        # 拼接 Markdown 格式的内容（用于在 App 内完美渲染图片）
        content_md = "### 🛒 当前售卖道具与精灵\n\n---\n\n"
        for item in props + pets:
            name = item.get("name", "未知商品")
            icon_url = item.get("icon_url", "")
            # Markdown 图片语法，配合加粗字体
            content_md += f"![{name}]({icon_url}) **{name}**\n\n"
            
        return body_text, content_md

    except Exception as e:
        return None, f"获取商人数据失败: {e}"

def push_via_notifyme(body_text, markdown_text):
    # 根据获取结果判断标题和内容
    if body_text is None:
        title = "⚠️ 远行商人监控异常"
        body = markdown_text # 此时 markdown_text 里装的是报错信息
        md = markdown_text
    else:
        title = "📢 洛克王国：远行商人已刷新"
        body = body_text
        md = markdown_text

    # 严格按照新版开发文档构建 JSON 结构
    payload = {
        "data": {
            "uuid": NOTIFYME_UUID,
            "ttl": 86400,            # 离线保存 1 天
            "priority": "high",      # 高优先级，穿透 Doze 模式
            "data": {
                "title": title,
                "body": body,        # 通知栏显示的纯文本摘要
                "markdown": md,      # App 内显示的富文本图文
                "group": "洛克王国",  # 消息归类分组
                "bigText": True,     # 允许在通知栏展开显示多行
                "record": 1          # 记录到 App 的历史消息中
            }
        }
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        # 注意：如果单纯发到域名根目录报错（404），可尝试把 URL 改为 https://notifyme-server.wzn556.top/api/send
        res = requests.post(NOTIFYME_SERVER_URL, json=payload, headers=headers)
        
        if res.status_code == 200:
            print("NotifyMe 新版 API 推送成功！")
        else:
            print(f"推送失败，状态码: {res.status_code}, 返回内容: {res.text}")
    except Exception as e:
        print(f"推送请求异常: {e}")

if __name__ == "__main__":
    b_text, md_text = get_merchant_data()
    push_via_notifyme(b_text, md_text)
