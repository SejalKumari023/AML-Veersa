
from docling.datamodel import vlm_model_specs
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    VlmPipelineOptions,
)
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.vlm_pipeline import VlmPipeline

from pathlib import Path
import json

# Convert a public arXiv PDF; replace with a local path if preferred.
# source = "https://arxiv.org/pdf/2501.17887"
source = Path(__file__).parent.parent.parent / "data" / "Swiss_Home_Purchase_Agreement_Scanned_Noise_forparticipants.pdf"

###### USING SIMPLE DEFAULT VALUES
# - GraniteDocling model
# - Using the transformers framework

# pipeline_options = VlmPipelineOptions(
#     vlm_options=vlm_model_specs.GRANITEDOCLING_VLLM,
# )

# converter = DocumentConverter(
#     format_options={
#         InputFormat.PDF: PdfFormatOption(
#             pipeline_cls=VlmPipeline,
#         ),
#     }
# )

# doc = converter.convert(source=source).document

# print(doc.export_to_markdown())


###### USING MACOS MPS ACCELERATOR
# Demonstrates using MLX on macOS with MPS acceleration (macOS only).
# For more options see the `compare_vlm_models.py` example.

pipeline_options = VlmPipelineOptions(
    vlm_options=vlm_model_specs.GRANITEDOCLING_MLX,
)

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_cls=VlmPipeline,
            pipeline_options=pipeline_options,
        ),
    }
)

doc = converter.convert(source=source).document

markdown = doc.export_to_markdown()
print(markdown)

md_path = Path("[NEW] Swiss_Home_Purchase_Agreement_Scanned_Noise_forparticipants.md")
markdown_content = doc.export_to_markdown()
with md_path.open("w", encoding="utf-8") as f:
    f.write(markdown_content)

json_path = Path("[NEW] Swiss_Home_Purchase_Agreement_Scanned_Noise_forparticipants.json")
with json_path.open("w", encoding="utf-8") as f:
    json_content = doc.export_to_dict()
    json.dump(json_content, f, indent=2)