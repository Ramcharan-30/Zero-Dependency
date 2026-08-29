import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.zcomp.archive import create_archive, extract_archive
from src.zcomp.metrics import format_size, Timer
from src.zcomp.codecs import get_codec
from src.zcomp.transforms import get_transform

def run_benchmarks():
    print("=========================================================================================")
    print("                    ZEROSHRINK ADAPTIVE SUITE BENCHMARK MATRIX                           ")
    print("=========================================================================================")

    fixtures = [
        ("Text Prose", b"The ZeroShrink adaptive compression engine profiles file byte structure.\n" * 200),
        ("Source Code", b"def calculate_entropy(data: bytes):\n    return -sum(p * math.log2(p))\n" * 150),
        ("Repetitive Text", b"AAAAABBBBBCCCCCDDDDD" * 500),
        ("Structured Numeric", bytes([i % 256 for i in range(10000)])),
        ("Repetitive Binary", b"\x00\xFF\x00\xFF" * 2500),
        ("High Entropy Mock", bytes([(i * 37 + 13) % 256 for i in range(5000)])),
    ]

    header_fmt = "{:<20} | {:>10} | {:>10} | {:>22} | {:>8} | {:>10}"
    print(header_fmt.format("Dataset", "Original", "Final .ZC", "Selected Strategy", "Saved %", "Result"))
    print("-" * 95)

    for label, data in fixtures:
        dummy_path = Path(f"{label.lower().replace(' ', '_')}.bin")

        t_comp = Timer()
        t_comp.start()
        arc_bytes, selection, profile = create_archive(dummy_path, data)
        t_comp.stop()

        t_decomp = Timer()
        t_decomp.start()
        orig_name, restored_bytes, header, v_result = extract_archive(arc_bytes)
        t_decomp.stop()

        orig_sz = len(data)
        final_sz = len(arc_bytes)
        saved_pct = ((orig_sz - final_sz) / orig_sz * 100.0) if orig_sz > 0 else 0.0

        codec_name = get_codec(header.codec_id).__class__.__name__.replace('Codec', '')
        transform_name = get_transform(header.transform_id).name
        strat_str = codec_name if transform_name == "NONE" else f"{transform_name}+{codec_name}"

        ver_str = "PASS" if (v_result.is_valid and restored_bytes == data) else "FAIL"

        print(header_fmt.format(
            label,
            format_size(orig_sz),
            format_size(final_sz),
            strat_str,
            f"{saved_pct:.1f}%",
            ver_str
        ))

    print("=========================================================================================")

if __name__ == "__main__":
    run_benchmarks()
