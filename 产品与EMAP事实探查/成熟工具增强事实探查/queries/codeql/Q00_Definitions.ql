/** Inventory of definition locations, not complete translation-unit coverage. */
import cpp
import Scope

from Function f, Location loc
where loc = f.getDefinitionLocation() and inScope(loc.getFile())
select loc.getFile().getAbsolutePath() as file,
  f.getQualifiedName() as function, f.getParameterString() as parameters,
  loc.getStartLine() as line
