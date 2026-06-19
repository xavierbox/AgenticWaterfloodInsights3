import json
import sys 
sys.path.append("./")
sys.path.append("../")
sys.path.append("../../")

from pathlib import Path
from typing import Any, Dict

from runtime.v4.semantics.models.semantic_models import SemanticCatalog


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def load_idiom_rules( idiom = 'duckdb', path = Path('semantics/idioms.json')):
 
    idioms = _load_json( path )

    rules = idioms[ idiom ]
    context = "\n".join(f"{name}: {detail}" for name, detail in rules.items())
    return rules, context
    
#idioms_path = Path("../semantics/idioms.json")
#with idioms_path.open() as fh:
#    idioms = json.load(fh)


def load_semantics(full_path: Path ):#= Path('semantics')) -> tuple[SemanticCatalog, SQLIdiomsCatalog, SemanticContext]:
    semantic_catalog = SemanticCatalog.model_validate(_load_json(full_path))
    return semantic_catalog
    #sql_idioms = SQLIdiomsCatalog.model_validate(_load_json(base_dir / 'sql_idioms.json'))
    #semantic_context = SemanticContext.model_validate(_load_json(base_dir / 'semantic_temporal.json'))
    #return semantic_catalog, sql_idioms, semantic_context


def main() -> None:
    catalog = load_semantics( Path("semantic_models.json"))
    print(
        f"Loaded semantics successfully: "
        f"{len(catalog.tables)} tables, "
        f"{len(catalog.query_catalog)} queries, "
        #f"{len(idioms.idioms)} SQL idioms, "
        #f"{len(context.definitions)} definitions."
    )

    #print ( idioms )
    print ( catalog.tables )
    print( catalog.semantic_constraints ) 

if __name__ == '__main__':
    print(20*'**')
    main()
