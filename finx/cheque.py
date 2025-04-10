from fpdf import FPDF
from num2words import num2words

def convert_amount_to_words(amount):
    """
    Convert a numerical amount to words with BHD format.
    :param amount: float - the numerical amount
    :return: str - the amount in words with BHD currency
    """
    words = num2words(amount, to='currency', lang='en')
    return words.replace('euro', 'Dinar').replace('cents', 'Fils')

def format_bhd(amount):
    """
    Format the amount to BHD format with two decimal places.
    :param amount: float - the numerical amount
    :return: str - formatted amount
    """
    return f"BHD {amount:,.2f}"

def generate_cheque(cheque_data):
    """
    Generates a cheque PDF adjusted to match the original cheque layout and logic.

    :param cheque_data: Dictionary containing cheque details.
    """
    pdf = FPDF(format='A4', unit='mm')
    pdf.add_page()

    # Set font and ensure no borders or additional formatting
    pdf.set_font('Arial', '', 12)

    # Bank Name (Top-Center)
    pdf.set_xy(80, 10)
    pdf.cell(50, 10, cheque_data['bank_name'], align='C')

    # Payee Name ("Pay to the Order of")
    pdf.set_xy(20, 45)
    pdf.cell(0, 10, "Pay to the Order of:")
    pdf.set_xy(70, 45)
    pdf.cell(0, 10, cheque_data['payee_name'], border='B')

    # Amount in Words
    pdf.set_xy(20, 55)
    pdf.cell(0, 10, "Amount in Words:")
    pdf.set_xy(70, 55)
    pdf.multi_cell(120, 8, cheque_data['amount_words'], border='B')

    # Amount in Figures
    pdf.set_xy(160, 45)
    pdf.cell(30, 10, cheque_data['amount_figures'], border='B', align='R')

    # Date (Split into day, month, year for precise alignment)
    date_parts = cheque_data['date'].split('/')
    pdf.set_xy(160, 30)
    pdf.cell(10, 10, date_parts[0])  # Day
    pdf.set_xy(170, 30)
    pdf.cell(10, 10, date_parts[1])  # Month
    pdf.set_xy(180, 30)
    pdf.cell(10, 10, date_parts[2])  # Year

    # Save the PDF
    output_filename = "cheque.pdf"
    pdf.output(output_filename)
    print(f"Cheque saved as {output_filename}")

# Example cheque data
amount = 1050.0
cheque_data_example = {
    'bank_name': 'Bank of Python',
    'payee_name': 'John Doe',
    'amount_words': convert_amount_to_words(amount),
    'amount_figures': format_bhd(amount),
    'date': '01/01/2025'
}

# Generate the cheque
generate_cheque(cheque_data_example)
