import click
from pathlib import Path


@click.command()
@click.argument('input_file', type=click.Path(exists=True, path_type=Path))
@click.argument('output_file', type=click.Path(path_type=Path))
@click.option('--source-lang', '-s', required=True, help='Source language (e.g., English, Spanish)')
@click.option('--target-lang', '-t', required=True, help='Target language (e.g., French, German)')
@click.option('--config', '-c', default='config.yaml', help='Path to config file')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--batch-size', default=10, help='Number of subtitle entries per batch')
def translate_subtitles(input_file, output_file, source_lang, target_lang, config, verbose, batch_size):
    """
    Translate SRT subtitle files using OpenAI models via LangChain.
    
    INPUT_FILE: Path to the input SRT file
    OUTPUT_FILE: Path to the output translated SRT file
    """
    from .app import SubtitleTranslatorApp
    app = SubtitleTranslatorApp(config_path=config, verbose=verbose)
    
    try:
        app.translate_file(
            input_path=str(input_file),
            output_path=str(output_file),
            source_lang=source_lang,
            target_lang=target_lang,
            batch_size=batch_size
        )
        
        if not verbose:  # Only show this if not in verbose mode (verbose mode has its own completion message)
            click.echo(f"Translation completed: {output_file}")
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    translate_subtitles()