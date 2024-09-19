import xml.etree.ElementTree as ET

def parse_xml_to_bib(xml_file):
    # Parse the XML file
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # Define the namespace
    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
    
    # Open a file to write the BibTeX entries
    with open('output.bib', 'w') as bibfile:
        # Iterate over each bibliographic entry
        for biblStruct in root.findall('.//tei:biblStruct', ns):
            # Extracting elements
            analytic = biblStruct.find('tei:analytic', ns)
            monogr = biblStruct.find('tei:monogr', ns)
            meeting = monogr.find('tei:meeting', ns) if monogr is not None else None
            imprint = monogr.find('tei:imprint', ns) if monogr is not None else None
            
            # Extract title and authors
            title = analytic.find('.//tei:title', ns).text if analytic is not None and analytic.find('.//tei:title', ns) is not None else ''
            authors = analytic.findall('.//tei:author/tei:persName', ns) if analytic is not None else []
            
            # Format authors for BibTeX
            author_list = ' and\n      '.join([f"{author.find('tei:surname', ns).text}, {author.find('tei:forename', ns).text}" for author in authors if author.find('tei:surname', ns) is not None and author.find('tei:forename', ns) is not None])
            
            # Extract conference and other details
            booktitle = monogr.find('.//tei:title[@level="m"]', ns).text if monogr is not None and monogr.find('.//tei:title[@level="m"]', ns) is not None else ''
            address = meeting.find('.//tei:address/tei:addrLine', ns).text if meeting is not None and meeting.find('.//tei:address/tei:addrLine', ns) is not None else ''
            publisher = imprint.find('tei:publisher', ns).text if imprint is not None and imprint.find('tei:publisher', ns) is not None else ''
            date = imprint.find('tei:date', ns).get('when') if imprint is not None and imprint.find('tei:date', ns) is not None else ''
            pages = imprint.find('tei:biblScope[@unit="page"]', ns)
            page_range = f"{pages.get('from')}--{pages.get('to')}" if pages is not None else ''
            doi = analytic.find('.//tei:idno[@type="DOI"]', ns).text if analytic is not None and analytic.find('.//tei:idno[@type="DOI"]', ns) is not None else ''
            
            # Construct the BibTeX entry
            if date and '-' in date:
                month = date.split('-')[1]
            else:
                month = ''
            bib_entry = f"""@inproceedings{{{biblStruct.get('xml:id')},
    title = {{{title}}},
    author = {{{author_list}}},
    booktitle = {{{booktitle}}},
    month = {{{month}}},
    year = {{{date.split('-')[0] if date else ''}}},
    address = {{{address}}},
    publisher = {{{publisher}}},
    doi = {{{doi}}},
    pages = {{{page_range}}}
}}\n"""
            # Write to file
            bibfile.write(bib_entry)

# Example usage
parse_xml_to_bib('pdfs/2020.acl-main.648.grobid.tei.xml')