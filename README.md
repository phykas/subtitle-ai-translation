# Subtitle Translator

A Python CLI application that uses LangChain and OpenAI to translate SRT subtitle files efficiently while preserving perfect timing and structure.

## Quick Start (Using Pre-built Executable)

**For beginners who just want to use the tool without installing Python:**

1. **Download the Latest Release**:
   - Go to the [Releases page](../../releases)
   - Download `subtitle-translator.exe` from the latest release

2. **Set up Required Files**:
   - Create a folder for your subtitle translations
   - Place the downloaded `subtitle-translator.exe` in this folder
   - Create two configuration files (see instructions below)

3. **Ready to Use**:
   ```bash
   subtitle-translator.exe input.srt output.srt -s "English" -t "Spanish" -v
   ```

### Important Notes for Exe Users:
- Make sure both `.env` and `config.yaml` files are in the same folder as the executable
- Your folder structure should look like:
  ```
  your-folder/
  ├── subtitle-translator.exe
  ├── .env
  ├── config.yaml
  ├── input.srt (your subtitle file)
  └── output.srt (will be created)
  ```

## Features

- **Efficient Batching**: Translates multiple subtitles per API call using structured JSON format
- **Perfect Structure Preservation**: Keeps original timestamps and indices intact
- **Checkpoint/Resume**: Automatically saves progress and can resume from interruptions  
- **Real-time Progress**: Detailed logging shows exactly what's being translated
- **Incremental Output**: Updates output file after each batch for continuous progress tracking
- **Configurable Batching**: Adjustable batch sizes to balance speed vs. API efficiency
- **CLI Interface**: Simple command-line interface for batch processing

## Required Configuration Files

### 1. Create `.env` file (API Key Configuration)

Create a file named `.env` in the same folder as your executable:

```
OPENAI_API_KEY=your-actual-api-key-here
```

**To get your OpenAI API key:**
1. Go to [OpenAI API Keys page](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key and replace `your-actual-api-key-here` with it
5. Save the file (make sure it's named exactly `.env` with no extension)

### 2. Create `config.yaml` file (Translation Settings)

Create a file named `config.yaml` in the same folder as your executable:

```yaml
openai:
  model: "gpt-4o-mini"
  max_tokens: 4500
  temperature: 0.1
  context_buffer: 500

chunking:
  max_chunk_size: 4000
  overlap_lines: 2
```

**Configuration explained:**
- `model`: Which AI model to use (gpt-4o-mini is cost-effective and good quality)
- `max_tokens`: Maximum response length (4500 works well for most translations)
- `temperature`: How creative the translation should be (0.1 = more consistent, less creative)
- `context_buffer`: Reserved tokens for system instructions
- `max_chunk_size`: How much text to process at once
- `overlap_lines`: How many subtitle lines to overlap between chunks

## Setup for Python Developers

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

3. **Configure Settings** (optional):
   Edit `config.yaml` to adjust model settings and chunking parameters.

## Usage Examples

### Using the Executable
```bash
# Basic translation
subtitle-translator.exe input.srt output.srt -s "English" -t "Spanish" -v

# Custom batch size for faster processing
subtitle-translator.exe movie.srt movie_french.srt -s "English" -t "French" --batch-size 20 -v

# Resume interrupted translation (run same command again)
subtitle-translator.exe movie.srt movie_spanish.srt -s "English" -t "Spanish" -v
```

### Using Python (Developers)
```bash
python main.py input.srt output.srt -s "English" -t "Spanish" -v
```

### Arguments
- `input.srt`: Path to input SRT file
- `output.srt`: Path to output translated SRT file
- `-s, --source-lang`: Source language (e.g., "English") 
- `-t, --target-lang`: Target language (e.g., "Spanish")
- `-c, --config`: Config file path (default: config.yaml)
- `-v, --verbose`: Enable detailed progress logging
- `--batch-size`: Number of subtitles per batch (default: 10)

### Examples

```bash
# Basic translation with progress logging
python main.py movie.srt movie_spanish.srt -s "English" -t "Spanish" -v

# Custom batch size for faster processing (fewer API calls)
python main.py input.srt output.srt -s "English" -t "French" --batch-size 20 -v

# Resume interrupted translation (same command - automatically detects checkpoint)
python main.py movie.srt movie_spanish.srt -s "English" -t "Spanish" -v
```

## Configuration

Edit `config.yaml` to customize:

```yaml
openai:
  model: "gpt-4o-mini"        # OpenAI model to use
  max_tokens: 4500            # Max tokens for model  
  temperature: 0.1            # Temperature for translation
  context_buffer: 500         # Reserve tokens for system prompt

chunking:
  max_chunk_size: 4000        # Max tokens per chunk (not used in current approach)
  overlap_lines: 2            # Overlap lines (not used in current approach)
```

## How it Works

1. **Parse SRT**: Reads and parses the input SRT file into structured entries
2. **Batch Processing**: Groups subtitles into configurable batches (default: 10)
3. **JSON Translation**: Sends structured JSON to OpenAI with reliable ID-based mapping
4. **Structure Preservation**: Maps translations back to original timestamps and indices
5. **Checkpoint Saving**: Saves progress after each successful batch
6. **Incremental Output**: Updates output SRT file continuously for real-time progress
7. **Resume Capability**: Automatically resumes from last checkpoint if interrupted

## Checkpoint & Resume

The application automatically creates checkpoint files (`output.srt.checkpoint`) that track translation progress:

- **Automatic Resume**: If interrupted, simply run the same command again
- **Progress Tracking**: Shows exactly how many entries have been translated  
- **Safe Interruption**: You can safely stop the process anytime (Ctrl+C)
- **Cleanup**: Checkpoint files are automatically removed when translation completes

## Batch Size Recommendations

- **Small batches (5-10)**: More frequent saves, easier to resume, slower overall
- **Medium batches (10-20)**: Good balance of speed and safety (recommended)
- **Large batches (20+)**: Faster translation, less frequent saves, more tokens per API call

Choose based on your subtitle file size and reliability needs.