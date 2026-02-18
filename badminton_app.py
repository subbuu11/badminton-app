import streamlit as st
import string
import random
import pandas as pd

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Badminton Manager Pro", layout="centered")

# ---------------- MOBILE & UI STYLING ----------------
st.markdown("""
<style>
    @media (max-width: 768px) {
        .block-container { padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
        .stButton > button { width: 100% !important; }
    }
    .pinned-header {
        position: sticky; top: 0; background: #0e1117; z-index: 999;
        padding: 10px; border-bottom: 2px solid #1a73e8; margin-bottom: 20px;
    }
    .team-chip {
        display: inline-block; padding: 4px 10px; border-radius: 15px;
        margin: 4px; font-weight: bold; font-size: 13px; border: 1px solid;
    }
    .winner-text {
        color: #00ff00; font-weight: bold; font-size: 16px; 
        margin-top: 5px; text-align: center; border: 1px solid #00ff00;
        padding: 5px; border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align:center; color:#1a73e8;'>🏸 Badminton Tournament Manager</h2>", unsafe_allow_html=True)

# ---------------- INITIAL INPUTS ----------------
total_players = st.number_input("Total Players", min_value=2, step=2)
total_teams = total_players // 2
team_names = [f"Team {string.ascii_uppercase[i]}" for i in range(total_teams)]

# ---------------- SESSION STATE ----------------
if "teams" not in st.session_state or len(st.session_state.get("teams", {})) != total_teams:
    st.session_state.teams = {}
    st.session_state.scores = {}
    st.session_state.completed_matches = []
    st.session_state.final_mode = False
    st.session_state.final_choice = None # Track if user clicked "Continue" or "Final"
    
    colors = ["#FF6B6B", "#4D96FF", "#6BCB77", "#FFD93D", "#845EC2", "#FF9671", "#00C9A7", "#C34A36"]
    random.shuffle(colors)
    st.session_state.team_colors = {t: colors[i % len(colors)] for i, t in enumerate(team_names)}

# ---------------- TEAM SETUP ----------------
st.subheader("Assign Players")
c1 = st.text_area("Category 1 Players")
c2 = st.text_area("Category 2 Players")

if st.button("Generate Teams", use_container_width=True):
    p1 = [x.strip() for x in c1.split("\n") if x.strip()]
    p2 = [x.strip() for x in c2.split("\n") if x.strip()]
    if len(p1) == total_teams and len(p2) == total_teams:
        random.shuffle(p1); random.shuffle(p2)
        for i, team in enumerate(team_names):
            st.session_state.teams[team] = [p1[i], p2[i]]
        st.rerun()

if not st.session_state.teams: st.stop()

# ---------------- PINNED TEAM REFERENCE ----------------
header_html = "<div class='pinned-header'>"
for team, players in st.session_state.teams.items():
    color = st.session_state.team_colors[team]
    header_html += f"<span class='team-chip' style='color:{color}; border-color:{color};'>{team}: {players[0]} & {players[1]}</span>"
header_html += "</div>"
st.markdown(header_html, unsafe_allow_html=True)

# ---------------- ROUND ROBIN LOGIC ----------------
def get_rounds(tnames):
    n = len(tnames)
    rs = []
    for j in range(n - 1):
        pairs = []
        for i in range(n // 2):
            pairs.append((tnames[i], tnames[n - 1 - i]))
        rs.append(pairs)
        tnames = [tnames[0]] + [tnames[-1]] + tnames[1:-1]
    return rs

rounds_list = get_rounds(team_names)
match_order = [m for r in rounds_list for m in r]

# ---------------- LEADERBOARD ----------------
stats = {t: {"Pts": 0, "RR": 0} for t in team_names}
for (t1, t2), (s1, s2) in st.session_state.scores.items():
    stats[t1]["RR"] += (s1 - s2); stats[t2]["RR"] += (s2 - s1)
    if s1 > s2: stats[t1]["Pts"] += 2
    elif s2 > s1: stats[t2]["Pts"] += 2

df = pd.DataFrame([{"Team": t, **v} for t, v in stats.items()]).sort_values(["Pts", "RR"], ascending=False)
st.subheader("Leaderboard")
st.dataframe(df, use_container_width=True, hide_index=True)

# ---------------- ROUND CHECK & DECISION POPUP ----------------
completed_round_count = 0
for r_idx, m_list in enumerate(rounds_list):
    if all(m in st.session_state.completed_matches for m in m_list):
        completed_round_count = r_idx + 1

# Logic: If finished the second to last round, ask for choice
if completed_round_count == len(rounds_list) - 1 and st.session_state.final_choice is None:
    st.warning("⚠️ Round Decision: All matches except the final round are done.")
    top_2 = df["Team"].tolist()[:2]
    st.write(f"Top 2 by Run Rate: **{top_2[0]}** & **{top_2[1]}**")
    
    col_a, col_b = st.columns(2)
    if col_a.button("Proceed to FINAL now"):
        st.session_state.final_choice = "FINAL"
        st.session_state.final_mode = True
        st.rerun()
    if col_b.button("Continue League Round"):
        st.session_state.final_choice = "CONTINUE"
        st.rerun()

# ---------------- LEAGUE MATCHES ----------------
if not st.session_state.final_mode:
    st.subheader("League Matches")
    for r_idx, matches in enumerate(rounds_list, 1):
        st.markdown(f"### Round {r_idx}")
        for (t1, t2) in matches:
            m_key = (t1, t2)
            is_done = m_key in st.session_state.completed_matches
            is_active = len(st.session_state.completed_matches) == match_order.index(m_key)
            
            p1a, p1b = st.session_state.teams[t1]
            p2a, p2b = st.session_state.teams[t2]
            
            with st.container(border=True):
                st.markdown(f"**{t1}** ({p1a} & {p1b}) vs **{t2}** ({p2a} & {p2b})")
                
                if is_done:
                    s1, s2 = st.session_state.scores[m_key]
                    winner = t1 if s1 > s2 else t2
                    st.write(f"Score: {s1} - {s2}")
                    st.markdown(f"<div class='winner-text'>WINNER: {winner}</div>", unsafe_allow_html=True)
                else:
                    ca, cb = st.columns(2)
                    sc1 = ca.number_input(f"{t1} Score", 0, key=f"s1_{m_key}")
                    sc2 = cb.number_input(f"{t2} Score", 0, key=f"s2_{m_key}")
                    if is_active and st.button("Submit Result", key=f"btn_{m_key}"):
                        st.session_state.scores[m_key] = (sc1, sc2)
                        st.session_state.completed_matches.append(m_key)
                        st.rerun()

# ---------------- FINAL MATCH ----------------
if st.session_state.final_mode:
    st.divider()
    st.markdown("<h1 style='text-align:center;'>🏆 GRAND FINAL 🏆</h1>", unsafe_allow_html=True)
    top_2 = df["Team"].tolist()[:2]
    t1, t2 = top_2
    
    col_x, col_y = st.columns(2)
    fs1 = col_x.number_input(f"{t1} Score", 0, key="final_s1")
    fs2 = col_y.number_input(f"{t2} Score", 0, key="final_s2")
    
    if st.button("Declare Champion", type="primary", use_container_width=True):
        winner = t1 if fs1 > fs2 else t2
        st.balloons()
        st.success(f"🏆 {winner} are the Tournament Champions!")
