# X-Validator
Validate JSON and YAML files against a schema.

## Install
```bash
pip install git+https://github.com/azweb76/x-validator [--upgrade]
```

## Usage (validate)
Validate a file against a schema.

```bash
xvalidator validate --schema myfile.schema.yaml myfile.yaml
```

*myfile.schema.yaml*
```yaml
'field[0-9]+': !field
  type: str
  required: true
  validation: ^[a-zA-Z0-9]+$
listfield:
  type: list
  required: true
  item:
    sfield: !field
      type: int
```

*myfile.yaml*
```yaml
field1: test-value
field2: test-value
listfield:
  - sfield: 1
```
