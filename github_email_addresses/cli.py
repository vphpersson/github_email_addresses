from argparse import RawDescriptionHelpFormatter

from typed_argument_parser import TypedArgumentParser


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
            **(
                dict(
                    description='List the authors that appear in the commit history of a user\'s repositories.',
                    epilog=(
                        'The information is obtained by making requests with the GitHub REST API. '
                        'One must authenticate using a personal access token to avoid traffic limitations.\n'
                        'Scans all branches of a repository. '
                        'In case the repository is forked, only commits made after the fork date are examined.'
                    ),
                    formatter_class=RawDescriptionHelpFormatter,
                ) | kwargs
            )
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
