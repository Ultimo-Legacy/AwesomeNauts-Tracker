uploaded_file = st.file_uploader("Upload ApplicationPersistent.log", type=["log"])

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import os
import base64

# =========================
# CONFIG
# =========================
LOG_PATH = r"C:\Users\anize\Steam\steamapps\common\Awesomenauts\ApplicationPersistent.log"

IMG_LEFT = r"C:\Users\anize\Steam\steamapps\common\Awesomenauts\Awesomenauts - Image1.jpg"
IMG_RIGHT = r"C:\Users\anize\Steam\steamapps\common\Awesomenauts\Awesomenauts - Image2.jpg"

ELITE_THRESHOLD = 160000

st.set_page_config(page_title="Awesomenauts Tracker", layout="wide")


# =========================
# BOX STYLE (ONLY ADDITION)
# =========================
BOX_STYLE = """
<div style="
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 14px;
    border-radius: 10px;
    margin-bottom: 10px;
">
"""
CLOSE_BOX = "</div>"


# =========================
# LOG PARSER
# =========================
@st.cache_data(ttl=10)
def parse_log():
    matches = []
    seen_scores = set()
    current = None

    try:
        with open(LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except:
        return []

    for line in lines:

        if "Match start" in line:
            current = {
                "date": None,
                "rating": None,
                "mu": None,
                "sigma": None,
                "won": False
            }

            try:
                date_str = line.split("\t")[0]
                current["date"] = datetime.strptime(date_str, "%Y-%m-%d %a %H:%M:%S")
            except:
                current["date"] = None

        if current is None:
            continue

        if "Own team won." in line:
            current["won"] = True

        if "Uploading new mean score" in line:
            try:
                current["mu"] = float(line.strip().split()[-1])
            except:
                pass

        if "Uploading new stddev score" in line:
            try:
                current["sigma"] = float(line.strip().split()[-1])
            except:
                pass

        if "Uploading new ranking score" in line:
            try:
                rating = int(line.strip().split()[-1])
            except:
                continue

            if rating in seen_scores:
                continue

            seen_scores.add(rating)
            current["rating"] = rating
            matches.append(current.copy())

    return matches


# =========================
# WIN STREAK
# =========================
def win_streak(matches):
    best = 0
    current = 0

    for m in matches:
        if m.get("won"):
            current += 1
            best = max(best, current)
        else:
            current = 0

    return best, current


# =========================
# BEST STATS
# =========================
def best_stats(df):
    if df.empty:
        return None, 0, 0, 0, 0.0, 0.0, 0

    df = df.copy()
    df["date_only"] = df["date"].dt.date

    grouped = df.groupby("date_only")

    best_day = None
    best_gain = -999999
    best_data = None

    for day, data in grouped:
        rating_gain = data["rating_delta"].sum()

        if rating_gain > best_gain:
            best_gain = rating_gain
            best_day = day
            best_data = data

    games = len(best_data)
    wins = int(best_data["won"].sum())
    losses = games - wins
    winrate = round((wins / games) * 100, 1)

    times = best_data["date"].dropna()
    if len(times) > 1:
        hours = (times.max() - times.min()).total_seconds() / 3600
    else:
        hours = 0.0

    return best_day, games, wins, losses, winrate, hours, int(best_gain)


# =========================
# LOAD DATA
# =========================
if uploaded_file is not None:
    log_data = uploaded_file.read().decode("utf-8")
    matches = parse_log_from_string(log_data)
else:
    matches = []
def parse_log_from_string(log_data):
    matches = []
    seen_scores = set()
    current = None

    lines = log_data.splitlines()

    for line in lines:

        if "Match start" in line:
            current = {
                "date": None,
                "rating": None,
                "mu": None,
                "sigma": None,
                "won": False
            }

            try:
                date_str = line.split("\t")[0]
                current["date"] = datetime.strptime(date_str, "%Y-%m-%d %a %H:%M:%S")
            except:
                current["date"] = None

        if current is None:
            continue

        if "Own team won." in line:
            current["won"] = True

        if "Uploading new mean score" in line:
            try:
                current["mu"] = float(line.strip().split()[-1])
            except:
                pass

        if "Uploading new stddev score" in line:
            try:
                current["sigma"] = float(line.strip().split()[-1])
            except:
                pass

        if "Uploading new ranking score" in line:
            try:
                rating = int(line.strip().split()[-1])
            except:
                continue

            if rating in seen_scores:
                continue

            seen_scores.add(rating)
            current["rating"] = rating
            matches.append(current.copy())

    return matches
df = pd.DataFrame(matches)

if not df.empty:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

today = datetime.now().date()
yesterday = today - timedelta(days=1)

if not df.empty:
    df = df.sort_values("date").reset_index(drop=True)
    df["rating_delta"] = df["rating"].diff().fillna(0)


# =========================
# HEADER
# =========================
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    if os.path.exists(IMG_LEFT):
        st.image(IMG_LEFT, width=360)

with col2:
    st.markdown(
        """
        <div style="text-align:center; padding: 10px 0;">
            <div style="font-size:34px; font-weight:800;">
                🎮 Awesomenauts Tracker
            </div>
            <div style="font-size:18px; opacity:0.85; margin-top:6px;">
                Player Stats - Ultimo-Legacy
            </div>
            <div style="font-size:14px; opacity:0.6; margin-top:4px;">
                Platform - STEAM
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    icon_path = r"C:\Users\anize\Steam\steamapps\common\Awesomenauts\Ultimo-Legacy-Icon.jpg"

    if os.path.exists(icon_path):
        with open(icon_path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode()

        st.markdown(f"""
        <div style="text-align:center; margin-top:10px;">
            <img src="data:image/png;base64,{encoded}" width="120"/>
        </div>
        """, unsafe_allow_html=True)

with col3:
    if os.path.exists(IMG_RIGHT):
        st.image(IMG_RIGHT, width=360)

st.button("🔄 Refresh", on_click=lambda: st.rerun())


# =========================
# TOP ROW (ALL BOXED)
# =========================
col1, col2, col3 = st.columns(3)

with col1:

    first_match_date = df["date"].min().strftime("%d %b %Y") if not df.empty else "Unknown"

    st.markdown(
        BOX_STYLE + f"📊 <b>All-Time Stats - 📅 From {first_match_date}</b>",
        unsafe_allow_html=True
    )

    if not df.empty:
        games = len(df)
        wins = int(df["won"].sum())
        losses = games - wins
        winrate = round((wins / games) * 100, 1)

        times = df["date"].dropna()
        hours = (times.max() - times.min()).total_seconds() / 3600 if len(times) > 1 else 0.0

        total_rating = int(df["rating_delta"].sum())

        st.markdown(f"""
Games: {games}  
Wins: {wins}  
Losses: {losses}  
Winrate: {winrate}%  
Time Played: {hours:.2f} hrs  
⭐ Rating Earned: {total_rating:+}
""", unsafe_allow_html=True)

    st.markdown(CLOSE_BOX, unsafe_allow_html=True)


with col2:
    best, current = win_streak(matches)

    st.markdown(BOX_STYLE + "🔥 <b>Win Streak</b>", unsafe_allow_html=True)

    st.markdown(f"""
Current streak: {current}  
Best streak: {best}
""", unsafe_allow_html=True)

    st.markdown(CLOSE_BOX, unsafe_allow_html=True)


with col3:
    st.markdown(BOX_STYLE + "🏆 <b>Leaderboard Rating Progress</b>", unsafe_allow_html=True)

    if not df.empty and df["rating"].notna().any():
        current_rating = int(df.iloc[-1]["rating"])
        st.markdown(f"Current: {current_rating}")
        st.progress(min(current_rating / ELITE_THRESHOLD, 1.0))

    st.markdown(CLOSE_BOX, unsafe_allow_html=True)


# =========================
# PERFORMANCE HEADER
# =========================
st.markdown(BOX_STYLE + "📊 <b>Performance</b>" + CLOSE_BOX, unsafe_allow_html=True)

if not df.empty:

    today_df = df[df["date"].dt.date == today]
    yesterday_df = df[df["date"].dt.date == yesterday]
    last7_df = df[df["date"].dt.date >= (today - timedelta(days=7))]

    def get_stats(data):
        if data.empty:
            return 0, 0, 0, 0.0, 0.0, 0

        games = len(data)
        wins = int(data["won"].sum())
        losses = games - wins
        winrate = round((wins / games) * 100, 1)

        times = data["date"].dropna()
        hours = (times.max() - times.min()).total_seconds() / 3600 if len(times) > 1 else 0.0

        rating_gain = int(data["rating_delta"].sum())

        return games, wins, losses, winrate, hours, rating_gain

    def render_block(title, data, date_value):
        games, wins, losses, winrate, hours, rating_gain = get_stats(data)
        formatted_date = date_value.strftime("%d %b %Y")

        st.markdown(f"""
<div style="margin-bottom:12px;"></div>

### 📅 {title} {formatted_date}

Games: {games}  
Wins: {wins}  
Losses: {losses}  
Winrate: {winrate}%  
Time Played: {hours:.2f} hrs  
⭐ Rating Earned: {rating_gain:+}

<br><br>
""", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        render_block("Today", today_df, today)

    with col2:
        render_block("Yesterday", yesterday_df, yesterday)

    with col3:
        render_block("Last 7 Days", last7_df, today - timedelta(days=7))


# =========================
# MATCH HISTORY
# =========================
st.markdown("""
<div style="text-align:center; font-size:26px; font-weight:800; margin-top:20px;">
📜 Match History
</div>
""", unsafe_allow_html=True)

if not df.empty:

    best_day, games, wins, losses, winrate, hours, gain = best_stats(df)

    col_left, col_right = st.columns([1, 3])

    with col_left:
        if best_day is not None:
            st.markdown(f"""
<div style="
    background: rgba(255,255,255,0.03);
    padding: 16px;
    border-radius: 10px;
    border: 1px solid rgba(255,255,255,0.08);
">

### 📅 Best Stats ({best_day.strftime("%d %b %Y")})

**Games:** {games}  
**Wins:** {wins}  
**Losses:** {losses}  
**Winrate:** {winrate}%  
**Time Played:** {hours:.2f} hrs  
⭐ **Rating Earned:** {gain:+}

</div>
""", unsafe_allow_html=True)

    with col_right:

        display_df = df.copy()

        def result(row):
            if row.get("rating") == 100000:
                return "🟠 ERROR - Default Rating"
            if row.get("won") is True:
                return "🟢 WIN"
            elif row.get("won") is False:
                return "🔴 LOSS"
            return "🟠 DISCONNECT"

        display_df["Result"] = display_df.apply(result, axis=1)
        display_df["Rating Earned Per Match"] = display_df["rating_delta"].astype(int)

        display_df = display_df.rename(columns={
            "date": "📅 Match Date",
            "rating": "⭐ Rating",
            "mu": "🎯 MU - Skill Rating",
            "sigma": "📈 Sigma - Consistency"
        })

        display_df = display_df[
            [
                "📅 Match Date",
                "⭐ Rating",
                "Rating Earned Per Match",
                "🎯 MU - Skill Rating",
                "📈 Sigma - Consistency",
                "Result"
            ]
        ][::-1]

        st.data_editor(
            display_df,
            use_container_width=True,
            disabled=True
        )