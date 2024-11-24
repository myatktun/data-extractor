import os
import re

MD_DIR = f"{os.environ['HOME']}/Documents/Vimwiki"
SECTION_HEADER_PREFIX = "## "


def generate_index_list():
    index_list = []

    for path, _, files in os.walk(MD_DIR):
        if path == MD_DIR:
            continue

        for file_name in files:
            if file_name.endswith(".md"):
                file = os.path.join(path, file_name)
                index_content = os.path.relpath(file, start=MD_DIR)
                index_content = index_content.rsplit('.', maxsplit=1)[0]
                index_list.append(index_content)

    index_list.sort(key=lambda index: index.split('/')[1])

    return index_list


def process_index_rst():
    index_file_template = """
Notes
=====

.. toctree::
   :maxdepth: 1
   :caption: Contents:

"""

    index_list = generate_index_list()

    with open(f"{MD_DIR}/index.rst", "w") as f:
        f.write(index_file_template)
        for index in index_list:
            f.write("   " + index + '\n')


def convert_md_to_rst():
    process_md(f"{MD_DIR}/Linux/Linux.md")

    for path, _, files in os.walk(MD_DIR):
        if path == MD_DIR:
            continue

        for file_name in files:
            if file_name.endswith(".md"):
                file = os.path.join(path, file_name)
                process_md(file)


def process_md(file):
    header_lines_to_write, section_headers = extract_header_data(file)

    if header_lines_to_write is None:
        print("No lines to write")
        return

    write_rst(file, header_lines_to_write, section_headers)


def extract_header_data(file_path):
    # [header_overline, header_underline]
    header_lines_to_write = []

    section_headers = []

    with open(file_path, "r") as f:
        for line_num, line in enumerate(f):
            if line.startswith(SECTION_HEADER_PREFIX):
                header_lines_to_write.append(line_num - 1)
                header_lines_to_write.append(line_num + 1)
                section_headers.append(line.split(' ', maxsplit=1)[1].strip())

    return header_lines_to_write, section_headers


def write_rst(md_file, header_lines_to_write, section_headers):
    content_regex = r"\[(.*?)\]"
    main_content_prefix = r"^\d+.*$"
    section_content_prefix = "* ["
    section_sub_header_prefix = "* **"
    back_to_top_prefix = "##### "

    rst_file = os.path.splitext(md_file)[0] + '.rst'

    with open(md_file, "r") as original, open(rst_file, "w+") as temp:

        line_idx = 0
        section_header_idx = 0
        main_content_num = 1

        for line_num, line in enumerate(original):
            # main header
            if line_num == 0:
                main_header = line.split(' ', maxsplit=1)[1].strip()
                line = main_header + '\n' + \
                    generate_section_line("=", len(main_header)) + '\n'

            # main content
            if re.match(main_content_prefix, line):
                match = re.search(content_regex, line)
                if match is not None:
                    line = f"{main_content_num}. `{match.group(1)}`_\n"
                    main_content_num += 1

            # remove '## ' from section header
            if line.startswith(SECTION_HEADER_PREFIX):
                line = section_headers[section_header_idx] + '\n'

            # section line
            if line_idx < len(header_lines_to_write) and \
                    line_num == header_lines_to_write[line_idx]:

                section_header_len = len(section_headers[section_header_idx])
                section_line = generate_section_line("=", section_header_len)

                # line_idx, Even: overline Odd: underline
                if line_idx % 2 == 0:
                    temp.write("\n" + section_line)
                else:
                    temp.write(section_line + "\n")
                    section_header_idx += 1

                line_idx += 1

            # section sub header
            if line.startswith(section_sub_header_prefix):
                line = generate_section_sub_header(line)

            # section content
            if line.startswith(section_content_prefix):
                match = re.findall(content_regex, line)
                line = generate_section_content(match)

            # process each bullet point line, avoid section content line
            if not re.match(r"^\*\s`.*`_", line) and \
                    re.match(r"^\s*(?:[-*>`])\s*", line):
                line = process_bullet_line(line)

            # "back to top"
            if line.startswith(back_to_top_prefix):
                line = "`back to top <#deep-learning>`_\n"

            temp.write(line)


def process_bullet_line(line):
    # change starting '-' and '>+' to '*', '>' to whitespace
    # add extra backticks if line contains word with backticks
    def replace(m: re.Match[str]):
        if m.group(2):  # - or >+ or >
            if m.group(2) == ">":
                return f"{m.group(1)}  "
            return f"{m.group(1)}* "
        elif m.group(4):  # backticks
            return f"``{m.group(4)}``"

        return m.group(0)

    line = re.sub(r"^(\s*)(-|\>\+|\>)\s*|(>\+)|`([^`]*)`", replace, line)

    return line


def generate_section_line(format_str, length):
    return format_str * length


def generate_section_sub_header(line):
    '''
    Format:
    Section Sub Header
    ------------------
    '''
    section_sub_header_regex = r"\*\*(.*?)\*\*"

    match = re.search(section_sub_header_regex, line)
    if match is not None:
        header = match.group(1)
        line = '\n' + header + '\n' + generate_section_line('-', len(header)) \
            + '\n'

    return line


def generate_section_content(content_list):
    '''
    Format:
    * `content1`_ , `content2`_
    '''
    line = "* "
    idx = 0

    while idx < len(content_list):
        line += f"`{content_list[idx]}`_"
        if idx != len(content_list) - 1:
            line += ", "
        idx += 1

    line += '\n'
    return line


def main():
    convert_md_to_rst()
    process_index_rst()


main()
