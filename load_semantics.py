import json
from pathlib import Path
from typing import Any, Dict

from semantics import SemanticCatalog, SemanticContext, SQLIdiomsCatalog


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)




def load_semantics(base_dir: Path = Path('semantics')) -> tuple[SemanticCatalog, SQLIdiomsCatalog, SemanticContext]:
    semantic_catalog = SemanticCatalog.model_validate(_load_json(base_dir / 'semantic_models.json'))
    sql_idioms = SQLIdiomsCatalog.model_validate(_load_json(base_dir / 'sql_idioms.json'))
    semantic_context = SemanticContext.model_validate(_load_json(base_dir / 'semantic_temporal.json'))
    return semantic_catalog, sql_idioms, semantic_context


def main() -> None:
    catalog, idioms, context = load_semantics()
    print(
        f"Loaded semantics successfully: "
        f"{len(catalog.tables)} tables, "
        f"{len(catalog.query_catalog)} queries, "
        f"{len(idioms.idioms)} SQL idioms, "
        f"{len(context.definitions)} definitions."
    )

    print ( idioms )
    print ( catalog.tables )

if __name__ == '__main__':
    main()
