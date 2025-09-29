import sys
import subprocess

# --- Dependency Check ---
# This block checks if the 'requests' library is installed.
# If not, it attempts to install it using pip.
try:
    import requests
except ImportError:
    print("The 'requests' library is not installed. Attempting to install it now...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        import requests
    except Exception as e:
        print(f"Error: Failed to install the 'requests' library.", file=sys.stderr)
        print(f"Please install it manually by running: pip install requests", file=sys.stderr)
        print(f"Original error: {e}", file=sys.stderr)
        sys.exit(1)
# --- End of Dependency Check ---

import csv


def get_all_repos(account_name):
    """
    Fetches all public repositories for a given GitHub user or organization.
    It handles pagination to retrieve all results.
    """
    repos = []
    # First, try the organization API endpoint
    api_url = f"https://api.github.com/orgs/{account_name}/repos"
    print(f"Attempting to fetch org repos for '{account_name}'...")
    response = requests.get(api_url, params={'per_page': 100})

    # If the organization endpoint fails (e.g., it's a user), try the user endpoint
    if response.status_code != 200:
        print(f"Could not find organization '{account_name}', trying as a user...")
        api_url = f"https://api.github.com/users/{account_name}/repos"
        response = requests.get(api_url, params={'per_page': 100})
        # If this also fails, the account may not exist or there's another issue
        if response.status_code != 200:
            print(f"Error: Could not fetch repositories for '{account_name}'. "
                  f"Status code: {response.status_code}", file=sys.stderr)
            print(f"Response: {response.text}", file=sys.stderr)
            return None

    # Process the first page of results
    repos.extend(response.json())

    # Handle paginated results
    while 'next' in response.links:
        next_url = response.links['next']['url']
        print(f"Fetching next page for '{account_name}': {next_url}")
        response = requests.get(next_url)
        if response.status_code == 200:
            repos.extend(response.json())
        else:
            print(f"Error fetching page {next_url}. Status code: {response.status_code}", file=sys.stderr)
            break

    return repos


def extract_license_info(repos, account_name):
    """
    Extracts the account name, repository name, and license from a list of repository data.
    """
    license_data = []
    if not repos:
        return license_data

    for repo in repos:
        repo_name = repo.get('name', 'N/A')
        license_info = repo.get('license')

        if license_info and 'name' in license_info:
            license_name = license_info['name']
        else:
            license_name = "Not specified"

        license_data.append([account_name, repo_name, license_name])

    return license_data


def save_to_csv(data, filename):
    """
    Saves the provided data to a CSV file.
    """
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            # Write the header
            writer.writerow(['Account', 'Repository', 'License'])
            # Write the data rows
            writer.writerows(data)
        print(f"\nSuccessfully saved data to {filename}")
    except IOError as e:
        print(f"Error: Could not write to file {filename}. Reason: {e}", file=sys.stderr)


def main():
    """
    Main function to run the script.
    """
    user_input = input("Enter GitHub usernames or org names, separated by commas (e.g., 'actgov,google,torvalds'): ")
    if not user_input:
        print("Error: No account names provided.", file=sys.stderr)
        return

    # Split the input string by commas and strip any whitespace from each name
    github_accounts = [name.strip() for name in user_input.split(',')]
    all_license_data = []

    for account in github_accounts:
        if not account:
            continue  # Skip empty strings that might result from trailing commas

        print(f"\n--- Processing '{account}' ---")
        all_repos = get_all_repos(account)

        if all_repos:
            print(f"Found {len(all_repos)} repositories for '{account}'. Extracting license info...")
            license_list = extract_license_info(all_repos, account)
            all_license_data.extend(license_list)
        else:
            print(f"No repositories found or could not access '{account}'.")

    if all_license_data:
        # Sort the data by Account (column 0), then by Repository (column 1)
        all_license_data.sort(key=lambda x: (x[0].lower(), x[1].lower()))

        output_filename = "github_licenses_report.csv"
        save_to_csv(all_license_data, output_filename)
    else:
        print("\nNo data was collected from any of the provided accounts.")


if __name__ == "__main__":
    main()