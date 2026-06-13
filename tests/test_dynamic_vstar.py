from __future__ import annotations

import json
import random
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from dynamic_vstar.compositing import composite_context_crop
from dynamic_vstar.concept_library import sample_add_detail
from dynamic_vstar.geometry import canvas_spec_for_crop, crop_spec_for_slot, letterbox_crop, restore_letterboxed_content
from dynamic_vstar.image_api import FakeImageGenerator, image_bytes_from_payload
from dynamic_vstar.pipeline import run_dynamic_item
from dynamic_vstar.pipeline import choose_image_size
from dynamic_vstar.planning import OpenRouterPlanner, PlanValidationError, build_plan, planner_input_payload
from dynamic_vstar.sampling import sample_image_edits, valid_replace_targets
from dynamic_vstar.schemas import SampleSpec, SampledEdit, annotation_row_from_dict
from scripts.parse_labelstudio_export import parse as parse_labelstudio_export


def sample_row(mode: str = "replace") -> dict:
    slot: dict = {
        "slot_id": "S1",
        "context_region": {"xyxy": [20, 20, 80, 80], "ref": "a person wearing blue gloves"},
        "edit_region": {"xyxy": [40, 40, 60, 60], "mode": mode},
    }
    if mode in {"add", "either"}:
        slot["add"] = {
            "placements": ["countertop_or_table"],
            "entity_families": ["tiny_object", "small_container"],
        }
    if mode in {"replace", "either"}:
        slot["replace"] = {
            "targets": [
                {
                    "target_ref": "blue plastic glove",
                    "attribute_scope": "wearable",
                    "edit_types": ["color_change"],
                }
            ],
        }
    return {
        "image_id": "vstar_0000",
        "question_id": "0",
        "category": "direct_attributes",
        "original_question": "What color is the glove?",
        "slots": [slot],
    }


class FakeOpenRouterCompletions:
    def __init__(self, content: str) -> None:
        self.content = content
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "id": "fake-openrouter-response",
            "model": kwargs.get("model"),
            "choices": [{"message": {"content": self.content}}],
            "usage": {"total_tokens": 12},
        }


class FakeOpenRouterChat:
    def __init__(self, completions: FakeOpenRouterCompletions) -> None:
        self.completions = completions

    def send(self, **kwargs):
        return self.completions.create(**kwargs)


class FakeOpenRouterClient:
    def __init__(self, content: str) -> None:
        completions = FakeOpenRouterCompletions(content)
        self.completions = completions
        self.chat = FakeOpenRouterChat(completions)


class FakeOpenRouterEventStream:
    def __init__(self, content: str) -> None:
        self.content = content

    def __enter__(self):
        return iter(
            [
                {
                    "id": "fake-stream-response",
                    "choices": [{"message": {"content": self.content}}],
                    "usage": {"total_tokens": 20},
                }
            ]
        )

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class FakeOpenRouterStreamChat:
    def __init__(self, content: str) -> None:
        self.content = content
        self.calls: list[dict] = []

    def send(self, **kwargs):
        self.calls.append(kwargs)
        return FakeOpenRouterEventStream(self.content)


class FakeOpenRouterStreamClient:
    def __init__(self, content: str) -> None:
        self.chat = FakeOpenRouterStreamChat(content)


class DynamicVstarTests(unittest.TestCase):
    def test_sampling_is_deterministic(self) -> None:
        row = annotation_row_from_dict(sample_row("replace"))
        first = sample_image_edits(row, run_id="r1")
        second = sample_image_edits(row, run_id="r1")
        self.assertEqual(first, second)
        self.assertEqual(first.edits[0].operation, "replace")
        self.assertEqual(first.edits[0].edit_type, "color_change")
        self.assertEqual(first.edits[0].answer_attribute, "color")
        self.assertEqual(first.edits[0].target_name, "blue plastic glove")

    def test_replace_samples_target_bound_edit_types(self) -> None:
        raw = sample_row("replace")
        raw["slots"][0]["replace"] = {
            "targets": [
                {"target_ref": "blue plastic glove", "edit_types": ["color_change"]},
                {"target_ref": "white phone", "edit_types": ["color_change"]},
            ]
        }
        row = annotation_row_from_dict(raw)
        seen_refs = set()
        for index in range(12):
            sample = sample_image_edits(row, run_id=f"multi_target_{index}")
            edit = sample.edits[0]
            self.assertEqual(edit.edit_type, "color_change")
            self.assertEqual(edit.answer_attribute, "color")
            seen_refs.add(edit.target_name)
        self.assertTrue(len(seen_refs) >= 1)

    def test_replace_color_change_plan(self) -> None:
        raw = sample_row("replace")
        raw["original_question"] = "What color is the glove?"
        raw["slots"][0]["replace"] = {
            "targets": [
                {
                    "target_ref": "blue plastic glove",
                    "attribute_scope": "wearable",
                    "edit_types": ["color_change"],
                }
            ]
        }
        row = annotation_row_from_dict(raw)
        sample = sample_image_edits(row, run_id="color_plan")
        plan = build_plan(row, sample)
        edit = plan.edits[0]
        self.assertEqual(edit.question_type, "color")
        self.assertEqual(edit.answer, sample.edits[0].answer)

    def test_parser_emits_replace_targets(self) -> None:
        task = {
            "data": {"image_id": "vstar_9999", "question_id": "9999", "category": "direct_attributes"},
            "annotations": [
                {
                    "created_at": "2026-05-05",
                    "result": [
                        {"id": "ctx", "from_name": "slot_box", "value": {"rectanglelabels": ["context_region"], "x": 0, "y": 0, "width": 50, "height": 50, "original_width": 100, "original_height": 100}},
                        {"id": "ctx", "from_name": "context_slot_id", "value": {"text": ["S1"]}},
                        {"id": "ctx", "from_name": "context_ref", "value": {"text": ["person hands with gloves and phone"]}},
                        {"id": "edt", "from_name": "slot_box", "value": {"rectanglelabels": ["edit_region"], "x": 10, "y": 10, "width": 20, "height": 20, "original_width": 100, "original_height": 100}},
                        {"id": "edt", "from_name": "edit_slot_id", "value": {"text": ["S1"]}},
                        {"id": "edt", "from_name": "edit_mode", "value": {"choices": ["replace"]}},
                        {"id": "edt", "from_name": "replace_target_1_ref", "value": {"text": ["blue plastic glove"]}},
                        {"id": "edt", "from_name": "replace_target_1_attribute_scope", "value": {"choices": ["wearable"]}},
                        {"id": "edt", "from_name": "replace_target_1_edit_types", "value": {"choices": ["color_change"]}},
                        {"id": "edt", "from_name": "replace_target_2_ref", "value": {"text": ["white phone case"]}},
                        {"id": "edt", "from_name": "replace_target_2_attribute_scope", "value": {"choices": ["rigid"]}},
                        {"id": "edt", "from_name": "replace_target_2_edit_types", "value": {"choices": ["color_change"]}},
                    ],
                }
            ],
        }
        rows = parse_labelstudio_export([task])
        targets = rows[0]["slots"][0]["replace"]["targets"]
        self.assertEqual(len(targets), 2)
        self.assertEqual(targets[0]["target_ref"], "blue plastic glove")
        self.assertEqual(targets[0]["edit_types"], ["color_change"])
        self.assertEqual(targets[1]["target_ref"], "white phone case")
        self.assertEqual(targets[1]["edit_types"], ["color_change"])

    def test_parser_pairs_one_context_with_multiple_edit_slots(self) -> None:
        task = {
            "data": {"image_id": "vstar_9998", "question_id": "9998", "category": "direct_attributes"},
            "annotations": [
                {
                    "created_at": "2026-05-05",
                    "result": [
                        {"id": "ctx", "from_name": "slot_box", "value": {"rectanglelabels": ["context_region"], "x": 0, "y": 0, "width": 80, "height": 80, "original_width": 100, "original_height": 100}},
                        {"id": "ctx", "from_name": "context_slot_id", "value": {"text": ["A"]}},
                        {"id": "ctx", "from_name": "context_ref", "value": {"text": ["shared counter area"]}},
                        {"id": "edt1", "from_name": "slot_box", "value": {"rectanglelabels": ["edit_region"], "x": 10, "y": 10, "width": 10, "height": 10, "original_width": 100, "original_height": 100}},
                        {"id": "edt1", "from_name": "edit_slot_id", "value": {"text": ["A1"]}},
                        {"id": "edt1", "from_name": "edit_mode", "value": {"choices": ["add"]}},
                        {"id": "edt1", "from_name": "add_placements", "value": {"choices": ["countertop_or_table"]}},
                        {"id": "edt1", "from_name": "add_entity_families", "value": {"choices": ["tiny_object"]}},
                        {"id": "edt2", "from_name": "slot_box", "value": {"rectanglelabels": ["edit_region"], "x": 40, "y": 40, "width": 10, "height": 10, "original_width": 100, "original_height": 100}},
                        {"id": "edt2", "from_name": "edit_slot_id", "value": {"text": ["A2"]}},
                        {"id": "edt2", "from_name": "edit_mode", "value": {"choices": ["add"]}},
                        {"id": "edt2", "from_name": "add_placements", "value": {"choices": ["vertical_surface"]}},
                        {"id": "edt2", "from_name": "add_entity_families", "value": {"choices": ["sticker_or_tag"]}},
                    ],
                }
            ],
        }
        rows = parse_labelstudio_export([task])
        slots = rows[0]["slots"]
        self.assertEqual([slot["slot_id"] for slot in slots], ["A1", "A2"])
        self.assertEqual(slots[0]["context_region"]["ref"], "shared counter area")
        self.assertEqual(slots[1]["context_region"]["xyxy"], [0, 0, 80, 80])
        self.assertEqual(slots[0]["edit_region"]["xyxy"], [10, 10, 20, 20])
        self.assertEqual(slots[1]["edit_region"]["xyxy"], [40, 40, 50, 50])

    def test_add_sampling_filters_incompatible_pairs(self) -> None:
        raw = sample_row("add")
        raw["slots"][0]["add"] = {
            "placements": ["water_surface"],
            "entity_families": ["vehicle"],
        }
        row = annotation_row_from_dict(raw)
        sample = sample_image_edits(row, run_id="r1")
        self.assertEqual(sample.edits[0].placement, "water_surface")
        self.assertEqual(sample.edits[0].entity_family, "vehicle")
        self.assertIn(sample.edits[0].object_name, ("boat", "buoy"))

    def test_position_source_samples_two_slots(self) -> None:
        raw = sample_row("add")
        raw["original_question"] = "Is the object to the left or right of the other object?"
        raw["slots"].append(
            {
                "slot_id": "S2",
                "context_region": {"xyxy": [100, 20, 170, 90], "ref": "a second table area"},
                "edit_region": {"xyxy": [125, 40, 145, 60], "mode": "add"},
                "add": {
                    "placements": ["countertop_or_table"],
                    "entity_families": ["tiny_object"],
                },
            }
        )
        row = annotation_row_from_dict(raw)
        sample = sample_image_edits(row, run_id="position_sample")
        self.assertEqual(sample.slot_count, 2)
        self.assertEqual(len(sample.edits), 2)

    def test_tiny_object_sampling(self) -> None:
        rng = random.Random(0)
        allowed = {"clip", "cap"}
        for _ in range(20):
            detail = sample_add_detail(rng, "tiny_object", "color")
            self.assertIn(detail["object_name"], allowed)

    def test_replace_sampling_requires_explicit_target_ref(self) -> None:
        targets = valid_replace_targets(
            {
                "target_family": "human_wearable",
                "edit_types": ["color_change", "material_change"],
            }
        )
        self.assertEqual(targets, [])

    def test_planner_emits_options_and_correct_answer(self) -> None:
        row = annotation_row_from_dict(sample_row("replace"))
        sample = sample_image_edits(row, run_id="r1")
        plan = build_plan(row, sample)
        edit = plan.edits[0]
        self.assertEqual(plan.question_type, "color")
        self.assertEqual(plan.answer, edit.answer)
        self.assertEqual(edit.question_type, "color")
        self.assertIn("plastic glove", edit.target_phrase)
        self.assertIn(edit.correct_label, edit.options)
        self.assertEqual(edit.options[edit.correct_label], edit.answer)
        self.assertNotIn(edit.answer, edit.distractors)
        self.assertNotIn(edit.answer.lower(), edit.question.lower())

    def test_planner_input_contains_sampled_ground_truth(self) -> None:
        row = annotation_row_from_dict(sample_row("replace"))
        sample = sample_image_edits(row, run_id="r1")
        base_plan = build_plan(row, sample)
        payload = planner_input_payload(row, sample, base_plan)
        edit_payload = payload["slots"][0]
        self.assertEqual(edit_payload["slot_id"], "S1")
        self.assertEqual(edit_payload["target"], sample.edits[0].target_name)
        self.assertEqual(edit_payload["answer_attribute"], sample.edits[0].answer_attribute)
        self.assertEqual(edit_payload["answer"], sample.edits[0].answer)
        self.assertIn(sample.edits[0].answer, edit_payload["required_edit"])
        self.assertIn("code builds question", payload["ground_truth_note"])

    def test_planner_payload_includes_add_placement_hint(self) -> None:
        row = annotation_row_from_dict(sample_row("add"))
        sample = sample_image_edits(row, run_id="add_payload")
        payload = planner_input_payload(row, sample, build_plan(row, sample))
        edit_payload = payload["slots"][0]
        self.assertEqual(edit_payload["operation"], "add")
        self.assertEqual(edit_payload["placement"], "countertop_or_table")
        self.assertIn("tabletop or counter", edit_payload["placement_hint"])

    def test_openrouter_planner_preserves_sampled_ground_truth(self) -> None:
        row = annotation_row_from_dict(sample_row("replace"))
        sample = sample_image_edits(row, run_id="r1")
        sampled = sample.edits[0]
        content = json.dumps(
            {
                "target_phrase": "the glove on the person's hand",
                "edit_prompt": "Make the glove look deliberately satin while preserving the hand and phone.",
            }
        )
        client = FakeOpenRouterClient(content)
        planner = OpenRouterPlanner(model="test/model", api_key="test-key", client=client)
        plan = planner.build(row, sample, source_image=Image.new("RGBA", (100, 100), (20, 20, 20, 255)))
        edit = plan.edits[0]
        self.assertEqual(plan.answer, sampled.answer)
        self.assertEqual(edit.answer, sampled.answer)
        self.assertEqual(edit.target_phrase, "the glove on the person's hand")
        self.assertIn("satin", edit.image_prompt)
        self.assertNotIn(sampled.answer, edit.distractors)
        self.assertIn(edit.correct_label, edit.options)
        self.assertEqual(edit.options[edit.correct_label], sampled.answer)
        self.assertEqual(plan.planner_metadata["backend"], "openrouter")
        self.assertFalse(plan.planner_metadata["fallback_used"])
        self.assertEqual(client.completions.calls[0]["model"], "test/model")
        self.assertFalse(client.completions.calls[0]["stream"])
        self.assertEqual(client.completions.calls[0]["response_format"], {"type": "json_object"})
        user_content = client.completions.calls[0]["messages"][1]["content"]
        self.assertEqual(user_content[1]["type"], "image_url")

    def test_openrouter_planner_accepts_sdk_event_stream_response(self) -> None:
        row = annotation_row_from_dict(sample_row("replace"))
        sample = sample_image_edits(row, run_id="r1")
        content = json.dumps(
            {
                "target_phrase": "the glove on the person's hand",
                "edit_prompt": "Make only the glove more textured.",
            }
        )
        client = FakeOpenRouterStreamClient(content)
        planner = OpenRouterPlanner(model="test/model", api_key="test-key", client=client)
        plan = planner.build(row, sample, source_image=Image.new("RGBA", (100, 100), (20, 20, 20, 255)))
        self.assertEqual(plan.edits[0].target_phrase, "the glove on the person's hand")
        self.assertFalse(plan.planner_metadata["fallback_used"])
        self.assertEqual(plan.planner_metadata["responses"][0]["response"]["id"], "fake-stream-response")
        self.assertEqual(client.chat.calls[0]["response_format"], {"type": "json_object"})

    def test_openrouter_position_planner_builds_left_right_question(self) -> None:
        raw = sample_row("add")
        raw["original_question"] = "Is the object to the left or right of the other object?"
        raw["slots"].append(
            {
                "slot_id": "S2",
                "context_region": {"xyxy": [100, 20, 170, 90], "ref": "a second table area"},
                "edit_region": {"xyxy": [125, 40, 145, 60], "mode": "add"},
                "add": {
                    "placements": ["countertop_or_table"],
                    "entity_families": ["tiny_object"],
                },
            }
        )
        row = annotation_row_from_dict(raw)
        sample = sample_image_edits(row, run_id="position_plan")
        content = json.dumps(
            {
                "edits": [
                    {
                        "slot_id": sample.edits[0].slot_id,
                        "target_phrase": "the small red clip on the table",
                        "edit_prompt": "Add a small red clip on the table.",
                    },
                    {
                        "slot_id": sample.edits[1].slot_id,
                        "target_phrase": "the tiny blue tag on the second table",
                        "edit_prompt": "Add a tiny blue tag on the second table.",
                    },
                ]
            }
        )
        client = FakeOpenRouterClient(content)
        planner = OpenRouterPlanner(model="test/model", api_key="test-key", client=client)
        plan = planner.build(row, sample, source_image=Image.new("RGBA", (180, 100), (20, 20, 20, 255)))
        self.assertEqual(plan.question_type, "position_left_right")
        self.assertIn("left or right", plan.question)
        self.assertEqual(plan.options, {"A": "left", "B": "right"})
        user_content = client.completions.calls[0]["messages"][1]["content"]
        self.assertEqual([part["type"] for part in user_content], ["text", "image_url", "image_url"])

    def test_openrouter_planner_retries_invalid_slot_output(self) -> None:
        row = annotation_row_from_dict(sample_row("replace"))
        sample = sample_image_edits(row, run_id="r1")
        sampled = sample.edits[0]
        bad = json.dumps(
            {
                "target_phrase": f"the {sampled.answer} glove on the person's hand",
                "edit_prompt": f"Change the glove material to {sampled.answer}.",
            }
        )
        good = json.dumps(
            {
                "target_phrase": "the glove on the person's hand",
                "edit_prompt": f"Change the glove material to {sampled.answer}.",
            }
        )
        client = FakeOpenRouterClient(bad)
        client.completions.content = bad
        original_create = client.completions.create

        def create_then_fix(**kwargs):
            if len(client.completions.calls) == 0:
                return original_create(**kwargs)
            client.completions.content = good
            return original_create(**kwargs)

        client.completions.create = create_then_fix
        planner = OpenRouterPlanner(model="test/model", api_key="test-key", client=client, max_retries=1)
        plan = planner.build(row, sample, source_image=Image.new("RGBA", (100, 100), (20, 20, 20, 255)))
        self.assertNotIn(sampled.answer, plan.edits[0].target_phrase)
        self.assertEqual(plan.planner_metadata["retry_count"], 1)

    def test_openrouter_planner_raises_on_persistent_failure(self) -> None:
        row = annotation_row_from_dict(sample_row("replace"))
        sample = sample_image_edits(row, run_id="r1")
        client = FakeOpenRouterClient("not json")
        planner = OpenRouterPlanner(model="test/model", api_key="test-key", client=client)
        with self.assertRaises(PlanValidationError):
            planner.build(row, sample)

    def test_openrouter_planner_fallback_when_opted_in(self) -> None:
        row = annotation_row_from_dict(sample_row("replace"))
        sample = sample_image_edits(row, run_id="r1")
        client = FakeOpenRouterClient("not json")
        planner = OpenRouterPlanner(model="test/model", api_key="test-key", client=client, fallback_to_rule=True)
        plan = planner.build(row, sample)
        self.assertTrue(plan.planner_metadata["fallback_used"])

    def test_color_question_does_not_leak_answer(self) -> None:
        raw = sample_row("replace")
        row = annotation_row_from_dict(raw)
        sample = sample_image_edits(row, run_id="r1")
        plan = build_plan(row, sample)
        edit = plan.edits[0]
        self.assertEqual(edit.question_type, "color")
        self.assertNotIn(edit.answer.lower(), edit.question.lower())

    def test_multislot_position_question(self) -> None:
        raw = sample_row("add")
        raw["original_question"] = "Is the object to the left or right of the other object?"
        raw["slots"].append(
            {
                "slot_id": "S2",
                "context_region": {"xyxy": [100, 20, 170, 90], "ref": "a second table area"},
                "edit_region": {"xyxy": [125, 40, 145, 60], "mode": "add"},
                "add": {
                    "placements": ["countertop_or_table"],
                    "entity_families": ["tiny_object"],
                },
            }
        )
        row = annotation_row_from_dict(raw)
        sample = SampleSpec(
            image_id=row.image_id,
            question_id=row.question_id,
            run_id="r1",
            seed=1,
            slot_count=2,
            edits=[
                SampledEdit(
                    slot_id="S1",
                    operation="add",
                    placement="countertop_or_table",
                    entity_family="tiny_object",
                    target_family=None,
                    edit_type="add_object",
                    object_name="small tag",
                    target_name="",
                    answer_attribute="color",
                    answer="red",
                    attributes={"color": "red", "material": "plastic", "pattern": "plain"},
                ),
                SampledEdit(
                    slot_id="S2",
                    operation="add",
                    placement="countertop_or_table",
                    entity_family="tiny_object",
                    target_family=None,
                    edit_type="add_object",
                    object_name="tiny clip",
                    target_name="",
                    answer_attribute="color",
                    answer="blue",
                    attributes={"color": "blue", "material": "plastic", "pattern": "plain"},
                ),
            ],
            probability_trace={},
        )
        plan = build_plan(row, sample)
        self.assertEqual(plan.question_type, "position_left_right")
        self.assertTrue(plan.question.startswith("Is "))
        self.assertIn(plan.answer, {"left", "right"})

    def test_context_crop_composite_pastes_whole_crop(self) -> None:
        row = annotation_row_from_dict(sample_row("add"))
        slot = row.slots[0]
        source = Image.new("RGBA", (100, 100), (0, 0, 0, 255))
        generated = Image.new("RGBA", (60, 60), (255, 0, 0, 255))
        crop = crop_spec_for_slot(slot, source.size)
        composite = composite_context_crop(
            source,
            generated,
            crop,
        )
        self.assertEqual(composite.getpixel((10, 10)), source.getpixel((10, 10)))
        self.assertNotEqual(composite.getpixel((30, 30)), source.getpixel((30, 30)))
        self.assertNotEqual(composite.getpixel((50, 50)), source.getpixel((50, 50)))

    def test_standard_canvas_roundtrip_restores_context_size(self) -> None:
        row = annotation_row_from_dict(sample_row("replace"))
        slot = row.slots[0]
        crop = crop_spec_for_slot(slot, (100, 100))
        context = Image.new("RGBA", crop.output_size, (10, 20, 30, 255))
        canvas = canvas_spec_for_crop(crop, (1024, 1024))
        clean = letterbox_crop(context, canvas)
        restored = restore_letterboxed_content(clean, canvas)
        self.assertEqual(clean.size, (1024, 1024))
        self.assertEqual(restored.size, crop.output_size)
        self.assertEqual(canvas.content_xyxy, (0, 0, 1024, 1024))
        self.assertEqual(canvas.edit_xyxy_in_canvas, (341, 341, 683, 683))

    def test_fake_pipeline_writes_manifest(self) -> None:
        row = annotation_row_from_dict(sample_row("replace"))
        source = Image.new("RGBA", (100, 100), (20, 20, 20, 255))
        with tempfile.TemporaryDirectory() as tmp:
            item = run_dynamic_item(
                row,
                source,
                out_root=Path(tmp),
                run_id="smoke",
                generator=FakeImageGenerator(),
            )
            run_dir = Path(item.overview_image_path).parent
            manifest = run_dir / "artifacts" / "manifest.json"
            overview = run_dir / "overview.png"
            self.assertTrue(Path(item.composite_image_path).exists())
            self.assertTrue(Path(item.overview_image_path).exists())
            self.assertTrue(overview.exists())
            self.assertTrue(manifest.exists())
            self.assertEqual({path.name for path in run_dir.iterdir()}, {"artifacts", "overview.png"})
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(data["image_id"], "vstar_0000")
            self.assertEqual(data["overview_image_path"], str(overview))
            self.assertTrue(Path(data["files"]["source_boxed"]).exists())
            self.assertTrue(Path(data["files"]["overview"]).exists())
            self.assertEqual(len(data["generations"]), 1)
            self.assertEqual(data["generations"][0]["api_metadata"]["size"], "1024x1024")
            self.assertEqual(data["generations"][0]["canvas"]["size"], [1024, 1024])
            self.assertTrue(Path(data["generations"][0]["clean_canvas_path"]).exists())
            self.assertTrue(Path(data["generations"][0]["generated_canvas_path"]).exists())
            self.assertTrue(Path(data["generations"][0]["restored_context_path"]).exists())

    def test_fake_pipeline_accepts_openrouter_planner(self) -> None:
        row = annotation_row_from_dict(sample_row("replace"))
        source = Image.new("RGBA", (100, 100), (20, 20, 20, 255))
        content = json.dumps(
            {
                "target_phrase": "the glove on the person's hand",
                "edit_prompt": "Retouch only the glove while keeping the phone unchanged.",
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            item = run_dynamic_item(
                row,
                source,
                out_root=Path(tmp),
                run_id="smoke_llm_plan",
                generator=FakeImageGenerator(),
                planner=OpenRouterPlanner(model="test/model", api_key="test-key", client=FakeOpenRouterClient(content)),
            )
            self.assertTrue(Path(item.composite_image_path).exists())
            self.assertTrue(Path(item.overview_image_path).exists())
            self.assertEqual(item.plan.planner_metadata["backend"], "openrouter")
            self.assertFalse(item.plan.planner_metadata["fallback_used"])
            self.assertEqual(item.plan.edits[0].target_phrase, "the glove on the person's hand")

    def test_image_payload_b64_parser(self) -> None:
        payload = {"data": [{"b64_json": "aGVsbG8="}]}
        self.assertEqual(image_bytes_from_payload(payload), b"hello")

    def test_choose_image_size_matches_aspect_ratio(self) -> None:
        self.assertEqual(choose_image_size((400, 800), "match"), "1024x1536")
        self.assertEqual(choose_image_size((800, 400), "match"), "1536x1024")
        self.assertEqual(choose_image_size((500, 520), "match"), "1024x1024")


if __name__ == "__main__":
    unittest.main()
