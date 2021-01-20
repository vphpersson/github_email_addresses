from asyncio import gather as asyncio_gather
from dataclasses import dataclass
from itertools import count
from typing import Any
from http import HTTPStatus

from httpx import AsyncClient as HttpxAsyncClient, Response

# The maximum number of results per page for API calls; set by Github.
MAX_NUM_RESULTS_PER_PAGE = 100


@dataclass(frozen=True)
class CommitAuthor:
    name: str
    email_address: str

    def __str__(self) -> str:
        return f'{self.email_address} {self.name}'


@dataclass
class RepositoryInfo:
    name: str
    owner: str
    commit_authors: set[CommitAuthor]


async def _collect_repository_information(
    client: HttpxAsyncClient,
    repository_entries: list[dict[str, Any]],
    repository_information_list: list[RepositoryInfo]
) -> None:
    """
    Collect information about a Github user's repositories.

    The information collected includes the repository's name, its owner, and its commit authors.

    The function is intended to be run concurrently. Repository entries are read from the input list until it is empty.
    The repository information is collected in the other list. Both lists are shared, concurrently.

    :param client: An HTTP client with which to perform requests towards Github's REST API.
    :param repository_entries: A list of repository entries of a user, as returned by Github's API.
    :param repository_information_list: A list onto which information about a repository is appended.
    :return: None
    """

    while True:
        try:
            repository_entry: dict[str, Any] = repository_entries.pop()
        except IndexError:
            break

        branch_names: set[str] = set()
        for page_number in count(start=1):
            branches_entries_response = await client.get(
                url=f'/repos/{repository_entry["full_name"]}/branches',
                params={'per_page': MAX_NUM_RESULTS_PER_PAGE, 'page': page_number}
            )
            branches_entries_response.raise_for_status()

            branch_entries = branches_entries_response.json()
            branch_names.update(branch_entry['name'] for branch_entry in branch_entries)

            if len(branch_entries) < MAX_NUM_RESULTS_PER_PAGE:
                break

        # If the repository is forked, collect only the commits that were made after the forked repository was
        # was created.
        extra_request_parameters: dict[str, Any] = {}
        if repository_entry['fork']:
            extra_request_parameters['since'] = repository_entry['created_at']

        commit_entries: list[dict[str, Any]] = []

        for branch_name in branch_names:
            for page_number in count(start=1):
                commit_entries_response: Response = await client.get(
                    url=f'/repos/{repository_entry["full_name"]}/commits',
                    params={
                        'per_page': MAX_NUM_RESULTS_PER_PAGE,
                        'page': page_number,
                        'sha': branch_name
                    } | extra_request_parameters
                )

                # The repository has no commits.
                if commit_entries_response.status_code == HTTPStatus.CONFLICT:
                    break
                else:
                    commit_entries_response.raise_for_status()

                response_commit_entries: list[dict[str, Any]] = commit_entries_response.json()
                commit_entries.extend(response_commit_entries)

                if len(response_commit_entries) < MAX_NUM_RESULTS_PER_PAGE:
                    break

        repository_information_list.append(
            RepositoryInfo(
                name=repository_entry['name'],
                owner=repository_entry['owner']['login'],
                commit_authors=set(
                    CommitAuthor(
                        name=commit['commit']['author']['name'],
                        email_address=commit['commit']['author']['email']
                    )
                    for commit in commit_entries
                )
            )
        )


async def obtain_github_authors(
    client: HttpxAsyncClient,
    username: str,
    num_max_concurrent: int = 5
) -> set[CommitAuthor]:
    """
    Obtain information about authors from the commit history of a Github user's repositories.

    :param client: An HTTP client with which to request information from Github's API.
    :param username: The username of the Github user whose repositories to scan.
    :param num_max_concurrent: The maximum number of concurrent HTTP requests.
    :return: A set of the commit authors in a Github user's repositories.
    """

    repository_entries: list[dict[str, Any]] = []
    for page_number in count(start=1):
        repository_entries_response: Response = await client.get(
            url=f'/users/{username}/repos',
            params={'per_page': MAX_NUM_RESULTS_PER_PAGE, 'page': page_number}
        )
        repository_entries_response.raise_for_status()

        response_repositories_entries = repository_entries_response.json()
        repository_entries.extend(response_repositories_entries)

        if len(response_repositories_entries) < MAX_NUM_RESULTS_PER_PAGE:
            break

    num_repository_entries = len(repository_entries)
    repository_information_list: list[RepositoryInfo] = []
    await asyncio_gather(
        *[
            _collect_repository_information(
                client=client,
                repository_entries=repository_entries,
                repository_information_list=repository_information_list
            )
            for _ in range(min(num_repository_entries, num_max_concurrent))
        ]
    )

    return {
        author
        for repo_info in repository_information_list
        for author in repo_info.commit_authors
    }
