/** Function references (for example addresses used in registration tables).
 * These are reference sites, not proof that registration or invocation occurred.
 */
import cpp
import Scope

from FunctionAccess a, Function f
where f = a.getTarget() and inScope(a.getFile())
select a.getFile().getAbsolutePath() as file, a.getLocation().getStartLine() as line,
  a.toString() as reference_expression, f.getQualifiedName() as referenced_function,
  f.getParameterString() as parameters
