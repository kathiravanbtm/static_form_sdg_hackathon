import re
from flask import Flask, request, send_file, render_template
from docx import Document
import os
import io
import re 
from docx.shared import Pt 

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Function to clean the text by removing unwanted newlines and keeping paragraph separation



import re

def clean_pdf_text(input_text):
    # Replace multiple newlines with a single space
    cleaned_text = re.sub(r'\n+', ' ', input_text)

    # Remove leading/trailing whitespace
    cleaned_text = cleaned_text.strip()

    # Ensure there's no extra spaces between sentences
    cleaned_text = re.sub(r' +', ' ', cleaned_text)

    # Preserve double spacing if user entered it explicitly
    cleaned_text = re.sub(r'(\s{2,})', '  ', cleaned_text)

    # Fix any unwanted line breaks by checking if they are part of a list (keeping list structure intact)
    cleaned_text = re.sub(r'([^\n])\n([^\n])', r'\1 \2', cleaned_text)

    # Optional: If there are specific section identifiers like 'Mass Storage System' etc., ensure they are kept as headings
    cleaned_text = re.sub(r'(Mass Storage System|UNIX Security|Mobile OS)', r'\n\1\n', cleaned_text)

    # Optional: Adding paragraph breaks where needed
    cleaned_text = cleaned_text.replace(' .', '.\n')

    return cleaned_text



@app.route('/')
def index():
    return render_template('index.html')  # Load the HTML form

@app.route('/generate', methods=['POST'])
def generate_doc():
    template_path = os.path.join(BASE_DIR, "template.docx")

    if not os.path.exists(template_path):
        return "Error: template.docx not found!", 404

    doc = Document(template_path)

   # Collect form data and clean all text fields if pasted from PDF
    semester = request.form.get('Semester', '')
    course_name = request.form.get('CourseName', '')
    course_code = request.form.get('CourseCode', '')
    course_description = request.form.get('CourseDescription', '')
    
    prerequisites = [clean_pdf_text(p.strip()) for p in request.form.getlist('Prerequisites') if p.strip()]
    objectives = [clean_pdf_text(obj.strip()) for obj in request.form.getlist('objective') if obj.strip()]
    course_outcomes = [clean_pdf_text(outcome.strip()) for outcome in request.form.getlist('course_outcome') if outcome.strip()]
    textbooks = [clean_pdf_text(textbook.strip()) for textbook in request.form.getlist('textbook') if textbook.strip()]
    references = [clean_pdf_text(reference.strip()) for reference in request.form.getlist('reference') if reference.strip()]
    assessments_grading = clean_pdf_text(request.form.get('AssessmentsGrading', ''))
    course_format = clean_pdf_text(request.form.get('course_format', ''))
    assessments = clean_pdf_text(request.form.get('assessments', ''))
    grading = clean_pdf_text(request.form.get('grading', ''))

    # Format placeholders into readable lists and apply `<REMOVE>` for empty values
    placeholders = {
        "{Semester}": semester if semester else "<REMOVE>",
        "{CourseName}": course_name if course_name else "<REMOVE>",
        "{CourseCode}": course_code if course_code else "<REMOVE>",
        "{Coursedescriptionname}": "COURSE DESCRIPTION" if course_description else "<REMOVE>",
        "{CourseDescription}": course_description if course_description else "<REMOVE>",
        "{prerequisitename}": "PREREQUISITES" if prerequisites else "<REMOVE>",
        "{Prerequisites}": "\n".join([f"{i+1}. {prereq}" for i, prereq in enumerate(prerequisites)]) if prerequisites else "<REMOVE>",
        "{objectivename}": "COURSE OBJECTIVES" if objectives else "<REMOVE>",
        "{Objectives}": "\n".join([f"{i+1}. {obj}" for i, obj in enumerate(objectives)]) if objectives else "<REMOVE>",
        "{assessmentsandgradingname}": "ASSESSMENTS AND GRADING" if assessments_grading else "<REMOVE>",
        "{AssessmentsGrading}": assessments_grading if assessments_grading else "<REMOVE>",
        "{courseoutcomesname}": "COURSE OUTCOMES" if course_outcomes else "<REMOVE>",
        "{CourseOutcomes}": "\n".join([f"CO{i+1}: {outcome}" for i, outcome in enumerate(course_outcomes)]) if course_outcomes else "<REMOVE>",
        "{textbooksname}": "TEXTBOOKS   " if textbooks else "<REMOVE>",
        "{Textbooks}": "\n".join([f"{i+1}. {text}" for i, text in enumerate(textbooks)]) if textbooks else "<REMOVE>",
        "{referencesname}": "REFERENCES" if references else "<REMOVE>",
        "{References}": "\n".join([f"{i+1}. {ref}" for i, ref in enumerate(references)]) if references else "<REMOVE>",
        "{courseformatname}": "COURSE FORMAT\n" if course_format else "<REMOVE>",
        "{CourseFormat}": course_format if course_format else "<REMOVE>",
        "{Assessments}": assessments if assessments else "<REMOVE>",
        "{Grading}": grading if grading else "<REMOVE>",
    }

    # Collect Practical Periods checkbox and value
    has_practical = request.form.get('hasPractical')  
    practical_periods = request.form.get('practical_periods') if has_practical else "<REMOVE>"
    # Add practical periods to placeholders if applicable
    if has_practical and practical_periods:
        placeholders["{PracticalPeriodsName}"] = "PRACTICAL PERIODS "
        placeholders["{PracticalPeriods}"] = practical_periods if practical_periods else "<REMOVE>"
    else:
        placeholders["{PracticalPeriodsName}"] = "<REMOVE>"
        placeholders["{PracticalPeriods}"] = "<REMOVE>"

    # Dynamically collect and format units including the number of periods
    units = []
    total_periods = 0
    i = 1

    while True:
        unit_title = clean_pdf_text(request.form.get(f'unit_title_{i}', ''))
        unit_content = clean_pdf_text(request.form.get(f'unit_content_{i}', ''))
        unit_periods = request.form.get(f'unit_periods_{i}')

        if not unit_title or not unit_content:
            break

        try:
            unit_periods = int(unit_periods) if unit_periods else 0
        except ValueError:
            unit_periods = 0

        total_periods += unit_periods
        units.append((unit_title, unit_content, unit_periods))
        i += 1
    # Format units into a structured text block with periods
    units_text = ""
    for i, (unit_title, unit_content, unit_periods) in enumerate(units, 1):
        units_text += f"UNIT {i}: {unit_title} (No. of Periods: {unit_periods})\n\n{unit_content}\n\n"

    # Add formatted units and total periods to placeholders
    placeholders["{TotalPeriods}"] ="TOTAL NUMBER OF PERIODS:" + str(total_periods) if total_periods > 0 else "<REMOVE>"

    replace_units_with_formatting(doc, units)
    # print(placeholders)
    replace_placeholders_in_doc(doc, placeholders)
    
    # Save and return the generated document
    file_stream = io.BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)

    return send_file(file_stream, as_attachment=True, download_name="Course_Syllabus.docx",
                     mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

def replace_placeholders_in_doc(doc, placeholders):
    """Replaces placeholders in paragraphs and removes lines marked `<REMOVE>`"""
    for paragraph in doc.paragraphs:
        replace_placeholders_in_paragraph(paragraph, placeholders)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    replace_placeholders_in_paragraph(paragraph, placeholders)

def replace_placeholders_in_paragraph(paragraph, placeholders):
    """Replaces placeholders while preserving formatting. Removes `<REMOVE>` placeholders."""
    if paragraph.runs:
        full_text = ''.join(run.text for run in paragraph.runs)

        for placeholder, value in placeholders.items():
            if placeholder in full_text:
                full_text = full_text.replace(placeholder, value)

        # Remove the entire paragraph if `<REMOVE>` is present
        if "<REMOVE>" in full_text:
            p_element = paragraph._element
            p_element.getparent().remove(p_element)
            return

        # Apply the modified text while keeping formatting
        for i, run in enumerate(paragraph.runs):
            if i == 0:
                run.text = full_text
            else:
                run.text = ""
def replace_units_with_formatting(doc, units):
    """Finds {Units} placeholder and inserts formatted units with proper indentation & normal content formatting."""
    for paragraph in doc.paragraphs:
        if "{Units}" in paragraph.text:
            p_element = paragraph._element  # Store reference to remove placeholder
            parent = p_element.getparent()  # Get parent XML element
            paragraph_style = paragraph.style  # Store the style of the original paragraph

            # Create a new paragraph at the same location before removing {Units}
            new_paragraph = paragraph.insert_paragraph_before("")
            new_paragraph.style = paragraph_style  # Apply the same style as the placeholder
            parent.remove(p_element)  # Remove {Units} placeholder

            for i, (unit_title, unit_content, unit_periods) in enumerate(units, 1):
                # Insert Unit Title (Bold) with correct style
                title_paragraph = new_paragraph.insert_paragraph_before("")
                title_paragraph.style = paragraph_style  # Apply same style
                title_run = title_paragraph.add_run(f"UNIT {i}: {unit_title} (No. of Periods: {unit_periods})\n")
                title_run.bold = True
                title_run.font.size = Pt(12)

                # Insert Unit Content (Normal) with correct indentation
                content_paragraph = new_paragraph.insert_paragraph_before("")
                content_paragraph.style = paragraph_style  # Apply same style
                content_run = content_paragraph.add_run(f"{unit_content}\n\n")
                content_run.bold = False  # 🔥 Fix: Ensure normal text
                content_run.font.size = Pt(11)

            break 

if __name__ == '__main__':
    app.run(debug=True)
