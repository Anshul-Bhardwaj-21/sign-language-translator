# Integration Tests for Signaling Server

## Overview

The file `test_signaling_integration.py` contains integration tests for the Socket.IO signaling server. These tests validate the complete WebRTC signaling flow, participant notifications, and chat message delivery as specified in requirements 10.3 and 21.6.

## Test Coverage

### 1. WebRTC Signaling Flow (Requirement 21.6)
- **Test**: `test_offer_answer_ice_flow`
- **Validates**:
  - Offer is forwarded from peer A to peer B
  - Answer is forwarded from peer B to peer A
  - ICE candidates are exchanged bidirectionally
  - ICE connection establishment completes within 3 seconds

### 2. Participant Join Notifications (Requirement 21.6)
- **Test**: `test_participant_join_notifications`
- **Validates**:
  - Existing participants receive 'participant-joined' event
  - New participant receives list of existing participants
  - Participant data includes correct media states (audio/video enabled)

### 3. Participant Leave Notifications (Requirement 21.6)
- **Test**: `test_participant_leave_notifications`
- **Validates**:
  - Remaining participants receive 'participant-left' event
  - Session is cleaned up in Redis
  - Leaving participant receives confirmation

### 4. Public Chat Message Delivery (Requirement 10.3)
- **Test**: `test_public_chat_message_delivery`
- **Validates**:
  - Messages are delivered to all participants within 500ms
  - All participants receive the message
  - Message includes sender name and timestamp

### 5. Private Chat Message Delivery (Requirement 10.3)
- **Test**: `test_private_chat_message_delivery`
- **Validates**:
  - Only recipient and sender receive the message
  - Other participants do not receive the message
  - Message is marked as private

### 6. Multiple Chat Messages Order (Requirement 10.3)
- **Test**: `test_multiple_chat_messages_order`
- **Validates**:
  - Messages are received in the order they were sent
  - All messages are delivered successfully

## Prerequisites

These integration tests require the following services to be running:

1. **Redis** - Session state and participant management
2. **PostgreSQL** - Chat message storage
3. **Signaling Server** - Socket.IO server on port 8001

## Running the Tests

### Option 1: Using Docker Compose (Recommended)

```bash
# Start all required services
docker-compose up -d redis postgres

# Start the signaling server
python backend/signaling_server.py &

# Run the integration tests
cd backend
SKIP_INTEGRATION_TESTS=false pytest test_signaling_integration.py -v

# Stop the signaling server
kill %1  # or use Ctrl+C if running in foreground
```

### Option 2: Manual Setup

1. **Start Redis**:
   ```bash
   redis-server
   ```

2. **Start PostgreSQL**:
   ```bash
   # Using Docker
   docker run -d -p 5432:5432 \
     -e POSTGRES_USER=meeting_user \
     -e POSTGRES_PASSWORD=meeting_pass \
     -e POSTGRES_DB=meeting_db \
     postgres:15
   
   # Initialize the database schema
   python backend/database/init_db.py
   ```

3. **Start Signaling Server**:
   ```bash
   cd backend
   python signaling_server.py
   ```

4. **Run Tests** (in a new terminal):
   ```bash
   cd backend
   SKIP_INTEGRATION_TESTS=false pytest test_signaling_integration.py -v
   ```

### Option 3: Skip Integration Tests (Default)

By default, integration tests are skipped to avoid failures when services are not running:

```bash
cd backend
pytest test_signaling_integration.py -v
# All tests will be skipped with message about required services
```

## Environment Variables

- `SKIP_INTEGRATION_TESTS`: Set to `false` to run integration tests (default: `true`)
- `DATABASE_URL`: PostgreSQL connection string (default: `postgresql://meeting_user:meeting_pass@localhost:5432/meeting_db`)
- `SIGNALING_HOST`: Signaling server host (default: `0.0.0.0`)
- `SIGNALING_PORT`: Signaling server port (default: `8001`)

## Test Architecture

The integration tests use real Socket.IO client connections to test the actual signaling flow:

1. **SocketIOTestClient**: Helper class that wraps `socketio.AsyncClient`
   - Manages connection lifecycle
   - Captures all received events
   - Provides helper methods for event filtering

2. **Test Flow**:
   - Connect multiple test clients
   - Join a test meeting
   - Exchange signaling messages (offer/answer/ICE)
   - Verify events are received correctly
   - Verify timing requirements (e.g., < 500ms for chat, < 3s for ICE)
   - Clean up connections and Redis state

3. **Assertions**:
   - Event delivery and content
   - Timing constraints
   - Redis state management
   - Database persistence (for chat messages)

## Troubleshooting

### Connection Refused Errors

If you see errors like "Cannot connect to host localhost:8001":
- Ensure the signaling server is running on port 8001
- Check that no firewall is blocking the connection
- Verify the server started successfully (check logs)

### Redis Connection Errors

If you see "Error 10061 connecting to localhost:6379":
- Ensure Redis is running on port 6379
- Check Redis logs for errors
- Verify Redis is accepting connections: `redis-cli ping`

### Database Errors

If you see database connection errors:
- Ensure PostgreSQL is running on port 5432
- Verify the database schema is initialized
- Check database credentials in environment variables

### Test Timeouts

If tests timeout:
- Increase wait times in tests (currently 0.3-0.6 seconds)
- Check server logs for errors
- Verify network latency is acceptable

## CI/CD Integration

For CI/CD pipelines, you can:

1. **Skip integration tests** (default behavior):
   ```yaml
   - name: Run unit tests
     run: pytest backend/ -v
   ```

2. **Run with Docker Compose**:
   ```yaml
   - name: Start services
     run: docker-compose up -d redis postgres
   
   - name: Start signaling server
     run: python backend/signaling_server.py &
   
   - name: Run integration tests
     run: |
       cd backend
       SKIP_INTEGRATION_TESTS=false pytest test_signaling_integration.py -v
   ```

3. **Use separate test job**:
   ```yaml
   integration-tests:
     runs-on: ubuntu-latest
     services:
       redis:
         image: redis:7
         ports:
           - 6379:6379
       postgres:
         image: postgres:15
         env:
           POSTGRES_USER: meeting_user
           POSTGRES_PASSWORD: meeting_pass
           POSTGRES_DB: meeting_db
         ports:
           - 5432:5432
     steps:
       - uses: actions/checkout@v3
       - name: Run integration tests
         run: |
           python backend/signaling_server.py &
           cd backend
           SKIP_INTEGRATION_TESTS=false pytest test_signaling_integration.py -v
   ```

## Performance Benchmarks

Expected test execution times:
- `test_offer_answer_ice_flow`: < 3 seconds (validates Requirement 21.6)
- `test_participant_join_notifications`: < 2 seconds
- `test_participant_leave_notifications`: < 2 seconds
- `test_public_chat_message_delivery`: < 1 second (validates Requirement 10.3)
- `test_private_chat_message_delivery`: < 1 second
- `test_multiple_chat_messages_order`: < 2 seconds

Total suite execution time: < 15 seconds (with services running)

## Future Enhancements

Potential improvements for integration tests:

1. **Load Testing**: Test with 25+ concurrent participants (MVP requirement)
2. **Network Simulation**: Test with artificial latency and packet loss
3. **Failure Scenarios**: Test reconnection, server crashes, Redis failures
4. **Performance Monitoring**: Measure actual latency distributions
5. **End-to-End Tests**: Include frontend WebRTC client tests
