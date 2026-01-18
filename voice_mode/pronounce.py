"""Pronunciation rules management."""
import re
import os

class PronounceManager:
    def __init__(self):
        self.rules = {'tts': [], 'stt': []}
    
    def process_tts(self, text: str) -> str:
        return text
    
    def process_stt(self, text: str) -> str:
        return text

def get_manager():
    return PronounceManager()
