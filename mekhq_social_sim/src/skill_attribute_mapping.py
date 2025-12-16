"""
Skill to Attribute Mapping

Maps skill names to the attributes that support them.
Based on Classic BattleTech and A Time of War (AToW) rules.

This is a basic mapping that can be replaced with a JSON configuration later.
"""

from typing import Dict, List


# Skill name -> list of supporting attributes
SKILL_ATTRIBUTE_MAP: Dict[str, List[str]] = {
    # MekWarrior Skills
    "Gunnery/Mek": ["DEX", "RFL"],
    "Piloting/Mek": ["DEX", "RFL"],
    "Gunnery": ["DEX", "RFL"],
    "Piloting": ["DEX", "RFL"],
    "Mek Gunnery": ["DEX", "RFL"],
    "Mek Piloting": ["DEX", "RFL"],
    
    # Vehicle Skills
    "Gunnery/Vehicle": ["DEX", "RFL"],
    "Piloting/Vehicle": ["DEX", "RFL"],
    "Driving": ["DEX", "RFL"],
    
    # Aerospace Skills
    "Gunnery/Aerospace": ["DEX", "RFL"],
    "Piloting/Aerospace": ["DEX", "RFL"],
    
    # Infantry Skills
    "Anti-Mek": ["DEX", "RFL"],
    "Small Arms": ["DEX", "RFL"],
    
    # Technical Skills
    "Tech/Mek": ["INT", "EDG"],
    "Tech/Aero": ["INT", "EDG"],
    "Tech/Mechanic": ["INT", "EDG"],
    "Tech/BA": ["INT", "EDG"],
    "Technician": ["INT"],
    "Medtech": ["INT", "DEX"],
    "Medicine": ["INT", "EDG"],
    
    # Command & Communication Skills
    "Tactics": ["INT", "WIL"],
    "Strategy": ["INT", "WIL"],
    "Leadership": ["CHA", "WIL"],
    "Negotiation": ["CHA", "INT"],
    "Protocol": ["CHA", "INT"],
    "Communications": ["INT"],
    
    # Support Skills
    "Navigation": ["INT"],
    "Sensors": ["INT"],
    "Computer": ["INT"],
    "Administration": ["INT"],
    
    # Academic/Knowledge Skills
    "Astech": ["INT"],
    "Engineering": ["INT", "EDG"],
    "Science": ["INT"],
    
    # Physical Skills
    "Athletics": ["STR", "BOD"],
    "Running": ["STR", "BOD"],
    "Swimming": ["STR", "BOD"],
    "Climbing": ["STR", "DEX"],
    
    # Social Skills
    "Scrounge": ["CHA", "EDG"],
    "Streetwise": ["CHA", "INT"],
    
    # Perception & Awareness
    "Perception": ["INT", "WIL"],
    "Tracking": ["INT", "WIL"],
    
    # Survival Skills
    "Survival": ["INT", "WIL"],
    
    # AToW Extended Skills
    "Artillery": ["INT", "RFL"],
    "Demolitions": ["INT", "DEX"],
    "Disguise": ["CHA", "INT"],
    "Forgery": ["DEX", "INT"],
    "Hunting": ["DEX", "INT"],
    "Interrogation": ["CHA", "WIL"],
    "Investigation": ["INT", "WIL"],
    "Security Systems": ["INT", "DEX"],
    "Stealth": ["DEX", "WIL"],
    "Thrown Weapons": ["DEX", "STR"],
}


def get_skill_attributes(skill_name: str) -> List[str]:
    """
    Get the list of attributes that support a given skill.
    
    Args:
        skill_name: The name of the skill
        
    Returns:
        List of attribute abbreviations (e.g., ["DEX", "RFL"])
        Returns empty list if skill has no known mapping
    """
    # Try exact match first
    if skill_name in SKILL_ATTRIBUTE_MAP:
        return SKILL_ATTRIBUTE_MAP[skill_name]
    
    # Try case-insensitive match
    skill_lower = skill_name.lower()
    for key, attrs in SKILL_ATTRIBUTE_MAP.items():
        if key.lower() == skill_lower:
            return attrs
    
    # Try partial match (for variations like "Gunnery/Mek" vs "Gunnery")
    for key, attrs in SKILL_ATTRIBUTE_MAP.items():
        if skill_lower in key.lower() or key.lower() in skill_lower:
            return attrs
    
    return []


def format_skill_support(skill_name: str) -> str:
    """
    Format the attribute support for a skill as a string.
    
    Args:
        skill_name: The name of the skill
        
    Returns:
        Formatted string like "supported by: DEX, RFL" or empty string if no mapping
    """
    attrs = get_skill_attributes(skill_name)
    if attrs:
        return f"supported by: {', '.join(attrs)}"
    return ""
