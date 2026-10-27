"""Validated condition trees shared by data selection and SQL previews."""
import datetime
import json
import math

OPERATORS = {
    "eq": "等于", "ne": "不等于", "contains": "包含", "not_contains": "不包含",
    "in": "属于任一值", "not_in": "不属于任一值", "gt": "大于", "gte": "大于等于",
    "lt": "小于", "lte": "小于等于", "empty": "为空", "not_empty": "不为空",
}
TYPE_OPERATORS = {
    "text": ["eq", "ne", "contains", "not_contains", "in", "not_in", "empty", "not_empty"],
    "number": ["eq", "ne", "gt", "gte", "lt", "lte", "in", "not_in"],
    "date": ["eq", "ne", "gt", "gte", "lt", "lte"],
    "boolean": ["eq", "ne"],
    "enum": ["eq", "ne", "in", "not_in"],
    "tags": ["contains", "not_contains", "in", "not_in"],
}


def _value(value, spec):
    if isinstance(value, (dict, list)) or value is None or str(value).strip() == "":
        raise ValueError("请填写条件值")
    value = str(value).strip()
    kind = spec["type"]
    if kind == "number":
        try:
            result = float(value)
        except ValueError as error:
            raise ValueError("数值字段必须填写数字") from error
        if not math.isfinite(result):
            raise ValueError("数值字段必须填写有效数字")
        return result
    if kind == "date":
        try:
            datetime.date.fromisoformat(value)
        except ValueError as error:
            raise ValueError("日期格式应为 YYYY-MM-DD") from error
    if kind == "boolean":
        if value not in ("true", "false"):
            raise ValueError("请选择是或否")
        return value == "true"
    if spec.get("options") and value not in [str(item[0]) for item in spec["options"]]:
        raise ValueError("请选择有效的字段选项")
    return value


def parse_tree(raw, fields):
    """Reject partial/unknown rules instead of silently broadening a query."""
    if not raw:
        return {"logic": "and", "children": []}
    if len(raw) > 32768:
        raise ValueError("条件内容过长，请减少条件")
    try:
        tree = json.loads(raw)
    except (ValueError, RecursionError) as error:
        raise ValueError("条件格式无效，请重新配置") from error
    count = 0

    def validate(node, depth=0):
        nonlocal count
        count += 1
        if count > 100 or depth > 6:
            raise ValueError("最多支持 100 个条件节点、6 层嵌套")
        if not isinstance(node, dict):
            raise ValueError("条件格式无效")
        if "children" in node:
            children = node["children"]
            if node.get("logic") not in ("and", "or") or not isinstance(children, list):
                raise ValueError("条件组必须选择且或或")
            if depth and not children:
                raise ValueError("条件组不能为空，请添加条件或移除该组")
            return {"logic": node["logic"], "children": [validate(child, depth + 1) for child in children]}
        field, op = node.get("field"), node.get("op")
        if not isinstance(field, str) or field not in fields or op not in TYPE_OPERATORS[fields[field]["type"]]:
            raise ValueError("条件字段或运算符无效")
        value = node.get("value", "")
        if op in ("in", "not_in"):
            values = value if isinstance(value, list) else str(value).replace("，", ",").split(",")
            if not values or len(values) > 200:
                raise ValueError("请填写 1 至 200 个条件值")
            value = [_value(item, fields[field]) for item in values]
        elif op not in ("empty", "not_empty"):
            _value(value, fields[field])
        return {"field": field, "op": op, "value": value}

    if not isinstance(tree, dict) or "children" not in tree:
        raise ValueError("条件必须以条件组开始")
    return validate(tree)


def matches(tree, facts, fields):
    if "children" in tree:
        children = tree["children"]
        if not children:
            return True
        values = (matches(child, facts, fields) for child in children)
        return all(values) if tree["logic"] == "and" else any(values)
    spec, op = fields[tree["field"]], tree["op"]
    actual = facts.get(tree["field"])
    if op == "empty":
        return actual is None or actual == "" or actual == []
    if op == "not_empty":
        return actual is not None and actual != "" and actual != []
    if actual is None:
        return False
    raw = tree["value"]
    expected = [_value(value, spec) for value in raw] if op in ("in", "not_in") else _value(raw, spec)
    if op in ("in", "not_in"):
        hit = any(value in expected for value in actual) if isinstance(actual, list) else actual in expected
        return hit if op == "in" else not hit
    if op in ("contains", "not_contains"):
        hit = expected in actual
        return hit if op == "contains" else not hit
    if op == "eq":
        return actual == expected
    if op == "ne":
        return actual != expected
    if op == "gt":
        return actual > expected
    if op == "gte":
        return actual >= expected
    if op == "lt":
        return actual < expected
    return actual <= expected


def sql_literal(value):
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def tree_sql(tree, fields):
    if "children" in tree:
        children = [tree_sql(child, fields) for child in tree["children"]]
        return "(" + (" AND " if tree["logic"] == "and" else " OR ").join(children) + ")" if children else ""
    spec, op = fields[tree["field"]], tree["op"]
    column = spec.get("sql", tree["field"])
    if op in ("empty", "not_empty"):
        empty = f"({column} IS NULL OR {column} = '')"
        return "NOT " + empty if op == "not_empty" else empty
    raw = tree["value"]
    if op in ("in", "not_in"):
        values = [_value(value, spec) for value in raw]
        if spec["type"] == "tags":
            expression = "(" + " OR ".join(f"array_contains({column}, {sql_literal(value)})" for value in values) + ")"
            return "NOT " + expression if op == "not_in" else expression
        return f"{column} {'NOT IN' if op == 'not_in' else 'IN'} (" + ", ".join(map(sql_literal, values)) + ")"
    value = _value(raw, spec)
    if op in ("contains", "not_contains"):
        expression = (f"array_contains({column}, {sql_literal(value)})" if spec["type"] == "tags"
                      else f"contains({column}, {sql_literal(value)})")
        return f"NOT ({expression})" if op == "not_contains" else expression
    symbol = {"eq": "=", "ne": "<>", "gt": ">", "gte": ">=", "lt": "<", "lte": "<="}[op]
    return f"{column} {symbol} {sql_literal(value)}"
