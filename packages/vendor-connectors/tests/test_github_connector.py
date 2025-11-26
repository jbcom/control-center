"""Tests for GithubConnector."""
import pytest
from unittest.mock import MagicMock, patch

from cloud_connectors.github import GithubConnector


class TestGithubConnector:
    """Test suite for GithubConnector."""

    @patch('cloud_connectors.github.Github')
    def test_init_with_repo(self, mock_github_class, base_connector_kwargs):
        """Test initialization with repository."""
        mock_github = MagicMock()
        mock_org = MagicMock()
        mock_repo = MagicMock()
        mock_repo.default_branch = "main"
        
        mock_github.get_organization.return_value = mock_org
        mock_github.get_repo.return_value = mock_repo
        mock_github_class.return_value = mock_github
        
        connector = GithubConnector(
            github_owner="test-org",
            github_repo="test-repo",
            github_token="test-token",
            **base_connector_kwargs
        )
        
        assert connector.GITHUB_OWNER == "test-org"
        assert connector.GITHUB_REPO == "test-repo"
        assert connector.repo is not None
        assert connector.GITHUB_BRANCH == "main"

    @patch('cloud_connectors.github.Github')
    def test_init_without_repo(self, mock_github_class, base_connector_kwargs):
        """Test initialization without repository."""
        mock_github = MagicMock()
        mock_org = MagicMock()
        mock_github.get_organization.return_value = mock_org
        mock_github_class.return_value = mock_github
        
        connector = GithubConnector(
            github_owner="test-org",
            github_token="test-token",
            **base_connector_kwargs
        )
        
        assert connector.repo is None

    @patch('cloud_connectors.github.Github')
    def test_get_repository_branch(self, mock_github_class, base_connector_kwargs):
        """Test getting repository branch."""
        mock_github = MagicMock()
        mock_org = MagicMock()
        mock_repo = MagicMock()
        mock_branch = MagicMock()
        
        mock_repo.get_branch.return_value = mock_branch
        mock_repo.default_branch = "main"
        mock_github.get_organization.return_value = mock_org
        mock_github.get_repo.return_value = mock_repo
        mock_github_class.return_value = mock_github
        
        connector = GithubConnector(
            github_owner="test-org",
            github_repo="test-repo",
            github_token="test-token",
            **base_connector_kwargs
        )
        
        branch = connector.get_repository_branch("feature-branch")
        assert branch == mock_branch

    @patch('cloud_connectors.github.Github')
    def test_get_repository_file(self, mock_github_class, base_connector_kwargs):
        """Test getting repository file."""
        mock_github = MagicMock()
        mock_org = MagicMock()
        mock_repo = MagicMock()
        mock_file = MagicMock()
        mock_file.decoded_content = b'{"test": "data"}'
        mock_file.sha = "abc123"
        mock_file.content = "test content"
        
        mock_repo.get_contents.return_value = mock_file
        mock_repo.default_branch = "main"
        mock_github.get_organization.return_value = mock_org
        mock_github.get_repo.return_value = mock_repo
        mock_github_class.return_value = mock_github
        
        connector = GithubConnector(
            github_owner="test-org",
            github_repo="test-repo",
            github_token="test-token",
            **base_connector_kwargs
        )
        
        content = connector.get_repository_file("test.json")
        assert content is not None
