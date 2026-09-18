/** Functions with ErrorExpr nodes; empty results do not prove complete extraction. */
import cpp
import Scope

from Function f
where f.hasErrors() and inScope(f.getFile())
select f.getFile().getAbsolutePath() as file,
  f.getQualifiedName() as function, f.getLocation().getStartLine() as line
