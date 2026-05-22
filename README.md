# 🌺 小红书内容自动生成系统
> 马来语课程专用 · DeepSeek × GPT Image 1 × Google Drive

## 系统流程
```
输入主题
  └─ DeepSeek → 生成 N 个爆款大标题
       └─ 选择标题 → DeepSeek → 生成小红书文案
            └─ OpenAI gpt-image-1 → 生成竖版配图
                 └─ Google Drive → 自动上传文案(.txt) + 图片(.png)
```

---

## 🚀 用 Claude Code 跑起来（推荐方式）

### 第一步：安装 Claude Code
```bash
npm install -g @anthropic-ai/claude-code
```

### 第二步：进入项目，打开 Claude Code
```bash
cd xiaohongshu_system
claude
```

### 第三步：告诉 Claude Code 帮你跑起来
把以下内容贴给 Claude Code：

```
帮我把这个小红书内容生成系统跑起来：
1. 先安装 requirements.txt 的所有依赖
2. 检查 app.py 有没有问题
3. 帮我创建 .env 文件（复制 .env.example）
4. 告诉我怎么配置 Google Drive Service Account
5. 最后用 streamlit run app.py 启动
```

---

## 📋 手动安装步骤

### 1. 安装 Python 依赖
```bash
pip install -r requirements.txt
```

### 2. 配置 API Keys
```bash
cp .env.example .env
# 然后用任意编辑器打开 .env，填入你的 Key
```

### 3. 配置 Google Drive（最重要一步）

**a. 在 Google Cloud Console 创建 Service Account：**
1. 打开 https://console.cloud.google.com/
2. 新建项目（或使用现有项目）
3. 左侧菜单 → APIs & Services → Enabled APIs → 搜索并启用 "Google Drive API"
4. 左侧菜单 → IAM & Admin → Service Accounts → 创建 Service Account
5. 下载 JSON 密钥文件，保存到项目目录

**b. 把 Service Account 加入 Google Drive 文件夹：**
1. 打开目标 Google Drive 文件夹
2. 右键 → 共享
3. 粘贴 Service Account 的邮箱（在 JSON 文件里找 `client_email` 字段）
4. 权限设为 **编辑者**

**c. 获取 Folder ID：**
```
https://drive.google.com/drive/folders/【这里就是 Folder ID】
```

### 4. 启动系统
```bash
streamlit run app.py
```
浏览器会自动打开 `http://localhost:8501`

---

## 💡 给 Claude Code 的进阶指令

如果你想扩展功能，直接告诉 Claude Code：

**批量定时生成：**
```
帮我加一个定时功能，每天早上9点自动生成5套内容并上传Drive
```

**多账号支持：**
```
帮我支持多个 Google Drive 文件夹，可以在 UI 里切换目标文件夹
```

**内容历史记录：**
```
帮我把每次生成的记录保存到 SQLite，并在 UI 里显示历史记录
```

**小红书格式优化：**
```
帮我加一个功能，可以自定义文案风格（种草型/干货型/故事型）
```

---

## 📁 文件结构
```
xiaohongshu_system/
├── app.py              # 主程序（Streamlit UI）
├── requirements.txt    # Python 依赖
├── .env.example        # 环境变量模板
├── .env               # 你的实际配置（不要上传到 git！）
└── README.md          # 本文档
```

---

## ⚠️ 注意事项
- `.env` 文件含有 API Keys，**不要上传到 GitHub**
- `gpt-image-1` 每张图片约消耗 $0.04-0.08 USD
- DeepSeek API 费用极低，生成文案约 $0.001/篇
- Google Drive API 免费，无限量
