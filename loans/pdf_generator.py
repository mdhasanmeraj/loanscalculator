import requests
import json
import io
import base64
from django.template.loader import get_template
from weasyprint import HTML, CSS
import os

def get_base64_image(image_path):
    """Converts a local image file to a base64 string."""
    if not os.path.exists(image_path):
        return None
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def generate_pie_chart(principal, interest):
    """Generates a base64 encoded pie chart image using QuickChart API."""
    
    # Chart configuration
    chart_config = {
        "type": "pie",
        "data": {
            "labels": ["Principal", "Interest"],
            "datasets": [{
                "data": [round(float(principal), 2), round(float(interest), 2)],
                "backgroundColor": ["#1E3A8A", "#DC2626"]
            }]
        },
        "options": {
            "plugins": {
                "legend": {
                    "position": "bottom",
                    "labels": {
                        "fontSize": 14,
                        "fontStyle": "bold"
                    }
                },
                "datalabels": {
                    "color": "#fff",
                    "font": {
                        "weight": "bold",
                        "size": 16
                    }
                }
            }
        }
    }

    # QuickChart URL (using the JSON config)
    import urllib.parse
    encoded_config = urllib.parse.quote(json.dumps(chart_config))
    url = f"https://quickchart.io/chart?c={encoded_config}&w=400&h=400&devicePixelRatio=2"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            # Encode the image in base64
            return base64.b64encode(response.content).decode('utf-8')
    except Exception as e:
        print(f"Error generating chart via QuickChart: {e}")
        
    return None

def generate_brochure_pdf(customer_data, bank_comparisons, logo_url=None):
    """
    Renders the HTML template and converts it to PDF using WeasyPrint.
    """
    template_path = 'loans/brochure_template.html'
    context = {
        'customer': customer_data,
        'banks': bank_comparisons,
        'logo_url': logo_url
    }
    
    # Render template
    template = get_template(template_path)
    html_content = template.render(context)
    
    # Convert to PDF
    pdf_file = HTML(string=html_content).write_pdf()
    
    return pdf_file

def generate_quotation_pdf(context_data):
    """
    Renders the HTML template and converts it to PDF using WeasyPrint for the Instant Calculator Report.
    """
    template_path = 'loans/quotation_template.html'
    
    # Render template
    template = get_template(template_path)
    html_content = template.render(context_data)
    
    # Convert to PDF
    pdf_file = HTML(string=html_content).write_pdf()
    
    return pdf_file
