import unittest
from unittest.mock import patch, Mock
from rm_analyzer_local import send

class TestSend(unittest.TestCase):
    @patch("rm_analyzer_local.send.Credentials")
    @patch("rm_analyzer_local.send.build")
    @patch("rm_analyzer_local.send.os.path.exists", return_value=True)
    @patch("rm_analyzer_local.send.open", create=True)
    def test_gmail_send_message_mock(self, mock_open, mock_exists, mock_build, mock_creds):
        # Mock credentials and Gmail API service
        mock_creds.from_authorized_user_file.return_value = Mock(valid=True)
        mock_service = Mock()
        mock_build.return_value = mock_service
        mock_service.users.return_value.messages.return_value.send.return_value.execute.return_value = {"id": "123"}
        result = send.gmail_send_message(
            destination="test@example.com",
            subject="Test Subject",
            html="<b>Test</b>"
        )
        self.assertEqual(result["id"], "123")

if __name__ == "__main__":
    unittest.main()
