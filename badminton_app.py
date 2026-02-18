import streamlit as st
import string
import random
import pandas as pd

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Badminton Manager", layout="centered")

# ---------------- MOBILE RESPONSIVE FIX ----------------
st.markdown("""
<style>
@media (max-width: 768px) {
    .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
    .stButton > button { width: 100% !important; }
}
.winner-box {
    background-color: #2e7d32; color: white; padding: 2px 8px; 
    border-radius: 4px; font-size: 12px; font-weight: bold; margin-left: 10px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align:center; color:#1a73e8;'>🏸 Tournament Manager Pro</h2>", unsafe_allow_html=True)

# ---------------- TOTAL PLAYERS ----------------
total_players = st.number_input("Total Players (Even Number)", min_value=2, step=2)
if total_players % 2 != 0:
    st.warning("Players must be even.")
    st.stop()

total_teams = total_players // 2
team_names = [f"Team {string.ascii_uppercase[i]}" for i in range(total_teams)]

# ---------------- SESSION RESET ----------------
if "team_count" not in st.session_state or st.session_state.team_count != total_teams:
    st.session_state.team_count = total_teams
    st.session_state.teams = {}
    st.session_state.scores = {}
    st.session_state.completed_matches = []
    st.session_state.final_mode = False
    st.session_state.final_teams = None
    st.session_state.final_score = None
    colors = ["#FF6B6B", "#4D96FF", "#6BCB77", "#FFD93D", "#845EC2", "#FF9671", "#00C9A7", "#C34A36"]
    random.shuffle(colors)
    st.session_state.team_colors = {team: colors[i % len(colors)] for i, team in enumerate(team_names)}

# ---------------- CATEGORY INPUT ----------------
st.subheader("Player Categories")
c1_in = st.text_area("Category 1 (one per line)")
c2_in = st.text_area("Category 2 (one per line)")

if st.button("Randomize Teams", use_container_width=True):
    p1 = [x.strip() for x in c1_in.split("\n") if x.strip()]
    p2 = [x.strip() for x in c2_in.split("\n") if x.strip()]
    if len(p1) != total_teams or len(p2) != total_teams:
        st.error(f"Need exactly {total_teams} players per category.")
    else:
        random.shuffle(p1); random.shuffle(p2)
        for i, team in enumerate(team_names):
            st.session_state.teams[team] = {"players": [p1[i], p2[i]]}
        st.rerun()

if not st.session_state.teams: st.stop()

# ---------------- ROUND ROBIN LOGIC ----------------
def generate_round_robin(teams):
    if len(teams) % 2: teams.append(None)
    n = len(teams)
    rounds = []
    for j in range(n - 1):
        pairs = []
        for i in range(n // 2):
            if teams[i] and teams[n - 1 - i]:
                pairs.append((teams[i], teams[n - 1 - i]))
        rounds.append(pairs)
        teams = [teams[0]] + [teams[-1]] + teams[1:-1]
    return rounds

all_rounds = generate_round_robin(team_names)
match_order = [m for r in all_rounds for m in r]

# ---------------- LEADERBOARD ----------------
stats = {t: {"P": 0, "W": 0, "L": 0, "Pts": 0, "RR": 0} for t in team_names}
for (t1, t2), (s1, s2) in st.session_state.scores.items():
    stats[t1]["P"] += 1; stats[t2]["P"] += 1
    stats[t1]["RR"] += (s1 - s2); stats[t2]["RR"] += (s2 - s1)
    if s1 > s2: stats[t1]["W"] += 1; stats[t1]["Pts"] += 2; stats[t2]["L"] += 1
    elif s2 > s1: stats[t2]["W"] += 1; stats[t2]["Pts"] += 2; stats[t1]["L"] += 1

df = pd.DataFrame([{"Team": t, **v} for t, v in stats.items()]).sort_values(by=["Pts", "RR"], ascending=False)
st.subheader("Leaderboard")
st.dataframe(df, use_container_width=True, hide_index=True)

# ---------------- EARLY FINALS LOGIC ----------------
current_round_idx = 0
for i, r_matches in enumerate(all_rounds):
    if all((m in st.session_state.completed_matches) for m in r_matches):
        current_round_idx = i + 1

# If we have finished the PENULTIMATE round (e.g., Round 4 of 5)
if current_round_idx >= len(all_rounds) - 1 and not st.session_state.final_mode:
    top_2 = df["Team"].tolist()[:2]
    st.info(f"💡 **Finalists decided by Run Rate:** {top_2[0]} & {top_2[1]}")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Proceed to Final Round Now", type="primary"):
            st.session_state.final_teams = top_2
            st.session_state.final_mode = True
            st.rerun()
    with c2:
        st.write("Or continue remaining league matches below.")

# ---------------- LEAGUE MATCHES ----------------
if not st.session_state.final_mode:
    st.subheader("Match Schedule")
    for r_idx, matches in enumerate(all_rounds, 1):
        st.markdown(f"**Round {r_idx}**")
        for (t1, t2) in matches:
            m_key = (t1, t2)
            done = m_key in st.session_state.completed_matches
            active = len(st.session_state.completed_matches) == match_order.index(m_key)
            
            p1_names = " & ".join(st.session_state.teams[t1]["players"])
            p2_names = " & ".join(st.session_state.teams[t2]["players"])
            
            with st.expander(f"{t1} ({p1_names}) vs {t2} ({p2_names})", expanded=active):
                if done:
                    s1, s2 = st.session_state.scores[m_key]
                    win_team = t1 if s1 > s2 else t2
                    st.markdown(f"Result: {s1} - {s2} <span class='winner-box'>WON: {win_team}</span>", unsafe_allow_html=True)
                else:
                    c1, c2 = st.columns(2)
                    sc1 = c1.number_input(f"{t1} Score", 0, 100, key=f"sc1_{m_key}")
                    sc2 = c2.number_input(f"{t2} Score", 0, 100, key=f"sc2_{m_key}")
                    if active and st.button("Submit Result", key=f"btn_{m_key}"):
                        st.session_state.scores[m_key] = (sc1, sc2)
                        st.session_state.completed_matches.append(m_key)
                        st.rerun()

# ---------------- FINAL MATCH ----------------
else:
    st.subheader("🏆 GRAND FINAL")
    t1, t2 = st.session_state.final_teams
    p1 = " & ".join(st.session_state.teams[t1]["players"])
    p2 = " & ".join(st.session_state.teams[t2]["players"])
    
    st.write(f"**{t1}** ({p1}) vs **{t2}** ({p2})")
    c1, c2 = st.columns(2)
    fs1 = c1.number_input(f"{t1} Score", 0, key="fs1")
    fs2 = c2.number_input(f"{t2} Score", 0, key="fs2")
    
    if st.button("Confirm Champion", type="primary"):
        st.session_state.final_score = (fs1, fs2)
    
    if st.session_state.final_score:
        champ = t1 if st.session_state.final_score[0] > st.session_state.final_score[1] else t2
        st.balloons()
        st.success(f"🏆 {champ} are the Champions! 🏆")
