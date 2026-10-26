"""Grouped processing filters over per-rule current result snapshots."""
import json

from query_conditions import sql_literal

MAX_GROUPS = 20
ANY_SELECTION = '*'
def _selection(value):
    # Keep one-element arrays for existing query URLs and grouped filter state.
    if isinstance(value, str):
        value = [value.strip() or ANY_SELECTION]
    if (not isinstance(value, list) or len(value) != 1
            or any(not isinstance(item, str) or not item.strip() or len(item) > 300 for item in value)):
        raise ValueError('规则 / 流程只能单选，请选择任意或一个具体选项')
    return [value[0].strip()]


def _specific(group, key):
    return [value for value in _selection(group.get(key, '')) if value != ANY_SELECTION]


def parse_processing_filters(args, kind):
    raw = args.get(f"{kind}_filters")
    if raw is None:
        quality = kind == "quality"
        legacy_keys = (("is_qc", "qa", "quality_rule", "quality_flow") if quality else
                       ("is_annotated", "annotation_rule", "annotation_flow", "annover"))
        use_defaults = not any(key in args for key in legacy_keys)
        group = {
            "status": args.get("is_qc" if quality else "is_annotated", "yes" if use_defaults else ""),
            "rule": args.get(f"{kind}_rule", ""),
            "flow": args.get(f"{kind}_flow", ""),
        }
        if quality:
            group.update(rule_match="any", results=["pass"] if use_defaults else args.getlist("qa"))
        else:
            group["version"] = args.get("annover", "")
        data = {"logic": "and", "groups": [group]}
    else:
        if len(raw) > 32768:
            raise ValueError("处理筛选内容过长")
        try:
            data = json.loads(raw)
        except (ValueError, RecursionError) as error:
            raise ValueError("处理筛选格式无效，请重新配置") from error
    if (not isinstance(data, dict) or data.get("logic") not in ("and", "or")
            or not isinstance(data.get("groups"), list) or len(data["groups"]) > MAX_GROUPS):
        raise ValueError("处理筛选请选择组间关系，每类最多 20 组")
    groups = []
    allowed = {"status", "rule", "flow", "rule_match", "results"} if kind == "quality" else {"status", "rule", "flow", "version"}
    for raw_group in data["groups"]:
        if not isinstance(raw_group, dict) or set(raw_group) - allowed:
            raise ValueError("处理筛选字段无效")
        group = {}
        for name in ("status",) + (("version",) if kind == "annotation" else ()):
            value = raw_group.get(name, "")
            if not isinstance(value, str) or len(value) > 300:
                raise ValueError("处理筛选字段格式无效")
            group[name] = value.strip()
        for name in ('rule', 'flow'):
            group[name] = _selection(raw_group.get(name, ''))
        if group["status"] not in ("", "yes", "no"):
            raise ValueError("是否质检 / 是否标注请选择是或否")
        if kind == "quality":
            group["rule_match"] = raw_group.get("rule_match", "any")
            results = raw_group.get("results", [])
            if (group["rule_match"] not in ("any", "all") or not isinstance(results, list)
                    or any(value not in ("pass", "fail", "warn") for value in results)):
                raise ValueError("请选择有效的质检规则范围和质检结论")
            group["results"] = list(dict.fromkeys(results))
            if group["status"] == "no" and results:
                raise ValueError("未质检条件不能同时指定质检结论")
        else:
            if group["version"] and (not group["version"].isascii() or not group["version"].isdigit() or int(group["version"]) < 1):
                raise ValueError("旧平台标注版本必须为正整数")
            if group["version"] and (_specific(group, 'rule') or _specific(group, 'flow')):
                raise ValueError("新平台规则 / 流程与旧平台版本请分组配置")
        groups.append(group)
    return {"logic": data["logic"], "groups": groups}


def active_groups(config, kind):
    return [group for group in config["groups"] if any(group.get(key) for key in ("status", "results", "version"))
            or _specific(group, 'rule') or _specific(group, 'flow')
            or (kind == "quality" and group.get("rule_match") == "all")]


def _group_matches(group, entries, kind):
    rules, flows = _specific(group, 'rule'), _specific(group, 'flow')
    scoped = [entry for entry in entries if
              (not rules or entry.get("rule") in rules) and
              (not flows or entry.get("flow") in flows) and
              (kind != "annotation" or not group["version"] or
               (entry.get("platform") == "legacy" and str(entry.get("version", "")) == group["version"])) and
              (kind != "annotation" or not (rules or flows) or entry.get("platform") == "new")]
    if group["status"] == "no":
        return not any(entry.get("done") is True for entry in scoped)
    matched = [entry.get("done") is True and
               (kind != "quality" or not group["results"] or entry.get("result") in group["results"])
               for entry in scoped]
    if group.get("rule_match") == "all":
        return (bool(matched) and all(entry.get("rule") for entry in scoped) and all(matched)
                and all(any(entry.get('rule') == rule for entry in scoped) for rule in rules))
    return any(matched)


def processing_matches(config, kind, recording, completed):
    groups = active_groups(config, kind)
    if not groups:
        return True
    entries = recording.get(f"{kind}_records")
    if entries is None:
        # Compatibility for existing scalar records; no synthetic rule assignments.
        entries = [{"rule": recording.get(f"{kind}_rule", ""),
                    "flow": recording.get(f"{kind}_flow", ""), "done": completed,
                    "result": recording.get("qa"),
                    "version": str(recording.get("annotation_version", "")),
                    "platform": "legacy" if recording.get("annotation_version") else "new"}]
    hits = [_group_matches(group, entries, kind) for group in groups]
    return all(hits) if config["logic"] == "and" else any(hits)


def processing_sql(config, kind):
    """Generate correlated array predicates, never mix facts across rules."""
    expressions = []
    for group in active_groups(config, kind):
        rules, flows = _specific(group, 'rule'), _specific(group, 'flow')
        scope = []
        for key, values in (('rule', rules), ('flow', flows)):
            if values:
                scope.append(f'p.{key} = {sql_literal(values[0])}')
        if kind == "annotation":
            if group["version"]:
                scope += ["p.platform = 'legacy'", f"CAST(p.version AS STRING) = {sql_literal(group['version'])}"]
            elif rules or flows:
                scope.append("p.platform = 'new'")
        if kind == "quality":
            fallback = "named_struct('rule', quality_rule, 'flow', quality_flow, 'done', is_qc, 'result', qa_status)"
        else:
            fallback = ("named_struct('rule', annotation_rule, 'flow', annotation_flow, 'done', is_annotated, "
                        "'version', CAST(annotation_version AS STRING), 'platform', "
                        "CASE WHEN annotation_version IS NOT NULL THEN 'legacy' ELSE 'new' END)")
        source = f"COALESCE({kind}_records, array({fallback}))"
        if scope:
            source = f"filter({source}, p -> " + " AND ".join(scope) + ")"
        predicate = "COALESCE(p.done, FALSE)"
        if kind == "quality" and group["results"]:
            predicate += " AND COALESCE(p.result IN (" + ", ".join(map(sql_literal, group["results"])) + "), FALSE)"
        if group["status"] == "no":
            expression = f"NOT exists({source}, p -> COALESCE(p.done, FALSE))"
        elif group.get("rule_match") == "all":
            predicate = "COALESCE(p.rule <> '', FALSE) AND " + predicate
            required = f" AND exists({source}, p -> p.rule = {sql_literal(rules[0])})" if rules else ''
            expression = f"(size({source}) > 0 AND forall({source}, p -> {predicate}){required})"
        else:
            expression = f"exists({source}, p -> {predicate})"
        expressions.append(expression)
    return "(" + (" AND " if config["logic"] == "and" else " OR ").join(expressions) + ")" if expressions else ""
