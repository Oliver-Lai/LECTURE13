# 🌡️ Taiwan Weather Temperature Map

台灣即時氣溫地圖與一週預報視覺化應用程式

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://lecture13-keqensq2w6lbkckuzltrmc.streamlit.app/)

## 功能特色

### 即時觀測
- 🗺️ 互動式地圖顯示全台 ~300 個氣象觀測站
- 🌡️ 溫度色彩標記（藍色低溫 → 紅色高溫）
- 📊 統計資料（平均、最高、最低溫度）
- 📋 可篩選的資料表格（縣市、鄉鎮、溫度範圍）

### 一週預報
- 📅 縣市級一週氣溫預報（22 縣市、14 個時段）
- ⏰ 時間選擇器切換不同預報時段
- 🎬 動畫播放功能展示氣溫變化
- 📊 樞紐分析表（縣市 × 時間）

### 資料來源
- 中央氣象署 OpenData API
- O-A0003-001：即時觀測站資料
- F-D0047-091：縣市一週天氣預報

## 本地開發

### 1. 建立虛擬環境
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
```

### 2. 安裝依賴
```bash
pip install -r requirements.txt
```

### 3. 設定 API Key
建立 `.env` 檔案：
```
CWA_API_KEY=your_api_key_here
```

### 4. 執行應用程式
```bash
streamlit run app.py
```

## Streamlit Cloud 部署

### 步驟 1：準備 GitHub 儲存庫
1. 在 GitHub 建立新的 Repository
2. 上傳此專案的所有檔案（除了 `.env`、`LECTURE13/`、`data/` 資料夾）

### 步驟 2：連結 Streamlit Cloud
1. 前往 [share.streamlit.io](https://share.streamlit.io)
2. 使用 GitHub 帳號登入
3. 點擊 "New app"
4. 選擇您的 Repository 和 `app.py`

### 步驟 3：設定 Secrets
在 Streamlit Cloud 的 App Settings → Secrets 中加入：
```toml
CWA_API_KEY = "your_api_key_here"
```

### 步驟 4：部署
點擊 "Deploy" 即可！

## 專案結構

```
├── app.py              # 主應用程式
├── requirements.txt    # Python 依賴
├── .streamlit/
│   └── config.toml     # Streamlit 設定
├── src/
│   ├── __init__.py
│   ├── config.py       # 設定與環境變數
│   ├── scraper.py      # 氣象資料爬蟲
│   ├── storage.py      # SQLite 資料庫
│   └── visualization.py # 地圖視覺化
└── data/               # 資料庫存放位置
```

## 授權

MIT License
