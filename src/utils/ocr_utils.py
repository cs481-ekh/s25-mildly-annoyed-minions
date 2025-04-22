import re
import csv

columns = [
    "year",
    "code",
    "title",
    "street",
    "city",
    "state",
    "zip",
    "phone",
    "tag",
    "staff",
    "doctorates",
    "numTechsAndAuxs",
    "fields",
    "note",
    "leftover",
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


def parse_entry(entry, year, parent_code=None, parent_title=None):
    lines = [line.strip() for line in entry.split("\n") if line.strip()]
    row = make_dict(year)

    # Pointer entry
    if len(lines) == 2 and not re.match(r"^[A-Z.]*\d+", lines[0]):
        row["title"] = lines[0]
        row["note"] = lines[1]
        return row, parent_code, parent_title

    # Transform from multi-line into single-line
    entry_str = re.sub(r"(?<=[A-Za-z])-\s*\n\s*(?=[A-Za-z])", "", entry)
    entry_str = re.sub(r"(?<=\d)-\s*\n\s*(?=\d)", "-", entry_str)
    entry_str = re.sub(r"\s*\n\s*", " ", entry_str)
    entry_str = entry_str.replace("\t", "")
    entry_str = entry_str.replace(",*", ",")
    entry_str = entry_str.replace(",  ", ", ")

    # Clean-up irrelevant information that we know we don't need
    entry_str = re.sub(r"FAX:\s*[\d\-\s]+", "", entry_str, flags=re.IGNORECASE)
    entry_str = re.sub(
        r"Telex:\s*[\d\-\s,]+", "", entry_str, flags=re.IGNORECASE
    ).strip()

    # Match on the code
    code_match = re.match(r"^([A-Z.]*\d+)\s+", entry_str)
    if code_match:
        row["code"] = code_match.group(1)
        entry_str = entry_str[code_match.end() :]

    # Match on the tag
    for tag in possible_tags:
        pattern = rf"\(\s*{re.escape(tag)}\s*\)"  # e.g., '(pg)'
        match = re.search(pattern, entry_str, re.IGNORECASE)
        if match:
            row["tag"] = match.group(0).strip().replace("(", "").replace(")", "")
            entry_str = entry_str.replace(match.group(0), "", 1)
            break

    # Match on the title, assumes title = everything up until the street numbers in street address
    match = re.match(r"^(.*?),\s*([0-9].*)$", entry_str)
    if match:
        row["title"] = match.group(1).strip()
        entry_str = match.group(2).strip()

        # Match on the street address, assumes street address is USA based
        match = re.match(
            r"\s*(.*?),\s*([A-Za-z\s]+),\s*([A-Z]{2})\s*([\w\-]{5,10})\.", entry_str
        )
        if match:
            row["street"] = match.group(1).strip()
            row["city"] = match.group(2).strip()
            row["state"] = match.group(3).strip()
            row["zip"] = match.group(4).strip()
            entry_str = entry_str.replace(match.group(0), "", 1)
        else:
            # Check if there's a mailing add
            # Match full address with optional Mailing add
            match = re.match(
                r"\s*(.*?),\s*([A-Za-z\s]+),\s*([A-Z]{2})\s*\(Mailing add:\s*(PO Box \d+),\s*([\w\-]{5,10})\)\.",
                entry_str,
                flags=re.IGNORECASE,
            )
            if match:
                row["street"] = f"{match.group(1).strip()} {match.group(4).strip()}"
                row["city"] = match.group(2).strip()
                row["state"] = match.group(3).strip()
                row["zip"] = match.group(5).strip()
                entry_str = entry_str.replace(match.group(0), "", 1)

    # Match on the phone number
    match = re.search(r"Tel:\s*([\d\-]+)", entry_str)
    if match:
        row["phone"] = match.group(1).strip()
        if entry_str[match.end() + 1] == ";":
            entry_str = f"{entry_str[:match.start()]}{entry_str[match.end() + 2:]}"
        else:
            entry_str = entry_str.replace(match.group(0), "", 1).strip()
    else:
        match = re.search(r"\s*([\d\-]+)", entry_str)
        if match:
            row["phone"] = match.group(1).strip()
            if entry_str[match.end() + 1] == ";":
                entry_str = f"{entry_str[:match.start()]}{entry_str[match.end() + 2:]}"
            else:
                entry_str = entry_str.replace(match.group(0), "", 1).strip()

    # Match on the number of staffs
    staff_match = re.search(r"Professional Staff:\s*(\d+)", entry_str)
    if staff_match:
        row["staff"] = staff_match.group(1)
        entry_str = entry_str.replace(staff_match.group(0), "", 1)

    # Match on the number of doctorates
    doctorates_match = re.search(r"Doctorates:\s*(\d+)", entry_str)
    if doctorates_match:
        row["doctorates"] = doctorates_match.group(1)
        entry_str = entry_str.replace(doctorates_match.group(0), "", 1)

    # Match on the number of techs & auxiliaries
    match = re.search(r"Technicians\s*&\s*Auxiliaries:\s*(\d+)", entry_str)
    if match:
        row["numTechsAndAuxs"] = match.group(1)
        entry_str = entry_str.replace(match.group(0), "", 1)

    # Match on the fields of R&D
    match = re.search(r"Fields of R&D:(.*?)(?=Professional Staff:|$)", entry_str)
    if match:
        row["fields"] = " ".join(match.group(1).strip().split())
        entry_str = entry_str.replace(match.group(0), "", 1)

    # Fill the note column with everything not parsed by the parser
    row["leftover"] = entry_str

    return row, parent_code, parent_title


def make_dict(year):
    d = dict()
    for key in columns:
        d[key] = "" if key != "year" else year

    return d


def parse_file_to_csv(content, year, output_path):
    # Remove header
    content = re.sub(r"^\d+\s+.*?\n", "", content)

    entries = re.split(r"\n\s*\n", content)
    rows = []
    parent_code = None
    parent_title = None

    i = 0
    while i < len(entries):
        entry = entries[i]

        # Attempt to merge non-entries together for cleaner parsing
        while True:
            if not i < len(entries) - 1:
                break

            next_entry = entries[i + 1]

            ne_lines = next_entry.split("\n")
            if len(ne_lines) <= 2:
                break

            code_match = re.match(r"^([A-Z.]*\d+)\s+", ne_lines[0])
            if (
                not code_match
            ):  # If we fail to match a code, append to current entry, otherwise break and parse
                entry += next_entry
                i += 1
            else:
                break

        print(entry + "\n" * 2)

        if entry.strip():
            row, parent_code, parent_title = parse_entry(
                entry, year, parent_code, parent_title
            )
            rows.append(row)

        i += 1

    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
