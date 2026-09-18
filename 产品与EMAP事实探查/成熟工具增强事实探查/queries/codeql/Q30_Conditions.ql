/** Branch-condition candidates. Requires context/CFG review before assigning meaning. */
import cpp
import Scope

from Expr e
where e.isCondition() and inScope(e.getFile())
select e.getFile().getAbsolutePath() as file, e.getLocation().getStartLine() as line,
  e.toString() as condition
