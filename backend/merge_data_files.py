import json
import logging
import os
import shutil

import yaml

script_dir = os.path.dirname(__file__)
output_folder = os.path.join(script_dir, "..", "frontend", "public", "metadata")
data_dir = os.path.join(script_dir, "content", "data")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def log_message(message):
    logging.info(message)


def parse_yaml(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


SUMMARY_DATA_KEY_MAPPINGS = {
    "bioconda": {
        "name": ("package", "name"),
        "version": ("package", "version"),
        "license": ("about", "license"),
        "summary": ("about", "summary"),
    },
    "biotools": {
        "license": ("license",),
        "summary": ("description",),
        "addition_date": ("additionDate",),
        "last_update_date": ("lastUpdate",),
        "version": ("version",),
    },
    "bioschemas": {
        "name": ("sc:name",),
        "license": ("sc:license",),
        "version": ("sc:softwareVersion",),
    },
    "galaxy": {
        "summary": ("Description",),
        "edam_topics": ("EDAM_topics",),
    },
    "biocontainers": {
        "name": ("name",),
        "license": ("license",),
        "summary": ("description",),
    },
}

PAGE_DATA_KEY_MAPPINGS = {
    "bioconda": {
        "name": ("package", "name"),
        "version": ("package", "version"),
        "home": ("about", "home"),
        "documentation": ("about", "doc_url"),
        "license": ("about", "license"),
        "summary": ("about", "summary"),
        "identifiers": ("extra", "identifiers"),
    },
    "biocontainers": {
        "name": ("name",),
        "identifiers": ("identifiers",),
        "license": ("license",),
        "summary": ("description",),
    },
    "biotools": {
        "id": ("biotoolsID",),
        "home": ("homepage",),
        "license": ("license",),
        "summary": ("description",),
        "addition_date": ("additionDate",),
        "last_update_date": ("lastUpdate",),
        "tool_type": ("toolType",),
        "version": ("version",),
    },
    "bioschemas": {
        "name": ("sc:name",),
        "home": ("@id",),
        "license": ("sc:license",),
        "version": ("sc:softwareVersion",),
        "summary": ("sc:description",),
        "tool_type": ("@type",),
    },
    "galaxy": {
        "first_commit": ("Suite_first_commit_date",),
        "conda_name": ("Suite_conda_package",),
        "conda_version": ("Latest_suite_conda_package_version",),
        "summary": ("Description",),
        "edam_operations": ("EDAM_operations",),
        "edam_topics": ("EDAM_topics",),
        "toolshed_categories": ("ToolShed_categories",),
        "toolshed_id": ("Suite_ID",),
        "users_5_years": ("Suite_users_(last_5_years)_on_main_servers",),
        "users_all_time": ("Suite_users_on_main_servers",),
        "usage_5_years": ("Suite_runs_(last_5_years)_on_main_servers",),
        "usage_all_time": ("Suite_runs_on_main_servers",),
        "bio_tools_summary": ("bio.tool_description",),
        "bio_tools_ids": ("bio.tool_ID",),
        "bio_tools_name": ("bio.tool_name",),
        "related_tutorials": ("Related_Tutorials",),
        "related_workflows": ("Related_Workflows",),
        "tool_ids": ("Tool_IDs",),
        "no_of_tools": {
            "eu": ("Number_of_tools_on_UseGalaxy.eu",),
            "org": ("Number_of_tools_on_UseGalaxy.org_(Main)",),
            "au": ("Number_of_tools_on_UseGalaxy.org.au",),
            "be": ("Number_of_tools_on_UseGalaxy.be",),
            "cz": ("Number_of_tools_on_UseGalaxy.cz",),
            "fr": ("Number_of_tools_on_UseGalaxy.fr",),
            "no": ("Number_of_tools_on_UseGalaxy.no",),
        },
    },
}


def extract_data(tool_type, data, key_mappings):
    def traverse_keys(d, *keys):
        for key in keys:
            if isinstance(d, list):
                d = d[0] if d else None
            if isinstance(d, dict):
                d = d.get(key)
            else:
                return None
        return d

    def extract(d, mappings):
        return {
            k: extract(d, v) if isinstance(v, dict) else traverse_keys(d, *v) or None
            for k, v in mappings.items()
        }

    mappings = key_mappings.get(tool_type, {})
    if tool_type == "bioschemas":
        graph = data.get("@graph", [])
        software_data = next(
            (
                entry
                for entry in graph
                if entry.get("@type") == "sc:SoftwareApplication"
            ),
            None,
        )
        return {tool_type: extract(software_data, mappings)} if software_data else {}
    else:
        return {tool_type: extract(data, mappings)}


def process_files_in_folder(folder_path):
    folder_name = os.path.basename(folder_path)
    log_message(f"Extracting data for: {folder_name}")

    file_patterns = [
        (f"bioconda_{folder_name}.yaml", "bioconda"),
        (f"{folder_name}.biocontainers.yaml", "biocontainers"),
        (f"{folder_name}.biotools.json", "biotools"),
        (f"{folder_name}.bioschemas.jsonld", "bioschemas"),
        (f"{folder_name}.galaxy.json", "galaxy"),
    ]

    contents, fetched_metadata, extracted_page_metadata = set(), {}, {}

    if not any(
        os.path.exists(os.path.join(folder_path, file_name))
        for file_name, _ in file_patterns
    ):
        return {}, {}

    for file_name, tool_type in file_patterns:
        file_path = os.path.join(folder_path, file_name)
        if not os.path.exists(file_path):
            continue

        contents.add(tool_type)

        ext = os.path.splitext(file_path)[1]
        data = (
            parse_yaml(file_path)
            if ext in [".yaml", ".yml"]
            else parse_json(file_path) if ext in [".json", ".jsonld"] else None
        )
        if data is None:
            continue

        extracted_data = extract_data(tool_type, data, SUMMARY_DATA_KEY_MAPPINGS)
        fetched_metadata.update({k: v for k, v in extracted_data.items() if v})

        page_data = extract_data(tool_type, data, PAGE_DATA_KEY_MAPPINGS)
        extracted_page_metadata.update({k: v for k, v in page_data.items() if v})

    metadata = {
        "tool_name": folder_name,
        "contents": list(contents),
        "fetched_metadata": fetched_metadata,
    }

    page_metadata = {
        "tool_name": folder_name,
        "contents": list(contents),
        "page_metadata": extracted_page_metadata,
    }

    return metadata, page_metadata


def main():
    combined_metadata = []

    for root, _, _ in os.walk(data_dir):
        if root != data_dir:
            metadata, page_metadata = process_files_in_folder(root)
            if not metadata or not page_metadata:
                continue
            combined_metadata.append(metadata)
            save_metadata(f"tools/{page_metadata['tool_name']}.json", page_metadata)

    save_metadata("combined_metadata.json", combined_metadata)


def save_metadata(output_file, metadata):
    output_combined_file = os.path.join(output_folder, output_file)
    os.makedirs(os.path.dirname(output_combined_file), exist_ok=True)
    with open(output_combined_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, separators=(",", ":"))


if __name__ == "__main__":
    log_message("Starting metadata extraction and merging process")
    shutil.rmtree(output_folder, ignore_errors=True)
    log_message(f"Fetching metadata from the directory {data_dir}")
    main()
    log_message(f"Metadata combined and saved")
