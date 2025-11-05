"""
Simplified FEEL (Friendly Enough Expression Language) evaluator.

Supports a subset of FEEL needed for our DMN files:
- Literals: numbers, strings, booleans, dates
- Arithmetic: +, -, *, /, **
- Comparisons: =, !=, <, <=, >, >=
- Logical: and, or, not
- Context navigation: person.name, person.birth_date
- Function calls: years(date1, date2), min(a, b), max(a, b)
- Conditionals: if condition then value1 else value2
- Let bindings: let x = 1 in x + 2
- Lists: [1, 2, 3]
- List membership: value in [list]
"""
import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union

from .exceptions import FEELEvaluationError, FEELSyntaxError


class FEELEvaluator:
    """Evaluates FEEL expressions."""

    def __init__(self, trace_callback=None):
        self.context: Dict[str, Any] = {}
        self.trace_callback = trace_callback

    def _trace(self, event_type: str, data: Dict[str, Any]):
        """Emit a trace event if callback is configured."""
        if self.trace_callback:
            self.trace_callback(event_type, data)

    def evaluate(self, expression: str, context: Dict[str, Any]) -> Any:
        """
        Evaluate a FEEL expression in the given context.

        Args:
            expression: FEEL expression string
            context: Dictionary of variables available in scope

        Returns:
            Evaluated result

        Raises:
            FEELSyntaxError: If expression has syntax errors
            FEELEvaluationError: If evaluation fails
        """
        self.context = context
        # Normalize whitespace - replace newlines with spaces for multiline expressions
        expression = ' '.join(expression.split())

        if not expression:
            return None

        try:
            return self._eval_expression(expression)
        except FEELSyntaxError:
            raise
        except FEELEvaluationError:
            raise
        except Exception as e:
            raise FEELEvaluationError(f"Failed to evaluate '{expression}': {e}") from e

    def _eval_expression(self, expr: str) -> Any:
        """Evaluate a FEEL expression recursively."""
        expr = expr.strip()

        # Handle null/empty
        if expr == 'null' or expr == '':
            return None

        # Handle booleans
        if expr == 'true':
            return True
        if expr == 'false':
            return False

        # Handle let bindings: let x = 1, y = 2 in x + y
        if expr.startswith('let '):
            return self._eval_let(expr)

        # Handle if-then-else: if condition then value1 else value2
        if expr.startswith('if '):
            return self._eval_if(expr)

        # Handle function calls BEFORE operators to avoid parsing operators inside function args
        # Check if this looks like a function call: name(...) or name(...).property
        if '(' in expr and ')' in expr:
            # Check if it's a function call (not just parentheses for grouping)
            paren_start = expr.index('(')
            potential_func_name = expr[:paren_start].strip()
            # Function names should be valid identifiers (letters, numbers, underscores)
            if potential_func_name and potential_func_name.replace('_', '').isalnum():
                # Check if there's property access after the function call: func(...).property
                # Find the matching closing paren
                paren_depth = 0
                paren_end = -1
                for i in range(paren_start, len(expr)):
                    if expr[i] == '(':
                        paren_depth += 1
                    elif expr[i] == ')':
                        paren_depth -= 1
                        if paren_depth == 0:
                            paren_end = i
                            break

                if paren_end > 0:
                    after_call = expr[paren_end + 1:].strip()
                    if after_call.startswith('.'):
                        # Property access after function call: func(...).property
                        func_call = expr[:paren_end + 1]
                        property_path = after_call[1:]  # Remove leading dot
                        func_result = self._eval_function_call(func_call)
                        # Navigate properties on the result
                        return self._navigate_properties(func_result, property_path)
                    elif not after_call:
                        # Simple function call: func(...)
                        return self._eval_function_call(expr)
                # If we didn't match the pattern above, continue to other handlers

        # If expr ends with ), try as simple function call
        if '(' in expr and expr.rstrip().endswith(')'):
            paren_pos = expr.index('(')
            potential_func_name = expr[:paren_pos].strip()
            if potential_func_name and potential_func_name.replace('_', '').isalnum():
                return self._eval_function_call(expr)

        # Handle logical OR
        if ' or ' in expr:
            return self._eval_logical_or(expr)

        # Handle logical AND
        if ' and ' in expr:
            return self._eval_logical_and(expr)

        # Handle comparisons: =, !=, <, <=, >, >=
        for op in ['<=', '>=', '!=', '=', '<', '>']:
            if f' {op} ' in expr:
                return self._eval_comparison(expr, op)

        # Handle arithmetic: +, -, *, /, **
        # Process in order of precedence (lowest to highest)
        for op in ['+', '-']:
            parts = self._split_by_operator(expr, op)
            if len(parts) > 1:
                return self._eval_arithmetic(parts, op)

        for op in ['*', '/']:
            parts = self._split_by_operator(expr, op)
            if len(parts) > 1:
                return self._eval_arithmetic(parts, op)

        # Handle power
        if '**' in expr:
            parts = self._split_by_operator(expr, '**')
            if len(parts) > 1:
                return self._eval_arithmetic(parts, '**')

        # Handle list membership: value in [list] or value in list_var
        if ' in ' in expr:
            return self._eval_in(expr)

        # Handle NOT
        if expr.startswith('not '):
            return not self._eval_expression(expr[4:].strip())

        # Handle lists: [1, 2, 3]
        if expr.startswith('[') and expr.endswith(']'):
            return self._eval_list(expr)

        # Handle context/dict literals: {key: value}
        if expr.startswith('{') and expr.endswith('}'):
            return self._eval_context_literal(expr)

        # Handle strings
        if (expr.startswith('"') and expr.endswith('"')) or \
           (expr.startswith("'") and expr.endswith("'")):
            return expr[1:-1]

        # Handle numbers
        try:
            if '.' in expr:
                return float(expr)
            return int(expr)
        except ValueError:
            pass

        # Handle dates: @"2025-01-01" or date("2025-01-01")
        if expr.startswith('@"') and expr.endswith('"'):
            date_str = expr[2:-1]
            return datetime.fromisoformat(date_str).date()

        # Handle context navigation: person.name, person.birth_date
        if '.' in expr:
            return self._eval_context_navigation(expr)

        # Handle variable lookup
        if expr in self.context:
            return self.context[expr]

        # Handle parentheses
        if expr.startswith('(') and expr.endswith(')'):
            return self._eval_expression(expr[1:-1])

        raise FEELSyntaxError(f"Cannot parse FEEL expression: {expr}")

    def _eval_let(self, expr: str) -> Any:
        """Evaluate let binding: let x = 1, y = 2 in x + y"""
        # Find 'in' keyword
        in_pos = expr.rfind(' in ')
        if in_pos == -1:
            raise FEELSyntaxError(f"Let expression missing 'in': {expr}")

        bindings_str = expr[4:in_pos].strip()
        body = expr[in_pos + 4:].strip()

        # Parse bindings
        bindings = {}
        for binding in bindings_str.split(','):
            binding = binding.strip()
            if '=' not in binding:
                raise FEELSyntaxError(f"Invalid let binding: {binding}")

            name, value_expr = binding.split('=', 1)
            name = name.strip()
            value_expr = value_expr.strip()

            # Evaluate in current context
            value = self._eval_expression(value_expr)
            bindings[name] = value

        # Create new context with bindings
        old_context = self.context.copy()
        self.context.update(bindings)

        try:
            result = self._eval_expression(body)
        finally:
            self.context = old_context

        return result

    def _eval_if(self, expr: str) -> Any:
        """Evaluate if-then-else: if condition then value1 else value2"""
        # Find matching 'then' for the outermost 'if'
        then_pos = self._find_keyword(expr, ' then ', start=3)

        if then_pos == -1:
            raise FEELSyntaxError(f"If expression missing 'then': {expr}")

        condition = expr[3:then_pos].strip()

        # Find matching 'else' for this 'if' by counting nested if/then/else
        else_pos = self._find_matching_else(expr, then_pos + 6)

        if else_pos == -1:
            # No else clause
            true_value = expr[then_pos + 6:].strip()
            false_value = None
        else:
            true_value = expr[then_pos + 6:else_pos].strip()
            false_value = expr[else_pos + 6:].strip()

        # Evaluate condition
        cond_result = self._eval_expression(condition)

        # Trace the condition evaluation
        self._trace('condition', {
            'expression': condition,
            'result': cond_result
        })

        if cond_result:
            # Trace that we're taking the 'then' branch
            self._trace('branch', {
                'branch_type': 'then',
                'expression': true_value
            })
            result = self._eval_expression(true_value)
            self._trace('branch_result', {
                'branch_type': 'then',
                'result': result
            })
            return result
        elif false_value is not None:
            # Trace that we're taking the 'else' branch
            self._trace('branch', {
                'branch_type': 'else',
                'expression': false_value
            })
            result = self._eval_expression(false_value)
            self._trace('branch_result', {
                'branch_type': 'else',
                'result': result
            })
            return result
        else:
            return None

    def _find_keyword(self, expr: str, keyword: str, start: int = 0) -> int:
        """Find a keyword in expression, skipping over nested structures."""
        return expr.find(keyword, start)

    def _find_matching_else(self, expr: str, start: int) -> int:
        """Find the else that matches the current if level."""
        depth = 0
        i = start
        while i < len(expr) - 5:  # Need at least ' else ' (6 chars)
            # Check for nested 'if'
            if expr[i:i+4] == ' if ' or (i == 0 and expr[i:i+3] == 'if '):
                depth += 1
                i += 3
            # Check for 'then' (closes an 'if')
            elif expr[i:i+6] == ' then ':
                # This then is for a nested if
                i += 6
            # Check for 'else'
            elif expr[i:i+6] == ' else ':
                if depth == 0:
                    return i  # Found matching else
                # This else might close a nested if
                # Look ahead to see if next is 'if' (else if)
                if i + 6 < len(expr) and expr[i+6:i+9] == 'if ':
                    # This is 'else if', part of nested structure
                    pass
                else:
                    # This closes a nested if
                    depth = max(0, depth - 1)
                i += 6
            else:
                i += 1
        return -1  # No matching else found

    def _eval_logical_or(self, expr: str) -> bool:
        """Evaluate logical OR."""
        parts = [p.strip() for p in expr.split(' or ')]
        for part in parts:
            if self._eval_expression(part):
                return True
        return False

    def _eval_logical_and(self, expr: str) -> bool:
        """Evaluate logical AND."""
        parts = [p.strip() for p in expr.split(' and ')]
        for part in parts:
            if not self._eval_expression(part):
                return False
        return True

    def _eval_comparison(self, expr: str, op: str) -> bool:
        """Evaluate comparison operators."""
        left, right = expr.split(f' {op} ', 1)
        left_val = self._eval_expression(left.strip())
        right_val = self._eval_expression(right.strip())

        if op == '=':
            return left_val == right_val
        elif op == '!=':
            return left_val != right_val
        elif op == '<':
            return left_val < right_val
        elif op == '<=':
            return left_val <= right_val
        elif op == '>':
            return left_val > right_val
        elif op == '>=':
            return left_val >= right_val

        return False

    def _split_by_operator(self, expr: str, op: str) -> List[str]:
        """Split expression by operator, respecting parentheses."""
        parts = []
        current = []
        paren_depth = 0
        i = 0

        while i < len(expr):
            char = expr[i]

            if char == '(':
                paren_depth += 1
                current.append(char)
            elif char == ')':
                paren_depth -= 1
                current.append(char)
            elif char == op and paren_depth == 0:
                # Skip if part of ** when looking for *
                if op == '*' and i + 1 < len(expr) and expr[i + 1] == '*':
                    current.append(char)
                else:
                    parts.append(''.join(current).strip())
                    current = []
                    i += 1  # Skip operator
                    continue
            else:
                current.append(char)

            i += 1

        if current:
            parts.append(''.join(current).strip())

        return parts if len(parts) > 1 else [expr]

    def _eval_arithmetic(self, parts: List[str], op: str) -> Union[int, float]:
        """Evaluate arithmetic expressions."""
        result = self._eval_expression(parts[0])

        for part in parts[1:]:
            value = self._eval_expression(part)

            if op == '+':
                result = result + value
            elif op == '-':
                result = result - value
            elif op == '*':
                result = result * value
            elif op == '/':
                result = result / value
            elif op == '**':
                result = result ** value

        return result

    def _eval_in(self, expr: str) -> bool:
        """Evaluate list membership: value in [list]"""
        parts = expr.split(' in ', 1)
        if len(parts) != 2:
            raise FEELSyntaxError(f"Invalid 'in' expression: {expr}")

        value = self._eval_expression(parts[0].strip())
        list_expr = parts[1].strip()

        # Evaluate list
        list_val = self._eval_expression(list_expr)

        if not isinstance(list_val, list):
            return False

        return value in list_val

    def _eval_function_call(self, expr: str) -> Any:
        """Evaluate function calls."""
        # Find function name and arguments
        paren_pos = expr.index('(')
        func_name = expr[:paren_pos].strip()
        args_str = expr[paren_pos + 1:-1].strip()

        # Parse arguments
        args = self._parse_function_args(args_str)

        # Evaluate arguments
        evaluated_args = [self._eval_expression(arg) for arg in args]

        # Call function
        return self._call_function(func_name, evaluated_args)

    def _parse_function_args(self, args_str: str) -> List[str]:
        """Parse function arguments, respecting commas inside nested calls."""
        if not args_str:
            return []

        args = []
        current = []
        paren_depth = 0

        for char in args_str:
            if char == '(':
                paren_depth += 1
                current.append(char)
            elif char == ')':
                paren_depth -= 1
                current.append(char)
            elif char == ',' and paren_depth == 0:
                args.append(''.join(current).strip())
                current = []
            else:
                current.append(char)

        if current:
            args.append(''.join(current).strip())

        return args

    def _call_function(self, func_name: str, args: List[Any]) -> Any:
        """Call built-in FEEL functions or custom functions from context."""
        # Check if function exists in context first (for BKMs and custom functions)
        if func_name in self.context:
            func = self.context[func_name]
            if callable(func):
                return func(*args)

        # Date/time functions
        if func_name == 'years':
            return self._func_years(args)
        elif func_name == 'date':
            return self._func_date(args)
        elif func_name == 'today':
            return date.today()
        elif func_name == 'now':
            return datetime.now()

        # Numeric functions
        elif func_name == 'min':
            return min(args)
        elif func_name == 'max':
            return max(args)
        elif func_name == 'sum':
            return sum(args)
        elif func_name == 'mean':
            return sum(args) / len(args) if args else 0
        elif func_name == 'abs':
            return abs(args[0])
        elif func_name == 'floor':
            return int(args[0])
        elif func_name == 'ceiling':
            import math
            return math.ceil(args[0])

        # List functions
        elif func_name == 'count':
            return len(args[0]) if args else 0

        # String functions
        elif func_name == 'upper':
            return args[0].upper() if args else ''
        elif func_name == 'lower':
            return args[0].lower() if args else ''

        else:
            raise FEELEvaluationError(f"Unknown function: {func_name}")

    def _func_years(self, args: List[Any]) -> int:
        """Calculate years between two dates."""
        if len(args) != 2:
            raise FEELEvaluationError(f"years() requires 2 arguments, got {len(args)}")

        date1 = args[0]
        date2 = args[1]

        # Convert to date objects if needed
        if isinstance(date1, str):
            date1 = datetime.fromisoformat(date1).date()
        if isinstance(date2, str):
            date2 = datetime.fromisoformat(date2).date()

        # Calculate years difference
        years = date2.year - date1.year

        # Adjust if birthday hasn't occurred yet this year
        if (date2.month, date2.day) < (date1.month, date1.day):
            years -= 1

        return years

    def _func_date(self, args: List[Any]) -> date:
        """Parse date from string."""
        if not args:
            raise FEELEvaluationError("date() requires at least 1 argument")

        date_str = args[0]
        return datetime.fromisoformat(date_str).date()

    def _eval_list(self, expr: str) -> List[Any]:
        """Evaluate list literal: [1, 2, 3]"""
        content = expr[1:-1].strip()

        if not content:
            return []

        # Parse list items
        items = self._parse_function_args(content)

        # Evaluate each item
        return [self._eval_expression(item) for item in items]

    def _eval_context_literal(self, expr: str) -> Dict[str, Any]:
        """Evaluate context literal: {key: value, key2: value2}"""
        content = expr[1:-1].strip()

        if not content:
            return {}

        context_dict = {}

        # Split by commas (respecting nesting)
        items = self._parse_function_args(content)

        for item in items:
            if ':' not in item:
                raise FEELSyntaxError(f"Invalid context entry: {item}")

            key, value = item.split(':', 1)
            key = key.strip()
            value = value.strip()

            # Evaluate value
            context_dict[key] = self._eval_expression(value)

        return context_dict

    def _eval_context_navigation(self, expr: str) -> Any:
        """Evaluate context navigation: person.name or person.birth_date"""
        parts = expr.split('.')
        value = self.context

        for part in parts:
            part = part.strip()

            if isinstance(value, dict):
                if part in value:
                    value = value[part]
                else:
                    return None
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return None

        return value

    def _navigate_properties(self, value: Any, property_path: str) -> Any:
        """Navigate a property path on a value (dict or object)."""
        parts = property_path.split('.')

        for part in parts:
            part = part.strip()

            if isinstance(value, dict):
                if part in value:
                    value = value[part]
                else:
                    return None
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return None

        return value
