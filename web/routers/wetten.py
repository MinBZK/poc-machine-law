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
                    }
                    available_laws.append(law_data)
                except Exception:
                    # Skip laws that cause errors in implementations
                    law_data = {
                        "bwb_id": bwb_id,
                        **law_info,
                        "url": f"https://wetten.overheid.nl/{bwb_id}",
                        "implementations": [],
                    }
                    available_laws.append(law_data)

        # Debug template data first
        template_data = {
            "request": request,
            "laws": available_laws,
            "page_title": "Wetten.overheid.nl | Machine Law Clone",
        }

        try:
            return templates.TemplateResponse("wetten/index.html", template_data)
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

    return templates.TemplateResponse(
        "wetten/law_detail.html",
        {
            "request": request,
            "law": law_content,
            "implementations": implementations,
            "bwb_id": bwb_id,
            "page_title": f"{law_content.get('title', 'Onbekende wet')} | Wetten.overheid.nl",
            "today": datetime.now().strftime("%d-%m-%Y"),
        },
    )


@router.get("/{bwb_id}/artikel/{article_id}", response_class=HTMLResponse)
async def view_article(
    request: Request, bwb_id: str, article_id: str, machine_service: EngineInterface = Depends(get_machine_service)
):
    """Display a specific article with cross-references to YAML implementations"""
    law_content = load_law_content(bwb_id)
    if not law_content:
        raise HTTPException(status_code=404, detail="Wet niet gevonden")

    # Normalize article_id - add 'Artikel' prefix if not present
    if not article_id.startswith("Artikel"):
        article_id = f"Artikel{article_id}"

    # Find the specific article
    article = None
    chapter_context = None

    # First check if structure has direct articles (flat structure)
    structure = law_content.get("structure", {})
    if "articles" in structure:
        for art in structure["articles"]:
            if art.get("id") == article_id:
                article = art
                break

    # If not found, check nested structure
    if not article and "chapters" in structure:
        for chapter in structure["chapters"]:
            for section in chapter.get("sections", []):
                for subsection in section.get("sections", []):
                    for art in subsection.get("articles", []):
                        if art.get("id") == article_id:
                            article = art
                            chapter_context = {"chapter": chapter, "section": section, "subsection": subsection}
                            break
                    if article:
                        break
                # Also check direct articles in sections
                for art in section.get("articles", []):
                    if art.get("id") == article_id:
                        article = art
                        chapter_context = {"chapter": chapter, "section": section}
                        break
                if article:
                    break
            if article:
                break

    if not article:
        raise HTTPException(status_code=404, detail="Artikel niet gevonden")

    # Get YAML implementations that reference this article
    implementations = get_yaml_implementations(bwb_id, machine_service)

    # Find cross-references from YAML to this article
    yaml_references = []
    for impl in implementations:
        yaml_path = Path(__file__).parent.parent.parent / impl["path"]
        if yaml_path.exists():
            try:
                with open(yaml_path, encoding="utf-8") as f:
                    yaml_content = yaml.safe_load(f)

                # Check legal_basis references
                legal_basis = yaml_content.get("legal_basis", {})
                if legal_basis.get("article") == article_id.replace("Artikel", ""):
                    yaml_references.append(
                        {
                            "type": "legal_basis",
                            "implementation": impl,
                            "description": "Hoofdartikel voor deze regel",
                            "yaml_section": "legal_basis",
                        }
                    )

                # Check parameters, sources, etc. for legal_basis references
                for section_name in ["parameters", "sources", "input", "output", "actions"]:
                    section = yaml_content.get("properties", {}).get(section_name) or yaml_content.get(section_name, [])
                    if isinstance(section, list):
                        for item in section:
                            if isinstance(item, dict) and "legal_basis" in item:
                                lb = item["legal_basis"]
                                if lb.get("article") == article_id.replace("Artikel", ""):
                                    yaml_references.append(
                                        {
                                            "type": section_name,
                                            "implementation": impl,
                                            "description": item.get("description", f"{section_name} item"),
                                            "yaml_section": f"{section_name}.{item.get('name', 'unknown')}",
                                        }
                                    )

            except Exception:
                pass

    return templates.TemplateResponse(
        "wetten/article_detail.html",
        {
            "request": request,
            "law": law_content,
            "article": article,
            "chapter_context": chapter_context,
            "yaml_references": yaml_references,
            "implementations": implementations,
            "bwb_id": bwb_id,
            "article_id": article_id,
            "page_title": f"{article.get('title', article_id)} | {law_content.get('title', 'Wet')} | Wetten.overheid.nl",
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

    yaml_content_json = json.loads(json.dumps(yaml_content, cls=DateJSONEncoder))
    yaml_content_string = json.dumps(yaml_content_json, indent=2, ensure_ascii=False)

    # Render actions in regelspraak format
    renderer = RegelspraakRenderer(bwb_id=bwb_id)
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

    return templates.TemplateResponse(
        "wetten/yaml_detail.html",
        {
            "request": request,
            "law": law_content,
            "yaml_content": yaml_content_json,
            "yaml_content_string": yaml_content_string,
            "yaml_path": yaml_path,
            "bwb_id": bwb_id,
            "renderer": renderer,
            "rendered_actions": rendered_actions,
            "rendered_requirements": rendered_requirements,
            "page_title": f"{yaml_content.get('name', 'YAML implementatie')} | {law_content.get('title', 'Wet')} | Wetten.overheid.nl",
        },
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
