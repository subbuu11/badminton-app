import streamlit as st
import string
import random
import pandas as pd
import json
import os
import altair as alt

# ---------------- CONFIG & DATA SERVER ----------------
st.set_page_config(page_title="Badminton Manager Pro", layout="centered")

DATA_FILE = "tournament_data.json"

if "reset_key" not in st.session_state:
    st.session_state.reset_key = 0

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                data = json.load(f)
                st.session_state.teams = data.get("teams", {})
                st.session_state.scores = data.get("scores", {})
                st.session_state.completed_matches = data.get("completed_matches", [])
                st.session_state.final_mode = data.get("final_mode", False)
                st.session_state.final_choice = data.get("final_choice", None)
                st.session_state.team_colors = data.get("team_colors", {})
                return True
            except json.JSONDecodeError:
                return False
    return False

def save_data():
    data = {
        "teams": st.session_state.get("teams", {}),
        "scores": st.session_state.get("scores", {}),
        "completed_matches": st.session_state.get("completed_matches", []),
        "final_mode": st.session_state.get("final_mode", False),
        "final_choice": st.session_state.get("final_choice", None),
        "team_colors": st.session_state.get("team_colors", {})
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def reset_scores_and_matches():
    st.session_state.scores = {}
    st.session_state.completed_matches = []
    st.session_state.final_mode = False
    st.session_state.final_choice = None
    st.session_state.reset_key += 1 
    save_data()

def hard_reset_all():
    st.session_state.clear()
    st.session_state.reset_key = 0
    try:
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
    except Exception:
        pass

# ---------------- INITIALIZE DATA ----------------
if "teams" not in st.session_state:
    has_data = load_data()
    if not has_data:
        st.session_state.teams = {}
        st.session_state.scores = {}
        st.session_state.completed_matches = []
        st.session_state.final_mode = False
        st.session_state.final_choice = None 
        st.session_state.team_colors = {}

# ---------------- SIDEBAR CONTROLS ----------------
st.sidebar.header("⚙️ Data Management")
st.sidebar.button("🔄 Reset Scores & Matches", on_click=reset_scores_and_matches)
st.sidebar.button("⚠️ Hard Reset All Data", type="primary", on_click=hard_reset_all)

# ---------------- UI STYLING ----------------
st.markdown("""
<style>
    @media (max-width: 768px) {
        .block-container { padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
        .stButton > button { width: 100% !important; }
    }
    .winner-text {
        color: #00ff00; font-weight: bold; font-size: 14px;
        text-align: center; margin: 5px 0;
    }
    .roster-box {
        background-color: #1e212b; padding: 15px; border-radius: 10px; 
        border: 1px solid #333; margin-bottom: 20px; text-align: center;
    }
    .team-badge {
        display: inline-block; padding: 8px 16px; border-radius: 20px;
        margin: 5px; font-weight: bold; font-size: 15px; border: 2px solid;
        background-color: #0e1117;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align:center; color:#1a73e8;'>🏸Badminton Tournament Manager</h2>", unsafe_allow_html=True)

# ---------------- INITIAL INPUTS & TEAM SETUP ----------------
if not st.session_state.teams:
    total_players = st.number_input("Total Players (Even)", min_value=2, step=2)
    total_teams = total_players // 2
    team_names = [f"Team {string.ascii_uppercase[i]}" for i in range(total_teams)]
    
    st.subheader("Setup Teams")
    tab1, tab2 = st.tabs(["🔀 Randomize Players", "✍️ Manual Teams"])
    
    with tab1:
        c1, c2 = st.columns(2)
        cat1 = c1.text_area("Category 1 Players (One per line)")
        cat2 = c2.text_area("Category 2 Players (One per line)")

        if st.button("Generate & Randomize Teams", use_container_width=True):
            p1 = [x.strip() for x in cat1.split("\n") if x.strip()]
            p2 = [x.strip() for x in cat2.split("\n") if x.strip()]
            if len(p1) == total_teams and len(p2) == total_teams:
                random.shuffle(p1); random.shuffle(p2)
                for i, team in enumerate(team_names):
                    st.session_state.teams[team] = [p1[i], p2[i]]
                save_data() 
                st.rerun()

    with tab2:
        manual_inputs = {}
        for team in team_names:
            manual_inputs[team] = st.text_input(f"{team} Players", placeholder="Player 1, Player 2")
            
        if st.button("Save Manual Teams", type="primary", use_container_width=True):
            for team, p_str in manual_inputs.items():
                players = [x.strip() for x in p_str.split(",") if x.strip()]
                st.session_state.teams[team] = players
            save_data() 
            st.rerun()

    st.stop()

# ---------------- ASSIGN COLORS ----------------
colors_palette = ["#FF6B6B", "#4D96FF", "#6BCB77", "#FFD93D", "#845EC2", "#FF9671", "#00C9A7", "#C34A36", "#F38181", "#95E1D3"]
for i, team in enumerate(st.session_state.teams.keys()):
    if team not in st.session_state.team_colors or st.session_state.team_colors[team] == "#FFFFFF":
        st.session_state.team_colors[team] = colors_palette[i % len(colors_palette)]
save_data() 

# ---------------- TEAM ROSTER LEGEND ----------------
st.markdown("<h3 style='text-align:center;'>🏷️ Team Roster & Colors</h3>", unsafe_allow_html=True)
roster_html = "<div class='roster-box'>"
for team, players in st.session_state.teams.items():
    color = st.session_state.team_colors[team]
    roster_html += f"<span class='team-badge' style='color:{color}; border-color:{color};'>{team}: {players[0]} & {players[1]}</span>"
roster_html += "</div>"
st.markdown(roster_html, unsafe_allow_html=True)

# ---------------- LEADERBOARD & VISUALS ----------------
stats = {t: {"P": 0, "W": 0, "L": 0, "Pts": 0, "RR": 0} for t in st.session_state.teams}
for m_key, (s1, s2) in st.session_state.scores.items():
    t1, t2 = m_key.split("|") 
    stats[t1]["P"] += 1; stats[t2]["P"] += 1
    stats[t1]["RR"] += (s1 - s2); stats[t2]["RR"] += (s2 - s1)
    if s1 > s2: 
        stats[t1]["W"] += 1; stats[t1]["Pts"] += 2; stats[t2]["L"] += 1
    elif s2 > s1: 
        stats[t2]["W"] += 1; stats[t2]["Pts"] += 2; stats[t1]["L"] += 1

# SORTING: By Points, then Wins, then Run Rate (RR) as the tie-breaker
data_list = [{"Team": t, **v} for t, v in stats.items()]
df = pd.DataFrame(data_list).sort_values(by=["Pts", "W", "RR"], ascending=[False, False, False])

st.subheader("📊 Tournament Standings")
if not df.empty and df['Pts'].max() > 0:
    top = df.to_dict('records')
    cols = st.columns(min(len(top), 3))
    for i, c in enumerate(cols):
        icons = ["🥇", "🥈", "🥉"]
        c.metric(f"{icons[i]} Rank {i+1}", top[i]['Team'], f"{top[i]['Pts']} Pts")

    def color_team_column(val):
        color = st.session_state.team_colors.get(val, "white")
        return f'color: {color}; font-weight: bold;'

    try:
        styled_df = df.style.map(color_team_column, subset=['Team']) \
                            .background_gradient(subset=['Pts'], cmap="Blues") \
                            .background_gradient(subset=['W'], cmap="Greens") \
                            .background_gradient(subset=['RR'], cmap="YlOrRd")
    except AttributeError: 
        styled_df = df.style.applymap(color_team_column, subset=['Team']) \
                            .background_gradient(subset=['Pts'], cmap="Blues") \
                            .background_gradient(subset=['W'], cmap="Greens") \
                            .background_gradient(subset=['RR'], cmap="YlOrRd")

    st.dataframe(styled_df, use_container_width=True, hide_index=True)

# ---------------- MATCH LOGIC ----------------
team_names = list(st.session_state.teams.keys())
def get_rounds(tnames):
    temp = tnames[:]
    if len(temp) % 2: temp.append(None)
    n = len(temp)
    rs = []
    for j in range(n - 1):
        pairs = []
        for i in range(n // 2):
            if temp[i] and temp[n-1-i]: pairs.append((temp[i], temp[n-1-i]))
        rs.append(pairs)
        temp = [temp[0]] + [temp[-1]] + temp[1:-1]
    return rs

rounds_list = get_rounds(team_names)
completed_round_count = 0
for r_idx, m_list in enumerate(rounds_list):
    if all(f"{t1}|{t2}" in st.session_state.completed_matches for (t1, t2) in m_list):
        completed_round_count = r_idx + 1

if completed_round_count == len(rounds_list) - 1 and st.session_state.final_choice is None:
    st.warning("⚠️ **ALERT: DECISION REQUIRED!**")
    top_2 = df["Team"].tolist()[:2]
    st.write(f"Current Finalists: **{top_2[0]}** vs **{top_2[1]}**")
    ca, cb = st.columns(2)
    if ca.button("GO TO FINAL NOW", type="primary"):
        st.session_state.final_choice = "FINAL"; st.session_state.final_mode = True; save_data(); st.rerun()
    if cb.button("CONTINUE LAST ROUND"):
        st.session_state.final_choice = "CONTINUE"; save_data(); st.rerun()
    st.stop()

if not st.session_state.final_mode:
    st.subheader("🏸 Match Scoring Board")
    rk = st.session_state.reset_key
    for r_idx, matches in enumerate(rounds_list, 1):
        with st.expander(f"Round {r_idx}", expanded=(r_idx == completed_round_count + 1)):
            for (t1, t2) in matches:
                m_key = f"{t1}|{t2}"
                is_done = m_key in st.session_state.completed_matches
                val1, val2 = st.session_state.scores.get(m_key, [0, 0])
                current_winner = (t1 if val1 > val2 else t2) if is_done else None
                
                p1, p2 = st.session_state.teams[t1], st.session_state.teams[t2]
                color_1 = st.session_state.team_colors.get(t1, "#FFF")
                color_2 = st.session_state.team_colors.get(t2, "#FFF")
                
                expander_title = f"{t1} vs {t2}" if not is_done else f"✅ {t1} vs {t2} (Winner: {current_winner})"
                
                with st.expander(expander_title, expanded=not is_done):
                    st.markdown(f"<div style='text-align:center; font-size:16px; margin-bottom: 10px; padding: 5px; background-color: #1a1c23; border-radius: 5px;'><span style='color:{color_1}; font-weight:bold;'>{t1} ({p1[0]} & {p1[1]})</span> <span style='color:#888;'>🆚</span> <span style='color:{color_2}; font-weight:bold;'>{t2} ({p2[0]} & {p2[1]})</span></div>", unsafe_allow_html=True)
                    
                    c1, c2, c3 = st.columns([2, 2, 1])
                    s1 = c1.number_input(f"{t1} Score", 0, key=f"s1_{m_key}_{rk}", value=val1, label_visibility="collapsed")
                    s2 = c2.number_input(f"{t2} Score", 0, key=f"s2_{m_key}_{rk}", value=val2, label_visibility="collapsed")
                    
                    if c3.button("💾 Save", key=f"sv_{m_key}_{rk}", use_container_width=True):
                        st.session_state.scores[m_key] = [s1, s2]
                        if m_key not in st.session_state.completed_matches:
                            st.session_state.completed_matches.append(m_key)
                        save_data(); st.rerun()
                    
                    if is_done:
                        st.markdown(f"<p class='winner-text'>Winner: {current_winner}</p>", unsafe_allow_html=True)

# ---------------- FINAL MATCH ----------------
if st.session_state.final_mode:
    st.divider()
    st.markdown("<h1 style='text-align:center;'>🏆 GRAND FINAL</h1>", unsafe_allow_html=True)
    top_2 = df["Team"].tolist()[:2]
    t1, t2 = top_2[0], top_2[1]
    p1, p2 = st.session_state.teams[t1], st.session_state.teams[t2]
    
    color_1 = st.session_state.team_colors.get(t1, "#4D96FF")
    color_2 = st.session_state.team_colors.get(t2, "#FF6B6B")
    
    st.markdown(f"""
    <div style='text-align:center; padding: 20px; background-color: #1a1c23; border: 1px solid #333; border-radius: 12px; margin-bottom: 25px; box-shadow: 0px 4px 10px rgba(0,0,0,0.5);'>
        <h2 style='margin: 0; font-size: 32px;'>
            <span style='color: {color_1}; text-shadow: 1px 1px 2px rgba(0,0,0,0.8);'>{t1}</span> 
            <span style='color: #888; font-size: 20px; margin: 0 15px;'>🆚</span> 
            <span style='color: {color_2}; text-shadow: 1px 1px 2px rgba(0,0,0,0.8);'>{t2}</span>
        </h2>
        <div style='margin-top: 12px; font-size: 18px; color: #eee;'>
            <span style='border-bottom: 3px solid {color_1}; padding-bottom: 3px;'>{p1[0]} & {p1[1]}</span>
            <span style='margin: 0 25px; color: #555;'>|</span>
            <span style='border-bottom: 3px solid {color_2}; padding-bottom: 3px;'>{p2[0]} & {p2[1]}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    cx, cy = st.columns(2)
    fs1 = cx.number_input(f"{t1} Score", 0, key=f"fs1_{st.session_state.reset_key}")
    fs2 = cy.number_input(f"{t2} Score", 0, key=f"fs2_{st.session_state.reset_key}")
    
    if st.button("Complete Tournament", type="primary", use_container_width=True):
        champ = t1 if fs1 > fs2 else t2
        st.balloons()
        st.success(f"🏆 {champ} is the Champion! 🏆")

st.markdown("<hr><div style='text-align:center; color:#888;'>Developed with ❤️ by <b>Subbiah S</b></div>", unsafe_allow_html=True)
