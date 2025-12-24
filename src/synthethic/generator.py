# src/synthetic/generator.py
import random
from typing import List, Dict
from faker import Faker
import json

class SyntheticIncidentGenerator:
    """Generate synthetic cybersecurity incidents for stress testing"""
    
    def __init__(self, seed: int = 42):
        self.fake = Faker()
        self.fake.seed_instance(seed)
        random.seed(seed)
        
        # Templates for different types of incidents
        self.templates = {
            'benign': [
                "User {user} performed scheduled maintenance on server {server}. " +
                "Installed updates {updates}. Created backup at {path}. " +
                "All activities logged with admin credentials.",
                
                "Network scan detected {ip} performing vulnerability assessment. " +
                "Ports {ports} scanned. This is part of authorized security testing. " +
                "Scan originated from internal security server.",
                
                "Automated script {script} executed routine cleanup. " +
                "Removed temporary files from {path}. " +
                "Script signed by {company} IT department."
            ],
            'malicious': [
                "Unknown PowerShell script {script} executed from {path}. " +
                "Script attempted to disable Windows Defender. " +
                "Connection to {ip} on port {port}. " +
                "File hash {hash} matches known malware.",
                
                "User {user} credentials used from unusual location {location}. " +
                "Accessed sensitive files {files}. " +
                "Data exfiltration to {domain} detected. " +
                "Account now locked pending investigation.",
                
                "Ransomware detected on workstation {host}. " +
                "Files encrypted with {extension} extension. " +
                "Ransom note {note} found. " +
                "Communication with C2 server {ip}."
            ],
            'ambiguous': [
                "User {user} downloaded file {file} from {domain}. " +
                "File executed but no malicious behavior observed. " +
                "Antivirus scan clean. User claims legitimate business tool.",
                
                "Unusual network traffic from {ip} to {destination}. " +
                "Protocol {protocol} on port {port}. " +
                "No known business reason. Could be misconfiguration or covert channel.",
                
                "Service account {account} accessed resources at unusual time. " +
                "Accessed {resource}. No alerts triggered. " +
                "Could be legitimate maintenance or credential theft."
            ]
        }
    
    def generate_incident(self, incident_type: str = None, 
                         difficulty: str = 'medium') -> Dict:
        """Generate a synthetic incident"""
        if incident_type is None:
            incident_type = random.choice(['benign', 'malicious', 'ambiguous'])
        
        template = random.choice(self.templates[incident_type])
        
        # Fill template with fake data
        context = {
            'user': self.fake.user_name(),
            'server': self.fake.hostname(),
            'updates': f"KB{random.randint(100000, 999999)}",
            'path': self.fake.file_path(),
            'ip': self.fake.ipv4(),
            'ports': f"{random.randint(1, 1024)}, {random.randint(1025, 65535)}",
            'script': f"{self.fake.word()}.ps1",
            'port': random.randint(1024, 65535),
            'hash': self.fake.sha256(),
            'location': f"{self.fake.city()}, {self.fake.country()}",
            'files': f"{self.fake.file_name()}, {self.fake.file_name()}",
            'domain': self.fake.domain_name(),
            'host': self.fake.hostname(),
            'extension': f".{self.fake.word()}",
            'note': f"{self.fake.file_name()}.txt",
            'destination': self.fake.ipv4_private(),
            'protocol': random.choice(['TCP', 'UDP', 'ICMP']),
            'account': f"svc_{self.fake.word()}",
            'resource': f"//{self.fake.hostname()}/share",
            'company': self.fake.company()
        }
        
        text = template.format(**context)
        
        # Add difficulty modifiers
        if difficulty == 'easy':
            # Clear indicators
            if incident_type == 'malicious':
                text += " Windows Defender flagged as malware. Known bad IP from threat intel."
            elif incident_type == 'benign':
                text += " Approved change ticket #CHG-12345. All activities expected."
        elif difficulty == 'hard':
            # Add contradictory evidence
            if incident_type == 'malicious':
                text += " However, user has legitimate business with that domain."
            elif incident_type == 'benign':
                text += " However, activity pattern matches known attack TTP."
            else:
                text += " Evidence is contradictory and incomplete."
        
        return {
            'id': f"synthetic_{self.fake.uuid4()[:8]}",
            'text': text,
            'ground_truth': incident_type.upper() if incident_type != 'ambiguous' else None,
            'difficulty': difficulty,
            'type': incident_type
        }
    
    def generate_dataset(self, size: int = 100, 
                        distribution: Dict = None) -> List[Dict]:
        """Generate a balanced dataset of synthetic incidents"""
        if distribution is None:
            distribution = {'benign': 0.4, 'malicious': 0.4, 'ambiguous': 0.2}
        
        incidents = []
        counts = {k: int(size * v) for k, v in distribution.items()}
        
        for incident_type, count in counts.items():
            for _ in range(count):
                difficulty = random.choice(['easy', 'medium', 'hard'])
                incidents.append(self.generate_incident(incident_type, difficulty))
        
        # Shuffle
        random.shuffle(incidents)
        
        return incidents
    
    def save_dataset(self, incidents: List[Dict], path: str):
        """Save dataset to JSONL file"""
        with open(path, 'w') as f:
            for incident in incidents:
                f.write(json.dumps(incident) + '\n')
        
        print(f"[Generator] Saved {len(incidents)} incidents to {path}")