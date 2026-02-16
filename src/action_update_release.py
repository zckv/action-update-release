import requests

from pathlib import Path
from argparse import ArgumentParser, Namespace


class UpdaterParser:
    """A parser class that uses argparse to handle command-line arguments."""

    def __init__(self) -> None:
        """Initialize the argument parser."""
        self.parser = ArgumentParser(
            description="Update release information with tag, files, token, and project URL."
        )
        self._setup_arguments()

    def _setup_arguments(self) -> None:
        """Set up the command-line arguments."""
        self.parser.add_argument(
            "--tag", type=str, required=True, help="The release tag/version."
        )
        self.parser.add_argument(
            "--files",
            type=str,
            nargs="+",
            required=True,
            help="List of file paths to update.",
        )
        self.parser.add_argument(
            "--token",
            type=str,
            required=True,
            help="Authentication token for API access.",
        )
        self.parser.add_argument(
            "--project",
            type=str,
            required=True,
            help="Project name in the format of '[OWNER]/[REPO]'.",
        )

    def parse(self, args: list[str] | None = None) -> Namespace:
        """
        Parse command-line arguments.

        Args:
            args: Optional list of arguments. If None, uses sys.argv.

        Returns:
            Namespace object containing parsed arguments.
        """
        return self.parser.parse_args(args)


class Updater:
    """A class to manage release updates with tag, files, and authentication token."""

    def __init__(self, args: Namespace) -> None:
        """
        Initialize the Updater with release information.

        Args:
            args: Namespace object containing tag, files, token, and project URL.
        """
        self.tag = args.tag
        self.files = args.files
        self.token = args.token
        self.project = args.project

    def check_if_release_exists(self) -> dict:
        """
        Check if a release exists on GitHub.

        Returns:
            The release information as a dictionary if it exists, otherwise exits the program.

        Raises:
            requests.exceptions.RequestException: If the API request fails.
        """
        url = f"https://api.github.com/repos/{self.project}/releases/tags/{self.tag}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        response = requests.get(url, headers=headers)

        match response.status_code:
            case 404:
                print(f"Release with tag '{self.tag}' does not exist.")
            case 401:
                print("Unauthorized: Invalid authentication token.")
            case 200:
                return response.json()
            case _:
                response.raise_for_status()
        exit(1)

    def upload_asset(self, upload_url: str, path: Path):
        """
        Upload an asset to a release.

        Args:
            upload_url: The URL for uploading assets to the release.
            path: Path object pointing to the file to upload.

        Raises:
            requests.exceptions.RequestException: If the API request fails.
            FileNotFoundError: If the file does not exist.
        """
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        with path.open("rb") as f:
            files = {"file": f}
            response = requests.post(
                f"{upload_url}?name={path.name}", headers=headers, files=files
            )

        match response.status_code:
            case 200:
                return
            case 401:
                print("Unauthorized: Invalid authentication token.")
            case _:
                response.raise_for_status()

        exit(1)

    def delete_asset(self, asset_id: int) -> None:
        """
        Delete an asset from a release.

        Args:
            asset_id: The ID of the asset to delete.

        Raises:
            requests.exceptions.RequestException: If the API request fails.
        """
        url = f"https://api.github.com/repos/{self.project}/releases/assets/{asset_id}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        response = requests.delete(url, headers=headers)

        match response.status_code:
            case 204:
                return
            case 401:
                print("Unauthorized: Invalid authentication token.")
            case _:
                response.raise_for_status()
        exit(1)

    def get_provided_files(self) -> dict[str, Path]:
        """
        Load files from a list of file paths.

        Each value in self.files may be a relative path, absolute path,
        to a file or a directory.

        Returns:
            A dictionary mapping file path strings to their Path objects.

        Raises:
            FileNotFoundError: If no files match the provided patterns or paths.
        """
        loaded_files = {}

        for str_path in self.files:
            path = Path(str_path)
            if path.is_file():
                loaded_files[path.name] = path
                continue
            if path.is_dir():
                for file in path.iterdir():
                    if file.is_file():
                        loaded_files[file.name] = file
                continue
            print(f"Path does not exist: {str_path}")
        return loaded_files

    def __call__(self) -> None:
        """Update the release by checking if it exists, deleting existing assets if necessary, and uploading new assets."""
        if release := self.check_if_release_exists():
            existing_assets: list[dict] = release.get("assets", [])
            upload_url: str = release.get("upload_url", "").split("{")[0]
        else:
            print(f"Release with tag '{self.tag}' could not be parsed.")
            exit(1)

        files = self.get_provided_files()
        toggle = True
        for file_name, path in files.items():
            for asset in existing_assets:
                if asset["name"] == file_name:
                    self.delete_asset(asset["id"])
                    self.upload_asset(upload_url, path)
                    toggle = False
                    break
            if toggle:
                self.upload_asset(upload_url, path)


def main() -> None:
    """Entry point for the script."""
    args = UpdaterParser().parse()
    updater = Updater(args)
    updater()


if __name__ == "__main__":
    main()
