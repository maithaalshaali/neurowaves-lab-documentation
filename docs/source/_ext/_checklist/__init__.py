# _ext/my_checklist/__init__.py
from docutils import nodes
from sphinx.util.docutils import SphinxDirective

class checklist_node(nodes.General, nodes.Element):
    pass

class checkitem_node(nodes.General, nodes.Element):
    def __init__(self, text, checked, key):
        super().__init__()
        self['checked'] = bool(checked)
        self['key'] = key
        self += nodes.Text(text)

class ChecklistDirective(SphinxDirective):
    has_content = True

    def run(self):
        env = self.env
        root = checklist_node()
        idx = 0

        for raw in self.content:
            s = raw.strip()
            # Allow optional leading "- " or "* "
            if s.startswith(('- ', '* ')):
                s = s[2:].lstrip()

            checked = None
            if s.lower().startswith('[ ] '):
                checked, text = False, s[4:]
            elif s.lower().startswith('[x] '):
                checked, text = True, s[4:]
            else:
                # Non-task line: keep as paragraph (or skip, your choice)
                if s:
                    root += nodes.paragraph(text=s)
                continue

            # Stable per-item key for localStorage (docname + index + text)
            key = f"{env.docname}::{idx}::{text[:80]}"
            root += checkitem_node(text, checked, key)
            idx += 1

        return [root]

# ---------------- HTML writer ----------------
def html_visit_checklist_node(self, node):
    self.body.append('<ul class="task-list">')

def html_depart_checklist_node(self, node):
    self.body.append('</ul>')

def html_visit_checkitem_node(self, node):
    checked_attr = ' checked' if node.get('checked') else ''
    key_attr = f' data-key="{self.encode(node.get("key"))}"'
    self.body.append(f'<li><label><input type="checkbox"{checked_attr}{key_attr}> ')

def html_depart_checkitem_node(self, node):
    self.body.append('</label></li>')

# ---------------- LaTeX writer (PDF) ----------------
def latex_visit_checklist_node(self, node):
    self.body.append(r'\begin{itemize}' + '\n')

def latex_depart_checklist_node(self, node):
    self.body.append(r'\end{itemize}' + '\n')

def latex_visit_checkitem_node(self, node):
    box = r'$\boxtimes$' if node.get('checked') else r'$\Box$'
    self.body.append(r'\item ' + box + ' ')

def latex_depart_checkitem_node(self, node):
    pass

def setup(app):
    app.add_node(
        checklist_node,
        html=(html_visit_checklist_node, html_depart_checklist_node),
        latex=(latex_visit_checklist_node, latex_depart_checklist_node),
    )
    app.add_node(
        checkitem_node,
        html=(html_visit_checkitem_node, html_depart_checkitem_node),
        latex=(latex_visit_checkitem_node, latex_depart_checkitem_node),
    )
    app.add_directive("checklist", ChecklistDirective)

    # Load our CSS/JS that make it pretty and persistent (optional but recommended)
    app.add_css_file("checklist.css")
    app.add_js_file("checklist.js")

    return {"version": "0.1", "parallel_read_safe": True}
