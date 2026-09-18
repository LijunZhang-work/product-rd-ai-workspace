/** Call sites not represented as named FunctionCall bindings. Review explicitly. */
import cpp
import Scope

from Call c
where not c instanceof FunctionCall and inScope(c.getFile())
select c.getFile().getAbsolutePath() as file, c.getLocation().getStartLine() as line,
  c.toString() as expression, c.getPrimaryQlClasses() as classes
