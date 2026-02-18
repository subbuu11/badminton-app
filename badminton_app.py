import streamlit as st
import string
import random
import pandas as pd

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Badminton Tournament Manager", layout="centered")

# ---------------- MOBILE RESPONSIVE FIX ----------------
st.markdown("""
<style>
@media (max-width: 768px) {
    .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
    div[data-testid="column"] { flex: 1 1 100% !important; max-width: 100% !important; }
    .stButton > button { width: 100% !important; }
    .stNumberInput { width: 100% !important; }
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align:center; color:#1a73e8;'>🏸 Badminton Tournament Manager</h2>", unsafe_allow_html=True)

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

    colors = ["#FF6B6B", "#4D96FF", "#6BCB77", "#FFD93D",
              "#845EC2", "#FF9671", "#00C9A7", "#C34A36"]
    random.shuffle(colors)

    st.session_state.team_colors = {
        team: colors[i % len(colors)]
        for i, team in enumerate(team_names)
    }

# ---------------- CATEGORY INPUT ----------------
st.subheader("Player Categories")

cat1 = st.text_area("Category 1 Players (one per line)")
cat2 = st.text_area("Category 2 Players (one per line)")

if st.button("Randomize Teams", use_container_width=True):
    p1 = [x.strip() for x in cat1.split("\n") if x.strip()]
    p2 = [x.strip() for x in cat2.split("\n") if x.strip()]

    if len(p1) != total_teams or len(p2) != total_teams:
        st.error("Each category must match number of teams.")
    else:
        random.shuffle(p1)
        random.shuffle(p2)
        for i, team in enumerate(team_names):
            st.session_state.teams[team] = {"players": [p1[i], p2[i]]}
        st.rerun()

if len(st.session_state.teams) != total_teams:
    st.stop()

# ---------------- SHOW TEAMS ----------------
st.subheader("Teams")
for team in team_names:
    color = st.session_state.team_colors[team]
    p1, p2 = st.session_state.teams[team]["players"]
    st.markdown(f"""
    <div style="background:#1f2937;padding:10px;border-radius:8px;margin-bottom:6px;border-left:6px solid {color};">
        <b style="color:{color};font-size:16px;">{team}</b><br>
        <span style="font-size:14px;">{p1} & {p2}</span>
    </div>
    """, unsafe_allow_html=True)

# ---------------- ROUND ROBIN LOGIC ----------------
def generate_round_robin(teams):
    teams = teams[:]
    rounds = []
    n = len(teams)
    for _ in range(n - 1):
        pairs = []
        for i in range(n // 2):
            pairs.append((teams[i], teams[n - 1 - i]))
        rounds.append(pairs)
        teams = [teams[0]] + [teams[-1]] + teams[1:-1]
    return rounds

rounds = generate_round_robin(team_names)
match_order = [m for r in rounds for m in r]

# ---------------- LEADERBOARD CALCULATION ----------------
wins, losses, points, run_rate, played = ({t: 0 for t in team_names} for _ in range(5))

for (t1, t2), (s1, s2) in st.session_state.scores.items():
    played[t1] += 1
    played[t2] += 1
    run_rate[t1] += s1 - s2
    run_rate[t2] += s2 - s1
    if s1 > s2:
        wins[t1] += 1; losses[t2] += 1; points[t1] += 2
    elif s2 > s1:
        wins[t2] += 1; losses[t1] += 1; points[t2] += 2

table = [{"Team": t, "P": played[t], "W": wins[t], "L": losses[t], "Pts": points[t], "RR": run_rate[t]} for t in team_names]
df = pd.DataFrame(table).sort_values(by=["Pts", "RR"], ascending=False)

st.subheader("Live Leaderboard")
st.dataframe(df, use_container_width=True, hide_index=True)

# ---------------- MATHEMATICAL ELIMINATION CHECK ----------------
remaining_per_team = {t: 0 for t in team_names}
for match in match_order:
    if match not in st.session_state.completed_matches:
        remaining_per_team[match[0]] += 1
        remaining_per_team[match[1]] += 1

# Calculate max possible points for everyone
max_possible = {t: points[t] + (remaining_per_team[t] * 2) for t in team_names}
# Sort by current points and RR to find the current "cutoff" (2nd place)
current_rankings = df["Team"].tolist()
top_2_teams = current_rankings[:2]
cutoff_pts = points[current_rankings[1]] if len(current_rankings) > 1 else 0

# A team is still "alive" if their max possible points >= current 2nd place points
still_alive = [t for t in team_names if max_possible[t] >= cutoff_pts]

# Final logic: If only 2 teams can mathematically reach the top or all matches done
if len(still_alive) <= 2 or len(st.session_state.completed_matches) == len(match_order):
    if not st.session_state.final_mode:
        st.info(f"✨ Mathematical Certainty: {top_2_teams[0]} and {top_2_teams[1]} have qualified based on points and Run Rate.")
        if st.button("Proceed to Grand Final", type="primary", use_container_width=True):
            st.session_state.final_teams = top_2_teams
            st.session_state.final_mode = True
            st.rerun()

# ---------------- LEAGUE MATCHES ----------------
if not st.session_state.final_mode:
    st.subheader("League Matches")
    match_counter = 0
    for r, matches in enumerate(rounds, start=1):
        st.markdown(f"**Round {r}**")
        for (t1, t2) in matches:
            match_key = (t1, t2)
            is_completed = match_key in st.session_state.completed_matches
            is_next = len(st.session_state.completed_matches) == match_order.index(match_key)
            
            with st.expander(f"{t1} vs {t2} {'✅' if is_completed else '⏳'}", expanded=is_next):
                col1, col2 = st.columns(2)
                with col1:
                    s1 = st.number_input(f"{t1} Score", min_value=0, key=f"s1_{match_counter}", disabled=not is_next)
                with col2:
                    s2 = st.number_input(f"{t2} Score", min_value=0, key=f"s2_{match_counter}", disabled=not is_next)
                
                if is_next and not is_completed:
                    if st.button("Submit Result", key=f"btn_{match_counter}", use_container_width=True):
                        st.session_state.scores[match_key] = (s1, s2)
                        st.session_state.completed_matches.append(match_key)
                        st.rerun()
            match_counter += 1

# ---------------- FINAL MATCH ----------------
if st.session_state.final_mode and st.session_state.final_teams:
    st.divider()
    st.subheader("🏆 GRAND FINAL")
    t1, t2 = st.session_state.final_teams
    st.write(f"Matchup: **{t1}** vs **{t2}**")
    
    col1, col2 = st.columns(2)
    with col1: fs1 = st.number_input(f"{t1} Score", min_value=0, key="f_s1")
    with col2: fs2 = st.number_input(f"{t2} Score", min_value=0, key="f_s2")

    if st.button("Declare Champion", use_container_width=True, type="primary"):
        st.session_state.final_score = (fs1, fs2)

    if st.session_state.final_score:
        s1, s2 = st.session_state.final_score
        winner = t1 if s1 > s2 else t2
        st.balloons()
        st.success(f"🎊 Tournament Winner: {winner}! 🎊")
