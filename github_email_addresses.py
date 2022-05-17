#!/usr/bin/env python

from __future__ import annotations
from asyncio import run as asyncio_run
from typing import Type

from httpx import AsyncClient
from string_utils_py import underline

from github_email_addresses.cli import GithubEmailAddressesArgumentParser
from github_email_addresses import obtain_github_authors, RepositoryInfo


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
