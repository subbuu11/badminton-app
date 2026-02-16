import streamlit as st
import string

st.set_page_config(layout="centered")

# ---------- CUSTOM COLORS ----------
st.markdown("""
<style>
.main-title {
    font-size: 32px;
    font-weight: bold;
    color: #0E4C92;
}

.round-title {
    background-color: #0E4C92;
    color: white;
    padding: 8px 12px;
    border-radius: 8px;
    margin-top: 10px;
}

.match-card {
    border: 2px solid #d9e3f0;
    border-radius: 10px;
    padding: 12px;
    margin-bottom: 12px;
    background-color: #f8fbff;
}

.team-name {
    font-weight: bold;
    color: #003366;
    font-size: 18px;
}

.winner-box {
    background-color: #d4edda;
    color: #155724;
    padding: 8px;
    border-radius: 6px;
    margin-top: 6px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">Badminton Tournament Manager</div>', unsafe_allow_html=True)

# ---------------- STEP 1 ----------------
st.subheader("Step 1: Total Players")

total_players = st.number_input(
    "Enter total players (even number)",
    min_value=2,
    step=2
)

if total_players % 2 != 0:
    st.warning("Players must be even")
    st.stop()

total_teams = total_players // 2
team_names = [f"Team {string.ascii_uppercase[i]}" for i in range(total_teams)]

# ---------------- INIT ----------------
if "teams" not in st.session_state or len(st.session_state.teams) != total_teams:
    st.session_state.teams = {
        team: {"players": ["", ""]} for team in team_names
    }

if "scores" not in st.session_state:
    st.session_state.scores = {}

# ---------------- STEP 2 ----------------
st.subheader("Step 2: Enter Players")

for team in team_names:
    st.markdown(f"### {team}")
    st.session_state.teams[team]["players"][0] = st.text_input(
        "Player 1", key=f"{team}_p1"
    )
    st.session_state.teams[team]["players"][1] = st.text_input(
        "Player 2", key=f"{team}_p2"
    )
    st.divider()

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

# ---------------- STEP 3 MATCHES ----------------
st.subheader("Step 3: Round Robin Matches")

match_index = 0

for r, matches in enumerate(rounds, start=1):

    st.markdown(
        f'<div class="round-title">Round {r}</div>',
        unsafe_allow_html=True
    )

    for (t1, t2) in matches:

        p1a, p1b = st.session_state.teams[t1]["players"]
        p2a, p2b = st.session_state.teams[t2]["players"]

        st.markdown('<div class="match-card">', unsafe_allow_html=True)

        st.markdown(
            f'<div class="team-name">{t1}</div>{p1a} & {p1b}',
            unsafe_allow_html=True
        )
        st.markdown("VS")
        st.markdown(
            f'<div class="team-name">{t2}</div>{p2a} & {p2b}',
            unsafe_allow_html=True
        )

        s1 = st.number_input(
            f"{t1} Score",
            min_value=0,
            key=f"s1_{match_index}"
        )

        s2 = st.number_input(
            f"{t2} Score",
            min_value=0,
            key=f"s2_{match_index}"
        )

        st.session_state.scores[(t1, t2)] = (s1, s2)

        if s1 > s2:
            st.markdown(
                f'<div class="winner-box">Winner: {t1}</div>',
                unsafe_allow_html=True
            )
        elif s2 > s1:
            st.markdown(
                f'<div class="winner-box">Winner: {t2}</div>',
                unsafe_allow_html=True
            )

        st.markdown("</div>", unsafe_allow_html=True)

        match_index += 1

# ---------------- CALCULATIONS ----------------
run_rates = {team: 0 for team in team_names}
wins = {team: 0 for team in team_names}
losses = {team: 0 for team in team_names}
points = {team: 0 for team in team_names}

for (t1, t2), (s1, s2) in st.session_state.scores.items():

    diff = s1 - s2
    run_rates[t1] += diff
    run_rates[t2] -= diff

    if s1 > s2:
        wins[t1] += 1
        losses[t2] += 1
        points[t1] += 2
    elif s2 > s1:
        wins[t2] += 1
        losses[t1] += 1
        points[t2] += 2

# ---------------- POINTS TABLE ----------------
st.subheader("Points Table")

table_data = []

for team in team_names:
    table_data.append({
        "Team": team,
        "Wins": wins[team],
        "Losses": losses[team],
        "Points": points[team],
        "Run Rate": run_rates[team]
    })

table_data = sorted(
    table_data,
    key=lambda x: (x["Points"], x["Run Rate"]),
    reverse=True
)

st.table(table_data)

# ---------------- FINAL MATCH ----------------
st.subheader("Final Match")

if len(table_data) >= 2:
    st.success(f"{table_data[0]['Team']} vs {table_data[1]['Team']}")