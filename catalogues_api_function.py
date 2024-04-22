# IMPORT NECESSARY LIBRARIES
import http.client
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
import pandas as pd


#####################################
# Function to Call the Catalogues API
######################################

'''
calling catalogues: function used to call efsa's catalogues
             args:
                    - key : Subscription key which provides access to this API
                    - catalogue_code: catalogue code from EFSA Catalogues
            returns:
                    - term_df: pandas dataframe containing the catalogue
'''
def calling_catalogues(key, catalogue_code):

    # Define request headers - contains the authentication information
    headers = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': f'{key}',
    }

    # Define request body
    body = f'''
    {{
        "ExportCatalogueFile": 
        {{ 
            "catalogueCode" : "{catalogue_code}", 
            "catalogueVersion" : "", 
            "exportType" : "catalogFullDefinition", 
            "group" : "", 
            "dcCode" : "", 
            "fileType" : "XML" 
        }}
    }}
    '''

    # Define additional parameters (OPTIONAL)
    params = urllib.parse.urlencode({})

    # Establish connection, request catalogue, get response
    try:
        conn = http.client.HTTPSConnection('openapi.efsa.europa.eu')
        conn.request("POST", "/api/catalogues/catalogue-file?%s" % params, body, headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()

    # Raise error if failed
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))

    # Decode data and split lines into a list
    data = data.decode('utf-8')
    data_list = data.splitlines()

    # Iterate through list to remove non-XML code
    data_list = [line for line in data_list if line.strip().startswith('<')]

    # Recombine data into a string
    data = '\n'.join(data_list)

    # Create XML tree
    root = ET.ElementTree(ET.fromstring(data))

    # Create Catalogue Dataframe
    cat_nodes = [root.find(".//catalogueDesc"),
                root.find(".//catalogueVersion"),
                root.find(".//catalogueGroups")]
    cat_cols = []
    cat_rows = []
    cat_row = {}

    for node in cat_nodes:
        if node is not None:  # Add a check for None
            for n in node:
                if n.text:
                    cat_cols.append(n.tag)
                    cat_row[n.tag] = n.text

    cat_rows.append(cat_row)
    cat_df = pd.DataFrame(cat_rows, columns=cat_cols)

    # Create Hierarchy Dataframe
    hierarchy_cols = []
    hierarchy_elements = root.find('.//hierarchy')

    if hierarchy_elements is not None:
        for node in hierarchy_elements:
            for subnode in node:
                if subnode.text != '':
                    hierarchy_cols.append(subnode.tag)

    hierarchy_rows = []

    for node in root.findall('.//hierarchy'):
        hierarchy_row = {}

        for subnode in node.iter():
            if subnode.text != '':
                hierarchy_row[subnode.tag] = subnode.text

        hierarchy_rows.append(hierarchy_row)

    hierarchy_df = pd.DataFrame(hierarchy_rows, columns=hierarchy_cols)

    # Create Attribute Dataframe
    attr_cols = []
    attr_elements = root.find('.//attribute')  # Get the attribute element

    if attr_elements is not None:  # Check if the attribute element is not None
        for node in attr_elements:
            for subnode in node:
                if subnode.text != '':
                    attr_cols.append(subnode.tag)

    attr_rows = []

    if attr_elements is not None:  # Check if the attribute element is not None
        for node in attr_elements:
            attr_row = {}
            for subnode in node.iter():
                if subnode.text != '':
                    attr_row[subnode.tag] = subnode.text
            attr_rows.append(attr_row)

    attr_df = pd.DataFrame(attr_rows, columns=attr_cols)


    # Create Term Dataframe
    term_cols = []
    term_desc_elements = root.findall(".//termDesc")

    if term_desc_elements is not None:
        for term_desc in root.findall(".//termDesc"):
            for node in term_desc:
                if node.text.strip() and node.tag not in term_cols:
                    term_cols.append(node.tag)

    term_version_elements = root.findall(".//termVersion")

    if term_version_elements is not None:
        for term_version in term_version_elements:
            for node in term_version:
                if node.text.strip() and node.tag not in term_cols:
                    term_cols.append(node.tag)

    term_implicit_elements = root.findall(".//implicitAttributes")

    if term_implicit_elements is not None:
        for implicit_attr in root.findall(".//implicitAttributes"):
            for node in implicit_attr.iter():
                if node.tag == 'attributeCode' and node.text not in term_cols:
                    term_cols.append(node.text)

    term_cols.extend(['masterFlag', 'masterParentCode', 'masterOrder', 'masterReportable', 'masterHierarchyCode'])

    term_hierarchyassigments_elements = root.findall(".//hierarchyAssignments")

    if term_hierarchyassigments_elements is not None:
        for hierarchy_assign in root.findall(".//hierarchyAssignments"):
            for node in hierarchy_assign:
                hierarchy_code = node.find('hierarchyCode')

            if hierarchy_code.text != cat_df['name'].iloc[0]:
                for field in ['Flag', 'ParentCode', 'Order', 'Reportable', 'HierarchyCode']:
                    col_name = '{}{}'.format(hierarchy_code.text, field)
                    if col_name not in term_cols:
                        term_cols.append(col_name)

    term_rows = []

    for term in root.findall(".//term"):
        term_row = {}

        for node in term:
            if node.tag == 'termDesc' or node.tag == 'termVersion':
                for subnode in node:
                    if subnode.text.strip():
                        term_row[subnode.tag] = subnode.text

            if node.tag == 'hierarchyAssignments':
                for subnode in node:
                    hierarchy_code = subnode.find('hierarchyCode').text
                    if hierarchy_code == cat_df['name'].iloc[0]:
                        term_row['masterParentCode'] = subnode.find('parentCode').text
                        term_row['masterOrder'] = subnode.find('order').text
                        reportable_node = subnode.find('reportable')
                        if reportable_node is not None:  # Check if reportable_node is not None
                            term_row['masterReportable'] = reportable_node.text
                        else:
                            term_row['masterReportable'] = None  # or whatever default value you want
                    else:
                        term_row['{}ParentCode'.format(hierarchy_code)] = subnode.find('parentCode').text
                        term_row['{}Order'.format(hierarchy_code)] = subnode.find('order').text
                        reportable_node = subnode.find('reportable')
                        if reportable_node is not None:  # Check if reportable_node is not None
                            term_row['{}Reportable'.format(hierarchy_code)] = reportable_node.text
                        else:
                            term_row['{}Reportable'.format(hierarchy_code)] = None  # or whatever default value you want


            if node.tag == 'implicitAttributes':
                for implicit_att in node:
                    attr_code_node = implicit_att.find('attributeCode')
                    attr_value_node = implicit_att.find('attributeValue')
                    if attr_code_node is not None and attr_value_node is not None:
                        attr_code = attr_code_node.text
                        attr_value = attr_value_node.text
                        term_row[attr_code] = attr_value


        term_rows.append(term_row)

    term_df = pd.DataFrame(term_rows, columns=term_cols)

    # Returning only the termCode and the termExtendedName - columns only need for the enrichement
    return term_df[['termCode', 'termExtendedName']]