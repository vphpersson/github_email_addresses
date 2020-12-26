from asyncio import gather as asyncio_gather
from dataclasses import dataclass
from math import ceil
from itertools import count
from typing import Any

from httpx import AsyncClient as HttpxAsyncClient

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


async def _work(client: HttpxAsyncClient, repos: list[dict[str, Any]], repo_info_list: list[RepositoryInfo]):

    while True:
        try:
            repo = repos.pop()
        except IndexError:
            break

        commits = []
        for page_number in count(start=1):
            response = await client.get(
                url=f'/repos/{repo["full_name"]}/commits',
                params={'per_page': MAX_NUM_RESULTS_PER_PAGE, 'page': page_number}
            )
            if response.status_code == 409:
                # The repository has no commits.
                break
            else:
                response.raise_for_status()

            response_commits = response.json()
            commits.extend(response_commits)

            if not response_commits or len(response_commits) < MAX_NUM_RESULTS_PER_PAGE:
                break

        repo_info_list.append(
            RepositoryInfo(
                name=repo['name'],
                owner=repo['owner']['login'],
                commit_authors=set(
                    CommitAuthor(
                        name=commit['commit']['committer']['name'],
                        email_address=commit['commit']['committer']['email']
                    )
                    for commit in commits
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
    :return:
    """

    # Obtain the number of repositories that the user has, for paging reasons.
    num_repositories_response = await client.get(url='/search/repositories', params={'q': f'user:{username}'})
    num_repositories_response.raise_for_status()
    num_repositories: int = num_repositories_response.json()['total_count']

    repository_entries: list[dict[str, any]] = [
        repository
        for page_response in (
            (await asyncio_gather(*[
                client.get(
                    url=f'/users/{username}/repos',
                    params={'per_page': MAX_NUM_RESULTS_PER_PAGE, 'page': page_number}
                )
                for page_number in range(1, ceil(num_repositories / MAX_NUM_RESULTS_PER_PAGE) + 1)
            ]))
        )
        if page_response.raise_for_status() is None
        for repository in page_response.json()
        if not repository['fork']
    ]

    num_repository_entries = len(repository_entries)
    repo_info_list: list[RepositoryInfo] = []
    await asyncio_gather(
        *[
            _work(
                client=client,
                repos=repository_entries,
                repo_info_list=repo_info_list
            )
            for _ in range(min(num_repository_entries, num_max_concurrent))
        ]
    )

    return {
        author
        for repo_info in repo_info_list
        for author in repo_info.commit_authors
        if author.email_address != 'noreply@github.com'
    }
