import json
from datetime import date, datetime
from pathlib import Path

import yaml
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

from web.dependencies import get_machine_service, templates
from web.engines import EngineInterface
from web.yaml_renderer import RegelspraakRenderer


class DateJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles date objects"""

    def default(self, obj):
        if isinstance(obj, date | datetime):
            return obj.isoformat()
        return super().default(obj)


router = APIRouter(prefix="/wetten", tags=["wetten"])

# Path to law content files
LAWS_CONTENT_DIR = Path(__file__).parent.parent.parent / "laws" / "content"
BWB_MAPPING_PATH = Path(__file__).parent.parent.parent / "laws" / "bwb_mapping.yaml"


def load_bwb_mapping() -> dict:
    """Load the BWB mapping file"""
    try:
        with open(BWB_MAPPING_PATH, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return {"laws": []}


def load_law_content(bwb_id: str) -> dict | None:
    """Load law content for a specific BWB ID"""
    content_file = LAWS_CONTENT_DIR / f"{bwb_id}.yaml"
    if not content_file.exists():
        return None

    try:
        with open(content_file, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return None


def load_yaml_file_content(yaml_path: str) -> dict | None:
    """Load and return YAML file content"""
    yaml_file_path = Path(__file__).parent.parent.parent / yaml_path
    if not yaml_file_path.exists():
        return None
    try:
        with open(yaml_file_path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return None


def resolve_service_reference_url(service_ref: dict, bwb_mapping: dict = None) -> dict | None:
    """Resolve a service_reference to a URL that points to the specific output field"""
    if not service_ref or not isinstance(service_ref, dict):
        return None

    # Load BWB mapping if not provided
    if bwb_mapping is None:
        bwb_mapping = load_bwb_mapping()

    # Extract service reference components
    service = service_ref.get("service")
    field = service_ref.get("field")
    law = service_ref.get("law")

    if not all([service, field, law]):
        return None

    # Find the BWB ID for the referenced law
    target_bwb_id = None
    for bwb_id, law_info in bwb_mapping.get("laws", {}).items():
        # Check if this is the law we're looking for
        # Match by short_name or by checking the law path
        if law_info.get("short_name", "").lower().replace(" ", "_") == law.lower():
            target_bwb_id = bwb_id
            break

    # If not found by short name, try direct mapping for known laws
    law_to_bwb = {
        "wet_brp": "BWBR0033715",
        "algemene_ouderdomswet": "BWBR0002221",
        "wet_inkomstenbelasting": "BWBR0011353",
        "wet_studiefinanciering": "BWBR0011453",
        "zvw": "BWBR0018450",
        "zorgverzekeringswet": "BWBR0018450",
        "participatiewet": "BWBR0015703",
        "wet_structuur_uitvoeringsorganisatie_werk_en_inkomen": "BWBR0013060",
        "wet_op_het_centraal_bureau_voor_de_statistiek": "BWBR0015926",
    }

    if not target_bwb_id and law in law_to_bwb:
        target_bwb_id = law_to_bwb[law]

    if not target_bwb_id:
        return None

    # Load the law content to find the YAML file
    law_content = load_law_content(target_bwb_id)
    if not law_content or "yaml_files" not in law_content:
        return None

    # Find the YAML file for this service
    yaml_path = None
    for yaml_file in law_content["yaml_files"]:
        # Load the YAML to check if it's the right service
        yaml_content = load_yaml_file_content(yaml_file["path"])
        if yaml_content and yaml_content.get("service") == service:
            yaml_path = yaml_file["path"]
            break

    if not yaml_path:
        return None

    # Construct the URL
    url = f"/wetten/{target_bwb_id}/yaml/{yaml_path}#output-{field}"

    return {"url": url, "bwb_id": target_bwb_id, "yaml_path": yaml_path, "service": service, "field": field, "law": law}


def get_yaml_implementations(bwb_id: str, machine_service: EngineInterface) -> list[dict]:
    """Get all machine-executable YAML implementations for a law"""
    law_content = load_law_content(bwb_id)
    if not law_content or "yaml_files" not in law_content:
        return []

    implementations = []
    for yaml_file in law_content["yaml_files"]:
        # Check if this YAML file actually exists and get its details
        yaml_path = Path(__file__).parent.parent.parent / yaml_file["path"]
        if yaml_path.exists():
            try:
                with open(yaml_path, encoding="utf-8") as f:
                    yaml_content = yaml.safe_load(f)
                    implementations.append(
                        {
                            "path": yaml_file["path"],
                            "description": yaml_file["description"],
                            "name": yaml_content.get("name", "Onbekend"),
                            "service": yaml_content.get("service", "UNKNOWN"),
                            "law": yaml_content.get("law", "unknown"),
                            "discoverable": yaml_content.get("discoverable", "NONE"),
                            "valid_from": yaml_content.get("valid_from"),
                            "legal_basis": yaml_content.get("legal_basis", {}),
                        }
                    )
            except Exception:
                pass

    return implementations


def build_article_yaml_mapping(law_content: dict, yaml_explanations: dict) -> dict:
    """Build a mapping from article/paragraph references to YAML sections that reference them"""
    mapping = {}

    for yaml_path, yaml_content in yaml_explanations.items():
        # Helper function to add a reference to the mapping
        def add_reference(legal_basis: dict, section_path: str, parent_data: dict = None):
            if not isinstance(legal_basis, dict):
                return

            article = legal_basis.get("article")
            if not article:
                return

            # Build the key for this reference
            key = f"Artikel{article}"
            if "paragraph" in legal_basis:
                key += f"-para-{legal_basis['paragraph']}"
            if "subparagraph" in legal_basis:
                key += f"-{legal_basis['subparagraph']}"

            # Create the reference entry
            ref_entry = {
                "file": yaml_path,
                "section": section_path,
                "line_reference": section_path,
                "description": "",
                "explanation": legal_basis.get("explanation", ""),
            }

            # Add context-specific description
            if parent_data:
                if "name" in parent_data:
                    ref_entry["description"] = parent_data["name"]
                elif "description" in parent_data:
                    ref_entry["description"] = parent_data["description"]
                elif "output" in parent_data:
                    ref_entry["description"] = f"{parent_data['output']}"
                elif "operation" in parent_data:
                    op_names = {
                        "IF": "Voorwaardelijke berekening",
                        "ADD": "Optelling",
                        "SUBTRACT": "Aftrekking",
                        "MULTIPLY": "Vermenigvuldiging",
                        "DIVIDE": "Deling",
                        "MIN": "Minimum",
                        "MAX": "Maximum",
                    }
                    ref_entry["description"] = op_names.get(parent_data["operation"], parent_data["operation"])

            # If still no description, create one based on section path
            if not ref_entry["description"]:
                if "actions." in section_path:
                    ref_entry["description"] = "Berekening"
                elif "definitions." in section_path:
                    ref_entry["description"] = "Definitie"
                elif "parameters." in section_path:
                    ref_entry["description"] = "Parameter"
                elif "input." in section_path:
                    ref_entry["description"] = "Invoerveld"
                elif "output." in section_path:
                    ref_entry["description"] = "Resultaat"
                elif "sources." in section_path:
                    ref_entry["description"] = "Gegevensbron"
                else:
                    ref_entry["description"] = "Regelspraak"

            # Add to mapping
            if key not in mapping:
                mapping[key] = []
            mapping[key].append(ref_entry)

        # Scan top-level legal_basis
        if "legal_basis" in yaml_content:
            add_reference(yaml_content["legal_basis"], "legal_basis")

        # Scan definitions
        if "properties" in yaml_content and "definitions" in yaml_content["properties"]:
            for def_name, def_value in yaml_content["properties"]["definitions"].items():
                if isinstance(def_value, dict) and "legal_basis" in def_value:
                    add_reference(def_value["legal_basis"], f"properties.definitions.{def_name}", {"name": def_name})

        # Scan parameters
        if "properties" in yaml_content and "parameters" in yaml_content["properties"]:
            for i, param in enumerate(yaml_content["properties"]["parameters"]):
                if "legal_basis" in param:
                    add_reference(param["legal_basis"], f"properties.parameters.{param.get('name', i)}", param)

        # Scan sources
        if "properties" in yaml_content and "sources" in yaml_content["properties"]:
            for i, source in enumerate(yaml_content["properties"]["sources"]):
                if "legal_basis" in source:
                    add_reference(source["legal_basis"], f"properties.sources.{source.get('name', i)}", source)

        # Scan input
        if "properties" in yaml_content and "input" in yaml_content["properties"]:
            for i, input_item in enumerate(yaml_content["properties"]["input"]):
                if "legal_basis" in input_item:
                    add_reference(
                        input_item["legal_basis"], f"properties.input.{input_item.get('name', i)}", input_item
                    )

        # Scan output
        if "properties" in yaml_content and "output" in yaml_content["properties"]:
            for i, output_item in enumerate(yaml_content["properties"]["output"]):
                if "legal_basis" in output_item:
                    add_reference(
                        output_item["legal_basis"], f"properties.output.{output_item.get('name', i)}", output_item
                    )

        # Scan actions
        if "actions" in yaml_content:
            for i, action in enumerate(yaml_content["actions"]):
                if "legal_basis" in action:
                    add_reference(action["legal_basis"], f"actions.{i}", action)

                # Also scan nested legal_basis in action operations
                def scan_operation(op: dict, path_prefix: str):
                    if isinstance(op, dict):
                        if "legal_basis" in op:
                            add_reference(op["legal_basis"], path_prefix, op)
                        if "values" in op and isinstance(op["values"], list):
                            for j, val in enumerate(op["values"]):
                                scan_operation(val, f"{path_prefix}.values.{j}")
                        if "conditions" in op and isinstance(op["conditions"], list):
                            for j, cond in enumerate(op["conditions"]):
                                if "legal_basis" in cond:
                                    add_reference(cond["legal_basis"], f"{path_prefix}.conditions.{j}", cond)

                scan_operation(action, f"actions.{i}")

        # Scan requirements
        if "requirements" in yaml_content:
            for i, req in enumerate(yaml_content["requirements"]):
                if isinstance(req, dict) and "legal_basis" in req:
                    add_reference(req["legal_basis"], f"requirements.{i}", req)

    return mapping


@router.get("/", response_class=HTMLResponse)
async def wetten_home(request: Request, machine_service: EngineInterface = Depends(get_machine_service)):
    """Homepage that looks like wetten.overheid.nl showing available laws"""
    try:
        bwb_mapping = load_bwb_mapping()

        # Only show laws that have content files
        available_laws = []
        for bwb_id, law_info in bwb_mapping.get("laws", {}).items():
            law_content = load_law_content(bwb_id)
            if law_content:
                try:
                    implementations = get_yaml_implementations(bwb_id, machine_service)
                    law_data = {
                        "bwb_id": bwb_id,
                        **law_info,
                        "url": f"https://wetten.overheid.nl/{bwb_id}",
                        "implementations": implementations,
                        "valid_from": law_content.get("valid_from"),
                        "last_updated": law_content.get("last_updated"),
                    }
                    available_laws.append(law_data)
                except Exception:
                    # Skip laws that cause errors in implementations
                    law_data = {
                        "bwb_id": bwb_id,
                        **law_info,
                        "url": f"https://wetten.overheid.nl/{bwb_id}",
                        "implementations": [],
                        "valid_from": law_content.get("valid_from"),
                        "last_updated": law_content.get("last_updated"),
                    }
                    available_laws.append(law_data)

        # Debug template data first
        template_data = {
            "request": request,
            "laws": available_laws,
            "page_title": "Wetten.overheid.nl | Machine Law Clone",
        }

        try:
            # Use unified template that extends the base template
            return templates.TemplateResponse("wetten/index_unified.html", template_data)
        except Exception as template_error:
            return f"Template error: {str(template_error)}<br>Available laws: {len(available_laws)}"
    except Exception as e:
        return f"Error: {str(e)}"


@router.get("/{bwb_id}", response_class=HTMLResponse)
async def view_law(request: Request, bwb_id: str, machine_service: EngineInterface = Depends(get_machine_service)):
    """Display a specific law with wetten.overheid.nl styling"""
    law_content = load_law_content(bwb_id)
    if not law_content:
        raise HTTPException(status_code=404, detail="Wet niet gevonden")

    # Get YAML implementations
    implementations = get_yaml_implementations(bwb_id, machine_service)

    # Load YAML content to get explanations
    yaml_explanations = {}
    if "yaml_files" in law_content:
        for yaml_file in law_content["yaml_files"]:
            yaml_content = load_yaml_file_content(yaml_file["path"])
            if yaml_content:
                yaml_explanations[yaml_file["path"]] = yaml_content

    # Build article-to-YAML mapping from legal_basis references
    article_yaml_mapping = build_article_yaml_mapping(law_content, yaml_explanations)

    return templates.TemplateResponse(
        "wetten/law_detail_simple.html",
        {
            "request": request,
            "law": law_content,
            "implementations": implementations,
            "bwb_id": bwb_id,
            "yaml_explanations": yaml_explanations,
            "article_yaml_mapping": article_yaml_mapping,
            "page_title": f"{law_content.get('title', 'Onbekende wet')} | Wetten.overheid.nl",
            "today": datetime.now().strftime("%d-%m-%Y"),
        },
    )


@router.get("/{bwb_id}/yaml/{yaml_path:path}", response_class=HTMLResponse)
async def view_yaml_implementation(
    request: Request, bwb_id: str, yaml_path: str, machine_service: EngineInterface = Depends(get_machine_service)
):
    """Display YAML implementation with links back to law text"""
    law_content = load_law_content(bwb_id)
    if not law_content:
        raise HTTPException(status_code=404, detail="Wet niet gevonden")

    # Load the YAML implementation
    yaml_file_path = Path(__file__).parent.parent.parent / yaml_path
    if not yaml_file_path.exists():
        raise HTTPException(status_code=404, detail="YAML implementatie niet gevonden")

    try:
        with open(yaml_file_path, encoding="utf-8") as f:
            yaml_content = yaml.safe_load(f)
    except Exception:
        raise HTTPException(status_code=500, detail="Fout bij laden YAML bestand")

    # Convert yaml_content to JSON-serializable format
    import json

    # First preserve definitions if they exist
    definitions = yaml_content.get("definitions", None)

    yaml_content_json = json.loads(json.dumps(yaml_content, cls=DateJSONEncoder))

    # Restore definitions after JSON conversion
    if definitions is not None:
        yaml_content_json["definitions"] = definitions

    yaml_content_string = json.dumps(yaml_content_json, indent=2, ensure_ascii=False)

    # Render actions in regelspraak format
    renderer = RegelspraakRenderer(bwb_id=bwb_id, law_content=law_content)
    rendered_actions = []
    if "actions" in yaml_content:
        for action in yaml_content["actions"]:
            rendered_actions.append(renderer.render_action(action))

    # Render requirements from top level and from within actions
    all_requirements = []

    # Get top-level requirements
    if "requirements" in yaml_content:
        all_requirements.extend(yaml_content["requirements"])

    # Get requirements from actions
    if "actions" in yaml_content:
        for action in yaml_content["actions"]:
            if "requirements" in action:
                all_requirements.extend(action["requirements"])

    # Render all requirements
    rendered_requirements = None
    if all_requirements:
        rendered_requirements = renderer.render_requirements(all_requirements)

    # Note: definitions are constants, not actions with requirements

    # Resolve service references for input fields
    service_reference_urls = {}
    bwb_mapping = load_bwb_mapping()

    if "properties" in yaml_content_json and "input" in yaml_content_json["properties"]:
        for input_item in yaml_content_json["properties"]["input"]:
            if "service_reference" in input_item and "name" in input_item:
                ref_info = resolve_service_reference_url(input_item["service_reference"], bwb_mapping)
                if ref_info:
                    service_reference_urls[input_item["name"]] = ref_info

    # Add enumerate to template context
    template_context = {
        "request": request,
        "law": law_content,
        "yaml_content": yaml_content_json,
        "yaml_content_string": yaml_content_string,
        "yaml_path": yaml_path,
        "bwb_id": bwb_id,
        "renderer": renderer,
        "rendered_actions": rendered_actions,
        "rendered_requirements": rendered_requirements,
        "service_reference_urls": service_reference_urls,
        "page_title": f"{yaml_content.get('name', 'YAML implementatie')} | {law_content.get('title', 'Wet')} | Wetten.overheid.nl",
        "enumerate": enumerate,
    }

    return templates.TemplateResponse(
        "wetten/yaml_detail_complete.html",
        template_context,
    )


@router.get("/test")
async def test_wetten():
    """Test endpoint to debug data loading"""
    try:
        bwb_mapping = load_bwb_mapping()
        laws_count = len(bwb_mapping.get("laws", {}))

        # Count available content files
        available_laws = []
        for bwb_id, law_info in bwb_mapping.get("laws", {}).items():
            law_content = load_law_content(bwb_id)
            if law_content:
                available_laws.append(bwb_id)

        return {
            "status": "ok",
            "total_laws": laws_count,
            "available_content": len(available_laws),
            "available_laws": available_laws,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
