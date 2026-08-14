from pathlib import Path

import yaml
from openapi_spec_validator import validate


def main():
    path = Path(__file__).resolve().parents[1] / "docs" / "openapi.yaml"
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    validate(document)
    print(f"OpenAPI contract is valid: {path}")


if __name__ == "__main__":
    main()
