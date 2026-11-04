from pathlib import Path
import json
import argparse

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compact JSON file by removing unneeded whitespace and formatted layout."
    )
    parser.add_argument(
        '--input', '-i',
        type=Path,
        required=True,
        help="Path to the input JSON file."
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        required=True,
        help="Path to save the compacted JSON file."
    )
    parser.add_argument(
        '--force', '-f',
        action="store_true",
        help="Overwrite the output file if it already exists."
    )
    args = parser.parse_args()

    input_file: Path = args.input
    output_file: Path = args.output

    if not input_file.is_file():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    if output_file.exists() and not args.force:
        raise FileExistsError(
            f"Output file already exists: {output_file}. Use --force or -f to overwrite."
        )

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(input_file, 'r', encoding='utf-8') as r:
        data = json.load(r)

    with open(output_file, 'w', encoding='utf-8') as w:
        json.dump(data, w, separators=(',', ':'))

    print(f"Successfully compacted: {input_file} -> {output_file}")

if __name__ == '__main__':
    main()