import os
from pathlib import Path

from .config import ConfigManager
from .translator import SubtitleTranslator


class SubtitleTranslatorApp:
    def __init__(self, config_path: str = "config.yaml", verbose: bool = False):
        self.verbose = verbose
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.load_config()
        self.api_key = self.config_manager.get_openai_api_key()
        
        self.translator = SubtitleTranslator(self.config, self.api_key)
    
    def translate_file(self, input_path: str, output_path: str, source_lang: str, target_lang: str, 
                      batch_size: int = 10):
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        if self.verbose:
            print(f"Translating from {source_lang} to {target_lang}")
            print("Using simple approach: extract text -> translate -> preserve structure")
            print(f"Batch size: {batch_size} entries per API call")
            print(f"Output will be saved incrementally to: {output_path}")
            print(f"Checkpoint file: {output_path}.checkpoint")
            print("-" * 60)
        
        try:
            translated_entries = self.translator.translate_file(
                input_path, output_path, source_lang, target_lang, 
                batch_size=batch_size, verbose=self.verbose
            )
            
            if self.verbose:
                print("-" * 60)
                print(f"🎉 Translation completed successfully!")
                print(f"📊 Total entries translated: {len(translated_entries)}")
                print(f"📁 Output file: {output_path}")
                
        except Exception as e:
            print(f"❌ Error during translation: {str(e)}")
            if self.verbose:
                print("💡 You can restart the command to resume from the last checkpoint")
                import traceback
                traceback.print_exc()
            raise