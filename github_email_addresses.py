#!/usr/bin/env python3

from __future__ import annotations
from argparse import RawDescriptionHelpFormatter
from asyncio import run as asyncio_run
from typing import Type

from httpx import AsyncClient
from pyutils.argparse.typed_argument_parser import TypedArgumentParser
from pyutils.my_string import underline

from github_email_addresses import obtain_github_authors, RepositoryInfo


class GithubEmailAddressesArgumentParser(TypedArgumentParser):

    class Namespace:
        auth_username: str
        auth_access_token: str
        repo_user: str
        num_max_concurrent: int
        per_repo: bool

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            description='List the authors that appear in the commit history of a user\'s repositories.',
            epilog=(
                'The information is obtained by making requests with the GitHub REST API. '
                'One must authenticate using a personal access token to avoid traffic limitations.\n'
                'Scans all branches of a repository. '
                'In case the repository is forked, only commits made after the fork date are examined.'
            ),
            formatter_class=RawDescriptionHelpFormatter,
            **kwargs
        )

        self.add_argument(
            'auth_username',
            help='The username of the user with which to authenticate.'
        )

        self.add_argument(
            'auth_access_token',
            help='The access token of the user with which to authenticate.'
        )

        self.add_argument(
            'repo_user',
            help='The username of the GitHub user whose repositories to scan.'
        )

        self.add_argument(
            '-n', '--num-max-concurrent',
            help='The maximum number of concurrent HTTP requests.',
            type=int,
            default=5
        )

        self.add_argument(
            '-p', '--per-repo',
            help='Show commit authors per repository.',
            action='store_true'
        )


async def main():

    args: Type[GithubEmailAddressesArgumentParser.Namespace] = GithubEmailAddressesArgumentParser().parse_args()

    client_options = dict(
        base_url='https://api.github.com/',
        headers={
            'Accept': 'application/vnd.github.v3+json'
        },
        auth=(args.auth_username, args.auth_access_token)
    )
    async with AsyncClient(**client_options) as client:
        repository_information_list: list[RepositoryInfo] = await obtain_github_authors(
            client=client,
            username=args.repo_user,
            num_max_concurrent=args.num_max_concurrent
        )

    if args.per_repo:
        print(
            '\n\n'.join(
                underline(string=repository_information.name) + '\n' + '\n'.join(
                    sorted([str(author) for author in repository_information.commit_authors])
                )
                for repository_information in repository_information_list
            )
        )
    else:
        print(
            '\n'.join(
                sorted({
                    str(author)
                    for repo_info in repository_information_list
                    for author in repo_info.commit_authors
                })
            )
        )

if __name__ == '__main__':
    asyncio_run(main())
