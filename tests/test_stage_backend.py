from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

from PIL import Image

from test_case_agent.lean_v2.backend import (
    CodexExecStageBackend as LegacyCodexExecStageBackend,
)
from test_case_agent.lean_v2.backend import LeanV2BackendError
from test_case_agent.lean_v2.backend import StageResult as LegacyStageResult
from test_case_agent.stage_backend import (
    CodexExecStageBackend,
    RegisteredImageInput,
    StageBackendError,
    StageResult,
)


class StageBackendCompatibilityTests(unittest.TestCase):
    def test_legacy_backend_exports_are_identity_preserving_aliases(self) -> None:
        self.assertIs(CodexExecStageBackend, LegacyCodexExecStageBackend)
        self.assertIs(StageResult, LegacyStageResult)
        self.assertIs(StageBackendError, LeanV2BackendError)


class StageBackendImageTests(unittest.TestCase):
    TRUNCATED_IMAGE_BYTES = {
        ".png": b"\x89PNG\r\n\x1a\n",
        ".jpg": b"\xff\xd8\xff\xe0",
        ".jpeg": b"\xff\xd8\xff\xe1",
        ".gif": b"GIF89a",
        ".bmp": b"BM",
        ".webp": b"RIFF\x04\x00\x00\x00WEBP",
        ".avif": b"\x00\x00\x00\x10ftypavif\x00\x00\x00\x00",
    }

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    @staticmethod
    def _schema() -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"ok": {"type": "boolean"}},
            "required": ["ok"],
            "additionalProperties": False,
        }

    @staticmethod
    def _resolution() -> SimpleNamespace:
        return SimpleNamespace(
            verified=True,
            selected_executable="C:/mock/codex.exe",
            disable_args=("--disable", "plugins", "--disable", "shell_tool"),
            duration_ms=7,
            selected=SimpleNamespace(version="codex-cli test"),
        )

    @staticmethod
    def _registered_image(path: Path) -> RegisteredImageInput:
        content = path.read_bytes()
        return RegisteredImageInput(
            path=path.resolve(),
            sha256=hashlib.sha256(content).hexdigest(),
            size_bytes=len(content),
        )

    @staticmethod
    def _write_valid_image(path: Path) -> None:
        image = Image.new("RGB", (3, 2), color=(31, 97, 173))
        image.save(path)

    @staticmethod
    def _successful_run(
        command: list[str],
        **_kwargs: Any,
    ) -> subprocess.CompletedProcess[str]:
        output_path = Path(command[command.index("--output-last-message") + 1])
        output_path.write_text(json.dumps({"ok": True}), encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    def test_no_images_preserves_cli_and_receipt_shape(self) -> None:
        captured: dict[str, Any] = {}

        def fake_run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
            captured["command"] = command
            captured["kwargs"] = kwargs
            return self._successful_run(command, **kwargs)

        with (
            patch(
                "test_case_agent.stage_backend.resolve_verified_exec_capability",
                return_value=self._resolution(),
            ) as resolver,
            patch("test_case_agent.stage_backend.subprocess.run", side_effect=fake_run),
        ):
            result = CodexExecStageBackend().run_stage(
                stage="reviewer",
                prompt="bounded prompt",
                schema=self._schema(),
                artifact_dir=self.root / "no-images",
            )

        required = resolver.call_args.kwargs["additional_required_flags"]
        self.assertNotIn("--image", required)
        self.assertNotIn("--image", captured["command"])
        self.assertEqual("-", captured["command"][-1])
        self.assertEqual(
            {"count": 0, "bytes": 0}, result.receipt["image_attachments"]
        )
        self.assertEqual(2, result.receipt["input_artifacts"]["count"])
        self.assertIsNone(captured["kwargs"]["timeout"])

    def test_registered_images_are_staged_in_order_and_receipted(self) -> None:
        first = self.root / "first.PNG"
        second = self.root / "second.jpg"
        self._write_valid_image(first)
        self._write_valid_image(second)
        images = (self._registered_image(first), self._registered_image(second))
        captured: dict[str, Any] = {}

        def fake_run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
            image_indexes = [
                index for index, value in enumerate(command) if value == "--image"
            ]
            staged_paths = [Path(command[index + 1]) for index in image_indexes]
            captured["command"] = list(command)
            captured["staged_paths"] = staged_paths
            captured["staged_bytes"] = [path.read_bytes() for path in staged_paths]
            return self._successful_run(command, **kwargs)

        with (
            patch(
                "test_case_agent.stage_backend.resolve_verified_exec_capability",
                return_value=self._resolution(),
            ) as resolver,
            patch("test_case_agent.stage_backend.subprocess.run", side_effect=fake_run),
        ):
            result = CodexExecStageBackend().run_stage(
                stage="reviewer",
                prompt="bounded prompt",
                schema=self._schema(),
                artifact_dir=self.root / "with-images",
                images=images,
            )

        self.assertIn(
            "--image", resolver.call_args.kwargs["additional_required_flags"]
        )
        image_flag_positions = [
            index
            for index, value in enumerate(captured["command"])
            if value == "--image"
        ]
        self.assertEqual(2, len(image_flag_positions))
        self.assertEqual("-", captured["command"][-1])
        self.assertTrue(
            all(
                position < len(captured["command"]) - 1
                for position in image_flag_positions
            )
        )
        self.assertEqual(
            [first.read_bytes(), second.read_bytes()], captured["staged_bytes"]
        )
        self.assertTrue(all(path.is_absolute() for path in captured["staged_paths"]))
        self.assertTrue(
            all(path not in {first, second} for path in captured["staged_paths"])
        )
        image_bytes = first.stat().st_size + second.stat().st_size
        self.assertEqual(
            {"count": 2, "bytes": image_bytes}, result.receipt["image_attachments"]
        )
        self.assertEqual(4, result.receipt["input_artifacts"]["count"])
        self.assertGreater(result.receipt["input_artifacts"]["bytes"], image_bytes)
        self.assertIn("read-only", captured["command"])
        self.assertIn("--ephemeral", captured["command"])
        self.assertIn("--ignore-user-config", captured["command"])

    def test_stale_and_duplicate_registered_images_are_rejected_before_probe(self) -> None:
        image = self.root / "registered.png"
        self._write_valid_image(image)
        valid = self._registered_image(image)
        stale = RegisteredImageInput(
            path=valid.path,
            sha256="0" * 64,
            size_bytes=valid.size_bytes,
        )
        cases = (
            ((stale,), "bytes changed"),
            ((valid, valid), "duplicate registered image path"),
        )
        for index, (images, message) in enumerate(cases):
            with self.subTest(message=message):
                with (
                    patch(
                        "test_case_agent.stage_backend.resolve_verified_exec_capability"
                    ) as resolver,
                    patch("test_case_agent.stage_backend.subprocess.run") as runner,
                ):
                    with self.assertRaisesRegex(StageBackendError, message):
                        CodexExecStageBackend().run_stage(
                            stage="reviewer",
                            prompt="bounded prompt",
                            schema=self._schema(),
                            artifact_dir=self.root / f"invalid-{index}",
                            images=images,
                        )
                resolver.assert_not_called()
                runner.assert_not_called()

    def test_invalid_image_signature_is_rejected_before_probe(self) -> None:
        image = self.root / "not-really-an-image.png"
        image.write_bytes(b"plain text with a png suffix")

        with (
            patch(
                "test_case_agent.stage_backend.resolve_verified_exec_capability"
            ) as resolver,
            patch("test_case_agent.stage_backend.subprocess.run") as runner,
        ):
            with self.assertRaisesRegex(StageBackendError, "invalid \\.png signature"):
                CodexExecStageBackend().run_stage(
                    stage="reviewer",
                    prompt="bounded prompt",
                    schema=self._schema(),
                    artifact_dir=self.root / "invalid-signature",
                    images=(self._registered_image(image),),
                )

        resolver.assert_not_called()
        runner.assert_not_called()

    def test_decodable_image_with_wrong_suffix_is_rejected_before_probe(self) -> None:
        image = self.root / "png-disguised-as-jpeg.jpg"
        Image.new("RGB", (3, 2), color=(31, 97, 173)).save(image, format="PNG")

        with (
            patch(
                "test_case_agent.stage_backend.resolve_verified_exec_capability"
            ) as resolver,
            patch("test_case_agent.stage_backend.subprocess.run") as runner,
        ):
            with self.assertRaisesRegex(StageBackendError, "invalid \\.jpg signature"):
                CodexExecStageBackend().run_stage(
                    stage="reviewer",
                    prompt="bounded prompt",
                    schema=self._schema(),
                    artifact_dir=self.root / "wrong-suffix",
                    images=(self._registered_image(image),),
                )

        resolver.assert_not_called()
        runner.assert_not_called()

    def test_valid_decodable_images_for_every_supported_suffix_are_accepted(self) -> None:
        for suffix in self.TRUNCATED_IMAGE_BYTES:
            with self.subTest(suffix=suffix):
                image = self.root / f"valid{suffix}"
                self._write_valid_image(image)
                with (
                    patch(
                        "test_case_agent.stage_backend.resolve_verified_exec_capability",
                        return_value=self._resolution(),
                    ),
                    patch(
                        "test_case_agent.stage_backend.subprocess.run",
                        side_effect=self._successful_run,
                    ),
                ):
                    CodexExecStageBackend().run_stage(
                        stage="reviewer",
                        prompt="bounded prompt",
                        schema=self._schema(),
                        artifact_dir=self.root / f"valid-{suffix[1:]}",
                        images=(self._registered_image(image),),
                    )

    def test_signature_only_stubs_for_every_supported_suffix_are_rejected(self) -> None:
        for suffix, content in self.TRUNCATED_IMAGE_BYTES.items():
            with self.subTest(suffix=suffix):
                image = self.root / f"truncated{suffix}"
                image.write_bytes(content)
                with (
                    patch(
                        "test_case_agent.stage_backend.resolve_verified_exec_capability"
                    ) as resolver,
                    patch("test_case_agent.stage_backend.subprocess.run") as runner,
                ):
                    with self.assertRaisesRegex(
                        StageBackendError, "cannot be fully decoded"
                    ):
                        CodexExecStageBackend().run_stage(
                            stage="reviewer",
                            prompt="bounded prompt",
                            schema=self._schema(),
                            artifact_dir=self.root / f"truncated-{suffix[1:]}",
                            images=(self._registered_image(image),),
                        )
                resolver.assert_not_called()
                runner.assert_not_called()

    def test_tampered_image_is_rejected_before_backend_probe(self) -> None:
        image = self.root / "tampered.png"
        self._write_valid_image(image)
        registered = self._registered_image(image)
        image.write_bytes(b"mutated")

        with (
            patch(
                "test_case_agent.stage_backend.resolve_verified_exec_capability"
            ) as resolver,
            patch("test_case_agent.stage_backend.subprocess.run") as runner,
        ):
            with self.assertRaisesRegex(StageBackendError, "bytes changed"):
                CodexExecStageBackend().run_stage(
                    stage="reviewer",
                    prompt="bounded prompt",
                    schema=self._schema(),
                    artifact_dir=self.root / "tampered",
                    images=(registered,),
                )

        resolver.assert_not_called()
        runner.assert_not_called()

    def test_mutation_during_capability_probe_blocks_model_call(self) -> None:
        image = self.root / "probe-mutation.png"
        self._write_valid_image(image)
        registered = self._registered_image(image)

        def mutate_during_probe(*_args: Any, **_kwargs: Any) -> SimpleNamespace:
            image.write_bytes(b"mutated-during-probe")
            return self._resolution()

        with (
            patch(
                "test_case_agent.stage_backend.resolve_verified_exec_capability",
                side_effect=mutate_during_probe,
            ),
            patch("test_case_agent.stage_backend.subprocess.run") as runner,
        ):
            with self.assertRaisesRegex(StageBackendError, "bytes changed"):
                CodexExecStageBackend().run_stage(
                    stage="reviewer",
                    prompt="bounded prompt",
                    schema=self._schema(),
                    artifact_dir=self.root / "probe-mutation",
                    images=(registered,),
                )
        runner.assert_not_called()

    def test_mutation_during_subprocess_invalidates_result(self) -> None:
        image = self.root / "subprocess-mutation.png"
        self._write_valid_image(image)
        registered = self._registered_image(image)

        def mutate_during_run(
            command: list[str],
            **kwargs: Any,
        ) -> subprocess.CompletedProcess[str]:
            completed = self._successful_run(command, **kwargs)
            image.write_bytes(b"mutated-during-subprocess")
            return completed

        with (
            patch(
                "test_case_agent.stage_backend.resolve_verified_exec_capability",
                return_value=self._resolution(),
            ),
            patch(
                "test_case_agent.stage_backend.subprocess.run",
                side_effect=mutate_during_run,
            ),
        ):
            with self.assertRaisesRegex(StageBackendError, "bytes changed"):
                CodexExecStageBackend().run_stage(
                    stage="reviewer",
                    prompt="bounded prompt",
                    schema=self._schema(),
                    artifact_dir=self.root / "subprocess-mutation",
                    images=(registered,),
                )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
