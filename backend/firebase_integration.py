"""Firebase integration for caption sync and correction storage."""

from __future__ import annotations

import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class FirebaseClient:
    """
    Firebase client for Firestore and Storage operations.
    
    Gracefully handles missing Firebase configuration - app works without it.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.enabled = False
        self.db = None
        self.storage_bucket = None
        
        if config_path is None:
            config_path = "configs/firebase-credentials.json"
        
        if not os.path.exists(config_path):
            logger.info("Firebase credentials not found - running in local-only mode")
            return
        
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore, storage
            
            cred = credentials.Certificate(config_path)
            
            # Initialize app if not already initialized
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred, {
                    'storageBucket': self._get_storage_bucket(config_path)
                })
            
            self.db = firestore.client()
            self.storage_bucket = storage.bucket()
            self.enabled = True
            
            logger.info("Firebase initialized successfully")
        
        except ImportError:
            logger.warning("firebase-admin not installed - running in local-only mode")
        except Exception as exc:
            logger.error(f"Firebase initialization failed: {exc}")
    
    def _get_storage_bucket(self, config_path: str) -> str:
        """Extract storage bucket from credentials file."""
        try:
            with open(config_path, 'r') as f:
                creds = json.load(f)
                project_id = creds.get('project_id', '')
                return f"{project_id}.appspot.com"
        except Exception:
            return ""
    
    def is_connected(self) -> bool:
        """Check if Firebase is enabled and connected."""
        return self.enabled and self.db is not None
    
    # ========================================================================
    # Caption Operations
    # ========================================================================
    
    def store_caption(
        self,
        session_id: str,
        user_id: str,
        text: str,
        timestamp: float,
        is_confirmed: bool = False
    ) -> bool:
        """Store a caption in Firestore."""
        if not self.is_connected():
            return False
        
        try:
            doc_ref = self.db.collection('captions').document()
            doc_ref.set({
                'session_id': session_id,
                'user_id': user_id,
                'text': text,
                'timestamp': timestamp,
                'is_confirmed': is_confirmed,
                'created_at': datetime.now()
            })
            return True
        
        except Exception as exc:
            logger.error(f"Failed to store caption: {exc}")
            return False
    
    def get_session_captions(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Retrieve recent captions for a session."""
        if not self.is_connected():
            return []
        
        try:
            docs = (
                self.db.collection('captions')
                .where('session_id', '==', session_id)
                .order_by('timestamp', direction='DESCENDING')
                .limit(limit)
                .stream()
            )
            
            captions = []
            for doc in docs:
                data = doc.to_dict()
                captions.append(data)
            
            return list(reversed(captions))  # Return in chronological order
        
        except Exception as exc:
            logger.error(f"Failed to retrieve captions: {exc}")
            return []
    
    # ========================================================================
    # Correction Operations (for Incremental Learning)
    # ========================================================================
    
    def store_correction(
        self,
        user_id: str,
        original_text: str,
        corrected_text: str,
        landmark_sequence: Optional[List] = None,
        timestamp: float = None
    ) -> bool:
        """Store a user correction for incremental learning."""
        if not self.is_connected():
            return False
        
        if timestamp is None:
            timestamp = datetime.now().timestamp()
        
        try:
            doc_ref = self.db.collection('corrections').document()
            doc_ref.set({
                'user_id': user_id,
                'original_text': original_text,
                'corrected_text': corrected_text,
                'landmark_sequence': landmark_sequence,
                'timestamp': timestamp,
                'created_at': datetime.now(),
                'processed': False
            })
            return True
        
        except Exception as exc:
            logger.error(f"Failed to store correction: {exc}")
            return False
    
    def get_unprocessed_corrections(
        self,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve corrections that haven't been used for training yet."""
        if not self.is_connected():
            return []
        
        try:
            docs = (
                self.db.collection('corrections')
                .where('processed', '==', False)
                .limit(limit)
                .stream()
            )
            
            corrections = []
            for doc in docs:
                data = doc.to_dict()
                data['doc_id'] = doc.id
                corrections.append(data)
            
            return corrections
        
        except Exception as exc:
            logger.error(f"Failed to retrieve corrections: {exc}")
            return []
    
    def mark_corrections_processed(self, doc_ids: List[str]) -> bool:
        """Mark corrections as processed after training."""
        if not self.is_connected():
            return False
        
        try:
            batch = self.db.batch()
            
            for doc_id in doc_ids:
                doc_ref = self.db.collection('corrections').document(doc_id)
                batch.update(doc_ref, {'processed': True})
            
            batch.commit()
            return True
        
        except Exception as exc:
            logger.error(f"Failed to mark corrections as processed: {exc}")
            return False
    
    # ========================================================================
    # Session Operations
    # ========================================================================
    
    def create_session(
        self,
        session_id: str,
        participants: List[str],
        accessibility_mode: bool = False
    ) -> bool:
        """Create a new session record."""
        if not self.is_connected():
            return False
        
        try:
            doc_ref = self.db.collection('sessions').document(session_id)
            doc_ref.set({
                'session_id': session_id,
                'participants': participants,
                'accessibility_mode': accessibility_mode,
                'created_at': datetime.now(),
                'active': True
            })
            return True
        
        except Exception as exc:
            logger.error(f"Failed to create session: {exc}")
            return False
    
    def end_session(self, session_id: str) -> bool:
        """Mark a session as ended."""
        if not self.is_connected():
            return False
        
        try:
            doc_ref = self.db.collection('sessions').document(session_id)
            doc_ref.update({
                'active': False,
                'ended_at': datetime.now()
            })
            return True
        
        except Exception as exc:
            logger.error(f"Failed to end session: {exc}")
            return False
    
    # ========================================================================
    # Storage Operations
    # ========================================================================
    
    def upload_model(self, local_path: str, remote_path: str) -> bool:
        """Upload trained model to Firebase Storage."""
        if not self.is_connected() or self.storage_bucket is None:
            return False
        
        try:
            blob = self.storage_bucket.blob(remote_path)
            blob.upload_from_filename(local_path)
            logger.info(f"Uploaded model to {remote_path}")
            return True
        
        except Exception as exc:
            logger.error(f"Failed to upload model: {exc}")
            return False
    
    def download_model(self, remote_path: str, local_path: str) -> bool:
        """Download model from Firebase Storage."""
        if not self.is_connected() or self.storage_bucket is None:
            return False
        
        try:
            blob = self.storage_bucket.blob(remote_path)
            blob.download_to_filename(local_path)
            logger.info(f"Downloaded model from {remote_path}")
            return True
        
        except Exception as exc:
            logger.error(f"Failed to download model: {exc}")
            return False


# ============================================================================
# Initialization Helper
# ============================================================================

def initialize_firebase_collections(client: FirebaseClient) -> bool:
    """Initialize Firestore collections with indexes."""
    if not client.is_connected():
        logger.warning("Firebase not connected - skipping initialization")
        return False
    
    try:
        # Create sample documents to initialize collections
        # (Firestore creates collections on first write)
        
        # Captions collection
        client.db.collection('captions').document('_init').set({
            'initialized': True,
            'created_at': datetime.now()
        })
        
        # Corrections collection
        client.db.collection('corrections').document('_init').set({
            'initialized': True,
            'created_at': datetime.now()
        })
        
        # Sessions collection
        client.db.collection('sessions').document('_init').set({
            'initialized': True,
            'created_at': datetime.now()
        })
        
        logger.info("Firebase collections initialized")
        return True
    
    except Exception as exc:
        logger.error(f"Failed to initialize collections: {exc}")
        return False


# ============================================================================
# CLI for Testing
# ============================================================================

if __name__ == "__main__":
    import sys
    
    client = FirebaseClient()
    
    if "--init" in sys.argv:
        if initialize_firebase_collections(client):
            print("✓ Firebase collections initialized")
        else:
            print("✗ Failed to initialize Firebase")
            sys.exit(1)
    
    elif "--test" in sys.argv:
        if client.is_connected():
            print("✓ Firebase connected")
            
            # Test caption storage
            success = client.store_caption(
                session_id="test_session",
                user_id="test_user",
                text="Test caption",
                timestamp=datetime.now().timestamp()
            )
            print(f"{'✓' if success else '✗'} Caption storage test")
            
            # Test caption retrieval
            captions = client.get_session_captions("test_session")
            print(f"✓ Retrieved {len(captions)} captions")
        else:
            print("✗ Firebase not connected")
            sys.exit(1)
    
    else:
        print("Usage:")
        print("  python backend/firebase_integration.py --init   # Initialize collections")
        print("  python backend/firebase_integration.py --test   # Test connection")
