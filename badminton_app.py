import streamlit as st
import string
import random

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Badminton Tournament Manager",
    layout="centered"
)

# ---------------- STYLING ----------------
st.markdown("""
<style>

/* Title */
.main-title {
    font-size: 24px;
    font-weight: 700;
    text-align: center;
    color: #1a73e8;
    margin-bottom: 20px;
}

/* Round Header */
.round-title {
    font-size: 14px;
    font-weight: 600;
    color: #ffffff;
    background: linear-gradient(to right, #0E4C92, #1a73e8);
    padding: 6px 10px;
    border-radius: 6px;
    margin-top: 20px;
    margin-bottom: 6px;
}

/* Thin separator */
.separator {
    height: 1px;
    background-color: #1f2937;
    margin-bottom: 12px;
}

/* Winner box */
.winner-box {
    background-color: #0B3D2E;
    color: white;
    padding: 8px;
    border-radius: 8px;
    margin-top: 8px;
    font-weight: 700;
    text-align: center;
    font-size: 14px;
}

/* Player name */
.player-name {
    font-size: 12px;
    opacity: 0.8;
    margin-bottom: 6px;
}

.stButton > button {
    width: 100%;
    border-radius: 8px;
}

</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">Badminton Tournament Manager</div>', unsafe_allow_html=True)

# ---------------- TOTAL PLAYERS ----------------
total_players = st.number_input("Total Players (Even Number)", min_value=2, step=2)

if total_players % 2 != 0:
    st.warning("Players must be even.")
    st.stop()

total_teams = total_players // 2
team_names = [f"Team {string.ascii_uppercase[i]}" for i in range(total_teams)]

# ---------------- SAFE SESSION RESET ----------------
if "team_count" not in st.session_state or st.session_state.team_count != total_teams:
    st.session_state.team_count = total_teams
    st.session_state.teams = {
        team: {"players": ["", ""]} for team in team_names
    }
    st.session_state.scores = {}
    st.session_state.completed_matches = []

    colors = ["#FF6B6B", "#4D96FF", "#6BCB77", "#FFD93D",
              "#845EC2", "#FF9671", "#00C9A7", "#C34A36"]
    random.shuffle(colors)

    st.session_state.team_colors = {
        team: colors[i % len(colors)]
        for i, team in enumerate(team_names)
    }

# ---------------- REFEREE MODE ----------------
referee_mode = st.toggle("Referee Mode")

# ---------------- ENTER PLAYERS ----------------
st.subheader("Enter Players")

for team in team_names:
    st.session_state.teams[team]["players"][0] = st.text_input(
        f"{team} Player 1", key=f"{team}_p1"
    )
    st.session_state.teams[team]["players"][1] = st.text_input(
        f"{team} Player 2", key=f"{team}_p2"
    )

# ---------------- ROUND ROBIN ----------------
def generate_round_robin(teams):
    teams = teams[:]
    if len(teams) % 2 == 1:
        teams.append("BYE")

    n = len(teams)
    rounds = []

    for _ in range(n - 1):
        pairs = []
        for i in range(n // 2):
            t1 = teams[i]
            t2 = teams[n - 1 - i]
            if t1 != "BYE" and t2 != "BYE":
                pairs.append((t1, t2))
        rounds.append(pairs)
        teams = [teams[0]] + [teams[-1]] + teams[1:-1]

    return rounds

rounds = generate_round_robin(team_names)

# ---------------- LIVE LEADERBOARD ----------------
st.subheader("Live Leaderboard")

wins = {team: 0 for team in team_names}
points = {team: 0 for team in team_names}
run_rate = {team: 0 for team in team_names}

for (t1, t2), (s1, s2) in st.session_state.scores.items():
    run_rate[t1] += s1 - s2
    run_rate[t2] += s2 - s1

    if s1 > s2:
        wins[t1] += 1
        points[t1] += 2
    elif s2 > s1:
        wins[t2] += 1
        points[t2] += 2

table = []
for team in team_names:
    table.append({
        "Team": team,
        "Wins": wins[team],
        "Points": points[team],
        "Run Rate": run_rate[team]
    })

table = sorted(table, key=lambda x: (x["Points"], x["Run Rate"]), reverse=True)
st.table(table)

# ---------------- MATCHES ----------------
st.subheader("Matches")

match_order = [m for round_matches in rounds for m in round_matches]
match_counter = 0

for r, matches in enumerate(rounds, start=1):

    st.markdown(f'<div class="round-title">Round {r}</div>', unsafe_allow_html=True)
    st.markdown('<div class="separator"></div>', unsafe_allow_html=True)

    for (t1, t2) in matches:

        match_key = (t1, t2)
        is_completed = match_key in st.session_state.completed_matches
        is_next = len(st.session_state.completed_matches) == match_order.index(match_key)

        with st.container():

            color1 = st.session_state.team_colors[t1]
            color2 = st.session_state.team_colors[t2]

            p1a, p1b = st.session_state.teams[t1]["players"]
            p2a, p2b = st.session_state.teams[t2]["players"]

            st.markdown(
                f"<div style='color:{color1}; font-weight:600'>{t1}</div>"
                f"<div class='player-name'>{p1a} & {p1b}</div>",
                unsafe_allow_html=True
            )

            s1 = st.text_input(
                "Score",
                key=f"s1_{match_counter}",
                disabled=not is_next or (referee_mode and is_completed)
            )

            st.markdown(
                f"<div style='color:{color2}; font-weight:600'>{t2}</div>"
                f"<div class='player-name'>{p2a} & {p2b}</div>",
                unsafe_allow_html=True
            )

            s2 = st.text_input(
                "Score ",
                key=f"s2_{match_counter}",
                disabled=not is_next or (referee_mode and is_completed)
            )

            if not is_completed and is_next:
                if st.button("Submit Result", key=f"submit_{match_counter}"):

                    if s1.isdigit() and s2.isdigit():
                        s1_int = int(s1)
                        s2_int = int(s2)

                        st.session_state.scores[match_key] = (s1_int, s2_int)
                        st.session_state.completed_matches.append(match_key)

                        if s1_int != s2_int:
                            st.balloons()

                        st.rerun()
                    else:
                        st.warning("Enter valid numeric scores")

            if is_completed:
                s1_saved, s2_saved = st.session_state.scores[match_key]

                if s1_saved > s2_saved:
                    st.markdown(
                        f'<div class="winner-box">Winner: {t1}</div>',
                        unsafe_allow_html=True
                    )
                elif s2_saved > s1_saved:
                    st.markdown(
                        f'<div class="winner-box">Winner: {t2}</div>',
                        unsafe_allow_html=True
                    )

        match_counter += 1

# ---------------- FINAL ----------------
st.subheader("Final Match")

if len(table) >= 2:
    st.success(f"{table[0]['Team']} vs {table[1]['Team']}")
