"""Metadata and ecological profiles for the 10 target wildlife species."""

SPECIES_METADATA = {
    "Elephant": {
        "scientific_name": "Loxodonta africana / Elephas maximus",
        "category": "Herbivore / Megaherbivore",
        "conservation_status": "Endangered",
        "risk_level": "HIGH",
        "danger_reason": "Aggressive when threatened, crop-raiding, trampling hazards.",
        "safety_advice": "Maintain 100m distance; avoid flash photography; do not block herd movement pathways.",
        "icon": "🐘",
        "color": "#e67e22"
    },
    "Tiger": {
        "scientific_name": "Panthera tigris",
        "category": "Carnivore / Apex Predator",
        "conservation_status": "Endangered",
        "risk_level": "CRITICAL",
        "danger_reason": "Lethal predator; territorial ambush hunter.",
        "safety_advice": "Do not turn your back or run; stand tall; back away slowly; sound perimeter siren.",
        "icon": "🐅",
        "color": "#e74c3c"
    },
    "Lion": {
        "scientific_name": "Panthera leo",
        "category": "Carnivore / Apex Predator",
        "conservation_status": "Vulnerable",
        "risk_level": "CRITICAL",
        "danger_reason": "Coordinated pack hunter; high human-settlement hazard.",
        "safety_advice": "Stay in enclosed vehicles or structures; activate perimeter electric fencing.",
        "icon": "🦁",
        "color": "#c0392b"
    },
    "Leopard": {
        "scientific_name": "Panthera pardus",
        "category": "Carnivore / Solitary Predator",
        "conservation_status": "Vulnerable",
        "risk_level": "CRITICAL",
        "danger_reason": "Master of stealth; climbs trees; attacks pets and livestock.",
        "safety_advice": "Secure livestock in fortified sheds; use bright floodlighting at night.",
        "icon": "🐆",
        "color": "#d35400"
    },
    "Bear": {
        "scientific_name": "Ursus arctos / Ursus americanus",
        "category": "Omnivore / Large Mammal",
        "conservation_status": "Threatened",
        "risk_level": "HIGH",
        "danger_reason": "Extremely strong; attacks when startled or protecting cubs.",
        "safety_advice": "Make loud noises; do not leave food or garbage exposed.",
        "icon": "🐻",
        "color": "#8e44ad"
    },
    "Deer": {
        "scientific_name": "Cervidae",
        "category": "Herbivore / Ungulate",
        "conservation_status": "Least Concern",
        "risk_level": "LOW",
        "danger_reason": "Non-aggressive; highway crossing collision risk only.",
        "safety_advice": "Slow down vehicles near forest corridors.",
        "icon": "🦌",
        "color": "#27ae60"
    },
    "Giraffe": {
        "scientific_name": "Giraffa camelopardalis",
        "category": "Herbivore / Browser",
        "conservation_status": "Vulnerable",
        "risk_level": "LOW",
        "danger_reason": "Gentle herbivore; low threat to humans.",
        "safety_advice": "Observe peacefully; keep safe distance to avoid defensive kicks.",
        "icon": "🦒",
        "color": "#f1c40f"
    },
    "Zebra": {
        "scientific_name": "Equus quagga",
        "category": "Herbivore / Grazing Herd",
        "conservation_status": "Near Threatened",
        "risk_level": "LOW",
        "danger_reason": "Non-aggressive; defensive biting or kicking if cornered.",
        "safety_advice": "Maintain standard safari perimeter.",
        "icon": "🦓",
        "color": "#34495e"
    },
    "Wolf": {
        "scientific_name": "Canis lupus",
        "category": "Carnivore / Pack Hunter",
        "conservation_status": "Least Concern",
        "risk_level": "MEDIUM",
        "danger_reason": "Livestock depredation; potential pack aggression.",
        "safety_advice": "Keep guard dogs, herd livestock into pens before dusk.",
        "icon": "🐺",
        "color": "#7f8c8d"
    },
    "Rhinoceros": {
        "scientific_name": "Rhinocerotidae",
        "category": "Herbivore / Megaherbivore",
        "conservation_status": "Critically Endangered",
        "risk_level": "HIGH",
        "danger_reason": "Poor eyesight but swift charge; high anti-poaching patrol alert.",
        "safety_advice": "Alert ranger anti-poaching unit immediately upon detection; keep distance.",
        "icon": "🦏",
        "color": "#16a085"
    }
}

def get_species_info(name: str):
    return SPECIES_METADATA.get(name, {
        "scientific_name": "Unknown Wildlife",
        "category": "Unknown",
        "conservation_status": "Unassessed",
        "risk_level": "LOW",
        "danger_reason": "None known",
        "safety_advice": "Observe cautiously.",
        "icon": "🐾",
        "color": "#95a5a6"
    })
