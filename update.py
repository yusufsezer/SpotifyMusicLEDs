import git

from dynamodb_client import DynamoDBClient

def parse_git_settings(record):
    """ Parse and return the git branch and commit ID from a DynamoDB record

    Returns the git branch and git commit ID as a tuple
    """
    settings = record['settings']['M']
    git_branch = settings['gitBranch']['S']
    git_commit = settings['gitCommitID']['S']
    return git_branch, git_commit

if __name__ == "__main__":
    """ Script responsible for updating the Spotify Lights source code

    Retrieves user settings from DynamoDB, extracts the desired git branch and
    git commit ID as specified un the settings, and updates the source code
    using git commands.
    """

    # Retrieve git settings from DynamoDB
    dynamoDBClient = DynamoDBClient()
    record = dynamoDBClient.get_record()
    git_branch, git_commit = parse_git_settings(record)

    # Perform update (checkout the specified git branch and commit)
    try:
        repo = git.Repo()
        repo.git.fetch()
        repo.git.checkout(git_branch)
        repo.git.checkout(git_commit)
        print(f"Updated software to branch {git_branch} and commit {git_commit}")
    except Exception as ex:
        print(f"Failure occured while performing software update: {ex}")

    exit(0)
