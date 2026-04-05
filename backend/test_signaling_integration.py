"""
Integration tests for Socket.IO Signaling Server

Tests the complete WebRTC signaling flow, participant notifications,
and chat message delivery with real Socket.IO connections.

Requirements: 10.3, 21.6

IMPORTANT: These integration tests require the following services to be running:
1. Redis server on localhost:6379
2. PostgreSQL database (for chat message storage)
3. Signaling server on localhost:8001

To run these tests:
1. Start Redis: redis-server (or docker-compose up redis)
2. Start PostgreSQL: docker-compose up postgres
3. Start signaling server: python signaling_server.py
4. Run tests: pytest test_signaling_integration.py -v

These tests validate:
- WebRTC signaling flow (offer/answer/ICE) - Requirement 21.6
- Participant join/leave notifications - Requirement 21.6
- Chat message delivery within 500ms - Requirement 10.3
"""

import asyncio
import os
import time
from typing import Dict, List
from uuid import uuid4

import pytest
import socketio
from fastapi.testclient import TestClient

from signaling_server import app, socket_app
from redis_client import get_redis_client


# Skip all tests if services are not available
pytestmark = pytest.mark.skipif(
    os.getenv('SKIP_INTEGRATION_TESTS', 'true').lower() == 'true',
    reason="Integration tests require running services (Redis, PostgreSQL, Signaling Server). "
           "Set SKIP_INTEGRATION_TESTS=false to run these tests."
)


# ============================================================================
# Test Configuration
# ============================================================================

TEST_MEETING_ID = "test-meeting-integration"
TEST_USER_1 = "user-integration-1"
TEST_USER_2 = "user-integration-2"
TEST_USER_3 = "user-integration-3"


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def redis_client():
    """Get Redis client and clean up test data."""
    client = get_redis_client()
    
    # Clean up before test
    client.delete_session(TEST_USER_1)
    client.delete_session(TEST_USER_2)
    client.delete_session(TEST_USER_3)
    client.remove_participant(TEST_MEETING_ID, TEST_USER_1)
    client.remove_participant(TEST_MEETING_ID, TEST_USER_2)
    client.remove_participant(TEST_MEETING_ID, TEST_USER_3)
    
    yield client
    
    # Clean up after test
    client.delete_session(TEST_USER_1)
    client.delete_session(TEST_USER_2)
    client.delete_session(TEST_USER_3)
    client.remove_participant(TEST_MEETING_ID, TEST_USER_1)
    client.remove_participant(TEST_MEETING_ID, TEST_USER_2)
    client.remove_participant(TEST_MEETING_ID, TEST_USER_3)


@pytest.fixture
async def test_client():
    """Create test client for FastAPI app."""
    with TestClient(app) as client:
        yield client


class SocketIOTestClient:
    """Helper class for Socket.IO test clients."""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.client = socketio.AsyncClient()
        self.received_events: List[Dict] = []
        self.connected = False
        
        # Register event handlers
        @self.client.on('connect')
        async def on_connect():
            self.connected = True
        
        @self.client.on('disconnect')
        async def on_disconnect():
            self.connected = False
        
        @self.client.on('*')
        async def catch_all(event, data):
            self.received_events.append({
                'event': event,
                'data': data,
                'timestamp': time.time()
            })
    
    async def connect(self, url: str = 'http://localhost:8001'):
        """Connect to Socket.IO server."""
        await self.client.connect(url, socketio_path='/socket.io')
        # Wait for connection
        for _ in range(10):
            if self.connected:
                break
            await asyncio.sleep(0.1)
        return self.connected
    
    async def disconnect(self):
        """Disconnect from Socket.IO server."""
        await self.client.disconnect()
    
    async def emit(self, event: str, data: Dict):
        """Emit event to server."""
        await self.client.emit(event, data)
    
    def get_events(self, event_name: str) -> List[Dict]:
        """Get all received events of a specific type."""
        return [e for e in self.received_events if e['event'] == event_name]
    
    def clear_events(self):
        """Clear received events."""
        self.received_events.clear()


# ============================================================================
# Integration Tests
# ============================================================================

class TestWebRTCSignalingFlow:
    """
    Test complete WebRTC signaling flow (offer/answer/ICE).
    
    Requirements: 21.6
    """
    
    @pytest.mark.asyncio
    async def test_offer_answer_ice_flow(self, redis_client):
        """
        Test complete WebRTC signaling flow between two peers.
        
        Validates:
        - Offer is forwarded from peer A to peer B
        - Answer is forwarded from peer B to peer A
        - ICE candidates are exchanged bidirectionally
        - Requirement 21.6: ICE connection establishment within 3 seconds
        """
        # Create two test clients
        client_a = SocketIOTestClient(TEST_USER_1)
        client_b = SocketIOTestClient(TEST_USER_2)
        
        try:
            # Connect both clients
            await client_a.connect()
            await client_b.connect()
            
            assert client_a.connected
            assert client_b.connected
            
            # Both join the same meeting
            await client_a.emit('join-meeting', {
                'meetingId': TEST_MEETING_ID,
                'userId': TEST_USER_1,
                'mediaCapabilities': {'audio': True, 'video': True}
            })
            
            await client_b.emit('join-meeting', {
                'meetingId': TEST_MEETING_ID,
                'userId': TEST_USER_2,
                'mediaCapabilities': {'audio': True, 'video': True}
            })
            
            # Wait for join confirmations
            await asyncio.sleep(0.5)
            
            # Clear events to focus on signaling
            client_a.clear_events()
            client_b.clear_events()
            
            # Start timing for Requirement 21.6 (ICE within 3 seconds)
            start_time = time.time()
            
            # Step 1: Client A sends offer to Client B
            test_sdp_offer = 'v=0\r\no=- 123456 2 IN IP4 127.0.0.1\r\ns=-\r\nt=0 0\r\n'
            await client_a.emit('offer', {
                'from': TEST_USER_1,
                'to': TEST_USER_2,
                'sdp': test_sdp_offer
            })
            
            # Wait for offer to be received
            await asyncio.sleep(0.2)
            
            # Verify Client B received the offer
            offers = client_b.get_events('offer')
            assert len(offers) == 1
            assert offers[0]['data']['from'] == TEST_USER_1
            assert offers[0]['data']['sdp'] == test_sdp_offer
            
            # Step 2: Client B sends answer to Client A
            test_sdp_answer = 'v=0\r\no=- 789012 2 IN IP4 127.0.0.1\r\ns=-\r\nt=0 0\r\n'
            await client_b.emit('answer', {
                'from': TEST_USER_2,
                'to': TEST_USER_1,
                'sdp': test_sdp_answer
            })
            
            # Wait for answer to be received
            await asyncio.sleep(0.2)
            
            # Verify Client A received the answer
            answers = client_a.get_events('answer')
            assert len(answers) == 1
            assert answers[0]['data']['from'] == TEST_USER_2
            assert answers[0]['data']['sdp'] == test_sdp_answer
            
            # Step 3: Exchange ICE candidates
            test_ice_candidate_a = {
                'candidate': 'candidate:1 1 UDP 2130706431 192.168.1.100 54321 typ host',
                'sdpMLineIndex': 0,
                'sdpMid': 'audio'
            }
            
            test_ice_candidate_b = {
                'candidate': 'candidate:2 1 UDP 2130706431 192.168.1.101 54322 typ host',
                'sdpMLineIndex': 0,
                'sdpMid': 'video'
            }
            
            # Client A sends ICE candidate to Client B
            await client_a.emit('ice-candidate', {
                'from': TEST_USER_1,
                'to': TEST_USER_2,
                'candidate': test_ice_candidate_a
            })
            
            # Client B sends ICE candidate to Client A
            await client_b.emit('ice-candidate', {
                'from': TEST_USER_2,
                'to': TEST_USER_1,
                'candidate': test_ice_candidate_b
            })
            
            # Wait for ICE candidates to be received
            await asyncio.sleep(0.2)
            
            # Verify ICE candidates were exchanged
            ice_candidates_b = client_b.get_events('ice-candidate')
            assert len(ice_candidates_b) >= 1
            assert ice_candidates_b[0]['data']['from'] == TEST_USER_1
            assert ice_candidates_b[0]['data']['candidate'] == test_ice_candidate_a
            
            ice_candidates_a = client_a.get_events('ice-candidate')
            assert len(ice_candidates_a) >= 1
            assert ice_candidates_a[0]['data']['from'] == TEST_USER_2
            assert ice_candidates_a[0]['data']['candidate'] == test_ice_candidate_b
            
            # Verify total time is within 3 seconds (Requirement 21.6)
            elapsed_time = time.time() - start_time
            assert elapsed_time < 3.0, f"ICE exchange took {elapsed_time}s, should be < 3s"
            
        finally:
            await client_a.disconnect()
            await client_b.disconnect()


class TestParticipantNotifications:
    """
    Test participant join/leave notifications.
    
    Requirements: 21.6
    """
    
    @pytest.mark.asyncio
    async def test_participant_join_notifications(self, redis_client):
        """
        Test that all participants are notified when a new participant joins.
        
        Validates:
        - Existing participants receive 'participant-joined' event
        - New participant receives list of existing participants
        - Participant data includes correct media states
        """
        client_1 = SocketIOTestClient(TEST_USER_1)
        client_2 = SocketIOTestClient(TEST_USER_2)
        client_3 = SocketIOTestClient(TEST_USER_3)
        
        try:
            # Connect all clients
            await client_1.connect()
            await client_2.connect()
            await client_3.connect()
            
            # Client 1 joins first
            await client_1.emit('join-meeting', {
                'meetingId': TEST_MEETING_ID,
                'userId': TEST_USER_1,
                'mediaCapabilities': {'audio': True, 'video': True}
            })
            
            await asyncio.sleep(0.3)
            
            # Verify Client 1 received success with empty participants list
            join_success = client_1.get_events('join-meeting-success')
            assert len(join_success) == 1
            assert join_success[0]['data']['success'] is True
            assert len(join_success[0]['data']['participants']) == 0
            
            # Clear events
            client_1.clear_events()
            
            # Client 2 joins
            await client_2.emit('join-meeting', {
                'meetingId': TEST_MEETING_ID,
                'userId': TEST_USER_2,
                'mediaCapabilities': {'audio': False, 'video': True}
            })
            
            await asyncio.sleep(0.3)
            
            # Verify Client 1 received participant-joined notification
            joined_events = client_1.get_events('participant-joined')
            assert len(joined_events) == 1
            assert joined_events[0]['data']['participant']['userId'] == TEST_USER_2
            assert joined_events[0]['data']['participant']['audioEnabled'] is False
            assert joined_events[0]['data']['participant']['videoEnabled'] is True
            
            # Verify Client 2 received existing participants
            join_success_2 = client_2.get_events('join-meeting-success')
            assert len(join_success_2) == 1
            participants = join_success_2[0]['data']['participants']
            assert len(participants) == 1
            assert participants[0]['userId'] == TEST_USER_1
            
            # Clear events
            client_1.clear_events()
            client_2.clear_events()
            
            # Client 3 joins
            await client_3.emit('join-meeting', {
                'meetingId': TEST_MEETING_ID,
                'userId': TEST_USER_3,
                'mediaCapabilities': {'audio': True, 'video': False}
            })
            
            await asyncio.sleep(0.3)
            
            # Verify both Client 1 and Client 2 received notification
            joined_events_1 = client_1.get_events('participant-joined')
            joined_events_2 = client_2.get_events('participant-joined')
            
            assert len(joined_events_1) == 1
            assert len(joined_events_2) == 1
            assert joined_events_1[0]['data']['participant']['userId'] == TEST_USER_3
            assert joined_events_2[0]['data']['participant']['userId'] == TEST_USER_3
            
            # Verify Client 3 received both existing participants
            join_success_3 = client_3.get_events('join-meeting-success')
            assert len(join_success_3) == 1
            participants_3 = join_success_3[0]['data']['participants']
            assert len(participants_3) == 2
            user_ids = [p['userId'] for p in participants_3]
            assert TEST_USER_1 in user_ids
            assert TEST_USER_2 in user_ids
            
        finally:
            await client_1.disconnect()
            await client_2.disconnect()
            await client_3.disconnect()
    
    @pytest.mark.asyncio
    async def test_participant_leave_notifications(self, redis_client):
        """
        Test that all participants are notified when a participant leaves.
        
        Validates:
        - Remaining participants receive 'participant-left' event
        - Session is cleaned up in Redis
        - Leaving participant receives confirmation
        """
        client_1 = SocketIOTestClient(TEST_USER_1)
        client_2 = SocketIOTestClient(TEST_USER_2)
        
        try:
            # Connect and join
            await client_1.connect()
            await client_2.connect()
            
            await client_1.emit('join-meeting', {
                'meetingId': TEST_MEETING_ID,
                'userId': TEST_USER_1,
                'mediaCapabilities': {'audio': True, 'video': True}
            })
            
            await client_2.emit('join-meeting', {
                'meetingId': TEST_MEETING_ID,
                'userId': TEST_USER_2,
                'mediaCapabilities': {'audio': True, 'video': True}
            })
            
            await asyncio.sleep(0.3)
            
            # Verify both are in the meeting
            participants = redis_client.get_participants(TEST_MEETING_ID)
            assert TEST_USER_1 in participants
            assert TEST_USER_2 in participants
            
            # Clear events
            client_1.clear_events()
            client_2.clear_events()
            
            # Client 2 leaves
            await client_2.emit('leave-meeting', {
                'meetingId': TEST_MEETING_ID,
                'userId': TEST_USER_2
            })
            
            await asyncio.sleep(0.3)
            
            # Verify Client 1 received participant-left notification
            left_events = client_1.get_events('participant-left')
            assert len(left_events) == 1
            assert left_events[0]['data']['userId'] == TEST_USER_2
            
            # Verify Client 2 received leave confirmation
            leave_success = client_2.get_events('leave-meeting-success')
            assert len(leave_success) == 1
            assert leave_success[0]['data']['success'] is True
            
            # Verify session cleaned up in Redis
            session = redis_client.get_session(TEST_USER_2)
            assert session is None
            
            # Verify participant removed from meeting
            participants = redis_client.get_participants(TEST_MEETING_ID)
            assert TEST_USER_2 not in participants
            assert TEST_USER_1 in participants
            
        finally:
            await client_1.disconnect()
            await client_2.disconnect()


class TestChatMessageDelivery:
    """
    Test chat message delivery.
    
    Requirements: 10.3
    """
    
    @pytest.mark.asyncio
    async def test_public_chat_message_delivery(self, redis_client):
        """
        Test public chat messages are delivered to all participants within 500ms.
        
        Validates:
        - Requirement 10.3: Messages delivered within 500ms
        - All participants receive the message
        - Message includes sender name and timestamp
        """
        client_1 = SocketIOTestClient(TEST_USER_1)
        client_2 = SocketIOTestClient(TEST_USER_2)
        client_3 = SocketIOTestClient(TEST_USER_3)
        
        try:
            # Connect and join all clients
            await client_1.connect()
            await client_2.connect()
            await client_3.connect()
            
            await client_1.emit('join-meeting', {
                'meetingId': TEST_MEETING_ID,
                'userId': TEST_USER_1,
                'mediaCapabilities': {'audio': True, 'video': True}
            })
            
            await client_2.emit('join-meeting', {
                'meetingId': TEST_MEETING_ID,
                'userId': TEST_USER_2,
                'mediaCapabilities': {'audio': True, 'video': True}
            })
            
            await client_3.emit('join-meeting', {
                'meetingId': TEST_MEETING_ID,
                'userId': TEST_USER_3,
                'mediaCapabilities': {'audio': True, 'video': True}
            })
            
            await asyncio.sleep(0.3)
            
            # Clear events
            client_1.clear_events()
            client_2.clear_events()
            client_3.clear_events()
            
            # Client 1 sends a public message
            start_time = time.time()
            
            await client_1.emit('send-chat-message', {
                'meetingId': TEST_MEETING_ID,
                'senderId': TEST_USER_1,
                'senderName': 'Alice',
                'messageText': 'Hello everyone!'
            })
            
            # Wait for message delivery
            await asyncio.sleep(0.6)  # Slightly more than 500ms to ensure delivery
            
            delivery_time = time.time() - start_time
            
            # Verify all clients received the message
            messages_1 = client_1.get_events('chat-message')
            messages_2 = client_2.get_events('chat-message')
            messages_3 = client_3.get_events('chat-message')
            
            assert len(messages_1) == 1, "Sender should receive own message"
            assert len(messages_2) == 1, "Client 2 should receive message"
            assert len(messages_3) == 1, "Client 3 should receive message"
            
            # Verify message content
            for messages in [messages_1, messages_2, messages_3]:
                msg = messages[0]['data']
                assert msg['senderId'] == TEST_USER_1
                assert msg['senderName'] == 'Alice'
                assert msg['messageText'] == 'Hello everyone!'
                assert msg['isPrivate'] is False
                assert 'timestamp' in msg
                assert 'id' in msg
            
            # Verify delivery time (Requirement 10.3: within 500ms)
            assert delivery_time < 0.5, f"Message delivery took {delivery_time}s, should be < 500ms"
            
        finally:
            await client_1.disconnect()
            await client_2.disconnect()
            await client_3.disconnect()
    
    @pytest.mark.asyncio
    async def test_private_chat_message_delivery(self, redis_client):
        """
        Test private chat messages are delivered only to recipient and sender.
        
        Validates:
        - Only recipient and sender receive the message
        - Other participants do not receive the message
        - Message is marked as private
        """
        client_1 = SocketIOTestClient(TEST_USER_1)
        client_2 = SocketIOTestClient(TEST_USER_2)
        client_3 = SocketIOTestClient(TEST_USER_3)
        
        try:
            # Connect and join all clients
            await client_1.connect()
            await client_2.connect()
            await client_3.connect()
            
            await client_1.emit('join-meeting', {
                'meetingId': TEST_MEETING_ID,
                'userId': TEST_USER_1,
                'mediaCapabilities': {'audio': True, 'video': True}
            })
            
            await client_2.emit('join-meeting', {
                'meetingId': TEST_MEETING_ID,
                'userId': TEST_USER_2,
                'mediaCapabilities': {'audio': True, 'video': True}
            })
            
            await client_3.emit('join-meeting', {
                'meetingId': TEST_MEETING_ID,
                'userId': TEST_USER_3,
                'mediaCapabilities': {'audio': True, 'video': True}
            })
            
            await asyncio.sleep(0.3)
            
            # Clear events
            client_1.clear_events()
            client_2.clear_events()
            client_3.clear_events()
            
            # Client 1 sends a private message to Client 2
            await client_1.emit('send-chat-message', {
                'meetingId': TEST_MEETING_ID,
                'senderId': TEST_USER_1,
                'senderName': 'Alice',
                'messageText': 'Private message for Bob',
                'recipientId': TEST_USER_2
            })
            
            # Wait for message delivery
            await asyncio.sleep(0.3)
            
            # Verify only Client 1 (sender) and Client 2 (recipient) received the message
            messages_1 = client_1.get_events('chat-message')
            messages_2 = client_2.get_events('chat-message')
            messages_3 = client_3.get_events('chat-message')
            
            assert len(messages_1) == 1, "Sender should receive own message"
            assert len(messages_2) == 1, "Recipient should receive message"
            assert len(messages_3) == 0, "Other participants should NOT receive private message"
            
            # Verify message content
            for messages in [messages_1, messages_2]:
                msg = messages[0]['data']
                assert msg['senderId'] == TEST_USER_1
                assert msg['senderName'] == 'Alice'
                assert msg['messageText'] == 'Private message for Bob'
                assert msg['isPrivate'] is True
                assert msg['recipientId'] == TEST_USER_2
            
        finally:
            await client_1.disconnect()
            await client_2.disconnect()
            await client_3.disconnect()
    
    @pytest.mark.asyncio
    async def test_multiple_chat_messages_order(self, redis_client):
        """
        Test that multiple chat messages are delivered in order.
        
        Validates:
        - Messages are received in the order they were sent
        - All messages are delivered successfully
        """
        client_1 = SocketIOTestClient(TEST_USER_1)
        client_2 = SocketIOTestClient(TEST_USER_2)
        
        try:
            # Connect and join
            await client_1.connect()
            await client_2.connect()
            
            await client_1.emit('join-meeting', {
                'meetingId': TEST_MEETING_ID,
                'userId': TEST_USER_1,
                'mediaCapabilities': {'audio': True, 'video': True}
            })
            
            await client_2.emit('join-meeting', {
                'meetingId': TEST_MEETING_ID,
                'userId': TEST_USER_2,
                'mediaCapabilities': {'audio': True, 'video': True}
            })
            
            await asyncio.sleep(0.3)
            
            # Clear events
            client_1.clear_events()
            client_2.clear_events()
            
            # Send multiple messages in sequence
            messages_to_send = [
                'First message',
                'Second message',
                'Third message',
                'Fourth message',
                'Fifth message'
            ]
            
            for msg_text in messages_to_send:
                await client_1.emit('send-chat-message', {
                    'meetingId': TEST_MEETING_ID,
                    'senderId': TEST_USER_1,
                    'senderName': 'Alice',
                    'messageText': msg_text
                })
                await asyncio.sleep(0.1)  # Small delay between messages
            
            # Wait for all messages to be delivered
            await asyncio.sleep(0.5)
            
            # Verify Client 2 received all messages in order
            messages_2 = client_2.get_events('chat-message')
            assert len(messages_2) == len(messages_to_send)
            
            for i, expected_text in enumerate(messages_to_send):
                assert messages_2[i]['data']['messageText'] == expected_text
            
        finally:
            await client_1.disconnect()
            await client_2.disconnect()


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
