from pathlib import Path
import json
import argparse

# ============================================================================
#  stream_compact.py — compact JSON top-level ARRAY dengan memori terbatas.
# ============================================================================
#  Varian chunked dari main.py untuk file raksasa (ratusan MB): jangan
#  json.load() seluruh dokumen ke RAM; baca berkas per-chunk, pisahkan
#  elemen array satu per satu via json.JSONDecoder.raw_decode, dan tulis
#  ulang tiap elemen dalam bentuk compact (separators=(',', ':') — format
#  byte output identik dengan main.py).
#
#  Memori: hanya buffer selingkung elemen terbesar (mis. satu clue Jeopardy
#  ~2 KB) + chunk baca. Cocok untuk jeopardy.json hasil crawl j-archive.
# ============================================================================

CHUNK_SIZE = 4 * 1024 * 1024  # 4 MiB


def stream_compact(input_file: Path, output_file: Path) -> int:
    """Compact array-of-values JSON; kembalikan jumlah elemen."""
    decoder = json.JSONDecoder()
    buffer = ""
    idx = 0
    started = False
    finished = False
    first = True
    count = 0

    with open(input_file, "r", encoding="utf-8") as r, \
         open(output_file, "w", encoding="utf-8", newline="") as w:
        w.write("[")
        while not finished:
            chunk = r.read(CHUNK_SIZE)
            if chunk:
                buffer += chunk
            eof = not chunk

            progressed = True
            while progressed:
                progressed = False

                # Buang whitespace di depan buffer.
                while idx < len(buffer) and buffer[idx].isspace():
                    idx += 1
                if idx >= len(buffer):
                    if eof:
                        finished = True
                    else:
                        buffer, idx = "", 0  # buffer habis di whitespace — isi ulang
                    break

                head = buffer[idx]

                if not started:
                    if head != "[":
                        raise ValueError(
                            f"Elemen top-level bukan array (dapat {head!r}) — "
                            "pakai main.py untuk JSON non-array."
                        )
                    started = True
                    idx += 1
                    progressed = True
                    continue

                if head == "]":
                    finished = True
                    break
                if head == ",":
                    idx += 1
                    progressed = True
                    continue

                # Parse satu elemen; butuh data lagi bila gagal & belum EOF.
                try:
                    element, end = decoder.raw_decode(buffer, idx)
                except json.JSONDecodeError:
                    if eof:
                        raise
                    break  # refill buffer, lanjut di outer loop

                w.write(("" if first else ",") + json.dumps(element, separators=(",", ":")))
                first = False
                count += 1
                idx = end
                progressed = True

                # Pangkas prefix yang sudah dikonsumsi agar buffer tetap kecil.
                if idx > CHUNK_SIZE:
                    buffer = buffer[idx:]
                    idx = 0
        w.write("]")

    return count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compact JSON array besar secara streaming (chunked, memori terbatas)."
    )
    parser.add_argument("--input", "-i", type=Path, required=True,
                        help="Path to the input JSON file (top-level array).")
    parser.add_argument("--output", "-o", type=Path, required=True,
                        help="Path to save the compacted JSON file.")
    parser.add_argument("--force", "-f", action="store_true",
                        help="Overwrite the output file if it already exists.")
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

    count = stream_compact(input_file, output_file)
    size_mb = output_file.stat().st_size / (1024 * 1024)
    print(f"Successfully compacted (streamed, {count} elements, "
          f"{size_mb:.1f} MB): {input_file} -> {output_file}")


if __name__ == "__main__":
    main()
