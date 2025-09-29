import re
import csv
import os


def load_local_licenses(directory='text'):
    """
    Loads license texts from the .txt files in the SPDX repository's 'text' folder.
    """
    print(f"📁 Loading local license files from the '{directory}/' directory...")
    licenses_data = []

    if not os.path.isdir(directory):
        print(f"❌ Error: Directory '{directory}' not found.")
        print("Please make sure this script is inside the 'license-list-data' folder.")
        return None

    for filename in os.listdir(directory):
        if filename.endswith('.txt'):
            # Use the filename (without .txt) as the license SPDX ID
            license_id = os.path.splitext(filename)[0]
            file_path = os.path.join(directory, filename)

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    license_text = f.read()
                    licenses_data.append({
                        'licenseId': license_id,
                        'licenseText': license_text
                    })
            except IOError as e:
                print(f"⚠️ Could not read file {filename}: {e}")

    if not licenses_data:
        print("❌ No license files found. Ensure the 'text' directory is not empty.")
        return None

    print(f"✅ Loaded {len(licenses_data)} local licenses.\n")
    return licenses_data


def sanitize_for_foldername(term):
    """
    Removes characters that are invalid for folder names and limits length.
    """
    sanitized = re.sub(r'[<>:"/\\|?*]', '', term)
    return sanitized[:100].strip()


def search_and_save(licenses_data, search_term, csv_writer):
    """
    Searches for a term/phrase and writes any matches to the provided CSV writer.
    Returns the total number of matches found.
    """
    print(f"🔎 Searching for '{search_term}' and preparing CSV report...")
    found_count = 0
    search_term = search_term.strip()

    for license_info in licenses_data:
        license_id = license_info['licenseId']
        license_text = license_info['licenseText']

        paragraphs = re.split(r'\n\s*\n', license_text)

        for i, para in enumerate(paragraphs):
            clean_para = para.strip()
            if not clean_para:
                continue

            if re.search(search_term, clean_para, re.IGNORECASE):
                found_count += 1

                prev_para = paragraphs[i - 1].strip() if i > 0 else "N/A"
                next_para = paragraphs[i + 1].strip() if i < len(paragraphs) - 1 else "N/A"

                csv_writer.writerow([license_id, prev_para, clean_para, next_para])

    return found_count


def main():
    """
    Main function to run the license searcher program on local files.
    """
    license_data = load_local_licenses()

    if license_data:
        try:
            while True:
                term = input("Enter the word or phrase to search for (or type 'exit' to quit): ")
                if term.lower() == 'exit':
                    break
                if not term.strip():
                    print("⚠️ Please enter a valid search term.")
                    continue

                folder_name = sanitize_for_foldername(term)
                # Save the results folder outside the repository folder to keep it clean
                output_path = os.path.join('..', folder_name)
                os.makedirs(output_path, exist_ok=True)

                file_path = os.path.join(output_path, 'results.csv')

                try:
                    with open(file_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(['License ID', 'Paragraph Before', 'Paragraph with Hit', 'Paragraph After'])

                        found_count = search_and_save(license_data, term, writer)

                    if found_count > 0:
                        full_path = os.path.abspath(file_path)
                        print(f"\n🎉 Search complete. Found {found_count} matches.")
                        print(f"Results saved to: {full_path}")
                    else:
                        print(f"\n🤷 No results found for '{term}'.")
                        os.rmdir(output_path)  # Clean up empty folder

                except IOError as e:
                    print(f"❌ Error writing to file: {e}")

        except KeyboardInterrupt:
            print("\n👋 Exiting program.")


if __name__ == '__main__':
    main()
