"""
MESSAGING Module
Purpose: Handle text messaging and chat during video calls
"""

import time
from typing import List, Optional, Dict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


# ============================================
# MESSAGE TYPES
# ============================================

class MessageType(Enum):
    """Type of message."""
    TEXT = "text"
    SYSTEM = "system"
    CAPTION = "caption"
    NOTIFICATION = "notification"


class MessageStatus(Enum):
    """Status of message delivery."""
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


# ============================================
# MESSAGE DATA STRUCTURE
# ============================================

@dataclass
class Message:
    """Represents a single message."""
    message_id: str
    sender_id: str
    sender_name: str
    content: str
    message_type: MessageType = MessageType.TEXT
    timestamp: datetime = None
    status: MessageStatus = MessageStatus.SENT
    read_at: Optional[datetime] = None
    edited_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def mark_as_read(self) -> None:
        """Mark message as read."""
        self.status = MessageStatus.READ
        self.read_at = datetime.now()
    
    def get_formatted_time(self) -> str:
        """Get formatted timestamp."""
        return self.timestamp.strftime("%H:%M:%S")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "sender_name": self.sender_name,
            "content": self.content,
            "type": self.message_type.value,
            "timestamp": self.get_formatted_time(),
            "status": self.status.value
        }


# ============================================
# CHAT HISTORY
# ============================================

class ChatHistory:
    """Manages chat history and message storage."""
    
    def __init__(self, max_messages: int = 1000):
        """
        Initialize chat history.
        
        Args:
            max_messages: Maximum messages to keep in memory
        """
        self.messages: List[Message] = []
        self.max_messages = max_messages
        self.unread_count = 0
    
    def add_message(self, message: Message) -> bool:
        """
        Add message to history.
        
        Args:
            message: Message to add
        
        Returns:
            True if added, False otherwise
        """
        try:
            self.messages.append(message)
            
            # Trim old messages if exceeding limit
            if len(self.messages) > self.max_messages:
                self.messages = self.messages[-self.max_messages:]
            
            self.unread_count += 1
            return True
        
        except Exception as e:
            print(f"ERROR: Failed to add message: {str(e)}")
            return False
    
    def get_all_messages(self) -> List[Message]:
        """Get all messages in history."""
        return self.messages.copy()
    
    def get_recent_messages(self, count: int = 50) -> List[Message]:
        """Get last N messages."""
        return self.messages[-count:]
    
    def get_messages_from_sender(self, sender_id: str) -> List[Message]:
        """Get all messages from specific sender."""
        return [m for m in self.messages if m.sender_id == sender_id]
    
    def get_messages_by_type(self, message_type: MessageType) -> List[Message]:
        """Get messages by type."""
        return [m for m in self.messages if m.message_type == message_type]
    
    def mark_all_as_read(self) -> None:
        """Mark all unread messages as read."""
        for message in self.messages:
            if message.status != MessageStatus.READ:
                message.mark_as_read()
        self.unread_count = 0
    
    def get_unread_count(self) -> int:
        """Get unread message count."""
        return sum(1 for m in self.messages if m.status != MessageStatus.READ)
    
    def clear_history(self) -> None:
        """Clear all messages."""
        self.messages.clear()
        self.unread_count = 0
    
    def search_messages(self, keyword: str) -> List[Message]:
        """Search messages by keyword."""
        keyword_lower = keyword.lower()
        return [m for m in self.messages 
                if keyword_lower in m.content.lower() 
                or keyword_lower in m.sender_name.lower()]


# ============================================
# MESSAGE MANAGER (MAIN CLASS)
# ============================================

class MessageManager:
    """Manages messaging for video call."""
    
    def __init__(self):
        """Initialize message manager."""
        self.chat_history = ChatHistory()
        self.participants_typing: Dict[str, float] = {}  # participant_id -> timestamp
        self.message_callbacks = {}
    
    def send_message(
        self,
        message_id: str,
        sender_id: str,
        sender_name: str,
        content: str,
        message_type: MessageType = MessageType.TEXT
    ) -> bool:
        """
        Send a message.
        
        Args:
            message_id: Unique message ID
            sender_id: ID of sender
            sender_name: Display name of sender
            content: Message content
            message_type: Type of message
        
        Returns:
            True if sent, False otherwise
        """
        try:
            # Validate message
            if not content or len(content.strip()) == 0:
                return False
            
            if len(content) > 5000:  # Max message length
                content = content[:5000]
            
            # Create message
            message = Message(
                message_id=message_id,
                sender_id=sender_id,
                sender_name=sender_name,
                content=content.strip(),
                message_type=message_type,
                status=MessageStatus.SENT
            )
            
            # Add to history
            self.chat_history.add_message(message)
            
            # Trigger callback
            self._trigger_callback("message_sent", message)
            
            print(f"✓ Message sent from {sender_name}")
            return True
        
        except Exception as e:
            print(f"ERROR: Failed to send message: {str(e)}")
            return False
    
    def send_system_message(self, content: str) -> bool:
        """Send system notification message."""
        return self.send_message(
            message_id=self._generate_id(),
            sender_id="system",
            sender_name="System",
            content=content,
            message_type=MessageType.SYSTEM
        )
    
    def send_caption_message(
        self,
        sender_id: str,
        sender_name: str,
        caption: str
    ) -> bool:
        """Send live caption message."""
        return self.send_message(
            message_id=self._generate_id(),
            sender_id=sender_id,
            sender_name=sender_name,
            content=caption,
            message_type=MessageType.CAPTION
        )
    
    def get_messages(self, limit: int = 50) -> List[Dict]:
        """Get messages as dictionaries."""
        return [m.to_dict() for m in self.chat_history.get_recent_messages(limit)]
    
    def get_chat_display(self, limit: int = 20) -> str:
        """Get formatted chat for display."""
        messages = self.chat_history.get_recent_messages(limit)
        if not messages:
            return "No messages yet"
        
        display = []
        for msg in messages:
            formatted = f"[{msg.get_formatted_time()}] {msg.sender_name}: {msg.content}"
            display.append(formatted)
        
        return "\n".join(display)
    
    def set_participant_typing(self, participant_id: str, is_typing: bool) -> None:
        """
        Set participant typing status.
        
        Args:
            participant_id: ID of participant
            is_typing: Whether typing
        """
        try:
            if is_typing:
                self.participants_typing[participant_id] = time.time()
            else:
                self.participants_typing.pop(participant_id, None)
            
            self._trigger_callback("typing_status_changed", 
                                  (participant_id, is_typing))
        
        except Exception as e:
            print(f"ERROR: Failed to update typing status: {str(e)}")
    
    def get_typing_participants(self) -> List[str]:
        """Get list of participants currently typing."""
        current_time = time.time()
        typing_timeout = 5  # seconds
        
        active_typists = [
            pid for pid, ts in self.participants_typing.items()
            if current_time - ts < typing_timeout
        ]
        
        return active_typists
    
    def delete_message(self, message_id: str) -> bool:
        """Delete a message."""
        try:
            self.chat_history.messages = [
                m for m in self.chat_history.messages 
                if m.message_id != message_id
            ]
            return True
        except:
            return False
    
    def clear_chat(self) -> None:
        """Clear all chat messages."""
        self.chat_history.clear_history()
        self._trigger_callback("chat_cleared", None)
    
    def search_chat(self, keyword: str) -> List[Dict]:
        """Search chat messages."""
        results = self.chat_history.search_messages(keyword)
        return [m.to_dict() for m in results]
    
    def mark_chat_read(self) -> None:
        """Mark all messages as read."""
        self.chat_history.mark_all_as_read()
    
    def get_statistics(self) -> Dict:
        """Get chat statistics."""
        return {
            "total_messages": len(self.chat_history.messages),
            "unread_messages": self.chat_history.get_unread_count(),
            "total_participants": len(set(m.sender_id 
                                         for m in self.chat_history.messages))
        }
    
    @staticmethod
    def _generate_id() -> str:
        """Generate unique message ID."""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _trigger_callback(self, callback_name: str, data: any) -> None:
        """Trigger registered callback."""
        try:
            if callback_name in self.message_callbacks:
                self.message_callbacks[callback_name](data)
        except Exception as e:
            print(f"ERROR: Message callback failed: {str(e)}")
    
    def register_callback(self, callback_name: str, callback) -> None:
        """Register message callback."""
        self.message_callbacks[callback_name] = callback


# ============================================
# QUICK MESSAGE UTILITIES
# ============================================

class QuickMessages:
    """Pre-defined quick messages for quick sending."""
    
    MESSAGES = {
        "hello": "Hello! Can you hear me?",
        "bye": "Goodbye!",
        "thank_you": "Thank you!",
        "need_help": "I need help",
        "one_moment": "One moment please",
        "can_you_see": "Can you see me?",
        "yes": "Yes",
        "no": "No",
        "slow": "Connection is slow",
        "clear_audio": "Audio is clear",
        "repeat": "Can you repeat that?",
        "deaf_relay": "Using deaf relay service"
    }
    
    @staticmethod
    def get_message(key: str) -> Optional[str]:
        """Get quick message by key."""
        return QuickMessages.MESSAGES.get(key)
    
    @staticmethod
    def get_all_messages() -> Dict[str, str]:
        """Get all quick messages."""
        return QuickMessages.MESSAGES.copy()
