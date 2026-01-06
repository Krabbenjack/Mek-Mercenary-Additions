"""
Interaction Resolver - Layer 3

Responsible for:
- Loading resolution rules from interaction_resolution_*.json
- Using existing skill check system (rules/skill_roll.py)
- Executing stage-based resolution
- Producing resolution results with success/failure/margin

Does NOT:
- Apply outcomes
- Change any state
- Know about events or UI

This layer only executes mechanical resolution.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import sys

# Import existing skill check system
sys.path.insert(0, str(Path(__file__).parent.parent))
from rules.skill_roll import resolve_skill_check, SkillRollResult


@dataclass
class StageResult:
    """Result of a single resolution stage"""
    stage_id: str
    success: bool
    margin: int
    roll_result: Optional[SkillRollResult] = None
    notes: str = ""


@dataclass
class ResolutionResult:
    """
    Complete resolution result for an interaction.
    This is the output of the Interaction Resolver.
    """
    interaction_name: str
    domain: str
    stages: List[StageResult] = field(default_factory=list)
    overall_success: bool = False
    great_success: bool = False
    fumble: bool = False
    participants: List[str] = field(default_factory=list)
    
    def get_outcome_tier(self) -> str:
        """
        Determine the outcome tier for outcome application.
        
        Returns:
            "on_failure", "on_success", or "on_great_success"
        """
        if self.fumble:
            return "on_failure"
        elif self.great_success:
            return "on_great_success"
        elif self.overall_success:
            return "on_success"
        else:
            return "on_failure"


class InteractionResolver:
    """
    Interaction Resolver - executes mechanical resolution using skill checks.
    
    Loads:
    - interaction_resolution_social.json
    - interaction_resolution_operational.json
    
    Uses:
    - rules/skill_roll.py (existing skill check system)
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the interaction resolver.
        
        Args:
            config_dir: Path to config/events directory. If None, uses default location.
        """
        if config_dir is None:
            config_dir = Path(__file__).parent.parent.parent / "config" / "events"
        
        self.config_dir = config_dir
        self.resolution_profiles: Dict[str, Dict[str, Any]] = {}
        self.interaction_resolutions: Dict[str, Dict[str, Any]] = {}
        
        self._load_resolution_rules()
    
    def _load_json_with_comments(self, filepath: Path) -> Dict[str, Any]:
        """Load JSON file, stripping C-style comments"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Remove single-line comments
            lines = []
            for line in content.split('\n'):
                comment_pos = line.find('//')
                if comment_pos >= 0:
                    line = line[:comment_pos]
                lines.append(line)
            
            clean_content = '\n'.join(lines)
            
            # Remove C-style comment blocks
            while '/*' in clean_content:
                start = clean_content.find('/*')
                end = clean_content.find('*/', start)
                if end >= 0:
                    clean_content = clean_content[:start] + clean_content[end+2:]
                else:
                    break
            
            return json.loads(clean_content)
    
    def _load_resolution_rules(self):
        """Load resolution rules from interaction_resolution_*.json"""
        resolution_dir = self.config_dir / "resolution"
        
        # Load social resolution
        social_path = resolution_dir / "interaction_resolution_social.json"
        if social_path.exists():
            data = self._load_json_with_comments(social_path)
            self.resolution_profiles.update(data.get('resolution_profiles', {}))
            self.interaction_resolutions.update(data.get('interaction_resolutions', {}))
        
        # Load operational resolution
        operational_path = resolution_dir / "interaction_resolution_operational.json"
        if operational_path.exists():
            data = self._load_json_with_comments(operational_path)
            self.resolution_profiles.update(data.get('resolution_profiles', {}))
            self.interaction_resolutions.update(data.get('interaction_resolutions', {}))
    
    def get_resolution_rules(self, interaction_name: str) -> Optional[Dict[str, Any]]:
        """Get resolution rules for an interaction"""
        return self.interaction_resolutions.get(interaction_name)
    
    def _get_character_skill_level(self, character: Any, skill_name: str) -> int:
        """Get character's skill level"""
        if hasattr(character, 'skills') and skill_name in character.skills:
            return character.skills[skill_name]
        return 0
    
    def _get_character_attribute(self, character: Any, attribute_name: str) -> int:
        """Get character's attribute value"""
        if hasattr(character, 'attributes') and attribute_name in character.attributes:
            return character.attributes[attribute_name]
        return 0
    
    def _resolve_stage(
        self,
        stage_data: Dict[str, Any],
        character: Any,
        modifiers: Dict[str, float],
        target_number: int = 8
    ) -> StageResult:
        """
        Resolve a single stage of an interaction.
        
        Args:
            stage_data: Stage configuration from resolution rules
            character: Character object
            modifiers: Modifiers from environment/tone
            target_number: Base target number for the check
            
        Returns:
            StageResult containing the outcome
        """
        stage_id = stage_data.get('id', 'unknown')
        profile_name = stage_data.get('profile', '')
        profile = self.resolution_profiles.get(profile_name, {})
        
        check_type = profile.get('check_type', 'skill_or_attribute')
        
        # Determine skill or attribute to use
        primary_skill = stage_data.get('primary_skill')
        fallback_attribute = stage_data.get('fallback_attribute')
        attribute_only = stage_data.get('attribute')
        
        # Get difficulty modifiers
        difficulty_mod = 0
        difficulty_source = stage_data.get('difficulty_source', '')
        
        if difficulty_source == 'tone' and 'social' in modifiers:
            tone_data = modifiers.get('social', {})
            if isinstance(tone_data, dict):
                difficulty_mod = tone_data.get('difficulty', 0)
        elif difficulty_source == 'environment' and 'operational' in modifiers:
            env_data = modifiers.get('operational', {})
            if isinstance(env_data, dict):
                difficulty_mod = env_data.get('difficulty', 0)
        elif difficulty_source == 'tone_and_environment':
            # Combine both
            if 'social' in modifiers and isinstance(modifiers['social'], dict):
                difficulty_mod += modifiers['social'].get('difficulty', 0)
            if 'operational' in modifiers and isinstance(modifiers['operational'], dict):
                difficulty_mod += modifiers['operational'].get('difficulty', 0)
        
        # Perform the check
        if check_type == 'attribute' and attribute_only:
            # Attribute-only check
            attribute_score = self._get_character_attribute(character, attribute_only)
            
            roll_result = resolve_skill_check(
                target_number=target_number,
                trained=False,
                attribute_score=attribute_score,
                difficulty_mod=int(difficulty_mod)
            )
        
        elif check_type == 'skill_or_attribute':
            # Skill check with attribute fallback
            if primary_skill:
                skill_level = self._get_character_skill_level(character, primary_skill)
                
                if skill_level > 0:
                    # Has the skill - use it
                    attribute_mod = 0
                    if fallback_attribute:
                        attribute_mod = self._get_character_attribute(character, fallback_attribute)
                    
                    roll_result = resolve_skill_check(
                        target_number=target_number,
                        trained=True,
                        skill_level=skill_level,
                        attribute_link_mod=attribute_mod,
                        difficulty_mod=int(difficulty_mod)
                    )
                else:
                    # No skill - use attribute
                    attribute_score = 0
                    if fallback_attribute:
                        attribute_score = self._get_character_attribute(character, fallback_attribute)
                    
                    roll_result = resolve_skill_check(
                        target_number=target_number,
                        trained=False,
                        attribute_score=attribute_score,
                        difficulty_mod=int(difficulty_mod)
                    )
            elif fallback_attribute:
                # Only attribute specified
                attribute_score = self._get_character_attribute(character, fallback_attribute)
                
                roll_result = resolve_skill_check(
                    target_number=target_number,
                    trained=False,
                    attribute_score=attribute_score,
                    difficulty_mod=int(difficulty_mod)
                )
            else:
                # No skill or attribute - default check
                roll_result = resolve_skill_check(
                    target_number=target_number,
                    trained=False,
                    attribute_score=0,
                    difficulty_mod=int(difficulty_mod)
                )
        else:
            # Default check
            roll_result = resolve_skill_check(
                target_number=target_number,
                trained=False,
                attribute_score=0,
                difficulty_mod=int(difficulty_mod)
            )
        
        return StageResult(
            stage_id=stage_id,
            success=roll_result.success,
            margin=roll_result.margin,
            roll_result=roll_result,
            notes=roll_result.notes or ""
        )
    
    def resolve_interaction(
        self,
        selected_interaction: Any,
        characters: List[Any],
        target_number: int = 8
    ) -> ResolutionResult:
        """
        Resolve an interaction through all its stages.
        
        Args:
            selected_interaction: SelectedInteraction from the selector
            characters: List of Character objects (participants)
            target_number: Base target number for checks (default: 8)
            
        Returns:
            ResolutionResult containing all stage results and overall outcome
        """
        interaction_name = selected_interaction.interaction_name
        rules = self.get_resolution_rules(interaction_name)
        
        result = ResolutionResult(
            interaction_name=interaction_name,
            domain=selected_interaction.domain,
            participants=[c.id for c in characters]
        )
        
        if not rules:
            # No resolution rules - treat as automatic success
            result.overall_success = True
            return result
        
        stages = rules.get('stages', [])
        
        # Resolve each stage
        for stage_data in stages:
            # For simplicity, use first participant for single checks
            # Future: handle group checks, opposed checks, etc.
            if characters:
                character = characters[0]
                
                stage_result = self._resolve_stage(
                    stage_data,
                    character,
                    selected_interaction.modifiers,
                    target_number
                )
                
                result.stages.append(stage_result)
                
                # Check for early termination
                on_failure = stage_data.get('on_failure')
                if not stage_result.success and on_failure == 'no_interaction':
                    result.overall_success = False
                    return result
        
        # Determine overall success
        if result.stages:
            # Success if any stage succeeded (can be configured differently)
            result.overall_success = any(s.success for s in result.stages)
            
            # Great success if stunning success occurred
            result.great_success = any(
                s.roll_result and s.roll_result.stunning_success
                for s in result.stages
            )
            
            # Fumble if any stage fumbled
            result.fumble = any(
                s.roll_result and s.roll_result.fumble
                for s in result.stages
            )
        
        return result
