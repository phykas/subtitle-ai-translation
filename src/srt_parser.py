import re
from dataclasses import dataclass
from typing import List
from pathlib import Path


@dataclass
class SubtitleEntry:
    index: int
    start_time: str
    end_time: str
    text: str
    
    def to_srt_format(self) -> str:
        return f"{self.index}\n{self.start_time} --> {self.end_time}\n{self.text}\n"


class SRTParser:
    def __init__(self):
        self.time_pattern = re.compile(r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})')
    
    def parse(self, file_path: str) -> List[SubtitleEntry]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"SRT file not found: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as file:
            content = file.read().strip()
        
        return self._parse_content(content)
    
    def _parse_content(self, content: str) -> List[SubtitleEntry]:
        entries = []
        blocks = content.split('\n\n')
        
        for block in blocks:
            if not block.strip():
                continue
                
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue
            
            try:
                index = int(lines[0])
                time_match = self.time_pattern.match(lines[1])
                
                if not time_match:
                    continue
                
                start_time, end_time = time_match.groups()
                text = '\n'.join(lines[2:])
                
                entries.append(SubtitleEntry(
                    index=index,
                    start_time=start_time,
                    end_time=end_time,
                    text=text
                ))
                
            except (ValueError, IndexError):
                continue
        
        return entries
    
    def write_srt(self, entries: List[SubtitleEntry], output_path: str):
        with open(output_path, 'w', encoding='utf-8') as file:
            for entry in entries:
                file.write(entry.to_srt_format() + '\n')