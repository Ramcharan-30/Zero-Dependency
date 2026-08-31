#!/usr/bin/env python3
"""
ZeroShrink Web Demo Server
Built entirely on Python standard library.
Serves the interactive compression demo at http://localhost:8000
"""

import json
import base64
import sys
from email.parser import BytesParser
from email.policy import default
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

# Ensure src/ is on path so we can import zcomp
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from zcomp.archive import create_archive, extract_archive
from zcomp.errors import ArchiveValidationError
from zcomp.metrics import format_size, Timer
from zcomp.profiler import profile_content


WEB_DIR = Path(__file__).resolve().parent
MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB demo limit


class DemoHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        # Quieter logs for demo
        pass

    def _send_json(self, status: int, data: dict):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _send_static(self, rel_path: str, content_type: str):
        full = WEB_DIR / rel_path

        if not full.exists():
            self.send_error(404)
            return

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(full.read_bytes())

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self._send_static(
                "index.html",
                "text/html; charset=utf-8"
            )

        elif path == "/style.css":
            self._send_static(
                "style.css",
                "text/css; charset=utf-8"
            )

        elif path == "/app.js":
            self._send_static(
                "app.js",
                "application/javascript; charset=utf-8"
            )

        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/compress":
            self._handle_compress()

        elif path == "/api/decompress":
            self._handle_decompress()

        else:
            self.send_error(404)

    def _read_body(self) -> bytes:
        """Read HTTP request body with upload-size protection."""

        content_length_header = self.headers.get("Content-Length")

        if not content_length_header:
            raise ValueError("Missing Content-Length")

        try:
            content_length = int(content_length_header)
        except ValueError:
            raise ValueError("Invalid Content-Length")

        if content_length < 0:
            raise ValueError("Invalid Content-Length")

        if content_length > MAX_UPLOAD_BYTES:
            raise ValueError(
                f"Upload exceeds {MAX_UPLOAD_BYTES} bytes"
            )

        body = self.rfile.read(content_length)

        if len(body) != content_length:
            raise ValueError("Incomplete request body")

        return body

    def _parse_multipart(self, body: bytes, content_type: str):
        """
        Parse multipart/form-data using Python's standard library.

        This replaces the removed cgi.FieldStorage API and works
        with Python 3.13+.
        """

        if not content_type:
            raise ValueError("Missing Content-Type")

        if not content_type.lower().startswith("multipart/form-data"):
            raise ValueError(
                "Expected multipart/form-data"
            )

        # Create a MIME-style message for the standard-library
        # email parser.
        message = (
            f"Content-Type: {content_type}\r\n"
            "MIME-Version: 1.0\r\n"
            "\r\n"
        ).encode("utf-8") + body

        parsed = BytesParser(
            policy=default
        ).parsebytes(message)

        if not parsed.is_multipart():
            raise ValueError(
                "Invalid multipart/form-data request"
            )

        fields = {}

        for part in parsed.iter_parts():

            disposition = part.get_content_disposition()

            if disposition != "form-data":
                continue

            field_name = part.get_param(
                "name",
                header="Content-Disposition"
            )

            if not field_name:
                continue

            filename = part.get_filename()

            if filename is not None:
                # Uploaded file.
                #
                # Never trust a client-provided path.
                safe_filename = Path(filename).name

                file_data = part.get_payload(
                    decode=True
                ) or b""

                fields[field_name] = {
                    "filename": safe_filename,
                    "data": file_data,
                }

            else:
                # Normal text form field.
                fields[field_name] = part.get_content()

        return fields

    def _handle_compress(self):
        try:
            body = self._read_body()

            content_type = self.headers.get(
                "Content-Type",
                ""
            )

            form = self._parse_multipart(
                body,
                content_type
            )

            file_item = form.get("file")

            if not file_item or not isinstance(file_item, dict):
                self._send_json(
                    400,
                    {"error": "No file uploaded"}
                )
                return

            filename = file_item["filename"]
            data = file_item["data"]

            if len(data) == 0:
                self._send_json(
                    400,
                    {"error": "Empty file"}
                )
                return

            # Run the ACTUAL compression engine.
            timer = Timer()
            timer.start()

            fake_path = Path(filename)

            archive_bytes, selection_result, profile = (
                create_archive(
                    fake_path,
                    data
                )
            )

            timer.stop()

            orig_size = len(data)
            best_size = selection_result.best_size

            saved_pct = (
                (orig_size - best_size)
                / orig_size
                * 100.0
                if orig_size > 0
                else 0.0
            )

            # Build candidate table.
            candidates = []

            for ev in selection_result.evaluations:

                candidates.append({
                    "transform": ev.transform_name,
                    "codec": ev.codec_name,
                    "label": ev.display_label,
                    "size": ev.archive_size,
                    "size_human": format_size(
                        ev.archive_size
                    ),
                    "is_winner": ev.is_winner,
                    "ratio": (
                        round(
                            orig_size / ev.archive_size,
                            2
                        )
                        if ev.archive_size > 0
                        else 0.0
                    ),
                    "saved_pct": round(
                        (
                            (orig_size - ev.archive_size)
                            / orig_size
                            * 100.0
                        )
                        if orig_size > 0
                        else 0.0,
                        2
                    ),
                })

            # Profile information.
            profile_info = {
                "entropy": round(
                    getattr(profile, "entropy", 0.0),
                    4
                ),
                "byte_diversity": round(
                    getattr(
                        profile,
                        "byte_diversity",
                        0.0
                    ),
                    4
                ),
                "printable_ratio": round(
                    getattr(
                        profile,
                        "printable_ratio",
                        0.0
                    ),
                    4
                ),
                "run_ratio": round(
                    getattr(
                        profile,
                        "run_ratio",
                        0.0
                    ),
                    4
                ),
                "repetition_score": round(
                    getattr(
                        profile,
                        "repetition_score",
                        0.0
                    ),
                    4
                ),
                "signature": (
                    getattr(
                        profile,
                        "signature",
                        "unknown"
                    )
                    or "none"
                ),
                "already_compressed": getattr(
                    profile,
                    "already_compressed",
                    False
                ),
            }

            self._send_json(
                200,
                {
                    "success": True,
                    "filename": filename,

                    "original_size": orig_size,
                    "original_size_human": format_size(
                        orig_size
                    ),

                    "compressed_size": best_size,
                    "compressed_size_human": format_size(
                        best_size
                    ),

                    "saved_bytes": (
                        orig_size - best_size
                    ),

                    "saved_bytes_human": format_size(
                        abs(orig_size - best_size)
                    ),

                    "saved_pct": round(
                        saved_pct,
                        2
                    ),

                    "compression_ratio": (
                        round(
                            orig_size / best_size,
                            2
                        )
                        if best_size > 0
                        else 0.0
                    ),

                    "elapsed_ms": round(
                        timer.elapsed * 1000,
                        2
                    ),

                    "winner_strategy": (
                        selection_result
                        .best_transform
                        .name
                        + " + "
                        + selection_result
                        .best_codec
                        .__class__
                        .__name__
                        .replace(
                            "Codec",
                            ""
                        )
                    ),

                    "candidates": candidates,

                    "profile": profile_info,

                    "archive_b64": (
                        base64
                        .b64encode(archive_bytes)
                        .decode("ascii")
                    ),
                }
            )

        except ValueError as e:
            self._send_json(
                400,
                {"error": str(e)}
            )

        except Exception as e:
            self._send_json(
                500,
                {"error": str(e)}
            )

    def _handle_decompress(self):
        try:
            body = self._read_body()

            content_type = self.headers.get(
                "Content-Type",
                ""
            )

            form = self._parse_multipart(
                body,
                content_type
            )

            file_item = form.get("file")

            if not file_item or not isinstance(file_item, dict):
                self._send_json(
                    400,
                    {"error": "No file uploaded"}
                )
                return

            archive_data = file_item["data"]

            if len(archive_data) == 0:
                self._send_json(
                    400,
                    {"error": "Empty archive"}
                )
                return

            timer = Timer()
            timer.start()

            filename, restored_bytes, header, v_result = (
                extract_archive(
                    archive_data
                )
            )

            timer.stop()

            self._send_json(
                200,
                {
                    "success": True,

                    "filename": filename,

                    "restored_size": len(
                        restored_bytes
                    ),

                    "restored_size_human": format_size(
                        len(restored_bytes)
                    ),

                    "elapsed_ms": round(
                        timer.elapsed * 1000,
                        2
                    ),

                    "verified": v_result.is_valid,

                    "crc32_match": getattr(
                        v_result,
                        "crc32_match",
                        False
                    ),

                    "sha256_match": getattr(
                        v_result,
                        "sha256_match",
                        False
                    ),

                    "size_match": getattr(
                        v_result,
                        "size_match",
                        False
                    ),

                    "original_sha256": (
                        header.sha256.hex()
                    ),

                    "restored_b64": (
                        base64
                        .b64encode(restored_bytes)
                        .decode("ascii")
                    ),
                }
            )

        except ArchiveValidationError as e:
            self._send_json(
                400,
                {
                    "error":
                        f"Archive validation failed: {e}"
                }
            )

        except ValueError as e:
            self._send_json(
                400,
                {"error": str(e)}
            )

        except Exception as e:
            self._send_json(
                500,
                {"error": str(e)}
            )


def run_server(port: int = 8000):
    server = HTTPServer(
        ("127.0.0.1", port),
        DemoHandler
    )

    print(
        f"ZeroShrink Demo running at "
        f"http://127.0.0.1:{port}"
    )

    print("Press Ctrl+C to stop.")

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


if __name__ == "__main__":
    port = (
        int(sys.argv[1])
        if len(sys.argv) > 1
        else 8000
    )

    run_server(port)