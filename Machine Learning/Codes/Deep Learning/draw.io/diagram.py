from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString

def create_shape(parent, id, value, x, y, width=160, height=60):
    shape = SubElement(parent, 'mxCell', {
        'id': id,
        'value': value,
        'style': 'shape=rectangle;whiteSpace=wrap;html=1;',
        'vertex': '1',
        'parent': '1'
    })
    geometry = SubElement(shape, 'mxGeometry', {
        'x': str(x),
        'y': str(y),
        'width': str(width),
        'height': str(height),
        'as': 'geometry'
    })
    return shape

root = Element('mxGraphModel', {
    'dx': '1024', 'dy': '768', 'grid': '1', 'gridSize': '10',
    'guides': '1', 'tooltips': '1', 'connect': '1', 'arrows': '1',
    'fold': '1', 'page': '1', 'pageScale': '1', 'pageWidth': '850',
    'pageHeight': '1100', 'math': '0', 'shadow': '0'
})

root_cell = SubElement(root, 'root')
SubElement(root_cell, 'mxCell', {'id': '0'})
SubElement(root_cell, 'mxCell', {'id': '1', 'parent': '0'})

# Main Structure
create_shape(root_cell, 'A', 'Mixed-Methods Research Approach', 300, 20)
create_shape(root_cell, 'B1', 'Qualitative Component<br>- Design decisions<br>- Chatbot behavior', 100, 120)
create_shape(root_cell, 'B2', 'Quantitative Component<br>- Metrics<br>- PII analysis', 500, 120)

create_shape(root_cell, 'C1', 'Response Accuracy', 500, 220)
create_shape(root_cell, 'D1', 'Classification\nAccuracy = Correct / Total', 300, 320)
create_shape(root_cell, 'D2', 'Factual QA\nEM + F1 Score', 500, 320)
create_shape(root_cell, 'D3', 'PII Tasks\nAccuracy = no leakage / total', 700, 320)

create_shape(root_cell, 'C2', 'PII Removal Effectiveness', 500, 420)
create_shape(root_cell, 'E1', 'Define PII', 200, 520)
create_shape(root_cell, 'E2', 'Detection Tools', 400, 520)
create_shape(root_cell, 'E3', 'Calculate Metrics', 600, 520)

create_shape(root_cell, 'F1', 'Precision / Recall / F1', 500, 600)
create_shape(root_cell, 'F2', 'Leakage Rate\n1 - (post / pre)', 600, 660)
create_shape(root_cell, 'F3', 'False Positive Rate', 700, 720)
create_shape(root_cell, 'F4', 'Utility Score\n(BLEU, ROUGE, etc)', 800, 780)

create_shape(root_cell, 'C3', 'Cosine Similarity Evaluation', 500, 860)
create_shape(root_cell, 'G1', '1. Embedding Model\n(SBERT, Ada)', 300, 940)
create_shape(root_cell, 'G2', '2. Compute Similarity', 500, 940)
create_shape(root_cell, 'G3', '3. Interpret Results', 700, 940)

# Generate XML file
pretty_xml = parseString(tostring(root)).toprettyxml(indent="  ")
with open("pii_research_diagram.drawio", "w", encoding="utf-8") as f:
    f.write(pretty_xml)

print("Draw.io file generated as 'pii_research_diagram.drawio'")
