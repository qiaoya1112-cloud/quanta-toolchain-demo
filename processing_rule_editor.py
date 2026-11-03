"""One renderer for the rule-management and inline processing editors."""
import html
import json
from pathlib import Path
from processing_rule_store import permissions


def render_rule_editor(rules, projects):
    import quanta_eval_platform as ep
    template = Path(__file__).with_name('templates').joinpath('processing_rule_editor.html').read_text(encoding='utf-8')
    detail = {r['id']: dict(r, document_link=r.get('rule_config', '')) for r in rules}
    projects=[projects] if isinstance(projects,str) else projects
    project_rights=[permissions(project) for project in projects]
    effective={key:any(right[key] for right in project_rights) for key in permissions()}
    rights = '<script>window.RULE_EDITOR_PERMISSIONS=' + json.dumps(effective) + ';</script>'
    return rights + (template.replace('__RULE_DETAIL_DATA__', json.dumps(detail, ensure_ascii=False).replace('</', '<\\/'))
            .replace('__RULE_PROJECT_OPTIONS__', ''.join('<option value="{0}">{0}</option>'.format(html.escape(p, quote=True)) for p in projects if p))
            .replace('__RULE_TAG_TREE__', ep.build_tree_selector_html('rule-tags', ep.tag_management_dimensions())))
