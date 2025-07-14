import streamlit as st
import pandas as pd
from collections import defaultdict
import random
from io import BytesIO
import base64

# Set Streamlit config
st.set_page_config(page_title="Duty Scheduler", layout="centered")

# ---------------------------
# 🎨 Background, photo, copyright
# ---------------------------
def set_background():
    with open("bg.jpg", "rb") as f:
        bg_data = f.read()
    encoded_bg = base64.b64encode(bg_data).decode()

    with open("photo.jpg", "rb") as f:
        photo_data = f.read()
    encoded_photo = base64.b64encode(photo_data).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0.85)),
                        url("data:image/jpg;base64,{encoded_bg}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        .profile {{
            position: fixed;
            bottom: 10px;
            left: 10px;
            z-index: 1000;
        }}
        .copyright {{
            position: fixed;
            bottom: 10px;
            right: 10px;
            color: gray;
            font-size: 13px;
            z-index: 1000;
        }}
        </style>
        <div class="profile">
            <img src="data:image/jpg;base64,{encoded_photo}" width="60px" style="border-radius:50%;">
        </div>
        <div class="copyright">© Snehasis Banerjee, 2025</div>
        """,
        unsafe_allow_html=True
    )

# ---------------------------
# 📥 Sample Excel Generator
# ---------------------------
def generate_sample_excel():
    teachers_data = {
        "Name of Teacher": ["Snehasis Banerjee", "Animesh", "Goutam Kr. Paul", "Sudip Bandopadhyay", "Arup", "Parnajyoti"],
        "Day Off": ["15-07-2025", "16-07-2025", "18-07-2025", "17-07-2025", "", "na"]
    }

    dates_data = {
        "Dates of Examinations": ["15-07-2025", "16-07-2025", "18-07-2025", "19-07-2025"],
        "Required Invigilators": [3, 2, 4, 1]
    }

    df_teachers = pd.DataFrame(teachers_data)
    df_dates = pd.DataFrame(dates_data)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_teachers.to_excel(writer, sheet_name="Teachers", index=False)
        df_dates.to_excel(writer, sheet_name="Dates", index=False)
    output.seek(0)
    return output

# ---------------------------
# 🧮 Assignment Logic
# ---------------------------
def assign_duties(uploaded_file):
    df_teachers = pd.read_excel(uploaded_file, sheet_name="Teachers")
    df_dates = pd.read_excel(uploaded_file, sheet_name="Dates")

    df_teachers.columns = df_teachers.columns.str.strip()
    df_dates.columns = df_dates.columns.str.strip()

    # ✅ Update to match new column name
    df_dates["Formatted Date"] = pd.to_datetime(df_dates["Dates of Examinations"], dayfirst=True).dt.strftime("%Y-%m-%d")
    df_teachers["Day Off"] = df_teachers["Day Off"].astype(str)

    schedule = pd.DataFrame({"Name of Teacher": df_teachers["Name of Teacher"]})
    for date in df_dates["Formatted Date"]:
        schedule[date] = ""

    offdays = {}
    exempt_teachers = set()

    for _, row in df_teachers.iterrows():
        name = row["Name of Teacher"]
        dayoffs_raw = str(row["Day Off"]).strip()

        if dayoffs_raw.lower() in ["na", "leave", "off", "exempt", "NA"]:
            exempt_teachers.add(name)
            offdays[name] = set()
        elif not dayoffs_raw or dayoffs_raw.lower() == "nan":
            offdays[name] = set()
        else:
            try:
                offdays[name] = set(
                    pd.to_datetime(d.strip(), dayfirst=True).strftime("%Y-%m-%d")
                    for d in dayoffs_raw.split(",") if d.strip()
                )
            except Exception:
                offdays[name] = set()

    duty_count = defaultdict(int)

    for _, row in df_dates.iterrows():
        date = row["Formatted Date"]
        required = int(row["Required Invigilators"])

        available_teachers = [
            teacher for teacher in df_teachers["Name of Teacher"]
            if teacher not in exempt_teachers and date not in offdays.get(teacher, set())
        ]

        random.shuffle(available_teachers)
        available_teachers.sort(key=lambda x: duty_count[x])

        selected_teachers = available_teachers[:min(required, len(available_teachers))]

        for teacher in selected_teachers:
            schedule.loc[schedule["Name of Teacher"] == teacher, date] = "✓"
            duty_count[teacher] += 1

    schedule["Total Duties"] = schedule.apply(lambda row: sum(cell == "✓" for cell in row[1:]), axis=1)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        schedule.to_excel(writer, index=False)
    output.seek(0)
    return output

# ---------------------------
# 🚀 Streamlit UI
# ---------------------------
set_background()
st.title("📘 Exam Duty Scheduler (HMC)")

st.markdown("🔽 **Download Sample Excel File to Fill In:**")
sample = generate_sample_excel()
st.download_button(
    label="📥 Download Sample Excel",
    data=sample,
    file_name="sample_input.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.markdown("📤 **Upload Your Filled Excel File:**")
uploaded_file = st.file_uploader("Upload `input.xlsx`", type=["xlsx"])

if uploaded_file:
    st.success("✅ File uploaded successfully!")

    if st.button("Generate Duty Schedule"):
        try:
            result = assign_duties(uploaded_file)
            st.success("✅ Schedule generated successfully!")

            st.download_button(
                label="📥 Download Duty Schedule",
                data=result,
                file_name="balanced_duty_schedule.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"❌ Error: {e}")
