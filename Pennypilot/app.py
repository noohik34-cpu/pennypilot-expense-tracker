import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import date, datetime
from pathlib import Path

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="PennyPilot | Finance Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. DATABASE SETUP
# ==========================================

DB_PATH = Path(__file__).resolve().parent / "pennypilot.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    with get_connection() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_type TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                category TEXT NOT NULL,
                transaction_date TEXT NOT NULL,
                description TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                UNIQUE(month, category)
            )
        """)


create_tables()


# ==========================================
# 3. DATABASE FUNCTIONS
# ==========================================

def add_transaction(kind, amount, category, trans_date, description):

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO transactions
            (transaction_type, amount, category,
             transaction_date, description)
            VALUES (?, ?, ?, ?, ?)
        """, (
            kind,
            amount,
            category,
            str(trans_date),
            description
        ))


def load_transactions():

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM transactions
            ORDER BY transaction_date DESC, id DESC
        """).fetchall()

    return pd.DataFrame([dict(row) for row in rows])


def update_transaction(
    trans_id, kind, amount, category, trans_date, description
):

    with get_connection() as conn:
        conn.execute("""
            UPDATE transactions
            SET transaction_type = ?,
                amount = ?,
                category = ?,
                transaction_date = ?,
                description = ?
            WHERE id = ?
        """, (
            kind,
            amount,
            category,
            str(trans_date),
            description,
            trans_id
        ))


def delete_transaction(trans_id):

    with get_connection() as conn:
        conn.execute(
            "DELETE FROM transactions WHERE id = ?",
            (trans_id,)
        )


def save_budget(month, category, amount):

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO budgets (month, category, amount)
            VALUES (?, ?, ?)
            ON CONFLICT(month, category)
            DO UPDATE SET amount = excluded.amount
        """, (month, category, amount))


def load_budgets(month):

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM budgets
            WHERE month = ?
            ORDER BY category
        """, (month,)).fetchall()

    return pd.DataFrame([dict(row) for row in rows])


# ==========================================
# 4. CUSTOM DESIGN
# ==========================================

st.markdown("""
<style>

.stApp {
    background-color: #F5F5EF;
}

[data-testid="stSidebar"] {
    background-color: #183D32;
}

[data-testid="stSidebar"] * {
    color: white !important;
}

h1, h2, h3 {
    color: #183D32;
}

.hero {
    background:
    linear-gradient(
        90deg,
        rgba(15, 43, 34, 0.92),
        rgba(15, 43, 34, 0.35)
    ),
    url("https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=1400");

    background-size: cover;
    background-position: center;
    padding: 55px 35px;
    border-radius: 22px;
    margin-bottom: 25px;
}

.hero h1 {
    color: white !important;
    font-size: 38px;
}

.hero p {
    color: white !important;
    font-size: 16px;
}

div[data-testid="stMetric"] {
    background: white;
    padding: 20px;
    border-radius: 16px;
    border: 1px solid #E3E9E2;
    box-shadow: 0 4px 15px rgba(0,0,0,0.04);
}

div[data-testid="stMetricLabel"] {
    color: #65766C;
}

div[data-testid="stMetricValue"] {
    color: #183D32;
}

.stButton button {
    background-color: #183D32;
    color: white;
    border-radius: 10px;
    border: none;
}

.stButton button:hover {
    background-color: #2D6853;
    color: white;
}

</style>
""", unsafe_allow_html=True)


# ==========================================
# 5. SIDEBAR NAVIGATION
# ==========================================

st.sidebar.title("💰 PennyPilot")
st.sidebar.caption("Your Money. Your Control.")
st.sidebar.divider()

page = st.sidebar.radio(
    "NAVIGATION",
    [
        "Dashboard",
        "Add Transaction",
        "Transaction History",
        "Budget Planner",
        "Reports"
    ]
)

st.sidebar.divider()
st.sidebar.caption("Personal Finance Manager")
st.sidebar.caption("Built with Python & Streamlit")


# ==========================================
# 6. LOAD DATA
# ==========================================

df = load_transactions()

if not df.empty:
    df["amount"] = pd.to_numeric(
        df["amount"], errors="coerce"
    ).fillna(0)

    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"], errors="coerce"
    )

    df["month"] = df["transaction_date"].dt.strftime("%Y-%m")


# ==========================================
# 7. DASHBOARD
# ==========================================

if page == "Dashboard":

    st.markdown("""
    <div class="hero">
        <h1>Welcome to PennyPilot 👋</h1>
        <p>Your Money. Your Control.</p>
        <p>
        Track your spending, manage your budget
        and build better financial habits.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Your Financial Overview")

    income = 0.0
    expenses = 0.0

    if not df.empty:

        income = df.loc[
            df["transaction_type"] == "Income",
            "amount"
        ].sum()

        expenses = df.loc[
            df["transaction_type"] == "Expense",
            "amount"
        ].sum()

    balance = income - expenses

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "💰 Total Income",
        f"₹{income:,.2f}"
    )

    c2.metric(
        "💸 Total Expenses",
        f"₹{expenses:,.2f}"
    )

    c3.metric(
        "💚 Available Balance",
        f"₹{balance:,.2f}"
    )

    st.divider()

    if not df.empty:

        left, right = st.columns(2)

        expense_df = df[
            df["transaction_type"] == "Expense"
        ]

        with left:

            st.subheader("Spending Breakdown")

            if not expense_df.empty:

                fig = px.pie(
                    expense_df,
                    names="category",
                    values="amount",
                    hole=0.65,
                    color_discrete_sequence=[
                        "#183D32",
                        "#6B9B7D",
                        "#D9B66F",
                        "#A9C5B2",
                        "#B8A58B"
                    ]
                )

                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(t=20, b=20)
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

            else:
                st.info("No expenses recorded yet.")

        with right:

            st.subheader("Income vs Expenses")

            summary = pd.DataFrame({
                "Type": ["Income", "Expenses"],
                "Amount": [income, expenses]
            })

            fig = px.bar(
                summary,
                x="Type",
                y="Amount",
                color="Type",
                text_auto=".2s",
                color_discrete_map={
                    "Income": "#183D32",
                    "Expenses": "#D9B66F"
                }
            )

            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        st.subheader("Recent Transactions")

        st.dataframe(
            df[
                [
                    "transaction_type",
                    "amount",
                    "category",
                    "transaction_date",
                    "description"
                ]
            ].head(5),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "Your dashboard is ready! "
            "Add your first transaction to see analytics."
        )


# ==========================================
# 8. ADD TRANSACTION
# ==========================================

elif page == "Add Transaction":

    st.title("➕ Add New Transaction")

    with st.form("transaction_form"):

        kind = st.selectbox(
            "Transaction Type",
            ["Income", "Expense"]
        )

        amount = st.number_input(
            "Amount (₹)",
            min_value=0.0,
            step=100.0
        )

        if kind == "Income":

            categories = [
                "Salary",
                "Business",
                "Freelancing",
                "Investment",
                "Other"
            ]

        else:

            categories = [
                "Food",
                "Travel",
                "Shopping",
                "Education",
                "Healthcare",
                "Entertainment",
                "Bills",
                "Rent",
                "Other"
            ]

        category = st.selectbox(
            "Category",
            categories
        )

        trans_date = st.date_input(
            "Transaction Date",
            value=date.today()
        )

        description = st.text_input(
            "Description",
            max_chars=200
        )

        submitted = st.form_submit_button(
            "Save Transaction"
        )

        if submitted:

            if amount <= 0:

                st.error("Amount must be greater than zero.")

            else:

                add_transaction(
                    kind,
                    amount,
                    category,
                    trans_date,
                    description.strip()
                )

                st.success("Transaction saved successfully!")
                st.rerun()


# ==========================================
# 9. TRANSACTION HISTORY
# ==========================================

elif page == "Transaction History":

    st.title("📋 Transaction History")

    df = load_transactions()

    if not df.empty:

        search = st.text_input(
            "Search by category or description"
        )

        filtered = df.copy()

        if search:
            mask = (
                filtered["category"].str.contains(
                    search, case=False, na=False
                )
                |
                filtered["description"].str.contains(
                    search, case=False, na=False
                )
            )

            filtered = filtered[mask]

        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        st.subheader("Manage Transactions")

        selected_id = st.selectbox(
            "Select Transaction ID",
            df["id"].tolist()
        )

        selected = df[
            df["id"] == selected_id
        ].iloc[0]

        with st.form("edit_transaction"):

            new_kind = st.selectbox(
                "Transaction Type",
                ["Income", "Expense"],
                index=0 if selected["transaction_type"] == "Income" else 1
            )

            new_amount = st.number_input(
                "Amount",
                min_value=0.01,
                value=float(selected["amount"])
            )

            if new_kind == "Income":
                options = [
                    "Salary", "Business", "Freelancing",
                    "Investment", "Other"
                ]
            else:
                options = [
                    "Food", "Travel", "Shopping",
                    "Education", "Healthcare",
                    "Entertainment", "Bills", "Rent", "Other"
                ]

            old_category = selected["category"]

            category_index = (
                options.index(old_category)
                if old_category in options else 0
            )

            new_category = st.selectbox(
                "Category",
                options,
                index=category_index
            )

            old_date = pd.to_datetime(
                selected["transaction_date"]
            ).date()

            new_date = st.date_input(
                "Date",
                value=old_date
            )

            new_description = st.text_input(
                "Description",
                value=selected["description"] or ""
            )

            update = st.form_submit_button(
                "Update Transaction"
            )

            if update:

                update_transaction(
                    selected_id,
                    new_kind,
                    new_amount,
                    new_category,
                    new_date,
                    new_description.strip()
                )

                st.success("Transaction updated!")
                st.rerun()

        if st.button("🗑️ Delete Selected Transaction"):

            delete_transaction(selected_id)

            st.success("Transaction deleted!")
            st.rerun()

    else:

        st.info("No transactions available yet.")


# ==========================================
# 10. BUDGET PLANNER
# ==========================================

elif page == "Budget Planner":

    st.title("🎯 Monthly Budget Planner")

    selected_month = st.text_input(
        "Month (YYYY-MM)",
        value=date.today().strftime("%Y-%m")
    )

    try:
        datetime.strptime(selected_month, "%Y-%m")
        valid_month = True
    except ValueError:
        valid_month = False
        st.error("Enter month in YYYY-MM format.")

    if valid_month:

        st.subheader("Set Category Budget")

        with st.form("budget_form"):

            budget_category = st.selectbox(
                "Category",
                [
                    "Food",
                    "Travel",
                    "Shopping",
                    "Education",
                    "Healthcare",
                    "Entertainment",
                    "Bills",
                    "Rent",
                    "Other"
                ]
            )

            budget_amount = st.number_input(
                "Monthly Budget (₹)",
                min_value=0.0,
                step=500.0
            )

            save = st.form_submit_button(
                "Save Budget"
            )

            if save:

                if budget_amount <= 0:
                    st.error("Budget must be greater than zero.")
                else:
                    save_budget(
                        selected_month,
                        budget_category,
                        budget_amount
                    )

                    st.success("Budget saved successfully!")
                    st.rerun()

        st.divider()

        st.subheader("Budget Performance")

        budgets = load_budgets(selected_month)

        if not budgets.empty:

            current_data = load_transactions()

            if not current_data.empty:

                current_data["month"] = pd.to_datetime(
                    current_data["transaction_date"]
                ).dt.strftime("%Y-%m")

                current_data = current_data[
                    (current_data["month"] == selected_month)
                    &
                    (current_data["transaction_type"] == "Expense")
                ]

            for _, budget in budgets.iterrows():

                spent = 0.0

                if not current_data.empty:

                    spent = current_data.loc[
                        current_data["category"] == budget["category"],
                        "amount"
                    ].sum()

                limit = float(budget["amount"])

                progress = min(spent / limit, 1.0)

                st.write(
                    f"**{budget['category']}**"
                )

                st.progress(progress)

                st.write(
                    f"Spent: ₹{spent:,.2f} / "
                    f"Budget: ₹{limit:,.2f}"
                )

                if spent > limit:
                    st.warning("You have exceeded this budget!")
                else:
                    st.success(
                        f"Remaining: ₹{limit - spent:,.2f}"
                    )

        else:

            st.info("No budgets created for this month yet.")


# ==========================================
# 11. REPORTS
# ==========================================

elif page == "Reports":

    st.title("📊 Financial Reports")

    df = load_transactions()

    if not df.empty:

        col1, col2 = st.columns(2)

        with col1:
            start_date = st.date_input(
                "Start Date",
                value=date(date.today().year, 1, 1)
            )

        with col2:
            end_date = st.date_input(
                "End Date",
                value=date.today()
            )

        if start_date > end_date:

            st.error("Start date cannot be after end date.")

        else:

            df["transaction_date"] = pd.to_datetime(
                df["transaction_date"]
            )

            filtered = df[
                (df["transaction_date"].dt.date >= start_date)
                &
                (df["transaction_date"].dt.date <= end_date)
            ]

            st.subheader("Filtered Transactions")

            st.dataframe(
                filtered,
                use_container_width=True,
                hide_index=True
            )

            csv = filtered.to_csv(
                index=False
            ).encode("utf-8")

            st.download_button(
                label="⬇️ Download CSV Report",
                data=csv,
                file_name="pennypilot_report.csv",
                mime="text/csv"
            )

            total_income = filtered.loc[
                filtered["transaction_type"] == "Income",
                "amount"
            ].sum()

            total_expenses = filtered.loc[
                filtered["transaction_type"] == "Expense",
                "amount"
            ].sum()

            st.metric(
                "Period Balance",
                f"₹{total_income - total_expenses:,.2f}"
            )

    else:

        st.info("No data available to generate reports.")


# ==========================================
# 12. FOOTER
# ==========================================

st.divider()

st.markdown(
    """
    <div style="text-align:center; color:#65766C;">
        <b>PennyPilot</b> | Your Money. Your Control.
        <br>
        Built with Python, Streamlit, SQLite and Plotly.
    </div>
    """,
    unsafe_allow_html=True
)