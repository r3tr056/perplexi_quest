from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import difflib
from dataclasses import dataclass
from enum import Enum

from app.collab.session_manager import CollaborationConflict

class ConflictType(str, Enum):
	CONCURRENT_EDIT = "concurrent_edit"
	OVERWRITE_CONFLICT = "overwrite_conflict"
	SECTION_LOCK_CONFLICT = "section_lock_conflict"
	PERMISSION_CONFLICT = "permission_conflict"

class ResolutionStrategy(str, Enum):
	MERGE_CHANGES = "merge_changes"
	USER_CHOICE = "user_choice"
	TIMESTAMP_PRIORITY = "timestamp_priority"
	ROLE_PRIORITY = "role_priority"

@dataclass
class EditDelta:
	operation: str  # "insert", "delete", "replace"
	position: int
	old_content: str
	new_content: str
	timestamp: datetime
	user_id: str

class ConflictResolver:
	def __init__(self):
		self.resolution_strategies = {
			ConflictType.CONCURRENT_EDIT: ResolutionStrategy.MERGE_CHANGES,
			ConflictType.OVERWRITE_CONFLICT: ResolutionStrategy.USER_CHOICE,
			ConflictType.SECTION_LOCK_CONFLICT: ResolutionStrategy.TIMESTAMP_PRIORITY,
			ConflictType.PERMISSION_CONFLICT: ResolutionStrategy.ROLE_PRIORITY
		}

	async def detect_conflict(
		self, 
		session_id: str, 
		section_id: str, 
		user_id: str, 
		new_edit: Dict[str, Any],
		current_state: Dict[str, Any]
	) -> Optional[CollaborationConflict]:
		concurrent_conflict = await self._detect_concurrent_edit_conflict(session_id, section_id, user_id, new_edit, current_state)
		if concurrent_conflict:
			return concurrent_conflict
		overwrite_conflict = await self._detect_overwrite_conflict(session_id, section_id, user_id, new_edit, current_state)
		if overwrite_conflict:
			return overwrite_conflict
		return None

	async def resolve_conflict(
		self, 
		conflict: CollaborationConflict,
		resolution_preference: Optional[ResolutionStrategy] = None
	) -> Dict[str, Any]:
		strategy = resolution_preference or self.resolution_strategies.get(
			ConflictType(conflict.conflict_type), 
			ResolutionStrategy.USER_CHOICE
		)
		resolution_result = {
			"conflict_id": conflict.conflict_id,
			"resolution_strategy": strategy.value,
			"timestamp": datetime.utcnow().isoformat(),
			"resolver": "r3tr056"
		}

		if strategy == ResolutionStrategy.MERGE_CHANGES:
			merged_result = await self._merge_conflicting_changes(conflict)
			resolution_result.update({
				"success": True,
				"merged_content": merged_result["merged_content"],
				"merge_metadata": merged_result["metadata"]
			})

		elif strategy == ResolutionStrategy.USER_CHOICE:
			resolution_result.update({
				"success": False,
				"requires_user_input": True,
				"conflict_options": {
					"option_1": {
						"user_id": conflict.user1_id,
						"content": conflict.content1,
						"description": "Accept changes from first user"
					},
					"option_2": {
						"user_id": conflict.user2_id,
						"content": conflict.content2,
						"description": "Accept changes from second user"
					},
					"option_3": {
						"description": "Manual merge required",
						"merge_suggestions": await self._generate_merge_suggestions(conflict)
					}
				}
			})
			
		elif strategy == ResolutionStrategy.TIMESTAMP_PRIORITY:
			if conflict.content1.get("timestamp", "") > conflict.content2.get("timestamp", ""):
				winning_content = conflict.content1
				winning_user = conflict.user1_id
			else:
				winning_content = conflict.content2
				winning_user = conflict.user2_id
			resolution_result.update({
				"success": True,
				"resolved_content": winning_content,
				"winning_user": winning_user,
				"resolution_reason": "timestamp_priority"
			})
			
		elif strategy == ResolutionStrategy.ROLE_PRIORITY:
			role_priority_result = await self._resolve_by_role_priority(conflict)
			resolution_result.update(role_priority_result)
		
		return resolution_result

	async def _merge_conflicting_changes(self, conflict: CollaborationConflict) -> Dict[str, Any]:
		content1 = conflict.content1.get("content", "")
		content2 = conflict.content2.get("content", "")

		differ = difflib.unified_diff(
			content1.splitlines(keepends=True),
			content2.splitlines(keepends=True),
			fromfile=f"user_{conflict.user1_id}",
			tofile=f"user_{conflict.user2_id}",
			lineterm=""
		)

		merge_analysis = self._analyze_changes_for_merging(content1, content2)
		if merge_analysis["can_auto_merge"]:
			merged_content = await self._perform_automatic_merge(
				content1, content2, merge_analysis
			)
			return {
				"merged_content": merged_content,
				"metadata": {
					"merge_type": "automatic",
					"confidence": merge_analysis["confidence"],
					"changes_merged": merge_analysis["mergeable_changes"],
					"merge_timestamp": datetime.utcnow().isoformat()
				}
			}
		else:
			return {
				"merged_content": None,
				"metadata": {
					"merge_type": "manual_required",
					"conflicts": merge_analysis["conflicts"],
					"suggestions": merge_analysis["suggestions"]
				}
			}

	def _analyze_changes_for_merging(self, content1: str, content2: str) -> Dict[str, Any]:
		lines1 = content1.splitlines()
		lines2 = content2.splitlines()
		matcher = difflib.SequenceMatcher(None, lines1, lines2)
		conflicts = []
		mergeable_changes = []
		
		for tag, i1, i2, j1, j2 in matcher.get_opcodes():
			if tag == 'replace':
				if self._are_changes_compatible(lines1[i1:i2], lines2[j1:j2]):
					mergeable_changes.append({
						"type": "compatible_replace",
						"original": lines1[i1:i2],
						"change1": lines1[i1:i2],
						"change2": lines2[j1:j2]
					})
				else:
					conflicts.append({
						"type": "incompatible_replace",
						"line_range": [i1, i2],
						"content1": lines1[i1:i2],
						"content2": lines2[j1:j2]
					})
			elif tag in ['insert', 'delete']:
				mergeable_changes.append({
					"type": tag,
					"content": lines2[j1:j2] if tag == 'insert' else lines1[i1:i2]
				})
		
		confidence = len(mergeable_changes) / max(len(mergeable_changes) + len(conflicts), 1)
		return {
			"can_auto_merge": len(conflicts) == 0 and confidence > 0.7,
			"confidence": confidence,
			"mergeable_changes": mergeable_changes,
			"conflicts": conflicts,
			"suggestions": self._generate_merge_suggestions_from_analysis(conflicts)
		}

	def _are_changes_compatible(self, lines1: List[str], lines2: List[str]) -> bool:
		if len(lines1) != len(lines2):
			return False
		
		for l1, l2 in zip(lines1, lines2):
			if l1.strip() and l2.strip():
				similarity = difflib.SequenceMatcher(None, l1, l2).ratio()
				if similarity < 0.5:
					return False
		return True

	async def _perform_automatic_merge(
		self, 
		content1: str, 
		content2: str, 
		merge_analysis: Dict[str, Any]
	) -> str:
		lines1 = content1.splitlines()
		lines2 = content2.splitlines()
		merged_lines = []
		matcher = difflib.SequenceMatcher(None, lines1, lines2)
		for tag, i1, i2, j1, j2 in matcher.get_opcodes():
			if tag == 'equal':
				merged_lines.extend(lines1[i1:i2])
			elif tag == 'insert':
				merged_lines.extend(lines2[j1:j2])
			elif tag == 'delete':
				pass
			elif tag == 'replace':
				merged_lines.extend(lines1[i1:i2])
				merged_lines.extend(lines2[j1:j2])
		return '\n'.join(merged_lines)

	async def _generate_merge_suggestions(self, conflict: CollaborationConflict) -> List[Dict[str, Any]]:
		suggestions = []
		suggestions.append({
			"suggestion_id": "keep_both_attributed",
			"description": "Keep both changes with user attribution",
			"preview": f"""
			[Edit by {conflict.user1_id}]: {conflict.content1.get('content', '')[:100]}...
			[Edit by {conflict.user2_id}]: {conflict.content2.get('content', '')[:100]}...
			""",
			"confidence": 0.8
		})
		suggestions.append({
			"suggestion_id": "merge_complementary",
			"description": "Merge non-conflicting parts of both changes",
			"preview": await self._create_complementary_merge_preview(conflict),
			"confidence": 0.6
		})
		quality_analysis = await self._analyze_content_quality(conflict)
		suggestions.append({
			"suggestion_id": "quality_based",
			"description": f"Choose higher quality content (User {quality_analysis['preferred_user']})",
			"preview": quality_analysis["preferred_content"][:200] + "...",
			"confidence": quality_analysis["confidence"]
		})
		return suggestions

	async def _analyze_content_quality(self, conflict: CollaborationConflict) -> Dict[str, Any]:
		content1 = conflict.content1.get("content", "")
		content2 = conflict.content2.get("content", "")
		metrics1 = self._calculate_content_metrics(content1)
		metrics2 = self._calculate_content_metrics(content2)
		
		if metrics1["overall_score"] > metrics2["overall_score"]:
			return {
				"preferred_user": conflict.user1_id,
				"preferred_content": content1,
				"confidence": abs(metrics1["overall_score"] - metrics2["overall_score"]),
				"reasoning": f"Content 1 scored {metrics1['overall_score']:.2f} vs {metrics2['overall_score']:.2f}"
			}
		else:
			return {
				"preferred_user": conflict.user2_id,
				"preferred_content": content2,
				"confidence": abs(metrics2["overall_score"] - metrics1["overall_score"]),
				"reasoning": f"Content 2 scored {metrics2['overall_score']:.2f} vs {metrics1['overall_score']:.2f}"
			}

	def _calculate_content_metrics(self, content: str) -> Dict[str, float]:
		if not content:
			return {"overall_score": 0.0}
		length_score = min(len(content) / 500, 1.0) if len(content) < 1000 else max(1.0 - (len(content) - 1000) / 2000, 0.5)
		sentences = content.count('.') + content.count('!') + content.count('?')
		words = len(content.split())
		readability_score = 0.8 if sentences > 0 and 10 <= words/max(sentences, 1) <= 25 else 0.5
		factual_indicators = ['according to', 'research shows', 'study found', '%', 'statistics']
		fact_count = sum(1 for indicator in factual_indicators if indicator in content.lower())
		density_score = min(fact_count / 3, 1.0)
		overall_score = (length_score + readability_score + density_score) / 3
		return {
			"length_score": length_score,
			"readability_score": readability_score,
			"density_score": density_score,
			"overall_score": overall_score
		}