"""
Resolver Bundle - Central loader for all meta resolver files.

This module loads and provides access to:
- participant_resolution_map.json (roles, filters, person_sets)
- relationship_resolution_map.json (relationship predicates and derived relations)
- age_groups.json (age group definitions)

Implements minimal include resolution for age_groups reference in participant map.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, List


class ResolverBundle:
    """
    Central access point for all resolver configuration.
    
    This class loads the resolver maps once and caches them for reuse.
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the resolver bundle.
        
        Args:
            config_dir: Path to config/events directory. If None, uses default.
        """
        if config_dir is None:
            module_dir = Path(__file__).resolve().parent
            self.config_dir = module_dir.parent.parent / "config" / "events"
        else:
            self.config_dir = Path(config_dir)
        
        self.meta_dir = self.config_dir / "meta"
        
        # Loaded configurations
        self.participant_map: Dict[str, Any] = {}
        self.relationship_map: Dict[str, Any] = {}
        self.age_groups: Dict[str, Any] = {}
        
        self._load_all()
    
    def _strip_json_comments(self, json_str: str) -> str:
        """Remove C-style comments from JSON string."""
        # Remove single-line comments
        json_str = re.sub(r'//.*', '', json_str)
        # Remove multi-line comments
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        return json_str
    
    def _load_json_file(self, filepath: Path) -> Dict[str, Any]:
        """Load a JSON file with comment stripping."""
        if not filepath.exists():
            print(f"[WARNING] Resolver file not found: {filepath}")
            return {}
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                json_content = f.read()
            
            clean_json = self._strip_json_comments(json_content)
            return json.loads(clean_json)
        except Exception as e:
            print(f"[ERROR] Failed to load {filepath}: {e}")
            return {}
    
    def _resolve_includes(self, data: Dict[str, Any]) -> None:
        """
        Resolve includes in the participant map.
        
        Specifically handles the age_groups include by loading the referenced file
        and merging it into the appropriate location.
        
        Args:
            data: The participant map data to process
        """
        includes = data.get("includes", {})
        
        # Handle age_groups include
        age_groups_include = includes.get("age_groups", {})
        if age_groups_include:
            path = age_groups_include.get("path")
            json_pointer = age_groups_include.get("json_pointer")
            
            if path and json_pointer:
                # Load the age_groups file
                age_groups_file = Path(path)
                if not age_groups_file.is_absolute():
                    # Resolve relative to project root
                    project_root = Path(__file__).resolve().parent.parent.parent.parent
                    age_groups_file = project_root / path
                
                age_groups_data = self._load_json_file(age_groups_file)
                
                # Extract the data at json_pointer (e.g., "/age_groups")
                pointer_parts = json_pointer.strip('/').split('/')
                extracted_data = age_groups_data
                for part in pointer_parts:
                    if part and isinstance(extracted_data, dict):
                        extracted_data = extracted_data.get(part, {})
                
                # Store the resolved age groups
                self.age_groups = extracted_data
    
    def _load_all(self) -> None:
        """Load all resolver files."""
        # Load participant resolution map
        participant_file = self.meta_dir / "participant_resolution_map.json"
        self.participant_map = self._load_json_file(participant_file)
        
        # Resolve includes (loads age_groups)
        self._resolve_includes(self.participant_map)
        
        # Load relationship resolution map
        relationship_file = self.meta_dir / "relationship_resolution_map.json"
        self.relationship_map = self._load_json_file(relationship_file)
        
        # If age_groups wasn't loaded via include, load it directly
        if not self.age_groups:
            age_groups_file = self.meta_dir / "age_groups.json"
            age_groups_data = self._load_json_file(age_groups_file)
            self.age_groups = age_groups_data.get("age_groups", {})
    
    # -------------------------------------------------------------------------
    # Participant Map Accessors
    # -------------------------------------------------------------------------
    
    def get_role_mapping(self, abstract_role: str) -> List[str]:
        """
        Get the concrete role(s) for an abstract role.
        
        Args:
            abstract_role: Abstract role name (e.g., "HR", "TECHNICIAN")
            
        Returns:
            List of concrete roles (e.g., ["ADMINISTRATOR_HR"])
            Empty list if role is unknown
        """
        roles = self.participant_map.get("roles", {})
        return roles.get(abstract_role.upper(), [])
    
    def get_filter_definition(self, filter_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the filter definition for a filter name.
        
        Args:
            filter_name: Filter name (e.g., "present", "alive")
            
        Returns:
            Filter definition dict, or None if unknown
        """
        filters = self.participant_map.get("filters", {})
        return filters.get(filter_name)
    
    def get_person_set_definition(self, person_set_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the person set definition.
        
        Args:
            person_set_name: Person set name (e.g., "any_person", "ALL_PRESENT_PERSONS")
            
        Returns:
            Person set definition dict, or None if unknown
        """
        person_sets = self.participant_map.get("person_sets", {})
        return person_sets.get(person_set_name)
    
    def get_unknown_role_policy(self) -> str:
        """Get the policy for unknown roles."""
        debug = self.participant_map.get("debug", {})
        return debug.get("unknown_role_policy", "warn_and_fail")
    
    def get_unknown_filter_policy(self) -> str:
        """Get the policy for unknown filters."""
        debug = self.participant_map.get("debug", {})
        return debug.get("unknown_filter_policy", "warn_and_fail")
    
    def get_unknown_person_set_policy(self) -> str:
        """Get the policy for unknown person sets."""
        debug = self.participant_map.get("debug", {})
        return debug.get("unknown_person_set_policy", "warn_and_fail")
    
    # -------------------------------------------------------------------------
    # Age Groups Accessors
    # -------------------------------------------------------------------------
    
    def get_age_group_definition(self, group_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the age group definition.
        
        Args:
            group_name: Age group name (e.g., "EARLY_TEEN", "TEEN", "ADULT")
            
        Returns:
            Age group definition with min_age, max_age, notes
            None if group is unknown
        """
        return self.age_groups.get(group_name.upper())
    
    def get_all_age_groups(self) -> Dict[str, Dict[str, Any]]:
        """Get all age group definitions."""
        return self.age_groups.copy()
    
    # -------------------------------------------------------------------------
    # Relationship Map Accessors
    # -------------------------------------------------------------------------
    
    def get_pair_predicate(self, predicate_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the pair predicate definition.
        
        Args:
            predicate_name: Predicate name (e.g., "RELATIONSHIP_ACTIVE_WITH_EACH_OTHER")
            
        Returns:
            Predicate definition dict, or None if unknown
        """
        predicates = self.relationship_map.get("pair_predicates", {})
        return predicates.get(predicate_name)
    
    def get_availability_requirement(self, req_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the availability requirement definition.
        
        Args:
            req_name: Requirement name (e.g., "relationship_exists", "authority_present")
            
        Returns:
            Requirement definition dict, or None if unknown
        """
        reqs = self.relationship_map.get("availability_requires", {})
        return reqs.get(req_name)
    
    def get_derived_relation(self, relation_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the derived relation definition.
        
        Args:
            relation_name: Relation name (e.g., "HR_REPRESENTATIVE", "AUTHORITY_OVER")
            
        Returns:
            Relation definition dict, or None if unknown
        """
        relations = self.relationship_map.get("derived_relations", {})
        return relations.get(relation_name)
    
    def get_unknown_required_relation_policy(self) -> str:
        """Get the policy for unknown required relations."""
        debug = self.relationship_map.get("debug", {})
        return debug.get("unknown_required_relation_policy", "warn_and_fail")
    
    def get_unknown_derived_relation_policy(self) -> str:
        """Get the policy for unknown derived relations."""
        debug = self.relationship_map.get("debug", {})
        return debug.get("unknown_derived_relation_policy", "warn_and_fail")
    
    def should_warn_on_unsupported(self) -> bool:
        """Check if warnings should be emitted for unsupported tokens."""
        debug = self.relationship_map.get("debug", {})
        return debug.get("warn_on_unsupported", True)


# Global singleton instance
_resolver_bundle: Optional[ResolverBundle] = None


def get_resolver_bundle() -> ResolverBundle:
    """Get the global ResolverBundle singleton instance."""
    global _resolver_bundle
    if _resolver_bundle is None:
        _resolver_bundle = ResolverBundle()
    return _resolver_bundle


def initialize_resolver_bundle(config_dir: Optional[Path] = None) -> ResolverBundle:
    """
    Initialize the global resolver bundle with a custom config directory.
    
    Args:
        config_dir: Path to config/events directory
        
    Returns:
        ResolverBundle instance
    """
    global _resolver_bundle
    _resolver_bundle = ResolverBundle(config_dir)
    return _resolver_bundle
