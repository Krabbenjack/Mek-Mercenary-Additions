"""
Interaction Selector - Layer 2

Responsible for:
- Loading interaction definitions (social and operational)
- Loading environment modifiers
- Loading tone modifiers
- Selecting interactions based on weighted probabilities
- Applying context modifiers

Does NOT:
- Perform mechanical resolution
- Apply outcomes
- Change any state
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import random


@dataclass
class InteractionDefinition:
    """Definition of an interaction from interactions_*.json"""
    name: str
    domain: str  # "social" or "operational"
    roll_type: str
    participants: Dict[str, Any]
    description: str = ""
    base_weight: float = 1.0


@dataclass
class SelectedInteraction:
    """
    A selected interaction ready for resolution.
    This is the output of the Interaction Selector.
    """
    interaction_name: str
    domain: str
    roll_type: str
    participants: List[str]  # character IDs
    environment: Optional[str] = None
    tone: Optional[str] = None
    modifiers: Dict[str, float] = field(default_factory=dict)


class InteractionSelector:
    """
    Interaction Selector - selects interactions based on event context.
    
    Loads:
    - interactions_social.json
    - interactions_operational.json
    - event_environment_list.json
    - interactions_Tones.json
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the interaction selector.
        
        Args:
            config_dir: Path to config/events directory. If None, uses default location.
        """
        if config_dir is None:
            config_dir = Path(__file__).parent.parent.parent / "config" / "events"
        
        self.config_dir = config_dir
        self.interactions: Dict[str, InteractionDefinition] = {}
        self.environments: Dict[str, Dict[str, Any]] = {}
        self.tones: Dict[str, Dict[str, Any]] = {}
        
        self._load_interactions()
        self._load_environments()
        self._load_tones()
    
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
    
    def _load_interactions(self):
        """Load interaction definitions from interactions_*.json"""
        context_dir = self.config_dir / "context"
        
        # Load social interactions
        social_path = context_dir / "interactions_social.json"
        if social_path.exists():
            data = self._load_json_with_comments(social_path)
            domain = data.get('interaction_domain', 'social')
            
            for name, interaction_data in data.get('interactions', {}).items():
                self.interactions[name] = InteractionDefinition(
                    name=name,
                    domain=domain,
                    roll_type=interaction_data.get('roll_type', 'single'),
                    participants=interaction_data.get('participants', {}),
                    description=interaction_data.get('description', ''),
                    base_weight=1.0
                )
        
        # Load operational interactions
        operational_path = context_dir / "interactions_operational.json"
        if operational_path.exists():
            data = self._load_json_with_comments(operational_path)
            domain = data.get('interaction_domain', 'operational')
            
            for name, interaction_data in data.get('interactions', {}).items():
                self.interactions[name] = InteractionDefinition(
                    name=name,
                    domain=domain,
                    roll_type=interaction_data.get('roll_type', 'single'),
                    participants=interaction_data.get('participants', {}),
                    description=interaction_data.get('description', ''),
                    base_weight=1.0
                )
    
    def _load_environments(self):
        """Load environment definitions and modifiers"""
        filepath = self.config_dir / "context" / "event_environment_list.json"
        if not filepath.exists():
            return
        
        data = self._load_json_with_comments(filepath)
        self.environments = data.get('environments', {})
    
    def _load_tones(self):
        """Load tone definitions and modifiers"""
        filepath = self.config_dir / "context" / "interactions_Tones.json"
        if not filepath.exists():
            return
        
        data = self._load_json_with_comments(filepath)
        self.tones = data.get('tones', {})
    
    def get_interaction(self, interaction_name: str) -> Optional[InteractionDefinition]:
        """Get an interaction definition by name"""
        return self.interactions.get(interaction_name)
    
    def get_interactions_by_domain(self, domain: str) -> List[InteractionDefinition]:
        """Get all interactions for a specific domain"""
        return [
            interaction
            for interaction in self.interactions.values()
            if interaction.domain == domain
        ]
    
    def get_environment_modifiers(
        self,
        environment: str,
        interaction_name: str
    ) -> Dict[str, float]:
        """
        Get environment modifiers for an interaction.
        
        Returns:
            Dictionary of modifier types and their values
        """
        if environment not in self.environments:
            return {}
        
        env_data = self.environments[environment]
        modifiers = {}
        
        # Get interaction weight modifiers
        weight_mods = env_data.get('interaction_weight_modifiers', {})
        if interaction_name in weight_mods:
            modifiers['weight'] = weight_mods[interaction_name]
        
        # Get check modifiers
        check_mods = env_data.get('check_modifiers', {})
        modifiers.update(check_mods)
        
        # Get outcome modifiers
        outcome_mods = env_data.get('outcome_modifiers', {})
        modifiers.update(outcome_mods)
        
        return modifiers
    
    def get_tone_modifiers(
        self,
        tone: str,
        interaction_name: str
    ) -> Dict[str, float]:
        """
        Get tone modifiers for an interaction.
        
        Returns:
            Dictionary of modifier types and their values
        """
        if tone not in self.tones:
            return {}
        
        tone_data = self.tones[tone]
        modifiers = {}
        
        # Get interaction weight modifiers
        weight_mods = tone_data.get('interaction_weight_modifiers', {})
        if interaction_name in weight_mods:
            modifiers['weight'] = weight_mods[interaction_name]
        
        # Get check modifiers
        check_mods = tone_data.get('check_modifiers', {})
        modifiers.update(check_mods)
        
        # Get escalation modifiers
        escalation_mods = tone_data.get('escalation_modifiers', {})
        if interaction_name in escalation_mods:
            modifiers['escalation'] = escalation_mods[interaction_name]
        
        return modifiers
    
    def calculate_weighted_probability(
        self,
        interaction_name: str,
        environment: Optional[str] = None,
        tone: Optional[str] = None
    ) -> float:
        """
        Calculate the weighted probability for selecting an interaction.
        
        Args:
            interaction_name: Name of the interaction
            environment: Optional environment context
            tone: Optional tone context
            
        Returns:
            Weighted probability (base weight + modifiers)
        """
        interaction = self.get_interaction(interaction_name)
        if not interaction:
            return 0.0
        
        weight = interaction.base_weight
        
        # Apply environment modifiers
        if environment:
            env_mods = self.get_environment_modifiers(environment, interaction_name)
            weight += env_mods.get('weight', 0.0)
        
        # Apply tone modifiers
        if tone:
            tone_mods = self.get_tone_modifiers(tone, interaction_name)
            weight += tone_mods.get('weight', 0.0)
        
        # Ensure weight is non-negative
        return max(0.0, weight)
    
    def select_interaction(
        self,
        domain: str,
        participant_ids: List[str],
        environment: Optional[str] = None,
        tone: Optional[str] = None,
        allowed_interactions: Optional[List[str]] = None
    ) -> Optional[SelectedInteraction]:
        """
        Select an interaction based on weighted probabilities.
        
        Args:
            domain: Interaction domain ("social" or "operational")
            participant_ids: List of character IDs participating
            environment: Optional environment context
            tone: Optional tone context
            allowed_interactions: Optional list of allowed interaction names
            
        Returns:
            SelectedInteraction if successful, None otherwise
        """
        # Get candidate interactions
        candidates = self.get_interactions_by_domain(domain)
        
        # Filter by environment domains if specified
        if environment and environment in self.environments:
            env_data = self.environments[environment]
            allowed_domains = env_data.get('domains', [])
            if allowed_domains:
                candidates = [c for c in candidates if c.domain in allowed_domains]
        
        # Filter by allowed interactions if specified
        if allowed_interactions:
            candidates = [c for c in candidates if c.name in allowed_interactions]
        
        if not candidates:
            return None
        
        # Calculate weights
        weights = []
        for interaction in candidates:
            weight = self.calculate_weighted_probability(
                interaction.name,
                environment,
                tone
            )
            weights.append(weight)
        
        # Select weighted random
        total_weight = sum(weights)
        if total_weight <= 0:
            return None
        
        r = random.uniform(0, total_weight)
        accumulated = 0.0
        selected_interaction = None
        
        for interaction, weight in zip(candidates, weights):
            accumulated += weight
            if r <= accumulated:
                selected_interaction = interaction
                break
        
        if not selected_interaction:
            selected_interaction = candidates[-1]
        
        # Gather all modifiers
        modifiers = {}
        if environment:
            env_mods = self.get_environment_modifiers(environment, selected_interaction.name)
            modifiers.update(env_mods)
        
        if tone:
            tone_mods = self.get_tone_modifiers(tone, selected_interaction.name)
            modifiers.update(tone_mods)
        
        return SelectedInteraction(
            interaction_name=selected_interaction.name,
            domain=selected_interaction.domain,
            roll_type=selected_interaction.roll_type,
            participants=participant_ids,
            environment=environment,
            tone=tone,
            modifiers=modifiers
        )
    
    def select_interaction_for_event(
        self,
        event_instance: Any,
        domain: str = "social",
        environment: Optional[str] = None,
        tone: Optional[str] = None
    ) -> Optional[SelectedInteraction]:
        """
        Select an interaction for an event instance.
        
        Args:
            event_instance: EventInstance from the injector
            domain: Interaction domain (default: "social")
            environment: Optional environment context
            tone: Optional tone context
            
        Returns:
            SelectedInteraction if successful, None otherwise
        """
        return self.select_interaction(
            domain=domain,
            participant_ids=event_instance.primary_participants,
            environment=environment,
            tone=tone
        )
