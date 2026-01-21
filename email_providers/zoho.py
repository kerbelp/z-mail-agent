"""Zoho Mail email provider implementation."""
import json
import logging
import requests
from typing import List, Dict, Optional

from email_providers.base import EmailProvider
from config import (
    RUN_CONFIG,
    ZOHO_MCP_URL,
    ZOHO_ACCOUNT_ID,
    REPLY_EMAIL_ADDRESS,
    READ_EMAIL_STATUS
)

logger = logging.getLogger(__name__)


class ZohoEmailProvider(EmailProvider):
    """Zoho Mail implementation of the EmailProvider interface."""
    
    def __init__(self):
        """Initialize Zoho email provider with configuration."""
        self.mcp_url = ZOHO_MCP_URL
        self.account_id = ZOHO_ACCOUNT_ID
        self.reply_from_address = REPLY_EMAIL_ADDRESS
        self.timeout = 10
    
    def _make_request(self, tool_name: str, arguments: dict) -> dict:
        """
        Make a request to Zoho MCP server.
        
        Args:
            tool_name: Name of the Zoho MCP tool to call
            arguments: Tool arguments
            
        Returns:
            API response as dictionary
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": 1
        }
        
        response = requests.post(
            self.mcp_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=self.timeout
        )
        response.raise_for_status()
        
        if RUN_CONFIG.debug:
            logger.info(f"[DEBUG] {tool_name} response: {response.json()}")
        
        return response.json()
    
    def fetch_unread_emails(self, limit: int, exclude_label_id: Optional[str] = None) -> List[Dict]:
        """Fetch unread emails from Zoho Mail, optionally excluding a label."""
        logger.info("Start fetching emails from Zoho")
        
        try:
            # TEMPORARY HACK: Fetch 3x limit when filtering by label to avoid getting stuck
            # when first N emails all have the label. Remove this once Zoho API supports
            # filtering by "label NOT IN" at the API level instead of client-side filtering.
            fetch_limit = limit * 3 if exclude_label_id else limit
            
            response = self._make_request(
                "ZohoMail_listEmails",
                {
                    "path_variables": {"accountId": self.account_id},
                    "query_params": {
                        "status": READ_EMAIL_STATUS,
                        "limit": fetch_limit
                    }
                }
            )
            
            raw_text = response['result']['content'][0]['text']
            all_emails = json.loads(raw_text).get('data', [])
            
            # Filter out emails with the excluded label
            if exclude_label_id:
                unprocessed_emails = [
                    email for email in all_emails 
                    if exclude_label_id not in email.get('labelId', [])
                ]
                
                # Only return up to the requested limit
                unprocessed_emails = unprocessed_emails[:limit]
                
                filtered_count = len(all_emails) - len(unprocessed_emails)
                if filtered_count > 0:
                    logger.info(
                        f"Filtered out {filtered_count} already processed emails "
                        f"(with labelId '{exclude_label_id}')"
                    )
                
                logger.info(
                    f"Fetched {len(all_emails)} unread emails, "
                    f"{len(unprocessed_emails)} unprocessed"
                )
                return unprocessed_emails
            
            logger.info(f"Fetched {len(all_emails)} unread emails")
            return all_emails
            
        except Exception as e:
            logger.error(f"Error fetching emails: {str(e)}")
            return []
    
    def get_email_content(self, message_id: str, folder_id: str) -> str:
        """Fetch full email content from Zoho Mail."""
        if not message_id or not folder_id:
            logger.error(
                f"Cannot fetch email content: missing required parameter "
                f"(message_id={message_id}, folder_id={folder_id})"
            )
            return ""
        
        logger.info(f"Fetching content for email {message_id}")
        
        try:
            response = self._make_request(
                "ZohoMail_getMessageContent",
                {
                    "path_variables": {
                        "accountId": self.account_id,
                        "folderId": folder_id,
                        "messageId": message_id
                    },
                    "query_params": {"includeBlockContent": False}
                }
            )
            
            raw_text = response['result']['content'][0]['text']
            return json.loads(raw_text).get('data', {}).get('content', '')
            
        except Exception as e:
            logger.error(f"Error fetching email content for {message_id}: {str(e)}")
            return ""
    
    def send_reply(self, message_id: str, to_address: str, subject: str, content: str) -> bool:
        """Send a reply email via Zoho Mail."""
        if not message_id or not to_address:
            logger.error(
                f"Cannot send reply: missing required parameter "
                f"(message_id={message_id}, to_address={to_address})"
            )
            return False
        
        if RUN_CONFIG.dry_run or not RUN_CONFIG.send_reply:
            logger.info(
                f"[SKIP] Would send reply to {to_address} "
                f"(dry_run={RUN_CONFIG.dry_run}, send_reply={RUN_CONFIG.send_reply})"
            )
            return True
        
        try:
            self._make_request(
                "ZohoMail_sendReplyEmail",
                {
                    "path_variables": {
                        "accountId": self.account_id,
                        "messageId": message_id
                    },
                    "body": {
                        "action": "reply",
                        "fromAddress": self.reply_from_address,
                        "toAddress": to_address,
                        "subject": f"Re: {subject}",
                        "content": content,
                        "mailFormat": "plaintext"
                    }
                }
            )
            
            logger.info(f"Sent reply to {to_address}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending reply to {to_address}: {str(e)}")
            return False
    
    def mark_as_read(self, message_id: str) -> bool:
        """Mark an email as read in Zoho Mail."""
        if not message_id:
            logger.error("Cannot mark as read: message_id is None or empty")
            return False
        
        if RUN_CONFIG.dry_run:
            logger.info(f"[DRY RUN] Would mark email {message_id} as read")
            return True
        
        try:
            self._make_request(
                "ZohoMail_readMessages",
                {
                    "path_variables": {"accountIdToRead": self.account_id},
                    "body": {
                        "mode": "markAsRead",
                        "messageId": [int(message_id)]
                    }
                }
            )
            
            logger.info(f"Marked email {message_id} as read")
            return True
            
        except Exception as e:
            logger.error(f"Error marking email {message_id} as read: {str(e)}")
            return False
    
    def apply_label(self, message_id: str, folder_id: str, label_id: str) -> bool:
        """Apply a label to an email in Zoho Mail."""
        # Validate required parameters
        if not message_id or not folder_id or not label_id:
            logger.error(
                f"Cannot apply label: missing required parameter "
                f"(message_id={message_id}, folder_id={folder_id}, label_id={label_id})"
            )
            return False
        
        if RUN_CONFIG.dry_run or not RUN_CONFIG.add_label:
            logger.info(
                f"[SKIP] Would apply label to email {message_id} "
                f"(dry_run={RUN_CONFIG.dry_run}, add_label={RUN_CONFIG.add_label})"
            )
            return True
        
        try:
            response = self._make_request(
                "ZohoMail_applyLabelToMessages",
                {
                    "path_variables": {"accountIdToApplyLabel": self.account_id},
                    "body": {
                        "mode": "applyLabel",
                        "labelId": [label_id],
                        "messageId": [int(message_id)],
                        "isFolderSpecific": True,
                        "folderId": folder_id
                    }
                }
            )
            
            # Check if API returned an error
            if response.get('result', {}).get('isError'):
                logger.error(f"Error applying label to {message_id}: {response}")
                return False
            
            logger.info(f"Applied label to email {message_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error applying label to {message_id}: {str(e)}")
            return False
