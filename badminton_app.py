import streamlit as st
import string
import random
import pandas as pd
import json
import os

# ---------------- CONFIG & DATA SERVER ----------------
st.set_page_config(page_title="Badminton Manager Pro", layout="centered")

DATA_FILE = "tournament_data.json"

def load_data():
    """Reads data from the local JSON server."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            st.session_state.teams = data.get("teams", {})
            st.session_state.scores = data.get("scores", {})
            st.session_state.completed_matches = data.get("completed_matches", [])
            st.session_state.final_mode = data.get("final_mode", False)
            st.session_state.final_choice = data.get("final_choice", None)
            st.session_state.team_colors = data.get("team_colors", {})
            return True
    return False

def save_data():
    """Writes the current session state to the local JSON server."""
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

# --- CALLBACK FUNCTIONS --- 
def reset_scores_and_matches():
    st.session_state.scores = {}
    st.session_state.completed_matches = []
    st.session_state.final_mode = False
    st.session_state.final_choice = None
    save_data()
    
    for key in list(st.session_state.keys()):
        if key.startswith("s1_") or key.startswith("s2_") or key.startswith("fs"):
            del st.session_state[key]

def hard_reset_all():
    st.session_state.clear()
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)

# ---------------- INITIALIZE DATA ----------------
# Load from file first. If empty, setup the basic session state
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
st.sidebar.button("🔄 Reset Scores & Matches", on_click=reset_scores_and_matches, help="Clears the leaderboard and matches, but keeps your teams.")
st.sidebar.button("⚠️ Hard Reset All Data", type="primary", on_click=hard_reset_all, help="Completely wipes all teams and scores.")

# ---------------- UI STYLING ----------------
st.markdown("""
<style>
    @media (max-width: 768px) {
        .block-container { padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
        .stButton > button { width: 100% !important; }
    }
    .pinned-header {
        position: sticky; top: 0; background: #0e1117; z-index: 999;
        padding: 10px; border-bottom: 2px solid #1a73e8; margin-bottom: 10px;
    }
    .team-chip {
        display: inline-block; padding: 4px 10px; border-radius: 15px;
        margin: 4px; font-weight: bold; font-size: 11px; border: 1px solid;
    }
    .winner-text {
        color: #00ff00; font-weight: bold; font-size: 14px;
        text-align: center; margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align:center; color:#1a73e8;'>🏸Badminton Tournament Manager</h2>", unsafe_allow_html=True)

# ---------------- INITIAL INPUTS & TEAM SETUP ----------------
if not st.session_state.teams:
    total_players = st.number_input("Total Players (Even)", min_value=2, step=2)
    total_teams = total_players // 2
    team_names = [f"Team {string.ascii_uppercase[i]}" for i in range(total_teams)]
    
    # Assign colors early
    if not st.session_state.team_colors:
        colors = ["#FF6B6B", "#4D96FF", "#6BCB77", "#FFD93D", "#845EC2", "#FF9671", "#00C9A7", "#C34A36"]
        random.shuffle(colors)
        st.session_state.team_colors = {t: colors[i % len(colors)] for i, t in enumerate(team_names)}

    st.subheader("Setup Teams")
    
    # Tabs for Manual vs Random selection
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
                save_data() # Save to database
                st.rerun()
            else:
                st.error(f"Please enter exactly {total_teams} players in each category.")

    with tab2:
        st.write("Enter exact pairings for your teams.")
        manual_inputs = {}
        for team in team_names:
            manual_inputs[team] = st.text_input(f"{team} Players", placeholder="e.g., Player 1, Player 2")
            
        if st.button("Save Manual Teams", type="primary", use_container_width=True):
            valid = True
            for team, p_str in manual_inputs.items():
                players = [x.strip() for x in p_str.split(",") if x.strip()]
                if len(players) != 2:
                    st.error(f"{team} must have exactly 2 players separated by a comma.")
                    valid = False
                    break
                st.session_state.teams[team] = players
            
            if valid:
                save_data() # Save to database
                st.rerun()

    st.markdown("""
    <hr style="margin-top:40px;">
    <div style='text-align:center; font-size:14px; color:#888; padding:15px;'>
    Developed with ❤️ by <b>Subbiah S</b>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

team_names = list(st.session_state.teams.keys())

# ---------------- PINNED TEAM REFERENCE ----------------
header_html = "<div class='pinned-header'>"
for team, players in st.session_state.teams.items():
    color = st.session_state.team_colors.get(team, "#FFFFFF")
    header_html += f"<span class='team-chip' style='color:{color}; border-color:{color};'>{team}: {players[0]} & {players[1]}</span>"
header_html += "</div>"
st.markdown(header_html, unsafe_allow_html=True)

# ---------------- ROUND ROBIN LOGIC ----------------
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

# ---------------- LEADERBOARD ----------------
stats = {t: {"P": 0, "W": 0, "L": 0, "Pts": 0, "RR": 0} for t in team_names}
for m_key, (s1, s2) in st.session_state.scores.items():
    t1, t2 = m_key.split("|") # Split our string key back to teams
    stats[t1]["P"] += 1; stats[t2]["P"] += 1
    stats[t1]["RR"] += (s1 - s2); stats[t2]["RR"] += (s2 - s1)
    if s1 > s2: 
        stats[t1]["W"] += 1; stats[t1]["Pts"] += 2; stats[t2]["L"] += 1
    elif s2 > s1: 
        stats[t2]["W"] += 1; stats[t2]["Pts"] += 2; stats[t1]["L"] += 1

df = pd.DataFrame([{"Team": t, **v} for t, v in stats.items()]).sort_values(["RR", "Pts"], ascending=False)

st.subheader("Leaderboard")
st.dataframe(df, use_container_width=True, hide_index=True)

# ---------------- DECISION GATE ----------------
completed_round_count = 0
for r_idx, m_list in enumerate(rounds_list):
    # check string keys
    if all(f"{t1}|{t2}" in st.session_state.completed_matches for (t1, t2) in m_list):
        completed_round_count = r_idx + 1

gate_triggered = (completed_round_count == len(rounds_list) - 1 and st.session_state.final_choice is None)

if gate_triggered:
    st.warning("⚠️ **ALERT: DECISION REQUIRED BEFORE PROCEEDING!**")
    st.error("🚨 You have reached the final round of the league.")
    top_2 = df["Team"].tolist()[:2]
    st.write(f"Current Finalists: **{top_2[0]}** vs **{top_2[1]}**")
    ca, cb = st.columns(2)
    if ca.button("GO TO FINAL NOW", type="primary"):
        st.session_state.final_choice = "FINAL"; st.session_state.final_mode = True; save_data(); st.rerun()
    if cb.button("CONTINUE LAST ROUND"):
        st.session_state.final_choice = "CONTINUE"; save_data(); st.rerun()
    st.stop() 

if completed_round_count == len(rounds_list) and not st.session_state.final_mode:
    st.success("✅ All league matches are complete!")
    if st.button("PROCEED TO GRAND FINAL", type="primary", use_container_width=True):
        st.session_state.final_mode = True
        save_data()
        st.rerun()

# ---------------- LEAGUE MATCHES ----------------
if not st.session_state.final_mode:
    active_round_idx = completed_round_count + 1
    
    st.subheader("Match Entries")
    for r_idx, matches in enumerate(rounds_list, 1):
        is_expanded = (r_idx == active_round_idx)
        
        with st.expander(f"Round {r_idx}", expanded=is_expanded):
            for (t1, t2) in matches:
                if t1 not in st.session_state.teams or t2 not in st.session_state.teams: continue
                m_key = f"{t1}|{t2}" # Using a string key so JSON handles it perfectly
                is_done = m_key in st.session_state.completed_matches
                p1, p2 = st.session_state.teams[t1], st.session_state.teams[t2]
                
                val1, val2 = st.session_state.scores.get(m_key, [0, 0])
                
                if is_done:
                    winner = t1 if val1 > val2 else t2
                    match_title = f"✅ {t1} vs {t2} (:green[Winner: {winner}])"
                else:
                    match_title = f"🏸 {t1} vs {t2}"
                
                with st.expander(match_title, expanded=not is_done):
                    if is_done:
                        t1_disp = f":green[**{t1}** ({p1[0]}&{p1[1]})]" if val1 > val2 else f"**{t1}** ({p1[0]}&{p1[1]})"
                        t2_disp = f":green[**{t2}** ({p2[0]}&{p2[1]})]" if val2 > val1 else f"**{t2}** ({p2[0]}&{p2[1]})"
                        st.markdown(f"{t1_disp} vs {t2_disp}")
                    else:
                        st.markdown(f"**{t1}** ({p1[0]}&{p1[1]}) vs **{t2}** ({p2[0]}&{p2[1]})")
                    
                    col1, col2, col3 = st.columns([2,2,1])
                    
                    s1 = col1.number_input(f"{t1}", 0, key=f"s1_{m_key}", value=val1, label_visibility="collapsed")
                    s2 = col2.number_input(f"{t2}", 0, key=f"s2_{m_key}", value=val2, label_visibility="collapsed")
                    
                    if col3.button("💾", key=f"sv_{m_key}"):
                        st.session_state.scores[m_key] = [s1, s2]
                        if m_key not in st.session_state.completed_matches:
                            st.session_state.completed_matches.append(m_key)
                        save_data() # Save to database instantly
                        st.rerun()
                    
                    if is_done:
                        st.markdown(f"<p class='winner-text'>Winner: {winner}</p>", unsafe_allow_html=True)

# ---------------- FINAL MATCH ----------------
if st.session_state.final_mode:
    st.divider()
    st.markdown("<h1 style='text-align:center;'>🏆 GRAND FINAL</h1>", unsafe_allow_html=True)
    top_2 = df["Team"].tolist()[:2]
    t1, t2 = top_2[0], top_2[1]
    p1, p2 = st.session_state.teams[t1], st.session_state.teams[t2]
    
    st.markdown(f"<div style='text-align:center;'><b>{t1}</b> ({p1[0]}&{p1[1]}) <br>vs<br> <b>{t2}</b> ({p2[0]}&{p2[1]})</div>", unsafe_allow_html=True)
    cx, cy = st.columns(2)
    fs1 = cx.number_input(f"{t1} Score", 0, key="fs1")
    fs2 = cy.number_input(f"{t2} Score", 0, key="fs2")
    
    if st.button("Complete Tournament", type="primary", use_container_width=True):
        champ = t1 if fs1 > fs2 else t2
        st.balloons()
        st.success(f"🏆 {champ} is the Champion! 🏆")

# ---------------- GLOBAL FOOTER ----------------
st.markdown("""
<hr style="margin-top:40px;">
<div style='text-align:center; font-size:14px; color:#888; padding:15px;'>
Developed with ❤️ by <b>Subbiah S</b>
</div>
""", unsafe_allow_html=True)