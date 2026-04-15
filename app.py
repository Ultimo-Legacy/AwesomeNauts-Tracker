import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import os

# =========================
# CONFIG
# =========================
ELITE_THRESHOLD = 160000

st.set_page_config(page_title="Awesomenauts Tracker", layout="wide")


# =========================
# FILE UPLOAD (CLOUD FIX)
# =========================
uploaded_file = st.file_uploader("Upload ApplicationPersistent.log", type=["log"])


# =========================
# LOG PARSER (YOUR ORIGINAL)
# =========================
def parse_log():
    matches = []
    seen_scores = set()
    current = None

    try:
        with open("ApplicationPersistent.log", "r", encoding="utf-8", errors="ignore") as f:
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
# CLOUD SAFE PARSER
# =========================
def parse_log_from_string(log_data):
    matches = []
    seen_scores = set()
    current = None

    for line in log_data.splitlines():

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
# LOAD DATA (FIXED)
# =========================
if uploaded_file is not None:
    log_data = uploaded_file.getvalue().decode("utf-8", errors="ignore")
    matches = parse_log_from_string(log_data)
else:
    matches = parse_log()

df = pd.DataFrame(matches)

if not df.empty:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values("date").reset_index(drop=True)
    df["rating_delta"] = df["rating"].diff().fillna(0)


today = datetime.now().date()
yesterday = today - timedelta(days=1)


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
    hours = (times.max() - times.min()).total_seconds() / 3600 if len(times) > 1 else 0.0

    return best_day, games, wins, losses, winrate, hours, int(best_gain)


# =========================
# UI HEADER
# =========================
st.markdown("""
<div style="text-align:center;">
    <h1>🎮 Awesomenauts Tracker</h1>
    <p>Upload your ApplicationPersistent.log</p>
</div>
""", unsafe_allow_html=True)


# =========================
# STOP IF NO DATA
# =========================
if df.empty:
    st.info("Upload your log file to view stats.")
    st.stop()


# =========================
# ALL TIME STATS
# =========================
first_match = df["date"].min().strftime("%d %b %Y")

st.markdown(f"## 📊 All-Time Stats - 📅 From {first_match}")

games = len(df)
wins = int(df["won"].sum())
losses = games - wins
winrate = round((wins / games) * 100, 1)

hours = (df["date"].max() - df["date"].min()).total_seconds() / 3600

st.markdown(f"""
Games: {games}  
Wins: {wins}  
Losses: {losses}  
Winrate: {winrate}%  
Time Played: {hours:.2f} hrs  
⭐ Rating Earned: {int(df["rating_delta"].sum()):+}
""")


# =========================
# WIN STREAK
# =========================
st.markdown("## 🔥 Win Streak")
best, current = win_streak(matches)
st.write(f"Current: {current}")
st.write(f"Best: {best}")


# =========================
# PERFORMANCE
# =========================
st.markdown("## 📊 Performance")

today_df = df[df["date"].dt.date == today]
yesterday_df = df[df["date"].dt.date == yesterday]


def render(title, data, date_label):
    if data.empty:
        return

    games = len(data)
    wins = int(data["won"].sum())
    losses = games - wins
    winrate = round((wins / games) * 100, 1)

    hours = (data["date"].max() - data["date"].min()).total_seconds() / 3600

    st.markdown(f"""
### 📅 {title} {date_label}
Games: {games}  
Wins: {wins}  
Losses: {losses}  
Winrate: {winrate}%  
Time Played: {hours:.2f} hrs  
⭐ Rating Earned: {int(data["rating_delta"].sum()):+}
""")

render("Today", today_df, today.strftime("%d %b %Y"))
render("Yesterday", yesterday_df, yesterday.strftime("%d %b %Y"))


# =========================
# MATCH HISTORY
# =========================
st.markdown("## 📜 Match History")

display_df = df.copy()

display_df["Result"] = display_df["won"].apply(lambda x: "🟢 WIN" if x else "🔴 LOSS")

st.dataframe(display_df, use_container_width=True)