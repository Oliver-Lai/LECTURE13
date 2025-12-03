"""Taiwan Weather Temperature Map - Streamlit Application."""

import logging
import time
from datetime import datetime

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from src.scraper import (
    fetch_weather_data,
    fetch_weekly_forecast,
    get_forecast_dates,
    get_forecast_by_date
)
from src.storage import WeatherDatabase
from src.visualization import (
    calculate_statistics,
    create_folium_map,
    TEMPERATURE_COLORS
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Taiwan Weather Map",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded"
)


def init_session_state():
    """Initialize session state variables."""
    if 'weather_data' not in st.session_state:
        st.session_state.weather_data = None
    if 'forecast_data' not in st.session_state:
        st.session_state.forecast_data = None
    if 'last_update' not in st.session_state:
        st.session_state.last_update = None
    if 'db' not in st.session_state:
        st.session_state.db = WeatherDatabase("data/weather.db")
    if 'view_mode' not in st.session_state:
        st.session_state.view_mode = "即時觀測"
    if 'selected_time' not in st.session_state:
        st.session_state.selected_time = None
    if 'animation_running' not in st.session_state:
        st.session_state.animation_running = False
    if 'display_mode' not in st.session_state:
        st.session_state.display_mode = "地圖"  # 地圖 or 表格


def load_realtime_data(force_refresh: bool = False) -> list[dict]:
    """Load real-time weather data."""
    if force_refresh or st.session_state.weather_data is None:
        try:
            with st.spinner("正在取得即時觀測資料..."):
                data = fetch_weather_data()
                st.session_state.db.save_weather_data(data)
                st.session_state.weather_data = data
                st.session_state.last_update = datetime.now()
        except Exception as e:
            st.error(f"❌ 無法取得資料: {e}")
            try:
                data = st.session_state.db.get_latest_data()
                if data:
                    st.session_state.weather_data = data
                    st.warning("⚠️ 使用資料庫中的舊資料")
            except:
                pass
    return st.session_state.weather_data or []


def load_forecast_data(force_refresh: bool = False) -> dict:
    """Load weekly forecast data."""
    if force_refresh or st.session_state.forecast_data is None:
        try:
            with st.spinner("正在取得一週預報資料..."):
                forecast = fetch_weekly_forecast()
                st.session_state.forecast_data = forecast
                st.session_state.last_update = datetime.now()
                
                # Set default selected time
                dates = get_forecast_dates(forecast)
                if dates and not st.session_state.selected_time:
                    st.session_state.selected_time = dates[0]
        except Exception as e:
            st.error(f"❌ 無法取得預報: {e}")
    return st.session_state.forecast_data or {"dates": [], "by_date": {}}


def render_sidebar():
    """Render sidebar controls."""
    st.sidebar.title("🌡️ 台灣氣象地圖")
    
    # View mode
    st.sidebar.header("📺 顯示模式")
    mode = st.sidebar.radio(
        "選擇模式",
        ["即時觀測", "一週預報"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    if mode != st.session_state.view_mode:
        st.session_state.view_mode = mode
        st.session_state.animation_running = False
        st.rerun()
    
    st.sidebar.divider()
    
    # Refresh button
    if st.sidebar.button("🔄 重新整理", use_container_width=True):
        if st.session_state.view_mode == "即時觀測":
            load_realtime_data(force_refresh=True)
        else:
            load_forecast_data(force_refresh=True)
        st.rerun()
    
    if st.session_state.last_update:
        st.sidebar.caption(f"更新: {st.session_state.last_update.strftime('%H:%M:%S')}")
    
    return mode


def render_forecast_controls(forecast: dict):
    """Render forecast time selection controls."""
    dates = get_forecast_dates(forecast)
    if not dates:
        return None
    
    st.sidebar.divider()
    st.sidebar.header("📅 預報時間")
    
    # Format display options
    display_map = {}
    for d in dates:
        try:
            dt = datetime.strptime(d, "%Y-%m-%d %H:%M")
            weekdays = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]
            display = f"{dt.strftime('%m/%d')} {weekdays[dt.weekday()]} {dt.strftime('%H:%M')}"
            display_map[display] = d
        except:
            display_map[d] = d
    
    display_options = list(display_map.keys())
    
    # Find current index
    current_idx = 0
    for i, (disp, key) in enumerate(display_map.items()):
        if key == st.session_state.selected_time:
            current_idx = i
            break
    
    # Dropdown selector
    selected_display = st.sidebar.selectbox(
        "選擇時間",
        options=display_options,
        index=current_idx,
        label_visibility="collapsed"
    )
    st.session_state.selected_time = display_map[selected_display]
    
    # Slider
    slider_val = st.sidebar.slider(
        "時間軸",
        0, len(dates) - 1,
        current_idx,
        format=f"第 %d 時段"
    )
    if slider_val != current_idx:
        st.session_state.selected_time = dates[slider_val]
        st.rerun()
    
    st.sidebar.divider()
    
    # Animation controls
    st.sidebar.header("🎬 動畫播放")
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("▶️ 播放", use_container_width=True):
            st.session_state.animation_running = True
            st.rerun()
    
    with col2:
        if st.button("⏹️ 停止", use_container_width=True):
            st.session_state.animation_running = False
            st.rerun()
    
    speed = st.sidebar.slider("速度", 0.5, 2.0, 1.0, 0.5, format="%.1f秒")
    
    return st.session_state.selected_time, speed, dates


def render_statistics(data: list[dict]):
    """Render statistics in sidebar."""
    if not data:
        return
    
    st.sidebar.divider()
    st.sidebar.header("📊 統計")
    
    stats = calculate_statistics(data)
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("站數", stats['count'])
    with col2:
        if stats['avg_temp']:
            st.metric("平均", f"{stats['avg_temp']}°C")
    
    if stats['max_temp']:
        st.sidebar.metric("🔥 最高", f"{stats['max_temp']}°C", stats['max_location'], delta_color="off")
    if stats['min_temp']:
        st.sidebar.metric("❄️ 最低", f"{stats['min_temp']}°C", stats['min_location'], delta_color="off")


def render_legend():
    """Render temperature legend."""
    st.sidebar.divider()
    st.sidebar.header("🎨 圖例")
    
    for _, _, color, label in TEMPERATURE_COLORS:
        st.sidebar.markdown(
            f'<div style="display:flex;align-items:center;margin:3px 0;">'
            f'<span style="background:{color};width:18px;height:18px;'
            f'display:inline-block;margin-right:8px;border-radius:50%;'
            f'border:1px solid #ccc;"></span><span>{label}</span></div>',
            unsafe_allow_html=True
        )


def render_map(data: list[dict], title: str = ""):
    """Render the weather map."""
    if not data:
        st.warning("⚠️ 沒有資料")
        return
    
    try:
        m = create_folium_map(data)
        st_folium(m, width=None, height=600, returned_objects=[])
    except Exception as e:
        st.error(f"❌ 地圖載入失敗: {e}")


def render_realtime_table(data: list[dict]):
    """Render real-time data as filterable table."""
    if not data:
        st.warning("⚠️ 沒有資料")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Rename columns for display
    df_display = df[['location_name', 'county_name', 'town_name', 'temperature', 
                     'weather_description', 'humidity', 'wind_speed', 'observation_time']].copy()
    df_display.columns = ['站名', '縣市', '鄉鎮', '溫度(°C)', '天氣', '濕度(%)', '風速(m/s)', '觀測時間']
    
    # Filters
    st.subheader("🔍 篩選條件")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        counties = ['全部'] + sorted(df_display['縣市'].dropna().unique().tolist())
        selected_county = st.selectbox("選擇縣市", counties, key="rt_county")
    
    with col2:
        if selected_county != '全部':
            towns = ['全部'] + sorted(df_display[df_display['縣市'] == selected_county]['鄉鎮'].dropna().unique().tolist())
        else:
            towns = ['全部'] + sorted(df_display['鄉鎮'].dropna().unique().tolist())
        selected_town = st.selectbox("選擇鄉鎮", towns, key="rt_town")
    
    with col3:
        temp_range = st.slider(
            "溫度範圍 (°C)",
            min_value=int(df_display['溫度(°C)'].min()) if not df_display['溫度(°C)'].isna().all() else 0,
            max_value=int(df_display['溫度(°C)'].max()) + 1 if not df_display['溫度(°C)'].isna().all() else 40,
            value=(int(df_display['溫度(°C)'].min()) if not df_display['溫度(°C)'].isna().all() else 0,
                   int(df_display['溫度(°C)'].max()) + 1 if not df_display['溫度(°C)'].isna().all() else 40),
            key="rt_temp"
        )
    
    # Apply filters
    filtered_df = df_display.copy()
    if selected_county != '全部':
        filtered_df = filtered_df[filtered_df['縣市'] == selected_county]
    if selected_town != '全部':
        filtered_df = filtered_df[filtered_df['鄉鎮'] == selected_town]
    filtered_df = filtered_df[
        (filtered_df['溫度(°C)'] >= temp_range[0]) & 
        (filtered_df['溫度(°C)'] <= temp_range[1])
    ]
    
    # Format observation time
    filtered_df['觀測時間'] = filtered_df['觀測時間'].apply(
        lambda x: x.replace('T', ' ').replace('+08:00', '') if pd.notna(x) else ''
    )
    
    # Display stats
    st.caption(f"顯示 {len(filtered_df)} / {len(df_display)} 筆資料")
    
    # Display table with styling
    st.dataframe(
        filtered_df.style.background_gradient(subset=['溫度(°C)'], cmap='RdYlBu_r'),
        use_container_width=True,
        height=500
    )
    
    # Download button
    csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        "📥 下載 CSV",
        csv,
        "weather_data.csv",
        "text/csv",
        key="download_rt"
    )


def render_forecast_table(forecast: dict):
    """Render forecast data as filterable table."""
    if not forecast or not forecast.get('dates'):
        st.warning("⚠️ 沒有預報資料")
        return
    
    # Build complete DataFrame from all dates
    all_records = []
    for date_key in forecast['dates']:
        for record in forecast.get('by_date', {}).get(date_key, []):
            all_records.append({
                '時間': date_key,
                '縣市': record.get('location_name', ''),
                '溫度(°C)': record.get('temperature'),
                '天氣': record.get('weather_description', ''),
                '經度': record.get('longitude'),
                '緯度': record.get('latitude')
            })
    
    if not all_records:
        st.warning("⚠️ 沒有資料")
        return
    
    df = pd.DataFrame(all_records)
    
    # Filters
    st.subheader("🔍 篩選條件")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        counties = ['全部'] + sorted(df['縣市'].unique().tolist())
        selected_county = st.selectbox("選擇縣市", counties, key="fc_county")
    
    with col2:
        # Format time options for display
        time_options = ['全部']
        time_display_map = {'全部': '全部'}
        for t in forecast['dates']:
            try:
                dt = datetime.strptime(t, "%Y-%m-%d %H:%M")
                weekdays = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]
                display = f"{dt.strftime('%m/%d')} {weekdays[dt.weekday()]} {dt.strftime('%H:%M')}"
                time_options.append(display)
                time_display_map[display] = t
            except:
                time_options.append(t)
                time_display_map[t] = t
        
        selected_time_display = st.selectbox("選擇時間", time_options, key="fc_time")
        selected_time = time_display_map[selected_time_display]
    
    with col3:
        temp_min = df['溫度(°C)'].min() if not df['溫度(°C)'].isna().all() else 0
        temp_max = df['溫度(°C)'].max() if not df['溫度(°C)'].isna().all() else 40
        temp_range = st.slider(
            "溫度範圍 (°C)",
            min_value=int(temp_min),
            max_value=int(temp_max) + 1,
            value=(int(temp_min), int(temp_max) + 1),
            key="fc_temp"
        )
    
    # Apply filters
    filtered_df = df.copy()
    if selected_county != '全部':
        filtered_df = filtered_df[filtered_df['縣市'] == selected_county]
    if selected_time != '全部':
        filtered_df = filtered_df[filtered_df['時間'] == selected_time]
    filtered_df = filtered_df[
        (filtered_df['溫度(°C)'] >= temp_range[0]) & 
        (filtered_df['溫度(°C)'] <= temp_range[1])
    ]
    
    # Format time for display
    def format_time(t):
        try:
            dt = datetime.strptime(t, "%Y-%m-%d %H:%M")
            weekdays = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]
            return f"{dt.strftime('%m/%d')} {weekdays[dt.weekday()]} {dt.strftime('%H:%M')}"
        except:
            return t
    
    display_df = filtered_df.copy()
    display_df['時間'] = display_df['時間'].apply(format_time)
    display_df = display_df[['時間', '縣市', '溫度(°C)', '天氣']]
    
    # Display stats
    st.caption(f"顯示 {len(filtered_df)} / {len(df)} 筆資料")
    
    # Display table
    st.dataframe(
        display_df.style.background_gradient(subset=['溫度(°C)'], cmap='RdYlBu_r'),
        use_container_width=True,
        height=500
    )
    
    # Pivot table view
    with st.expander("📊 樞紐分析表 (縣市 × 時間)"):
        pivot_df = df.pivot_table(
            values='溫度(°C)', 
            index='縣市', 
            columns='時間', 
            aggfunc='first'
        )
        # Rename columns to shorter format
        pivot_df.columns = [format_time(c) for c in pivot_df.columns]
        st.dataframe(
            pivot_df.style.background_gradient(cmap='RdYlBu_r', axis=None),
            use_container_width=True
        )
    
    # Download button
    csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        "📥 下載 CSV",
        csv,
        "forecast_data.csv",
        "text/csv",
        key="download_fc"
    )


def run_animation(forecast: dict, speed: float, dates: list[str]):
    """Run forecast animation."""
    if not dates:
        return
    
    # Find starting index
    start_idx = 0
    if st.session_state.selected_time in dates:
        start_idx = dates.index(st.session_state.selected_time)
    
    # Placeholders
    time_placeholder = st.empty()
    stats_placeholder = st.empty()
    map_placeholder = st.empty()
    
    idx = start_idx
    
    while st.session_state.animation_running:
        current_time = dates[idx]
        data = get_forecast_by_date(forecast, current_time)
        
        # Display time
        try:
            dt = datetime.strptime(current_time, "%Y-%m-%d %H:%M")
            weekdays = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]
            time_str = f"📅 {dt.strftime('%Y/%m/%d')} {weekdays[dt.weekday()]} {dt.strftime('%H:%M')}"
        except:
            time_str = current_time
        
        time_placeholder.markdown(f"### {time_str}")
        
        # Statistics
        with stats_placeholder.container():
            stats = calculate_statistics(data)
            cols = st.columns(4)
            cols[0].metric("縣市數", stats['count'])
            cols[1].metric("平均", f"{stats['avg_temp']}°C" if stats['avg_temp'] else "N/A")
            cols[2].metric("最高", f"{stats['max_temp']}°C" if stats['max_temp'] else "N/A")
            cols[3].metric("最低", f"{stats['min_temp']}°C" if stats['min_temp'] else "N/A")
        
        # Map
        with map_placeholder.container():
            m = create_folium_map(data)
            st_folium(m, width=None, height=500, returned_objects=[])
        
        st.session_state.selected_time = current_time
        
        idx = (idx + 1) % len(dates)
        time.sleep(speed)
    
    st.rerun()


def main():
    """Main entry point."""
    init_session_state()
    
    mode = render_sidebar()
    
    if mode == "即時觀測":
        # Real-time mode
        data = load_realtime_data()
        render_statistics(data)
        render_legend()
        
        st.title("🌡️ 台灣即時氣溫地圖")
        st.caption("資料來源: 中央氣象署 | 觀測站即時資料")
        
        # Display mode tabs
        tab1, tab2 = st.tabs(["🗺️ 地圖檢視", "📋 表格檢視"])
        
        with tab1:
            render_map(data)
        
        with tab2:
            render_realtime_table(data)
        
    else:
        # Forecast mode
        forecast = load_forecast_data()
        
        result = render_forecast_controls(forecast)
        if result:
            selected_time, speed, dates = result
            data = get_forecast_by_date(forecast, selected_time)
        else:
            data = []
            speed = 1.0
            dates = []
        
        render_statistics(data)
        render_legend()
        
        st.title("🌡️ 台灣一週氣溫預報")
        st.caption("資料來源: 中央氣象署 | 縣市一週預報")
        
        # Display mode tabs
        tab1, tab2 = st.tabs(["🗺️ 地圖檢視", "📋 表格檢視"])
        
        with tab1:
            # Display current time
            if st.session_state.selected_time:
                try:
                    dt = datetime.strptime(st.session_state.selected_time, "%Y-%m-%d %H:%M")
                    weekdays = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]
                    st.markdown(f"### 📅 {dt.strftime('%Y/%m/%d')} {weekdays[dt.weekday()]} {dt.strftime('%H:%M')}")
                except:
                    st.markdown(f"### 📅 {st.session_state.selected_time}")
            
            # Handle animation or static display
            if st.session_state.animation_running and dates:
                run_animation(forecast, speed, dates)
            else:
                render_map(data)
        
        with tab2:
            render_forecast_table(forecast)
    
    # Footer
    st.divider()
    st.caption("💡 點擊標記查看詳情 | 滾輪縮放 | 拖曳移動")


if __name__ == "__main__":
    main()
