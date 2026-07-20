import asyncio
from crawl4ai import AsyncWebCrawler
import re
import json
import argparse
import os

def remove_menus(text):
    cleaned = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    return cleaned

def parse_PP(text, start, end):
    match = re.search(
        rf"{start}(.*?){end}",
        text,
        re.DOTALL
    )

    # print(f"1ST SECTION: {match.group(0)[:200]}")
    # print(f"2ND SECTION: {match.group(1)[:200]}")

    if match:
        policy = match.group(1).strip()

        return policy
    
    return text

def get_headings_2(text):
    # tries the first pattern
    pattern1 = r"^\s*(?:\*\s*)?(#+)\s+(.*)$"

    matches = []

    for m in re.finditer(pattern1, text, re.MULTILINE):
        matches.append({
            "title": m.group(1).strip("*_ "),
            "start": m.start(),
            "end": m.end()
        })

    if matches:
        return matches

    # tries the second pattern
    pattern2 = r"^\*\*(?!\d)(.*?)\*\*$"

    for m in re.finditer(pattern2, text, re.MULTILINE):
        matches.append({
            "title": m.group(1).strip("*_ "),
            "start": m.start(),
            "end": m.end()
        })

    return matches

    #return list(re.finditer(pattern2, text, re.MULTILINE))

def get_headings(text):
    pattern = r"^\s*(?:\*\s*)?(#+)\s+(.*)$"
    headings = list(re.finditer(pattern, text, re.MULTILINE))
    if not headings:
        headings = re.findall( r"^\*\*(?!\d)(.*?)\*\*$", text, re.MULTILINE )
    return headings

def make_sections(text, heading_matches):
    sections = {}
    for i, match in enumerate(heading_matches):
        title = match.group(2).strip()
        start = match.end()
        end = (
            heading_matches[i + 1].start()
            if i + 1 < len(heading_matches)
            else len(text) )
        sections[title] = text[start:end].strip()
    return sections


def make_sections_2(text, headings):
    sections = {}

    for i, h in enumerate(headings):
        title = h["title"]

        start = h["end"]

        end = (
            headings[i + 1]["start"]
            if i + 1 < len(headings)
            else len(text)
        )

        sections[title] = text[start:end].strip()

    return sections

def make_sections(text, heading_matches):
    sections = {}

    for i, match in enumerate(heading_matches):
        print(f"MATCH: {match}")
        title = match.group(2).strip()

        start = match.end()

        end = (
            heading_matches[i + 1].start()
            if i + 1 < len(heading_matches)
            else len(text)
        )

        sections[title] = text[start:end].strip()

    if sections:
        return sections

    #sections = {}

    for i, h in enumerate(headings):
        title = h["title"]

        start = h["end"]

        end = (
            headings[i + 1]["start"]
            if i + 1 < len(headings)
            else len(text)
        )

        sections[title] = text[start:end].strip()

    return sections

def load_config(json_file):
    with open(json_file, "r", encoding="utf-8") as j:
        config = json.load(j)

    return config

async def extract_text(source_name, url):

    # makes the output file path
    output_file = f"{source_name.replace(' ', '_')}_raw_text.txt"

    # create output directory if it doesn't exist
    #os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Source: {source_name}\nURL: {url}\n\n")

        async with AsyncWebCrawler() as crawler:
            # Run the crawler on a URL
            result = await crawler.arun(url)

            # Print the extracted content
            #print(result.markdown)
            f.write(result.markdown)


if __name__ == "__main__":
    # sources = {
    #     "Apple": "https://www.apple.com/legal/privacy/en-ww/",
    #     "Cisco": "https://www.cisco.com/c/en/us/about/legal/privacy-full.html",

    # }
    # source_name = "Cisco"
    # url = "https://www.cisco.com/c/en/us/about/legal/privacy-full.html"

    # source_name = "Smartthings"
    # url = "https://eula.samsungiotcloud.com/legal/us/en/pps.html"

    source_name = "Apple"
    url = "https://www.apple.com/legal/privacy/en-ww/"
    #asyncio.run(extract_text(source_name, url))

    #exit()


    parser = argparse.ArgumentParser(description='Scrape e-commerce websites')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--apple', action='store_true', help='Use Apple config')
    group.add_argument('--cisco', action='store_true', help='Use Cisco config')
    group.add_argument('--smartthings', action='store_true', help='Use Smartthings config')
    # group.add_argument('--target', action='store_true', help='Use Target config')
    # group.add_argument('--walmart', action='store_true', help='Use Walmart config')

    args = parser.parse_args()

    if args.apple:
        config_name = "apple_PP.json"
    elif args.cisco:
        config_name = "cisco_PP.json"
    elif args.smartthings:
        config_name = "smartthings_PP.json"

    # loads the config
    config = load_config(os.path.join("src", "configs", config_name))

    start_heading = config["start_pattern"]
    end_heading = config["end_pattern"]
    

    with open(f"{source_name}_raw_text.txt", "r", encoding="utf-8") as f:
        text = f.read()

    text = remove_menus(text)
    print("AFTER REMOVING MENUS")
    print(text)
    text = parse_PP(text, start_heading, end_heading)
    print("AFTER PARSING PP")
    print(text)

    # tries the first parsing method
    try:
        headings = get_headings(text)
        sections = make_sections(text, headings)
    except:
        headings = get_headings_2(text)
        sections = make_sections_2(text, headings)

    # headings = get_headings(text)
    # print(f"HEADINGS: {headings}")
    # print(type(headings))

    # sections = make_sections(text, headings)

    print(sections)

    with open(f"{source_name}_parsed.json", "w", encoding="utf-8") as j:
        json.dump(sections, j, indent=4)

    with open(f"{source_name}_parsed.txt", "w", encoding="utf-8") as f:
        f.write(text)