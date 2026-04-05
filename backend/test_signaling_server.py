"""
Unit tests for Socket.IO Signaling Server

Tests WebRTC signaling events, participant management, and Redis integration.

Requirements: 21.6, 23.6
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import socketio

from signaling_server import (
    app,
    broadcast_to_meeting,
    get_meeting_participants_sockets,
    get_socket_id_from_user,
    get_user_id_from_socket,
    sio,
    socket_to_user,
    user_to_socket,
)


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing."""
    with patch('signaling_server.redis_client') as mock:
        # Configure mock methods
        mock.get_session.return_value = None
        mock.set_session.return_value = True
        mock.delete_session.return_value = True
        mock.add_participant.return_value = True
        mock.remove_participant.return_value = True
        mock.get_participants.return_value = []
        mock.get_participant_count.return_value = 0
        mock.health_check.return_value = {
            'status': 'healthy',
            'latency_ms': 1.5,
            'connected': True,
        }
        yield mock


@pytest.fixture
def clear_socket_mappings():
    """Clear socket mappings before and after each test."""
    socket_to_user.clear()
    user_to_socket.clear()
    yield
    socket_to_user.clear()
    user_to_socket.clear()


class TestHelperFunctions:
    """Test helper functions for socket and user mapping."""
    
    @pytest.mark.asyncio
    async def test_get_user_id_from_socket(self, clear_socket_mappings):
        """Test retrieving user_id from socket_id."""
        socket_to_user['socket123'] = 'user456'
        
        user_id = await get_user_id_from_socket('socket123')
        assert user_id == 'user456'
        
        user_id = await get_user_id_from_socket('nonexistent')
        assert user_id is None
    
    @pytest.mark.asyncio
    async def test_get_socket_id_from_user(self, clear_socket_mappings):
        """Test retrieving socket_id from user_id."""
        user_to_socket['user456'] = 'socket123'
        
        socket_id = await get_socket_id_from_user('user456')
        assert socket_id == 'socket123'
        
        socket_id = await get_socket_id_from_user('nonexistent')
        assert socket_id is None
    
    @pytest.mark.asyncio
    async def test_get_meeting_participants_sockets(
        self,
        mock_redis_client,
        clear_socket_mappings,
    ):
        """Test retrieving all socket IDs for meeting participants."""
        # Setup
        mock_redis_client.get_participants.return_value = ['user1', 'user2', 'user3']
        user_to_socket['user1'] = 'socket1'
        user_to_socket['user2'] = 'socket2'
        # user3 not in mapping (disconnected)
        
        # Execute
        socket_ids = await get_meeting_participants_sockets('meeting123')
        
        # Verify
        assert socket_ids == ['socket1', 'socket2']
        mock_redis_client.get_participants.assert_called_once_with('meeting123')


class TestJoinMeeting:
    """Test join-meeting event handler."""
    
    @pytest.mark.asyncio
    async def test_join_meeting_success(self, mock_redis_client, clear_socket_mappings):
        """Test successful join-meeting event."""
        # Setup
        sid = 'socket123'
        data = {
            'meetingId': 'meeting456',
            'userId': 'user789',
            'mediaCapabilities': {
                'audio': True,
                'video': True,
                'screenShare': False,
            }
        }
        
        mock_redis_client.get_participants.return_value = []
        
        # Mock sio.emit
        with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
            # Import and call the handler directly
            from signaling_server import join_meeting
            await join_meeting(sid, data)
            
            # Verify socket mappings
            assert socket_to_user[sid] == 'user789'
            assert user_to_socket['user789'] == sid
            
            # Verify Redis calls
            mock_redis_client.set_session.assert_called_once()
            mock_redis_client.add_participant.assert_called_once_with(
                'meeting456',
                'user789',
            )
            
            # Verify emit was called with success response
            assert mock_emit.call_count >= 1
            
            # Find the join-meeting-success call
            success_call = None
            for call in mock_emit.call_args_list:
                if call[0][0] == 'join-meeting-success':
                    success_call = call
                    break
            
            assert success_call is not None
            assert success_call[0][1]['success'] is True
    
    @pytest.mark.asyncio
    async def test_join_meeting_missing_data(self, mock_redis_client, clear_socket_mappings):
        """Test join-meeting with missing required data."""
        sid = 'socket123'
        data = {'meetingId': 'meeting456'}  # Missing userId
        
        with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
            from signaling_server import join_meeting
            await join_meeting(sid, data)
            
            # Verify error was emitted
            error_call = None
            for call in mock_emit.call_args_list:
                if call[0][0] == 'error':
                    error_call = call
                    break
            
            assert error_call is not None
            assert 'Missing meetingId or userId' in error_call[0][1]['message']
    
    @pytest.mark.asyncio
    async def test_join_meeting_with_existing_participants(
        self,
        mock_redis_client,
        clear_socket_mappings,
    ):
        """Test joining meeting with existing participants."""
        sid = 'socket_new'
        data = {
            'meetingId': 'meeting123',
            'userId': 'user_new',
            'mediaCapabilities': {'audio': True, 'video': True}
        }
        
        # Mock existing participants
        mock_redis_client.get_participants.return_value = ['user1', 'user2']
        mock_redis_client.get_session.side_effect = lambda uid: {
            'user1': {
                'joined_at': '2024-01-01T10:00:00',
                'audio_enabled': True,
                'video_enabled': True,
                'screen_sharing': False,
            },
            'user2': {
                'joined_at': '2024-01-01T10:05:00',
                'audio_enabled': False,
                'video_enabled': True,
                'screen_sharing': False,
            },
        }.get(uid)
        
        with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
            from signaling_server import join_meeting
            await join_meeting(sid, data)
            
            # Find the success response
            success_call = None
            for call in mock_emit.call_args_list:
                if call[0][0] == 'join-meeting-success':
                    success_call = call
                    break
            
            assert success_call is not None
            participants = success_call[0][1]['participants']
            assert len(participants) == 2
            assert participants[0]['userId'] == 'user1'
            assert participants[1]['userId'] == 'user2'


class TestLeaveMeeting:
    """Test leave-meeting event handler."""
    
    @pytest.mark.asyncio
    async def test_leave_meeting_success(self, mock_redis_client, clear_socket_mappings):
        """Test successful leave-meeting event."""
        sid = 'socket123'
        user_id = 'user789'
        meeting_id = 'meeting456'
        
        # Setup mappings
        socket_to_user[sid] = user_id
        user_to_socket[user_id] = sid
        
        data = {
            'meetingId': meeting_id,
            'userId': user_id,
        }
        
        with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
            from signaling_server import leave_meeting
            await leave_meeting(sid, data)
            
            # Verify Redis calls
            mock_redis_client.remove_participant.assert_called_once_with(
                meeting_id,
                user_id,
            )
            mock_redis_client.delete_session.assert_called_once_with(user_id)
            
            # Verify mappings cleared
            assert sid not in socket_to_user
            assert user_id not in user_to_socket
            
            # Verify success response
            success_call = None
            for call in mock_emit.call_args_list:
                if call[0][0] == 'leave-meeting-success':
                    success_call = call
                    break
            
            assert success_call is not None
            assert success_call[0][1]['success'] is True


class TestWebRTCSignaling:
    """Test WebRTC signaling events (offer, answer, ice-candidate)."""
    
    @pytest.mark.asyncio
    async def test_offer_forwarding(self, mock_redis_client, clear_socket_mappings):
        """Test WebRTC offer is forwarded to target peer."""
        # Setup
        from_sid = 'socket_sender'
        to_sid = 'socket_receiver'
        from_user = 'user_sender'
        to_user = 'user_receiver'
        
        socket_to_user[from_sid] = from_user
        socket_to_user[to_sid] = to_user
        user_to_socket[from_user] = from_sid
        user_to_socket[to_user] = to_sid
        
        data = {
            'from': from_user,
            'to': to_user,
            'sdp': 'v=0\r\no=- 123456 2 IN IP4 127.0.0.1\r\n...',
        }
        
        with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
            from signaling_server import offer
            await offer(from_sid, data)
            
            # Verify offer was forwarded to target
            mock_emit.assert_called_once()
            call_args = mock_emit.call_args
            assert call_args[0][0] == 'offer'
            assert call_args[0][1]['from'] == from_user
            assert call_args[0][1]['sdp'] == data['sdp']
            assert call_args[1]['room'] == to_sid
    
    @pytest.mark.asyncio
    async def test_answer_forwarding(self, mock_redis_client, clear_socket_mappings):
        """Test WebRTC answer is forwarded to target peer."""
        from_sid = 'socket_sender'
        to_sid = 'socket_receiver'
        from_user = 'user_sender'
        to_user = 'user_receiver'
        
        socket_to_user[from_sid] = from_user
        socket_to_user[to_sid] = to_user
        user_to_socket[from_user] = from_sid
        user_to_socket[to_user] = to_sid
        
        data = {
            'from': from_user,
            'to': to_user,
            'sdp': 'v=0\r\no=- 789012 2 IN IP4 127.0.0.1\r\n...',
        }
        
        with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
            from signaling_server import answer
            await answer(from_sid, data)
            
            # Verify answer was forwarded
            mock_emit.assert_called_once()
            call_args = mock_emit.call_args
            assert call_args[0][0] == 'answer'
            assert call_args[0][1]['from'] == from_user
            assert call_args[0][1]['sdp'] == data['sdp']
            assert call_args[1]['room'] == to_sid
    
    @pytest.mark.asyncio
    async def test_ice_candidate_forwarding(self, mock_redis_client, clear_socket_mappings):
        """Test ICE candidate is forwarded to target peer."""
        from_sid = 'socket_sender'
        to_sid = 'socket_receiver'
        from_user = 'user_sender'
        to_user = 'user_receiver'
        
        socket_to_user[from_sid] = from_user
        socket_to_user[to_sid] = to_user
        user_to_socket[from_user] = from_sid
        user_to_socket[to_user] = to_sid
        
        data = {
            'from': from_user,
            'to': to_user,
            'candidate': {
                'candidate': 'candidate:1 1 UDP 2130706431 192.168.1.100 54321 typ host',
                'sdpMLineIndex': 0,
                'sdpMid': 'audio',
            },
        }
        
        with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
            from signaling_server import ice_candidate
            await ice_candidate(from_sid, data)
            
            # Verify ICE candidate was forwarded
            mock_emit.assert_called_once()
            call_args = mock_emit.call_args
            assert call_args[0][0] == 'ice-candidate'
            assert call_args[0][1]['from'] == from_user
            assert call_args[0][1]['candidate'] == data['candidate']
            assert call_args[1]['room'] == to_sid
    
    @pytest.mark.asyncio
    async def test_offer_target_not_found(self, mock_redis_client, clear_socket_mappings):
        """Test offer when target user is not connected."""
        from_sid = 'socket_sender'
        from_user = 'user_sender'
        to_user = 'user_nonexistent'
        
        socket_to_user[from_sid] = from_user
        user_to_socket[from_user] = from_sid
        
        data = {
            'from': from_user,
            'to': to_user,
            'sdp': 'v=0\r\n...',
        }
        
        with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
            from signaling_server import offer
            await offer(from_sid, data)
            
            # Verify no emit was called (target not found)
            mock_emit.assert_not_called()


class TestDisconnect:
    """Test disconnect event handler."""
    
    @pytest.mark.asyncio
    async def test_disconnect_cleans_up_session(
        self,
        mock_redis_client,
        clear_socket_mappings,
    ):
        """Test disconnect event cleans up session and broadcasts."""
        sid = 'socket123'
        user_id = 'user789'
        meeting_id = 'meeting456'
        
        # Setup
        socket_to_user[sid] = user_id
        user_to_socket[user_id] = sid
        
        mock_redis_client.get_session.return_value = {
            'meeting_id': meeting_id,
            'socket_id': sid,
        }
        mock_redis_client.get_participants.return_value = []
        
        with patch.object(sio, 'emit', new_callable=AsyncMock):
            from signaling_server import disconnect
            await disconnect(sid)
            
            # Verify cleanup
            mock_redis_client.remove_participant.assert_called_once_with(
                meeting_id,
                user_id,
            )
            mock_redis_client.delete_session.assert_called_once_with(user_id)
            
            # Verify mappings cleared
            assert sid not in socket_to_user
            assert user_id not in user_to_socket


class TestMediaControlEvents:
    """Test media control event handlers (toggle-audio, toggle-video, screen sharing)."""
    
    @pytest.mark.asyncio
    async def test_toggle_audio_enable(self, mock_redis_client, clear_socket_mappings):
        """Test enabling audio updates session and broadcasts to participants."""
        sid = 'socket123'
        user_id = 'user789'
        meeting_id = 'meeting456'
        
        # Setup session
        session = {
            'meeting_id': meeting_id,
            'socket_id': sid,
            'audio_enabled': False,
            'video_enabled': True,
            'screen_sharing': False,
        }
        mock_redis_client.get_session.return_value = session
        mock_redis_client.get_participants.return_value = [user_id]
        user_to_socket[user_id] = sid
        
        data = {
            'userId': user_id,
            'meetingId': meeting_id,
            'enabled': True,
        }
        
        with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
            from signaling_server import toggle_audio
            await toggle_audio(sid, data)
            
            # Verify session was updated
            mock_redis_client.set_session.assert_called_once()
            call_args = mock_redis_client.set_session.call_args
            updated_session = call_args[0][1]
            assert updated_session['audio_enabled'] is True
            
            # Verify broadcast to participants
            broadcast_call = None
            for call in mock_emit.call_args_list:
                if call[0][0] == 'participant-updated':
                    broadcast_call = call
                    break
            
            assert broadcast_call is not None
            assert broadcast_call[0][1]['userId'] == user_id
            assert broadcast_call[0][1]['updates']['audioEnabled'] is True
    
    @pytest.mark.asyncio
    async def test_toggle_audio_disable(self, mock_redis_client, clear_socket_mappings):
        """Test disabling audio updates session and broadcasts to participants."""
        sid = 'socket123'
        user_id = 'user789'
        meeting_id = 'meeting456'
        
        session = {
            'meeting_id': meeting_id,
            'socket_id': sid,
            'audio_enabled': True,
            'video_enabled': True,
            'screen_sharing': False,
        }
        mock_redis_client.get_session.return_value = session
        mock_redis_client.get_participants.return_value = [user_id]
        user_to_socket[user_id] = sid
        
        data = {
            'userId': user_id,
            'meetingId': meeting_id,
            'enabled': False,
        }
        
        with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
            from signaling_server import toggle_audio
            await toggle_audio(sid, data)
            
            # Verify session was updated
            call_args = mock_redis_client.set_session.call_args
            updated_session = call_args[0][1]
            assert updated_session['audio_enabled'] is False
    
    @pytest.mark.asyncio
    async def test_toggle_video_enable(self, mock_redis_client, clear_socket_mappings):
        """Test enabling video updates session and broadcasts to participants."""
        sid = 'socket123'
        user_id = 'user789'
        meeting_id = 'meeting456'
        
        session = {
            'meeting_id': meeting_id,
            'socket_id': sid,
            'audio_enabled': True,
            'video_enabled': False,
            'screen_sharing': False,
        }
        mock_redis_client.get_session.return_value = session
        mock_redis_client.get_participants.return_value = [user_id]
        user_to_socket[user_id] = sid
        
        data = {
            'userId': user_id,
            'meetingId': meeting_id,
            'enabled': True,
        }
        
        with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
            from signaling_server import toggle_video
            await toggle_video(sid, data)
            
            # Verify session was updated
            call_args = mock_redis_client.set_session.call_args
            updated_session = call_args[0][1]
            assert updated_session['video_enabled'] is True
            
            # Verify broadcast
            broadcast_call = None
            for call in mock_emit.call_args_list:
                if call[0][0] == 'participant-updated':
                    broadcast_call = call
                    break
            
            assert broadcast_call is not None
            assert broadcast_call[0][1]['updates']['videoEnabled'] is True
    
    @pytest.mark.asyncio
    async def test_toggle_video_disable(self, mock_redis_client, clear_socket_mappings):
        """Test disabling video updates session and broadcasts to participants."""
        sid = 'socket123'
        user_id = 'user789'
        meeting_id = 'meeting456'
        
        session = {
            'meeting_id': meeting_id,
            'socket_id': sid,
            'audio_enabled': True,
            'video_enabled': True,
            'screen_sharing': False,
        }
        mock_redis_client.get_session.return_value = session
        mock_redis_client.get_participants.return_value = [user_id]
        user_to_socket[user_id] = sid
        
        data = {
            'userId': user_id,
            'meetingId': meeting_id,
            'enabled': False,
        }
        
        with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
            from signaling_server import toggle_video
            await toggle_video(sid, data)
            
            # Verify session was updated
            call_args = mock_redis_client.set_session.call_args
            updated_session = call_args[0][1]
            assert updated_session['video_enabled'] is False
    
    @pytest.mark.asyncio
    async def test_start_screen_share_success(self, mock_redis_client, clear_socket_mappings):
        """Test starting screen share when no one else is sharing."""
        sid = 'socket123'
        user_id = 'user789'
        meeting_id = 'meeting456'
        
        session = {
            'meeting_id': meeting_id,
            'socket_id': sid,
            'audio_enabled': True,
            'video_enabled': True,
            'screen_sharing': False,
        }
        mock_redis_client.get_session.return_value = session
        mock_redis_client.get_participants.return_value = [user_id]
        user_to_socket[user_id] = sid
        
        data = {
            'userId': user_id,
            'meetingId': meeting_id,
        }
        
        with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
            from signaling_server import start_screen_share
            await start_screen_share(sid, data)
            
            # Verify session was updated
            call_args = mock_redis_client.set_session.call_args
            updated_session = call_args[0][1]
            assert updated_session['screen_sharing'] is True
            
            # Verify broadcast
            broadcast_call = None
            for call in mock_emit.call_args_list:
                if call[0][0] == 'participant-updated':
                    broadcast_call = call
                    break
            
            assert broadcast_call is not None
            assert broadcast_call[0][1]['updates']['screenSharing'] is True
    
    @pytest.mark.asyncio
    async def test_start_screen_share_already_sharing(
        self,
        mock_redis_client,
        clear_socket_mappings,
    ):
        """Test starting screen share when another participant is already sharing."""
        sid = 'socket123'
        user_id = 'user789'
        other_user_id = 'user_other'
        meeting_id = 'meeting456'
        
        # Setup: other user is already screen sharing
        mock_redis_client.get_participants.return_value = [user_id, other_user_id]
        
        def get_session_side_effect(uid):
            if uid == user_id:
                return {
                    'meeting_id': meeting_id,
                    'socket_id': sid,
                    'screen_sharing': False,
                }
            elif uid == other_user_id:
                return {
                    'meeting_id': meeting_id,
                    'socket_id': 'socket_other',
                    'screen_sharing': True,  # Already sharing
                }
            return None
        
        mock_redis_client.get_session.side_effect = get_session_side_effect
        
        data = {
            'userId': user_id,
            'meetingId': meeting_id,
        }
        
        with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
            from signaling_server import start_screen_share
            await start_screen_share(sid, data)
            
            # Verify error was emitted
            error_call = None
            for call in mock_emit.call_args_list:
                if call[0][0] == 'error':
                    error_call = call
                    break
            
            assert error_call is not None
            assert 'Another participant is already screen sharing' in error_call[0][1]['message']
            assert error_call[0][1]['code'] == 'SCREEN_SHARE_IN_PROGRESS'
            
            # Verify session was NOT updated
            mock_redis_client.set_session.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_stop_screen_share(self, mock_redis_client, clear_socket_mappings):
        """Test stopping screen share updates session and broadcasts."""
        sid = 'socket123'
        user_id = 'user789'
        meeting_id = 'meeting456'
        
        session = {
            'meeting_id': meeting_id,
            'socket_id': sid,
            'audio_enabled': True,
            'video_enabled': True,
            'screen_sharing': True,
        }
        mock_redis_client.get_session.return_value = session
        mock_redis_client.get_participants.return_value = [user_id]
        user_to_socket[user_id] = sid
        
        data = {
            'userId': user_id,
            'meetingId': meeting_id,
        }
        
        with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
            from signaling_server import stop_screen_share
            await stop_screen_share(sid, data)
            
            # Verify session was updated
            call_args = mock_redis_client.set_session.call_args
            updated_session = call_args[0][1]
            assert updated_session['screen_sharing'] is False
            
            # Verify broadcast
            broadcast_call = None
            for call in mock_emit.call_args_list:
                if call[0][0] == 'participant-updated':
                    broadcast_call = call
                    break
            
            assert broadcast_call is not None
            assert broadcast_call[0][1]['updates']['screenSharing'] is False
    
    @pytest.mark.asyncio
    async def test_toggle_audio_missing_data(self, mock_redis_client, clear_socket_mappings):
        """Test toggle-audio with missing required data."""
        sid = 'socket123'
        data = {'userId': 'user789'}  # Missing meetingId
        
        with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
            from signaling_server import toggle_audio
            await toggle_audio(sid, data)
            
            # Verify error was emitted
            error_call = None
            for call in mock_emit.call_args_list:
                if call[0][0] == 'error':
                    error_call = call
                    break
            
            assert error_call is not None
            assert 'Missing userId or meetingId' in error_call[0][1]['message']
    
    @pytest.mark.asyncio
    async def test_toggle_audio_session_not_found(
        self,
        mock_redis_client,
        clear_socket_mappings,
    ):
        """Test toggle-audio when session is not found."""
        sid = 'socket123'
        data = {
            'userId': 'user789',
            'meetingId': 'meeting456',
            'enabled': True,
        }
        
        mock_redis_client.get_session.return_value = None
        
        with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
            from signaling_server import toggle_audio
            await toggle_audio(sid, data)
            
            # Verify error was emitted
            error_call = None
            for call in mock_emit.call_args_list:
                if call[0][0] == 'error':
                    error_call = call
                    break
            
            assert error_call is not None
            assert 'Session not found' in error_call[0][1]['message']


class TestChatAndReactions:
    """Test chat and reactions event handlers."""
    
    @pytest.mark.asyncio
    async def test_send_chat_message_public(self, mock_redis_client, clear_socket_mappings):
        """Test sending a public chat message to all participants."""
        sid = 'socket123'
        sender_id = 'user789'
        meeting_id = 'meeting456'
        
        # Setup socket mappings for multiple participants
        user_to_socket[sender_id] = sid
        user_to_socket['user2'] = 'socket2'
        user_to_socket['user3'] = 'socket3'
        mock_redis_client.get_participants.return_value = [sender_id, 'user2', 'user3']
        
        data = {
            'meetingId': meeting_id,
            'senderId': sender_id,
            'senderName': 'John Doe',
            'messageText': 'Hello everyone!',
        }
        
        with patch('signaling_server.get_db_connection') as mock_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_db.return_value = mock_conn
            
            with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
                from signaling_server import send_chat_message
                await send_chat_message(sid, data)
                
                # Verify database insert
                mock_cursor.execute.assert_called_once()
                call_args = mock_cursor.execute.call_args[0]
                assert 'INSERT INTO chat_messages' in call_args[0]
                assert call_args[1][1] == meeting_id  # meeting_id
                assert call_args[1][2] == sender_id  # sender_id
                assert call_args[1][3] is None  # recipient_id (public message)
                assert call_args[1][4] == 'Hello everyone!'  # message_text
                assert call_args[1][6] is False  # is_private
                
                mock_conn.commit.assert_called_once()
                
                # Verify broadcast to all participants
                chat_message_calls = [
                    call for call in mock_emit.call_args_list
                    if call[0][0] == 'chat-message'
                ]
                assert len(chat_message_calls) >= 1
                
                # Check message payload
                message_payload = chat_message_calls[0][0][1]
                assert message_payload['meetingId'] == meeting_id
                assert message_payload['senderId'] == sender_id
                assert message_payload['senderName'] == 'John Doe'
                assert message_payload['messageText'] == 'Hello everyone!'
                assert message_payload['isPrivate'] is False
    
    @pytest.mark.asyncio
    async def test_send_chat_message_private(self, mock_redis_client, clear_socket_mappings):
        """Test sending a private chat message to a specific participant."""
        sid = 'socket_sender'
        sender_id = 'user_sender'
        recipient_id = 'user_recipient'
        meeting_id = 'meeting456'
        
        # Setup socket mappings
        user_to_socket[sender_id] = sid
        user_to_socket[recipient_id] = 'socket_recipient'
        
        data = {
            'meetingId': meeting_id,
            'senderId': sender_id,
            'senderName': 'Alice',
            'messageText': 'Private message for you',
            'recipientId': recipient_id,
        }
        
        with patch('signaling_server.get_db_connection') as mock_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_db.return_value = mock_conn
            
            with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
                from signaling_server import send_chat_message
                await send_chat_message(sid, data)
                
                # Verify database insert with recipient_id
                call_args = mock_cursor.execute.call_args[0]
                assert call_args[1][3] == recipient_id  # recipient_id
                assert call_args[1][6] is True  # is_private
                
                # Verify message sent to recipient and sender only
                chat_message_calls = [
                    call for call in mock_emit.call_args_list
                    if call[0][0] == 'chat-message'
                ]
                assert len(chat_message_calls) == 2  # To recipient and back to sender
                
                # Check message payload includes recipientId
                message_payload = chat_message_calls[0][0][1]
                assert message_payload['isPrivate'] is True
                assert message_payload['recipientId'] == recipient_id
    
    @pytest.mark.asyncio
    async def test_send_chat_message_missing_data(self, mock_redis_client, clear_socket_mappings):
        """Test sending chat message with missing required fields."""
        sid = 'socket123'
        data = {
            'meetingId': 'meeting456',
            'senderId': 'user789',
            # Missing senderName and messageText
        }
        
        with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
            from signaling_server import send_chat_message
            await send_chat_message(sid, data)
            
            # Verify error was emitted
            error_call = None
            for call in mock_emit.call_args_list:
                if call[0][0] == 'error':
                    error_call = call
                    break
            
            assert error_call is not None
            assert 'Missing required fields' in error_call[0][1]['message']
    
    @pytest.mark.asyncio
    async def test_raise_hand(self, mock_redis_client, clear_socket_mappings):
        """Test raising hand broadcasts to all participants."""
        sid = 'socket123'
        user_id = 'user789'
        meeting_id = 'meeting456'
        
        # Setup socket mappings for multiple participants
        user_to_socket[user_id] = sid
        user_to_socket['user2'] = 'socket2'
        mock_redis_client.get_participants.return_value = [user_id, 'user2']
        
        data = {
            'userId': user_id,
            'userName': 'John Doe',
            'meetingId': meeting_id,
            'raised': True,
        }
        
        with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
            from signaling_server import raise_hand
            await raise_hand(sid, data)
            
            # Verify broadcast to all participants
            hand_raised_calls = [
                call for call in mock_emit.call_args_list
                if call[0][0] == 'hand-raised'
            ]
            assert len(hand_raised_calls) >= 1
            
            # Check payload
            payload = hand_raised_calls[0][0][1]
            assert payload['userId'] == user_id
            assert payload['userName'] == 'John Doe'
            assert payload['raised'] is True
            assert 'timestamp' in payload
    
    @pytest.mark.asyncio
    async def test_lower_hand(self, mock_redis_client, clear_socket_mappings):
        """Test lowering hand broadcasts to all participants."""
        sid = 'socket123'
        user_id = 'user789'
        meeting_id = 'meeting456'
        
        user_to_socket[user_id] = sid
        mock_redis_client.get_participants.return_value = [user_id]
        
        data = {
            'userId': user_id,
            'userName': 'John Doe',
            'meetingId': meeting_id,
            'raised': False,
        }
        
        with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
            from signaling_server import raise_hand
            await raise_hand(sid, data)
            
            # Verify broadcast
            hand_raised_calls = [
                call for call in mock_emit.call_args_list
                if call[0][0] == 'hand-raised'
            ]
            assert len(hand_raised_calls) >= 1
            
            payload = hand_raised_calls[0][0][1]
            assert payload['raised'] is False
    
    @pytest.mark.asyncio
    async def test_raise_hand_missing_data(self, mock_redis_client, clear_socket_mappings):
        """Test raising hand with missing required fields."""
        sid = 'socket123'
        data = {
            'userId': 'user789',
            # Missing userName and meetingId
        }
        
        with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
            from signaling_server import raise_hand
            await raise_hand(sid, data)
            
            # Verify error was emitted
            error_call = None
            for call in mock_emit.call_args_list:
                if call[0][0] == 'error':
                    error_call = call
                    break
            
            assert error_call is not None
            assert 'Missing required fields' in error_call[0][1]['message']
    
    @pytest.mark.asyncio
    async def test_send_reaction_valid(self, mock_redis_client, clear_socket_mappings):
        """Test sending a valid reaction broadcasts to all participants."""
        sid = 'socket123'
        user_id = 'user789'
        meeting_id = 'meeting456'
        
        user_to_socket[user_id] = sid
        user_to_socket['user2'] = 'socket2'
        mock_redis_client.get_participants.return_value = [user_id, 'user2']
        
        # Test each valid reaction
        valid_reactions = ['thumbs-up', 'clapping', 'heart', 'thinking', 'laughing']
        
        for reaction in valid_reactions:
            data = {
                'userId': user_id,
                'userName': 'John Doe',
                'meetingId': meeting_id,
                'reaction': reaction,
            }
            
            with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
                from signaling_server import send_reaction
                await send_reaction(sid, data)
                
                # Verify broadcast
                reaction_calls = [
                    call for call in mock_emit.call_args_list
                    if call[0][0] == 'reaction'
                ]
                assert len(reaction_calls) >= 1
                
                # Check payload
                payload = reaction_calls[0][0][1]
                assert payload['userId'] == user_id
                assert payload['userName'] == 'John Doe'
                assert payload['reaction'] == reaction
                assert 'timestamp' in payload
    
    @pytest.mark.asyncio
    async def test_send_reaction_invalid(self, mock_redis_client, clear_socket_mappings):
        """Test sending an invalid reaction returns error."""
        sid = 'socket123'
        user_id = 'user789'
        meeting_id = 'meeting456'
        
        data = {
            'userId': user_id,
            'userName': 'John Doe',
            'meetingId': meeting_id,
            'reaction': 'invalid-reaction',
        }
        
        with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
            from signaling_server import send_reaction
            await send_reaction(sid, data)
            
            # Verify error was emitted
            error_call = None
            for call in mock_emit.call_args_list:
                if call[0][0] == 'error':
                    error_call = call
                    break
            
            assert error_call is not None
            assert 'Invalid reaction' in error_call[0][1]['message']
    
    @pytest.mark.asyncio
    async def test_send_reaction_missing_data(self, mock_redis_client, clear_socket_mappings):
        """Test sending reaction with missing required fields."""
        sid = 'socket123'
        data = {
            'userId': 'user789',
            'meetingId': 'meeting456',
            # Missing userName and reaction
        }
        
        with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
            from signaling_server import send_reaction
            await send_reaction(sid, data)
            
            # Verify error was emitted
            error_call = None
            for call in mock_emit.call_args_list:
                if call[0][0] == 'error':
                    error_call = call
                    break
            
            assert error_call is not None
            assert 'Missing required fields' in error_call[0][1]['message']


class TestHealthCheck:
    """Test health check endpoint."""
    
    @pytest.mark.asyncio
    async def test_health_check_healthy(self, mock_redis_client):
        """Test health check when Redis is healthy."""
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'signaling-server'
        assert 'redis' in data
    
    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, mock_redis_client):
        """Test health check when Redis is unhealthy."""
        from fastapi.testclient import TestClient
        
        mock_redis_client.health_check.return_value = {
            'status': 'unhealthy',
            'error': 'connection_failed',
        }
        
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'unhealthy'
        assert data['redis']['status'] == 'unhealthy'
