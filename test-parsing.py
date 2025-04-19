import csv
import re

columns = [
    "year", "code", "title", "street", "city", "state", "zip", "phone", "tag",
    "staff", "doctorates", "numTechsAndAuxs", "fields", "note", "leftover"
]

possible_tags = [
    "p",
    "g",
    "i",
    "c",
    "pg",
    "pi",
    "pc",
    "gp",
    "gi",
    "gc",
    "ip",
    "ig",
    "ic",
    "cp",
    "cg",
    "ci",
    "pgi",
    "pgc",
    "pig",
    "pic",
    "pcg",
    "pci",
    "gpi",
    "gpc",
    "gip",
    "gic",
    "gcp",
    "gci",
    "ipg",
    "ipc",
    "igp",
    "igc",
    "icp",
    "icg",
    "cpg",
    "cpi",
    "cgp",
    "cgi",
    "cip",
    "cig",
    "pgic",
    "pgci",
    "pigc",
    "picg",
    "pcgi",
    "pcig",
    "gpic",
    "gpci",
    "gipc",
    "gicp",
    "gcpi",
    "gcip",
    "ipgc",
    "ipcg",
    "igpc",
    "igcp",
    "icpg",
    "icgp",
    "cpgi",
    "cpig",
    "cgpi",
    "cgip",
    "cipg",
    "cigp",
]

def parse_entry(entry, parent_code=None, parent_title=None):
    lines = [line.strip() for line in entry.split('\n') if line.strip()]
    row = dict.fromkeys(columns, "")

    # Pointer entry
    if len(lines) == 2 and not re.match(r'^[A-Z.]*\d+', lines[0]):
        row["title"] = lines[0]
        row["note"] = lines[1]
        return row, parent_code, parent_title

    header = lines[0]
    body = "\n".join(lines[1:])
    code_match = re.match(r'^([A-Z.]?\s?-?\d+)\s+(.*)', header)

    if code_match:
        code_raw = code_match.group(1).replace(" ", "").replace("-", "")
        title_and_address = code_match.group(2).strip()

        is_subentry = re.match(r'^(\d+|\.?\d+)$', code_raw)

        # Determine code
        if is_subentry and parent_code:
            full_code = f"{parent_code}.{code_raw.lstrip('.')}"
        else:
            full_code = code_raw
            parent_code = full_code  # set new parent

        row["code"] = full_code

        # Parse title and address
        title_match = re.match(r'^([^,]+),\s*(.*)', title_and_address)
        if title_match:
            this_title = title_match.group(1).strip()
            if is_subentry and parent_title:
                row["title"] = f"{parent_title}{this_title}"
            else:
                row["title"] = this_title
                parent_title = this_title  # set new parent title

            address_part = title_match.group(2)
            address_match = re.match(r'(.*?),\s*([A-Z]{2})\s*(\d{5}(?:-\d{4})?)?', address_part)
            if address_match:
                row["street"] = address_match.group(1).strip()
                row["state"] = address_match.group(2)
                row["zip"] = address_match.group(3) or ""
                city_match = re.search(r'([^,]+),', address_part)
                row["city"] = city_match.group(1).strip() if city_match else ""

        # Tag (optional)
        tag_match = re.search(r',\s*\(([^)]+)\)', header)
        if tag_match:
            row["tag"] = tag_match.group(1)

    # Phone
    phone_match = re.search(r'Tel:\s*([\d\-]+)', body)
    if phone_match:
        row["phone"] = phone_match.group(1)

    # Staff and doctorates
    staff_match = re.search(r'Professional Staff:\s*(\d+)\s*\(Doctorates:\s*(\d+)', body)
    if staff_match:
        row["staff"] = staff_match.group(1)
        row["doctorates"] = staff_match.group(2)

    # Techs
    techs_match = re.search(r'Technicians\s*&\s*Auxiliaries:\s*(\d+)', body)
    if techs_match:
        row["numTechsAndAuxs"] = techs_match.group(1)

    # Fields
    fields_match = re.search(r'Fields of R&D:(.*?)(?:$|\n[A-Z])', body, re.DOTALL)
    if fields_match:
        row["fields"] = ' '.join(fields_match.group(1).split())

    # Remaining body becomes note
    row["note"] = ' '.join(body.split())

    return row, parent_code, parent_title

def make_dict():
    d = dict()
    for key in columns:
        d[key] = "" if key != "year" else "1991"

    return d

def custom_parser(text):
    # Create a list of blocks
    blocks = text.split("\n\n")

    # First block is the page number which we don't need
    blocks = blocks[1:]

    # Construct list of entries
    entries = [make_dict() for _ in range(len(blocks))]

    # Parse each block
    for i, block in enumerate(blocks):
        lines = block.split("\n")

        # Only the redirects are two lines long (from what I've seen)
        if len(lines) == 2:
            entries[i]["title"] = lines[0]
            entries[i]["note"] = lines[1]
            continue

        # Transform from multi-line into single-line
        entry_str = re.sub(r'(?<=[A-Za-z])-\s*\n\s*(?=[A-Za-z])', '', block)
        entry_str = re.sub(r'(?<=\d)-\s*\n\s*(?=\d)', '-', entry_str)
        entry_str = re.sub(r'\s*\n\s*', ' ', entry_str)
        entry_str = entry_str.replace('\t', '')
        entry_str = entry_str.replace(',*', ',')
        entry_str = entry_str.replace(',  ', ', ')

        print(entry_str + "\n")

        # Clean-up irrelevant information that we know we don't need
        entry_str = re.sub(r'FAX:\s*[\d\-\s]+', '', entry_str, flags=re.IGNORECASE)
        entry_str = re.sub(r'Telex:\s*[\d\-\s,]+', '', entry_str, flags=re.IGNORECASE).strip()

        # Match on the code
        code_match = re.match(r'^([A-Z.]*\d+)\s+', entry_str)
        if code_match:
            entries[i]["code"] = code_match.group(1)
            entry_str = entry_str[code_match.end():]

        # Match on the tag
        for tag in possible_tags:
            pattern = rf'\(\s*{re.escape(tag)}\s*\)'  # e.g., '(pg)'
            match = re.search(pattern, entry_str, re.IGNORECASE)
            if match:
                entries[i]['tag'] = match.group(0).strip().replace("(", "").replace(")", "")
                entry_str = entry_str.replace(match.group(0), '', 1)
                break

        # Match on the title, assumes title = everything up until the street numbers in street address
        match = re.match(r'^(.*?),\s*([0-9].*)$', entry_str)
        if match:
            entries[i]['title'] = match.group(1).strip()
            entry_str = match.group(2).strip()

        # Match on the street address, assumes street address is USA based
        match = re.match(r'\s*(.*?),\s*([A-Za-z\s]+),\s*([A-Z]{2})\s*([\w\-]{5,10})\.', entry_str)
        if match:
            entries[i]['street'] = match.group(1).strip()
            entries[i]['city'] = match.group(2).strip()
            entries[i]['state'] = match.group(3).strip()
            entries[i]['zip'] = match.group(4).strip()
            entry_str = entry_str.replace(match.group(0), '', 1)
        else:
            # Check if there's a mailing add
            # Match full address with optional Mailing add
            match = re.match(
                r'\s*(.*?),\s*([A-Za-z\s]+),\s*([A-Z]{2})\s*\(Mailing add:\s*(PO Box \d+),\s*([\w\-]{5,10})\)\.',
                entry_str,
                flags=re.IGNORECASE
            )
            if match:
                entries[i]['street'] = f"{match.group(1).strip()} {match.group(4).strip()}"
                entries[i]['city'] = match.group(2).strip()
                entries[i]['state'] = match.group(3).strip()
                entries[i]['zip'] = match.group(5).strip()
                entry_str = entry_str.replace(match.group(0), '', 1)

        # Match on the phone number
        match = re.search(r'Tel:\s*([\d\-]+)', entry_str)
        if match:
            entries[i]['phone'] = match.group(1).strip()
            if entry_str[match.end() + 1] == ";":
                entry_str = f"{entry_str[:match.start()]}{entry_str[match.end() + 2:]}"
            else:
                entry_str = entry_str.replace(match.group(0), '', 1).strip()

        # Match on the number of staffs
        staff_match = re.search(r'Professional Staff:\s*(\d+)', entry_str)
        if staff_match:
            entries[i]['staff'] = staff_match.group(1)
            entry_str = entry_str.replace(staff_match.group(0), '', 1)

        # Match on the number of doctorates
        doctorates_match = re.search(r'Doctorates:\s*(\d+)', entry_str)
        if doctorates_match:
            entries[i]['doctorates'] = doctorates_match.group(1)
            entry_str = entry_str.replace(doctorates_match.group(0), '', 1)

        # Match on the number of techs & auxiliaries
        match = re.search(r'Technicians\s*&\s*Auxiliaries:\s*(\d+)', entry_str)
        if match:
            entries[i]['numTechsAndAuxs'] = match.group(1)
            entry_str = entry_str.replace(match.group(0), '', 1)

        # Match on the fields of R&D
        match = re.search(r'Fields of R&D:(.*?)(?=Professional Staff:|$)', entry_str)
        if match:
            entries[i]['fields'] = ' '.join(match.group(1).strip().split())
            entry_str = entry_str.replace(match.group(0), '', 1)

        # Fill the note column with everything not parsed by the parser
        entries[i]["leftover"] = entry_str

    return entries


def write_entries(entries):
    with open("parsed_output.csv", "w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(entries)


def parse_file_to_csv(input_path, output_path):
    with open(input_path, "r") as f:
        content = f.read()

    # Remove header
    content = re.sub(r'^\d+\s+.*?\n', '', content)

    entries = re.split(r'\n\s*\n', content)
    rows = []
    parent_code = None
    parent_title = None

    i = 0
    while i < len(entries):
        entry = entries[i]

        # Check if there was a page break between entries
        # If there was, append the next entry to the current entry and
        # increment i by 1 to account for it
        next_entry = None
        if i < len(entries) - 1:
            next_entry = entries[i + 1]

        ne_lines = next_entry.split("\n")
        if len(ne_lines) > 2:
            code_match = re.match(r'^([A-Z.]*\d+)\s+', ne_lines[0])
            if code_match:
                entry += next_entry
                i += 1

        if entry.strip():
            row, parent_code, parent_title = parse_entry(entry, parent_code, parent_title)
            row["year"] = "1991"
            rows.append(row)

        i += 1

    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)



if __name__ == "__main__":
    # Example usage:
    # parse_file_to_csv("text-output.txt", "parsed_output.csv")
    with open("multi-page-test.txt", "r") as f:
        text = f.read()
        entries = custom_parser(text)
        write_entries(entries)
