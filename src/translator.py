import json
import os
from typing import List, Optional
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from .srt_parser import SubtitleEntry, SRTParser
from .config import AppConfig


class SubtitleTranslator:
    def __init__(self, config: AppConfig, api_key: str):
        self.config = config
        self.llm = ChatOpenAI(
            model=config.openai.model,
            temperature=config.openai.temperature,
            max_tokens=config.openai.max_tokens,
            openai_api_key=api_key
        )
        self.parser = SRTParser()
    
    def translate_file(self, input_file: str, output_file: str, source_lang: str, target_lang: str, 
                      batch_size: int = 10, verbose: bool = False):
        """
        Simple approach with checkpointing: Extract text, translate in batches, map back to original structure
        """
        # Parse original SRT file
        entries = self.parser.parse(input_file)
        if verbose:
            print(f"Loaded {len(entries)} subtitle entries from {input_file}")
        
        # Check for existing checkpoint
        checkpoint_file = f"{output_file}.checkpoint"
        translated_entries = self._load_checkpoint(checkpoint_file, entries)
        
        start_index = len(translated_entries)
        if start_index > 0 and verbose:
            print(f"Resuming from checkpoint: {start_index}/{len(entries)} entries already translated")
        
        # Translate remaining entries in batches
        for i in range(start_index, len(entries), batch_size):
            batch_end = min(i + batch_size, len(entries))
            batch_entries = entries[i:batch_end]
            
            if verbose:
                print(f"Translating batch {i//batch_size + 1}: entries {i+1}-{batch_end}/{len(entries)}")
            
            try:
                # Extract texts from this batch
                batch_texts = [entry.text for entry in batch_entries]
                
                if verbose:
                    for j, entry in enumerate(batch_entries):
                        print(f"  Entry {i+j+1}: '{entry.text[:50]}{'...' if len(entry.text) > 50 else ''}'")
                
                # Translate the entire batch in one API call
                translated_texts = self._translate_batch_texts(batch_texts, source_lang, target_lang)
                
                # Create translated entries for this batch
                batch_translated = []
                for j, entry in enumerate(batch_entries):
                    translated_text = translated_texts[j] if j < len(translated_texts) else entry.text
                    batch_translated.append(SubtitleEntry(
                        index=entry.index,
                        start_time=entry.start_time,
                        end_time=entry.end_time,
                        text=translated_text
                    ))
                    
                    if verbose:
                        print(f"  ✓ Entry {i+j+1}: '{translated_text[:50]}{'...' if len(translated_text) > 50 else ''}'")
                
                # Add to overall results
                translated_entries.extend(batch_translated)
                
                # Save checkpoint and output file after each successful batch
                self._save_checkpoint(checkpoint_file, translated_entries)
                self.parser.write_srt(translated_entries, output_file)
                
                if verbose:
                    print(f"✓ Batch {i//batch_size + 1} completed and saved ({len(translated_entries)}/{len(entries)} total)")
                    print("")
                    
            except Exception as e:
                if verbose:
                    print(f"✗ Error translating batch {i//batch_size + 1}: {str(e)}")
                raise
        
        # Clean up checkpoint file on successful completion
        if os.path.exists(checkpoint_file):
            os.remove(checkpoint_file)
            if verbose:
                print("Translation completed successfully, checkpoint removed")
        
        return translated_entries
    
    def _translate_batch_texts(self, texts: List[str], source_lang: str, target_lang: str) -> List[str]:
        """
        Translate a batch of subtitle texts using JSON format for reliable parsing
        """
        # Create input JSON structure
        input_data = []
        for i, text in enumerate(texts):
            input_data.append({"id": i, "text": text})
        
        system_prompt = self._create_batch_system_prompt(source_lang, target_lang, len(texts))
        human_prompt = f"Translate the following subtitle texts:\n\n{json.dumps(input_data, ensure_ascii=False, indent=2)}"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            response_text = response.content.strip()
            
            # Parse the JSON response
            try:
                translated_data = json.loads(response_text)
                
                # Extract translated texts in the correct order
                translated_texts = [None] * len(texts)
                for item in translated_data:
                    if isinstance(item, dict) and 'id' in item and 'text' in item:
                        idx = item['id']
                        if 0 <= idx < len(texts):
                            translated_texts[idx] = item['text']
                
                # Fill any missing translations with originals
                for i in range(len(texts)):
                    if translated_texts[i] is None:
                        translated_texts[i] = texts[i]
                
                return translated_texts
                
            except json.JSONDecodeError:
                # Fallback: try to extract translations line by line if JSON fails
                print(f"Warning: JSON parsing failed, attempting fallback parsing")
                return self._fallback_parse_response(response_text, texts)
                
        except Exception as e:
            print(f"Warning: Batch translation failed, using originals: {e}")
            return texts  # fallback to originals
    
    def _fallback_parse_response(self, response_text: str, original_texts: List[str]) -> List[str]:
        """
        Fallback parser if JSON format fails
        """
        lines = response_text.strip().split('\n')
        translations = []
        
        # Try to extract meaningful content
        for line in lines:
            line = line.strip()
            if line and not line.startswith('{') and not line.startswith('[') and not line.startswith('"id"'):
                # Remove common JSON artifacts
                line = line.replace('"text":', '').replace('"', '').strip()
                if line.startswith(': '):
                    line = line[2:]
                if line and line != ',':
                    translations.append(line)
        
        # Ensure we have the right number of translations
        while len(translations) < len(original_texts):
            translations.append(original_texts[len(translations)])
            
        return translations[:len(original_texts)]
    
    def _create_batch_system_prompt(self, source_lang: str, target_lang: str, num_texts: int) -> str:
        return f"""You are a professional subtitle translator. Translate subtitles from {source_lang} to {target_lang}.

You will receive a JSON array with {num_texts} subtitle entries, each with an "id" and "text" field.

CRITICAL RULES:
1. Return a JSON array with the same structure, keeping the same "id" for each entry
2. Translate ONLY the "text" field for each entry
3. Keep translations concise and appropriate for subtitles  
4. Preserve speaker indicators like [SPEAKER], (sound effects), etc.
5. Maintain line breaks within the subtitle text
6. Do NOT add explanations or extra text outside the JSON
7. Ensure you return exactly {num_texts} entries with the same IDs

Example format:
Input: [{{"id": 0, "text": "Hello world"}}, {{"id": 1, "text": "How are you?"}}]
Output: [{{"id": 0, "text": "Hola mundo"}}, {{"id": 1, "text": "¿Cómo estás?"}}]

Your response must be valid JSON only."""
    
    def _load_checkpoint(self, checkpoint_file: str, original_entries: List[SubtitleEntry]) -> List[SubtitleEntry]:
        """Load existing translations from checkpoint file"""
        if not os.path.exists(checkpoint_file):
            return []
        
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
            
            translated_entries = []
            for entry_data in checkpoint_data:
                translated_entries.append(SubtitleEntry(
                    index=entry_data['index'],
                    start_time=entry_data['start_time'],
                    end_time=entry_data['end_time'],
                    text=entry_data['text']
                ))
            
            return translated_entries
            
        except Exception as e:
            print(f"Warning: Could not load checkpoint file: {e}")
            return []
    
    def _save_checkpoint(self, checkpoint_file: str, translated_entries: List[SubtitleEntry]):
        """Save current progress to checkpoint file"""
        try:
            checkpoint_data = []
            for entry in translated_entries:
                checkpoint_data.append({
                    'index': entry.index,
                    'start_time': entry.start_time,
                    'end_time': entry.end_time,
                    'text': entry.text
                })
            
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not save checkpoint: {e}")