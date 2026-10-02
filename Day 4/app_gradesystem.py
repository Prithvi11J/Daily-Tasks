import base64  # Let the page use its background image.
import io  # Hold the PDF before the user downloads it.
import re  # Make a safe name for the PDF file.
from datetime import datetime  # Add the report creation date.
from html import escape  # Safely display student details.
from pathlib import Path  # Find images beside this Python file.

import streamlit as st  # Build the app page.


APP_FOLDER = Path(__file__).parent  # Find the folder containing this script.
LOGO_PATH = APP_FOLDER / "social_eagle_logo.png"  # Find the eagle logo image.
BACKGROUND_PATH = APP_FOLDER / "school_background.png"  # Find the page background image.
SUBJECTS = [  # Use the same six subjects for every student.
    "English",
    "Mathematics",
    "Science",
    "Social Studies",
    "Computer Science",
    "Hindi",
]
STANDARDS = ["10th Standard", "12th Standard"]  # Add the standard choices.
CLASSES = STANDARDS  # Use the same standard choices for the class manager.

st.set_page_config(  # Set the browser tab and page layout.
    page_title="Students Grade Manager",
    page_icon="🦅",
    layout="centered",
)


def get_grade(mark):  # Return the grade for one mark.
    if mark >= 90:
        return "S"
    if mark >= 80:
        return "A"
    if mark >= 70:
        return "B"
    if mark >= 50:
        return "C"
    return "Fail"


def create_pdf(report):  # Build a downloadable PDF report card.
    try:
        from reportlab.lib import colors  # Set colors in the PDF.
        from reportlab.lib.enums import TA_CENTER  # Center the PDF title text.
        from reportlab.lib.pagesizes import A4  # Use A4 paper size.
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # Format report text.
        from reportlab.lib.units import mm  # Set PDF sizes in millimeters.
        from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as error:
        raise RuntimeError("Install PDF support first: python -m pip install reportlab") from error

    output = io.BytesIO()  # Create the PDF in memory.
    document = SimpleDocTemplate(  # Set the paper and margins.
        output,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="Social Eagle Institution Report Card",
    )

    navy = colors.HexColor("#12324A")  # Set the school navy color.
    teal = colors.HexColor("#176B72")  # Set the school teal color.
    pale = colors.HexColor("#EAF3F4")  # Set a light table color.
    styles = getSampleStyleSheet()  # Load basic PDF text styles.
    title_style = ParagraphStyle(
        "SchoolTitle", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=19, leading=23, textColor=colors.white, alignment=TA_CENTER,
    )  # Style the school name in the PDF.
    subtitle_style = ParagraphStyle(
        "ReportSubtitle", parent=styles["Normal"], fontSize=10,
        textColor=colors.white, alignment=TA_CENTER,
    )  # Style the report subtitle.
    section_style = ParagraphStyle(
        "ReportSection", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=13, textColor=navy, spaceBefore=8, spaceAfter=7,
    )  # Style the section headings.
    body_style = ParagraphStyle(
        "ReportBody", parent=styles["BodyText"], fontSize=10,
        leading=15, textColor=colors.HexColor("#243B53"),
    )  # Style normal report text.

    story = []  # Store the PDF sections in order.
    logo = Image(str(LOGO_PATH), width=28 * mm, height=28 * mm)  # Add the eagle logo.
    header = Table(
        [[logo, [Paragraph("Social Eagle Institution", title_style),
                 Paragraph("STUDENT REPORT CARD", subtitle_style)], ""]],
        colWidths=[34 * mm, 106 * mm, 34 * mm],
        rowHeights=[32 * mm],
    )  # Place the logo and title in a header.
    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), navy),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))  # Style the PDF header.
    story.extend([header, Spacer(1, 8 * mm)])  # Add the header to the report.

    student_info = [[
        Paragraph(f"<b>Student</b><br/>{escape(report['name'])}", body_style),
        Paragraph(f"<b>Student ID</b><br/>{escape(report['student_id'])}", body_style),
        Paragraph(f"<b>Standard</b><br/>{escape(report['standard'])}", body_style),
    ]]
    info_table = Table(student_info, colWidths=[58 * mm, 58 * mm, 58 * mm])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), pale),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1DFE5")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))  # Style the student information boxes.
    story.extend([Paragraph("Student information", section_style), info_table, Spacer(1, 5 * mm)])

    subject_rows = [["Subject", "Mark", "Grade"]]  # Add the table headings.
    for subject, mark in report["marks"].items():  # Add each subject result.
        subject_rows.append([subject, f"{mark:g} / 100", get_grade(mark)])
    subject_table = Table(subject_rows, colWidths=[100 * mm, 42 * mm, 32 * mm], repeatRows=1)
    subject_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), teal),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, pale]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1DFE5")),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))  # Style the marks table.
    story.extend([Paragraph("Subject results", section_style), subject_table, Spacer(1, 6 * mm)])

    summary = Table(
        [["TOTAL", "AVERAGE", "OVERALL GRADE"],
         [f"{report['total']:g} / 600", f"{report['average']:.1f}%", report["grade"]]],
        colWidths=[58 * mm, 58 * mm, 58 * mm],
    )  # Add total, average, and grade summary.
    summary.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), navy),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, 1), pale),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, 1), 14),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1DFE5")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.white),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))  # Style the summary.
    story.extend([summary, Spacer(1, 6 * mm)])

    story.append(Paragraph("Grade bands: S 90–100 · A 80–89 · B 70–79 · C 50–69 · Fail below 50", body_style))
    story.append(Spacer(1, 4 * mm))
    report_date = datetime.now().strftime("%d %B %Y, %I:%M %p")
    story.append(Paragraph(f"Generated on {report_date}", body_style))
    document.build(story)  # Create the finished PDF.
    return output.getvalue()  # Return the PDF bytes for download.


def create_class_pdf(class_name, students, average_mark, highest_student, lowest_student):
    """Build a PDF summary of every student in the selected class."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as error:
        raise RuntimeError("Install PDF support first: python -m pip install reportlab") from error

    output = io.BytesIO()
    document = SimpleDocTemplate(
        output, pagesize=landscape(A4), leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=14 * mm, bottomMargin=14 * mm, title=f"{class_name} Class Report",
    )
    navy = colors.HexColor("#12324A")
    teal = colors.HexColor("#176B72")
    pale = colors.HexColor("#EAF3F4")
    styles = getSampleStyleSheet()
    centered_title = ParagraphStyle(
        "ClassReportTitle", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=18, leading=23, textColor=colors.white, alignment=TA_CENTER,
    )
    centered_subtitle = ParagraphStyle(
        "ClassReportSubtitle", parent=styles["Normal"], fontSize=11,
        textColor=colors.white, alignment=TA_CENTER,
    )
    body = ParagraphStyle(
        "ClassReportBody", parent=styles["BodyText"], fontSize=10,
        leading=14, textColor=colors.HexColor("#243B53"),
    )

    title_cell = [
        Paragraph("Social Eagle Institution", centered_title),
        Paragraph(f"CLASS RESULTS · {escape(class_name)}", centered_subtitle),
    ]
    if LOGO_PATH.exists():
        logo = Image(str(LOGO_PATH), width=25 * mm, height=25 * mm)
        banner = Table([[logo, title_cell]], colWidths=[35 * mm, 225 * mm], rowHeights=[29 * mm])
    else:
        banner = Table([[title_cell]], colWidths=[260 * mm], rowHeights=[29 * mm])
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), navy),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))

    summary = Table(
        [["Students", "Class average", "Highest mark", "Lowest mark"],
         [str(len(students)), f"{average_mark:.1f}%",
          f"{highest_student['Mark']} · {escape(highest_student['Name'])}",
          f"{lowest_student['Mark']} · {escape(lowest_student['Name'])}"]],
        colWidths=[45 * mm, 60 * mm, 75 * mm, 75 * mm],
    )
    summary.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), navy),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, 1), pale),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1DFE5")),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))

    rows = [["No.", "Student name", "Mark / 100", "Grade"]]
    rows.extend([[str(index), escape(student["Name"]), str(student["Mark"]), student["Grade"]]
                 for index, student in enumerate(students, start=1)])
    results = Table(rows, colWidths=[20 * mm, 140 * mm, 55 * mm, 40 * mm], repeatRows=1)
    results.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), teal),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, pale]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1DFE5")),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story = [banner, Spacer(1, 7 * mm), summary, Spacer(1, 8 * mm),
             Paragraph("Student results", ParagraphStyle(
                 "ClassResultsHeading", parent=styles["Heading2"],
                 textColor=navy, fontName="Helvetica-Bold")), results,
             Spacer(1, 5 * mm), Paragraph(
                 "Grade bands: S 90–100 · A 80–89 · B 70–79 · C 50–69 · Fail below 50", body),
             Spacer(1, 3 * mm), Paragraph(
                 f"Generated on {datetime.now().strftime('%d %B %Y, %I:%M %p')}", body)]
    document.build(story)
    return output.getvalue()


def handle_dialog_dismiss():  # Update app state when the popup is closed.
    st.session_state["show_report"] = False


def handle_class_dialog_dismiss():  # Close the class report popup after its × is clicked.
    st.session_state["show_class_report"] = False


def reset_form():  # Clear all student details and marks.
    st.session_state["student_name"] = ""  # Clear the student's name.
    st.session_state["student_id"] = ""  # Clear the student's ID.
    st.session_state["standard"] = STANDARDS[0]  # Reset the dropdown to 10th Standard.
    for index in range(6):  # Clear all six subject marks.
        st.session_state[f"mark_{index}"] = ""
    st.session_state["report_ready"] = False
    st.session_state["report_data"] = None
    st.session_state["show_report"] = False


def add_class_student():  # Add one student's name, mark, and grade to the chosen class.
    class_name = st.session_state["selected_class"]
    student_name = st.session_state.get("class_student_name", "").strip()
    entered_mark = st.session_state.get("class_mark", "").strip()

    if not student_name:
        st.session_state["class_message"] = ("error", "Enter the student's name.")
        return
    if not entered_mark:
        st.session_state["class_message"] = ("error", "Enter a mark from 0 to 100.")
        return
    if not entered_mark.isdigit() or int(entered_mark) > 100:
        st.session_state["class_message"] = ("error", "Use digits only and enter a whole number from 0 to 100.")
        return

    mark = int(entered_mark)
    roster = st.session_state["class_lists"].setdefault(class_name, [])
    roster.append({"Name": student_name, "Mark": mark, "Grade": get_grade(mark)})
    st.session_state["class_message"] = ("success", f"Added {student_name} to {class_name}.")
    st.session_state["class_student_name"] = ""
    st.session_state["class_mark"] = ""


def calculate_class_report():  # Calculate summary data and open the class report popup.
    class_name = st.session_state["selected_class"]
    students = st.session_state["class_lists"].get(class_name, [])
    if not students:
        st.session_state["class_message"] = ("error", "Add at least one student before creating the class report.")
        return
    marks = [student["Mark"] for student in students]
    average_mark = sum(marks) / len(marks)
    highest_student = max(students, key=lambda student: student["Mark"])
    lowest_student = min(students, key=lambda student: student["Mark"])
    try:
        pdf_data = create_class_pdf(class_name, students, average_mark, highest_student, lowest_student)
    except RuntimeError as error:
        st.session_state["class_message"] = ("error", str(error))
        return
    filename = re.sub(r"[^A-Za-z0-9_-]", "_", class_name)
    st.session_state["class_report_data"] = {
        "class_name": class_name, "students": students.copy(), "average": average_mark,
        "highest": highest_student.copy(), "lowest": lowest_student.copy(),
        "pdf": pdf_data, "filename": f"social_eagle_{filename}_class_report.pdf",
    }
    st.session_state["show_class_report"] = True
    st.session_state["class_message"] = None


@st.dialog("Class report", width="large", on_dismiss=handle_class_dialog_dismiss)
def show_class_report_dialog():  # Show the class summary and PDF download in a popup.
    report = st.session_state["class_report_data"]
    st.markdown(f"### {escape(report['class_name'])}")
    student_count, average_column, high_column, low_column = st.columns(4)
    student_count.metric("Students", len(report["students"]))
    average_column.metric("Class average", f"{report['average']:.1f}%")
    high_column.metric("Highest mark", f"{report['highest']['Mark']} · {report['highest']['Name']}")
    low_column.metric("Lowest mark", f"{report['lowest']['Mark']} · {report['lowest']['Name']}")
    st.dataframe(report["students"], hide_index=True, use_container_width=True)
    st.download_button(
        "Download class report as PDF", data=report["pdf"], file_name=report["filename"],
        mime="application/pdf", use_container_width=True,
    )


@st.dialog("Student report card", width="large", on_dismiss=handle_dialog_dismiss)
def show_report_dialog():  # Show results and the PDF download in a popup.
    report = st.session_state["report_data"]
    st.markdown(f"### {escape(report['name'])} · {escape(report['standard'])}")
    st.caption(f"Student ID: {escape(report['student_id'])}")

    total_col, average_col, grade_col = st.columns(3)
    total_col.metric("Total marks", f"{report['total']:g} / 600")
    average_col.metric("Average", f"{report['average']:.1f}%")
    grade_col.metric("Overall grade", report["grade"])
    st.progress(int(report["average"]))
    st.dataframe(report["rows"], hide_index=True, use_container_width=True)

    if report["grade"] == "S":
        st.markdown(
            '<div class="result-message result-success">Outstanding result! Keep soaring!</div>',
            unsafe_allow_html=True,
        )
    elif report["failed_subjects"]:
        st.markdown(
            '<div class="result-message result-encourage">Keep going! One result does not define you. '
            'Review these subjects, ask for help, and try again.</div>',
            unsafe_allow_html=True,
        )
        st.info("Subjects to work on: " + ", ".join(report["failed_subjects"]))
    else:
        st.markdown(
            '<div class="result-message result-success">Good work! Keep learning and building on your progress.</div>',
            unsafe_allow_html=True,
        )

    st.download_button(
        label="Download report card as PDF",
        data=report["pdf"],
        file_name=report["filename"],
        mime="application/pdf",
        use_container_width=True,
    )
    st.caption("Close this window using the × at the top. The reset button will then appear on the page.")


st.session_state.setdefault("show_report", False)  # Remember if the report popup is open.
st.session_state.setdefault("report_ready", False)  # Remember if a report has been created.
st.session_state.setdefault("report_data", None)  # Store the latest report for the popup.
st.session_state.setdefault("class_lists", {})  # Keep a separate roster for each class.
st.session_state.setdefault("selected_class", CLASSES[0])  # Remember the selected class.
st.session_state.setdefault("class_message", None)  # Keep the latest class-entry message.
st.session_state.setdefault("show_class_report", False)  # Remember if the class popup is open.
st.session_state.setdefault("class_report_data", None)  # Store the latest class report.

background_style = ""  # Use the image only when it is available.
if BACKGROUND_PATH.exists():
    image_data = base64.b64encode(BACKGROUND_PATH.read_bytes()).decode("ascii")
    background_style = (
        "background-image: linear-gradient(rgba(247, 250, 252, 0.70), "
        f"rgba(247, 250, 252, 0.70)), url('data:image/png;base64,{image_data}');"
    )

# Apply high-contrast colors and the new background image.
st.markdown(
    f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        {background_style}
        background-color: #edf2f5;
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    .block-container {{ max-width: 1320px; padding-top: 1.5rem; padding-bottom: 3rem; }}
    .stMarkdown, [data-testid="stWidgetLabel"] p, label {{ color: #183047 !important; }}
    h1, h2, h3 {{ font-family: Georgia, 'Times New Roman', serif !important; color: #12324A !important; }}
    .school-banner {{ position: relative; background: linear-gradient(120deg, #12324A, #176B72); color: white; padding: 22px; border-radius: 18px; margin-bottom: 18px; box-shadow: 0 10px 24px #12324A30; min-height: 112px; display: flex; align-items: center; justify-content: center; }}
    .school-banner h1, .school-banner p {{ color: white !important; margin: 0; text-align: center; }}
    .school-logo {{ position: absolute; left: 16px; top: 50%; transform: translateY(-50%); width: 92px; height: 92px; object-fit: contain; }}
    .school-title {{ width: 100%; text-align: center; padding: 0 92px; }}
    [role="dialog"] {{ background: #F7FAFC !important; color: #183047 !important; }}
    [role="dialog"] h1, [role="dialog"] h2, [role="dialog"] h3, [role="dialog"] p, [role="dialog"] label {{ color: #183047 !important; }}
    [role="dialog"] [data-testid="stMetricLabel"] p {{ color: #52677A !important; }}
    [role="dialog"] [data-testid="stMetricValue"] {{ color: #12324A !important; }}
    [role="dialog"] [data-testid="stDataFrame"] {{ background: white !important; }}
    [data-testid="stForm"] {{ background: rgba(255,255,255,0.96); padding: 22px; border: 1px solid #D8E3EA; border-radius: 18px; }}
    [data-testid="stFormSubmitButton"] button, [data-testid="stDownloadButton"] button {{ background: #176B72 !important; color: white !important; border: 0 !important; min-height: 3rem; font-weight: 700; }}
    [data-testid="stFormSubmitButton"] button p, [data-testid="stDownloadButton"] button p {{ color: white !important; }}
    [data-testid="stButton"] button {{ background: #176B72 !important; color: #ffffff !important; border: 0 !important; font-weight: 700; }}
    [data-testid="stButton"] button:hover, [data-testid="stButton"] button:focus {{ background: #12565C !important; color: #ffffff !important; border: 0 !important; }}
    [data-testid="stButton"] button p {{ color: #ffffff !important; }}
    div[data-testid="stAlert"] p {{ color: #183047 !important; }}
    .result-message {{ border-radius: 12px; padding: 14px 16px; font-weight: 700; margin: 8px 0 14px; }}
    .result-success {{ color: #12452b; background: #d8f3e4; border: 1px solid #83c99b; }}
    .result-encourage {{ color: #173b61; background: #e1efff; border: 1px solid #91bce8; }}
    </style>
    """,
    unsafe_allow_html=True,
)

if LOGO_PATH.exists():  # Show the eagle logo with centered school text.
    logo_base64 = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
    st.markdown(
        f'<div class="school-banner">'
        f'<img class="school-logo" src="data:image/png;base64,{logo_base64}" alt="Eagle logo">'
        '<div class="school-title"><h1>Social Eagle Institution</h1>'
        '<p>Student Results Portal · Learn, grow, and soar</p></div></div>',
        unsafe_allow_html=True,
    )
else:  # Show an eagle symbol if the logo image is missing.
    st.markdown(
        '<div class="school-banner"><h1>🦅 Social Eagle Institution</h1>'
        '<p>Student Results Portal · Learn, grow, and soar</p></div>',
        unsafe_allow_html=True,
    )

st.markdown("# Students Grade Manager")  # Name the combined student and class tool.
left_column, right_column = st.columns([1, 1.4], gap="large")  # Put class and individual tools side by side.

with left_column:  # Build the multi-student class manager on the left.
    st.markdown("### Class manager")
    st.write("Choose a class, then add each student's name and overall mark.")
    with st.form("class_student_form"):
        st.selectbox("Class", CLASSES, key="selected_class")
        st.text_input("Student name", placeholder="Enter the student's name", key="class_student_name")
        st.text_input(
            "Mark (0–100)", placeholder="Type a whole number", max_chars=3,
            validate=(r"^(?:[0-9]{1,2}|100)?$", "Use digits only, from 0 to 100."),
            key="class_mark",
        )
        st.form_submit_button("Add student", use_container_width=True, on_click=add_class_student)

    if st.session_state["class_message"]:
        message_type, message_text = st.session_state["class_message"]
        if message_type == "success":
            st.success(message_text)
        else:
            st.error(message_text)

    selected_class = st.session_state["selected_class"]
    class_students = st.session_state["class_lists"].get(selected_class, [])
    if class_students:
        st.markdown("#### Students in this class")
        st.dataframe(class_students, hide_index=True, use_container_width=True)
        st.button(
            "Calculate class report", use_container_width=True, key="calculate_class",
            on_click=calculate_class_report,
        )
    else:
        st.info("No students have been added to this class yet.")

with right_column:  # Keep the existing six-subject individual PDF form on the right.
    st.markdown("### Individual student report")
    st.write("Enter one student's details and marks for all six subjects.")
    with st.form("student_entry_form"):
        student_name = st.text_input("Student name", placeholder="Enter the student's name", key="student_name")
        student_id = st.text_input("Student ID", placeholder="Enter the student ID", key="student_id")
        standard = st.selectbox("Standard", STANDARDS, key="standard")
        st.markdown("#### Subject marks")

        mark_inputs = {}  # Keep the typed mark for each subject.
        for index, subject in enumerate(SUBJECTS):
            subject_column, mark_column = st.columns([2, 1])
            with subject_column:
                st.write(subject)
            with mark_column:
                mark_inputs[subject] = st.text_input(
                    f"{subject} mark", placeholder="Type 0–100", max_chars=3,
                    validate=(r"^(?:[0-9]{1,2}|100)?$", "Use digits only and enter a whole number from 0 to 100."),
                    label_visibility="collapsed", key=f"mark_{index}",
                )
        submitted = st.form_submit_button("Create individual PDF report", use_container_width=True)

if submitted:  # Validate marks and save the report for the popup.
    errors = []  # Collect validation problems.
    marks = {}  # Store valid marks as numbers.

    if not student_name.strip():
        errors.append("Enter the student's name.")
    if not student_id.strip():
        errors.append("Enter the student ID.")

    for subject, entered_mark in mark_inputs.items():  # Check every subject mark.
        if not entered_mark:
            errors.append(f"{subject}: enter a mark from 0 to 100.")
        elif not entered_mark.isdigit() or int(entered_mark) > 100:
            errors.append(f"{subject}: enter digits only, from 0 to 100.")
        else:
            marks[subject] = int(entered_mark)

    if errors:  # Show readable errors when information is missing or invalid.
        for message in errors:
            st.error(message)
    else:
        total = sum(marks.values())  # Add all six marks.
        average = total / len(SUBJECTS)  # Calculate the average score.
        overall_grade = get_grade(average)  # Find the overall grade.
        result_rows = [  # Prepare the subject results for the popup.
            {"Subject": subject, "Mark": f"{mark:g} / 100", "Grade": get_grade(mark)}
            for subject, mark in marks.items()
        ]
        failed_subjects = [subject for subject, mark in marks.items() if mark < 50]

        report = {
            "name": student_name.strip(),
            "student_id": student_id.strip(),
            "standard": standard,
            "marks": marks,
            "total": total,
            "average": average,
            "grade": overall_grade,
            "rows": result_rows,
            "failed_subjects": failed_subjects,
        }  # Keep the report details together.

        try:
            report["pdf"] = create_pdf(report)  # Create the downloadable PDF.
            safe_id = re.sub(r"[^A-Za-z0-9_-]", "_", report["student_id"])
            report["filename"] = f"social_eagle_report_{safe_id}.pdf"

            st.session_state["report_data"] = report
            st.session_state["report_ready"] = True
            st.session_state["show_report"] = True
        except RuntimeError as error:
            st.error(str(error))

if st.session_state["show_report"] and st.session_state["report_data"]:  # Open the result popup.
    show_report_dialog()

if st.session_state["show_class_report"] and st.session_state["class_report_data"]:
    show_class_report_dialog()

if st.session_state["report_ready"] and not st.session_state["show_report"]:  # Offer reset after popup closes.
    st.button("Reset individual student details", on_click=reset_form, type="secondary")
