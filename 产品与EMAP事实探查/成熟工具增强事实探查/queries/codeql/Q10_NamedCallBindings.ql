/** Named compile-time bindings. A virtual binding is not its runtime dispatch target. */
import cpp
import Scope

from FunctionCall c, Function f, string relation
where f = c.getTarget() and inScope(c.getFile()) and
  ((c.isVirtual() and relation = "virtual_static_binding") or
   (not c.isVirtual() and relation = "named_compile_time_binding"))
select c.getFile().getAbsolutePath() as file, c.getLocation().getStartLine() as line,
  c.toString() as call_expression, f.getQualifiedName() as target,
  f.getParameterString() as parameters, f.getFile().getAbsolutePath() as target_file,
  relation as relation_kind
