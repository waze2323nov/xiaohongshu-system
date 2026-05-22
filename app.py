import streamlit as st
import os
import json
import requests
import base64
import pickle
from openai import OpenAI
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", st.secrets.get("DEEPSEEK_API_KEY", ""))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", st.secrets.get("OPENAI_API_KEY", ""))
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", st.secrets.get("GOOGLE_DRIVE_FOLDER_ID", ""))
GOOGLE_TOKEN_BASE64 = os.getenv("GOOGLE_TOKEN_BASE64", st.secrets.get("GOOGLE_TOKEN_BASE64", ""))
OAUTH_CREDENTIALS = "oauth_credentials.json"
TOKEN_FILE = "token.pickle"
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

COURSE_CONTEXT = """
这是一个马来语课程，专门针对在马来西亚生活的华人/中国大陆移民。
课程三级包：
1. 马来西亚生活生存包（初级）RM1200/12小时 - 租房、看病、问路、办手续
2. 人际与职场连接包（中级）RM1600/12小时 - 职场会议、银行、移民厅
3. 商务谈判精英包（高级）RM1800/12小时 - 谈合作、管理员工、政府审批
核心痛点：租房看不懂合同、移民厅不讲英文、开会听不懂、做生意全程马来语、看病说不清症状
"""

PRESET_TOPICS = [
    "🏠 新移民租房踩坑", "🏛️ 移民厅跑流程", "💼 外派工程师",
    "🛒 巴刹夜市生活", "💰 大马做生意", "🏥 在大马看病",
    "👨‍👩‍👧 陪读妈妈", "🗣️ 学马来语心得",
]

def generate_titles(topic, num=5):
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    prompt = f"""你是小红书爆款标题专家。背景：{COURSE_CONTEXT}
主题：{topic}
生成{num}个爆款小红书标题，要求：强烈共鸣感、针对马来西亚华人/中国移民、口语化、每个带1-2个emoji、15-30字、多样化类型。
只返回标题列表，每行一个，不要编号。"""
    resp = requests.post("https://api.deepseek.com/chat/completions", headers=headers,
        json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "max_tokens": 600, "temperature": 0.9}, timeout=30)
    resp.raise_for_status()
    text = resp.json()["choices"][0]["message"]["content"]
    return [t.strip() for t in text.strip().splitlines() if t.strip()]

def generate_copy(title):
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    prompt = f"""你是小红书爆款文案专家。背景：{COURSE_CONTEXT}
根据标题写小红书文案：【{title}】
格式：标题行 + 空行 + 正文200-250字（强钩子开头、真实场景、口语化、自然融入马来语课程价值、结尾引导互动）+ 空行 + 5个hashtag
只返回文案，不要其他说明。"""
    resp = requests.post("https://api.deepseek.com/chat/completions", headers=headers,
        json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "max_tokens": 900, "temperature": 0.85}, timeout=30)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

def generate_image(title):
    client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = f"""Vibrant vertical social media image for Chinese lifestyle post about living in Malaysia.
Concept: {title}
Style: 小红书 editorial aesthetic, tropical Malaysia atmosphere, warm colors, KL city elements, NO text in image."""
    response = client.images.generate(model="gpt-image-1", prompt=prompt, size="1024x1536", quality="medium", n=1)
    return base64.b64decode(response.data[0].b64_json)

def get_drive_service():
    creds = None
    
    # Method 1: Load from base64 token in secrets (for Streamlit Cloud)
    if GOOGLE_TOKEN_BASE64:
        try:
            token_bytes = base64.b64decode(GOOGLE_TOKEN_BASE64)
            creds = pickle.loads(token_bytes)
        except Exception:
            pass
    
    # Method 2: Load from local token file
    if not creds and os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)
    
    # Refresh if expired
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception:
            creds = None
    
    # Method 3: OAuth flow (local only)
    if not creds and os.path.exists(OAUTH_CREDENTIALS):
        flow = InstalledAppFlow.from_client_secrets_file(OAUTH_CREDENTIALS, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)
    
    if not creds:
        raise Exception("Google Drive 未授权。请在本地先运行 OAuth 授权。")
    
    return build("drive", "v3", credentials=creds)

def upload_to_drive(name, data, mime, folder_id):
    svc = get_drive_service()
    meta = {"name": name, "parents": [folder_id]}
    media = MediaInMemoryUpload(data, mimetype=mime)
    f = svc.files().create(body=meta, media_body=media, fields="id,webViewLink").execute()
    return f.get("webViewLink", "")

def safe_filename(title):
    keep = "".join(c for c in title if c.isalnum() or c in " _-（）()。，,")
    return keep.strip()[:30]

def main():
    st.set_page_config(page_title="小红书内容生成系统", page_icon="🌺", layout="wide", initial_sidebar_state="expanded")
    st.markdown("""<style>
    .stButton > button[kind="primary"] { background: linear-gradient(135deg, #ff4757, #ff6b81); border: none; border-radius: 10px; font-weight: 600; }
    </style>""", unsafe_allow_html=True)

    drive_ready = bool(GOOGLE_TOKEN_BASE64) or os.path.exists(TOKEN_FILE) or os.path.exists(OAUTH_CREDENTIALS)

    with st.sidebar:
        st.markdown("## 🌺 内容生成系统")
        st.caption("DeepSeek × GPT Image × Google Drive")
        st.divider()
        st.markdown("### ⚙️ 生成设置")
        num_titles = st.slider("标题数量", 3, 10, 5)
        auto_upload = st.toggle("自动上传 Google Drive", value=drive_ready)
        show_image_preview = st.toggle("显示图片预览", value=True)
        st.divider()
        st.markdown("### 🔌 API 状态")
        st.success("✅ DeepSeek") if DEEPSEEK_API_KEY else st.error("❌ DeepSeek")
        st.success("✅ OpenAI Image") if OPENAI_API_KEY else st.error("❌ OpenAI")
        if drive_ready:
            st.success("✅ Google Drive")
        else:
            st.warning("⚠️ Google Drive 未配置")

    st.markdown("# 🌺 小红书内容自动生成系统")
    st.caption("马来语课程专用 · 输入主题 → 自动生成标题 + 文案 + 配图 → 一键存入 Google Drive")
    st.markdown("### 📌 选择或输入主题")

    cols = st.columns(4)
    preset_clicked = None
    for i, p in enumerate(PRESET_TOPICS):
        with cols[i % 4]:
            if st.button(p, key=f"p{i}", use_container_width=True):
                preset_clicked = p

    topic = st.text_input("自定义主题", value=preset_clicked or st.session_state.get("topic", ""),
        placeholder="例如：在吉隆坡买车踩坑经验...", label_visibility="collapsed")
    if preset_clicked:
        st.session_state["topic"] = preset_clicked
        topic = preset_clicked

    gen_titles_btn = st.button("🚀 生成标题", type="primary")

    if "titles" not in st.session_state: st.session_state.titles = []
    if "results" not in st.session_state: st.session_state.results = []

    if gen_titles_btn and topic:
        st.session_state.results = []
        with st.spinner("🤔 DeepSeek 正在构思爆款标题…"):
            try:
                st.session_state.titles = generate_titles(topic, num_titles)
                st.session_state["topic"] = topic
            except Exception as e:
                st.error(f"标题生成失败：{e}")

    if st.session_state.titles:
        st.divider()
        st.markdown(f"### ✍️ 选择要制作的标题：")
        selected = []
        for i, t in enumerate(st.session_state.titles):
            if st.checkbox(t, value=True, key=f"chk_{i}"):
                selected.append(t)

        st.caption(f"已选 {len(selected)} 个")
        gen_content_btn = st.button(f"🎨 生成 {len(selected)} 套内容", type="primary", disabled=len(selected)==0)

        if gen_content_btn and selected:
            st.session_state.results = []
            progress = st.progress(0, text="准备中…")
            log = st.empty()

            for i, title in enumerate(selected):
                log.info(f"({i+1}/{len(selected)}) 处理：{title[:25]}…")
                result = {"title": title, "copy": None, "image_bytes": None, "drive_copy_link": None, "drive_img_link": None, "error": None}
                try:
                    progress.progress((i/len(selected))+0.05, text=f"📝 生成文案 ({i+1}/{len(selected)})…")
                    result["copy"] = generate_copy(title)
                    progress.progress((i/len(selected))+0.15, text=f"🎨 生成图片 ({i+1}/{len(selected)})…")
                    result["image_bytes"] = generate_image(title)
                    if auto_upload and GOOGLE_DRIVE_FOLDER_ID:
                        progress.progress((i/len(selected))+0.25, text=f"☁️ 上传 Drive ({i+1}/{len(selected)})…")
                        ts = datetime.now().strftime("%Y%m%d_%H%M")
                        safe = safe_filename(title)
                        result["drive_copy_link"] = upload_to_drive(f"{safe}_{ts}_文案.txt", result["copy"].encode("utf-8"), "text/plain", GOOGLE_DRIVE_FOLDER_ID)
                        result["drive_img_link"] = upload_to_drive(f"{safe}_{ts}_图片.png", result["image_bytes"], "image/png", GOOGLE_DRIVE_FOLDER_ID)
                except Exception as e:
                    result["error"] = str(e)
                st.session_state.results.append(result)
                progress.progress((i+1)/len(selected))

            log.empty()
            st.success(f"🎉 全部完成！共生成 {len(selected)} 套小红书内容")

    if st.session_state.results:
        st.divider()
        st.markdown("### 🎉 生成结果")
        for r in st.session_state.results:
            st.markdown(f"#### 📌 {r['title']}")
            if r["error"]:
                st.error(f"生成失败：{r['error']}")
                continue
            col_copy, col_img = st.columns([1, 1])
            with col_copy:
                st.caption("📝 小红书文案")
                st.text_area("", value=r["copy"] or "", height=320, key=f"ta_{r['title'][:8]}", label_visibility="collapsed")
                if r["copy"]:
                    st.download_button("⬇️ 下载文案", data=r["copy"].encode("utf-8"), file_name=f"{safe_filename(r['title'])}_文案.txt", mime="text/plain", key=f"dl_copy_{r['title'][:8]}")
                if r["drive_copy_link"]:
                    st.link_button("📁 Drive 查看文案", r["drive_copy_link"])
            with col_img:
                st.caption("🖼️ 配图")
                if r["image_bytes"] and show_image_preview:
                    st.image(r["image_bytes"], use_container_width=True)
                if r["image_bytes"]:
                    st.download_button("⬇️ 下载图片", data=r["image_bytes"], file_name=f"{safe_filename(r['title'])}_图片.png", mime="image/png", key=f"dl_img_{r['title'][:8]}")
                if r["drive_img_link"]:
                    st.link_button("📁 Drive 查看图片", r["drive_img_link"])
            st.divider()

if __name__ == "__main__":
    main()
