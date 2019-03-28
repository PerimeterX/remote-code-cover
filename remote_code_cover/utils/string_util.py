from jinja2 import Template


def find_parens(s, open_symbol='{'):
    close_symbol = '}'
    if open_symbol == '(':
        close_symbol = ')'

    to_ret = {}
    p_stack = []

    for i, c in enumerate(s):
        if c == open_symbol:
            p_stack.append(i)
        elif c == close_symbol:
            if len(p_stack) == 0:
                raise IndexError("No matching closing parens at: " + str(i))
            to_ret[p_stack.pop()] = i

    if len(p_stack) > 0:
        raise IndexError("No matching opening parens at: " + str(p_stack.pop()))

    return to_ret


def render_template_with_variables(content, replacements):
    """
    Renders a string from a template string with replacement variables
    Returns the resulting rendered string
    """
    template = Template(content)
    return template.render(**replacements)
