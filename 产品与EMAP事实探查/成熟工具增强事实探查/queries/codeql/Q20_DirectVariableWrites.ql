/** Direct variable-write relation supplied by the C++ library.
 * Not an exhaustive inventory of writes through aliases, DMA or binary code.
 */
import cpp
import Scope

from Function f, Variable v
where v = f.getAWrittenVariable() and inScope(f.getFile())
select f.getFile().getAbsolutePath() as file, f.getQualifiedName() as function,
  v.getQualifiedName() as variable, v.getFile().getAbsolutePath() as variable_file,
  v.getLocation().getStartLine() as variable_line
