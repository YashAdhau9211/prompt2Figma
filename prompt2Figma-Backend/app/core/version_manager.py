# app/core/version_manager.py
"""
Version management for the Stateful Iterative Design Engine.
Handles version tracking, diff calculation, and performance optimization.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import hashlib

from app.core.models import DesignState, SessionMetrics, EditType
from app.core.state_store import RedisStateStore

logger = logging.getLogger(__name__)


@dataclass
class VersionMetadata:
    """Metadata for a design version."""
    version: int
    created_at: datetime
    changes_summary: str
    edit_type: EditType
    target_elements: List[str]
    processing_time_ms: int
    content_hash: str
    compressed: bool = False


@dataclass
class VersionDiff:
    """Represents differences between two versions."""
    from_version: int
    to_version: int
    added_elements: List[Dict[str, Any]]
    removed_elements: List[Dict[str, Any]]
    modified_elements: List[Dict[str, Any]]
    metadata_changes: Dict[str, Any]
    summary: str


class VersionManager:
    """
    Manages version tracking, diff calculation, and compression for design states.
    
    Responsibilities:
    - Create and track design state versions
    - Calculate diffs between versions
    - Compress old versions for performance
    - Maintain version integrity and metadata
    """
    
    def __init__(self, state_store: RedisStateStore):
        self.state_store = state_store
        self.compression_threshold = 10  # Compress versions older than 10
        self.max_versions_per_session = 50  # Keep max 50 versions
    
    async def create_version(
        self, 
        session_id: str, 
        wireframe_json: Dict[str, Any],
        changes: Dict[str, Any], 
        metadata: Dict[str, Any]
    ) -> int:
        """
        Create a new version of the design state.
        
        Args:
            session_id: The session identifier
            wireframe_json: The complete wireframe JSON
            changes: Dictionary describing what changed
            metadata: Additional metadata for this version
            
        Returns:
            The new version number
        """
        try:
            # Get current session metadata to determine next version
            session_metadata = await self.state_store.get_session_metadata(session_id)
            if not session_metadata:
                raise ValueError(f"Session {session_id} not found")
            
            new_version = session_metadata.current_version + 1
            
            # Create content hash for integrity checking
            content_hash = self._calculate_content_hash(wireframe_json)
            
            # Create design state
            design_state = DesignState(
                wireframe_json=wireframe_json,
                metadata={
                    **metadata,
                    "changes": changes,
                    "content_hash": content_hash,
                    "edit_type": changes.get("edit_type", "modify"),
                    "target_elements": changes.get("target_elements", []),
                    "processing_time_ms": changes.get("processing_time_ms", 0)
                },
                created_at=datetime.utcnow(),
                version=new_version
            )
            
            # Store the design state
            success = await self.state_store.store_design_state(
                session_id, new_version, design_state
            )
            
            if not success:
                raise RuntimeError(f"Failed to store design state for version {new_version}")
            
            # Store version metadata separately for quick access
            await self._store_version_metadata(session_id, new_version, design_state, changes)
            
            # Check if we need to compress old versions
            await self._check_and_compress_versions(session_id)
            
            logger.info(f"Created version {new_version} for session {session_id}")
            return new_version
            
        except Exception as e:
            logger.error(f"Failed to create version for session {session_id}: {e}")
            raise
    
    async def get_version_diff(
        self, 
        session_id: str, 
        from_version: int, 
        to_version: int
    ) -> Optional[VersionDiff]:
        """
        Calculate the differences between two versions.
        
        Args:
            session_id: The session identifier
            from_version: Starting version number
            to_version: Ending version number
            
        Returns:
            VersionDiff object or None if versions not found
        """
        try:
            # Get both design states
            from_state = await self.state_store.get_design_state(session_id, from_version)
            to_state = await self.state_store.get_design_state(session_id, to_version)
            
            if not from_state or not to_state:
                logger.warning(f"Could not find versions {from_version} or {to_version} for session {session_id}")
                return None
            
            # Calculate differences
            diff = self._calculate_diff(from_state, to_state)
            
            return VersionDiff(
                from_version=from_version,
                to_version=to_version,
                added_elements=diff["added"],
                removed_elements=diff["removed"],
                modified_elements=diff["modified"],
                metadata_changes=diff["metadata_changes"],
                summary=diff["summary"]
            )
            
        except Exception as e:
            logger.error(f"Failed to calculate diff between versions {from_version}-{to_version}: {e}")
            return None
    
    async def get_version_metadata(self, session_id: str, version: int) -> Optional[VersionMetadata]:
        """Get metadata for a specific version."""
        try:
            metadata_key = f"session:{session_id}:version_metadata:v{version}"
            data = await self.state_store.redis.hgetall(metadata_key)
            
            if not data:
                return None
            
            return VersionMetadata(
                version=int(data["version"]),
                created_at=datetime.fromisoformat(data["created_at"]),
                changes_summary=data["changes_summary"],
                edit_type=EditType(data["edit_type"]),
                target_elements=json.loads(data["target_elements"]),
                processing_time_ms=int(data["processing_time_ms"]),
                content_hash=data["content_hash"],
                compressed=data.get("compressed", "false").lower() == "true"
            )
            
        except Exception as e:
            logger.error(f"Failed to get version metadata {session_id} v{version}: {e}")
            return None
    
    async def compress_old_versions(self, session_id: str, keep_recent: int = 10) -> int:
        """
        Compress old versions to save space while preserving essential data.
        
        Args:
            session_id: The session identifier
            keep_recent: Number of recent versions to keep uncompressed
            
        Returns:
            Number of versions compressed
        """
        try:
            # Get all versions for the session
            all_versions = await self.state_store.get_all_versions(session_id)
            
            if len(all_versions) <= keep_recent:
                return 0  # Nothing to compress
            
            # Sort versions and identify which ones to compress
            all_versions.sort(reverse=True)  # Newest first
            versions_to_compress = all_versions[keep_recent:]
            
            compressed_count = 0
            
            for version in versions_to_compress:
                # Check if already compressed
                metadata = await self.get_version_metadata(session_id, version)
                if metadata and metadata.compressed:
                    continue
                
                # Get the full state
                state = await self.state_store.get_design_state(session_id, version)
                if not state:
                    continue
                
                # Create compressed version (keep only essential data)
                compressed_state = self._create_compressed_state(state)
                
                # Store compressed version
                success = await self.state_store.store_design_state(
                    session_id, version, compressed_state
                )
                
                if success:
                    # Update metadata to mark as compressed
                    await self._mark_version_compressed(session_id, version)
                    compressed_count += 1
                    logger.info(f"Compressed version {version} for session {session_id}")
            
            return compressed_count
            
        except Exception as e:
            logger.error(f"Failed to compress versions for session {session_id}: {e}")
            return 0
    
    async def calculate_session_metrics(self, session_id: str) -> Optional[SessionMetrics]:
        """Calculate comprehensive metrics for a session."""
        try:
            session_metadata = await self.state_store.get_session_metadata(session_id)
            if not session_metadata:
                return None
            
            # Get all version metadata
            all_versions = await self.state_store.get_all_versions(session_id)
            
            total_edits = len(all_versions) - 1  # Subtract initial version
            session_duration = (
                session_metadata.last_activity - session_metadata.created_at
            ).total_seconds() / 60  # Convert to minutes
            
            # Calculate edit type distribution and processing times
            edit_types_distribution = {}
            processing_times = []
            
            for version in all_versions[1:]:  # Skip initial version
                metadata = await self.get_version_metadata(session_id, version)
                if metadata:
                    edit_type = metadata.edit_type
                    edit_types_distribution[edit_type] = edit_types_distribution.get(edit_type, 0) + 1
                    processing_times.append(metadata.processing_time_ms)
            
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            
            return SessionMetrics(
                total_edits=total_edits,
                session_duration_minutes=int(session_duration),
                edit_types_distribution=edit_types_distribution,
                average_processing_time_ms=avg_processing_time
            )
            
        except Exception as e:
            logger.error(f"Failed to calculate session metrics for {session_id}: {e}")
            return None
    
    async def verify_version_integrity(self, session_id: str, version: int) -> bool:
        """Verify the integrity of a version using content hash."""
        try:
            state = await self.state_store.get_design_state(session_id, version)
            if not state:
                return False
            
            # Calculate current hash
            current_hash = self._calculate_content_hash(state.wireframe_json)
            
            # Get stored hash from metadata
            stored_hash = state.metadata.get("content_hash")
            
            if not stored_hash:
                logger.warning(f"No content hash found for version {version}")
                return False
            
            is_valid = current_hash == stored_hash
            if not is_valid:
                logger.error(f"Content hash mismatch for version {version}: {current_hash} != {stored_hash}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Failed to verify integrity for version {version}: {e}")
            return False
    
    # Private helper methods
    
    def _calculate_content_hash(self, wireframe_json: Dict[str, Any]) -> str:
        """Calculate SHA-256 hash of wireframe content for integrity checking."""
        content_str = json.dumps(wireframe_json, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    async def _store_version_metadata(
        self, 
        session_id: str, 
        version: int, 
        design_state: DesignState,
        changes: Dict[str, Any]
    ):
        """Store version metadata separately for quick access."""
        try:
            metadata_key = f"session:{session_id}:version_metadata:v{version}"
            
            metadata_data = {
                "version": version,
                "created_at": design_state.created_at.isoformat(),
                "changes_summary": changes.get("summary", ""),
                "edit_type": changes.get("edit_type", "modify"),
                "target_elements": json.dumps(changes.get("target_elements", [])),
                "processing_time_ms": changes.get("processing_time_ms", 0),
                "content_hash": design_state.metadata.get("content_hash", ""),
                "compressed": "false"
            }
            
            await self.state_store.redis.hset(metadata_key, mapping=metadata_data)
            await self.state_store.redis.expire(metadata_key, self.state_store.session_ttl)
            
        except Exception as e:
            logger.error(f"Failed to store version metadata: {e}")
    
    def _calculate_diff(self, from_state: DesignState, to_state: DesignState) -> Dict[str, Any]:
        """Calculate detailed differences between two design states."""
        from_elements = from_state.wireframe_json.get("elements", [])
        to_elements = to_state.wireframe_json.get("elements", [])
        
        # Create lookup dictionaries by element ID
        from_lookup = {elem.get("id"): elem for elem in from_elements if elem.get("id")}
        to_lookup = {elem.get("id"): elem for elem in to_elements if elem.get("id")}
        
        added = []
        removed = []
        modified = []
        
        # Find added elements
        for elem_id, elem in to_lookup.items():
            if elem_id not in from_lookup:
                added.append(elem)
        
        # Find removed elements
        for elem_id, elem in from_lookup.items():
            if elem_id not in to_lookup:
                removed.append(elem)
        
        # Find modified elements
        for elem_id in set(from_lookup.keys()) & set(to_lookup.keys()):
            from_elem = from_lookup[elem_id]
            to_elem = to_lookup[elem_id]
            
            if from_elem != to_elem:
                modified.append({
                    "id": elem_id,
                    "from": from_elem,
                    "to": to_elem
                })
        
        # Calculate metadata changes
        metadata_changes = {}
        for key in set(from_state.metadata.keys()) | set(to_state.metadata.keys()):
            from_val = from_state.metadata.get(key)
            to_val = to_state.metadata.get(key)
            if from_val != to_val:
                metadata_changes[key] = {"from": from_val, "to": to_val}
        
        # Generate summary
        summary_parts = []
        if added:
            summary_parts.append(f"{len(added)} elements added")
        if removed:
            summary_parts.append(f"{len(removed)} elements removed")
        if modified:
            summary_parts.append(f"{len(modified)} elements modified")
        
        summary = ", ".join(summary_parts) if summary_parts else "No changes detected"
        
        return {
            "added": added,
            "removed": removed,
            "modified": modified,
            "metadata_changes": metadata_changes,
            "summary": summary
        }
    
    def _create_compressed_state(self, state: DesignState) -> DesignState:
        """Create a compressed version of a design state."""
        # For compression, we keep essential structure but remove detailed styling
        compressed_wireframe = {
            "elements": [],
            "layout": state.wireframe_json.get("layout", {}),
            "compressed": True
        }
        
        # Keep only essential element data
        for element in state.wireframe_json.get("elements", []):
            compressed_element = {
                "id": element.get("id"),
                "type": element.get("type"),
                "position": element.get("position"),
                "size": element.get("size"),
                # Remove detailed styling, animations, etc.
            }
            compressed_wireframe["elements"].append(compressed_element)
        
        # Create compressed metadata
        compressed_metadata = {
            **state.metadata,
            "compressed": True,
            "original_size": len(json.dumps(state.wireframe_json))
        }
        
        return DesignState(
            wireframe_json=compressed_wireframe,
            metadata=compressed_metadata,
            created_at=state.created_at,
            version=state.version
        )
    
    async def _mark_version_compressed(self, session_id: str, version: int):
        """Mark a version as compressed in its metadata."""
        try:
            metadata_key = f"session:{session_id}:version_metadata:v{version}"
            await self.state_store.redis.hset(metadata_key, "compressed", "true")
        except Exception as e:
            logger.error(f"Failed to mark version {version} as compressed: {e}")
    
    async def _check_and_compress_versions(self, session_id: str):
        """Check if we need to compress old versions based on thresholds."""
        try:
            all_versions = await self.state_store.get_all_versions(session_id)
            
            # If we have more than max versions, compress old ones
            if len(all_versions) > self.max_versions_per_session:
                await self.compress_old_versions(session_id, self.compression_threshold)
                
        except Exception as e:
            logger.error(f"Failed to check compression for session {session_id}: {e}")