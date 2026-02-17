import streamlit as st
import string
import random
import pandas as pd

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Badminton Tournament Manager", layout="centered")

# ---------------- MOBILE RESPONSIVE FIX ----------------
st.markdown("""
<style>

/* Reduce side padding on mobile */
@media (max-width: 768px) {
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    /* Stack columns vertically */
    div[data-testid="column"] {
        flex: 1 1 100% !important;
        max-width: 100% !important;
    }

    /* Full width buttons */
    .stButton > button {
        width: 100% !important;
    }

    /* Number inputs full width */
    .stNumberInput {
        width: 100% !important;
    }

    /* Responsive font sizes */
    h2 {
        font-size: 20px !important;
    }
}

/* Dataframe responsive */
[data-testid="stDataFrame"] {
    width: 100% !important;
}

</style>
""", unsafe_allow_html=True)

st.markdown(
    "<h2 style='text-align:center; color:#1a73e8;'> Badminton Tournament Manager</h2>",
    unsafe_allow_html=True
)

# ---------------- AUTO SCROLL ----------------
def scroll_top():
    st.markdown(
        """
        <script>
        window.scrollTo(0, 0);
        </script>
        """,
        unsafe_allow_html=True
    )

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
    st.session_state.final_prompt = False
    st.session_state.final_mode = False

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
            st.session_state.teams[team] = {
                "players": [p1[i], p2[i]]
            }

        st.success("Teams randomized successfully!")
        st.rerun()

if len(st.session_state.teams) != total_teams:
    st.stop()

# ---------------- TEAMS ----------------
st.subheader("Teams")

for team in team_names:
    color = st.session_state.team_colors[team]
    p1, p2 = st.session_state.teams[team]["players"]

    st.markdown(f"""
    <div style="background:#1f2937;
                padding:10px;
                border-radius:8px;
                margin-bottom:6px;
                border-left:6px solid {color};">
        <b style="color:{color}; font-size:clamp(14px,4vw,16px);">{team}</b><br>
        <span style="font-size:clamp(12px,3.5vw,14px);">
        {p1} & {p2}
        </span>
    </div>
    """, unsafe_allow_html=True)

# ---------------- ROUND ROBIN ----------------
def generate_round_robin(teams):
    teams = teams[:]
    if len(teams) % 2 == 1:
        teams.append("BYE")

    rounds = []
    n = len(teams)

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
match_order = [m for r in rounds for m in r]

# ---------------- LEADERBOARD ----------------
wins = {t: 0 for t in team_names}
losses = {t: 0 for t in team_names}
points = {t: 0 for t in team_names}
run_rate = {t: 0 for t in team_names}
played = {t: 0 for t in team_names}

for (t1, t2), (s1, s2) in st.session_state.scores.items():

    played[t1] += 1
    played[t2] += 1

    run_rate[t1] += s1 - s2
    run_rate[t2] += s2 - s1

    if s1 > s2:
        wins[t1] += 1
        losses[t2] += 1
        points[t1] += 2
    elif s2 > s1:
        wins[t2] += 1
        losses[t1] += 1
        points[t2] += 2

table = []

for t in team_names:
    table.append({
        "Team": t,
        "P": played[t],
        "W": wins[t],
        "L": losses[t],
        "Pts": points[t],
        "RR": run_rate[t]
    })

table = sorted(table, key=lambda x: (x["Pts"], x["RR"]), reverse=True)
df = pd.DataFrame(table)

st.subheader("Live Leaderboard")

if len(df) > 0:
    styled_df = df.style \
        .background_gradient(subset=["Pts"], cmap="YlGn") \
        .background_gradient(subset=["RR"], cmap="Blues")

    st.dataframe(styled_df, use_container_width=True, hide_index=True)

# ---------------- MATCHES ----------------
if total_teams >= 2:

    st.subheader("Matches")
    match_counter = 0

    for r, matches in enumerate(rounds, start=1):

        st.markdown(f"### Round {r}")

        for (t1, t2) in matches:

            match_key = (t1, t2)
            is_completed = match_key in st.session_state.completed_matches
            is_next = (
                len(st.session_state.completed_matches)
                < len(match_order)
                and len(st.session_state.completed_matches)
                == match_order.index(match_key)
            )

            color1 = st.session_state.team_colors[t1]
            color2 = st.session_state.team_colors[t2]

            p1a, p1b = st.session_state.teams[t1]["players"]
            p2a, p2b = st.session_state.teams[t2]["players"]

            st.markdown(f"""
            <div style="margin-bottom:8px;">
                <b style="color:{color1}; font-size:clamp(14px,4vw,16px);">{t1}</b>
                <span style="font-size:clamp(12px,3.5vw,14px);">
                ({p1a} & {p1b})
                </span>
                &nbsp; <b>vs</b> &nbsp;
                <b style="color:{color2}; font-size:clamp(14px,4vw,16px);">{t2}</b>
                <span style="font-size:clamp(12px,3.5vw,14px);">
                ({p2a} & {p2b})
                </span>
            </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2, gap="small")

            with col1:
                s1 = st.number_input(
                    f"{t1} Score",
                    min_value=0,
                    step=1,
                    key=f"s1_{match_counter}",
                    disabled=not is_next
                )

            with col2:
                s2 = st.number_input(
                    f"{t2} Score",
                    min_value=0,
                    step=1,
                    key=f"s2_{match_counter}",
                    disabled=not is_next
                )

            if not is_completed and is_next:
                if st.button("Submit", key=f"submit_{match_counter}", use_container_width=True):
                    st.session_state.scores[match_key] = (s1, s2)
                    st.session_state.completed_matches.append(match_key)
                    st.rerun()

            if is_completed:
                s1_saved, s2_saved = st.session_state.scores[match_key]
                winner = t1 if s1_saved > s2_saved else t2
                st.success(f"Winner: {winner}")

            match_counter += 1
