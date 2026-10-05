import sqlite3

import requests
import streamlit as st

from database import init_db, load_history, save_results


API_URL = "http://127.0.0.1:8000/analyze"
VALID_LABELS = {"positive", "negative", "neutral"}

st.set_page_config(page_title="Food Review Analyzer", page_icon="🍽️")
st.title("Food Review Analyzer")
st.write(
    "Paste one review per line. Each non-empty line will be analyzed separately."
)

try:
    init_db()
except sqlite3.Error as error:
    st.error(f"Could not initialize the feedback database: {error}")
    st.stop()


def analyze_review(review: str) -> dict[str, object]:
    response = requests.post(API_URL, json={"text": review}, timeout=120)
    if not response.ok:
        detail = response.text.strip() or "The API returned no details."
        raise RuntimeError(f"API error ({response.status_code}): {detail}")

    result = response.json()
    if not isinstance(result, dict):
        raise ValueError("The API returned an unexpected response format.")

    label = result.get("label")
    score = result.get("score")
    theme = result.get("theme")
    if (
        label not in VALID_LABELS
        or isinstance(score, bool)
        or not isinstance(score, int)
        or not 1 <= score <= 5
        or not isinstance(theme, str)
        or not theme.strip()
    ):
        raise ValueError("The API response did not contain valid analysis results.")

    return {
        "review": review,
        "label": label,
        "score": score,
        "theme": theme.strip(),
    }


with st.form("review_form"):
    review_text = st.text_area(
        "Customer review(s)",
        placeholder=(
            "The food arrived hot and fresh.\n"
            "My order was late and the meal was cold."
        ),
        height=180,
        help="Put each review on its own line.",
    )
    analyze_clicked = st.form_submit_button(
        "Analyze reviews",
        type="primary",
        use_container_width=True,
    )

if analyze_clicked:
    reviews = [line.strip() for line in review_text.splitlines() if line.strip()]
    if not reviews:
        st.warning("Please enter at least one review.")
    else:
        results: list[dict[str, object]] = []
        errors: list[str] = []
        progress = st.progress(0, text=f"Analyzing 0 of {len(reviews)}...")

        for index, review in enumerate(reviews, start=1):
            try:
                results.append(analyze_review(review))
            except (requests.RequestException, RuntimeError, ValueError) as error:
                errors.append(f"Review {index}: {error}")
            finally:
                progress.progress(
                    index / len(reviews),
                    text=f"Analyzing {index} of {len(reviews)}...",
                )

        st.session_state["analysis_results"] = results
        st.session_state["analysis_errors"] = errors
        st.session_state["results_saved"] = False
        st.session_state["show_database"] = False

results = st.session_state.get("analysis_results", [])
errors = st.session_state.get("analysis_errors", [])

if results:
    st.subheader("Review analysis")
    st.dataframe(
        [
            {
                "Review": result["review"],
                "Label": str(result["label"]).title(),
                "Score": result["score"],
                "Theme": result["theme"],
            }
            for result in results
        ],
        hide_index=True,
        use_container_width=True,
    )

    total_reviews = len(results)
    average_score = sum(int(result["score"]) for result in results) / total_reviews
    positive_count = sum(result["label"] == "positive" for result in results)
    positive_percent = positive_count / total_reviews * 100

    st.subheader("Batch summary")
    total_col, score_col, positive_col = st.columns(3)
    total_col.metric("Reviews analyzed", total_reviews)
    score_col.metric("Overall average score", f"{average_score:.1f} / 5")
    positive_col.metric("Positive reviews", f"{positive_percent:.1f}%")

    if errors:
        st.warning(f"{len(errors)} review(s) could not be analyzed.")
        for error in errors:
            st.error(error)

    if st.session_state.get("results_saved", False):
        st.success("These results have been saved to the database.")
    elif st.button("Save these results to the database", type="primary"):
        try:
            save_results(results)
        except (sqlite3.Error, KeyError, TypeError) as error:
            st.error(f"Could not save the results: {error}")
        else:
            st.session_state["results_saved"] = True
            st.success(f"Saved {total_reviews} review(s) to the database.")

st.divider()
show_database = st.session_state.get("show_database", False)
button_label = "Hide database records" if show_database else "View database records"
if st.button(button_label):
    st.session_state["show_database"] = not show_database
    show_database = not show_database

if show_database:
    st.subheader("Database records")
    try:
        records = load_history()
    except sqlite3.Error as error:
        st.error(f"Could not load database records: {error}")
    else:
        if records:
            st.dataframe(records, hide_index=True, use_container_width=True)
        else:
            st.info("There are no saved reviews yet.")
